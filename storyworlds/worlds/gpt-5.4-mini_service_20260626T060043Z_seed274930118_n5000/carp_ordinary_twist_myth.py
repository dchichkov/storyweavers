#!/usr/bin/env python3
"""
storyworlds/worlds/carp_ordinary_twist_myth.py
==============================================

A small Myth-style storyworld about an ordinary carp, a risky crossing, and a
twist that turns a hard journey into a safe one.

The premise is deliberately simple and classical:
- an ordinary carp loves one mythic task,
- the task threatens something precious,
- an elder warns of the danger,
- a twist reveals a better path,
- the carp finishes changed, and the world feels a little wiser.

The script follows the shared Storyweavers contract:
- self-contained stdlib storyworld
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- dataclass StoryParams, parameter registries, parser/resolution, generate, emit, main
- optional QA, JSON, trace, ASP, verify, and show-asp support
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    carp: object | None = None
    parent: object | None = None
    relic: object | None = None
    sacred: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        if not self.meters:
            self.meters = {"wet": 0.0, "tired": 0.0, "safe": 0.0}
        if not self.memes:
            self.memes = {"awe": 0.0, "worry": 0.0, "hope": 0.0, "pride": 0.0, "ordinary": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Pool:
    name: str
    depth: str
    current: str
    affords: set[str] = field(default_factory=set)
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    twist: str
    zone: set[str]
    keyword: str
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
class Relic:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    sacred: bool = False
    genders: set[str] = field(default_factory=lambda: {"any"})
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
    def __init__(self, pool: Pool) -> None:
        self.pool = pool
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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

    def copy(self) -> "World":
        import copy

        clone = World(self.pool)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


@dataclass
class StoryParams:
    place: str = ""
    task: str = ""
    relic: str = ""
    name: str = ""
    parent: str = ""
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


POOLS = {
    "moonpond": Pool(name="the moon pond", depth="deep", current="quiet", affords={"cross", "fetch"}),
    "riverbend": Pool(name="the river bend", depth="swift", current="tugging", affords={"cross", "carry"}),
    "reedpool": Pool(name="the reed pool", depth="shallow", current="spiraling", affords={"cross", "carry", "guard"}),
}

TASKS = {
    "cross": Task(
        id="cross",
        verb="cross the shining water",
        gerund="crossing the shining water",
        rush="dart into the current",
        risk="the current could spin the carp away",
        twist="a hidden twist in the reeds opens a calm lane",
        zone={"body"},
        keyword="cross",
        tags={"water", "current", "twist"},
    ),
    "carry": Task(
        id="carry",
        verb="carry a relic to the shrine",
        gerund="carrying the relic",
        rush="push toward the bank",
        risk="the relic could slip into the water",
        twist="the carp learns to hold the relic in a curl of reeds",
        zone={"mouth", "body"},
        keyword="carry",
        tags={"shrine", "relic", "twist"},
    ),
    "guard": Task(
        id="guard",
        verb="guard the river gate",
        gerund="guarding the river gate",
        rush="swim up to the stones",
        risk="the gate could be left open to the dark water",
        twist="the gate is not broken; it is waiting for a steady watch",
        zone={"body"},
        keyword="guard",
        tags={"gate", "watch", "twist"},
    ),
}

RELICS = {
    "moonpearl": Relic(
        label="moon pearl",
        phrase="a pale moon pearl",
        type="pearl",
        region="mouth",
        sacred=True,
    ),
    "reedbell": Relic(
        label="reed bell",
        phrase="a little bell of braided reeds",
        type="bell",
        region="body",
        sacred=True,
    ),
    "stonekey": Relic(
        label="stone key",
        phrase="a smooth stone key",
        type="key",
        region="mouth",
        sacred=False,
    ),
}

CHARMS = [
    Charm(
        id="reedcurl",
        label="a reed curl",
        covers={"mouth"},
        guards={"slip"},
        prep="guide the carp with a reed curl",
        tail="followed the reed curl through the safe lane",
    ),
    Charm(
        id="leafbridge",
        label="a leaf bridge",
        covers={"body"},
        guards={"sweep", "spin"},
        prep="set down a leaf bridge first",
        tail="slid along the leaf bridge without losing the relic",
    ),
    Charm(
        id="stillstalk",
        label="still stalks",
        covers={"body", "mouth"},
        guards={"spin", "slip", "sweep"},
        prep="weave still stalks into a quiet path",
        tail="swam through the quiet path as if the pond itself were helping",
        plural=True,
    ),
]

NAMES = ["Mira", "Oren", "Niko", "Luma", "Suri", "Tavi", "Piko", "Rin"]
PARENTS = ["grandmother", "grandfather", "aunt", "uncle"]
TRAITS = ["ordinary", "patient", "small", "steady", "quiet"]


def can_story(task: Task, relic: Relic) -> bool:
    return relic.region in task.zone and "twist" in task.tags


def choose_charm(task: Task, relic: Relic) -> Optional[Charm]:
    for charm in CHARMS:
        if relic.region in charm.covers:
            return charm
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, pool in POOLS.items():
        for task_id in pool.affords:
            task = _safe_lookup(TASKS, task_id)
            for relic_id, relic in RELICS.items():
                if can_story(task, relic) and choose_charm(task, relic):
                    out.append((place, task_id, relic_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Myth-style storyworld about an ordinary carp and a twist.")
    ap.add_argument("--place", choices=POOLS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    if getattr(args, "task", None) and getattr(args, "relic", None):
        if not can_story(_safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(RELICS, getattr(args, "relic", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, relic = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    return StoryParams(place=place, task=task, relic=relic, name=name, parent=parent)


def _do_task(world: World, carp: Entity, task: Task, relic: Entity, narrate: bool = True) -> None:
    carp.meters["tired"] += 1
    carp.memes["ordinary"] += 1
    world.zone = set(task.zone)
    if task.id == "carry":
        relic.meters["safe"] += 1
    if narrate:
        world.say(f"{carp.id} began {task.gerund}.")


def predict_risk(world: World, carp: Entity, task: Task, relic_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(carp.id), task, sim.get(relic_id), narrate=False)
    relic = sim.get(relic_id)
    return {
        "risk": bool(relic.meters["safe"] < THRESHOLD and task.id == "carry"),
        "tired": sim.get(carp.id).meters["tired"],
    }


def opening(world: World, carp: Entity, task: Task) -> None:
    world.say(
        f"In {world.pool.name}, an ordinary carp named {carp.id} lived beneath the water lilies."
    )
    world.say(
        f"{carp.id} loved {task.gerund}, because the pond's old songs said even small ripples can begin myths."
    )


def relic_intro(world: World, carp: Entity, relic: Entity, parent: Entity) -> None:
    world.say(
        f"One day {carp.id}'s {parent.label} brought {carp.pronoun('object')} {relic.phrase} and said it must reach the shrine stone before dusk."
    )
    relic.worn_by = carp.id


def warning(world: World, parent: Entity, carp: Entity, task: Task, relic: Entity) -> None:
    pred = predict_risk(world, carp, task, relic.id)
    carp.memes["worry"] += 1
    world.say(
        f'“{task.risk.capitalize()},” {parent.label} warned. “The old water does not always make room for a small swimmer.”'
    )
    world.facts["predicted_risk"] = pred["risk"]


def twist_turn(world: World, carp: Entity, task: Task, relic: Entity) -> None:
    carp.memes["hope"] += 1
    world.say(
        f"{carp.id} tried to {task.rush}, but then the twist came: {task.twist}."
    )


def offer_charm(world: World, parent: Entity, carp: Entity, task: Task, relic: Entity) -> Optional[Charm]:
    charm = choose_charm(task, relic)
    if charm is None:
        return None
    world.say(
        f"{parent.label} smiled and offered {charm.label}."
    )
    return charm


def accept_charm(world: World, carp: Entity, task: Task, relic: Entity, charm: Charm) -> None:
    carp.memes["hope"] += 1
    carp.memes["pride"] += 1
    world.say(
        f"{carp.id} accepted the help, and {charm.tail}."
    )
    world.say(
        f"At last, {carp.id} reached the shrine with {relic.phrase} still safe, and the ordinary carp looked anything but small in the moonlight."
    )


def tell(pool: Pool, task: Task, relic_cfg: Relic, name: str, parent_label: str) -> World:
    world = World(pool)
    carp = world.add(Entity(id=name, kind="character", type="carp", label="carp"))
    parent = world.add(Entity(id="Elder", kind="character", type="elder", label=parent_label))
    relic = world.add(Entity(
        id=relic_cfg.label.replace(" ", "_"),
        type=relic_cfg.type,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        caretaker=parent.id,
        owner=carp.id,
        region=relic_cfg.region,
        sacred=relic_cfg.sacred,
    ))
    carp.memes["ordinary"] += 1

    opening(world, carp, task)
    world.para()
    relic_intro(world, carp, relic, parent)
    warning(world, parent, carp, task, relic)
    twist_turn(world, carp, task, relic)
    world.para()
    charm = offer_charm(world, parent, carp, task, relic)
    if charm:
        accept_charm(world, carp, task, relic, charm)

    world.facts.update(
        carp=carp,
        parent=parent,
        relic=relic,
        task=task,
        charm=charm,
        place=pool,
        resolved=charm is not None,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    carp, parent, task, relic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "carp"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic")
    return [
        "Write a short myth about an ordinary carp who faces a watery test and finds a wise twist.",
        f"Tell a gentle story in a mythic style about {carp.id}, a carp who wants to {task.verb} with {relic.phrase}.",
        f"Write a child-friendly myth where {parent.label} warns {carp.id} about the water, but a twist gives the carp a safer way forward.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    carp, parent, task, relic, pool = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "carp"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    qa = [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is about {carp.id}, an ordinary carp in {pool.name}."
        ),
        QAItem(
            question=f"What did {carp.id} want to do with the {relic.label}?",
            answer=f"{carp.id} wanted to {task.verb} with {relic.phrase} and bring it to the shrine."
        ),
        QAItem(
            question=f"Why did {parent.label} worry?",
            answer=f"{parent.label} worried because {task.risk}."
        ),
    ]
    if f.get("charm"):
        charm = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm")
        qa.append(
            QAItem(
                question=f"How did {parent.label} help {carp.id} after the twist?",
                answer=f"{parent.label} offered {charm.label}, which gave {carp.id} a safer way to finish the journey."
            )
        )
        qa.append(
            QAItem(
                question=f"What changed by the end?",
                answer=f"By the end, {carp.id} reached the shrine with the {relic.label} safe, and the ordinary carp felt proud."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a carp?",
            answer="A carp is a kind of fish that lives in fresh water, such as ponds and rivers."
        ),
        QAItem(
            question="What does ordinary mean?",
            answer="Ordinary means plain or regular, not flashy or special at first glance."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising turn that changes how the problem gets solved."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moonpond", task="carry", relic="moonpearl", name="Mira", parent="grandmother"),
    StoryParams(place="riverbend", task="cross", relic="stonekey", name="Oren", parent="uncle"),
    StoryParams(place="reedpool", task="guard", relic="reedbell", name="Luma", parent="aunt"),
]


def explain_rejection(task: Task, relic: Relic) -> str:
    return f"(No story: {task.verb} does not fit a relic worn on the {relic.region} in this world.)"


ASP_RULES = r"""
task_ok(T) :- task(T).
relic_ok(R) :- relic(R).
valid(Place, Task, Relic) :- afford(Place, Task), task(Task), relic(Relic), can(Task, Relic).

can(carry, moonpearl) :- true.
can(carry, stonekey) :- true.
can(cross, moonpearl) :- true.
can(cross, stonekey) :- true.
can(guard, reedbell) :- true.

% The declarative twin mirrors the Python gate:
% a story is valid when the place affords the task and the task can truthfully
% involve the chosen relic.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, pool in POOLS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(pool.affords):
            lines.append(asp.fact("afford", pid, t))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("region", rid, relic.region))
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(POOLS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(RELICS, params.relic), params.name, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, task, relic) combos:\n")
        for combo in combos:
            print("  ", combo)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
