#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/conclusion_teamwork_transformation_tall_tale.py
====================================================================================================

A small tall-tale storyworld about teamwork that brings about a transformation
and ends with a clear conclusion image.

The seed idea:
A child and a helper want to finish a big job in a tiny place, but the job is
too large for one pair of hands. They team up, transform the raw materials into
something useful, and end with a proud final scene that proves the change.

This world is intentionally narrow:
- one task
- one obstacle
- one teamwork solution
- one visible transformation
- one concluding image

It is designed to generate complete, child-facing tall tales with a causal arc.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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


@dataclass
class Place:
    name: str
    adjective: str
    roomy: bool = False
    wind: bool = False
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
class Task:
    id: str
    verb: str
    gerund: str
    fuss: str
    transformation: str
    visible_result: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    required: set[str] = field(default_factory=set)
    transform: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
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
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "yard": Place(name="the dusty yard", adjective="dusty", roomy=True, wind=True,
                  affords={"fence", "bridge"}),
    "prairie": Place(name="the wide prairie", adjective="wide", roomy=True, wind=True,
                     affords={"fence", "bridge"}),
    "hill": Place(name="the windy hill", adjective="windy", roomy=False, wind=True,
                   affords={"fence"}),
    "barn": Place(name="the old barn", adjective="old", roomy=True, wind=False,
                  affords={"fence", "bridge"}),
}

TASKS = {
    "fence": Task(
        id="fence",
        verb="build a fence",
        gerund="building fences",
        fuss="the boards kept wobbling and flopping in the wind",
        transformation="a pile of rough boards became a fence as straight as a parade drum",
        visible_result="the fence stood up tall and neat",
        keyword="fence",
        tags={"wood", "wind", "work"},
    ),
    "bridge": Task(
        id="bridge",
        verb="build a bridge",
        gerund="building bridges",
        fuss="the planks looked too long and heavy for one pair of hands",
        transformation="a heap of planks became a bridge that marched across the gap",
        visible_result="the bridge stretched across like a wooden grin",
        keyword="bridge",
        tags={"wood", "gap", "work"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a long rope",
        helps={"fence", "bridge"},
        required={"wind"},
        transform="held the pieces together",
    ),
    "nails": Tool(
        id="nails",
        label="nails",
        phrase="a tin of bright nails",
        helps={"fence", "bridge"},
        required={"wood"},
        transform="fastened the pieces tight",
    ),
    "braces": Tool(
        id="braces",
        label="braces",
        phrase="two sturdy braces",
        helps={"fence"},
        required={"wind"},
        transform="kept the fence from toppling over",
    ),
    "planks": Tool(
        id="planks",
        label="planks",
        phrase="a stack of planks",
        helps={"bridge"},
        required={"gap"},
        transform="made the crossing long enough to reach the other side",
    ),
}

HERO_NAMES = ["Nora", "Milo", "June", "Otis", "Willa", "Beck", "Ivy", "Hank"]
HELPER_NAMES = ["Aunt Dot", "Uncle Gus", "Mabel", "Sage", "Pip", "Gran"]

TRAITS = ["bold", "quick", "bright-eyed", "steady", "brave", "lively"]


# ---------------------------------------------------------------------------
# Parameters
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


def task_needs_teamwork(task: Task, place: Place) -> bool:
    if task.id == "fence":
        return place.wind or place.roomy
    if task.id == "bridge":
        return True
    return False


def choose_tool(task: Task, place: Place) -> Optional[Tool]:
    for tool in TOOLS.values():
        if task.id in tool.helps:
            if not tool.required or tool.required & place.affords or task.id == "bridge":
                return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for task_id, task in TASKS.items():
            if task_needs_teamwork(task, place) and choose_tool(task, place) is not None:
                combos.append((place_id, task_id))
    return combos


def explain_rejection(place: Place, task: Task) -> str:
    if not task_needs_teamwork(task, place):
        return (
            f"(No story: {task.gerund} would not create a big enough problem in {place.name} "
            f"to need teamwork. Choose a windier or trickier place.)"
        )
    return (
        f"(No story: there is no sensible tool in this tiny world that can help with "
        f"{task.gerund} at {place.name}. The transformation would not be believable.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
task(T) :- task_id(T).
tool(U) :- tool_id(U).

needs_teamwork(T,P) :- task(T), place(P), teamwork_case(T,P).
compatible(T,P,U) :- needs_teamwork(T,P), helps(U,T), tool(U), tool_for_place(U,P).
valid_story(P,T) :- needs_teamwork(T,P), compatible(T,P,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if place.roomy:
            lines.append(asp.fact("roomy", pid))
        if place.wind:
            lines.append(asp.fact("windy", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("teamwork_case", pid, a))
            if a == "bridge":
                lines.append(asp.fact("gap_place", pid))
            if a == "fence":
                lines.append(asp.fact("wood_place", pid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task_id", tid))
        for t in sorted(task.tags):
            lines.append(asp.fact("tag", tid, t))
        if tid == "bridge":
            lines.append(asp.fact("gap_task", tid))
        if tid == "fence":
            lines.append(asp.fact("wood_task", tid))
    for uid, tool in TOOLS.items():
        lines.append(asp.fact("tool_id", uid))
        for t in sorted(tool.helps):
            lines.append(asp.fact("helps", uid, t))
        for req in sorted(tool.required):
            lines.append(asp.fact("tool_for_place", uid, "any") if req == "any" else asp.fact("tool_for_place", uid, req))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
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
# Story engine
# ---------------------------------------------------------------------------
def start_line(hero: Entity, helper: Entity, place: Place) -> str:
    return f"{hero.id} and {helper.id} lived near {place.name}, where even the wind seemed to have elbows."


def setup_line(hero: Entity, task: Task) -> str:
    return f"{hero.id} had a mind to {task.verb}, because {task.gerund} was the kind of work that made the whole day feel tall."


def arrive_line(place: Place, task: Task) -> str:
    return f"On a blustery morning, the pair went out to {place.name}, where {task.fuss}."


def conflict_line(hero: Entity, helper: Entity, task: Task) -> str:
    return f"{hero.id} frowned, but {helper.id} laughed kindly and said, \"One small hand is good, but two small hands are a whole crew.\""


def teamwork_line(tool: Tool, hero: Entity, helper: Entity, task: Task) -> str:
    return f"They fetched {tool.phrase}, and together they {tool.transform} while they worked side by side."


def transform_line(task: Task, hero: Entity, helper: Entity) -> str:
    return f"Little by little, {task.transformation}. {hero.id} and {helper.id} kept at it until the last piece finally listened."


def conclusion_line(task: Task, hero: Entity, helper: Entity) -> str:
    return f"In the end, {task.visible_result}, and {hero.id} stood with {helper.id}, grinning at the finished wonder as if they had tied the wind itself into a neat bow."


def perform(world: World, params: StoryParams) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    task = _safe_lookup(TASKS, params.task)
    tool = choose_tool(task, world.place)
    if tool is None:
        pass

    world.say(start_line(hero, helper, world.place))
    world.say(setup_line(hero, task))
    world.para()
    world.say(arrive_line(world.place, task))
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    helper.memes["calm"] = helper.memes.get("calm", 0) + 1
    world.say(conflict_line(hero, helper, task))
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(teamwork_line(tool, hero, helper, task))
    hero.meters["work"] = hero.meters.get("work", 0) + 1
    helper.meters["work"] = helper.meters.get("work", 0) + 1
    world.say(transform_line(task, hero, helper))
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0) + 1
    world.para()
    world.say(conclusion_line(task, hero, helper))
    world.facts.update(
        hero=hero,
        helper=helper,
        task=task,
        tool=tool,
        place=world.place,
        transformed=True,
    )


def tell(place: Place, params: StoryParams) -> World:
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type="boy" if params.name in {"Milo", "Otis", "Beck", "Hank"} else "girl"))
    helper = world.add(Entity(id=params.helper, kind="character", type="woman" if "Aunt" in params.helper or "Gran" in params.helper or params.helper == "Mabel" else "man"))
    world.facts["params"] = params
    perform(world, params)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, task, place = f["hero"], f["helper"], f["task"], f["place"]
    return [
        f'Write a short tall tale for a young child about "{task.keyword}" that shows {hero.id} and {helper.id} working together.',
        f"Tell a playful story where {hero.id} cannot finish {task.verb} alone at {place.name}, but {helper.id} helps and the job changes shape.",
        f"Write a child-friendly story that begins with a problem, grows into teamwork, and ends with the finished {task.keyword}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, task, place = f["hero"], f["helper"], f["task"], f["place"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do near {place.name}?",
            answer=f"{hero.id} wanted to {task.verb}, and the story showed that it was a job too big for one pair of hands.",
        ),
        QAItem(
            question=f"Who helped {hero.id} finish the work?",
            answer=f"{helper.id} helped {hero.id}, and together they made the whole job possible.",
        ),
        QAItem(
            question=f"What changed because they worked together?",
            answer=f"The rough start turned into a transformation: {task.transformation}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {task.visible_result}, which proved the work was finished and the team had done it together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    task = _safe_fact(world, f, "task")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    out = []
    if "wood" in task.tags:
        out.append(QAItem(
            question="Why do people use tools when they build with wood?",
            answer="People use tools so they can hold, fasten, and shape the pieces safely and neatly.",
        ))
    out.append(QAItem(
        question="What is teamwork?",
        answer="Teamwork is when two or more helpers work together so a hard job becomes easier.",
    ))
    out.append(QAItem(
        question=f"What does {tool.label} do in this kind of work?",
        answer=f"{tool.label.capitalize()} helps by making the pieces stay in place and work together as one finished thing.",
    ))
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
# Params and generation
# ---------------------------------------------------------------------------
def valid_name_options() -> list[str]:
    return HERO_NAMES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "task", None):
        place = _safe_lookup(PLACES, getattr(args, "place", None))
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        if (getattr(args, "place", None), getattr(args, "task", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, task_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place_id, task=task_id, name=name, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params)
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tall-tale story world about teamwork and transformation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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


CURATED = [
    StoryParams(place="yard", task="fence", name="Nora", helper="Aunt Dot", trait="bold"),
    StoryParams(place="prairie", task="bridge", name="Milo", helper="Uncle Gus", trait="steady"),
    StoryParams(place="barn", task="fence", name="Ivy", helper="Gran", trait="bright-eyed"),
    StoryParams(place="hill", task="fence", name="Willa", helper="Sage", trait="lively"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible (place, task) combos:")
        for place, task in combos:
            print(f"  {place:8} {task}")
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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
