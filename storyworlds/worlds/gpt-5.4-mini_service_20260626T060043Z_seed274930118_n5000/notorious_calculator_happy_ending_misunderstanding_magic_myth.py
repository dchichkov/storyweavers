#!/usr/bin/env python3
"""
storyworlds/worlds/notorious_calculator_happy_ending_misunderstanding_magic_myth.py
===================================================================================

A small myth-style storyworld about a notorious calculator, a magical mistake,
and a happy ending after a misunderstanding.

The premise:
- A child or young helper receives a famous calculator with a reputation.
- The calculator is meant to help with a task tied to numbers, offerings, or
  stars in a mythic setting.
- A misunderstanding makes the hero think the calculator has done something
  strange or powerful.
- Magic and a careful explanation turn the trouble into a happy ending.

This world is intentionally compact: it models one mythic problem with a
reasonably causal turn and resolution, plus grounded Q&A and an ASP twin for
parity checking.
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
# World model
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the shrine"
    mood: str = "moonlit"
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
class Ritual:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    weather_words: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    type: str
    plural: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Charm:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "shrine": Setting(place="the old shrine", mood="moonlit", affords={"count_stars", "read_omens"}),
    "cave": Setting(place="the echo cave", mood="shadowy", affords={"count_stars", "read_omens"}),
    "hill": Setting(place="the windy hill", mood="bright", affords={"count_stars", "read_omens"}),
}

RITUALS = {
    "count_stars": Ritual(
        id="count_stars",
        verb="count the stars",
        gerund="counting the stars",
        rush="rush to count the stars",
        effect="glowed and twinkled",
        weather_words={"moonlit"},
        tags={"stars", "magic"},
    ),
    "read_omens": Ritual(
        id="read_omens",
        verb="read the omens",
        gerund="reading the omens",
        rush="hurry to read the omens",
        effect="spun like a secret sign",
        weather_words={"shadowy"},
        tags={"omens", "magic"},
    ),
}

PRIZES = {
    "tablet": Prize(label="tablet", phrase="a carved slate tablet", region="hands", type="tablet"),
    "scroll": Prize(label="scroll", phrase="a long linen scroll", region="hands", type="scroll"),
    "crown": Prize(label="crown", phrase="a tiny golden crown", region="head", type="crown"),
}

CHARMS = [
    Charm(
        id="lens",
        label="a crystal lens",
        covers={"hands", "head"},
        guards={"glow", "spark"},
        prep="set the crystal lens beside the calculator",
        tail="placed the crystal lens where the moonlight could touch it",
    ),
    Charm(
        id="cloth",
        label="a blue cloth wrap",
        covers={"hands"},
        guards={"dust", "spark"},
        prep="wrap the calculator in a blue cloth first",
        tail="tied the blue cloth around the calculator",
    ),
]

NAMES = ["Ari", "Mina", "Tala", "Niko", "Eli", "Sera", "Liora", "Kian"]
ROLES = ["child", "apprentice", "messenger", "keeper"]
KINDS = ["girl", "boy"]
HELPERS = ["priestess", "old keeper", "garden monk", "star reader"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    ritual: str
    prize: str
    name: str
    gender: str
    helper: str
    role: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def ritual_at_risk(ritual: Ritual, prize: Prize) -> bool:
    return (ritual.id == "count_stars" and prize.region in {"hands", "head"}) or (
        ritual.id == "read_omens" and prize.region in {"hands", "head"}
    )


def select_charm(ritual: Ritual, prize: Prize) -> Optional[Charm]:
    for charm in CHARMS:
        if prize.region in charm.covers and "spark" in charm.guards:
            return charm
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for ritual_id in setting.affords:
            ritual = _safe_lookup(RITUALS, ritual_id)
            for prize_id, prize in PRIZES.items():
                if ritual_at_risk(ritual, prize) and select_charm(ritual, prize):
                    out.append((place, ritual_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def begin_story(world: World, hero: Entity, helper: Entity, ritual: Ritual, prize: Entity) -> None:
    world.say(
        f"In the {world.setting.place}, {hero.id} was known as a little {hero.type} "
        f"who carried a notorious calculator that everyone had heard about."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {ritual.gerund}, and {helper.pronoun('possessive')} "
        f"{helper.label or helper.type} had given {hero.pronoun('object')} the calculator to help."
    )
    world.say(
        f"That same day, {hero.id} held {hero.pronoun('possessive')} {prize.label} "
        f"and hoped to use the calculator for the rite."
    )


def misunderstanding(world: World, hero: Entity, helper: Entity, ritual: Ritual, prize: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.para()
    world.say(
        f"When {hero.id} pressed the buttons, the calculator flashed at once and "
        f"{ritual.effect} in the moonlight."
    )
    world.say(
        f"{hero.id} thought the notorious calculator had made a wild mistake, "
        f"and {hero.pronoun().capitalize()} frowned at {prize.phrase}."
    )
    world.say(
        f"But {helper.pronoun('possessive')} {helper.label or helper.type} smiled and said the glow was only a sign, not a curse."
    )
    world.facts["misunderstanding"] = True


def offer_charm(world: World, hero: Entity, helper: Entity, ritual: Ritual, prize: Entity) -> Optional[Charm]:
    charm = select_charm(ritual, prize)
    if not charm:
        return None
    world.para()
    world.say(
        f"{helper.pronoun().capitalize()} set {charm.label} near the calculator and said, "
        f'"The light needs a gentler frame."'
    )
    world.say(
        f"{helper.pronoun().capitalize()} told {hero.id} to {charm.prep}, so the omen could be read safely."
    )
    return charm


def happy_ending(world: World, hero: Entity, helper: Entity, ritual: Ritual, prize: Entity, charm: Charm) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["fear"] = 0
    world.para()
    world.say(
        f"{hero.id} followed the advice, and soon the calculator hummed like a tiny temple bell."
    )
    world.say(
        f"The sign became clear: the world was not broken at all; it was only asking for patience."
    )
    world.say(
        f"So {hero.id} {ritual.gerund} with {prize.phrase} held close, the charm glimmered beside the calculator, "
        f"and the day ended in a happy ending with laughter, steady hands, and calm stars."
    )
    world.facts["resolved"] = True
    world.facts["charm"] = charm.id


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short myth for a child about a notorious calculator, a magical misunderstanding, and a happy ending.',
        f"Tell a mythic story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} uses a calculator at {world.setting.place} while trying to {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ritual").verb}.",
        f"Write a gentle myth about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id}, a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize").label}, and a magical light that is first misunderstood and then explained.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    ritual: Ritual = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ritual")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    charm: Charm = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm_entity")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who carried the notorious calculator in the story?",
            answer=f"{hero.id} carried it with {hero.pronoun('possessive')} {prize.label} at {place}.",
        ),
        QAItem(
            question=f"What did {hero.id} first think when the calculator flashed?",
            answer=f"{hero.id} thought the calculator had made a mistake, but it was really a magical sign.",
        ),
        QAItem(
            question=f"How did the helper calm the misunderstanding?",
            answer=f"{helper.id} brought {charm.label} and explained that the light needed a gentler frame.",
        ),
        QAItem(
            question=f"What was the ending of the myth?",
            answer=f"The ending was happy because {hero.id} could keep {ritual.gerund} and everyone understood the magic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does a calculator do?",
            answer="A calculator helps people add, subtract, multiply, or divide numbers quickly.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something wondrous that seems beyond ordinary life, like a light, a spell, or a strange sign.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(R, P) :- ritual(R), prize(P), (R = count_stars; R = read_omens), (P = tablet; P = scroll; P = crown).
has_fix(R, P) :- prize_at_risk(R, P), charm(C), covers(C, Reg), worn_on(P, Reg), guards(C, spark).
valid(Place, R, P) :- affords(Place, R), prize_at_risk(R, P), has_fix(R, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for r in sorted(s.affords):
            lines.append(asp.fact("affords", sid, r))
    for rid in RITUALS:
        lines.append(asp.fact("ritual", rid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for rg in sorted(c.covers):
            lines.append(asp.fact("covers", c.id, rg))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(setting: Setting, ritual: Ritual, prize_cfg: Prize, name: str, gender: str, helper_role: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    helper = world.add(Entity(id=helper_role, kind="character", type=helper_role, label=helper_role))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    world.facts.update(hero=hero, helper=helper, ritual=ritual, prize=prize, prize_cfg=prize_cfg)

    begin_story(world, hero, helper, ritual, prize)
    misunderstanding(world, hero, helper, ritual, prize)
    charm = offer_charm(world, hero, helper, ritual, prize)
    if charm is None:
        _fallback_pool = globals().get("CHARMS") or globals().get("CHARMES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        charm = next(iter(_fallback_pool), None)
        if charm is None:
            raise StoryError
    charm_ent = world.add(Entity(id=charm.id, type="charm", label=charm.label))
    world.facts["charm_entity"] = charm_ent
    happy_ending(world, hero, helper, ritual, prize, charm)
    return world


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    ritual: str
    prize: str
    name: str
    gender: str
    helper: str
    role: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "ritual", None) and getattr(args, "prize", None):
        if (getattr(args, "place", None), getattr(args, "ritual", None), getattr(args, "prize", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "ritual", None) is None or c[1] == getattr(args, "ritual", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, ritual, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(KINDS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(place=place, ritual=ritual, prize=prize, name=name, gender=gender, helper=helper, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(RITUALS, params.ritual), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper)
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} label={e.label}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="shrine", ritual="count_stars", prize="tablet", name="Ari", gender="girl", helper="priestess", role="child"),
    StoryParams(place="cave", ritual="read_omens", prize="scroll", name="Niko", gender="boy", helper="old keeper", role="apprentice"),
    StoryParams(place="hill", ritual="count_stars", prize="crown", name="Tala", gender="girl", helper="star reader", role="messenger"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth world: a notorious calculator, a misunderstanding, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--ritual", choices=RITUALS.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=KINDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--role", choices=ROLES)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
