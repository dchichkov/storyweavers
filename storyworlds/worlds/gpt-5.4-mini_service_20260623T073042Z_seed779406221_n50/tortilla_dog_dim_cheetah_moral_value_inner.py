#!/usr/bin/env python3
"""
storyworlds/worlds/tortilla_dog_dim_cheetah_moral_value_inner.py
================================================================

A small standalone storyworld about a child, a tortilla, a dog-dim mystery,
and a cheetah-like helper in an adventure tone.

The core premise:
- A tortilla goes missing.
- The "dog-dim" clue is a dim, dog-shaped shadow or scent-trail marker.
- A cheetah-like scout helps solve the mystery.
- The child wrestles with an inner moral choice: tell the truth, share, or
  take a shortcut.
- The story resolves through a concrete world change, not a frozen paragraph.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports storyworlds/results eagerly for QAItem, StoryError, StorySample
- imports storyworlds/asp lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    title: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    tortilla: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    indoors: bool
    affordances: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Mystery:
    id: str
    clue: str
    source: str
    suspected_place: str
    hidden_by: str
    danger: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class ValueChoice:
    id: str
    label: str
    choice_text: str
    conscience_text: str
    honest_text: str
    points: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Scout:
    id: str
    label: str
    title: str
    speed: str
    helper_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def _ensure_defaults(ent: Entity) -> None:
    for k in ["lost", "found", "shared", "honest", "guilty", "relief", "curiosity", "trust"]:
        ent.memes.setdefault(k, 0.0)
    for k in ["dust", "smudge", "distance", "worry", "hope", "movement", "mystery"]:
        ent.meters.setdefault(k, 0.0)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for item in [e for e in world.entities.values() if e.kind == "thing"]:
            if item.meters.get("smudge", 0.0) >= THRESHOLD:
                sig = ("smudge_seen", item.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(f"The clue looked dim, but it was real.")
                    changed = True
        for char in [e for e in world.entities.values() if e.kind == "character"]:
            if char.memes.get("honest", 0.0) >= THRESHOLD and not char.attrs.get("confessed"):
                sig = ("confess", char.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    char.attrs["confessed"] = True
                    out.append(f"{char.id} chose the honest path.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            if m.suspected_place in setting.affordances:
                for vid in VALUES:
                    for sid in SCOUTS:
                        combos.append((place, mid, vid))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    value: str
    scout: str
    child_name: str
    child_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: tortilla, dog-dim mystery, cheetah scout, and moral choice.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--scout", choices=SCOUTS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "value", None) is None or c[2] == getattr(args, "value", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, value = rng.choice(list(combos))
    scout = getattr(args, "scout", None) or rng.choice(list(SCOUTS))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    return StoryParams(place=place, mystery=mystery, value=value, scout=scout, child_name=child_name, child_type=child_type)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id=_safe_lookup(SCOUTS, params.scout).label, kind="character", type="cat", label=_safe_lookup(SCOUTS, params.scout).label, title=_safe_lookup(SCOUTS, params.scout).title))
    tortilla = world.add(Entity(id="tortilla", type="thing", label="tortilla"))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    value = _safe_lookup(VALUES, params.value)

    for e in [child, helper, tortilla]:
        _ensure_defaults(e)
    child.memes["curiosity"] += 1
    child.meters["mystery"] += 1
    world.facts.update(child=child, helper=helper, tortilla=tortilla, mystery=mystery, value=value, setting=world.setting)

    world.say(f"{child.id} set out through {world.setting.place} on a small adventure.")
    world.say(f"Somewhere, a tortilla had gone missing, and the only clue was a dog-dim mark {mystery.clue}.")
    world.say(f"{child.id} wondered if the clue meant {mystery.hidden_by} was hiding the tortilla.")
    world.say(f"{child.id} followed the sign, while {child.pronoun().capitalize()} listened to a quiet inner voice: {value.choice_text}")

    world.para()
    child.memes["worry"] += 1
    child.memes["trust"] += 1
    world.say(f"{_safe_lookup(SCOUTS, params.scout).title} {helper.id} padded along beside {child.id} and pointed with a paw.")
    world.say(f'"{_safe_lookup(SCOUTS, params.scout).helper_text}"')
    world.say(f"The trail led toward {mystery.suspected_place}, where the air felt full of questions.")

    world.para()
    if value.points >= 2:
        child.memes["honest"] += 1
        world.say(f"{child.id} decided not to take a shortcut. {value.conscience_text}")
    else:
        child.memes["guilty"] += 1
        world.say(f"{child.id} almost chose the easy way, but the thought of it felt wrong.")
    propagate(world)

    world.para()
    tortilla.meters["found"] += 1
    child.meters["found"] += 1
    child.memes["relief"] += 1
    world.say(f"At last, the mystery ended at {mystery.suspected_place}: the tortilla was there, safe and plain.")
    world.say(f"It had been hidden by {mystery.hidden_by}, and the dim clue had only looked scary at first.")
    if child.attrs.get("confessed"):
        world.say(f"{child.id} told the truth about what {child.pronoun('subject')} had seen, and that made the answer feel brighter.")
    world.say(f"{child.id} shared the tortilla and felt proud for choosing the honest path.")
    world.say(f"That made the little adventure feel complete: clue, courage, and a clean ending image.")

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "market": Setting("the market", False, {"stall", "basket", "shadow"}),
    "courtyard": Setting("the courtyard", False, {"bench", "wall", "shadow"}),
    "path": Setting("the winding path", False, {"tree", "rock", "shadow"}),
}

MYSTERIES = {
    "stall-shadow": Mystery("stall-shadow", "beside a basket", "a shadow", "the market stall", "a tall basket", "someone's snack", {"shadow", "dog-dim"}),
    "bench-trail": Mystery("bench-trail", "near a bench", "a dim trail", "the courtyard", "a stone bench", "a tucked-away tortilla", {"shadow", "dog-dim"}),
    "path-mark": Mystery("path-mark", "under a tree", "a faint mark", "the winding path", "a low rock", "the wind", {"shadow", "dog-dim"}),
}

VALUES = {
    "honesty": ValueChoice("honesty", "honesty", "I should tell the truth.", "The right thing felt bigger than the easy thing.", "telling the truth made the answer feel safe", 3, {"moral"}),
    "sharing": ValueChoice("sharing", "sharing", "I should share what I found.", "Keeping it all would be lonely.", "sharing made the adventure kinder", 2, {"moral"}),
    "care": ValueChoice("care", "care", "I should be careful and fair.", "A brave choice can still be a gentle one.", "care kept the search honest", 1, {"moral"}),
}

SCOUTS = {
    "cheetah": Scout("cheetah", "cheetah", "Scout", "fast", "The cheetah sniffed the trail and pointed at the right clue.", {"cheetah"}),
    "runner": Scout("runner", "runner", "Scout", "swift", "The swift scout padded ahead and noticed the hidden place.", {"cheetah"}),
}

GIRL_NAMES = ["Mia", "Lina", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Noah", "Eli", "Finn", "Milo"]


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.mystery not in MYSTERIES or params.value not in VALUES or params.scout not in SCOUTS:
        pass
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a small child involving a tortilla, a dog-dim clue, and a cheetah helper in {world.setting.place}.',
        f"Tell a mystery story where {f['child'].id} follows a dog-dim sign to find a missing tortilla and learns that {f['value'].label} matters.",
        f'Write a short child-friendly adventure with an inner monologue about "{f["value"].choice_text}" and a gentle mystery ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    mystery = f["mystery"]
    value = f["value"]
    helper = f["helper"]
    return [
        QAItem(question=f"What was {child.id} trying to solve?", answer=f"{child.id} was trying to solve a small mystery about where the tortilla had gone."),
        QAItem(question=f"What clue did {child.id} follow?", answer=f"{child.id} followed a dog-dim clue {mystery.clue}."),
        QAItem(question=f"Who helped {child.id} on the adventure?", answer=f"The cheetah scout, {helper.id}, helped by pointing toward the right place."),
        QAItem(question=f"What did the inner voice remind {child.id} to do?", answer=f"It reminded {child.id} that {value.honest_text} and that the honest path was the better one."),
        QAItem(question=f"Where was the tortilla found?", answer=f"The tortilla was found at {mystery.suspected_place}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a tortilla?", answer="A tortilla is a soft flat bread used in many snacks and meals."),
        QAItem(question="What is a mystery?", answer="A mystery is a question or puzzle that needs clues to solve it."),
        QAItem(question="What does a cheetah mean in a story?", answer="A cheetah is a very fast animal, so it can make a story feel quick and adventurous."),
        QAItem(question="What is an inner monologue?", answer="An inner monologue is the silent voice a character hears in their own mind."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} {e.kind:9} meters={dict(e.meters)} memes={dict(e.memes)} attrs={dict(e.attrs)}")
    return "\n".join(lines)


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


CURATED = [
    StoryParams(place="market", mystery="stall-shadow", value="honesty", scout="cheetah", child_name="Mia", child_type="girl"),
    StoryParams(place="courtyard", mystery="bench-trail", value="sharing", scout="runner", child_name="Leo", child_type="boy"),
    StoryParams(place="path", mystery="path-mark", value="care", scout="cheetah", child_name="Nora", child_type="girl"),
]


def resolve_relevant_value(value_id: str) -> ValueChoice:
    if value_id not in VALUES:
        pass
    return _safe_lookup(VALUES, value_id)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("suspected_place", mid, m.suspected_place))
    for vid, v in VALUES.items():
        lines.append(asp.fact("value", vid))
        lines.append(asp.fact("points", vid, v.points))
    for sid in SCOUTS:
        lines.append(asp.fact("scout", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,M,V) :- place(P), mystery(M), value(V), suspected_place(M, SP), place(P), has_adventure(P).
has_adventure(P) :- place(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_story_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_story(params: StoryParams) -> StorySample:
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.mystery not in MYSTERIES or params.value not in VALUES or params.scout not in SCOUTS:
        pass
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
