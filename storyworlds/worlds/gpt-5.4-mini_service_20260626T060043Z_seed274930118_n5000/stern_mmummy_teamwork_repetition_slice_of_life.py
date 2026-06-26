#!/usr/bin/env python3
"""
A small slice-of-life story world about a stern mmummy, a child, and the quiet
work of teamwork through repetition.

Seed premise:
- A stern mmummy notices a small household task is not getting done.
- The child wants to help, but keeps making the same mistake.
- Through repeated practice, they learn to work together.
- The ending proves the change in the home's state: the task is finished, and
  the mood is softer.

The world is designed so state drives prose:
- meters model physical progress, counts, and repeated actions
- memes model feelings like worry, patience, pride, and closeness
- the story changes as the world changes
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
# Core world model
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "mmummy"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the kitchen"
    time_of_day: str = "morning"
    weather: str = "quiet"
    affords: set[str] = field(default_factory=lambda: {"tidy", "cook", "wash"})
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
    label: str
    phrase: str
    verb: str
    repeated_step: str
    finish_step: str
    difficulty: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
    helps: set[str]
    repeated_step: str
    finish_step: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.tasks_done: float = 0.0
        self.mistakes: int = 0
        self.repetitions: int = 0
        self.teamwork: float = 0.0

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.tasks_done = self.tasks_done
        clone.mistakes = self.mistakes
        clone.repetitions = self.repetitions
        clone.teamwork = self.teamwork
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", time_of_day="morning", weather="quiet", affords={"tidy", "wash", "cook"}),
    "living_room": Setting(place="the living room", time_of_day="afternoon", weather="soft light", affords={"tidy", "fold", "sort"}),
    "laundry_room": Setting(place="the laundry room", time_of_day="late morning", weather="humming", affords={"wash", "fold", "sort"}),
}

TASKS = {
    "tidy_blocks": Task(
        id="tidy_blocks",
        label="blocks",
        phrase="a pile of blocks",
        verb="tidy the blocks",
        repeated_step="stacking the blocks the right way again",
        finish_step="the blocks stood in a neat little tower",
        difficulty="tricky",
        keyword="blocks",
        tags={"tidy", "teamwork", "repetition"},
    ),
    "fold_towels": Task(
        id="fold_towels",
        label="towels",
        phrase="a basket of towels",
        verb="fold the towels",
        repeated_step="folding one towel, then folding the next one the same careful way",
        finish_step="the towels lay in a soft square stack",
        difficulty="steady",
        keyword="towels",
        tags={"fold", "teamwork", "repetition"},
    ),
    "sort_socks": Task(
        id="sort_socks",
        label="socks",
        phrase="a little basket of socks",
        verb="sort the socks",
        repeated_step="matching one sock after another by color",
        finish_step="the socks sat in matching pairs",
        difficulty="patient",
        keyword="socks",
        tags={"sort", "teamwork", "repetition"},
    ),
}

TOOLS = {
    "basket": Tool(
        id="basket",
        label="a wicker basket",
        phrase="a wicker basket",
        helps={"fold", "sort", "tidy"},
        repeated_step="carrying the pieces back to the right spot again and again",
        finish_step="the basket stood empty and ready on the shelf",
    ),
    "cloth": Tool(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth",
        helps={"tidy", "wash"},
        repeated_step="wiping the table in slow, even circles",
        finish_step="the table shone without crumbs",
    ),
    "pairing_cards": Tool(
        id="pairing_cards",
        label="pairing cards",
        phrase="pairing cards with small pictures",
        helps={"sort"},
        repeated_step="checking each card against the next one",
        finish_step="the pairs matched neatly in a line",
    ),
}

NAMES = ["Mina", "Noah", "June", "Leo", "Ivy", "Owen", "Lena", "Theo"]
TRAITS = ["quiet", "careful", "curious", "gentle", "small", "bright"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    task: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    parent_label: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
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


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _pluralize(noun: str) -> str:
    if noun.endswith("s"):
        return noun
    return noun + "s"


def _child_pronouns(gender: str) -> dict[str, str]:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}
    return {"subject": "he", "object": "him", "possessive": "his"}


def _parent_pronouns(gender: str) -> dict[str, str]:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}
    return {"subject": "he", "object": "him", "possessive": "his"}


def _task_requires_teamwork(task: Task) -> bool:
    return "teamwork" in task.tags


def _task_requires_repetition(task: Task) -> bool:
    return "repetition" in task.tags


def _select_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS.values():
        if task.id.split("_")[0] in tool.helps or any(t in tool.helps for t in task.tags):
            return tool
    return None


def _reasonableness_gate(task: Task) -> bool:
    return _task_requires_teamwork(task) and _task_requires_repetition(task) and _select_tool(task) is not None


# ---------------------------------------------------------------------------
# World events
# ---------------------------------------------------------------------------

def _introduce(world: World, child: Entity, parent: Entity, task: Task) -> None:
    world.say(
        f"{child.id} was { _article(child.traits[0]) } {child.traits[0]} little {child.type} who liked helping around {world.setting.place}."
    )
    world.say(
        f"{parent.id} was a stern {parent.type}, but {parent.id} always noticed when a job needed doing."
    )
    world.say(
        f"That day, there was {task.phrase} waiting to be put right."
    )


def _start_task(world: World, child: Entity, parent: Entity, task: Task) -> None:
    child.memes["eager"] = child.memes.get("eager", 0.0) + 1
    parent.memes["sternness"] = parent.memes.get("sternness", 0.0) + 1
    world.say(
        f"{child.id} wanted to {task.verb}, but {child.id} kept doing it the wrong way."
    )
    world.say(
        f"{parent.id} pointed at the mess and said, \"Again, but slower.\""
    )


def _repeat_step(world: World, child: Entity, parent: Entity, task: Task, tool: Tool) -> None:
    world.repetitions += 1
    child.meters["tries"] = child.meters.get("tries", 0.0) + 1
    world.tasks_done = min(1.0, world.tasks_done + 0.25)

    if world.repetitions == 1:
        world.mistakes += 1
        child.memes["frustrated"] = child.memes.get("frustrated", 0.0) + 1
        world.say(
            f"The first try slipped apart, so {child.id} and {parent.id} tried again."
        )
    elif world.repetitions == 2:
        child.memes["focus"] = child.memes.get("focus", 0.0) + 1
        world.say(
            f"The next time, {parent.id} showed {child.id} {tool.phrase}, and they kept going step by step."
        )
    elif world.repetitions == 3:
        world.teamwork += 0.5
        child.memes["confidence"] = child.memes.get("confidence", 0.0) + 1
        parent.memes["pride"] = parent.memes.get("pride", 0.0) + 1
        world.say(
            f"{child.id} copied the rhythm and matched {parent.id}'s pace."
        )
    else:
        world.teamwork += 0.5
        world.say(
            f"With one more careful try, the two of them worked like a little team."
        )


def _finish(world: World, child: Entity, parent: Entity, task: Task, tool: Tool) -> None:
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    parent.memes["softness"] = parent.memes.get("softness", 0.0) + 1
    world.say(
        f"At last, {task.finish_step}, and {parent.id} nodded at {child.id} with a small smile."
    )
    world.say(
        f"{child.id} stood a little taller, because {child.id} had helped make the room calm again."
    )


def tell(setting: Setting, task: Task, child_name: str, child_gender: str, parent_name: str, parent_gender: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, traits=[trait, "small"]))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, label="the mmummy"))
    tool = _select_tool(task)
    if tool is None:
        pass
    helper = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase))

    _introduce(world, child, parent, task)
    world.para()
    _start_task(world, child, parent, task)

    world.say(
        f"{parent.id} set {helper.phrase} on the table and showed {child.id} the first step."
    )
    world.say(f"{child.id} listened, then tried again.")

    world.para()
    while world.repetitions < 4:
        _repeat_step(world, child, parent, task, tool)

    _finish(world, child, parent, task, tool)

    world.facts.update(
        child=child,
        parent=parent,
        task=task,
        tool=tool,
        setting=setting,
        done=world.tasks_done >= THRESHOLD,
        repeated=world.repetitions,
        teamwork=world.teamwork,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    task = _safe_fact(world, f, "task")
    return [
        f"Write a short slice-of-life story about a stern mmummy teaching {child.id} to {task.verb} through repetition.",
        f"Tell a gentle household story where {child.id} and {parent.id} work together again and again until {task.finish_step}.",
        f"Write a child-friendly story about teamwork, repetition, and a stern mmummy helping a small child finish {task.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    task = _safe_fact(world, f, "task")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    child_p = _child_pronouns(child.type)
    parent_p = _parent_pronouns(parent.type)
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id} and {parent.id}, a stern mmummy who helps {child.id} learn by repeating the steps.",
        ),
        QAItem(
            question=f"What was {child.id} trying to do?",
            answer=f"{child.id} was trying to {task.verb}, but {child.id} needed to practice it several times.",
        ),
        QAItem(
            question=f"What did {parent.id} use to help with the job?",
            answer=f"{parent.id} used {tool.phrase} to show {child.id} a steady way to do the task.",
        ),
        QAItem(
            question=f"Why did the story need repetition?",
            answer=f"It needed repetition because {child.id} did not get {task.verb} right on the first try, so {parent.id} said to do it again and again until it felt easy.",
        ),
        QAItem(
            question=f"How did teamwork change the ending?",
            answer=f"Teamwork helped because {child.id} and {parent.id} kept working side by side, and at the end {task.finish_step}.",
        ),
    ]
    if f["repeated"] >= 4:
        qa.append(
            QAItem(
                question=f"How many times did they practice?",
                answer=f"They practiced several times, and the story shows {f['repeated']} careful repeats before the job was finished.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together instead of alone.",
        ),
        QAItem(
            question="Why can teamwork make a job easier?",
            answer="Teamwork can make a job easier because two people can share the work, keep each other on track, and finish together.",
        ),
    ],
    "repetition": [
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing something again and again, often to practice or make it better.",
        ),
        QAItem(
            question="Why do people repeat things when they are learning?",
            answer="People repeat things when they are learning so they can remember the steps and get more careful each time.",
        ),
    ],
    "stern": [
        QAItem(
            question="What does stern mean?",
            answer="Stern means serious and firm, like someone who expects careful behavior.",
        )
    ],
    "mmummy": [
        QAItem(
            question="Who is a mmummy?",
            answer="A mmummy is a mother figure in the story, the one who watches over the child and gives guidance.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["teamwork"])
    out.extend(WORLD_KNOWLEDGE["repetition"])
    out.extend(WORLD_KNOWLEDGE["stern"])
    out.extend(WORLD_KNOWLEDGE["mmummy"])
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  tasks_done={world.tasks_done:.2f} mistakes={world.mistakes} repetitions={world.repetitions} teamwork={world.teamwork:.2f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
task_with_teamwork(T) :- task(T), teamwork_required(T).
task_with_repetition(T) :- task(T), repetition_required(T).
reasonable(T) :- task_with_teamwork(T), task_with_repetition(T), tool_for(T, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        if _task_requires_teamwork(t):
            lines.append(asp.fact("teamwork_required", tid))
        if _task_requires_repetition(t):
            lines.append(asp.fact("repetition_required", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for uid, u in TOOLS.items():
        lines.append(asp.fact("tool", uid))
        for h in sorted(u.helps):
            lines.append(asp.fact("tool_for", h, uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, task in TASKS.items():
            if task.id in setting.affords and _reasonableness_gate(task):
                combos.append((sid, tid))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/1.\n"))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import asp
    py = {t for _, t in valid_combos()}
    amodel = asp.one_model(asp_program("#show reasonable/1.\n"))
    cl = {a[0] for a in asp.atoms(amodel, "reasonable")}
    if py == cl:
        print(f"OK: ASP parity matches Python reasonableness gate ({len(py)} tasks).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a stern mmummy, teamwork, and repetition.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-label", default="mmummy")
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
    if getattr(args, "task", None) and getattr(args, "place", None):
        if getattr(args, "task", None) not in _safe_lookup(SETTINGS, getattr(args, "place", None)).affords:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "task", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        if not _reasonableness_gate(task):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "task", None):
        combos = [c for c in combos if c[1] == getattr(args, "task", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place_id, task_id = rng.choice(list(combos))
    task = _safe_lookup(TASKS, task_id)
    child_gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    parent_gender = getattr(args, "parent_gender", None) or "girl"
    child_name = getattr(args, "child_name", None) or rng.choice(NAMES)
    parent_name = getattr(args, "parent_name", None) or "Mara"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        task=task_id,
        child_name=child_name,
        child_gender=child_gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
        parent_label=getattr(args, "parent_label", None),
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TASKS, params.task),
        params.child_name,
        params.child_gender,
        params.parent_name,
        params.parent_gender,
        params.trait,
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


CURATED = [
    StoryParams(place="kitchen", task="tidy_blocks", child_name="Mina", child_gender="girl", parent_name="Mara", parent_gender="girl", parent_label="mmummy", trait="careful"),
    StoryParams(place="living_room", task="fold_towels", child_name="Leo", child_gender="boy", parent_name="Mara", parent_gender="girl", parent_label="mmummy", trait="quiet"),
    StoryParams(place="laundry_room", task="sort_socks", child_name="Ivy", child_gender="girl", parent_name="Mara", parent_gender="girl", parent_label="mmummy", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/1.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} reasonable task combos:")
        for place, task in valid_combos():
            print(f"  {place:12} {task}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
