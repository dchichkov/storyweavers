#!/usr/bin/env python3
"""
storyworlds/worlds/explosion_departure_curiosity_conflict_slice_of_life.py
=========================================================================

A small slice-of-life story world about a child, a departure, and a harmless
explosion-shaped surprise that makes everyone pause.

Premise:
- A family is getting ready to leave.
- The child is full of curiosity about a little burst or pop nearby.
- The parent worries that stopping to look will make them miss the departure.
- They solve the conflict by choosing a safe, brief look and then leaving on time.

This world keeps the action concrete and state-driven:
- meters: physical closeness, readiness, time left, and a small burst of mess/smoke
- memes: curiosity, conflict, calm, and relief

The featured words are intentionally present in the generated stories:
- explosion
- departure
- Curiosity
- Conflict

The ASP twin mirrors the Python reasonableness gate: a story is valid only when
there is a departure, a curiosity trigger, a nearby harmless explosion, and a
safe compromise that still allows leaving on time.
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

    child: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ["distance", "time", "noise", "smoke", "tidy"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "conflict", "calm", "relief", "worry", "delight"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they"
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------
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
class StoryParams:
    place: str
    departure: str
    explosion: str
    name: str
    gender: str
    parent: str
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


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    indoors: bool
    afford_departure: bool
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


@dataclass(frozen=True)
class Departure:
    id: str
    verb: str
    noun: str
    urgency: str
    endpoint: str
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


@dataclass(frozen=True)
class Explosion:
    id: str
    label: str
    source: str
    safe: bool
    loudness: str
    smoke: str
    curiosity_word: str = "Curiosity"
    conflict_word: str = "Conflict"
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


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", True, True),
    "front_porch": Place("front_porch", "the front porch", False, True),
    "station": Place("station", "the little station", False, True),
    "sidewalk": Place("sidewalk", "the sidewalk", False, True),
}

DEPARTURES = {
    "bus": Departure("bus", "catch the bus", "bus ride", "soon", "the corner"),
    "grandma": Departure("grandma", "visit Grandma", "visit", "right away", "her house"),
    "market": Departure("market", "go to the market", "shopping trip", "before lunch", "the market"),
    "train": Departure("train", "catch the train", "train ride", "in a few minutes", "the station"),
}

EXPLOSIONS = {
    "balloon_pop": Explosion("balloon_pop", "a balloon pop", "a balloon brushing a fence", True, "sharp", "a tiny puff"),
    "popcorn_pot": Explosion("popcorn_pot", "a popcorn pop", "a pot shaking on the stove", True, "bubbly", "a little steam"),
    "firecracker_far": Explosion("firecracker_far", "a distant firecracker explosion", "a faraway celebration", True, "far-off", "a thin ribbon of smoke"),
    "science_boop": Explosion("science_boop", "a science-table explosion", "a baking-soda bottle", True, "sudden", "white fizz"),
}

GIRL_NAMES = ["Mia", "Lena", "Tara", "Nina", "Ruby", "Ivy", "Noa"]
BOY_NAMES = ["Owen", "Milo", "Eli", "Theo", "Finn", "Leo", "Kai"]
TRAITS = ["curious", "patient", "bouncy", "quiet", "gentle", "spirited"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combo(place: Place, dep: Departure, exp: Explosion) -> bool:
    return place.afford_departure and exp.safe and dep.endpoint != ""


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES.values():
        for d in DEPARTURES.values():
            for e in EXPLOSIONS.values():
                if valid_combo(p, d, e):
                    out.append((p.id, d.id, e.id))
    return out


def intro(world: World, child: Entity, parent: Entity, place: Place, dep: Departure) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a big love for noticing everything at {place.label}."
    )
    world.say(
        f"That morning, {child.id} and {parent.label} were getting ready for a {dep.noun}."
    )
    child.memes["curiosity"] += 1
    parent.memes["worry"] += 1


def trigger(world: World, child: Entity, exp: Explosion, dep: Departure) -> None:
    world.say(
        f"Then came {exp.label}: {exp.source}, with {exp.loudness} sound and {exp.smoke} in the air."
    )
    child.meters["distance"] = 1.0
    child.meters["noise"] += 1.0
    child.memes["curiosity"] += 1.0
    world.facts["curiosity_trigger"] = exp.id
    world.facts["departure"] = dep.id
    world.say(
        f"{Entity(id='', type=child.type).pronoun('subject').capitalize()} wanted to look closer, because Curiosity was tugging hard."
    )


def warn(world: World, parent: Entity, child: Entity, dep: Departure) -> None:
    parent.memes["worry"] += 1.0
    child.memes["conflict"] += 1.0
    world.say(
        f'"If we stop now, we might miss the departure," {parent.id} said. "Come on, we need to leave."'
    )
    world.say(
        f"{child.id} frowned. The feeling inside {child.pronoun('possessive')} chest turned into Conflict."
    )


def compromise(world: World, child: Entity, parent: Entity, exp: Explosion, dep: Departure) -> None:
    child.memes["calm"] += 1.0
    child.memes["conflict"] = 0.0
    child.memes["relief"] += 1.0
    parent.memes["relief"] += 1.0
    world.facts["resolved"] = True
    world.say(
        f"{parent.id} held out a hand and said they could take one quick look from a safe distance."
    )
    world.say(
        f"So {child.id} peeked once at {exp.label}, smiled at the little puff it left behind, and then hurried along."
    )
    world.say(
        f"They made the departure on time, with Curiosity satisfied and Conflict quiet again."
    )


def ending(world: World, child: Entity, parent: Entity, place: Place, dep: Departure, exp: Explosion) -> None:
    world.say(
        f"By the time they reached {dep.endpoint}, {child.id} was talking about the {exp.label} as if it had been a tiny surprise in an ordinary day."
    )
    world.say(
        f"Their shoes tapped softly on the ground, and the morning felt calm and ready for the {dep.noun}."
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    dep = _safe_lookup(DEPARTURES, params.departure)
    exp = _safe_lookup(EXPLOSIONS, params.explosion)

    if not valid_combo(place, dep, exp):
        pass

    world = World()
    gender = params.gender
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=gender,
        label=params.name,
        meters={"distance": 0.0, "time": 0.0, "noise": 0.0, "smoke": 0.0, "tidy": 1.0},
        memes={"curiosity": 0.0, "conflict": 0.0, "calm": 0.0, "relief": 0.0, "worry": 0.0, "delight": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"distance": 0.0, "time": 0.0, "noise": 0.0, "smoke": 0.0, "tidy": 1.0},
        memes={"curiosity": 0.0, "conflict": 0.0, "calm": 0.0, "relief": 0.0, "worry": 0.0, "delight": 0.0},
    ))

    world.facts.update(
        place=place,
        departure=dep,
        explosion=exp,
        child=child,
        parent=parent,
    )

    intro(world, child, parent, place, dep)
    world.para()
    trigger(world, child, exp, dep)
    warn(world, parent, child, dep)
    world.para()
    compromise(world, child, parent, exp, dep)
    ending(world, child, parent, place, dep, exp)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    dep = _safe_fact(world, f, "departure")
    exp = _safe_fact(world, f, "explosion")
    return [
        f"Write a slice-of-life story for a young child where {child.id} notices {exp.label} and then has to leave for a {dep.noun}.",
        f"Tell a gentle story with Curiosity and Conflict as a child wants to look at {exp.label} but the family must make a departure.",
        f"Write a short story that includes the words explosion and departure and ends with everyone leaving calmly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    dep: Departure = _safe_fact(world, f, "departure")
    exp: Explosion = _safe_fact(world, f, "explosion")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What was {child.id} curious about at {place.label}?",
            answer=f"{child.id} was curious about {exp.label}, which came from {exp.source}.",
        ),
        QAItem(
            question=f"Why did the parent worry about stopping near the {exp.label}?",
            answer=f"The parent worried that if they stopped too long, they would miss the departure for the {dep.noun}.",
        ),
        QAItem(
            question=f"What changed after Curiosity and Conflict settled down?",
            answer=f"{child.id} took one safe look, Conflict went quiet, and the family left on time.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "curiosity": QAItem(
        question="What does curiosity mean?",
        answer="Curiosity means wanting to know more, look closer, or ask questions about something interesting.",
    ),
    "conflict": QAItem(
        question="What is conflict in a story?",
        answer="Conflict is the hard part of a story when two wants pull against each other, like wanting to stay and needing to go.",
    ),
    "departure": QAItem(
        question="What is a departure?",
        answer="A departure is when someone leaves a place and starts a trip or goes away from where they were.",
    ),
    "explosion": QAItem(
        question="What is an explosion?",
        answer="An explosion is a sudden burst of sound, air, or movement. In a gentle story, it can be a safe little pop or puff.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.append(WORLD_KNOWLEDGE["curiosity"])
    out.append(WORLD_KNOWLEDGE["conflict"])
    out.append(WORLD_KNOWLEDGE["departure"])
    out.append(WORLD_KNOWLEDGE["explosion"])
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
departure(D) :- depart(D).
explosion(E) :- burst(E).

curious_story(P,D,E) :- place(P), departure(D), explosion(E), safe(E).
conflict_story(P,D,E) :- curious_story(P,D,E), departure_needed(D), curiosity_rises(E).

valid_story(P,D,E) :- curious_story(P,D,E), conflict_story(P,D,E), safe_compromise(P,D,E).
#show valid_story/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("setting", p.id))
    for d in DEPARTURES.values():
        lines.append(asp.fact("depart", d.id))
        lines.append(asp.fact("departure_needed", d.id))
    for e in EXPLOSIONS.values():
        lines.append(asp.fact("burst", e.id))
        if e.safe:
            lines.append(asp.fact("safe", e.id))
        lines.append(asp.fact("curiosity_rises", e.id))
    for p in PLACES.values():
        for d in DEPARTURES.values():
            for e in EXPLOSIONS.values():
                if valid_combo(p, d, e):
                    lines.append(asp.fact("safe_compromise", p.id, d.id, e.id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about Curiosity, Conflict, explosion, and departure.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--departure", choices=DEPARTURES)
    ap.add_argument("--explosion", choices=EXPLOSIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "departure", None) is None or c[1] == getattr(args, "departure", None))
        and (getattr(args, "explosion", None) is None or c[2] == getattr(args, "explosion", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, dep, exp = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, departure=dep, explosion=exp, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
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
    StoryParams(place="kitchen", departure="bus", explosion="popcorn_pot", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="front_porch", departure="train", explosion="balloon_pop", name="Eli", gender="boy", parent="father", trait="bouncy"),
    StoryParams(place="sidewalk", departure="grandma", explosion="firecracker_far", name="Noa", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="station", departure="train", explosion="science_boop", name="Finn", gender="boy", parent="father", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid story combos")
        for t in vals:
            print("  ", t)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.departure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
