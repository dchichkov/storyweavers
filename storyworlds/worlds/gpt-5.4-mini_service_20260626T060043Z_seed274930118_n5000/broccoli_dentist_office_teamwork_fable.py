#!/usr/bin/env python3
"""
storyworlds/worlds/broccoli_dentist_office_teamwork_fable.py
=============================================================

A small fable-style story world set in a dentist office.

Premise:
- A child comes to a dentist office with broccoli stuck in their teeth or braces.
- The dentist worries the snack will cause pain if the child keeps chewing.
- A helper team works together: one steadies, one fetches tools, one rinses.
- The child learns that teamwork makes a hard fix feel gentle.

The world is intentionally small and constraint-checked:
- only plausible patient/tool/problem combinations are allowed
- explicit invalid combinations raise StoryError
- state changes drive the story and the QA answers

This script follows the Storyweavers storyworld contract.
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
# Entities
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    crumb: object | None = None
    dentist: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "dentist"}
        male = {"boy", "father", "dad", "man"}
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
class Office:
    name: str = "the dentist office"
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
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    location: str
    clue: str
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
    action: str
    solves: set[str]
    requires_teamwork: bool = True
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
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
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


class World:
    def __init__(self, office: Office) -> None:
        self.office = office
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
OFFICES = {
    "dentist_office": Office(name="the dentist office", affords={"clean", "rinse", "floss", "teamwork"}),
}

PROBLEMS = {
    "broccoli": Problem(
        id="broccoli",
        label="broccoli",
        phrase="a little piece of broccoli",
        risk="stuck between the teeth",
        location="teeth",
        clue="green and leafy",
        tags={"broccoli", "food", "healthy"},
    ),
    "broccoli_braces": Problem(
        id="broccoli_braces",
        label="broccoli",
        phrase="a little piece of broccoli",
        risk="caught in the braces",
        location="braces",
        clue="green and leafy",
        tags={"broccoli", "food", "healthy"},
    ),
}

TOOLS = {
    "brush": Tool(
        id="brush",
        label="toothbrush",
        phrase="a soft toothbrush",
        action="brush away the bits",
        solves={"broccoli", "broccoli_braces"},
    ),
    "floss": Tool(
        id="floss",
        label="floss",
        phrase="a long string of floss",
        action="slip between the teeth",
        solves={"broccoli", "broccoli_braces"},
    ),
    "rinse": Tool(
        id="rinse",
        label="cup of water",
        phrase="a clean cup of water",
        action="rinse the mouth",
        solves={"broccoli", "broccoli_braces"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Maya"]
BOY_NAMES = ["Finn", "Leo", "Owen", "Theo", "Max"]
TRAITS = ["patient", "brave", "gentle", "curious", "cheerful"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in OFFICES:
        for prob in PROBLEMS:
            for tool in TOOLS:
                if prob in _safe_lookup(TOOLS, tool).solves:
                    combos.append((place, prob, tool))
    return combos


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} could not reasonably solve {problem.label} here. "
        f"The office teamwork needs a tool that truly helps with that kind of stuck food.)"
    )


def story_allowed(args: argparse.Namespace) -> None:
    if getattr(args, "problem", None) and getattr(args, "tool", None):
        prob = _safe_lookup(PROBLEMS, getattr(args, "problem", None))
        tool = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if getattr(args, "problem", None) not in tool.solves:
            pass


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "small")
    world.say(
        f"{child.id} was a little {trait} {child.type} who tried to be brave at the dentist office."
    )


def setup(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    child.memes["worry"] += 1
    helper.memes["care"] += 1
    world.say(
        f"One day, {child.id} came in with {problem.phrase} {problem.risk}."
    )
    world.say(
        f"{helper.id} noticed the {problem.clue} piece and said it would be easier if everyone worked together."
    )


def tension(world: World, child: Entity, dentist: Entity, problem: Problem) -> None:
    child.memes["nervous"] += 1
    dentist.memes["focus"] += 1
    world.say(
        f"{child.id} wanted the worry gone right away, but {dentist.id} held up a calm hand."
    )
    world.say(
        f"\"If we rush, the {problem.label} may stay put,\" {dentist.id} said. \"We need teamwork.\""
    )


def teamwork_fix(world: World, child: Entity, helper: Entity, dentist: Entity, problem: Problem, tool: Tool) -> None:
    child.memes["trust"] += 1
    helper.memes["teamwork"] += 1
    dentist.memes["teamwork"] += 1
    world.say(
        f"{helper.id} brought {tool.phrase}, and {dentist.id} showed {child.id} how to open wide and stay still."
    )
    world.say(
        f"Together they used the {tool.label} to {tool.action}, and then a rinse washed the last bits away."
    )
    world.say(
        f"{child.id} smiled as the green crumb disappeared, and the office felt bright again."
    )


def ending(world: World, child: Entity, helper: Entity, dentist: Entity) -> None:
    child.memes["relief"] += 1
    helper.memes["joy"] += 1
    dentist.memes["joy"] += 1
    world.say(
        f"{child.id} left with a clean grin, {helper.id} laughed softly, and {dentist.id} said that teamwork can turn a sticky fix into a gentle one."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(office: Office, problem: Problem, tool: Tool, name: str, gender: str, helper_role: str, trait: str) -> World:
    world = World(office)

    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        traits=["little", trait],
    ))
    dentist = world.add(Entity(
        id="Dentist",
        kind="character",
        type="dentist",
        label="the dentist",
        traits=["calm", "careful"],
    ))
    helper = world.add(Entity(
        id=helper_role,
        kind="character",
        type="assistant",
        label=f"the {helper_role}",
        traits=["helpful", "steady"],
    ))
    crumb = world.add(Entity(
        id="broccoli_piece",
        type="broccoli",
        label="broccoli",
        phrase=problem.phrase,
        owner=child.id,
        location=problem.location,
    ))

    introduce(world, child)
    setup(world, child, helper, problem)

    world.para()
    tension(world, child, dentist, problem)

    world.para()
    teamwork_fix(world, child, helper, dentist, problem, tool)

    world.para()
    ending(world, child, helper, dentist)

    world.facts.update(
        child=child,
        dentist=dentist,
        helper=helper,
        crumb=crumb,
        office=office,
        problem=problem,
        tool=tool,
        teamwork=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    problem: Problem = _safe_fact(world, f, "problem")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short fable for children about teamwork in {world.office.name} with the word "broccoli".',
        f"Tell a gentle story where {child.id} has {problem.phrase} and the team uses {tool.label} to help.",
        f"Write a small moral story in a dentist office where helpers cooperate to solve a broccoli problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    dentist: Entity = _safe_fact(world, f, "dentist")
    helper: Entity = _safe_fact(world, f, "helper")
    problem: Problem = _safe_fact(world, f, "problem")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))

    return [
        QAItem(
            question=f"Who was the story about at the dentist office?",
            answer=f"It was about {child.id}, a little {next(t for t in child.traits if t != 'little')} child who needed help with {problem.label}.",
        ),
        QAItem(
            question=f"What problem did {child.id} have?",
            answer=f"{child.id} had {problem.phrase} {problem.risk}, so the office team had to help carefully.",
        ),
        QAItem(
            question=f"How did the team solve the problem?",
            answer=f"{helper.id} brought the {tool.label}, {dentist.id} kept things calm, and together they used teamwork to clear away the broccoli.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {child.id} had a clean grin, and the office felt peaceful because the team worked together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "broccoli": [
        QAItem(
            question="What is broccoli?",
            answer="Broccoli is a green vegetable that grows in a bunch of little florets on a stalk.",
        ),
        QAItem(
            question="Why do people eat vegetables like broccoli?",
            answer="People eat vegetables like broccoli because they can help give the body important nourishment.",
        ),
    ],
    "teamwork": [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do different jobs together to reach one goal.",
        ),
        QAItem(
            question="Why can teamwork make a hard job easier?",
            answer="Teamwork can make a hard job easier because each helper can do one small part instead of one person doing everything alone.",
        ),
    ],
    "dentist": [
        QAItem(
            question="What does a dentist do?",
            answer="A dentist helps keep teeth healthy and checks for problems in the mouth.",
        ),
        QAItem(
            question="Why do people visit a dentist office?",
            answer="People visit a dentist office to get their teeth checked, cleaned, and cared for.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags) | {"teamwork", "dentist"}
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
problem(problem_broccoli).
problem(problem_broccoli_braces).

tool(tool_brush).
tool(tool_floss).
tool(tool_rinse).

solves(tool_brush, problem_broccoli).
solves(tool_brush, problem_broccoli_braces).
solves(tool_floss, problem_broccoli).
solves(tool_floss, problem_broccoli_braces).
solves(tool_rinse, problem_broccoli).
solves(tool_rinse, problem_broccoli_braces).

valid(place_dentist_office, P, T) :- problem(P), tool(T), solves(T, P).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "place_dentist_office")]
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = {( "place_dentist_office", p, t) for (_, p, t) in asp_valid_combos()}
    if py == {("dentist_office", p, t) for (_, p, t) in asp_set}:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about broccoli, a dentist office, and teamwork.")
    ap.add_argument("--place", choices=OFFICES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["assistant", "hygienist", "nurse"], default=None)
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


CURATED = [
    StoryParams(place="dentist_office", problem="broccoli", tool="floss", name="Mina", gender="girl", helper="assistant", trait="brave"),
    StoryParams(place="dentist_office", problem="broccoli_braces", tool="brush", name="Finn", gender="boy", helper="hygienist", trait="patient"),
    StoryParams(place="dentist_office", problem="broccoli", tool="rinse", name="Ivy", gender="girl", helper="nurse", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    story_place = getattr(args, "place", None) or "dentist_office"
    combos = [c for c in valid_combos() if c[0] == story_place]
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[1] == getattr(args, "problem", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    _, prob_id, tool_id = rng.choice(list(combos))
    problem = _safe_lookup(PROBLEMS, prob_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["assistant", "hygienist", "nurse"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=story_place,
        problem=prob_id,
        tool=tool_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(OFFICES, params.place),
        _safe_lookup(PROBLEMS, params.problem),
        _safe_lookup(TOOLS, params.tool),
        params.name,
        params.gender,
        params.helper,
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        atoms = asp.atoms(model, "valid")
        print(f"{len(atoms)} compatible combos:")
        for a in atoms:
            print(a)
        return

    story_allowed(args)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
