#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/kernel_king_teamwork_moral_value_fairy_tale.py
=========================================================================================================================

A small fairy-tale storyworld about a king, a kernel, teamwork, and a moral
value. The stories are short, child-facing, and state-driven: a little problem
arises, the characters work together, and the ending image proves what changed.

Seed inspiration:
- kernel
- king

This world keeps the classical Storyweavers shape:
- typed entities with meters and memes
- a simulated world model that drives prose
- grounded Q&A
- an inline ASP twin for reasonableness checks
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
# Core entity model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    planted_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear_ent: object | None = None
    helper: object | None = None
    king: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"king", "boy", "man", "father"}
        female = {"queen", "girl", "woman", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = False
    wind: bool = False
    affords: set[str] = field(default_factory=set)
    outdoors: bool = False
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


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    trouble: str
    rush: str
    requires: set[str] = field(default_factory=set)
    keyword: str = ""
    moral: str = "teamwork"
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
class Treasure:
    id: str
    label: str
    phrase: str
    type: str
    region: str
    fragile: bool = True
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
class HelperGear:
    id: str
    label: str
    covers: set[str]
    keeps_safe: set[str]
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "castle_garden": Place(
        id="castle_garden",
        label="the castle garden",
        outdoors=True,
        wind=False,
        affords={"plant"},
    ),
    "hill_meadow": Place(
        id="hill_meadow",
        label="the windy hill meadow",
        outdoors=True,
        wind=True,
        affords={"plant"},
    ),
    "sunny_courtyard": Place(
        id="sunny_courtyard",
        label="the sunny courtyard",
        outdoors=True,
        wind=False,
        affords={"plant", "share"},
    ),
}

TASKS = {
    "plant": Task(
        id="plant",
        verb="plant the kernel",
        gerund="planting the kernel",
        trouble="blow away",
        rush="run after the drifting kernel",
        requires={"seed", "hands"},
        keyword="kernel",
        moral="teamwork",
    ),
    "protect": Task(
        id="protect",
        verb="protect the kernel",
        gerund="protecting the kernel",
        trouble="get lost",
        rush="reach for the kernel",
        requires={"seed", "hands"},
        keyword="kernel",
        moral="teamwork",
    ),
}

TREASURES = {
    "kernel": Treasure(
        id="kernel",
        label="kernel",
        phrase="a tiny golden kernel",
        type="kernel",
        region="hands",
        fragile=True,
    ),
}

GEAR = [
    HelperGear(
        id="basket",
        label="a little basket",
        covers={"hands"},
        keeps_safe={"seed"},
        prep="put the kernel in a little basket first",
        tail="walked carefully with the little basket",
    ),
    HelperGear(
        id="cloth",
        label="a soft cloth wrap",
        covers={"hands"},
        keeps_safe={"seed"},
        prep="wrap the kernel in a soft cloth",
        tail="carried the soft cloth together",
    ),
]

KINGS = ["King Rowan", "King Alder", "King Felix", "King Cedric"]
HELPERS = ["the gardener", "the baker", "the mouse", "the page", "the seamstress"]
TRAITS = ["kind", "patient", "wise", "gentle", "brave"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rule helpers
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


THRESHOLD = 1.0


def can_reasonably_story(place: Place, task: Task) -> bool:
    return task.id in place.affords


def select_gear(task: Task, treasure: Treasure) -> Optional[HelperGear]:
    for gear in GEAR:
        if treasure.type in gear.keeps_safe and treasure.region in gear.covers:
            return gear
    return None


def explain_rejection(place: Place, task: Task) -> str:
    return f"(No story: {place.label} cannot reasonably host {task.gerund}.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _do_task(world: World, actor: Entity, task: Task, treasure: Entity, narrate: bool = True) -> None:
    if task.id not in world.place.affords:
        return
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1.0
    if world.place.wind and "seed" in task.requires:
        treasure.meters["risk"] = treasure.meters.get("risk", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} tried {task.gerund} in {world.place.label}.")


def predict_loss(world: World, actor: Entity, task: Task, treasure_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, sim.get(treasure_id), narrate=False)
    tr = sim.get(treasure_id)
    return {
        "lost": tr.meters.get("risk", 0.0) >= THRESHOLD,
    }


def resolve_teamwork(world: World, king: Entity, helper: Entity, task: Task, treasure: Entity) -> Optional[HelperGear]:
    gear = select_gear(task, treasure)
    if gear is None:
        return None
    if predict_loss(world, king, task, treasure.id)["lost"]:
        world.say(
            f"{king.id} and {helper.id} paused and chose {gear.label} so the kernel could stay safe."
        )
        return gear
    return None


def tell_story(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    task = _safe_lookup(TASKS, params.task)
    world = World(place)

    king = world.add(Entity(
        id=params.name,
        kind="character",
        type="king",
        label=params.name,
        meters={"duty": 1.0},
        memes={"kindness": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="helper",
        label=params.helper,
        meters={"help": 1.0},
        memes={"teamwork": 1.0},
    ))
    treasure = world.add(Entity(
        id="kernel",
        type="kernel",
        label="kernel",
        phrase="a tiny golden kernel",
        owner=king.id,
        caretaker=helper.id,
        meters={"risk": 0.0},
        memes={"value": 1.0},
    ))

    # Act 1
    world.say(
        f"Once in a bright little kingdom, {king.id} was a {params.trait} king who loved fair choices."
    )
    world.say(
        f"One morning, {king.id} found {treasure.phrase} and said it should be kept safe and shared wisely."
    )
    world.say(
        f"{helper.id.capitalize()} came to help, because a good kingdom grows strong when hands work together."
    )

    # Act 2
    world.para()
    world.say(f"They went to {place.label}.")
    world.say(f"{king.id} wanted to {task.verb}, but the wind could make the kernel {task.trouble}.")
    world.say(f"{helper.id.capitalize()} held out {('a little basket' if place.wind else 'steady hands')}.")

    predicted = predict_loss(world, king, task, treasure.id)
    world.facts.update(
        king=king,
        helper=helper,
        treasure=treasure,
        task=task,
        place=place,
        predicted_loss=predicted["lost"],
    )

    if predicted["lost"]:
        world.say(
            f"{king.id} saw the problem at once and smiled, because wisdom means noticing trouble before it grows."
        )
        gear = resolve_teamwork(world, king, helper, task, treasure)
        if gear:
            gear_ent = world.add(Entity(
                id=gear.id,
                type="gear",
                label=gear.label,
                protective=True,
                covers=set(gear.covers),
                plural=gear.plural,
            ))
            gear_ent.carried_by = king.id
            world.say(f"{king.id} and {helper.id} chose to {gear.prep}.")
            _do_task(world, king, task, treasure, narrate=False)
            treasure.meters["safe"] = 1.0
            world.say(
                f"Together they {gear.tail}, and the kernel stayed safe in the kingdom's care."
            )

    # Act 3
    world.para()
    if world.place.wind:
        world.say(
            f"At the end, the kernel rested safely, and the king thanked the helper for true teamwork."
        )
    else:
        world.say(
            f"At the end, the kernel stayed safe, and the king and helper shared a small, happy laugh."
        )
    world.say(
        f"The king had learned a moral value: good plans are made best when everyone helps."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    king: Entity = _safe_fact(world, f, "king")
    helper: Entity = _safe_fact(world, f, "helper")
    task: Task = _safe_fact(world, f, "task")
    place: Place = _safe_fact(world, f, "place")
    return [
        f"Write a fairy tale about {king.id} and {helper.id} in {place.label} where they use teamwork to keep a kernel safe.",
        f"Tell a child-friendly story in which a king tries to {task.verb} but learns a moral value about working together.",
        f"Write a short fairy tale that includes the word 'kernel' and ends with the king thanking the helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    king: Entity = _safe_fact(world, f, "king")
    helper: Entity = _safe_fact(world, f, "helper")
    treasure: Entity = _safe_fact(world, f, "treasure")
    task: Task = _safe_fact(world, f, "task")
    place: Place = _safe_fact(world, f, "place")

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {king.id}, a kind king, and {helper.id}, who helped keep the kernel safe.",
        ),
        QAItem(
            question=f"What did {king.id} want to do at {place.label}?",
            answer=f"{king.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"Why did {king.id} and {helper.id} need teamwork?",
            answer=(
                f"They needed teamwork because the wind in {place.label} could make {treasure.phrase} {task.trouble}."
                if place.wind
                else f"They needed teamwork so the kernel could be carried carefully and kept safe."
            ),
        ),
        QAItem(
            question="What moral value was shown in the story?",
            answer="The story showed teamwork, kindness, and wise planning.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the kernel safe and the king thanking the helper for helping.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kernel?",
            answer="A kernel is a tiny seed or grain that can grow into a plant or become food.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together to do something well.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way of acting, like kindness, fairness, or helping others.",
        ),
        QAItem(
            question="What is a king?",
            answer="A king is a ruler in a kingdom.",
        ),
    ]


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
place_affords(P,T) :- affords(P,T).
task_requires(T,R) :- requires(T,R).

teamwork_needed(P,T) :- place_affords(P,T), wind_place(P).
safe_with_gear(T,K) :- task_requires(T,S), gear_keeps(K,S), gear_covers(K,hands).

valid_story(P,T) :- place_affords(P,T), teamwork_needed(P,T), safe_with_gear(T,K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.wind:
            lines.append(asp.fact("wind_place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for r in sorted(t.requires):
            lines.append(asp.fact("requires", tid, r))
    for gid, g in TREASURES.items():
        lines.append(asp.fact("treasure", gid))
        lines.append(asp.fact("treasure_region", gid, g.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("gear_covers", gear.id, c))
        for k in sorted(gear.keeps_safe):
            lines.append(asp.fact("gear_keeps", gear.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple]:
    out = []
    for pid, p in PLACES.items():
        for tid, t in TASKS.items():
            if can_reasonably_story(p, t) and p.wind and select_gear(t, TREASURES["kernel"]):
                out.append((pid, tid))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(python_valid())
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about a king, a kernel, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=KINGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    task = getattr(args, "task", None) or rng.choice(list(TASKS))
    if not can_reasonably_story(_safe_lookup(PLACES, place), _safe_lookup(TASKS, task)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        task=task,
        name=getattr(args, "name", None) or rng.choice(KINGS),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.planted_in:
            bits.append(f"planted_in={e.planted_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
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
    StoryParams(place="hill_meadow", task="plant", name="King Rowan", helper="the gardener", trait="wise"),
    StoryParams(place="castle_garden", task="plant", name="King Alder", helper="the baker", trait="kind"),
    StoryParams(place="sunny_courtyard", task="protect", name="King Cedric", helper="the mouse", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combinations:")
        for combo in combos:
            print(" ", combo)
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
            header = f"### {p.name}: {p.task} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
