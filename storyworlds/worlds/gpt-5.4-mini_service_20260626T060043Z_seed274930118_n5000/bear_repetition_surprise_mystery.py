#!/usr/bin/env python3
"""
storyworlds/worlds/bear_repetition_surprise_mystery.py
======================================================

A small mystery-style storyworld about a repeating clue and a surprising bear.

Seed premise:
- A child notices the same clue again and again.
- Each repetition deepens the mystery.
- The surprise ending reveals the bear was not a threat, but the reason the clues appeared.

This world keeps the prose child-facing, concrete, and state-driven. The world
model tracks physical meters and emotional memes, and the story is generated
from the simulated resolution of the mystery.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
            keys = [upper, upper + "S", upper + "ES"]
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
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    facts: dict[str, object] = field(default_factory=dict)

    child: object | None = None
    clue: object | None = None
    mystery: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
    indoor: bool
    weather: str
    affordances: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Clue:
    id: str
    label: str
    repeat_word: str
    surprise_word: str
    answer_word: str
    sense: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Mystery:
    id: str
    label: str
    type: str
    size: str
    harmless: bool
    repeated_action: str
    hiding_place: str
    surprise_line: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _add_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _add_meme(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    clue = world.get("clue")
    mystery = world.get("mystery")
    if _meter(clue, "seen") >= 2 and not world.fired.__contains__(("repetition",)):
        world.fired.add(("repetition",))
        _add_meme(child, "curiosity", 1.0)
        _add_meme(child, "unease", 0.5)
        out.append(
            f"The same {clue.label} kept showing up again and again, and that made the little mystery feel bigger."
        )
    if _meter(clue, "seen") >= 3 and not world.fired.__contains__(("pattern",)):
        world.fired.add(("pattern",))
        _add_meme(child, "pattern_seen", 1.0)
        out.append(
            f"After the third time, the child knew it was not an accident; the clue was trying to tell a story."
        )
    if _meter(mystery, "revealed") >= 1 and not world.fired.__contains__(("surprise",)):
        world.fired.add(("surprise",))
        _add_meme(child, "relief", 1.0)
        out.append(
            f"Then the last shadow moved, and the surprise answer stepped out of the dark."
        )
    return out


CAUSAL_RULES = [_r_repetition]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _set_clue(world: World, clue: Entity) -> None:
    _add_meter(clue, "seen", 1.0)
    child = world.get("child")
    _add_meme(child, "curiosity", 0.5)
    world.say(
        f"{child.id} noticed the {clue.label} again: {clue.repeat_word}, then {clue.repeat_word} once more."
    )
    propagate(world)


def _investigate(world: World, clue: Entity, mystery: Entity) -> None:
    child = world.get("child")
    _add_meter(child, "thinking", 1.0)
    _add_meme(child, "caution", 0.5)
    world.say(
        f"{child.id} followed the clue {clue.repeat_word} by {clue.repeat_word}, listening very carefully."
    )
    world.say(
        f"Each new look made the mystery feel less random and more like a trail."
    )


def _reveal(world: World, clue: Entity, mystery: Entity, bear: Entity) -> None:
    _add_meter(mystery, "revealed", 1.0)
    _add_meter(bear, "seen", 1.0)
    _add_meme(bear, "gentle", 1.0)
    child = world.get("child")
    world.say(
        f"At last, {mystery.surprise_line} {bear.label} was there, not scary at all, but carrying the missing piece."
    )
    world.say(
        f"{child.id} blinked, surprised and relieved, because the bear's paw had been making the clue on purpose."
    )


def _resolve(world: World, clue: Entity, mystery: Entity, bear: Entity) -> None:
    child = world.get("child")
    _add_meme(child, "relief", 1.0)
    _add_meme(child, "joy", 1.0)
    world.say(
        f"The bear had been leading {child.pronoun('object')} to a small lost basket tucked under the {mystery.hiding_place}."
    )
    world.say(
        f"The child smiled, picked up the basket, and waved at the bear as the last clue finally made sense."
    )


SETTINGS = {
    "yard": Setting(place="the backyard", indoor=False, weather="quiet evening", affordances={"search"}),
    "garden": Setting(place="the garden", indoor=False, weather="windy morning", affordances={"search"}),
    "cabin": Setting(place="the cabin", indoor=True, weather="rainy afternoon", affordances={"search"}),
    "woods": Setting(place="the woods edge", indoor=False, weather="misty morning", affordances={"search"}),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="paw prints",
        repeat_word="tap-tap",
        surprise_word="soft",
        answer_word="bear",
        sense="sight",
        tags={"bear", "repeat", "trail"},
    ),
    "knock": Clue(
        id="knock",
        label="little knocks",
        repeat_word="knock-knock",
        surprise_word="gentle",
        answer_word="bear",
        sense="sound",
        tags={"bear", "repeat", "sound"},
    ),
    "ribbon": Clue(
        id="ribbon",
        label="a blue ribbon",
        repeat_word="flutter",
        surprise_word="bright",
        answer_word="bear",
        sense="sight",
        tags={"bear", "repeat", "found"},
    ),
}

MYSTERIES = {
    "basket": Mystery(
        id="basket",
        label="missing basket",
        type="basket",
        size="small",
        harmless=True,
        repeated_action="showed up",
        hiding_place="old stump",
        surprise_line="from behind the fern",
        tags={"find", "bear", "basket"},
    ),
    "bell": Mystery(
        id="bell",
        label="tiny bell",
        type="bell",
        size="small",
        harmless=True,
        repeated_action="rang twice",
        hiding_place="hollow log",
        surprise_line="under the pine branches",
        tags={"find", "bear", "bell"},
    ),
    "lantern": Mystery(
        id="lantern",
        label="lost lantern",
        type="lantern",
        size="small",
        harmless=True,
        repeated_action="glimmered again",
        hiding_place="woodpile",
        surprise_line="behind the stacked wood",
        tags={"find", "bear", "lantern"},
    ),
}

BEARS = {
    "brown": Entity(
        id="bear",
        kind="character",
        type="bear",
        label="the bear",
        phrase="a brown bear with soft eyes",
        facts={"kind": "brown"},
    ),
    "small": Entity(
        id="bear",
        kind="character",
        type="bear",
        label="the bear",
        phrase="a small bear with a careful nose",
        facts={"kind": "small"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Finn", "Ava", "Noah", "Zoe", "Eli"]
TRAITS = ["curious", "brave", "quiet", "careful", "gentle"]


@dataclass
class StoryParams:
    place: str
    clue: str
    mystery: str
    name: str
    trait: str
    seed: Optional[int] = None
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, clue_id, mystery_id) for place in SETTINGS for clue_id in CLUES for mystery_id in MYSTERIES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small repetition-and-surprise mystery storyworld about a bear.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
        and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, clue, mystery = rng.choice(list(combos))
    return StoryParams(
        place=place,
        clue=clue,
        mystery=mystery,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def tell(setting: Setting, clue_def: Clue, mystery_def: Mystery, hero_name: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="child", label=hero_name, phrase=f"a {trait} child"))
    clue = world.add(Entity(id="clue", type="clue", label=clue_def.label, phrase=clue_def.label))
    mystery = world.add(Entity(id="mystery", type=mystery_def.type, label=mystery_def.label, phrase=mystery_def.label))
    bear = world.add(copy.deepcopy(BEARS["brown"]))

    child.meters["steps"] = 0.0
    child.memes["curiosity"] = 0.0
    bear.meters["hiding"] = 1.0

    world.say(f"{child.label} was a {trait} child in {setting.place}, and one little mystery kept bothering {child.pronoun('object')}.")
    world.say(f"It started with {clue_def.repeat_word}, then {clue_def.repeat_word} again: the same {clue.label} showed up twice.")
    _set_clue(world, clue)

    world.para()
    world.say(f"{child.label} followed the trail through {setting.place}, wondering why the clue kept coming back.")
    _investigate(world, clue, mystery)
    _set_clue(world, clue)

    world.para()
    world.say(f"The trail repeated one more time, and now {child.label} was sure the answer had to be nearby.")
    _set_clue(world, clue)
    _reveal(world, clue, mystery, bear)
    _resolve(world, clue, mystery, bear)

    world.facts.update(
        child=child,
        clue=clue,
        mystery=mystery,
        bear=bear,
        setting=setting,
        trait=trait,
        name=hero_name,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CLUES, params.clue), _safe_lookup(MYSTERIES, params.mystery), params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    clue = _safe_fact(world, f, "clue")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short mystery story for a young child where the clue "{clue.repeat_word}" appears more than once.',
        f"Tell a gentle bear mystery where {child.label} keeps noticing {clue.label} until the surprise answer appears.",
        f"Write a child-friendly story about a repeating clue and a bear that turns out to be helpful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    clue = _safe_fact(world, f, "clue")
    mystery = _safe_fact(world, f, "mystery")
    bear = _safe_fact(world, f, "bear")
    return [
        QAItem(
            question=f"What kept repeating in the story?",
            answer=f"The repeating clue was {clue.label}. The same {clue.repeat_word} kept showing up again and again.",
        ),
        QAItem(
            question=f"Why did {child.label} think the little mystery was important?",
            answer=f"Because {clue.label} appeared more than once, {child.label} knew it was a pattern and not just a one-time accident.",
        ),
        QAItem(
            question=f"What was the surprise at the end?",
            answer=f"The surprise was that {bear.label} was behind the clue, and the bear was helping, not frightening anyone.",
        ),
        QAItem(
            question=f"What was {mystery.label}?",
            answer=f"It was the {mystery.label}, which turned out to be the thing the bear had been trying to help find.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not clear at first, so people look for clues to understand it.",
        ),
        QAItem(
            question="Why do repeated clues matter?",
            answer="Repeated clues matter because when the same thing happens again and again, it can show a pattern.",
        ),
        QAItem(
            question="Are bears always scary?",
            answer="No. Bears are wild animals, so they should be treated with care and space, but a story bear can also be gentle or helpful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_seen(C) :- clue(C), seen(C,N), N >= 2.
pattern(C) :- clue_seen(C).
surprise(M) :- mystery(M), revealed(M).
valid_story(Place, Clue, Mystery) :- setting(Place), clue(Clue), mystery(Mystery).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="yard", clue="pawprints", mystery="basket", name="Mia", trait="curious"),
    StoryParams(place="garden", clue="knock", mystery="bell", name="Leo", trait="careful"),
    StoryParams(place="woods", clue="ribbon", mystery="lantern", name="Nora", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for place, clue, mystery in stories:
            print(f"  {place:8} {clue:10} {mystery:10}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.clue} at {p.place} (mystery: {p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
