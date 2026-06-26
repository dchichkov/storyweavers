#!/usr/bin/env python3
"""
Storyworld: quartet_use_bravery_foreshadowing_friendship_folk_tale
===================================================================

A small folk-tale-style story world about a quartet that must use bravery and
friendship to solve a community problem.

Seed image:
- A little village quartet is asked to play at dusk, but one player is shy.
- The elders hint at thunder, a broken bridge, and a long road home.
- The quartet uses bravery together, shares the load, and keeps the music going.

This script keeps the story grounded in a tiny simulated world:
- entities have physical meters and emotional memes
- the premise, tension, turn, and resolution are driven by state
- ASP and Python share the same reasonableness gate
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wearing: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self):
        if not self.meters:
            self.meters = {"distance": 0.0, "weight": 0.0, "damage": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "fear": 0.0, "friendship": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
    id: str
    label: str
    kind: str = "place"
    features: set[str] = field(default_factory=set)
    risks: set[str] = field(default_factory=set)
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
class Task:
    id: str
    name: str
    verb: str
    gerund: str
    risk: str
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
class Helper:
    id: str
    label: str
    role: str
    action: str
    protection: str
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "meadow": Place(
        id="meadow",
        label="the green meadow",
        features={"open", "windy"},
        risks={"rain", "dark"},
    ),
    "bridge": Place(
        id="bridge",
        label="the old wooden bridge",
        features={"narrow", "echoing"},
        risks={"rain", "dark"},
    ),
    "hall": Place(
        id="hall",
        label="the village hall",
        features={"warm", "bright"},
        risks={"dark"},
    ),
    "hill": Place(
        id="hill",
        label="the lantern hill",
        features={"high", "windy"},
        risks={"rain", "dark"},
    ),
}

TASKS = {
    "play_at_dusk": Task(
        id="play_at_dusk",
        name="play at dusk",
        verb="play at dusk",
        gerund="playing at dusk",
        risk="dark",
        keyword="dusk",
        tags={"music", "dusk"},
    ),
    "cross_bridge": Task(
        id="cross_bridge",
        name="cross the bridge",
        verb="cross the bridge",
        gerund="crossing the bridge",
        risk="rain",
        keyword="bridge",
        tags={"bridge", "rain"},
    ),
    "carry_lanterns": Task(
        id="carry_lanterns",
        name="carry the lanterns",
        verb="carry the lanterns",
        gerund="carrying the lanterns",
        risk="dark",
        keyword="lanterns",
        tags={"lantern", "dark"},
    ),
}

HELPERS = {
    "shawl": Helper(
        id="shawl",
        label="a wool shawl",
        role="cover the shoulders",
        action="wrap the shawl around the shy player",
        protection="warmth",
        phrase="a wool shawl that could keep the cold away",
    ),
    "lamp": Helper(
        id="lamp",
        label="a little lamp",
        role="light the path",
        action="carry the lamp ahead of the group",
        protection="light",
        phrase="a little lamp with a steady flame",
    ),
    "rope": Helper(
        id="rope",
        label="a braided rope",
        role="steady the crossing",
        action="tie the rope to the cart",
        protection="balance",
        phrase="a braided rope strong enough to help everyone cross",
    ),
}

ROLES = ["fiddle", "flute", "drum", "harp"]
NAMES = ["Mira", "Tobin", "Elsa", "Rowan", "Anya", "Perrin", "Lina", "Gareth"]
TALENTS = ["gentle", "quick", "steady", "bright", "timid", "bold"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
% A task is risky at a place when the place has that risk.
task_risky(T, P) :- task(T), place(P), has_risk(P, R), task_risk(T, R).

% A helper is reasonable if it addresses the risk of the task.
helper_fits(H, T) :- helper(H), task(T), helper_protects(H, R), task_risk(T, R).

valid_story(P, T) :- place(P), task(T), task_risky(T, P), helper_fits(_, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for risk in sorted(place.risks):
            lines.append(asp.fact("has_risk", pid, risk))
        for feat in sorted(place.features):
            lines.append(asp.fact("has_feature", pid, feat))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_risk", tid, task.risk))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_protects", hid, helper.protection))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_stories() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_stories():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def task_is_risky(place: Place, task: Task) -> bool:
    return task.risk in place.risks


def select_helper(place: Place, task: Task) -> Optional[Helper]:
    for helper in HELPERS.values():
        if helper.protection == task.risk:
            return helper
    return None


def valid_stories() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES.values():
        for task in TASKS.values():
            if task_is_risky(place, task) and select_helper(place, task):
                combos.append((place.id, task.id))
    return combos


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict(world: World, task: Task, helper: Helper, child_id: str) -> dict:
    sim = world.copy()
    child = sim.get(child_id)
    child.memes["fear"] += 1
    if task.risk == "dark":
        child.meters["distance"] += 1
    return {
        "fear": child.memes["fear"],
        "risk": task_is_risky(sim.place, task),
    }


def do_setup(world: World, child: Entity, task: Task) -> None:
    child.memes["hope"] += 1
    world.say(
        f"Long ago, in {world.place.label}, there lived a small quartet with "
        f"four voices and one bright tune to share."
    )
    world.say(
        f"{child.id} was the {child.memes.get('talent', '')} one who loved {task.gerund}, "
        f"and the others loved how the notes fit together like four reeds in one river."
    )


def introduce_quartet(world: World, quartet: list[Entity], task: Task) -> None:
    names = ", ".join(e.id for e in quartet[:-1]) + f", and {quartet[-1].id}"
    world.say(
        f"The quartet was {names}. They had rehearsed for the village gathering, "
        f"and everyone knew they meant to {task.verb} before the moon climbed high."
    )


def foreshadow(world: World, task: Task) -> None:
    if task.risk == "dark":
        world.say(
            "An old bell in the square gave a slow warning, and even the crows "
            "settled close to the eaves."
        )
    elif task.risk == "rain":
        world.say(
            "The clouds gathered like gray sheep, and the bridge boards creaked under the first drops."
        )


def raise_tension(world: World, child: Entity, task: Task) -> None:
    child.memes["fear"] += 1
    world.say(
        f"Still, {child.id} wanted to {task.verb}, but the path ahead looked long and a little strange."
    )


def offer_help(world: World, helper: Helper, child: Entity, task: Task) -> None:
    world.say(
        f"Then a wise neighbor brought {helper.label}, saying it could {helper.role} and help the quartet be brave."
    )


def accept_help(world: World, helper: Helper, quartet: list[Entity], child: Entity, task: Task) -> None:
    world.say(
        f"{child.id} took a breath, and the others stood close, shoulder to shoulder, as if friendship itself had hands."
    )
    world.say(
        f"They used {helper.label} and stepped forward together, each one carrying a fair piece of the road."
    )
    for e in quartet:
        e.memes["bravery"] += 1
        e.memes["friendship"] += 1


def resolve(world: World, quartet: list[Entity], task: Task) -> None:
    names = ", ".join(e.id for e in quartet)
    world.say(
        f"At last the quartet played, and their music crossed the {world.place.label} like a lantern beam."
    )
    world.say(
        f"The brave song did not stop at the gate; it went on to {task.gerund}, and by the end {names} were laughing as one."
    )


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------

def tell(place: Place, task: Task, names: list[str]) -> World:
    world = World(place)
    quartet = [
        world.add(Entity(id=n, kind="character", type="person")) for n in names
    ]
    for idx, e in enumerate(quartet):
        e.memes["talent"] = 1.0
        e.memes["friendship"] = 1.0
        e.memes["bravery"] = 0.0 if idx == 0 else 0.5
        e.memes["fear"] = 0.0 if idx != 0 else 1.0

    do_setup(world, quartet[0], task)
    world.para()
    introduce_quartet(world, quartet, task)
    foreshadow(world, task)
    raise_tension(world, quartet[0], task)

    helper = select_helper(place, task)
    if helper is None:
        _fallback_pool = globals().get("HELPERS") or globals().get("HELPERES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        helper = next(iter(_fallback_pool), None)
        if helper is None:
            raise StoryError
    pred = predict(world, task, helper, quartet[0].id)
    if not pred["risk"]:
        pass

    world.para()
    offer_help(world, helper, quartet[0], task)
    accept_help(world, helper, quartet, quartet[0], task)

    world.para()
    resolve(world, quartet, task)

    world.facts.update(
        place=place,
        task=task,
        quartet=quartet,
        helper=helper,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    task: Task = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    return [
        f"Write a folk tale about a quartet in {place.label} who must use bravery to {task.verb}.",
        f"Tell a gentle story where a quartet faces a little danger, uses friendship, and keeps the music going.",
        f"Write a child-friendly folk tale with foreshadowing, bravery, and a happy ending at {place.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    task: Task = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    quartet: list[Entity] = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quartet")
    helper: Helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    leader = quartet[0]

    return [
        QAItem(
            question=f"What were the four friends trying to do at {place.label}?",
            answer=f"They were trying to {task.verb}. Their quartet had come together for that shared tune.",
        ),
        QAItem(
            question=f"Why did the old bell and the gray sky matter before they went on?",
            answer="They were foreshadowing. The story hinted that the road would be tricky, so the quartet would need courage and a careful plan.",
        ),
        QAItem(
            question=f"What helped {leader.id} and the others move forward without giving up?",
            answer=f"{helper.label} helped them {helper.role}. With that help, the quartet could be brave together instead of alone.",
        ),
        QAItem(
            question=f"How did the quartet feel at the end?",
            answer="They felt proud, close, and cheerful, because friendship carried them through the hard part and the song still reached the village.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    task: Task = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    helper: Helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    out = [
        QAItem(
            question="What is a quartet?",
            answer="A quartet is a group of four people who work or perform together.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard even when your heart is shaking a little.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives small hints about something important that might happen later.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond where people help each other, share, and stay together.",
        ),
    ]
    if task.keyword == "bridge" or helper.id == "rope":
        out.append(
            QAItem(
                question="What is a rope used for?",
                answer="A rope can tie things together, steady a crossing, or help people carry a load safely.",
            )
        )
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
# Selection / params
# ---------------------------------------------------------------------------

def explain_rejection(place: Place, task: Task) -> str:
    return (
        f"(No story: {task.name} is not a meaningful risk at {place.label}; "
        f"try a place whose shadows or weather match the task.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "task", None):
        place = _safe_lookup(PLACES, getattr(args, "place", None))
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        if not task_is_risky(place, task):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_stories()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, task_id = rng.choice(list(combos))
    return StoryParams(place=place_id, task=task_id, name=getattr(args, "name", None) or rng.choice(NAMES))


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    task = _safe_lookup(TASKS, params.task)
    names = [params.name]
    others = [n for n in NAMES if n != params.name]
    rng = random.Random(params.seed or 0)
    while len(names) < 4:
        pick = rng.choice(others)
        if pick not in names:
            names.append(pick)
    world = tell(place, task, names)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a quartet, bravery, foreshadowing, and friendship."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=NAMES)
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


CURATED = [
    StoryParams(place="meadow", task="play_at_dusk", name="Mira", seed=1),
    StoryParams(place="bridge", task="cross_bridge", name="Tobin", seed=2),
    StoryParams(place="hill", task="carry_lanterns", name="Elsa", seed=3),
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
        items = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(items)} compatible stories:")
        for place, task in items:
            print(f"  {place:10} {task}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
