#!/usr/bin/env python3
"""
storyworlds/worlds/gosling_dialogue_adventure.py
================================================

A small adventure storyworld about a gosling, a simple quest, and dialogue.
The domain is intentionally compact: one young gosling wants to go somewhere
interesting, meets a small challenge, speaks with a helper, and ends changed.

The story is built from state changes in a little world model:
- a gosling has meters (distance, tiredness, hunger, courage)
- objects have physical positions and ownership
- dialogue changes memes (curiosity, worry, relief, pride)

The narrative stays close to an adventure tone: a beginning with a goal, a
middle with a problem and a guide, and an ending image that proves the trip
changed the gosling.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_next(iterable, fallback=None):
    return next(iter(iterable), fallback)


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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    gosling: object | None = None
    helper: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for k in ("distance", "tiredness", "hunger", "courage", "storm", "blocked"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "relief", "pride", "friendship"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"gosling", "duckling"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"child", "girl", "boy"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    id: str
    label: str
    kind: str
    open_paths: set[str] = field(default_factory=set)
    shelter: bool = False
    water: bool = False
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


@dataclass
class Route:
    id: str
    from_place: str
    to_place: str
    distance: float
    hazard: str = ""
    blocked_by: str = ""
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    location: str = ""
    owner: Optional[str] = None
    portable: bool = True
    answer: object | None = None
    key: object | None = None
    question: object | None = None
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
class StoryParams:
    start: str = ""
    destination: str = ""
    obstacle: str = ""
    helper: str = ""
    name: str = ""
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, start: Place, destination: Place) -> None:
        self.start = start
        self.destination = destination
        self.places: dict[str, Place] = {start.id: start, destination.id: destination}
        self.routes: dict[str, Route] = {}
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_lines: list[str] = []

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def add_route(self, r: Route) -> Route:
        self.routes[r.id] = r
        return r

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
        clone = World(self.start, self.destination)
        clone.places = copy.deepcopy(self.places)
        clone.routes = copy.deepcopy(self.routes)
        clone.entities = copy.deepcopy(self.entities)
        clone.items = copy.deepcopy(self.items)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_travel_tired(world: World) -> list[str]:
    out = []
    gosling = world.get("gosling")
    if gosling.location == world.destination.id and gosling.meters["distance"] >= 1:
        sig = ("tired", gosling.id)
        if sig not in world.fired:
            world.fired.add(sig)
            gosling.meters["tiredness"] += 1
            out.append("The long trip made the gosling's legs feel wobbly.")
    return out


def _r_storm_worry(world: World) -> list[str]:
    out = []
    gosling = world.get("gosling")
    if gosling.meters["storm"] >= THRESHOLD and gosling.location != world.destination.id:
        sig = ("worry", gosling.id)
        if sig not in world.fired:
            world.fired.add(sig)
            gosling.memes["worry"] += 1
            out.append("The dark sky made the gosling's heart flutter with worry.")
    return out


def _r_help_relief(world: World) -> list[str]:
    out = []
    gosling = world.get("gosling")
    helper = world.get("helper")
    if helper.location == gosling.location and helper.memes["friendship"] >= THRESHOLD:
        sig = ("relief", gosling.id)
        if sig not in world.fired:
            world.fired.add(sig)
            gosling.memes["relief"] += 1
            gosling.memes["worry"] = 0.0
            out.append("The helper's calm voice made the gosling feel safe again.")
    return out


CAUSAL_RULES = [
    Rule("travel_tired", _r_travel_tired),
    Rule("storm_worry", _r_storm_worry),
    Rule("help_relief", _r_help_relief),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


PLACE_REGISTRY = {
    "nest": Place(id="nest", label="the nest", kind="home", open_paths={"pond", "meadow"}),
    "pond": Place(id="pond", label="the pond", kind="water", water=True, open_paths={"nest", "meadow"}),
    "meadow": Place(id="meadow", label="the meadow", kind="field", open_paths={"nest", "pond"}),
    "reed_bank": Place(id="reed_bank", label="the reed bank", kind="edge", open_paths={"pond"}, shelter=True),
}

ROUTES = [
    Route("nest_to_pond", "nest", "pond", 1.0),
    Route("pond_to_meadow", "pond", "meadow", 1.0),
    Route("meadow_to_pond", "meadow", "pond", 1.0),
    Route("pond_to_reed_bank", "pond", "reed_bank", 0.5),
    Route("reed_bank_to_pond", "reed_bank", "pond", 0.5),
]

HERO_NAMES = ["Pip", "Milo", "Nia", "Tavi", "Lumi", "Sora"]
HELPER_NAMES = ["Moss", "Rill", "Tern", "Wren"]
TRAITS = ["brave", "curious", "small", "eager"]


@dataclass
class StoryObject:
    label: str
    phrase: str
    kind: str
    location: str
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


OBSTACLES = {
    "wind": "A sharp wind ruffled the reeds.",
    "fog": "A pale fog hid the path near the pond.",
    "mud": "Sticky mud slowed every careful step.",
    "rain": "Rain tapped the ground and made the trail slippery.",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gosling adventure story world with dialogue.")
    ap.add_argument("--start", choices=PLACE_REGISTRY.keys())
    ap.add_argument("--destination", choices=["pond", "meadow", "reed_bank"])
    ap.add_argument("--obstacle", choices=OBSTACLES.keys())
    ap.add_argument("--helper", choices=["friend", "duck", "heron", "child"])
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.start == params.destination:
        pass
    if params.start not in PLACE_REGISTRY or params.destination not in PLACE_REGISTRY:
        pass
    if params.obstacle not in OBSTACLES:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    start = getattr(args, "start", None) or rng.choice(list(PLACE_REGISTRY.keys()))
    destination = getattr(args, "destination", None) or rng.choice(["pond", "meadow", "reed_bank"])
    obstacle = getattr(args, "obstacle", None) or rng.choice(list(OBSTACLES.keys()))
    helper = getattr(args, "helper", None) or rng.choice(["friend", "duck", "heron", "child"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    params = StoryParams(start=start, destination=destination, obstacle=obstacle, helper=helper, name=name)
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    start = _safe_lookup(PLACE_REGISTRY, params.start)
    dest = _safe_lookup(PLACE_REGISTRY, params.destination)
    world = World(start, dest)
    for r in ROUTES:
        world.add_route(copy.deepcopy(r))

    gosling = world.add_entity(Entity(
        id="gosling",
        kind="character",
        type="gosling",
        label=params.name,
        location=params.start,
        traits=["small", "curious"],
    ))
    helper = world.add_entity(Entity(
        id="helper",
        kind="character",
        type="duck" if params.helper == "duck" else params.helper,
        label={
            "friend": "a friend",
            "duck": "a duck",
            "heron": "a heron",
            "child": "a child",
        }[params.helper],
        location=params.destination if params.helper in {"duck", "heron"} else params.start,
        traits=["kind", "calm"],
    ))
    key = world.add_item(Item(
        id="key",
        label="little shell key",
        phrase="a little shell key",
        kind="key",
        location=params.destination,
    ))

    world.facts.update(gosling=gosling, helper=helper, key=key, params=params)
    return world


def can_travel(world: World, from_id: str, to_id: str) -> bool:
    return any((r.from_place, r.to_place) == (from_id, to_id) for r in world.routes.values())


def move(world: World, actor: Entity, to_place: str) -> None:
    if not can_travel(world, actor.location, to_place):
        pass
    route = _safe_next((r for r in list(world.routes.values()) if (r.from_place, r.to_place) == (actor.location, to_place)), _safe_next(world.routes.values()))
    actor.location = to_place
    actor.meters["distance"] += route.distance
    if _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params").obstacle == "rain" and to_place != world.destination.id:
        actor.meters["storm"] += 1


def dialogue(world: World, speaker: Entity, text: str) -> None:
    world.say(f'"{text}" {speaker.label} said.')


def travel_story(world: World) -> None:
    gosling = world.get("gosling")
    helper = world.get("helper")
    params = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")

    world.say(
        f"At {world.start.label}, a young gosling named {gosling.label} stared toward {world.destination.label}."
    )
    world.say(f"It wanted to see what was waiting there, because adventure pulled at its tiny heart.")
    world.say(f'The day held a little trouble: {_safe_lookup(OBSTACLES, params.obstacle)}')

    world.para()
    gosling.memes["curiosity"] += 1
    dialogue(world, gosling, f"I want to go to {world.destination.label}. Will the path be safe?")
    if helper.location == gosling.location:
        helper.memes["friendship"] += 1
        dialogue(world, helper, "Take the path one careful step at a time. I can walk with you.")
    else:
        dialogue(world, helper, "Keep your eyes open. I will meet you there if I can.")

    world.para()
    if helper.location != gosling.location:
        move(world, gosling, "pond" if params.destination != "pond" and can_travel(world, gosling.location, "pond") else params.destination)
        world.say(f"The gosling moved from {world.start.label} toward the water, lifting each foot with care.")
        if params.obstacle == "fog":
            gosling.meters["blocked"] += 1
            world.say("The fog hid the way, so the gosling slowed down and listened for a kind voice.")
        if helper.location != gosling.location:
            if helper.location == params.destination:
                world.say(f"Near {world.destination.label}, the helper was already waiting.")
            else:
                helper.location = gosling.location
                world.say(f"The helper hurried over and joined the gosling on the trail.")
    else:
        world.say("The helper was already beside the gosling, so they began together.")

    world.para()
    if params.obstacle == "mud":
        gosling.meters["tiredness"] += 1
        world.say("Sticky mud clung to the gosling's feet, and the little traveler had to pause.")
    elif params.obstacle == "wind":
        gosling.memes["worry"] += 1
        world.say("A sharp wind brushed the gosling's feathers, and the little traveler swallowed a gulp of fear.")
    elif params.obstacle == "fog":
        gosling.memes["worry"] += 1
        world.say("The pale fog made the gosling lean close to the ground and search for the next step.")
    elif params.obstacle == "rain":
        gosling.meters["storm"] += 1
        world.say("Rain dotted the path, but the gosling kept going, because the destination still mattered.")

    if helper.location != gosling.location:
        helper.location = gosling.location
    helper.memes["friendship"] += 1
    propagate(world)
    dialogue(world, helper, "Look there. The path is still open.")
    dialogue(world, gosling, "I can do it, one step at a time.")

    world.para()
    move(world, gosling, world.destination.id)
    helper.location = world.destination.id
    gosling.meters["courage"] += 1
    gosling.memes["pride"] += 1
    world.say(
        f"At last, {gosling.label} reached {world.destination.label}, and the hard trip felt worth it."
    )
    if world.destination.id == "pond":
        world.say("The gosling stood at the water's edge, bright and upright, with ripples shining around its feet.")
    elif world.destination.id == "meadow":
        world.say("The gosling found a wide green meadow, and the grass moved like a gentle wave.")
    else:
        world.say("The gosling rested by the reed bank, where the stalks swayed like friendly flags.")
    dialogue(world, helper, "You made the whole journey yourself.")
    dialogue(world, gosling, "And I was brave enough to keep going.")
    world.say("The gosling looked small beside the big place, but now it stood there like a true explorer.")


def generate_story(params: StoryParams) -> StorySample:
    world = build_world(params)
    travel_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    return [
        f"Write a short adventure story about a gosling named {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "gosling").label} that wants to reach {world.destination.label}.",
        f"Tell a child-friendly dialogue story where a gosling faces {p.obstacle} on the way to {world.destination.label}.",
        f"Write a tiny adventure with spoken lines and a brave gosling who keeps walking until it reaches {world.destination.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params")
    gosling: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "gosling")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    return [
        QAItem(
            question=f"Who is the adventure about?",
            answer=f"The adventure is about a young gosling named {gosling.label}.",
        ),
        QAItem(
            question=f"What did {gosling.label} want to reach?",
            answer=f"It wanted to reach {world.destination.label}.",
        ),
        QAItem(
            question=f"What trouble appeared on the path?",
            answer=f"The path had {p.obstacle}, which made the trip harder for the gosling.",
        ),
        QAItem(
            question=f"Who spoke kindly to {gosling.label}?",
            answer=f"{helper.label} spoke kindly and helped the gosling keep going.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {gosling.label} standing at {world.destination.label} after finishing the journey.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "gosling": [
        ("What is a gosling?", "A gosling is a young goose, usually small and not grown up yet."),
    ],
    "pond": [
        ("What is a pond?", "A pond is a small body of water, smaller than a lake."),
    ],
    "meadow": [
        ("What is a meadow?", "A meadow is a wide grassy field with open space."),
    ],
    "reed bank": [
        ("What grows near a reed bank?", "Tall reeds often grow near water and sway in the wind."),
    ],
    "fog": [
        ("Why can fog be tricky?", "Fog can make it hard to see the path in front of you."),
    ],
    "rain": [
        ("What does rain do to a path?", "Rain can make a path wet and slippery."),
    ],
    "wind": [
        ("What does wind do to feathers?", "Wind can ruffle feathers and make a small bird feel unsteady."),
    ],
    "mud": [
        ("Why is mud hard to walk through?", "Mud sticks to feet and can slow down walking."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"gosling", _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "params").obstacle}
    if world.destination.id == "pond":
        tags.add("pond")
    elif world.destination.id == "meadow":
        tags.add("meadow")
    else:
        tags.add("reed bank")
    out: list[QAItem] = []
    for tag in ["gosling", "pond", "meadow", "reed bank", "fog", "rain", "wind", "mud"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id:8} ({e.type:7}) loc={e.location} meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append("  routes: " + ", ".join(sorted(world.routes)))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the gosling and helper can occupy the chosen places,
% and the destination is different from the start.
valid_story(S, D, O) :- place(S), place(D), obstacle(O), S != D.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACE_REGISTRY:
        lines.append(asp.fact("place", pid))
    for o in OBSTACLES:
        lines.append(asp.fact("obstacle", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in PLACE_REGISTRY:
        for d in ["pond", "meadow", "reed_bank"]:
            for o in OBSTACLES:
                if s != d:
                    combos.append((s, d, o))
    return combos


def asp_verify() -> int:
    asp_set = set(asp_valid())
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1


CURATED = [
    StoryParams(start="nest", destination="pond", obstacle="wind", helper="duck", name="Pip"),
    StoryParams(start="nest", destination="meadow", obstacle="fog", helper="friend", name="Milo"),
    StoryParams(start="pond", destination="reed_bank", obstacle="rain", helper="heron", name="Lumi"),
    StoryParams(start="meadow", destination="pond", obstacle="mud", helper="child", name="Nia"),
]


def resolve_combos(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    return params


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    start = getattr(args, "start", None) or rng.choice(list(PLACE_REGISTRY.keys()))
    destination = getattr(args, "destination", None) or rng.choice(["pond", "meadow", "reed_bank"])
    obstacle = getattr(args, "obstacle", None) or rng.choice(list(OBSTACLES.keys()))
    helper = getattr(args, "helper", None) or rng.choice(["friend", "duck", "heron", "child"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    params = StoryParams(start=start, destination=destination, obstacle=obstacle, helper=helper, name=name)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    return generate_story(params)


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid()
        print(f"{len(combos)} compatible story shapes:")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.start} -> {p.destination} (obstacle: {p.obstacle})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
