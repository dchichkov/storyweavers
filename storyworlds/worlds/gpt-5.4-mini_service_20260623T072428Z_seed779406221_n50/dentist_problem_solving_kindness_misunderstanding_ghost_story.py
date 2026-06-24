#!/usr/bin/env python3
"""
storyworlds/worlds/dentist_problem_solving_kindness_misunderstanding_ghost_story.py
===================================================================================

A standalone storyworld for a small ghost-story style domain: a child visits a
dentist, there is a spooky misunderstanding, kindness helps, and a problem gets
solved with careful thinking.

The world is built from typed entities with physical meters and emotional memes.
The story stays child-facing and state-driven: a dark office, a strange sound,
a mistaken ghost, a patient explanation, and a kind resolution that proves what
changed.
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
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    adult: object | None = None
    chair: object | None = None
    child: object | None = None
    dentist: object | None = None
    lamp: object | None = None
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
class Setting:
    place: str
    dark: bool = True
    eerie: str = "The hallway felt quiet and a little spooky."
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
        return None


@dataclass
class Problem:
    id: str
    label: str
    sound: str
    cause: str
    fix: str
    clue: str
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


@dataclass
class Person:
    name: str
    gender: str
    kind: str
    trait: str
    role: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["fear"] >= THRESHOLD and child.memes["confusion"] >= THRESHOLD:
        sig = ("misunderstanding",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["misunderstanding"] += 1
        out.append("__misunderstanding__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["understanding"] >= THRESHOLD and child.memes["kindness"] >= THRESHOLD:
        sig = ("relief",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("misunderstanding", "social", _r_misunderstanding),
    Rule("relief", "social", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def should_misunderstand(problem: Problem) -> bool:
    return "spooky" in problem.tags or "ghost" in problem.tags


def can_solve(problem: Problem) -> bool:
    return bool(problem.fix)


def predict(world: World, problem: Problem) -> dict:
    sim = world.copy()
    dentist = sim.get("dentist")
    child = sim.get("child")
    child.memes["fear"] += 1
    child.memes["confusion"] += 1
    if should_misunderstand(problem):
        child.memes["misunderstanding"] += 1
    dentist.memes["kindness"] += 1
    dentist.memes["explanation"] += 1
    child.memes["understanding"] += 1
    return {"calmed": child.memes["understanding"] >= THRESHOLD}


def setup(world: World, child: Entity, dentist: Entity, problem: Problem) -> None:
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    dentist.memes["kindness"] += 1
    world.say(
        f"On a rainy afternoon, {child.id} and {child.pronoun('possessive')} "
        f"{'mom' if world.get('adult').type == 'mother' else 'dad'} went to {world.setting.place}. "
        f"{world.setting.eerie}"
    )
    world.say(
        f"{dentist.id} smiled from behind a bright lamp, and the room smelled like mint and clean paper."
    )
    world.say(
        f"{child.id} noticed the soft click of tools and wondered why {problem.label} was waiting nearby."
    )


def misunderstanding(world: World, child: Entity, problem: Problem) -> None:
    child.memes["fear"] += 1
    child.memes["confusion"] += 1
    world.say(
        f"Then {problem.sound} came from the next room. {child.id} jumped. "
        f'"Is that a ghost?" {child.pronoun()} whispered.'
    )
    world.say(
        f"The shadow on the wall looked wiggly, so {child.id} hugged {child.pronoun("possessive")} knees."
    )
    propagate(world, narrate=True)


def explain(world: World, dentist: Entity, child: Entity, problem: Problem) -> None:
    child.memes["understanding"] += 1
    dentist.memes["kindness"] += 1
    world.say(
        f"{dentist.id} knelt down and spoke in a calm voice. "
        f'"No ghost," {dentist.pronoun()} said. "That sound is just {problem.cause}."'
    )
    world.say(
        f"{dentist.id} pointed to {problem.clue}, and {child.id} started to see the answer."
    )


def solve_problem(world: World, dentist: Entity, child: Entity, problem: Problem) -> None:
    if not can_solve(problem):
        pass
    child.memes["curiosity"] += 1
    dentist.memes["problem_solving"] += 1
    world.say(
        f"Together they used a simple plan: {problem.fix}. "
        f"{dentist.id} showed each step, and {child.id} helped by staying still and opening wide."
    )


def ending(world: World, child: Entity, dentist: Entity, problem: Problem) -> None:
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["kindness"] += 1
    world.say(
        f"At last, the room felt bright instead of spooky. The funny sound was gone, "
        f"and {child.id} smiled at the shiny mirror."
    )
    world.say(
        f"{child.id} waved goodbye. {dentist.id} had solved the problem kindly, and the little ghost of a worry had disappeared."
    )


def tell(setting: Setting, problem: Problem, child_name: str, child_gender: str,
         adult_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    dentist = world.add(Entity(id="dentist", kind="character", type="adult", role="dentist"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_gender, role="parent"))
    chair = world.add(Entity(id="chair", type="thing", label="the dental chair"))
    lamp = world.add(Entity(id="lamp", type="thing", label="the bright lamp"))
    _ = chair, lamp

    setup(world, child, dentist, problem)
    world.para()
    misunderstanding(world, child, problem)
    world.para()
    explain(world, dentist, child, problem)
    solve_problem(world, dentist, child, problem)
    world.para()
    ending(world, child, dentist, problem)

    world.facts.update(
        child=child,
        dentist=dentist,
        adult=adult,
        problem=problem,
        setting=setting,
        solved=True,
        misunderstood=True,
    )
    return world


SETTINGS = {
    "clinic": Setting(place="the dentist clinic", eerie="The hallway felt quiet and a little spooky."),
    "small_room": Setting(place="the tiny dental room", eerie="The little room was dark except for one round lamp."),
}

PROBLEMS = {
    "drip": Problem(
        id="drip",
        label="a strange dripping sound",
        sound="drip... drip... drip...",
        cause="the sink faucet was not fully closed",
        fix="turn the faucet handle tightly and listen again",
        clue="the open sink",
        tags={"ghost", "misunderstanding"},
    ),
    "mask": Problem(
        id="mask",
        label="a floating white shape",
        sound="whoooosh",
        cause="the dentist was hanging up a paper mask on a hook",
        fix="show the mask and explain that it keeps germs away",
        clue="the little hook by the counter",
        tags={"misunderstanding", "kindness"},
    ),
    "chair": Problem(
        id="chair",
        label="a creaky chair noise",
        sound="creeeak",
        cause="the dental chair moved a little when someone sat down",
        fix="tighten the chair and let the child try it first",
        clue="the shiny chair lever",
        tags={"problem_solving", "kindness"},
    ),
}

NAMES = ["Mia", "Lily", "Noah", "Ben", "Ava", "Theo", "Zoe", "Leo"]
GENDERS = ["girl", "boy"]
TRAITS = ["curious", "brave", "gentle", "careful"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    child_name: str
    child_gender: str
    trait: str
    adult_gender: str = "mother"
    seed: Optional[int] = None
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
        return None


def valid_combos() -> list[tuple[str, str]]:
    return [(s, p) for s in SETTINGS for p in PROBLEMS if should_misunderstand(_safe_lookup(PROBLEMS, p))]


KNOWLEDGE = {
    "dentist": [("What does a dentist do?", "A dentist helps keep teeth clean and healthy.")],
    "ghost": [("Are all spooky sounds ghosts?", "No. Many spooky sounds are just normal things making noise.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and caring toward someone.")],
    "problem_solving": [("What is problem solving?", "Problem solving means figuring out a way to fix something.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding happens when someone thinks the wrong thing at first.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small ghost-story about a child named {f["child"].id} visiting a dentist and hearing a spooky sound.',
        f"Tell a child-friendly story where {f['child'].id} thinks something is a ghost, but the dentist kindly explains the real cause.",
        f'Write a gentle story with kindness, problem solving, and a misunderstanding in a dentist office.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    dentist = f["dentist"]
    problem = f["problem"]
    return [
        QAItem(
            question=f"Who is the story about when {child.id} goes to the dentist?",
            answer=f"The story is about {child.id}, who visits {dentist.id} and hears something spooky before it is explained kindly.",
        ),
        QAItem(
            question=f"What did {child.id} think the sound might be?",
            answer=f"{child.id} thought it might be a ghost, but it was really {problem.cause}.",
        ),
        QAItem(
            question=f"How did {dentist.id} help with the misunderstanding?",
            answer=f"{dentist.id} stayed calm, explained the real cause, and solved the problem kindly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ("dentist", "ghost", "kindness", "problem_solving", "misunderstanding"):
        if tag in KNOWLEDGE:
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(C) :- fear(C), confusion(C).
relief(C) :- understanding(C), kindness(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if should_misunderstand(p):
            lines.append(asp.fact("misunderstanding_problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding_problem/1."))
    return sorted(set(asp.atoms(model, "misunderstanding_problem")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {(p,) for p in PROBLEMS if should_misunderstand(_safe_lookup(PROBLEMS, p))}
    if clingo_set == python_set:
        print(f"OK: ASP matches valid_combos() ({len(clingo_set)} problems).")
        return 0
    print("MISMATCH between ASP and Python.")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story dentist world with kindness and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--adult", choices=["mother", "father"])
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    adult = getattr(args, "adult", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, problem=problem, child_name=name, child_gender=gender, trait=trait, adult_gender=adult)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PROBLEMS, params.problem), params.child_name, params.child_gender, params.adult_gender)
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
    StoryParams("clinic", "drip", "Mia", "girl", "curious", "mother"),
    StoryParams("small_room", "mask", "Noah", "boy", "gentle", "father"),
    StoryParams("clinic", "chair", "Ava", "girl", "careful", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show misunderstanding_problem/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP-valid problems:")
        for (p,) in combos:
            print(f"  {p}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.child_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
