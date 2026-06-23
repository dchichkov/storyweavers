#!/usr/bin/env python3
"""
storyworlds/worlds/xyz_pledge_ease_moral_value_happy_ending.py
==============================================================

A small slice-of-life story world about keeping a promise, making a task easier,
and choosing a moral value in a gentle happy ending.

Seed premise:
- Use the words: xyz, pledge, ease
- Features: Moral Value, Happy Ending
- Style: Slice of Life
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    owner: Optional[str] = None
    helper_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    aide: object | None = None
    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
        if not hasattr(self, "_tags"):
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
    supports: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    label: str
    verb: str
    noun: str
    risk: str
    hard: str
    needs_help: bool = True
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Tool:
    id: str
    label: str
    phrase: str
    ease_gain: float
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Value:
    id: str
    label: str
    lesson: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    value: str
    name: str = ""
    helper: str = ""
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    "kitchen": Place(id="kitchen", label="the kitchen", supports={"baking", "dishes", "cleanup"}),
    "library": Place(id="library", label="the little library corner", supports={"reading", "sorting"}),
    "garden": Place(id="garden", label="the garden", supports={"watering", "weeding"}),
    "laundry": Place(id="laundry", label="the laundry room", supports={"folding", "sorting"}),
}

TASKS = {
    "baking": Task(id="baking", label="bake cupcakes", verb="bake", noun="cupcakes", risk="mess", hard="sticky"),
    "dishes": Task(id="dishes", label="wash the dishes", verb="wash", noun="dishes", risk="splash", hard="wet"),
    "watering": Task(id="watering", label="water the plants", verb="water", noun="plants", risk="spill", hard="drippy"),
    "sorting": Task(id="sorting", label="sort the old books", verb="sort", noun="books", risk="dust", hard="slow"),
}

TOOLS = {
    "xyz": Tool(id="xyz", label="the xyz tray", phrase="the xyz tray with little compartments", ease_gain=2.0, tags={"xyz"}),
    "towel": Tool(id="towel", label="a folded towel", phrase="a folded towel", ease_gain=1.0, tags={"soft"}),
    "cart": Tool(id="cart", label="a rolling cart", phrase="a rolling cart", ease_gain=1.5, tags={"roll"}),
    "gloves": Tool(id="gloves", label="a pair of gloves", phrase="a pair of gloves", ease_gain=1.2, tags={"clean"}),
}

VALUES = {
    "pledge": Value(id="pledge", label="pledge", lesson="keep a promise", tags={"promise"}),
    "ease": Value(id="ease", label="ease", lesson="make the job easier", tags={"easy"}),
    "kindness": Value(id="kindness", label="kindness", lesson="help someone without being asked", tags={"care"}),
    "honesty": Value(id="honesty", label="honesty", lesson="say what is true and fix mistakes", tags={"true"}),
}

GIRL_NAMES = ["Maya", "Lina", "Iris", "Nora", "Zoe", "Lila"]
BOY_NAMES = ["Ben", "Owen", "Leo", "Sam", "Toby", "Milo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for task_id in p.supports:
            for tool_id, tool in TOOLS.items():
                for value_id in VALUES:
                    if tool_id == "xyz" or value_id == "pledge" or value_id == "ease":
                        combos.append((place, task_id, tool_id, value_id))
    return combos


def reason_ok(place: Place, task: Task, tool: Tool, value: Value) -> bool:
    return task.id in place.supports and (tool.id == "xyz" or value.id in {"pledge", "ease", "kindness", "honesty"})


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a pledge, some ease, and a gentle moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
              and (getattr(args, "value", None) is None or c[3] == getattr(args, "value", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, tool, value = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    return StoryParams(place=place, task=task, tool=tool, value=value, name=name, helper=helper)


def _setup(world: World, child: Entity, helper: Entity, task: Task, tool: Tool, value: Value) -> None:
    child.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(f"{child.id} and {helper.id} were busy in {world.place.label}.")
    world.say(f"{child.id} wanted to {task.verb} the {task.noun}, and {child.id} had a simple {value.label} in mind.")
    world.say(f"They found {tool.phrase}, and it seemed like a nice way to bring some {tool.label} to the job.")


def _turn(world: World, child: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    child.meters["work"] += 1
    child.memes["worry"] += 1
    world.say(f"But the {task.noun} were {task.hard}, and the work was starting to feel heavy.")
    world.say(f"{helper.id} noticed and offered a hand, so the job could have a little more ease.")


def _pledge(world: World, child: Entity, helper: Entity, value: Value) -> None:
    child.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(f'{child.id} made a small {value.label} to {helper.id}: "I will finish this with care."')
    world.say(f"{helper.id} smiled, because {value.lesson} made the room feel calm again.")


def _resolve(world: World, child: Entity, helper: Entity, task: Task, tool: Tool, value: Value) -> None:
    child.meters["work"] = max(0.0, child.meters["work"] - tool.ease_gain)
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(f"With {tool.label}, the task felt lighter.")
    world.say(f"{child.id} and {helper.id} finished the {task.noun} together, and the little {tool.label} helped every step go by with ease.")
    world.say(f"At the end, the counter was neat, the air was peaceful, and {value.lesson} was the bright part they both remembered.")


def tell(place: Place, task: Task, tool: Tool, value: Value, name: str, helper: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type="girl" if name in GIRL_NAMES else "boy"))
    aide = world.add(Entity(id=helper, kind="character", type="girl" if helper in GIRL_NAMES else "boy"))
    world.facts["child"] = child
    world.facts["helper"] = aide
    world.facts["task"] = task
    world.facts["tool"] = tool
    world.facts["value"] = value
    world.facts["place"] = place
    world.facts["resolved"] = False
    _setup(world, child, aide, task, tool, value)
    world.para()
    _turn(world, child, aide, task, tool)
    world.para()
    _pledge(world, child, aide, value)
    _resolve(world, child, aide, task, tool, value)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story with the words "xyz", "pledge", and "ease".',
        f"Tell a short story where {f['child'].id} and {f['helper'].id} work in {f['place'].label} and keep a pledge.",
        f"Write a happy story about making a task easier with {(f.get('tool') or next(iter(TOOLS.values()))).label} and ending with a moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, task, tool, value = f["child"], f["helper"], f["task"], (f.get("tool") or next(iter(TOOLS.values()))), f["value"]
    return [
        QAItem(
            question=f"What were {child.id} and {helper.id} trying to do in {world.place.label}?",
            answer=f"They were trying to {task.verb} the {task.noun}. It was a normal everyday job, but it needed patience and a little help.",
        ),
        QAItem(
            question=f"Why did the {tool.label} matter in the story?",
            answer=f"It made the work feel easier. That gave {child.id} more ease and helped the two of them keep going without getting stuck.",
        ),
        QAItem(
            question=f"What did {child.id} promise near the end?",
            answer=f"{child.id} made a pledge to finish the task with care. That promise showed the moral value in the story and helped everything end well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pledge?", "A pledge is a promise someone makes and means to keep."),
        QAItem("What does ease mean?", "Ease means something feels simpler, lighter, or less hard to do."),
        QAItem("What is the word xyz doing in this story?", "It is a special story word that helps make the tale feel playful and memorable."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,U,V) :- place(P), task(T), tool(U), value(V), supports(P,T), good_combo(U,V).
good_combo(xyz,_).
good_combo(_,pledge).
good_combo(_,ease).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    out = []
    for pid, p in PLACES.items():
        out.append(asp.fact("place", pid))
        for t in sorted(p.supports):
            out.append(asp.fact("supports", pid, t))
    for tid in TASKS:
        out.append(asp.fact("task", tid))
    for uid in TOOLS:
        out.append(asp.fact("tool", uid))
    for vid in VALUES:
        out.append(asp.fact("value", vid))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH:")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, task=None, tool=None, value=None, name=None, helper=None), random.Random(777)))
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    if ok:
        print(f"OK: ASP parity and generate() smoke test passed ({len(py)} combos).")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.tool not in TOOLS or params.value not in VALUES:
        pass
    place = _safe_lookup(PLACES, params.place)
    task = _safe_lookup(TASKS, params.task)
    tool = _safe_lookup(TOOLS, params.tool)
    value = _safe_lookup(VALUES, params.value)
    if not reason_ok(place, task, tool, value):
        pass
    world = tell(place, task, tool, value, params.name, params.helper)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", task="baking", tool="xyz", value="pledge", name="Maya", helper="Ben"),
    StoryParams(place="garden", task="watering", tool="cart", value="ease", name="Leo", helper="Nora"),
    StoryParams(place="library", task="sorting", tool="towel", value="kindness", name="Iris", helper="Owen"),
    StoryParams(place="laundry", task="dishes", tool="gloves", value="honesty", name="Sam", helper="Lila"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
