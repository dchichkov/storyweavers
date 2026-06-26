#!/usr/bin/env python3
"""
storyworlds/worlds/flood_sail_wonky_humor_suspense_slice_of.py
==============================================================

A small slice-of-life story world about a child, a flood, a wonky sail, and a
careful little repair that turns worry into laughter.

The premise is intentionally modest: something in a home or yard starts to flood,
a child wants to use a small sailboat or sail toy, the sail goes wonky, and the
family finds a practical fix that makes the day feel safe again. The world model
tracks physical state (meters) and feelings (memes) so the prose follows the
simulation rather than a fixed template.

This file is standalone and uses only stdlib, plus the shared result containers
from storyworlds/results.py. ASP support is inline and imported lazily only when
needed.
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
# Domain registries
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

@dataclass
class Setting:
    id: str
    place: str
    indoor: bool
    flood_source: str
    flood_word: str
    afford_sailing: bool = False
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
class Boat:
    id: str
    label: str
    phrase: str
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
class Sail:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
    tail: str = ""
    prep: str = ""
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
class FloodEvent:
    id: str
    mess: str
    danger: str
    splash_zone: set[str]
    sound: str
    weather: str
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


SETTINGS = {
    "back_porch": Setting(
        id="back_porch",
        place="the back porch",
        indoor=False,
        flood_source="the drain",
        flood_word="spilling water",
        afford_sailing=True,
    ),
    "laundry_room": Setting(
        id="laundry_room",
        place="the laundry room",
        indoor=True,
        flood_source="the washing machine",
        flood_word="spilling water",
        afford_sailing=True,
    ),
    "garden_path": Setting(
        id="garden_path",
        place="the garden path",
        indoor=False,
        flood_source="the hose",
        flood_word="rushing water",
        afford_sailing=True,
    ),
}

BOATS = {
    "toy_boat": Boat(
        id="toy_boat",
        label="toy boat",
        phrase="a little toy boat with a blue stripe",
    ),
    "paper_boat": Boat(
        id="paper_boat",
        label="paper boat",
        phrase="a folded paper boat",
    ),
    "bowl_boat": Boat(
        id="bowl_boat",
        label="bowl boat",
        phrase="a tiny bowl boat made from a cereal bowl",
    ),
}

SAILS = {
    "cloth_sail": Sail(
        id="cloth_sail",
        label="cloth sail",
        phrase="a small cloth sail",
        guards={"wet"},
        fixes={"wonky"},
        tail="smoothed the cloth sail and tied it tight",
        prep="straighten the cloth sail",
    ),
    "paper_sail": Sail(
        id="paper_sail",
        label="paper sail",
        phrase="a folded paper sail",
        guards={"light"},
        fixes={"wonky"},
        tail="re-folded the paper sail so it stood up better",
        prep="refold the paper sail",
    ),
    "stick_sail": Sail(
        id="stick_sail",
        label="stick sail",
        phrase="a little sail on a stick",
        guards={"wonky"},
        fixes={"wonky"},
        tail="taped the stick sail in place",
        prep="steady the stick sail",
    ),
}

FLOODS = {
    "leak": FloodEvent(
        id="leak",
        mess="wet",
        danger="damp",
        splash_zone={"feet", "legs"},
        sound="drip-drip",
        weather="rainy",
    ),
    "spill": FloodEvent(
        id="spill",
        mess="wet",
        danger="slippery",
        splash_zone={"feet", "legs", "hands"},
        sound="splash-splash",
        weather="cloudy",
    ),
    "overflow": FloodEvent(
        id="overflow",
        mess="wet",
        danger="swirly",
        splash_zone={"feet", "legs", "hands"},
        sound="glug-glug",
        weather="stormy",
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Lily", "Eli", "Nina", "Theo", "Iris", "Ben"]
PARENT_NAMES = ["Mom", "Dad", "Aunt Jo", "Uncle Sam"]
TRAITS = ["curious", "gentle", "silly", "patient", "bright", "careful"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    flood: str
    boat: str
    sail: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    boat: object | None = None
    child: object | None = None
    parent: object | None = None
    sail: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


THRESHOLD = 1.0


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def rule_slip(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if _meter(e, "wet") < THRESHOLD:
            continue
        sig = ("slip", e.id)
        if sig in world.fired:
            continue
        if world.setting.id == "laundry_room":
            e.memes["suspense"] = _meme(e, "suspense") + 1
            out.append(f"The floor looked slippery, and everyone took a smaller step.")
        world.fired.add(sig)
    return out


def rule_wonky_sail(world: World) -> list[str]:
    out: list[str] = []
    boat = world.entities.get("boat")
    sail = world.entities.get("sail")
    if not boat or not sail:
        return out
    if sail.props.get("shape") != "wonky":
        return out
    sig = ("wonky",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boat.memes["suspense"] = _meme(boat, "suspense") + 1
    out.append(f"The sail leaned sideways, so the little boat kept wobbling in place.")
    return out


def rule_laugh(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if _meme(child, "humor") < THRESHOLD:
        return out
    sig = ("laugh", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"{child.id} giggled, because the boat looked a little too proud of its wobbly sail.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (rule_slip, rule_wonky_sail, rule_laugh):
            produced = rule(world)
            if produced:
                changed = True
                lines.extend(produced)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def intro(world: World, child: Entity, parent: Entity, flood: FloodEvent) -> None:
    world.say(
        f"{child.id} was a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "trait")} little {child.type} who liked quiet play near {world.setting.place}."
    )
    world.say(
        f"That day, {world.setting.flood_source} made {flood.sound} sounds, and water kept {world.setting.flood_word} along the edge."
    )


def setup(world: World, child: Entity, parent: Entity, boat: Entity, sail: Entity) -> None:
    boat.meters["ready"] = 1
    sail.meters["ready"] = 1
    world.say(
        f"{child.id} had {boat.phrase}, and {child.pronoun('possessive')} {parent.type if parent.type else 'parent'} had {sail.phrase} ready in a basket."
    )
    world.say(
        f"{child.id} loved watching the tiny boat sail, even when the breeze made things a little wonky."
    )


def worry(world: World, child: Entity, parent: Entity, flood: FloodEvent, boat: Entity) -> None:
    child.memes["want"] = _meme(child, "want") + 1
    child.memes["suspense"] = _meme(child, "suspense") + 1
    world.say(
        f"{child.id} wanted to send the boat across the floodwater, but the water kept sliding close to the floor boards."
    )
    world.say(
        f"{child.pronoun().capitalize()} looked at the little boat and wondered if it would tip over."
    )


def caution(world: World, parent: Entity, child: Entity, flood: FloodEvent, boat: Entity) -> None:
    child.memes["fear"] = _meme(child, "fear") + 1
    world.say(
        f'"Careful," said {parent.id}, "the water can carry {boat.label} away if we do not guide it."'
    )


def make_wonky(world: World, child: Entity, sail: Entity) -> None:
    sail.props["shape"] = "wonky"
    child.memes["humor"] = _meme(child, "humor") + 1
    child.memes["suspense"] = _meme(child, "suspense") + 1
    world.say(
        f"{child.id} pinned the sail on, but it came out wonky, with one corner sticking up like a surprised ear."
    )


def fix_sail(world: World, child: Entity, parent: Entity, sail: Entity) -> None:
    if sail.props.get("shape") != "wonky":
        return
    child.memes["joy"] = _meme(child, "joy") + 1
    child.memes["humor"] = _meme(child, "humor") + 1
    sail.props["shape"] = "straight"
    world.say(
        f"{parent.id} smiled and helped {child.id} {_safe_lookup(SAILS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "sail")).prep}, and the tiny sail stood up straight at last."
    )
    world.say(
        f"Then the boat moved forward in a neat little line, as if it had finally remembered where to go."
    )


def ending(world: World, child: Entity, parent: Entity, boat: Entity, sail: Entity) -> None:
    world.say(
        f"{child.id} laughed at the funny little sail, and {parent.id} laughed too."
    )
    world.say(
        f"By the end, the flood was still there, but the boat was floating gently, and the wonky moment had turned into a happy one."
    )


# ---------------------------------------------------------------------------
# World building
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    flood = _safe_lookup(FLOODS, params.flood)
    boat_def = _safe_lookup(BOATS, params.boat)
    sail_def = _safe_lookup(SAILS, params.sail)

    world = World(setting)
    child_type = "girl" if params.name in {"Mia", "Lily", "Nina", "Iris"} else "boy"
    parent_type = "mother" if params.parent == "Mom" else "father"
    child = world.add(Entity(id=params.name, kind="character", type=child_type))
    parent = world.add(Entity(id=params.parent, kind="character", type=parent_type))
    boat = world.add(Entity(id="boat", label=boat_def.label, phrase=boat_def.phrase))
    sail = world.add(Entity(id="sail", label=sail_def.label, phrase=sail_def.phrase))

    world.facts.update(
        child=child,
        parent=parent,
        boat=boat,
        sail=sail,
        flood=flood,
        trait=params.trait,
        setting=setting,
    )

    intro(world, child, parent, flood)
    setup(world, child, parent, boat, sail)

    world.para()
    worry(world, child, parent, flood, boat)
    caution(world, parent, child, flood, boat)
    world.zone = set(flood.splash_zone)
    child.meters["wet"] = 1
    propagate(world, narrate=True)

    world.para()
    make_wonky(world, child, sail)
    propagate(world, narrate=True)
    fix_sail(world, child, parent, sail)
    ending(world, child, parent, boat, sail)
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(setting: Setting, flood: FloodEvent, boat: Boat, sail: Sail) -> bool:
    if not setting.afford_sailing:
        return False
    if "wonky" not in sail.fixes:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for fid, f in FLOODS.items():
            for bid, b in BOATS.items():
                for sail_id, sail in SAILS.items():
                    if valid_combo(s, f, b, sail):
                        out.append((sid, fid, bid, sail_id))
    return out


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    flood: FloodEvent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "flood")
    return [
        f"Write a short slice-of-life story for a young child named {child.id} about a flood and a wonky sail.",
        f"Tell a gentle humorous story where {child.id} and {parent.id} try to sail a tiny boat while water is pooling nearby.",
        f"Write a story that includes a funny wonky sail, a little suspense, and a calm family fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    boat: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "boat")
    sail: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sail")
    flood: FloodEvent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "flood")

    return [
        QAItem(
            question=f"What did {child.id} want to do with the {boat.label}?",
            answer=f"{child.id} wanted to sail the little {boat.label} across the floodwater.",
        ),
        QAItem(
            question=f"Why was the day a little suspenseful near {world.setting.place}?",
            answer=f"It was suspenseful because water was pooling from {world.setting.flood_source}, and everyone had to be careful not to slip or tip the boat.",
        ),
        QAItem(
            question=f"What was funny about the sail?",
            answer=f"The sail turned out wonky, with one corner sticking up funny before {parent.id} helped fix it.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the sail fixed, the boat floating gently, and {child.id} and {parent.id} laughing together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "flood": [
        QAItem(
            question="What is a flood?",
            answer="A flood is when too much water covers a place that is usually dry.",
        )
    ],
    "sail": [
        QAItem(
            question="What does a sail do?",
            answer="A sail catches air and helps a boat move along.",
        )
    ],
    "wonky": [
        QAItem(
            question="What does wonky mean?",
            answer="Wonky means crooked, uneven, or not quite straight.",
        )
    ],
    "wet": [
        QAItem(
            question="Why do wet floors need care?",
            answer="Wet floors can be slippery, so people walk slowly and carefully on them.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"flood", "sail", "wonky", "wet"}
    out: list[QAItem] = []
    for tag in ("flood", "sail", "wonky", "wet"):
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


# ---------------------------------------------------------------------------
# ASP support
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- setting_fact(S).
flood(F) :- flood_fact(F).
boat(B) :- boat_fact(B).
sail(Sl) :- sail_fact(Sl).

valid_story(Setting, Flood, Boat, Sail) :-
    setting_fact(Setting),
    flood_fact(Flood),
    boat_fact(Boat),
    sail_fact(Sail),
    afford_sailing(Setting),
    can_fix_wonky(Sail).

has_wonky_fix(S) :- sail_fact(S), fixes(S, wonky).
can_fix_wonky(S) :- has_wonky_fix(S).
#show valid_story/4.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        if s.afford_sailing:
            lines.append(asp.fact("afford_sailing", sid))
    for fid, f in FLOODS.items():
        lines.append(asp.fact("flood_fact", fid))
        lines.append(asp.fact("mess_of", fid, f.mess))
    for bid, b in BOATS.items():
        lines.append(asp.fact("boat_fact", bid))
    for sid, s in SAILS.items():
        lines.append(asp.fact("sail_fact", sid))
        for fx in sorted(s.fixes):
            lines.append(asp.fact("fixes", sid, fx))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(clingo_model, "valid_story"))
    if py == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python valid_combos():")
    print("  only in python:", sorted(py - clingo_set))
    print("  only in clingo:", sorted(clingo_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life story world: flood, sail, wonky, humor, suspense."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--flood", choices=FLOODS)
    ap.add_argument("--boat", choices=BOATS)
    ap.add_argument("--sail", choices=SAILS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    flood = getattr(args, "flood", None) or rng.choice(list(FLOODS))
    boat = getattr(args, "boat", None) or rng.choice(list(BOATS))
    sail = getattr(args, "sail", None) or rng.choice(list(SAILS))
    if not valid_combo(_safe_lookup(SETTINGS, setting), _safe_lookup(FLOODS, flood), _safe_lookup(BOATS, boat), _safe_lookup(SAILS, sail)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, flood=flood, boat=boat, sail=sail, name=name, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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
    StoryParams(setting="back_porch", flood="leak", boat="toy_boat", sail="cloth_sail", name="Mia", parent="Mom", trait="curious"),
    StoryParams(setting="laundry_room", flood="spill", boat="paper_boat", sail="paper_sail", name="Noah", parent="Dad", trait="careful"),
    StoryParams(setting="garden_path", flood="overflow", boat="bowl_boat", sail="stick_sail", name="Lily", parent="Mom", trait="silly"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for row in stories:
            print(" ", row)
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
            header = f"### {p.name}: {p.flood} at {p.setting} (boat: {p.boat}, sail: {p.sail})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
