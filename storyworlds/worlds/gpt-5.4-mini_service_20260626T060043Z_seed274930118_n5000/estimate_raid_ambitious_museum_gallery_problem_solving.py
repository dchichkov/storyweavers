#!/usr/bin/env python3
"""
storyworlds/worlds/estimate_raid_ambitious_museum_gallery_problem_solving.py
=============================================================================

A heartwarming story world about an ambitious museum helper who uses careful
estimates and kind problem solving to fix a gallery problem before opening.

Seed tale premise:
---
An ambitious child loves the museum gallery and wants to help the grown-ups.
One day, the child estimates how long a job will take, but a small raid of
mischief upsets the gallery setup. The child and a guide solve the problem
together, and the gallery opens in a warmer, calmer way.

World model:
---
Characters and objects both carry physical meters and emotional memes.
The story is driven by state changes: a thing gets misplaced, a person
estimates a repair, a helper fetches the right tool, tension softens, and the
gallery becomes ready again.

Narrative instruments:
---
estimate -> a character predicts how much work remains
raid     -> a problem event that knocks things out of place
ambitious-> the hero wants to do more than one small job and help the whole room
problem solving -> the heartwarming turn where the right tool and a kind plan fix things
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    tool_for: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "curator"}
        male = {"boy", "man", "father", "guard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Gallery:
    place: str = "the museum gallery"
    afford_tasks: set[str] = field(default_factory=set)
    GALLERY: object | None = None
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
    problem: str
    fix: str
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


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
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


@dataclass
class World:
    gallery: Gallery
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    c: object | None = None
    world: object | None = None
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
        c = World(self.gallery)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c
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
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_misplace(world: World) -> list[str]:
    out: list[str] = []
    for helper in world.characters():
        if helper.meters.get("busy", 0.0) < THRESHOLD:
            continue
        for obj in list(world.entities.values()):
            if obj.kind != "thing" or obj.meters.get("placed", 0.0) >= THRESHOLD:
                continue
            sig = ("misplace", obj.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            obj.meters["scattered"] = 1.0
            out.append(f"One label slipped out of line and landed on the floor.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.memes.get("care", 0) >= THRESHOLD), None)
    if not hero:
        return out
    for obj in list(world.entities.values()):
        if obj.kind != "thing" or obj.meters.get("scattered", 0.0) < THRESHOLD:
            continue
        tool_id = world.facts.get("tool_in_use")
        if not tool_id:
            continue
        sig = ("fix", obj.id, tool_id)
        if sig in world.fired:
            continue
        tool = world.get(tool_id)
        if obj.tool_for and obj.tool_for != tool.id:
            continue
        if obj.id not in tool.helps:
            continue
        world.fired.add(sig)
        obj.meters["placed"] = 1.0
        obj.meters["scattered"] = 0.0
        hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
        out.append(f"{hero.label} gently put things back where they belonged.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for char in world.characters():
        if char.memes.get("worry", 0) < THRESHOLD:
            continue
        if char.meters.get("fixed", 0) >= THRESHOLD:
            continue
        if any(obj.meters.get("placed", 0.0) < THRESHOLD for obj in world.entities.values() if obj.kind == "thing"):
            continue
        sig = ("calm", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["worry"] = 0.0
        char.memes["joy"] = char.memes.get("joy", 0.0) + 1
        out.append(f"The worry in the room softened at last.")
    return out


CAUSAL_RULES = [
    Rule("misplace", _r_misplace),
    Rule("fix", _r_fix),
    Rule("calm", _r_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(task: Task, item: str) -> bool:
    return item in _safe_lookup(TASK_RISKS, task.id)


def select_tool(task: Task, item: str) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.helps and item in tool.covers:
            return tool
    return None


def estimate_work(world: World, hero: Entity, task: Task, item: str) -> int:
    sim = world.copy()
    sim.get(hero.id).meters["busy"] = 1.0
    sim.get(hero.id).memes["care"] = 1.0
    sim.facts["tool_in_use"] = select_tool(task, item).id if select_tool(task, item) else ""
    propagate(sim, narrate=False)
    return sum(1 for e in sim.entities.values() if e.kind == "thing" and e.meters.get("scattered", 0.0) >= THRESHOLD)


def hero_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.label} was an ambitious little museum helper who noticed everything in the gallery."
    )


def love_gallery(world: World, hero: Entity, place: str) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved the museum gallery because every frame and every sign told a quiet story."
    )


def arrive(world: World, hero: Entity, guide: Entity) -> None:
    world.say(
        f"One morning, {hero.label} went to {world.gallery.place} with {guide.label} to help before opening."
    )


def estimate(world: World, hero: Entity, task: Task, item: str) -> None:
    count = estimate_work(world, hero, task, item)
    world.facts["estimate"] = count
    world.say(
        f"{hero.label} took a careful look and estimated that only {count} small fix would be needed."
    )


def raid(world: World, task: Task, item: str) -> None:
    world.say(
        f"Then a tiny raid of bumping feet and wobbling carts nudged the display out of place."
    )
    for obj in list(world.entities.values()):
        if obj.kind == "thing" and obj.tool_for == item:
            obj.meters["scattered"] = 1.0
    for ch in world.characters():
        ch.memes["worry"] = ch.memes.get("worry", 0.0) + 1


def ask_help(world: World, hero: Entity, guide: Entity, task: Task) -> None:
    hero.memes["care"] = 1.0
    guide.memes["care"] = 1.0
    hero.meters["busy"] = 1.0
    world.say(
        f"{hero.label} did not pout; {hero.pronoun()} asked {guide.label} for help and promised to solve the problem kindly."
    )


def choose_tool(world: World, hero: Entity, guide: Entity, task: Task, item: str) -> Optional[Tool]:
    tool = select_tool(task, item)
    if tool is None:
        return None
    world.facts["tool_in_use"] = tool.id
    world.say(
        f"{guide.label} handed over {tool.label}, the right tool for the job."
    )
    return tool


def solve(world: World, hero: Entity, guide: Entity, task: Task, item: str, tool: Tool) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{hero.label} used {tool.label} with careful hands, and together they {task.verb} the problem without hurting anything."
    )
    world.say(
        f"{guide.label} smiled because the gallery was ready again, and {hero.pronoun('possessive')} ambitious heart had helped everyone."
    )


TASK_RISKS = {
    "relabel": {"label"},
    "dust": {"frame"},
    "straighten": {"sign"},
    "count": {"catalog"},
}

TASKS = {
    "relabel": Task(
        id="relabel",
        verb="relabel",
        gerund="relabeling",
        rush="dash to the label stand",
        problem="labels off the floor",
        fix="put the labels back",
        risk="label",
        keyword="estimate",
        tags={"estimate"},
    ),
    "dust": Task(
        id="dust",
        verb="dust",
        gerund="dusting",
        rush="reach for the cloth",
        problem="dust on a frame",
        fix="wipe the frame clean",
        risk="frame",
        keyword="ambitious",
        tags={"ambitious"},
    ),
    "straighten": Task(
        id="straighten",
        verb="straighten",
        gerund="straightening",
        rush="hurry to the sign",
        problem="a tilted sign",
        fix="set the sign right",
        risk="sign",
        keyword="raid",
        tags={"raid"},
    ),
    "count": Task(
        id="count",
        verb="count",
        gerund="counting",
        rush="open the catalog",
        problem="missing numbers in the log",
        fix="finish the count",
        risk="catalog",
        keyword="problem solving",
        tags={"problem_solving"},
    ),
}

TOOLS = [
    Tool(id="tape", label="fresh display tape", helps={"relabel"}, covers={"label"}, prep="use fresh display tape", tail="kept the labels steady"),
    Tool(id="cloth", label="a soft dust cloth", helps={"dust"}, covers={"frame"}, prep="use a soft dust cloth", tail="wiped away the dust kindly"),
    Tool(id="level", label="a tiny level", helps={"straighten"}, covers={"sign"}, prep="check with a tiny level", tail="made the sign stand straight"),
    Tool(id="pencil", label="a neat pencil and checklist", helps={"count"}, covers={"catalog"}, prep="count with a neat pencil and checklist", tail="made the numbers line up"),
]

GALLERY = Gallery(place="the museum gallery", afford_tasks=set(TASKS))


@dataclass
class StoryParams:
    task: str
    item: str
    name: str
    guide: str
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


GIRL_NAMES = ["Maya", "Nina", "Lena", "Ivy", "Ruby", "Sofia"]
BOY_NAMES = ["Noah", "Eli", "Owen", "Theo", "Finn", "Leo"]


class _P:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming museum gallery problem-solving stories.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=["label", "frame", "sign", "catalog"])
    ap.add_argument("--name")
    ap.add_argument("--guide")
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for task in TASKS.values():
        for item in _safe_lookup(TASK_RISKS, task.id):
            if select_tool(task, item):
                out.append((task.id, item))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "task", None) and getattr(args, "item", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        if not prize_at_risk(task, getattr(args, "item", None)) or select_tool(task, getattr(args, "item", None)) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "task", None) is None or c[0] == getattr(args, "task", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    task, item = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["Mr. Lane", "Ms. Sol", "Curator June"])
    return StoryParams(task=task, item=item, name=name, guide=guide)


def build_world(params: StoryParams) -> World:
    world = World(GALLERY)
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy", label=params.name))
    guide_type = "curator" if params.guide == "Curator June" else "man" if params.guide == "Mr. Lane" else "woman"
    guide = world.add(Entity(id="guide", kind="character", type=guide_type, label=params.guide))
    task = _safe_lookup(TASKS, params.task)
    world.add(Entity(id="item", type=params.item, label=params.item, meters={"placed": 1.0}, tool_for=params.item))
    world.facts.update(hero=hero, guide=guide, task=task, item=params.item)
    hero.memes["ambition"] = 1.0
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    hero = world.get(params.name)
    guide = world.get("guide")
    task = _safe_lookup(TASKS, params.task)

    hero_intro(world, hero)
    love_gallery(world, hero, world.gallery.place)
    world.para()
    arrive(world, hero, guide)
    estimate(world, hero, task, params.item)
    raid(world, task, params.item)
    ask_help(world, hero, guide, task)
    tool = choose_tool(world, hero, guide, task, params.item)
    if tool is None:
        pass
    world.para()
    solve(world, hero, guide, task, params.item, tool)
    hero.meters["fixed"] = 1.0
    world.facts.update(tool_in_use=tool.id, resolved=True)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = _safe_fact(world, f, "task")
    return [
        f'Write a heartwarming story in a museum gallery that includes the word "{task.keyword}".',
        f"Tell a short story about an ambitious child who uses problem solving to fix a gallery problem.",
        f"Write a gentle museum story where someone makes an estimate, notices a raid of trouble, and finds the right tool.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    task = _safe_fact(world, f, "task")
    item = _safe_fact(world, f, "item")
    tool = _safe_fact(world, f, "tool_in_use")
    return [
        QAItem(
            question=f"What did {hero.label} estimate before the museum problem got bigger?",
            answer=f"{hero.label} estimated that only a small amount of work would be needed before opening.",
        ),
        QAItem(
            question=f"What did the little raid in the gallery do to the {item}?",
            answer=f"The little raid nudged the {item} out of place and made the room need careful problem solving.",
        ),
        QAItem(
            question=f"How did {guide.label} help {hero.label} solve the problem?",
            answer=f"{guide.label} gave {tool.label}, which was the right tool to {task.verb} the {item} back into order.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt proud and kind because the gallery was ready again and everyone could smile.",
        ),
    ]


KNOWLEDGE = {
    "estimate": [("What does it mean to estimate?",
                 "To estimate means to make a careful guess about how much, how long, or how many there are.")],
    "raid": [("What is a raid?",
               "A raid is a fast, sudden rush into a place, often causing trouble or a mess.")],
    "ambitious": [("What does ambitious mean?",
                   "Ambitious means wanting to do a lot and trying hard to do something important.")],
    "problem_solving": [("What is problem solving?",
                         "Problem solving means thinking carefully and trying different ideas until a problem is fixed.")],
    "museum": [("What is a museum?",
                "A museum is a place where people keep and show special things so others can learn about them.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    out: list[QAItem] = []
    for k in ["estimate", "raid", "ambitious", "problem_solving"]:
        if k in tags or k == "problem_solving":
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[k])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["museum"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(T, I) :- task(T), risk(T, I).
has_tool(T, I) :- task(T), risk(T, I), tool(U), helps(U, T), covers(U, I).
valid(T, I) :- prize_at_risk(T, I), has_tool(T, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
        for item in _safe_lookup(TASK_RISKS, tid):
            lines.append(asp.fact("risk", tid, item))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for t in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, t))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def explain_rejection(task: Task, item: str) -> str:
    return f"(No story: {task.verb} does not have a reasonable museum fix for a {item}.)"


def asp_valid_stories() -> list[tuple]:
    return valid_combos()


CURATED = [
    StoryParams(task="relabel", item="label", name="Maya", guide="Curator June"),
    StoryParams(task="dust", item="frame", name="Eli", guide="Ms. Sol"),
    StoryParams(task="straighten", item="sign", name="Nora", guide="Mr. Lane"),
    StoryParams(task="count", item="catalog", name="Theo", guide="Curator June"),
]


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_combos_asp())} valid story combos:")
        for t, i in valid_combos_asp():
            print(f"  {t:11} {i}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.task} / {p.item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "task", None) and getattr(args, "item", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        if not prize_at_risk(task, getattr(args, "item", None)) or select_tool(task, getattr(args, "item", None)) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "task", None) is None or c[0] == getattr(args, "task", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    task, item = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["Curator June", "Ms. Sol", "Mr. Lane"])
    return StoryParams(task=task, item=item, name=name, guide=guide)


if __name__ == "__main__":
    main()
