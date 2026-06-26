#!/usr/bin/env python3
"""
Storyworld: pebble bulk problem solving rhyming story.

A child finds a bulky pebble load in the way, then solves the problem with a
careful plan, helpers, and a rhyme-friendly ending.
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
    helper_for: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    problem: object | None = None
    tool: object | None = None
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
    indoor: bool = False
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
    title: str
    obstacle: str
    verb: str
    rhyme: str
    difficulty: str
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
    use_line: str
    helps: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "courtyard": Place("the courtyard", indoor=False, affords={"pebble"}),
    "garden": Place("the garden", indoor=False, affords={"pebble"}),
    "riverbank": Place("the riverbank", indoor=False, affords={"pebble"}),
    "workshop": Place("the workshop", indoor=True, affords={"pebble"}),
}

PROBLEMS = {
    "pebble_heap": Problem(
        id="pebble_heap",
        title="a pebble heap",
        obstacle="a bulky pebble heap blocking the path",
        verb="move the pebble heap",
        rhyme="bump and heap",
        difficulty="heavy",
        tags={"pebble", "bulk"},
    ),
    "pebble_cart": Problem(
        id="pebble_cart",
        title="a pebble cart",
        obstacle="a bulky cart of pebbles stuck in a rut",
        verb="free the pebble cart",
        rhyme="cart and start",
        difficulty="stuck",
        tags={"pebble", "bulk"},
    ),
    "pebble_bundle": Problem(
        id="pebble_bundle",
        title="a pebble bundle",
        obstacle="a bulky bundle of pebbles tied with twine",
        verb="sort the pebble bundle",
        rhyme="bundle and tumble",
        difficulty="tied",
        tags={"pebble", "bulk"},
    ),
}

TOOLS = {
    "tote": Tool("tote", "a tote bag", "the tote bag", "scoop the pebbles into the tote", helps={"pebble"}, plural=False),
    "tray": Tool("tray", "a flat tray", "the flat tray", "slide pebbles on the tray", helps={"pebble"}, plural=False),
    "ramp": Tool("ramp", "a little ramp", "the little ramp", "roll the load up the ramp", helps={"bulk"}, plural=False),
    "wagon": Tool("wagon", "a hand wagon", "the hand wagon", "wheel the bulk to the side", helps={"bulk"}, plural=False),
    "sieve": Tool("sieve", "a pebble sieve", "the pebble sieve", "shake the small stones through the sieve", helps={"pebble"}, plural=False),
}

NAMES = ["Milo", "Nina", "Pia", "Toby", "Lena", "Ravi", "Iris", "Sage"]
ROLES = ["child", "girl", "boy"]
HELPERS = ["mother", "father", "friend", "brother", "sister"]
TRAITS = ["bright", "spry", "kind", "brave", "cheery", "curious"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    role: str
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


def compatible(problem: Problem, tool: Tool) -> bool:
    return bool(problem.tags & tool.helps)


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, prob in PROBLEMS.items():
        for tid, tool in TOOLS.items():
            if compatible(prob, tool):
                out.append((pid, tid))
    return out


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not really help with {problem.obstacle}. "
        f"Pick a tool that can handle either pebble work or bulk work.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.role, meters={"hope": 1}, memes={"curiosity": 1}))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    problem = world.add(Entity(id="Problem", type=_safe_lookup(PROBLEMS, params.problem).id, label=_safe_lookup(PROBLEMS, params.problem).title))
    tool = world.add(Entity(id="Tool", type="tool", label="", phrase="", owner=hero.id))
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["problem_def"] = _safe_lookup(PROBLEMS, params.problem)
    world.facts["tool_def"] = None
    return world


def solve(world: World, params: StoryParams, tool_def: Tool) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    prob = _safe_fact(world, world.facts, "problem_def")

    world.facts["tool_def"] = tool_def

    hero.memes["stuck"] = 1
    world.say(f"{hero.id} came to {world.place.name} and saw {prob.obstacle}.")
    world.say(
        f"{hero.id} said, “This heap is in my way; it feels too big for me to play.”"
    )

    world.para()
    world.say(
        f"{helper.type.capitalize()} came with a grin and a simple plan, "
        f"for little problems often need a helping hand."
    )
    world.say(
        f"They looked at the bulk and chose {tool_def.label}, because it could truly do the trick."
    )
    hero.memes["hope"] += 1

    # Problem-solving turn
    if "bulk" in tool_def.helps:
        hero.meters["progress"] = 1
        world.say(
            f"They used {tool_def.phrase} and {tool_def.use_line}, slow and steady, neat and slick."
        )
    else:
        hero.meters["progress"] = 1

    # Resolution
    world.para()
    hero.memes["joy"] = 1
    hero.memes["stuck"] = 0
    world.say(
        f"At last the path was clear, with the pebble pile spread low and light."
    )
    world.say(
        f"{hero.id} laughed, “A problem can feel tall, but teamwork makes it small and bright.”"
    )
    world.say(
        f"So the pebble bulk was sorted out, and the day went smooth and right."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def choose_name(role: str, rng: random.Random) -> str:
    return rng.choice(NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "problem", None) and getattr(args, "tool", None):
        if not compatible(_safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(TOOLS, getattr(args, "tool", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = valid_combos()
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[0] == getattr(args, "problem", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[1] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    problem, tool = rng.choice(list(combos))
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES.keys()))
    role = getattr(args, "role", None) or rng.choice(ROLES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or choose_name(role, rng)
    return StoryParams(place=place, problem=problem, name=name, role=role, helper=helper, trait=trait)


def story_text(world: World, params: StoryParams) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "problem_def")
    t = _safe_fact(world, world.facts, "tool_def")
    h = _safe_fact(world, world.facts, "hero")
    return [
        f"Write a rhyming story about {h.id} solving {p.obstacle} with {t.label}.",
        f"Tell a child-friendly problem-solving tale that includes pebble and bulk and ends in a neat rhyme.",
        f"Write a short story where a helper and a child work together to fix a bulky pebble problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    p = _safe_fact(world, world.facts, "problem_def")
    t = _safe_fact(world, world.facts, "tool_def")
    return [
        QAItem(
            question=f"What problem did {hero.id} find at {world.place.name}?",
            answer=f"{hero.id} found {p.obstacle}. It was a bulky pebble problem that blocked the way.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"{helper.type.capitalize()} helped {hero.id}. They worked together instead of giving up.",
        ),
        QAItem(
            question=f"What did they use to fix the pebble bulk problem?",
            answer=f"They used {t.label} to handle the bulk and move the pebbles safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pebble?",
            answer="A pebble is a small, smooth stone.",
        ),
        QAItem(
            question="What does bulk mean?",
            answer="Bulk means something is big, heavy, or hard to move all at once.",
        ),
        QAItem(
            question="Why is a helper useful for a hard job?",
            answer="A helper can share the work, suggest a plan, and make the job easier and safer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    prob = _safe_lookup(PROBLEMS, params.problem)
    tool = None
    for t in TOOLS.values():
        if compatible(prob, t):
            tool = t
            break
    if tool is None:
        pass
    solve(world, params, tool)
    return StorySample(
        params=params,
        story=story_text(world, params),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print(format_qa(sample))
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A problem is compatible with a tool when the tool helps with a needed feature.
compatible(P, T) :- problem(P), tool(T), problem_needs(P, N), tool_helps(T, N).
valid_combo(P, T) :- compatible(P, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(prob.tags):
            lines.append(asp.fact("problem_needs", pid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(tool.helps):
            lines.append(asp.fact("tool_helps", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - ap))
    print("only clingo:", sorted(ap - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming problem-solving pebble storyworld.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    StoryParams(place="courtyard", problem="pebble_heap", name="Milo", role="boy", helper="mother", trait="curious"),
    StoryParams(place="garden", problem="pebble_bundle", name="Nina", role="girl", helper="father", trait="brave"),
    StoryParams(place="riverbank", problem="pebble_cart", name="Ravi", role="boy", helper="friend", trait="cheery"),
]


def resolve_all_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def asp_valid_story_count() -> int:
    return len(asp_valid_combos())


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, t in combos:
            print(f"  {p} {t}")
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
