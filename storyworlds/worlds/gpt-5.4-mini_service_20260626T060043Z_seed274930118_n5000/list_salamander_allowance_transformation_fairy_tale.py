#!/usr/bin/env python3
"""
storyworlds/worlds/list_salamander_allowance_transformation_fairy_tale.py
========================================================================

A small fairy-tale storyworld about a child, a salamander, a list, and an
allowance that can help a transformation come true.

Seed premise:
---
A child finds a talking salamander by a mossy well. The salamander wants a
small allowance to buy glow-seeds from the fairy market, but the child must
finish a kindly list of chores first. When the list is completed and the coins
are given in the right order, the salamander transforms from a plain little
pond-creature into a bright court messenger with golden spots.

World model:
---
- The list has named tasks and a reward.
- The child can be eager, stubborn, or gentle.
- The salamander has a desire meter, a hope meter, and a transformation meter.
- The allowance is a counted physical reward, but it also changes feelings:
  earned coins increase trust and calm.
- If the list is skipped, the allowance cannot be spent honestly and the
  transformation does not happen.
- If the list is completed, the salamander receives the allowance, spends it on
  a fairy-market charm, and transforms.

Style:
---
Fairy-tale prose, child-facing, concrete, and state-driven.

Contract notes:
---
- Self-contained stdlib script under storyworlds/worlds/
- Imports storyworlds/results.py eagerly
- Imports storyworlds/asp.py lazily inside ASP helpers
- Defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- Supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    salamander: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "mother", "woman"}
        male = {"boy", "king", "prince", "father", "man"}
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
    place: str = "the mossy well"
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
    clue: str
    reward: str
    feature: str = ""
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
    id: str
    label: str
    phrase: str
    region: str
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
class Charm:
    id: str
    label: str
    prep: str
    tail: str
    needed: int
    transformation: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.task_done: list[str] = []
        self.allowance_spent: bool = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.task_done = list(self.task_done)
        c.allowance_spent = self.allowance_spent
        return c


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


def _r_complete_list(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if child.meters.get("list_progress", 0.0) < THRESHOLD:
        return out
    if ("list_done",) in world.fired:
        return out
    world.fired.add(("list_done",))
    world.facts["list_done"] = True
    out.append("The little list was finished at last.")
    return out


def _r_allowance_earned(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    salamander = world.entities.get("salamander")
    if not child or not salamander:
        return out
    if child.meters.get("list_progress", 0.0) < THRESHOLD:
        return out
    if world.fired.__contains__(("allowance_earned",)):
        return out
    world.fired.add(("allowance_earned",))
    salamander.meters["allowance"] = salamander.meters.get("allowance", 0.0) + 3
    salamander.memes["hope"] = salamander.memes.get("hope", 0.0) + 1
    out.append("Because the list was done, three shiny coins became allowance in the salamander's palm.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    salamander = world.entities.get("salamander")
    if not salamander:
        return out
    if salamander.meters.get("allowance", 0.0) < 3:
        return out
    if salamander.meters.get("transformation", 0.0) >= THRESHOLD:
        return out
    if world.fired.__contains__(("transform",)):
        return out
    world.fired.add(("transform",))
    salamander.meters["transformation"] = 1.0
    salamander.type = "messenger"
    salamander.label = "the lantern messenger"
    salamander.phrase = "a bright court messenger with golden spots"
    salamander.memes["joy"] = salamander.memes.get("joy", 0.0) + 1
    out.append("The salamander touched the charm and changed into a bright court messenger with golden spots.")
    return out


CAUSAL_RULES = [
    Rule("complete_list", _r_complete_list),
    Rule("allowance_earned", _r_allowance_earned),
    Rule("transformation", _r_transformation),
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


def _do_task(world: World, child: Entity, task: Task, narrate: bool = True) -> None:
    if task.id in world.task_done:
        return
    child.meters["list_progress"] = child.meters.get("list_progress", 0.0) + 1
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    world.task_done.append(task.id)
    world.facts.setdefault("tasks", []).append(task.id)
    propagate(world, narrate=narrate)


def predict_outcome(world: World, child: Entity) -> dict:
    sim = world.copy()
    sim_child = sim.get(child.id)
    for task_id in sim.facts["plan_tasks"]:
        _do_task(sim, sim_child, _safe_lookup(TASKS, task_id), narrate=False)
    salamander = sim.entities["salamander"]
    return {
        "list_done": sim.facts.get("list_done", False),
        "allowance": salamander.meters.get("allowance", 0.0),
        "transformed": salamander.meters.get("transformation", 0.0) >= THRESHOLD,
    }


def introduce(world: World, child: Entity, salamander: Entity, prize: Prize) -> None:
    world.say(
        f"Once by a mossy well, a little {child.type} named {child.id} found "
        f"a talking salamander with a kind face and a pocket for allowance."
    )
    world.say(
        f"The salamander wanted {prize.phrase} from the fairy market, but first there was a careful list to finish."
    )


def show_list(world: World, child: Entity, task_ids: list[str]) -> None:
    tasks = [_safe_lookup(TASKS, t) for t in task_ids]
    names = ", ".join(t.clue for t in tasks[:-1]) + (", and " if len(tasks) > 1 else "") + tasks[-1].clue
    world.say(
        f"The list said to {names}. {child.id} looked at it and nodded, though the day was still young."
    )


def worry(world: World, child: Entity, salamander: Entity, prize: Prize) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f"{child.id} wanted to help at once, but {child.pronoun('possessive')} eyes kept going to the allowance jar and the {prize.label}."
    )


def work(world: World, child: Entity, task_ids: list[str]) -> None:
    for t in task_ids:
        task = _safe_lookup(TASKS, t)
        world.say(f"{child.id} did the next thing on the list: {task.gerund}.")
        _do_task(world, world.get(child.id), task)


def payment(world: World, salamander: Entity, charm: Charm) -> None:
    salamander.meters["allowance"] = salamander.meters.get("allowance", 0.0) - charm.needed
    world.allowance_spent = True
    world.say(
        f"Then the salamander spent the allowance on {charm.label}, just as the fairy keeper had taught."
    )


def transform_scene(world: World, salamander: Entity, charm: Charm) -> None:
    if salamander.meters.get("transformation", 0.0) >= THRESHOLD:
        world.say(
            f"{salamander.label.capitalize()} smiled as the charm warmed, and the small body became {salamander.phrase}."
        )


def tell(setting: Setting, task_ids: list[str], prize: Prize, charm: Charm,
         child_name: str = "Mira", child_type: str = "girl",
         child_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type,
                             traits=["little"] + (child_traits or ["kind", "brave"])))
    salamander = world.add(Entity(
        id="salamander", kind="character", type="salamander",
        label="the salamander", phrase="a plain little pond-creature",
        owner=child.id
    ))
    world.facts["plan_tasks"] = list(task_ids)
    world.facts["prize"] = prize
    world.facts["charm"] = charm
    world.facts["child"] = child
    world.facts["salamander"] = salamander

    introduce(world, child, salamander, prize)
    world.para()
    show_list(world, child, task_ids)
    worry(world, child, salamander, prize)
    world.para()
    work(world, child, task_ids)
    if salamander.meters.get("allowance", 0.0) >= charm.needed:
        payment(world, salamander, charm)
        propagate(world, narrate=True)
        transform_scene(world, salamander, charm)
    else:
        world.say("But the list was not enough, so the allowance stayed in the jar and the transformation never began.")
    world.facts["transformed"] = salamander.meters.get("transformation", 0.0) >= THRESHOLD
    return world


SETTING = Setting(place="the mossy well", indoors=False, affords={"tidy", "fetch", "greet"})

TASKS = {
    "tidy": Task(
        id="tidy",
        verb="tidy the cobbles",
        gerund="tidying the cobbles",
        clue="tidy the cobbles",
        reward="a clean path",
        feature="list",
        tags={"list"},
    ),
    "fetch": Task(
        id="fetch",
        verb="fetch a pail of water",
        gerund="fetching a pail of water",
        clue="fetch a pail of water",
        reward="a brimming pail",
        feature="water",
        tags={"water", "list"},
    ),
    "greet": Task(
        id="greet",
        verb="greet the sleepy bees kindly",
        gerund="greeting the sleepy bees kindly",
        clue="greet the sleepy bees kindly",
        reward="a gentle hum",
        feature="fairy",
        tags={"fairy", "list"},
    ),
}

PRIZES = {
    "glowseeds": Prize(id="glowseeds", label="glow-seeds", phrase="a little bag of glow-seeds", region="palm", plural=True),
    "silverribbon": Prize(id="silverribbon", label="silver ribbon", phrase="a silver ribbon for the market stall", region="neck"),
    "honeycake": Prize(id="honeycake", label="honey cake", phrase="a honey cake wrapped in waxed paper", region="hand"),
}

CHARMS = {
    "court": Charm(
        id="court",
        label="a court charm",
        prep="place the coins beneath a moonflower",
        tail="laid the coins under the moonflower",
        needed=3,
        transformation="into a bright court messenger",
        tags={"transformation", "fairy"},
    ),
    "spark": Charm(
        id="spark",
        label="a spark charm",
        prep="turn the coins three times in a ring of herbs",
        tail="turned the coins three times in the herb ring",
        needed=2,
        transformation="into a glowing helper",
        tags={"transformation"},
    ),
}

NAMES = ["Mira", "Elin", "Tilda", "Nora", "Lina", "Pippa", "Sana", "Wren"]
TRAITS = ["kind", "curious", "gentle", "brave", "patient", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"well": SETTING}.items():
        for task_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, task_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    task1: str
    task2: str
    task3: str
    prize: str
    charm: str
    name: str
    gender: str
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


KNOWLEDGE = {
    "list": [("What is a list?", "A list is a set of things written down one after another so you can remember them and do them in order.")],
    "salamander": [("What is a salamander?", "A salamander is a small amphibian, often spotted and smooth, that likes damp places near water.")],
    "allowance": [("What is allowance?", "Allowance is a little money given for helping or for doing chores.")],
    "transformation": [("What is a transformation?", "A transformation is a big change in how something looks or is, like a plain thing becoming something magical.")],
    "fairy": [("What is a fairy tale?", "A fairy tale is a made-up story with magic, chances, and special endings.")],
}
KNOWLEDGE_ORDER = ["list", "salamander", "allowance", "transformation", "fairy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a child about a list, a salamander, and an allowance.',
        f"Tell a gentle story where {f['child'].id} helps a salamander earn allowance by finishing a list.",
        f"Write a magical story that ends with a transformation after the allowance is spent wisely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    salamander: Entity = _safe_fact(world, f, "salamander")
    prize: Prize = _safe_fact(world, f, "prize")
    charm: Charm = _safe_fact(world, f, "charm")
    tasks = [_safe_lookup(TASKS, t) for t in f["tasks"]]
    task_names = ", ".join(t.clue for t in tasks)
    qa = [
        QAItem(
            question=f"What did {child.id} need to finish before the salamander could get allowance?",
            answer=f"{child.id} needed to finish the list: {task_names}. Only then could the salamander earn the allowance honestly.",
        ),
        QAItem(
            question=f"What did the salamander want to buy with the allowance?",
            answer=f"The salamander wanted {prize.phrase} from the fairy market.",
        ),
        QAItem(
            question=f"What changed after the coins were spent on {charm.label}?",
            answer=f"After the coins were spent on {charm.label}, the salamander transformed into {salamander.phrase}.",
        ),
    ]
    if f.get("transformed"):
        qa.append(
            QAItem(
                question=f"How did the transformation happen in the end?",
                answer=f"The list was finished, the allowance was earned, and then the salamander used the charm to transform at the well.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"list", "salamander", "allowance", "transformation", "fairy"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    lines.append(f"  tasks done: {world.task_done}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="well", task1="tidy", task2="fetch", task3="greet", prize="glowseeds", charm="court", name="Mira", gender="girl", trait="kind"),
    StoryParams(place="well", task1="fetch", task2="tidy", task3="greet", prize="silverribbon", charm="spark", name="Elin", gender="girl", trait="curious"),
]


def explain_rejection() -> str:
    return "(No story: the list must contain at least one task, the salamander must earn allowance, and the charm must be able to transform it.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "well"))
    lines.append(asp.fact("affords", "well", "tidy"))
    lines.append(asp.fact("affords", "well", "fetch"))
    lines.append(asp.fact("affords", "well", "greet"))
    for t in TASKS.values():
        lines.append(asp.fact("task", t.id))
        lines.append(asp.fact("task_tag", t.id, "list"))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", t.id, tag))
    for p in PRIZES.values():
        lines.append(asp.fact("prize", p.id))
        lines.append(asp.fact("prize_region", p.id, p.region))
    for c in CHARMS.values():
        lines.append(asp.fact("charm", c.id))
        lines.append(asp.fact("needed", c.id, c.needed))
        lines.append(asp.fact("transforms_to", c.id, c.transformation))
    return "\n".join(lines)


ASP_RULES = r"""
done_list(S) :- task_seq(S), all_tasks_done(S).
earn_allowance(S) :- done_list(S).
can_transform(S) :- earn_allowance(S), charm(C), transforms_to(C, _).
valid_story(S) :- can_transform(S).
#show valid_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    atoms = asp.atoms(model, "valid_story")
    ok = bool(atoms)
    if ok:
        print("OK: ASP gate is present and solvable.")
        return 0
    print("MISMATCH: ASP gate did not produce a valid story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: a list, a salamander, allowance, and transformation.")
    ap.add_argument("--place", choices=["well"], default=None)
    ap.add_argument("--prize", choices=PRIZES.keys(), default=None)
    ap.add_argument("--charm", choices=CHARMS.keys(), default=None)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    charm = getattr(args, "charm", None) or rng.choice(list(CHARMS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    tasks = rng.sample(list(TASKS), 3)
    return StoryParams(place="well", task1=tasks[0], task2=tasks[1], task3=tasks[2], prize=prize, charm=charm, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, [params.task1, params.task2, params.task3], _safe_lookup(PRIZES, params.prize), _safe_lookup(CHARMS, params.charm), params.name, params.gender, [params.trait, "stubborn"])
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
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP solvable." if asp.atoms(model, "valid_story") else "No model.")
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
