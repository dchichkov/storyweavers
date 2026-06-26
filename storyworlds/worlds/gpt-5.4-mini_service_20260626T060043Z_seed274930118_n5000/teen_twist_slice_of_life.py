#!/usr/bin/env python3
"""
storyworlds/worlds/teen_twist_slice_of_life.py
==============================================

A small slice-of-life teen story world with a gentle twist:
a careful plan gets nudged by a tiny everyday surprise, and the characters
choose the kind, practical version of the day.

Premise:
- A teen wants to do one ordinary thing after school.
- Something small goes sideways: a message, a forgotten item, a rain shift,
  a schedule change.
- The teen feels the wobble, then adapts with help.

World model:
- Typed entities with physical meters and emotional memes.
- State changes drive the prose, so the ending image proves what changed.
- The twist is not a fantasy shock; it is a realistic shift in plans that
  changes the teen's mood and next move.
"""

from __future__ import annotations

import argparse
import copy
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
# Small story world constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities and world state
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    guardian: object | None = None
    teen: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "nerves": 0.0,
                "annoyance": 0.0,
                "relief": 0.0,
                "trust": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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


@dataclass
class Place:
    name: str
    indoor: bool
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


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    twist: str
    mess: str
    zone: set[str]
    weather: str
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


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
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


@dataclass
class Gear:
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "school": Place(name="the school courtyard", indoor=False, affords={"study", "walk", "chat"}),
    "library": Place(name="the library", indoor=True, affords={"study", "chat"}),
    "cafe": Place(name="the corner cafe", indoor=True, affords={"chat", "study"}),
    "park": Place(name="the neighborhood park", indoor=False, affords={"walk", "chat"}),
}

ACTIVITIES = {
    "study": Activity(
        id="study",
        verb="study for the quiz",
        gerund="studying for the quiz",
        rush="rush to finish the notes",
        twist="the quiz date moved earlier",
        mess="scattered",
        zone={"desk"},
        weather="",
        keyword="notes",
        tags={"study", "school"},
    ),
    "walk": Activity(
        id="walk",
        verb="take a walk",
        gerund="walking slowly",
        rush="head out too fast",
        twist="the sky turned gray",
        mess="wet",
        zone={"shoes", "hood"},
        weather="rainy",
        keyword="rain",
        tags={"walk", "weather"},
    ),
    "chat": Activity(
        id="chat",
        verb="meet a friend",
        gerund="chatting at an easy pace",
        rush="run over to the table",
        twist="the friend arrived with one extra seat in mind",
        mess="spilled",
        zone={"table"},
        weather="",
        keyword="text",
        tags={"friend", "social"},
    ),
}

PRIZES = {
    "notebook": Prize(
        label="notebook",
        phrase="a neat spiral notebook",
        type="notebook",
        region="desk",
    ),
    "sneakers": Prize(
        label="sneakers",
        phrase="fresh white sneakers",
        type="sneakers",
        region="shoes",
        plural=True,
    ),
    "jacket": Prize(
        label="jacket",
        phrase="a light denim jacket",
        type="jacket",
        region="hood",
    ),
    "lunch": Prize(
        label="lunchbox",
        phrase="a bright lunchbox",
        type="lunchbox",
        region="table",
    ),
}

GEAR = [
    Gear(
        id="umbrella",
        label="an umbrella",
        covers={"hood", "shoes"},
        guards={"wet"},
        prep="grab an umbrella",
        tail="walked back out with the umbrella",
    ),
    Gear(
        id="zipbag",
        label="a zip bag",
        covers={"desk"},
        guards={"scattered"},
        prep="put the notes in a zip bag",
        tail="carried the notes in a zip bag",
    ),
    Gear(
        id="tray",
        label="a small tray",
        covers={"table"},
        guards={"spilled"},
        prep="move the drink to a small tray",
        tail="set the drink on a small tray",
    ),
]

TEEN_NAMES = ["Maya", "Noah", "Ava", "Eli", "Zoe", "Sam", "Nina", "Leo", "Iris", "Jules"]
FRIEND_NAMES = ["Tara", "Milo", "Ruby", "Finn", "Nadia", "Owen"]
GUARDIAN_NAMES = ["Mom", "Dad", "Auntie", "Uncle", "Guardian"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    friend: str
    guardian: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for act_id in place.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place_id, act_id, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly affect {prize.label}, "
        f"so there is no real problem to solve.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------


def _dirt(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if actor.meters["mess"] < THRESHOLD:
                continue
            if item.protective:
                continue
            if item.region not in ACTIVITIES[world.facts["activity"].id].zone:
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] += 1
            out.append(f"{item.label.capitalize()} got messed up.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    out.extend(_dirt(world))
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    sim_actor = sim.get(actor.id)
    sim_actor.meters["mess"] += 1
    sim.facts["activity"] = activity
    propagate(sim, narrate=False)
    prize = sim.get(prize_id)
    return prize.meters["damage"] >= THRESHOLD


def introduce(world: World, teen: Entity) -> None:
    world.say(
        f"{teen.id} was a little {teen.type} who liked ordinary days that felt steady and kind."
    )


def setup(world: World, teen: Entity, friend: Entity, guardian: Entity, prize: Entity, activity: Activity) -> None:
    teen.memes["joy"] += 1
    teen.memes["trust"] += 1
    prize.worn_by = teen.id
    world.say(
        f"{teen.id} had plans to {activity.verb} with {friend.id}, and {teen.pronoun('possessive')} "
        f"{guardian.id} had helped {teen.pronoun('object')} get ready."
    )
    world.say(
        f"{teen.id} kept {teen.pronoun('possessive')} {prize.label} close because {prize.phrase} "
        f"made the day feel put together."
    )


def twist_and_warning(world: World, teen: Entity, guardian: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict_mess(world, teen, activity, prize.id):
        return False
    teen.memes["nerves"] += 1
    world.say(
        f"Then came the twist: {activity.twist}. {guardian.id} glanced at {prize.phrase} and said, "
        f"\"That could get messy.\""
    )
    return True


def feel_wobble(world: World, teen: Entity, activity: Activity) -> None:
    teen.memes["annoyance"] += 1
    world.say(
        f"{teen.id} frowned for a second, because {teen.pronoun('possessive')} easy plan had just wobbled."
    )
    world.say(f"{teen.id} wanted to {activity.rush}, but {teen.id} stopped first.")


def offer_fix(world: World, guardian: Entity, teen: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    world.say(
        f"Then {guardian.id} smiled and said, \"How about we {gear.prep}?\""
    )
    new_gear = world.add(
        Entity(
            id=gear.id,
            kind="thing",
            type="gear",
            label=gear.label,
            protective=True,
            owner=teen.id,
            caretaker=guardian.id,
            plural=gear.plural,
            covers=set(gear.covers),
        )
    )
    new_gear.worn_by = teen.id if gear.id != "tray" else None
    return gear


def accept_fix(world: World, teen: Entity, friend: Entity, guardian: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    teen.memes["joy"] += 1
    teen.memes["relief"] += 1
    teen.memes["nerves"] = max(0.0, teen.memes["nerves"] - 1)
    teen.memes["annoyance"] = 0.0
    world.say(
        f"{teen.id} exhaled, and the tension in {teen.pronoun('possessive')} shoulders eased."
    )
    world.say(
        f"{teen.id}, {friend.id}, and {guardian.id} used {gear.label}, and soon the day fit again."
    )
    world.say(
        f"In the end, {teen.id} was {activity.gerund}, {prize.phrase} stayed safe, and the three of them "
        f"walked on with calmer faces."
    )


def tell(place: Place, activity: Activity, prize_cfg: Prize, teen_name: str, gender: str, friend_name: str, guardian_name: str) -> World:
    world = World(place)
    world.weather = activity.weather if not place.indoor else ""

    teen = world.add(Entity(id=teen_name, kind="character", type=gender, label=teen_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", label=friend_name))
    guardian = world.add(Entity(id=guardian_name, kind="character", type="adult", label=guardian_name))
    prize = world.add(
        Entity(
            id="prize",
            kind="thing",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=teen.id,
            caretaker=guardian.id,
            plural=prize_cfg.plural,
        )
    )

    world.facts.update(activity=activity, prize=prize, teen=teen, friend=friend, guardian=guardian)

    introduce(world, teen)
    setup(world, teen, friend, guardian, prize, activity)
    world.para()
    world.say(f"After school, they went to {place.name}.")
    if twist_and_warning(world, teen, guardian, activity, prize):
        feel_wobble(world, teen, activity)
        gear = offer_fix(world, guardian, teen, activity, prize)
        if gear:
            accept_fix(world, teen, friend, guardian, activity, prize, gear)

    return world


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    teen = _safe_fact(world, f, "teen")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f"Write a gentle slice-of-life story about a teen named {teen.id} whose after-school plan gets a small twist.",
        f"Tell a realistic story where {teen.id} wants to {act.verb} but needs to keep {prize.phrase} safe.",
        f"Write a short teen story with an ordinary twist, a careful fix, and a calm ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    teen = _safe_fact(world, f, "teen")
    guardian = _safe_fact(world, f, "guardian")
    friend = _safe_fact(world, f, "friend")
    activity = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")

    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was mainly about {teen.id}, a teen who wanted an ordinary day to stay nice and steady.",
        ),
        QAItem(
            question=f"What did {teen.id} want to do after school?",
            answer=f"{teen.id} wanted to {activity.verb} with {friend.id}. That was the plan before the twist showed up.",
        ),
        QAItem(
            question=f"Why did {guardian.id} worry about {prize.phrase}?",
            answer=f"{guardian.id} worried because {activity.twist.lower()}, and {prize.phrase} could get messed up if they kept going without a fix.",
        ),
        QAItem(
            question=f"What helped {teen.id} keep {prize.label} safe?",
            answer=f"They used {select_gear(activity, prize).label if select_gear(activity, prize) else 'a careful fix'} so {teen.id} could keep going without ruining {prize.phrase}.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "study": [
        QAItem(
            question="Why do people use notes when they study?",
            answer="People use notes to remember important things and to review them later when they are trying to learn.",
        )
    ],
    "weather": [
        QAItem(
            question="What does it mean when the sky turns gray before rain?",
            answer="A gray sky can mean clouds are getting thick and the weather may change soon.",
        )
    ],
    "friend": [
        QAItem(
            question="Why is it nice to meet a friend after school?",
            answer="It is nice because friends can make an ordinary day feel lighter, warmer, and more fun.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protected(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), protected(_,A,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only Python:", sorted(py - cl))
    if cl - py:
        print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="school", activity="study", prize="notebook", name="Maya", gender="girl", friend="Tara", guardian="Mom"),
    StoryParams(place="park", activity="walk", prize="jacket", name="Noah", gender="boy", friend="Finn", guardian="Dad"),
    StoryParams(place="cafe", activity="chat", prize="lunch", name="Ava", gender="girl", friend="Ruby", guardian="Auntie"),
    StoryParams(place="library", activity="study", prize="notebook", name="Jules", gender="girl", friend="Nadia", guardian="Guardian"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Teen slice-of-life story world with a small twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--guardian")
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, prize = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(TEEN_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    guardian = getattr(args, "guardian", None) or rng.choice(GUARDIAN_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, friend=friend, guardian=guardian)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.friend,
        params.guardian,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
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
