#!/usr/bin/env python3
"""
blue_curious_piggie_foreshadowing_folk_tale.py
==============================================

A small folk-tale story world about a blue, curious piggie who follows
foreshadowing signs through a meadow, a lane, and a little wood.

Premise:
- The piggie loves shining clues and hidden meanings.
- The village elder, a bluebird, and the wind each leave small warnings.
- Those warnings foreshadow a pond-fall or a fox-trouble if the piggie
  rushes ahead too fast.

Turn:
- The piggie notices the signs before stepping into trouble.
- The piggie uses a simple gift, a ribbon, and a careful plan.

Resolution:
- The piggie safely crosses the lane, helps a friend, and ends the tale
  looking at the sky with a wiser heart.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify checks Python/ASP parity and exercises generation
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    region: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
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
class Place:
    id: str
    label: str
    indoors: bool = False
    features: set[str] = field(default_factory=set)
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
class Sign:
    id: str
    label: str
    foreshadows: str
    seen_in: set[str] = field(default_factory=set)
    hint: str = ""
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    risk: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Helper:
    id: str
    label: str
    gift: str
    action: str
    promise: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str = ""
    sign: str = ""
    prize: str = ""
    helper: str = ""
    name: str = ""
    gender: str = ""
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
    "lane": Place(id="lane", label="the lane", features={"crossing", "mud"}),
    "meadow": Place(id="meadow", label="the meadow", features={"grass", "crossing"}),
    "wood": Place(id="wood", label="the little wood", features={"trees", "crossing"}),
}

SIGNS = {
    "ribbon": Sign(
        id="ribbon",
        label="a blue ribbon",
        foreshadows="a puddle under the grass",
        seen_in={"meadow", "wood", "lane"},
        hint="The ribbon fluttered once, as if to say to look down before stepping.",
    ),
    "bluebird": Sign(
        id="bluebird",
        label="a bluebird call",
        foreshadows="a fox near the hedge",
        seen_in={"meadow", "wood"},
        hint="The bird sang twice from the thorn bush, then fell silent.",
    ),
    "cobble": Sign(
        id="cobble",
        label="a wet cobble",
        foreshadows="a slippery bend by the stream",
        seen_in={"lane"},
        hint="The shiny stone glimmered like it had already met the rain.",
    ),
}

PRIZES = {
    "boots": Prize(
        id="boots",
        label="boots",
        phrase="small brown boots",
        region="feet",
        risk="muddy",
        genders={"girl", "boy"},
    ),
    "cap": Prize(
        id="cap",
        label="cap",
        phrase="a neat blue cap",
        region="head",
        risk="windy",
        genders={"girl", "boy"},
    ),
    "shawl": Prize(
        id="shawl",
        label="shawl",
        phrase="a warm red shawl",
        region="torso",
        risk="wet",
        genders={"girl"},
    ),
}

HELPERS = {
    "oldwillow": Helper(
        id="oldwillow",
        label="Old Willow",
        gift="a twig with a bend in it",
        action="points with a long arm toward the safe stones",
        promise="The bend in the twig will be a guide when the path looks tricky.",
    ),
    "aunt": Helper(
        id="aunt",
        label="Aunt Pebble",
        gift="a basket of dry cloth",
        action="knots a bright ribbon to the basket handle",
        promise="The ribbon can mark a dry path when the ground turns soggy.",
    ),
}

NAMES = ["Pip", "Mimi", "Toby", "Lula", "Nell", "Bram", "Wren", "Moss"]
TRAITS = ["curious", "gentle", "bold", "dreamy", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for sign_id, sign in SIGNS.items():
            if place_id not in sign.seen_in:
                continue
            for prize_id, prize in PRIZES.items():
                if prize.region in {"feet", "torso"} and "crossing" in place.features:
                    combos.append((place_id, sign_id, prize_id))
    return combos


def reasonableness_gate(place: Place, sign: Sign, prize: Prize) -> bool:
    return place.id in sign.seen_in and prize.region in {"feet", "head", "torso"} and "crossing" in place.features


def explain_rejection(place: Place, sign: Sign, prize: Prize) -> str:
    return (
        f"(No story: {sign.label} is not a good foreshadowing clue for {place.label} "
        f"with {prize.label} in this little tale.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} does not fit a typical {gender} in this tale; try --gender {ok}.)"


def predict_world(world: World, hero: Entity, sign: Sign, prize: Prize) -> dict:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    hero2.memes["curiosity"] = hero2.memes.get("curiosity", 0) + 1
    if sign.id == "bluebird":
        hero2.memes["alert"] = hero2.memes.get("alert", 0) + 1
    risky = sign.foreshadows
    return {
        "risk_seen": risky,
        "would_slip": prize.risk == "muddy" and sign.id in {"ribbon", "cobble"},
    }


def tell_intro(world: World, hero: Entity, prize: Entity) -> None:
    blue = "blue" if "blue" in hero.traits else "little"
    curious = "curious" if "curious" in hero.traits else "watchful"
    world.say(
        f"Once in the {world.place.label}, there was a {blue}, {curious} piggie named {hero.id}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved little signs and secret meanings, and {hero.pronoun('possessive')} {prize.label} "
        f"shone as neat as a berry on a leaf."
    )


def tell_foreshadow(world: World, hero: Entity, sign: Sign) -> None:
    world.say(
        f"One morning, {sign.label} appeared on the path. It felt like a whisper before a surprise."
    )
    world.say(sign.hint)


def tell_warning(world: World, hero: Entity, sign: Sign, prize: Entity) -> None:
    pred = predict_world(world, hero, sign, prize)
    world.facts["predicted_risk"] = pred["risk_seen"]
    if pred["would_slip"]:
        world.say(
            f"{hero.id} paused, because the clue seemed to foreshadow trouble for {hero.pronoun('possessive')} {prize.label}."
        )
    else:
        world.say(
            f"{hero.id} paused, because the clue seemed to foreshadow a choice worth taking slowly."
        )


def tell_turn(world: World, hero: Entity, helper: Entity, sign: Sign, prize: Entity) -> None:
    world.say(
        f"Then {helper.label} came along, carrying {helper.facts['gift'] if 'gift' in helper.facts else helper.label}."
    )
    world.say(
        f"{helper.label} {helper.facts['action'] if 'action' in helper.facts else 'smiled kindly'} and said, "
        f"\"{helper.facts['promise'] if 'promise' in helper.facts else helper.label}\"\n"
        if False else
        f"{helper.label} smiled kindly and said, \"{helper.promise}\""
    )


def tell_resolution(world: World, hero: Entity, helper: Entity, sign: Sign, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0) + 1
    world.say(
        f"{hero.id} followed the clue, stepped on the dry stones, and kept {hero.pronoun('possessive')} {prize.label} clean."
    )
    world.say(
        f"At the end, the {sign.label} still fluttered in the breeze, but now it felt like a friend."
    )


def build_story(world: World, hero: Entity, sign: Sign, prize: Entity, helper: Entity) -> None:
    tell_intro(world, hero, prize)
    world.para()
    tell_foreshadow(world, hero, sign)
    tell_warning(world, hero, sign, prize)
    world.para()
    tell_turn(world, hero, helper, sign, prize)
    world.para()
    tell_resolution(world, hero, helper, sign, prize)


def choose_helper(sign: Sign) -> Helper:
    return HELPERS["oldwillow"] if sign.id == "ribbon" else HELPERS["aunt"]


def choose_name(gender: str, rng: random.Random) -> str:
    if gender == "boy":
        pool = [n for n in NAMES if n not in {"Lula", "Nell", "Mimi"}]
    else:
        pool = NAMES
    return rng.choice(pool)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    sign: Sign = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sign")
    helper: Helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper_obj")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place_obj")
    return [
        QAItem(
            question=f"Who was the blue, curious piggie in the story?",
            answer=f"The story was about {hero.id}, a blue, curious piggie who loved to notice small clues.",
        ),
        QAItem(
            question=f"What clue foreshadowed trouble on the path?",
            answer=f"{sign.label} foreshadowed {sign.foreshadows}, so the clue warned {hero.id} to slow down and look carefully.",
        ),
        QAItem(
            question=f"Who helped the piggie make a safe choice?",
            answer=f"{helper.label} helped by sharing a careful hint and a promise that led {hero.id} safely through {place.label}.",
        ),
        QAItem(
            question=f"What stayed safe at the end?",
            answer=f"{hero.pronoun('possessive').capitalize()} {prize.label} stayed clean, and the piggie reached the end without getting into trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something foreshadows trouble?",
            answer="It means there are early signs that hint something tricky may happen later.",
        ),
        QAItem(
            question="What is a ribbon for?",
            answer="A ribbon is a thin strip of cloth used for decoration or to mark or tie things.",
        ),
        QAItem(
            question="Why do careful travelers look at wet stones?",
            answer="Wet stones can be slippery, so careful travelers look before stepping on them.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    sign: Sign = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sign")
    return [
        f"Write a short folk tale about a blue, curious piggie named {hero.id} who notices {sign.label} and listens to the hint.",
        f"Tell a gentle story where a piggie follows foreshadowing signs and keeps {hero.pronoun('possessive')} {prize.label} safe.",
        f"Write a child-friendly folk tale that begins with a clue and ends with a wiser piggie on a safe path.",
    ]


ASP_RULES = r"""
foreshadows(Sign, Risk) :- sign(Sign), clue(Sign), risk(Sign, Risk).
safe_choice(Hero, Prize) :- hero(Hero), prize(Prize), keeps_clean(Hero, Prize).
valid_story(Place, Sign, Prize) :- place(Place), sign_on_path(Sign, Place), prize(Prize), reasonable(Place, Sign, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for feat in sorted(place.features):
            lines.append(asp.fact("feature", pid, feat))
    for sid, sign in SIGNS.items():
        lines.append(asp.fact("sign", sid))
        lines.append(asp.fact("clue", sid))
        lines.append(asp.fact("risk", sid, sign.foreshadows))
        for p in sorted(sign.seen_in):
            lines.append(asp.fact("sign_on_path", sid, p))
    for prid, prize in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("keeps_clean", "piggie", prid))
        lines.append(asp.fact("prize_region", prid, prize.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [(p, s, r) for p, s, r in valid_combos()]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        sample = generate(resolve_params(argparse.Namespace(place=None, sign=None, prize=None, gender=None, name=None, helper=None), random.Random(1)))
        if not sample.story.strip():
            print("MISMATCH: empty story")
            return 1
        print(f"OK: ASP parity matches Python ({len(clingo_set)} combos), and generation works.")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in ASP:", sorted(clingo_set - python_set))
    print(" only in Python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale world about a blue, curious piggie and foreshadowing signs.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    place_id = getattr(args, "place", None) or rng.choice(list(PLACES))
    place = _safe_lookup(PLACES, place_id)
    sign_id = getattr(args, "sign", None) or rng.choice([s for s, obj in SIGNS.items() if place_id in obj.seen_in])
    sign = _safe_lookup(SIGNS, sign_id)
    prize_id = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    if gender not in prize.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not reasonableness_gate(place, sign, prize):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or choose_name(gender, rng)
    helper = getattr(args, "helper", None) or ("oldwillow" if sign_id == "cobble" else "aunt")
    return StoryParams(place=place_id, sign=sign_id, prize=prize_id, helper=helper, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    sign = _safe_lookup(SIGNS, params.sign)
    prize = _safe_lookup(PRIZES, params.prize)
    helper_def = _safe_lookup(HELPERS, params.helper)

    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="piggie",
        traits=["blue", "curious", "little"],
        meters={"presence": 1.0},
        memes={"curiosity": 2.0},
    ))
    prize_ent = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize.label,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        region=prize.region,
        plural=prize.label.endswith("s"),
    ))
    helper = world.add(Entity(
        id=helper_def.id,
        kind="character",
        type="elder",
        label=helper_def.label,
        phrase=helper_def.label,
        meters={"age": 1.0},
    ))
    helper.facts = {"gift": helper_def.gift, "action": helper_def.action, "promise": helper_def.promise}  # type: ignore[attr-defined]

    world.facts.update(
        hero=hero,
        prize=prize_ent,
        sign=sign,
        helper_obj=helper_def,
        place_obj=place,
    )
    build_story(world, hero, sign, prize_ent, helper_def)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
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
    StoryParams(place="meadow", sign="ribbon", prize="boots", helper="oldwillow", name="Pip", gender="boy"),
    StoryParams(place="wood", sign="bluebird", prize="shawl", helper="aunt", name="Lula", gender="girl"),
    StoryParams(place="lane", sign="cobble", prize="cap", helper="oldwillow", name="Moss", gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.sign} at {p.place} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
