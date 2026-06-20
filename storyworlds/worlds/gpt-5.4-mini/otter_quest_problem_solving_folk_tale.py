#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/otter_quest_problem_solving_folk_tale.py
========================================================================

A standalone storyworld for a tiny folk-tale quest about an otter who needs to
solve a practical problem before reaching a small treasure.

The domain:
- an otter must travel through a riverland and complete a quest
- a problem blocks the path or the prize
- the otter uses problem solving, with help from a folk-tale helper or elder
- the ending proves the obstacle was fixed and the quest changed the world

The story quality goal is a child-facing folk tale: concrete, calm, and
state-driven, with a clear beginning, middle turn, and ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother", "grandfather": "grandfather"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    scene: str
    quest_path: str
    ending_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Problem:
    id: str
    label: str
    description: str
    obstacle_type: str
    severity: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_text: str
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Helper:
    id: str
    label: str
    speech: str
    method: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    otter = world.get("otter")
    if otter.meters["stuck"] >= THRESHOLD and ("worry", "otter") not in world.fired:
        world.fired.add(("worry", "otter"))
        otter.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    otter = world.get("otter")
    if otter.meters["stuck"] < THRESHOLD and otter.meters["quest_done"] >= THRESHOLD:
        if ("relief", "otter") not in world.fired:
            world.fired.add(("relief", "otter"))
            otter.memes["joy"] += 1
            otter.memes["relief"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("relief", "social", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def problem_blocks_tool(problem: Problem, tool: Tool) -> bool:
    return problem.obstacle_type in {"river", "mire", "brambles"} and tool.power >= 1


def helper_matches(problem: Problem, helper: Helper) -> bool:
    return problem.obstacle_type in helper.tags or "problem_solving" in helper.tags


def is_resolved(problem: Problem, tool: Tool, helper: Optional[Helper]) -> bool:
    needed = problem.severity
    bonus = 1 if helper is not None else 0
    return tool.power + bonus >= needed


def _cross(world: World, problem: Problem, tool: Tool, helper: Optional[Helper]) -> None:
    otter = world.get("otter")
    otter.meters["stuck"] += 1
    otter.memes["determination"] += 1
    if helper:
        otter.memes["hope"] += 1
    propagate(world, narrate=False)


def tell(setting: Setting, problem: Problem, tool: Tool, helper: Optional[Helper]) -> World:
    world = World()
    otter = world.add(Entity(id="otter", kind="character", type="otter", role="hero", traits=["small", "curious"]))
    elder = world.add(Entity(id="elder", kind="character", type="grandmother", role="helper", label="the river elder"))
    world.add(Entity(id="bridge", kind="thing", type="thing", label="the broken bridge"))
    world.add(Entity(id="prize", kind="thing", type="thing", label="the silver reed"))
    otter.memes["curiosity"] = 1.0

    world.say(
        f"By the silver river, a little otter named {otter.id} lived beside {setting.place}. "
        f"{setting.scene}"
    )
    world.say(
        f"One morning, {otter.id} heard of a small quest: reach {setting.quest_path} and bring back "
        f"the silver reed."
    )
    world.say(
        f"But {problem.description}, and that made the way hard for a small swimmer."
    )

    world.para()
    otter.memes["desire"] += 1
    world.say(
        f"{otter.id} sniffed the air and looked at the path. {otter.pronoun().capitalize()} wanted to go on, "
        f"but the obstacle stood in the way."
    )

    if helper and helper_matches(problem, helper):
        world.say(
            f"Then {helper.label} came by and said, '{helper.speech}'"
        )
    else:
        world.say(
            f"Then the river elder sat on a stone and said, 'Slow feet and a wise head can find a way.'"
        )

    world.para()
    _cross(world, problem, tool, helper)
    if is_resolved(problem, tool, helper):
        otter.meters["quest_done"] += 1
        world.say(
            f"{otter.id} used {tool.phrase} and {tool.use_text}."
        )
        if helper:
            world.say(
                f"With that help, the path opened, and the current no longer bullied the tiny traveler."
            )
        else:
            world.say(
                f"Little by little, the path gave way, and the river's noise turned soft."
            )
        world.say(
            f"{otter.id} reached the silver reed, held it high, and scampered home with the prize."
        )
        world.para()
        world.say(
            f"At the end, {setting.ending_image}, and {otter.id} sat on the bank, proud and bright."
        )
    else:
        world.say(
            f"{otter.id} tried {tool.phrase}, but the problem was still too big."
        )
        world.say(
            f"So {otter.id} called for the elder again, and together they found another way around the trouble."
        )
        otter.meters["quest_done"] += 1
        world.say(
            f"At last, the silver reed was safe in {otter.id}'s paws, and the river quieted behind {otter.pronoun('object')}."
        )
        world.para()
        world.say(
            f"At the end, {setting.ending_image}, and the otter's clever heart had learned a new path."
        )

    world.facts.update(setting=setting, problem=problem, tool=tool, helper=helper, otter=otter)
    return world


SETTINGS = {
    "riverbank": Setting(
        "riverbank",
        "a mossy riverbank",
        "The reeds bowed low, and dragonflies stitched the air with blue thread.",
        "the far bend of the river",
        "the river sparkled under the reeds",
    ),
    "willow_grove": Setting(
        "willow_grove",
        "a willow grove",
        "The willow branches brushed the water like green hair, and the shade felt old and kind.",
        "the hidden ford",
        "the water glimmered between the roots",
    ),
    "quiet_marsh": Setting(
        "quiet_marsh",
        "a quiet marsh",
        "The marsh hummed with frogs, and the mud made soft prints for careful paws.",
        "the stone islet",
        "the little pool shone still and silver",
    ),
}

PROBLEMS = {
    "high_water": Problem("high_water", "high water", "the river had swollen from the rain", "river", 2, {"river"}),
    "fallen_log": Problem("fallen_log", "fallen log", "a fallen log blocked the path over the water", "bridge", 2, {"bridge", "problem_solving"}),
    "tangled_reeds": Problem("tangled_reeds", "tangled reeds", "tangled reeds made a narrow tunnel too tight to pass", "brambles", 3, {"brambles"}),
    "muddy_step": Problem("muddy_step", "muddy step", "the next step sank deep in the mud and would not hold", "mire", 3, {"mire"}),
}

TOOLS = {
    "stick": Tool("stick", "a smooth stick", "a smooth stick", "prodded the reeds aside", 1, {"river", "brambles"}),
    "rope": Tool("rope", "a long rope", "a long rope", "tied a safe line to the willow root", 2, {"bridge", "river"}),
    "stones": Tool("stones", "flat stones", "flat stones", "laid stepping stones one by one", 2, {"mire", "river"}),
    "basket": Tool("basket", "a woven basket", "a woven basket", "carried the reed carefully and kept balance", 1, {"problem_solving"}),
}

HELPERS = {
    "elder": Helper("elder", "the river elder", "Look for the dry root and trust the smallest step.", "problem_solving", {"problem_solving"}),
    "heron": Helper("heron", "a white heron", "Stand where the water is shallow and let your eyes do the work.", "river", {"river"}),
    "turtle": Helper("turtle", "an old turtle", "Slow is not stuck; slow can still reach the shore.", "mire", {"mire"}),
}



@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("riverbank", "high_water", "rope", "elder"),
    ("willow_grove", "fallen_log", "stick", "heron"),
    ("quiet_marsh", "muddy_step", "stones", "turtle"),
]



def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if not problem_blocks_tool(problem, tool):
                    continue
                for hid, helper in HELPERs.items():
                    if helper_matches(problem, helper) and is_resolved(problem, tool, helper):
                        combos.append((sid, pid, tid, hid))
    return combos
