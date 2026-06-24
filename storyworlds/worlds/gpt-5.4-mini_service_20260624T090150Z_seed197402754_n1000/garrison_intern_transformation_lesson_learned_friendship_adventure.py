#!/usr/bin/env python3
"""
A tiny adventure storyworld about a garrison, an intern, a transformation,
a lesson learned, and friendship.

The world starts with a short, child-facing premise:
an intern arrives at a garrison, wants to help on an adventurous task, makes a
mistake, learns from it, and changes in a way that strengthens friendship.

The simulation keeps state in meters and memes:
- meters track physical things like tools, maps, gates, and routes
- memes track feelings like confidence, worry, trust, and friendship

The story is generated from a small world model, not from a frozen template:
state changes drive the narration, the lesson, and the ending image.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    intern: object | None = None
    mentor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"intern", "kid", "boy"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"captain", "guard", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"lieutenant", "woman"}:
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
class Setting:
    place: str
    outdoors: bool
    affords: set[str] = field(default_factory=set)
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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


@dataclass
class Lesson:
    id: str
    phrase: str
    fix: str
    change: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    helps: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.route: str = ""
        self.trace: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.route = self.route
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "gates": Setting(place="the stone garrison gates", outdoors=True, affords={"patrol", "map"}),
    "tower": Setting(place="the watch tower", outdoors=False, affords={"map"}),
    "yard": Setting(place="the training yard", outdoors=True, affords={"patrol", "supply"}),
    "path": Setting(place="the forest path", outdoors=True, affords={"patrol"}),
}

TASKS = {
    "patrol": Task(
        id="patrol",
        verb="lead a patrol",
        gerund="leading a patrol",
        rush="dash down the path",
        risk="lose the trail",
        zone={"feet", "hands"},
        keyword="patrol",
        tags={"adventure", "path"},
    ),
    "map": Task(
        id="map",
        verb="study the map",
        gerund="studying the map",
        rush="lean over the map",
        risk="smudge the map",
        zone={"hands"},
        keyword="map",
        tags={"map", "adventure"},
    ),
    "supply": Task(
        id="supply",
        verb="carry supplies",
        gerund="carrying supplies",
        rush="rush with the supplies",
        risk="spill the supplies",
        zone={"hands"},
        keyword="supplies",
        tags={"care", "friendship"},
    ),
}

LESSONS = {
    "ask": Lesson(
        id="ask",
        phrase="ask for help before charging ahead",
        fix="pause and listen",
        change="became calmer and wiser",
    ),
    "share": Lesson(
        id="share",
        phrase="share the load so nobody stumbles alone",
        fix="split the work",
        change="became steadier and kinder",
    ),
    "guide": Lesson(
        id="guide",
        phrase="follow a gentle guide when the road is new",
        fix="take the safer route",
        change="learned how to move with care",
    ),
}

GEAR = {
    "gloves": Gear(
        id="gloves",
        label="leather gloves",
        covers={"hands"},
        helps={"map", "supply"},
        prep="put on leather gloves",
        tail="pulled on the leather gloves",
    ),
    "boots": Gear(
        id="boots",
        label="sturdy boots",
        covers={"feet"},
        helps={"patrol"},
        prep="lace up sturdy boots",
        tail="laced up the sturdy boots",
    ),
    "satchel": Gear(
        id="satchel",
        label="a satchel with a wide strap",
        covers={"hands"},
        helps={"map"},
        prep="carry the map in a satchel",
        tail="slung on the satchel",
    ),
}

NAMES = ["Mina", "Tao", "Rin", "Pip", "Lina", "Arlo", "Noa", "Ezra"]
ROLES = ["intern", "guard", "captain"]
TRAITS = ["eager", "curious", "brave", "careful", "hopeful"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    task: str
    lesson: str
    name: str
    role: str
    trait: str
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


ASP_RULES = r"""
setting(s). task(t). lesson(l). gear(g).

needs_gear(patrol,boots).
needs_gear(map,gloves).
needs_gear(supply,gloves).

compatible(Task,Gear) :- needs_gear(Task,Gear).
valid(Setting,Task,Lesson) :- setting(Setting), task(Task), lesson(Lesson),
                             affords(Setting,Task), lesson_ok(Task,Lesson).
lesson_ok(patrol,ask).
lesson_ok(patrol,guide).
lesson_ok(map,ask).
lesson_ok(map,guide).
lesson_ok(supply,share).
lesson_ok(supply,ask).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tagged", tid, tag))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
    for gid in GEAR:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def compatible(task: Task, gear: Gear) -> bool:
    return gear.id in GEAR and task.id in gear.helps


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for task_id in setting.affords:
            task = _safe_lookup(TASKS, task_id)
            for lesson_id, lesson in LESSONS.items():
                if task_id in {"patrol", "map"} and lesson_id in {"ask", "guide"}:
                    combos.append((setting_id, task_id, lesson_id))
                elif task_id == "supply" and lesson_id in {"share", "ask"}:
                    combos.append((setting_id, task_id, lesson_id))
    return combos


def explain_rejection(setting: Setting, task: Task, lesson: Lesson) -> str:
    return (
        f"(No story: {task.gerund} at {setting.place} does not fit the lesson "
        f'"{lesson.phrase}". The adventure needs a lesson that changes how the intern acts.)'
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def predict_problem(world: World, intern: Entity, task: Task) -> dict[str, bool]:
    sim = world.copy()
    sim.get(intern.id).memes["eager"] += 1
    sim.get(intern.id).meters["strain"] += 1
    if task.id == "patrol":
        sim.get(intern.id).memes["worry"] += 1
        sim.get(intern.id).meters["mud"] += 1
    elif task.id == "map":
        sim.get(intern.id).meters["smudge"] += 1
    elif task.id == "supply":
        sim.get(intern.id).meters["spill"] += 1
    return {
        "problem": True,
        "tension": sim.get(intern.id).memes.get("worry", 0) >= THRESHOLD or sim.get(intern.id).meters.get("smudge", 0) >= THRESHOLD,
    }


def fixpoint(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for ent in world.characters():
            if ent.meters.get("mistake", 0) >= THRESHOLD and ("lesson", ent.id) not in world.fired:
                world.fired.add(("lesson", ent.id))
                ent.memes["humble"] += 1
                ent.memes["learned"] += 1
                changed = True


# ---------------------------------------------------------------------------
# Story rendering
# ---------------------------------------------------------------------------

def opening(world: World, intern: Entity, mentor: Entity, task: Task) -> None:
    world.say(
        f"{intern.id} was a {intern.memes['trait_word']} intern at {world.setting.place}. "
        f"{intern.pronoun().capitalize()} wanted to help with {task.gerund}, and {mentor.id} trusted {intern.pronoun('object')} to try."
    )


def setup_item(world: World, intern: Entity, task: Task) -> None:
    if task.id == "patrol":
        intern.meters["boots"] += 1
        world.say(
            f"Before dawn, the gate opened, and the long road waited outside like a mystery."
        )
    elif task.id == "map":
        world.say(
            f"On a table near the lamp, an old map showed hills, pines, and a bend in the road."
        )
    else:
        world.say(
            f"Boxes of rope and bread waited by the wall, ready for the road ahead."
        )


def mistake(world: World, intern: Entity, mentor: Entity, task: Task) -> None:
    intern.memes["eager"] += 1
    if task.id == "patrol":
        intern.meters["mud"] += 1
        intern.memes["worry"] += 1
        world.say(
            f"{intern.id} hurried forward and nearly {task.rush}, but {intern.pronoun()} slipped in a muddy patch."
        )
    elif task.id == "map":
        intern.meters["smudge"] += 1
        intern.memes["worry"] += 1
        world.say(
            f"{intern.id} leaned too close and almost {task.risk}, leaving a gray thumbprint near the river bend."
        )
    else:
        intern.meters["spill"] += 1
        intern.memes["worry"] += 1
        world.say(
            f"{intern.id} rushed to help and almost {task.risk}, making the rope wobble in {intern.pronoun('possessive')} arms."
        )


def lesson_turn(world: World, intern: Entity, mentor: Entity, lesson: Lesson) -> None:
    intern.meters["mistake"] += 1
    fixpoint(world)
    world.say(
        f"{mentor.id} pointed to the mess and said, 'A good adventurer knows when to {lesson.fix}.' "
        f"{intern.id} listened closely and chose to {lesson.fix}."
    )
    intern.memes["trust"] += 1
    mentor.memes["trust"] += 1
    intern.memes["lesson"] += 1


def friendship_turn(world: World, intern: Entity, mentor: Entity, gear: Optional[Gear], task: Task, lesson: Lesson) -> None:
    if gear:
        world.say(
            f"They {gear.tail} together, and the work suddenly felt easier."
        )
    world.say(
        f"That small change made {intern.id} {lesson.change}. {mentor.id} smiled, and their friendship grew stronger."
    )
    intern.memes["friendship"] += 1
    mentor.memes["friendship"] += 1


def ending(world: World, intern: Entity, task: Task, gear: Optional[Gear], mentor: Entity) -> None:
    if task.id == "patrol":
        world.say(
            f"By sunset, {intern.id} was {task.gerund} with steady steps, sturdy boots, and a calm heart beside {mentor.id}."
        )
    elif task.id == "map":
        world.say(
            f"In the lamp glow, {intern.id} was carefully {task.gerund}, and the map stayed clean under a patient hand."
        )
    else:
        world.say(
            f"Before long, {intern.id} was {task.gerund} with careful hands, and the supplies stayed safe for everyone."
        )


def tell(setting: Setting, task: Task, lesson: Lesson, name: str, role: str, trait: str) -> World:
    world = World(setting)
    intern = world.add(Entity(
        id=name, kind="character", type=role, label=role, memes={"trait_word": trait}
    ))
    mentor = world.add(Entity(
        id="CaptainRowan", kind="character", type="captain", label="Captain Rowan"
    ))
    world.facts.update(intern=intern, mentor=mentor, task=task, lesson=lesson)

    opening(world, intern, mentor, task)
    world.para()
    setup_item(world, intern, task)
    mistake(world, intern, mentor, task)
    world.para()
    lesson_turn(world, intern, mentor, lesson)
    gear = None
    if task.id == "patrol":
        gear = world.add(Entity(id="boots", kind="thing", type="boots", label="sturdy boots"))
        gear.worn_by = intern.id
    elif task.id == "map":
        gear = world.add(Entity(id="gloves", kind="thing", type="gloves", label="leather gloves"))
        gear.worn_by = intern.id
    friendship_turn(world, intern, mentor, gear, task, lesson)
    world.para()
    ending(world, intern, task, gear, mentor)
    world.facts["gear"] = gear
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    intern = _safe_fact(world, f, "intern")
    task = _safe_fact(world, f, "task")
    lesson = _safe_fact(world, f, "lesson")
    return [
        f'Write a short adventure story about an intern named {intern.id} at a garrison who tries to {task.verb}.',
        f'Write a story where {intern.id} makes a small mistake, learns a lesson, and becomes friends with a captain.',
        f'Create a child-friendly adventure with the words "garrison", "intern", and "{lesson.phrase}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    intern = _safe_fact(world, f, "intern")
    mentor = _safe_fact(world, f, "mentor")
    task = _safe_fact(world, f, "task")
    lesson = _safe_fact(world, f, "lesson")
    gear = f.get("gear")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {intern.id}, an {intern.type} who worked at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {intern.id} want to do at the garrison?",
            answer=f"{intern.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"What lesson did {mentor.id} teach {intern.id}?",
            answer=f"{mentor.id} taught {intern.id} to {lesson.phrase}.",
        ),
        QAItem(
            question=f"How did the adventure end for {intern.id} and {mentor.id}?",
            answer=f"They finished the day as friends, and {intern.id} became {lesson.change}.",
        ),
    ] + (
        [
            QAItem(
                question=f"What helped {intern.id} do the task more safely?",
                answer=f"{gear.label.capitalize()} helped {intern.id} work more safely.",
            )
        ] if gear else []
    )


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a garrison?",
            answer="A garrison is a place where guards or soldiers stay so they can protect a town, gate, or road.",
        ),
        QAItem(
            question="What is an intern?",
            answer="An intern is a person who is learning by helping out and practicing a job.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind relationship where people care about each other and help each other.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important from an experience so you can do better next time.",
        ),
        QAItem(
            question="What is transformation?",
            answer="A transformation is when something changes into a different form or becomes a different kind of person through growth.",
        ),
    ]


# ---------------------------------------------------------------------------
# Params / generation / emit
# ---------------------------------------------------------------------------

def valid_story_choices() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: garrison, intern, transformation, lesson learned, friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=["intern"])
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
    settings = [getattr(args, "setting", None)] if getattr(args, "setting", None) else list(SETTINGS)
    tasks = [getattr(args, "task", None)] if getattr(args, "task", None) else list(TASKS)
    lessons = [getattr(args, "lesson", None)] if getattr(args, "lesson", None) else list(LESSONS)
    combos = []
    for s in settings:
        for t in tasks:
            if t not in _safe_lookup(SETTINGS, s).affords:
                continue
            for l in lessons:
                if (s, t, l) in valid_combos():
                    combos.append((s, t, l))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id, task_id, lesson_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or "intern"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, task=task_id, lesson=lesson_id, name=name, role=role, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TASKS, params.task), _safe_lookup(LESSONS, params.lesson), params.name, params.role, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(parts)}")
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_list() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="gates", task="patrol", lesson="guide", name="Mina", role="intern", trait="brave"),
    StoryParams(setting="tower", task="map", lesson="ask", name="Tao", role="intern", trait="curious"),
    StoryParams(setting="yard", task="supply", lesson="share", name="Rin", role="intern", trait="hopeful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_list()
        print(f"{len(triples)} compatible (setting, task, lesson) combos:\n")
        for s, t, l in triples:
            print(f"  {s:8} {t:8} {l:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
