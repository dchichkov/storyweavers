#!/usr/bin/env python3
"""
A tiny fable-style storyworld: an orphan, a mystery to solve, and a gentle
reconciliation.

The world is built from a short source-tale premise:
- an orphan child is mistaken for trouble,
- something important goes missing,
- the orphan follows clues and solves the mystery,
- the town and the orphan reconcile,
- the ending proves the change with a calm, earned image.

This file is self-contained apart from the shared storyworld result containers
and the optional shared ASP helper.
"""

from __future__ import annotations

import argparse
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guardian: object | None = None
    orphan: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    missing: str
    clue: str
    culprit: str
    reveal: str
    moral: str
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
class ResolveTool:
    id: str
    label: str
    use: str
    helps_with: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
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


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    guardian: str
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


SETTINGS = {
    "village": Setting(place="the village green", mood="quiet", affords={"lost_lantern"}),
    "orchard": Setting(place="the old orchard", mood="windy", affords={"lost_lantern"}),
    "river": Setting(place="the river path", mood="misty", affords={"lost_lantern"}),
}

MYSTERIES = {
    "lost_lantern": Mystery(
        id="lost_lantern",
        missing="the mayor's lantern",
        clue="a trail of berry-sticky pawprints",
        culprit="a curious fox",
        reveal="the fox had dragged the lantern to a hollow stump to hide it from the rain",
        moral="kindness can find a way where suspicion only makes shadows",
        tags={"fox", "lantern", "kindness"},
    ),
}

TOOLS = {
    "lantern_light": ResolveTool(
        id="lantern_light",
        label="a little lantern",
        use="shine a calm light on the clues",
        helps_with={"fox", "lantern"},
    ),
    "berry_basket": ResolveTool(
        id="berry_basket",
        label="a berry basket",
        use="carry back the recovered things",
        helps_with={"fox"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Nora", "Elin", "Sora", "Pippa"]
BOY_NAMES = ["Tomas", "Ari", "Bram", "Jonah", "Timo", "Eli"]
TRAITS = ["gentle", "patient", "curious", "brave", "soft-spoken"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable-style storyworld about an orphan who solves a mystery and helps a town reconcile."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["village elder", "widow", "farmer", "caretaker"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            if mid in MYSTERIES:
                out.append((place, mid))
    return out


def select_guardian(rng: random.Random) -> str:
    return rng.choice(["village elder", "widow", "farmer", "caretaker"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "mystery", None) and getattr(args, "place", None):
        if getattr(args, "mystery", None) not in _safe_lookup(SETTINGS, getattr(args, "place", None)).affords:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        (p, m) for p, m in valid_combos()
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
        and (getattr(args, "mystery", None) is None or m == getattr(args, "mystery", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery_id = rng.choice(list(combos))
    mystery = _safe_lookup(MYSTERIES, mystery_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = getattr(args, "guardian", None) or select_guardian(rng)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery_id, name=name, gender=gender, guardian=guardian, trait=trait)


def introduce(world: World, orphan: Entity, guardian: Entity) -> None:
    world.say(
        f"Long ago, an orphan named {orphan.id} lived beside {world.setting.place}, "
        f"where the days were quiet and the wind seemed to listen."
    )
    world.say(
        f"{orphan.id} was a {next(t for t in orphan.meters if False) if False else orphan.memes.get('trait_name', 'gentle')} child, and {guardian.label} watched over {orphan.pronoun('object')} with a tired but caring eye."
    )


def tell_setting(world: World, orphan: Entity) -> None:
    world.say(
        f"Each morning, {orphan.id} walked through {world.setting.place} and greeted the chickens, stones, and old doors as if they were neighbors."
    )


def open_mystery(world: World, orphan: Entity, guardian: Entity, mystery: Mystery) -> None:
    orphan.memes["curiosity"] += 1
    guardian.memes["worry"] += 1
    world.say(
        f"One day, {mystery.missing} went missing, and the village grew uneasy."
    )
    world.say(
        f"Some people frowned at {orphan.id} because {orphan.pronoun('subject')} had been near the square that morning."
    )


def inspect_clue(world: World, orphan: Entity, mystery: Mystery) -> None:
    orphan.memes["resolve"] += 1
    orphan.meters["search"] += 1
    world.say(
        f"But {orphan.id} did not hide or argue. {orphan.pronoun('subject').capitalize()} looked closely and found {mystery.clue} by the well."
    )
    world.say(
        f"That clue pointed toward the old fence, where the grass was bent in a small, careful trail."
    )


def follow_path(world: World, orphan: Entity, mystery: Mystery) -> None:
    orphan.meters["trail_followed"] += 1
    world.say(
        f"{orphan.id} followed the trail past a blackberry bush and under a low branch, until the marks led to a hollow stump."
    )
    world.say(
        f"There, {mystery.reveal}."
    )


def reveal_and_reconcile(world: World, orphan: Entity, guardian: Entity, mystery: Mystery) -> None:
    orphan.memes["compassion"] += 1
    guardian.memes["remorse"] += 1
    guardian.memes["love"] += 1
    world.say(
        f"The villagers hurried over, and {guardian.label} breathed out in relief. "
        f"{guardian.label.capitalize()} saw that {orphan.id} had not stolen anything at all."
    )
    world.say(
        f"{guardian.label.capitalize()} apologized for the harsh words, and {orphan.id} accepted the apology with a small nod."
    )
    world.say(
        f"Together they carried {mystery.missing} home, and the lantern shone warm again in the window."
    )
    world.say(
        f"From then on, the town remembered that a lonely child could still be the one who brought everyone back together."
    )


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, guardian_label: str, trait: str) -> World:
    world = World(setting, mystery)
    orphan = world.add(Entity(id=name, kind="character", type=gender, memes={"trait_name": trait}))
    guardian = world.add(Entity(id="Guardian", kind="character", type="guardian", label=guardian_label))
    world.facts.update(orphan=orphan, guardian=guardian, mystery=mystery, setting=setting)

    introduce(world, orphan, guardian)
    world.para()
    tell_setting(world, orphan)
    open_mystery(world, orphan, guardian, mystery)
    inspect_clue(world, orphan, mystery)
    follow_path(world, orphan, mystery)
    world.para()
    reveal_and_reconcile(world, orphan, guardian, mystery)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    orphan = _safe_fact(world, f, "orphan")
    mystery = _safe_fact(world, f, "mystery")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short fable about an orphan named {orphan.id} who solves a mystery at {setting.place}.',
        f"Tell a gentle story where {orphan.id} follows clues, finds {mystery.missing}, and the town apologizes for judging too quickly.",
        f'Write a child-friendly fable that includes the word "orphan" and ends with reconciliation after a mystery is solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    orphan = _safe_fact(world, f, "orphan")
    guardian = _safe_fact(world, f, "guardian")
    mystery = _safe_fact(world, f, "mystery")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {orphan.id}, an orphan who lives near {setting.place} and solves a mystery there.",
        ),
        QAItem(
            question=f"What went missing in the village?",
            answer=f"{mystery.missing} went missing, which made everyone nervous until the clue was followed and the truth came out.",
        ),
        QAItem(
            question=f"How did {orphan.id} solve the problem?",
            answer=f"{orphan.id} noticed {mystery.clue}, followed the trail, and found that {mystery.reveal}.",
        ),
        QAItem(
            question=f"How did the story end between {orphan.id} and {guardian.label}?",
            answer=f"{guardian.label.capitalize()} apologized for judging too quickly, and {orphan.id} accepted the apology. They carried {mystery.missing} home together, so they reconciled.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orphan?",
            answer="An orphan is a child whose parents are not there to care for them, so they need another grown-up or a community to help them.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something people do not understand at first, so they look for clues to find out what really happened.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop staying angry, say sorry when they should, and start being kind to each other again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village", mystery="lost_lantern", name="Mina", gender="girl", guardian="village elder", trait="gentle"),
    StoryParams(place="orchard", mystery="lost_lantern", name="Tomas", gender="boy", guardian="widow", trait="curious"),
]


ASP_RULES = r"""
setting(village).
setting(orchard).
setting(river).

affords(village,lost_lantern).
affords(orchard,lost_lantern).
affords(river,lost_lantern).

mystery(lost_lantern).

valid(P,M) :- setting(P), mystery(M), affords(P,M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for mid in _safe_lookup(SETTINGS, sid).affords:
            lines.append(asp.fact("affords", sid, mid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MYSTERIES, params.mystery), params.name, params.gender, params.guardian, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = getattr(args, "guardian", None) or select_guardian(rng)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery_id, name=name, gender=gender, guardian=guardian, trait=trait)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mystery) combos:\n")
        for place, mystery in combos:
            print(f"  {place:9} {mystery}")
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
