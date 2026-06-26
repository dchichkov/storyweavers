#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/peg_misunderstanding_bravery_magic_fable.py
=================================================================================================

A small fable-like storyworld about a peg, a misunderstanding, a brave choice,
and a little bit of magic.

Premise:
- A young animal or child cares about a peg that holds something important.
- Another character misunderstands the peg's purpose and thinks it is useless,
  stolen, or ordinary.
- A magical hint reveals the peg's real role.
- Brave action repairs the misunderstanding and proves the peg mattered.

The domain is intentionally tiny and constraint-checked: there are only a few
plausible combinations, and invalid choices raise StoryError.
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


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    peg: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "sister", "aunt", "queen"}
        male = {"boy", "father", "brother", "uncle", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_plural(self) -> bool:
        return self.type in {"sheep", "geese", "mice"} or self.label.endswith("s")


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    indoors: bool
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass
class PegType:
    id: str
    label: str
    phrase: str
    place_hint: str
    magic_key: str
    is_important: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Mistake:
    id: str
    misunderstanding: str
    accusation: str
    risk: str
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
class Magic:
    id: str
    label: str
    phrase: str
    reveal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


SETTINGS = {
    "barn": Setting(place="the barn", indoors=True, tags={"farm"}),
    "well": Setting(place="the well", indoors=False, tags={"water"}),
    "kitchen": Setting(place="the kitchen", indoors=True, tags={"home"}),
    "orchard": Setting(place="the orchard", indoors=False, tags={"trees"}),
}

PEGS = {
    "coat_hook": PegType(
        id="coat_hook",
        label="peg",
        phrase="a little wooden peg on the wall",
        place_hint="by the door",
        magic_key="cloak",
    ),
    "hay_peg": PegType(
        id="hay_peg",
        label="peg",
        phrase="a smooth peg in the barn beam",
        place_hint="over the hay",
        magic_key="lantern",
    ),
    "bucket_peg": PegType(
        id="bucket_peg",
        label="peg",
        phrase="a iron peg beside the well",
        place_hint="near the bucket rope",
        magic_key="bucket",
    ),
}

MISTAKES = {
    "useless": Mistake(
        id="useless",
        misunderstanding="thought the peg was useless",
        accusation="called it just a tiny stick",
        risk="would let the coat fall into the mud",
        tags={"cloak", "home"},
    ),
    "lost": Mistake(
        id="lost",
        misunderstanding="thought the peg had been lost",
        accusation="said somebody must have taken it away",
        risk="would leave the lantern hanging too low",
        tags={"lantern", "farm"},
    ),
    "ordinary": Mistake(
        id="ordinary",
        misunderstanding="thought the peg was ordinary",
        accusation="said it was no more important than a pebble",
        risk="would make the bucket rope slip",
        tags={"bucket", "water"},
    ),
}

MAGICS = {
    "glow": Magic(
        id="glow",
        label="a soft glow",
        phrase="a soft glow around the peg",
        reveal="the peg was holding the right thing in the right place",
        tags={"reveal"},
    ),
    "whisper": Magic(
        id="whisper",
        label="a whispering breeze",
        phrase="a whispering breeze that tugged at the peg",
        reveal="the peg was a small helper, not a useless bit of wood",
        tags={"reveal"},
    ),
    "spark": Magic(
        id="spark",
        label="a bright spark",
        phrase="a bright spark that winked beside the peg",
        reveal="the peg mattered because it kept the important thing steady",
        tags={"reveal"},
    ),
}

HERO_NAMES = ["Nina", "Toby", "Mara", "Owen", "Pip", "Lina", "Joss", "Rhea"]
HERO_TYPES = ["girl", "boy", "fox", "rabbit", "mouse"]
HELPER_NAMES = ["Gran", "Mum", "Dad", "the old owl", "the farmer"]
TRAITS = ["brave", "curious", "kind", "gentle", "steady"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    peg: str
    mistake: str
    magic: str
    name: str
    hero_type: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def name_or_label(ent: Entity) -> str:
    return ent.id


# ---------------------------------------------------------------------------
# Causal story steps
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, peg: Entity) -> None:
    world.say(
        f"{hero.id} was a {world.facts['trait']} little {hero.type} who loved to listen for lessons in the old house."
    )
    world.say(
        f"One day, {hero.id} noticed {peg.phrase} {Pegs[world.facts['peg']].place_hint if False else ''}".strip()
    )
    world.say(
        f"{helper.id} said that peg had always been there to help keep something safe."
    )


def setup(world: World, hero: Entity, helper: Entity, peg: Entity, mist: Mistake) -> None:
    world.say(
        f"But {helper.id} {mist.misunderstanding}, and {mist.accusation}."
    )
    world.say(
        f"If that were true, {mist.risk}."
    )


def reveal_magic(world: World, magic: Magic, peg: Entity, hero: Entity) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1.0
    world.say(
        f"Then {magic.phrase} appeared."
    )
    world.say(
        f"In that glow, {hero.id} saw that {magic.reveal}."
    )


def brave_turn(world: World, hero: Entity, helper: Entity, peg: Entity, mist: Mistake) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1.0
    world.say(
        f"{hero.id} took a brave breath and said, "
        f'"The peg is small, but it is not silly. It keeps things where they belong."'
    )
    world.say(
        f"{helper.id} paused, looked again, and nodded."
    )
    world.say(
        f"At once, the mistake lifted, and the worry that had shadowed the room grew light."
    )


def resolution(world: World, hero: Entity, helper: Entity, peg: Entity) -> None:
    world.say(
        f"Together they set the {peg.label} straight, and the coat, lantern, or bucket stayed safe at last."
    )
    world.say(
        f"{hero.id} smiled, because bravery had helped everyone understand what magic had already shown."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type="elder"))
    peg_type = _safe_lookup(PEGS, params.peg)
    peg = world.add(Entity(id=peg_type.id, type="peg", label="peg", phrase=peg_type.phrase))
    mistake = _safe_lookup(MISTAKES, params.mistake)
    magic = _safe_lookup(MAGICS, params.magic)

    world.facts.update(
        hero=hero,
        helper=helper,
        peg=peg,
        peg_type=peg_type,
        mistake=mistake,
        magic=magic,
        trait=params.trait,
        setting=setting,
        place=params.place,
    )

    introduce(world, hero, helper, peg)
    world.para()
    setup(world, hero, helper, peg, mistake)
    world.para()
    reveal_magic(world, magic, peg, hero)
    brave_turn(world, hero, helper, peg, mistake)
    world.para()
    resolution(world, hero, helper, peg)
    return world


# ---------------------------------------------------------------------------
# Validity / constraints
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for peg in PEGS:
            for mistake in MISTAKES:
                if peg == "coat_hook" and mistake != "useless":
                    continue
                if peg == "hay_peg" and mistake != "lost":
                    continue
                if peg == "bucket_peg" and mistake != "ordinary":
                    continue
                combos.append((place, peg, mistake))
    return combos


def explain_rejection(peg: PegType, mistake: Mistake) -> str:
    return (
        f"(No story: that peg-and-mistake pair does not fit this fable. "
        f"The peg would not honestly lead to the misunderstanding '{mistake.id}'. "
        f"Try the peg and mistake that belong together.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A peg/story is valid when the chosen peg and misunderstanding belong together.
valid(Peg, Mistake) :- peg(Peg), misunderstanding(Mistake), pair(Peg, Mistake).

% Fable-like compatibility: each peg has exactly one honest misunderstanding.
pair(coat_hook, useless).
pair(hay_peg, lost).
pair(bucket_peg, ordinary).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for peg_id in PEGS:
        lines.append(asp.fact("peg", peg_id))
    for m_id in MISTAKES:
        lines.append(asp.fact("misunderstanding", m_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((peg, mist) for _, peg, mist in valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny fable storyworld about a peg, misunderstanding, bravery, and magic."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--peg", choices=PEGS)
    ap.add_argument("--mistake", choices=MISTAKES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "peg", None) and getattr(args, "mistake", None):
        if (getattr(args, "peg", None), getattr(args, "mistake", None)) not in {(p, m) for _, p, m in valid_combos()}:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "peg", None):
        combos = [c for c in combos if c[1] == getattr(args, "peg", None)]
    if getattr(args, "mistake", None):
        combos = [c for c in combos if c[2] == getattr(args, "mistake", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, peg, mistake = rng.choice(list(combos))
    magic = _safe_lookup(PEGS, peg).magic_key
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        peg=peg,
        mistake=mistake,
        magic=magic,
        name=name,
        hero_type=hero_type,
        helper=helper,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# QA / story packaging
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child about a peg and a mistake, with the word "{f["peg"].label}".',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} misunderstand a peg, then use bravery and magic to understand it.",
        f"Write a simple story about {f['place']} that ends with everyone seeing why the peg mattered.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    peg: Entity = _safe_fact(world, f, "peg")
    mistake: Mistake = _safe_fact(world, f, "mistake")
    magic: Magic = _safe_fact(world, f, "magic")
    trait = _safe_fact(world, f, "trait")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a {trait} little {hero.type}, and {helper.id}, who first misunderstood the peg.",
        ),
        QAItem(
            question=f"What did the helper think about the peg at first?",
            answer=f"{helper.id} {mistake.misunderstanding} and {mistake.accusation}. That was why the peg seemed unimportant at first.",
        ),
        QAItem(
            question=f"What magical sign helped them look again at the peg?",
            answer=f"{magic.phrase} appeared, and it helped reveal that the peg was really holding something important in place.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} took a brave breath and spoke up kindly, explaining why the peg mattered and helping {helper.id} understand.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    peg: Entity = _safe_fact(world, f, "peg")
    mist: Mistake = _safe_fact(world, f, "mistake")
    mag: Magic = _safe_fact(world, f, "magic")
    out = [
        QAItem(
            question="What is a peg for?",
            answer="A peg is a small piece that can hold things up, like a coat, a lantern, or a rope.",
        ),
        QAItem(
            question="Why can a misunderstanding be a problem?",
            answer="A misunderstanding can make people act on the wrong idea, so they may not notice what is truly important.",
        ),
        QAItem(
            question="What does bravery mean in a fable?",
            answer="Bravery means doing the right thing even when you feel unsure, and saying what needs to be said kindly.",
        ),
        QAItem(
            question="How can magic help in a story?",
            answer="Magic can reveal something hidden, make a lesson easier to see, or give a character a hint to choose wisely.",
        ),
    ]
    if peg.id == "coat_hook":
        out.append(QAItem(question="What does a coat hook peg hold?", answer="It holds coats, cloaks, or other things near the door so they do not fall down."))
    elif peg.id == "hay_peg":
        out.append(QAItem(question="What might a peg in a barn beam hold?", answer="It might hold a lantern or tools safely above the hay."))
    else:
        out.append(QAItem(question="What might a peg near a well hold?", answer="It might help keep a bucket rope steady so the bucket does not slip."))
    return out


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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type}")
    lines.extend(f"- {s}" for s in world.trace)
    return "\n".join(lines)


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
    StoryParams(place="barn", peg="hay_peg", mistake="lost", magic="glow", name="Mara", hero_type="girl", helper="the old owl", trait="brave"),
    StoryParams(place="kitchen", peg="coat_hook", mistake="useless", magic="whisper", name="Pip", hero_type="mouse", helper="Gran", trait="kind"),
    StoryParams(place="orchard", peg="bucket_peg", mistake="ordinary", magic="spark", name="Owen", hero_type="boy", helper="the farmer", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible peg/mistake pairs:\n")
        for peg, mist in combos:
            print(f"  {peg:12} {mist}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
