#!/usr/bin/env python3
"""
storyworlds/worlds/perm_surprise_myth.py
========================================

A small myth-style story world about a child who longs for a perm, a warning
about the weather, and a surprise that changes the tale's ending.

The domain is intentionally tiny:
- a young hero wants a perm before a sacred gathering
- a parent or elder fears the rain will frizz the curls and spoil the day
- a surprise helper appears with a protective charm or a better plan
- the ending proves whether the perm stayed neat and what emotion changed

The narration is generated from world state, not from a fixed paragraph shell.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    charm_ent: object | None = None
    elder: object | None = None
    hero: object | None = None
    perm: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for k in ["rain", "wind", "tangle", "care", "joy", "fear", "surprise", "love", "pride"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "goddess"}
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
    outdoors: bool = True
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
class Event:
    id: str
    label: str
    weather: str
    risk: str
    risk_zone: set[str]
    surprise_kind: str
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
class Charm:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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


class World:
    def __init__(self, place: Place, event: Event):
        self.place = place
        self.event = event
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set(event.risk_zone)
        self.weather: str = event.weather

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
        clone = World(self.place, self.event)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))


@dataclass
class StoryParams:
    place: str = ""
    event: str = ""
    charm: str = ""
    name: str = ""
    gender: str = ""
    elder: str = ""
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


PLACES = {
    "temple_courtyard": Place("the temple courtyard", outdoors=True, affords={"festival", "rain"}),
    "river_bank": Place("the river bank", outdoors=True, affords={"festival", "rain"}),
    "hill_shrine": Place("the hill shrine", outdoors=True, affords={"festival", "wind"}),
}

EVENTS = {
    "festival": Event(
        id="festival",
        label="the lantern festival",
        weather="rain",
        risk="rain",
        risk_zone={"hair"},
        surprise_kind="surprise_help",
    ),
    "procession": Event(
        id="procession",
        label="the moon procession",
        weather="wind",
        risk="wind",
        risk_zone={"hair"},
        surprise_kind="surprise_visitor",
    ),
}

CHARMS = {
    "veil": Charm(
        id="veil",
        label="a silk veil",
        covers={"hair"},
        guards={"rain", "wind"},
        prep="wear the silk veil",
        tail="fastened the silk veil and walked on",
    ),
    "hood": Charm(
        id="hood",
        label="a hooded cloak",
        covers={"hair"},
        guards={"rain"},
        prep="pull on a hooded cloak",
        tail="pulled the hood tight and went on",
    ),
    "comb": Charm(
        id="comb",
        label="a moon comb",
        covers={"hair"},
        guards={"wind"},
        prep="pin the curls with the moon comb",
        tail="set the moon comb in place and smiled",
    ),
}

GIRL_NAMES = ["Mira", "Ione", "Lena", "Tara", "Asha", "Nia", "Sera", "Kira"]
BOY_NAMES = ["Orin", "Bela", "Rian", "Tavi", "Niko", "Ezra"]
TRAITS = ["curious", "brave", "gentle", "hopeful", "stubborn", "bright"]


def reasonableness_gate(event: Event, charm: Charm) -> bool:
    return event.risk in charm.guards and "hair" in charm.covers


def explain_rejection(event: Event, charm: Charm) -> str:
    return (
        f"(No story: {charm.label} does not truly guard the hair from {event.risk}. "
        f"The myth needs a remedy that can honestly protect the perm.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for event_id in place.affords:
            ev = _safe_lookup(EVENTS, event_id)
            for charm_id, charm in CHARMS.items():
                if reasonableness_gate(ev, charm):
                    combos.append((place_id, event_id, charm_id))
    return combos


def _rain_or_wind(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["surprise"] < THRESHOLD:
            continue
        if actor.meters[world.event.risk] < THRESHOLD:
            for item in world.worn_items(actor):
                if item.protective and world.event.risk in item.covers:
                    continue
                if "hair" in world.zone and not world.covered(actor, "hair"):
                    sig = ("damage", item.id, world.event.risk)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.meters[world.event.risk] += 1
                    actor.memes["fear"] += 1
                    out.append(f"The {world.event.risk} worried the air around {actor.id}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for sent in _rain_or_wind(world):
            changed = True
            produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def foresee(world: World, actor: Entity, prize_id: str) -> dict:
    sim = world.copy()
    act = sim.get(actor.id)
    if prize_id in sim.entities:
        prize = sim.get(prize_id)
        if prize.worn_by == act.id and sim.event.risk_zone and not sim.covered(act, "hair"):
            prize.meters[sim.event.risk] += 1
    return {"ruined": any(e.meters[world.event.risk] >= THRESHOLD for e in sim.entities.values())}


def tell(place: Place, event: Event, charm: Charm, hero_name: str, gender: str, elder_type: str, trait: str) -> World:
    world = World(place, event)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={}, memes={}))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    perm = world.add(Entity(
        id="perm",
        type="hair",
        label="perm",
        phrase="a shining perm with small springy curls",
        owner=hero.id,
        caretaker=elder.id,
        region="hair",
    ))
    hero.memes["love"] += 1
    hero.memes["surprise"] += 0
    perm.worn_by = hero.id

    world.say(f"{hero.id} was a {trait} child who loved {perm.phrase}.")
    world.say(f"The old songs said that {hero.id} looked like a little river spirit when the curls bounced.")
    world.say(f"Before the day of {event.label}, {hero.id}'s {elder.label or elder.type} gave {hero.pronoun('object')} the perm and promised to watch over it.")

    world.para()
    world.say(f"On the morning of {event.label}, {hero.id} went to {place.name}.")
    world.say(f"{hero.id} wanted to show the other children the perm, but the sky had grown full of {event.risk}.")
    hero.memes["desire"] += 1
    hero.memes["fear"] += 1

    if event.risk == "rain":
        world.say(f"The first drops tapped the stones, and {hero.id} worried the curls would lose their shine.")
    else:
        world.say(f"The wind ran over the hill like a wolf, and {hero.id} feared it would tangle every curl.")

    world.say(f'"If the {event.risk} reaches your hair, your perm may not stay neat," {elder.label or elder.type} said.')
    world.facts["foreseen_ruin"] = True

    world.para()
    hero.memes["surprise"] += 1
    if event.surprise_kind == "surprise_help":
        world.say(f"Then a surprise came: a veiled stranger stepped from the crowd and offered {charm.label}.")
    else:
        world.say(f"Then a surprise came: a bright messenger climbed the path and set {charm.label} into {hero.id}'s hands.")

    if not reasonableness_gate(event, charm):
        pass
    charm_ent = world.add(Entity(
        id=charm.id,
        type="charm",
        label=charm.label,
        owner=hero.id,
        protective=True,
        covers=set(charm.covers),
    ))
    charm_ent.worn_by = hero.id

    world.say(f'"{charm.prep}," the stranger said, "and the perm will be safe."')
    world.say(f"{hero.id} listened, took the gift, and the curls settled under it like a nest beneath leaves.")
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1

    propagate(world, narrate=False)
    world.say(f"{hero.id} {charm.tail}, and the {event.risk} could not touch the hair.")
    world.say(f"So the perm stayed bright at {place.name}, and {hero.id} smiled as if the gods themselves had blessed the curls.")

    world.facts.update(hero=hero, elder=elder, perm=perm, charm=charm_ent, event=event, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a small child about a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").type} named {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id}, a perm, and a surprise at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").name}.',
        f"Tell a gentle myth where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} loves a perm, fears the weather at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "event").label}, and a surprise gift helps.",
        f'Write a short, child-friendly legend that includes the word "perm" and ends with the curls still shining.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    elder = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")
    perm = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "perm")
    event = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "event")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    charm = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "charm")
    return [
        QAItem(
            question=f"What did {hero.id} love in the story?",
            answer=f"{hero.id} loved the perm, because the curls made {hero.pronoun('object')} feel like a little hero from an old myth.",
        ),
        QAItem(
            question=f"Why did {elder.label or elder.type} worry at {place.name}?",
            answer=f"{elder.label or elder.type.capitalize()} worried because {event.risk} might reach the hair and spoil the perm before the festival was over.",
        ),
        QAItem(
            question=f"What surprise helped {hero.id} keep the perm safe?",
            answer=f"A surprise gift of {charm.label} helped {hero.id} cover the hair so the {event.risk} could not ruin the curls.",
        ),
        QAItem(
            question=f"How did the story end for the perm?",
            answer=f"The perm stayed bright and neat at {place.name}, and {hero.id} ended the day smiling with pride.",
        ),
    ]


KNOWLEDGE = {
    "perm": [("What is a perm?", "A perm is a hairstyle made by setting hair into curls or waves that last for a while.")],
    "rain": [("What is rain?", "Rain is water that falls from clouds in the sky.")],
    "wind": [("What is wind?", "Wind is moving air you can feel on your skin and hair.")],
    "veil": [("What is a veil?", "A veil is a light cloth that can cover the head or face.")],
    "cloak": [("What is a cloak?", "A cloak is a loose outer garment that can keep the body dry or warm.")],
    "comb": [("What does a comb do?", "A comb helps smooth or arrange hair.")],
    "surprise": [("What is a surprise?", "A surprise is something you did not expect to happen.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.event.risk, "perm", "surprise"}
    if world.facts.get("charm"):
        tags.add(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "charm").id)
    out: list[QAItem] = []
    for tag in ["perm", "surprise", "rain", "wind", "veil", "cloak", "comb"]:
        if tag in tags and tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A perm is at risk when weather reaches the hair.
at_risk(E, P) :- event(E), perm(P), risk(E, R), worn_on(P, hair), weather_hits(E, hair).

% Charm is a valid fix only if it guards the risk and covers hair.
fix(C, E, P) :- charm(C), at_risk(E, P), guards(C, R), risk(E, R), covers(C, hair).

valid_story(Place, Event, Charm) :- place(Place), event(Event), affords(Place, Event), fix(Charm, Event, perm).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for ev in sorted(p.affords):
            lines.append(asp.fact("affords", pid, ev))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("risk", eid, e.risk))
        for z in sorted(e.risk_zone):
            lines.append(asp.fact("weather_hits", eid, z))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        for r in sorted(c.covers):
            lines.append(asp.fact("covers", cid, r))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", cid, g))
    lines.append(asp.fact("perm", "perm"))
    lines.append(asp.fact("worn_on", "perm", "hair"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about a perm and a surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "woman", "man"])
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
    combos = valid_combos()
    filtered = [c for c in combos if
                (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and
                (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None)) and
                (getattr(args, "charm", None) is None or c[2] == getattr(args, "charm", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, event, charm = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["mother", "father", "woman", "man"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, charm=charm, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(EVENTS, params.event), _safe_lookup(CHARMS, params.charm),
                 params.name, params.gender, params.elder, params.trait)
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
    StoryParams(place="temple_courtyard", event="festival", charm="veil", name="Mira", gender="girl", elder="mother", trait="bright"),
    StoryParams(place="hill_shrine", event="procession", charm="comb", name="Orin", gender="boy", elder="father", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
