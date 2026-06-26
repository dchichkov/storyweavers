#!/usr/bin/env python3
"""
storyworlds/worlds/marathon_bold_kindness_slice_of_life.py
==========================================================

A small story world about a community marathon, a bold child, and kindness
showing up in quiet, ordinary ways.

The core seed image is simple:
A child wants to run a marathon. Something small goes wrong before the race.
The child makes a bold choice to help someone else, and that kindness changes
how the day feels.

This world keeps the domain close to slice-of-life: sidewalks, shoes, bibs,
water cups, neighbors, encouragement, a little worry, and a warm finish.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    hero: object | None = None
    other: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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


@dataclass
class Place:
    id: str
    name: str
    supports: set[str] = field(default_factory=set)
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
class EventKind:
    id: str
    verb: str
    gerund: str
    place_hint: str
    risk: str
    score_key: str
    zone: str
    theme_word: str = ""
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
class ItemKind:
    id: str
    label: str
    phrase: str
    body_part: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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


@dataclass
class AidKind:
    id: str
    label: str
    protects: set[str]
    helps: set[str]
    offer: str
    ending: str
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
        self.events: list[str] = []
        self.fired: set[tuple] = set()
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

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.events = []
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "neighborhood": Place("neighborhood", "the neighborhood", {"run", "stretch", "hydrate"}),
    "school_track": Place("school_track", "the school track", {"run", "stretch", "hydrate"}),
    "park_loop": Place("park_loop", "the park loop", {"run", "stretch", "hydrate"}),
    "downtown": Place("downtown", "the downtown route", {"run", "stretch", "hydrate"}),
}

EVENTS = {
    "marathon": EventKind(
        id="marathon",
        verb="run the marathon",
        gerund="running the marathon",
        place_hint="route",
        risk="tired",
        score_key="endurance",
        zone="feet",
        theme_word="marathon",
        tags={"race", "run", "finish"},
    ),
    "relay": EventKind(
        id="relay",
        verb="run a relay leg",
        gerund="running a relay leg",
        place_hint="track",
        risk="tired",
        score_key="endurance",
        zone="feet",
        theme_word="relay",
        tags={"race", "run", "team"},
    ),
    "fun_run": EventKind(
        id="fun_run",
        verb="join the fun run",
        gerund="joining the fun run",
        place_hint="park",
        risk="tired",
        score_key="endurance",
        zone="feet",
        theme_word="run",
        tags={"race", "run", "community"},
    ),
}

ITEMS = {
    "bib": ItemKind("bib", "race bib", "a paper race bib", "torso"),
    "shoes": ItemKind("shoes", "running shoes", "new running shoes", "feet", plural=True),
    "hat": ItemKind("hat", "cap", "a sun cap", "head"),
    "medal": ItemKind("medal", "finisher medal", "a small finisher medal", "torso"),
}

AIDS = {
    "lace_knot": AidKind(
        id="lace_knot",
        label="a double knot",
        protects={"loose_lace"},
        helps={"feet"},
        offer="tie your shoelaces in a double knot first",
        ending="tied the double knot",
    ),
    "water_cup": AidKind(
        id="water_cup",
        label="a water cup",
        protects={"dry_throat"},
        helps={"hydrate"},
        offer="take a water cup and walk to the next station together",
        ending="carried water to the next station",
    ),
    "extra_shoes": AidKind(
        id="extra_shoes",
        label="spare shoes",
        protects={"mud"},
        helps={"feet"},
        offer="borrow the spare shoes from the locker room",
        ending="borrowed the spare shoes",
        plural=True,
    ),
    "kind_words": AidKind(
        id="kind_words",
        label="kind words",
        protects={"worry"},
        helps={"heart"},
        offer="say a few kind words and start together",
        ending="said kind words and started together",
    ),
}

NAMES = {
    "girl": ["Maya", "Lina", "Zoey", "Nora", "Ava", "Ella"],
    "boy": ["Eli", "Noah", "Finn", "Theo", "Max", "Leo"],
}
TRAITS = ["bold", "gentle", "curious", "steady", "cheerful", "quiet"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for event_id in place.supports:
            ev = _safe_lookup(EVENTS, event_id)
            for prize_id, prize in ITEMS.items():
                if prize.body_part == ev.zone:
                    combos.append((place_id, event_id, prize_id))
    return combos


def prize_at_risk(event: EventKind, prize: ItemKind) -> bool:
    return prize.body_part == event.zone


def choose_aid(event: EventKind, prize: ItemKind) -> Optional[AidKind]:
    for aid in AIDS.values():
        if event.zone in aid.helps and event.risk in aid.protects:
            return aid
        if event.zone in aid.helps and prize.body_part == event.zone and event.id == "marathon" and aid.id == "lace_knot":
            return aid
    if event.id == "marathon" and prize.id == "shoes":
        return AIDS["lace_knot"]
    if event.id == "fun_run":
        return AIDS["kind_words"]
    return None


def explain_rejection(event: EventKind, prize: ItemKind) -> str:
    if not prize_at_risk(event, prize):
        return (
            f"(No story: {event.gerund} does not threaten {prize.label}, "
            f"so there is no real problem to solve.)"
        )
    return "(No story: no reasonable aid in this tiny world can fix that combination.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, event: EventKind, prize_id: str) -> dict:
    sim = world.copy()
    _do_event(sim, sim.get(hero.id), event, narrate=False)
    prize = sim.get(prize_id)
    return {
        "risk": prize.meters.get("scuffed", 0.0) >= THRESHOLD,
        "worry": sim.get(hero.id).memes.get("worry", 0.0),
    }


def _do_event(world: World, actor: Entity, event: EventKind, narrate: bool = True) -> None:
    actor.meters[event.score_key] = actor.meters.get(event.score_key, 0.0) + 1.0
    actor.memes["energy"] = actor.memes.get("energy", 0.0) + 1.0
    if event.id == "marathon":
        actor.memes["focus"] = actor.memes.get("focus", 0.0) + 1.0
    if event.id == "relay":
        actor.memes["team"] = actor.memes.get("team", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} started {event.gerund}.")


def apply_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("endurance", 0.0) < THRESHOLD:
            continue
        for e in list(world.entities.values()):
            if e.owner != actor.id:
                continue
            if e.kind == "thing" and e.type == "running shoes":
                sig = ("risk", actor.id, e.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                e.meters["scuffed"] = e.meters.get("scuffed", 0.0) + 1.0
                out.append(f"{actor.pronoun('possessive').capitalize()} shoes got scuffed.")
    return out


def apply_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = next((c for c in world.characters() if c.memes.get("kindness", 0.0) >= THRESHOLD), None)
    if hero is None:
        return out
    if world.facts.get("need_help") and not world.facts.get("helped"):
        world.facts["helped"] = True
        helper = world.get(hero.id)
        other = world.get(world.facts["other"])
        other.memes["relief"] = other.memes.get("relief", 0.0) + 1.0
        helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1.0
        out.append(f"{helper.id} helped {other.id} first.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for sent in apply_risk(world):
            produced.append(sent)
            changed = True
        for sent in apply_kindness(world):
            produced.append(sent)
            changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Place, event: EventKind, prize_cfg: ItemKind,
         hero_name: str = "Maya", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"endurance": 0.0},
        memes={"bold": 1.0, "kindness": 1.0, "hope": 1.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    other = world.add(Entity(
        id="Neighbor",
        kind="character",
        type="boy",
        meters={"worry": 1.0},
        memes={"worry": 1.0},
    ))
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["prize"] = prize
    world.facts["event"] = event
    world.facts["other"] = other
    world.facts["setting"] = setting

    trait = next((t for t in (hero_traits or []) if t != "bold"), None)

    world.say(f"{hero.id} was a {('bold ' + trait) if trait else 'bold'} {hero.type} who loved ordinary mornings.")
    world.say(f"{hero.id} wanted to {event.verb}, and {hero.pronoun('possessive')} {parent.type} had bought {hero.pronoun('object')} {prize_cfg.phrase}.")
    world.say(f"{hero.id} liked how {prize_cfg.label} felt before the race began.")

    world.say(f"At {setting.name}, the neighbors were already lining up, and the air felt busy and kind.")
    world.say(f"{hero.id} looked toward the starting line and then toward {other.id}, who was standing too close to the curb.")

    if event.id == "marathon":
        world.facts["need_help"] = True
    elif event.id == "fun_run":
        world.facts["need_help"] = True
    else:
        world.facts["need_help"] = False

    if world.facts["need_help"]:
        world.say(f"{hero.id} wanted to start right away, but {other.id}'s shoelace was trailing on the ground.")
        world.say(f"{hero.id} felt a bold little pause, then knelt down to help.")

    hero.memes["kindness"] += 1.0
    other.memes["relief"] += 1.0
    world.facts["helped"] = True
    world.say(f"{hero.id} tied the lace and smiled, and {other.id} smiled back like the day had opened up.")

    _do_event(world, hero, event, narrate=True)
    propagate(world, narrate=True)

    aid = choose_aid(event, prize_cfg)
    if aid:
        world.facts["aid"] = aid
        if event.id == "marathon" and prize_cfg.id == "shoes":
            world.say(f"{hero.pronoun('possessive').capitalize()} {parent.type} said, \"Let's {aid.offer}.\"")
            world.say(f"So they {aid.ending}, and {hero.id} could keep going without tripping.")
            prize.meters["scuffed"] = 0.0
        elif event.id == "fun_run":
            world.say(f"{hero.pronoun('possessive').capitalize()} {parent.type} said, \"Let's {aid.offer}.\"")
            world.say(f"So they {aid.ending}, and the whole start felt calmer.")
        else:
            world.say(f"They chose {aid.label} and kept the day easy.")
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    world.say(f"By the finish, {hero.id} was still {event.gerund}, and the air felt bright with good effort.")
    world.say(f"{hero.id} crossed the line with a clean smile, and the little act of kindness mattered as much as the race.")

    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


PRIZE_GENDER = {
    "bib": {"girl", "boy"},
    "shoes": {"girl", "boy"},
    "hat": {"girl", "boy"},
    "medal": {"girl", "boy"},
}

CURATED = [
    StoryParams("neighborhood", "marathon", "shoes", "Maya", "girl", "mother", "bold"),
    StoryParams("school_track", "relay", "bib", "Eli", "boy", "father", "gentle"),
    StoryParams("park_loop", "fun_run", "hat", "Nora", "girl", "mother", "cheerful"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    event = _safe_fact(world, f, "event")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a warm slice-of-life story about a bold child named {hero.id} and a marathon.',
        f"Tell a gentle story where {hero.id} wants to {event.verb} while wearing {prize.phrase}, and kindness changes the day.",
        f"Write a simple story about a race, a small problem, and a helpful choice that keeps the mood kind.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    event = _safe_fact(world, f, "event")
    other = _safe_fact(world, f, "other")
    place = _safe_fact(world, f, "setting").name
    return [
        QAItem(
            question=f"Who was the story mostly about at {place}?",
            answer=f"The story was mostly about {hero.id}, a bold child who wanted to {event.verb} and keep the day kind.",
        ),
        QAItem(
            question=f"What small problem happened before {hero.id} started {event.gerund}?",
            answer=f"{other.id}'s shoelace was loose, so {hero.id} stopped to help before the race began.",
        ),
        QAItem(
            question=f"What did {hero.id}'s {parent.type} buy for the race?",
            answer=f"{hero.id}'s {parent.type} bought {prize.phrase}, and {hero.id} loved wearing {prize.label} for the day.",
        ),
        QAItem(
            question=f"How did kindness change what happened at the start?",
            answer=f"{hero.id} helped {other.id} first, and that made the start calmer and happier for everyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    event = _safe_fact(world, f, "event")
    out = [
        QAItem(
            question="What is a marathon?",
            answer="A marathon is a very long running race, so runners need practice, water, and steady effort.",
        ),
        QAItem(
            question="What does it mean to be bold?",
            answer="Being bold means you can do something brave or tricky even when you feel a little nervous.",
        ),
        QAItem(
            question="Why do runners tie their shoes carefully?",
            answer="Runners tie their shoes carefully so the laces do not come undone and trip them during the race.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, or speaking gently so someone else feels cared for.",
        ),
    ]
    if event.id == "relay":
        out.append(QAItem(
            question="What is a relay race?",
            answer="A relay race is a team race where runners take turns and pass the job to the next person.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"events: {world.events}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
event(E) :- activity(E).
item(I) :- prize(I).

valid_story(P,E,I) :- place(P), event(E), item(I), affords(P,E),
                      zone_of(E,Z), body_part(I,Z).

needs_kindness(E) :- event(E), (E = marathon; E = fun_run; E = relay).
helpable(E) :- needs_kindness(E).

% The declarative gate mirrors the Python one: a story is reasonable only when
% the prize is worn on the same body zone the event threatens.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        for e in sorted(place.supports):
            lines.append(asp.fact("affords", pid, e))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("activity", eid))
        lines.append(asp.fact("zone_of", eid, ev.zone))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("prize", iid))
        lines.append(asp.fact("body_part", iid, item.body_part))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP and Python agree on {len(py)} valid combos.")
        return 0
    print("MISMATCH:")
    if py - asp_set:
        print(" only Python:", sorted(py - asp_set))
    if asp_set - py:
        print(" only ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: marathon, bold, kindness, slice of life.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "event", None) and getattr(args, "prize", None):
        ev = _safe_lookup(EVENTS, getattr(args, "event", None))
        pr = _safe_lookup(ITEMS, getattr(args, "prize", None))
        if not prize_at_risk(ev, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, event, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, event, prize, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(EVENTS, params.event),
        _safe_lookup(ITEMS, params.prize),
        params.name,
        params.gender,
        [params.trait, "bold"],
        params.parent,
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.event} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
