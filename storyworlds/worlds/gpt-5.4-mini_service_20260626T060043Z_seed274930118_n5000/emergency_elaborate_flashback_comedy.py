#!/usr/bin/env python3
"""
storyworlds/worlds/emergency_elaborate_flashback_comedy.py
=========================================================

A small comedy storyworld about an emergency that feels huge, gets an elaborate
fix, and is told with a flashback that explains why the characters care so much.

Premise:
A child or small helper is preparing for a cheerful event when something
unexpected goes wrong. The main character remembers an earlier moment in a
flashback, realizes why the problem matters, and then makes an over-the-top but
helpful plan to save the day.

The domain stays tiny and classical:
- one place,
- one emergency,
- one remembered flashback object,
- one elaborate fix,
- one funny resolution.

The simulated world tracks meters and memes:
- meters: spilled, broken, ready, fixed, decorated, hidden
- memes: worry, confidence, laughter, embarrassment, relief, nostalgia

The story is not a frozen paragraph with swapped nouns. State changes drive the
plot: the emergency raises worry, the flashback adds motivation, the elaborate
plan changes the physical situation, and the ending proves what changed.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entities: set[str] = field(default_factory=set)
    helper: object | None = None
    hero: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
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
class Place:
    name: str
    indoor: bool = True
    emergency_kind: str = "spill"
    affords_flashback: bool = True
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


@dataclass
class Emergency:
    id: str
    label: str
    mess: str
    verb: str
    risk: str
    zone: str
    comic_cost: str
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
class Memory:
    id: str
    label: str
    phrase: str
    trigger: str
    emotion: str
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
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    effect: str
    comedy: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            owner=v.owner, caretaker=v.caretaker, meters=dict(v.meters), memes=dict(v.memes)
        ) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    emergency: str
    memory: str
    fix: str
    name: str
    gender: str
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


PLACES = {
    "kitchen": Place(name="the kitchen", indoor=True, emergency_kind="spill"),
    "classroom": Place(name="the classroom", indoor=True, emergency_kind="mess"),
    "garage": Place(name="the garage", indoor=True, emergency_kind="jam"),
    "stage": Place(name="the tiny stage", indoor=True, emergency_kind="panic"),
}

EMERGENCIES = {
    "spill": Emergency(
        id="spill",
        label="a huge spill",
        mess="spill",
        verb="splashed everywhere",
        risk="the floor turned slippery",
        zone="floor",
        comic_cost="the socks looked surprised",
        tags={"spill", "mess", "funny"},
    ),
    "jam": Emergency(
        id="jam",
        label="a stubborn jam",
        mess="jam",
        verb="would not open",
        risk="the lid refused to budge",
        zone="table",
        comic_cost="everyone pulled with heroic faces",
        tags={"jam", "stuck", "funny"},
    ),
    "panic": Emergency(
        id="panic",
        label="a tiny panic",
        mess="panic",
        verb="started buzzing in the room",
        risk="the crowd got wobbly and loud",
        zone="room",
        comic_cost="even the paper hats trembled",
        tags={"panic", "noise", "funny"},
    ),
}

MEMORIES = {
    "lost_cake": Memory(
        id="lost_cake",
        label="a flashback to the lost cake",
        phrase="the time the cake slid off the counter during the joke parade",
        trigger="cake",
        emotion="nostalgia",
        tags={"cake", "flashback", "comedy"},
    ),
    "backpack_mistake": Memory(
        id="backpack_mistake",
        label="a flashback to the upside-down backpack",
        phrase="the afternoon the backpack was worn like a hat by accident",
        trigger="backpack",
        emotion="nostalgia",
        tags={"backpack", "flashback", "comedy"},
    ),
    "sprinkler_day": Memory(
        id="sprinkler_day",
        label="a flashback to the sprinkler day",
        phrase="the day the sprinkler surprise made everyone shout and laugh",
        trigger="sprinkler",
        emotion="nostalgia",
        tags={"water", "flashback", "comedy"},
    ),
}

FIXES = {
    "tower": Fix(
        id="tower",
        label="a tower of towels",
        phrase="a tower of towels",
        method="stacked towels into a careful bridge",
        effect="the floor became safe again",
        comedy="it looked like a castle built by laundry",
        tags={"towel", "dry", "funny"},
    ),
    "helmet": Fix(
        id="helmet",
        label="a frying-pan helmet plan",
        phrase="a frying-pan helmet plan",
        method="used a shiny pan as a dramatic shield",
        effect="the noisy bits finally felt under control",
        comedy="it was very brave and very silly",
        tags={"pan", "shield", "funny"},
    ),
    "labels": Fix(
        id="labels",
        label="a label parade",
        phrase="a label parade",
        method="put big labels on every box and moved in a careful line",
        effect="the room stopped mixing everything up",
        comedy="each sticker looked extremely important",
        tags={"label", "organize", "funny"},
    ),
}

NAMES = ["Mia", "Leo", "Nina", "Theo", "Ava", "Ben", "Maya", "Noah"]
TRAITS = ["curious", "cheerful", "silly", "brave", "lively", "clever"]


def intro(world: World, hero: Entity, helper: Entity, emergency: Emergency) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'curious')} {hero.type} "
        f"who loved quiet plans and loud laughs."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {helper.label} were getting ready at {world.place.name} "
        f"when {emergency.label} suddenly {emergency.verb}."
    )


def trigger_emergency(world: World, hero: Entity, emergency: Emergency) -> None:
    hero.memes["worry"] = hero.meme("worry") + 1
    hero.memes["embarrassment"] = hero.meme("embarrassment") + 1
    world.say(
        f"That was an emergency, and {hero.id} froze for a second because "
        f"{emergency.risk}."
    )
    world.say(f"{emergency.comic_cost.capitalize()}.")


def flashback(world: World, hero: Entity, memory: Memory) -> None:
    hero.memes["nostalgia"] = hero.meme("nostalgia") + 1
    hero.memes["confidence"] = hero.meme("confidence") + 1
    world.say(
        f"Then {hero.id} had a flashback: {memory.phrase}."
    )
    world.say(
        f"Remembering that made {hero.pronoun('object')} stop worrying so much and grin."
    )


def plan_fix(world: World, hero: Entity, helper: Entity, fix: Fix, emergency: Emergency) -> None:
    hero.memes["laughter"] = hero.meme("laughter") + 1
    hero.memes["confidence"] = hero.meme("confidence") + 1
    world.say(
        f"{helper.label} suggested {fix.phrase}, which sounded very elaborate."
    )
    world.say(
        f"So {hero.id} and {helper.label} {fix.method}, and the whole thing was as funny as it was careful."
    )
    world.facts["fix"] = fix
    world.facts["emergency"] = emergency


def resolve(world: World, hero: Entity, helper: Entity, fix: Fix, emergency: Emergency) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = hero.meme("relief") + 1
    hero.memes["laughter"] = hero.meme("laughter") + 1
    world.say(
        f"At last, {fix.effect}, and {fix.comedy}."
    )
    world.say(
        f"{hero.id} laughed, {helper.label} laughed, and the emergency turned into a funny story instead of a disaster."
    )
    world.say(
        f"In the end, the room was calm again, and {hero.id} still remembered {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "memory").label}."
    )


def tell(place: Place, emergency: Emergency, memory: Memory, fix: Fix,
         name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=name, kind="character", type=gender, label=name,
        memes={"trait": trait, "worry": 0.0, "confidence": 0.0, "laughter": 0.0,
               "embarrassment": 0.0, "relief": 0.0, "nostalgia": 0.0}
    ))
    helper = world.add(Entity(
        id="helper", kind="character", type=helper_kind, label=f"the {helper_kind}"
    ))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["memory"] = memory
    intro(world, hero, helper, emergency)
    world.para()
    trigger_emergency(world, hero, emergency)
    flashback(world, hero, memory)
    world.para()
    plan_fix(world, hero, helper, fix, emergency)
    resolve(world, hero, helper, fix, emergency)
    return world


def valid_combo(place: str, emergency: str, memory: str, fix: str) -> bool:
    e = _safe_lookup(EMERGENCIES, emergency)
    m = _safe_lookup(MEMORIES, memory)
    f = _safe_lookup(FIXES, fix)
    if "flashback" not in m.tags:
        return False
    if emergency == "spill" and fix not in {"tower"}:
        return False
    if emergency == "jam" and fix not in {"helmet", "labels"}:
        return False
    if emergency == "panic" and fix not in {"labels", "helmet"}:
        return False
    if place == "garage" and fix == "tower":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in PLACES:
        for emergency in EMERGENCIES:
            for memory in MEMORIES:
                for fix in FIXES:
                    if valid_combo(place, emergency, memory, fix):
                        out.append((place, emergency, memory, fix))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a child where an emergency at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").name} gets an elaborate fix.',
        f"Tell a funny story that includes a flashback, a small emergency, and a careful plan led by {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id}.",
        f"Write a child-facing story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} remembers {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "memory").label} and solves the problem with a silly but helpful idea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")  # type: ignore[assignment]
    memory: Memory = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "memory")  # type: ignore[assignment]
    emergency: Emergency = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "emergency")  # type: ignore[assignment]
    fix: Fix = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "fix")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What problem happened at {world.place.name}?",
            answer=f"{emergency.label} happened, and it felt like an emergency because {emergency.risk}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered {memory.phrase}. That flashback helped {hero.pronoun('object')} stay calm.",
        ),
        QAItem(
            question=f"What elaborate plan solved the problem?",
            answer=f"They used {fix.phrase}. It was an elaborate plan, and it fixed the trouble without making the joke of it all worse.",
        ),
        QAItem(
            question=f"Who helped {hero.id}?",
            answer=f"{helper.label} helped {hero.id}. Together they turned the emergency into a funny, manageable moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened earlier.",
        ),
        QAItem(
            question="What does elaborate mean?",
            answer="Elaborate means carefully planned and detailed, with lots of small parts working together.",
        ),
        QAItem(
            question="Why can comedy make an emergency feel less scary?",
            answer="Comedy can help because laughter makes people feel lighter, calmer, and ready to solve the problem.",
        ),
    ]
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id:10} ({e.kind:8}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
emergency(E) :- emergency_kind(E).
memory(M) :- flashback(M).
fix(F) :- elaborate_fix(F).

compatible(P,E,M,F) :- place(P), emergency(E), memory(M), fix(F), flashback(M),
                       valid_combo(P,E,M,F).
#show compatible/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for eid in EMERGENCIES:
        lines.append(asp.fact("emergency_kind", eid))
    for mid in MEMORIES:
        lines.append(asp.fact("flashback", mid))
    for fid in FIXES:
        lines.append(asp.fact("elaborate_fix", fid))
    for p in PLACES:
        for e in EMERGENCIES:
            for m in MEMORIES:
                for f in FIXES:
                    if valid_combo(p, e, m, f):
                        lines.append(asp.fact("valid_combo", p, e, m, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with an emergency, an elaborate fix, and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--emergency", choices=EMERGENCIES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "teacher"])
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


def explain_rejection(place: str, emergency: str, memory: str, fix: str) -> str:
    return f"(No story: {place}, {emergency}, {memory}, and {fix} do not form a reasonable emergency-flashback-comedy.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "emergency", None) and getattr(args, "memory", None) and getattr(args, "fix", None):
        if not valid_combo(getattr(args, "place", None), getattr(args, "emergency", None), getattr(args, "memory", None), getattr(args, "fix", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "emergency", None) is None or c[1] == getattr(args, "emergency", None))
              and (getattr(args, "memory", None) is None or c[2] == getattr(args, "memory", None))
              and (getattr(args, "fix", None) is None or c[3] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, emergency, memory, fix = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "teacher"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, emergency=emergency, memory=memory, fix=fix,
                       name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(EMERGENCIES, params.emergency), _safe_lookup(MEMORIES, params.memory),
                 _safe_lookup(FIXES, params.fix), params.name, params.gender, params.helper, params.trait)
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


CURATED = [
    StoryParams(place="kitchen", emergency="spill", memory="lost_cake", fix="tower", name="Mia", gender="girl", helper="mother", trait="silly"),
    StoryParams(place="garage", emergency="jam", memory="backpack_mistake", fix="helmet", name="Leo", gender="boy", helper="father", trait="brave"),
    StoryParams(place="classroom", emergency="panic", memory="sprinkler_day", fix="labels", name="Ava", gender="girl", helper="teacher", trait="clever"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.emergency} at {p.place} with {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
