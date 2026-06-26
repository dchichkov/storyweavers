#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/quince_pore_hug_dim_suspense_repetition_fairy.py
==============================================================================================================================

A small fairy-tale story world built from the seed words quince, pore, and hug-dim.

Premise:
A little fairy wants a golden quince from a quiet orchard, but the fruit hangs
behind a thorny hedge and a tiny pore in the old gate is the only way to peek
inside. The fairy keeps pored-over clues, repeated careful tries, and a gentle
hug-dim charm to calm the suspense before finding a safe way to bring the fruit
home.

This world uses:
- physical meters for distance, light, ripeness, rustle, and safety
- emotional memes for worry, courage, patience, delight, and suspense

It includes a Python reasonableness gate and an inline ASP twin.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince"}:
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
    name: str
    indoors: bool = False
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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
    effect: str
    prep: str
    tail: str
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
class StoryParams:
    place: str = ""
    action: str = ""
    prize: str = ""
    charm: str = ""
    name: str = ""
    gender: str = ""
    parent: str = ""
    trait: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _bump_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = _meter(ent, key) + amt


def _bump_mem(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = _mem(ent, key) + amt


def _r_suspense(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if _mem(actor, "worry") < THRESHOLD:
            continue
        sig = ("suspense", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _bump_mem(actor, "suspense", 1.0)
        out.append(f"The air felt extra still, as if the orchard were holding its breath.")
    return out


def _r_charm(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if _mem(actor, "hugged") < THRESHOLD:
            continue
        sig = ("hug_dim", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _bump_mem(actor, "courage", 1.0)
        _bump_mem(actor, "worry", -1.0)
        out.append(f"The hug-dim charm made the little heart feel brighter and steadier.")
    return out


def _r_ripen(world: World) -> list[str]:
    out = []
    for prize in list(world.entities.values()):
        if prize.kind != "thing":
            continue
        if _meter(prize, "ripeness") >= THRESHOLD:
            continue
        if _mem(prize, "warmed") < THRESHOLD:
            continue
        sig = ("ripen", prize.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _bump_meter(prize, "ripeness", 1.0)
        out.append(f"The quince gave off a sweet little glow and looked ready at last.")
    return out


CAUSAL_RULES = [
    ("suspense", _r_suspense),
    ("hug_dim", _r_charm),
    ("ripen", _r_ripen),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_reach_prize(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def pick_charm(action: Action, prize: Prize) -> Optional[Charm]:
    if action.id == "pore" and prize.region == "branch":
        return CHARMES["hug_dim"]
    if action.id == "fetch" and prize.region == "branch":
        return CHARMES["basket"]
    return None


def predict_outcome(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    perform_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "unripe": _meter(prize, "ripeness") < THRESHOLD,
        "safely_found": _mem(actor, "courage") >= THRESHOLD,
    }


def perform_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.place.affords:
        pass
    world.zone = set(action.zone)
    _bump_mem(actor, action.id, 1.0)
    _bump_mem(actor, "worry", 0.5)
    if action.id == "pore":
        _bump_mem(actor, "suspense", 1.0)
    propagate(world, narrate=narrate)


def setup_line(world: World, hero: Entity, place: Place, prize: Entity) -> None:
    world.say(
        f"In a little fairy tale, {hero.id} lived by {place.name} and loved the golden quince."
    )
    world.say(
        f"Every evening, {hero.pronoun().capitalize()} would pore over the hedge and wonder if "
        f"{hero.pronoun('possessive')} {prize.label} was ready."
    )


def repeated_try(world: World, hero: Entity, action: Action) -> None:
    hero.memes["repetition"] = hero.memes.get("repetition", 0.0) + 1.0
    world.say(
        f"{hero.id} came back again and again, each time to {action.verb}, "
        f"each time to listen for a sign."
    )


def tell(world: World, hero: Entity, parent: Entity, prize: Entity, action: Action, charm: Optional[Charm]) -> World:
    setup_line(world, hero, world.place, prize)
    world.para()
    world.say(
        f"One dim evening, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.place.name}."
    )
    world.say(
        f"The hedge was high, but a tiny pore in the old gate let {hero.pronoun()} pore inside."
    )
    world.say(
        f"{hero.id} wanted to {action.verb}, but {hero.pronoun('possessive')} heart beat fast with suspense."
    )
    repeated_try(world, hero, action)
    if charm:
        world.say(f'{hero.pronoun("possessive").capitalize()} {parent.label} smiled and said, "{charm.prep}."')
    world.para()
    _bump_mem(hero, "worry", 1.0)
    if charm:
        _bump_mem(hero, "hugged", 1.0)
    if action.id == "pore":
        _bump_mem(prize, "warmed", 1.0)
    propagate(world, narrate=True)
    world.say(
        f"At last, {hero.id} found the quince, and the little orchard felt less suspenseful at the end."
    )
    if charm:
        world.say(
            f"They {charm.tail}, and {prize.label} shone softly in {hero.pronoun('possessive')} hands."
        )
    return world


PLACE_REGISTRY = {
    "orchard": Place(name="the orchard", indoors=False, affords={"pore", "fetch"}),
    "gate": Place(name="the old gate", indoors=False, affords={"pore"}),
    "garden": Place(name="the moon garden", indoors=False, affords={"pore", "fetch"}),
}

ACTION_REGISTRY = {
    "pore": Action(
        id="pore",
        verb="pore over the tiny opening",
        gerund="poring over the tiny opening",
        rush="peer through the pore again",
        mess="none",
        soil="",
        zone={"eye", "hand"},
        keyword="pore",
        tags={"suspense", "repetition", "pore"},
    ),
    "fetch": Action(
        id="fetch",
        verb="fetch the quince from the branch",
        gerund="fetching the quince",
        rush="reach for the branch",
        mess="none",
        soil="",
        zone={"hand", "arm"},
        keyword="quince",
        tags={"quince"},
    ),
}

PRIZE_REGISTRY = {
    "quince": Prize(
        id="quince",
        label="quince",
        phrase="a golden quince",
        region="branch",
        plural=False,
    )
}

CHARMES = {
    "hug_dim": Charm(
        id="hug_dim",
        label="hug-dim charm",
        effect="brings courage into the dimness",
        prep="Let's use the hug-dim charm and wait kindly",
        tail="walked home under a calm little moon",
    ),
    "basket": Charm(
        id="basket",
        label="basket",
        effect="carries fruit safely",
        prep="Let's bring a basket and take it carefully",
        tail="carried the fruit home without a bump",
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACE_REGISTRY.items():
        for action_id in place.affords:
            action = _safe_lookup(ACTION_REGISTRY, action_id)
            for prize_id, prize in PRIZE_REGISTRY.items():
                if can_reach_prize(action, prize):
                    combos.append((place_id, action_id, prize_id, "girl"))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, action in ACTION_REGISTRY.items():
        lines.append(asp.fact("action", aid))
        for r in sorted(action.zone):
            lines.append(asp.fact("zone", aid, r))
    for prid, prize in PRIZE_REGISTRY.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("worn_on", prid, prize.region))
    for cid, charm in CHARMES.items():
        lines.append(asp.fact("charm", cid))
    return "\n".join(lines)


ASP_RULES = r"""
can_reach(A,P) :- action(A), prize(P), zone(A,R), worn_on(P,R).
has_charm(A,P,hug_dim) :- can_reach(A,P), A = pore.
valid_story(Place,A,P,girl) :- affords(Place,A), can_reach(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only python:", sorted(py - cl))
    print(" only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale world of quince, pore, and hug-dim.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--action", choices=ACTION_REGISTRY)
    ap.add_argument("--prize", choices=PRIZE_REGISTRY)
    ap.add_argument("--charm", choices=CHARMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", default=None)
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
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or c[3] == getattr(args, "gender", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize, gender = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Lina", "Mira", "Tessa", "Ari", "Nina"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(["curious", "gentle", "brave", "patient"])
    charm = getattr(args, "charm", None) or "hug_dim"
    return StoryParams(place=place, action=action, prize=prize, charm=charm,
                       name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    act: Action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    return [
        f'Write a short fairy tale for a child that includes the words "quince", "pore", and "hug-dim".',
        f"Tell a gentle suspense story where {hero.id} keeps returning to {world.place.name} to {act.verb}.",
        f"Write a repeated, moonlit story where a tiny opening, a golden quince, and a hug-dim charm all matter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    prize: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    action: Action = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "action")
    charm: Optional[Charm] = f.get("charm")
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.place.name}?",
            answer=f"{hero.id} wanted to {action.verb}, because {hero.pronoun('possessive')} eyes kept finding the golden quince.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because the quince stayed just out of easy reach, and {hero.id} kept worrying while peering through the pore in the gate.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel calmer?",
            answer=f"The {charm.label if charm else 'quiet moonlight'} helped {hero.id} feel calmer, and the hug-dim charm made the fear soften.",
        ),
        QAItem(
            question=f"How did the repeated tries matter?",
            answer=f"{hero.id} tried again and again, and that repetition helped {hero.pronoun('subject')} notice the safer way to reach the quince.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} had the quince, and the orchard felt peaceful instead of tense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quince?",
            answer="A quince is a yellow fruit with a strong scent. People often cook it because it can be hard and tart when raw.",
        ),
        QAItem(
            question="What does pore mean when you pore over something?",
            answer="To pore over something means to look at it carefully and for a long time.",
        ),
        QAItem(
            question="What does a dim light do?",
            answer="A dim light shines softly and does not look very bright.",
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(PLACE_REGISTRY, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=[params.trait, "small"]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prize = world.add(Entity(id=params.prize, type="fruit", label="quince", phrase="a golden quince", caretaker=parent.id))
    action = _safe_lookup(ACTION_REGISTRY, params.action)
    charm = _safe_lookup(CHARMES, params.charm)

    world.facts.update(hero=hero, parent=parent, prize=prize, action=action, charm=charm, params=params)

    world.say(f"Once upon a time, {hero.id} lived near {world.place.name}.")
    world.say(f"{hero.pronoun().capitalize()} loved to pore over the hedge and dream of the quince.")
    world.para()
    world.say(f"One dim evening, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.place.name}.")
    world.say(f"A tiny pore in the old gate showed the quince shining beyond the thorns.")
    world.say(f"{hero.id} felt suspense, but {hero.pronoun('subject')} kept trying to {action.verb}.")
    _bump_mem(hero, "worry", 1.0)
    _bump_mem(hero, "repetition", 1.0)
    if params.action == "pore":
        _bump_mem(prize, "warmed", 1.0)
    if params.charm == "hug_dim":
        _bump_mem(hero, "hugged", 1.0)
    world.say(f"Then {hero.id} gave {hero.pronoun('possessive')} {parent.label} a hug-dim hug.")
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"At last, {hero.id} found the quince and carried it home, while the orchard grew quiet and kind."
    )

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
    StoryParams(place="orchard", action="pore", prize="quince", charm="hug_dim",
                name="Lina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="garden", action="pore", prize="quince", charm="hug_dim",
                name="Mira", gender="girl", parent="father", trait="patient"),
]


def explain_rejection() -> str:
    return "(No story: this fairy tale needs the quince, the pore, and a safe way to resolve the suspense.)"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
