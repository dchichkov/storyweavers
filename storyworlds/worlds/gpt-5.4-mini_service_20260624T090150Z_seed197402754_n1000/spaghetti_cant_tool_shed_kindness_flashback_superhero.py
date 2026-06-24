#!/usr/bin/env python3
"""
A small superhero storyworld set in a tool shed.

Seed inspiration:
- spaghetti
- cant
- Kindness
- Flashback
- Superhero Story
- tool shed

The world model tracks a hero, a helper, a simple problem, a remembered lesson,
and a kindness-based resolution. The story stays concrete and state-driven:
something breaks or goes missing in the tool shed, the hero wants to help,
a flashback reminds them of a kinder way, and the ending proves the change.
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
# Domain registries
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

@dataclass(frozen=True)
class Location:
    id: str
    label: str
    affordances: set[str] = field(default_factory=set)
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


@dataclass(frozen=True)
class Problem:
    id: str
    label: str
    verb: str
    consequence: str
    need: str
    keyword: str
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


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    used_for: set[str] = field(default_factory=set)
    fix: str = ""
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


@dataclass(frozen=True)
class HeroKind:
    id: str
    label: str
    pronoun: str
    possessive: str
    subject: str
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


LOCATIONS = {
    "tool_shed": Location(
        id="tool_shed",
        label="the tool shed",
        affordances={"spilled", "stuck", "shelving", "help"},
    )
}

PROBLEMS = {
    "spaghetti": Problem(
        id="spaghetti",
        label="spaghetti noodles",
        verb="spill",
        consequence="turned the floor slippery and twisty",
        need="clean up the mess before anyone slipped",
        keyword="spaghetti",
        tags={"spaghetti", "mess", "food"},
    ),
    "cant": Problem(
        id="cant",
        label="a stuck latch",
        verb="won't open",
        consequence="kept the shed door from opening",
        need="find a gentle way to open it",
        keyword="cant",
        tags={"cant", "stuck", "door"},
    ),
}

TOOLS = {
    "rag": Tool(
        id="rag",
        label="a clean rag",
        used_for={"spaghetti"},
        fix="wiped up the slippery noodles",
    ),
    "oil": Tool(
        id="oil",
        label="a little oil can",
        used_for={"cant"},
        fix="loosened the stuck latch",
    ),
    "bucket": Tool(
        id="bucket",
        label="a small bucket",
        used_for={"spaghetti"},
        fix="held the messy noodles until the floor was clean",
    ),
}

HERO_KINDS = {
    "girl": HeroKind(id="girl", label="girl", pronoun="she", possessive="her", subject="she"),
    "boy": HeroKind(id="boy", label="boy", pronoun="he", possessive="his", subject="he"),
}

HERO_NAMES = {
    "girl": ["Mina", "Tess", "Ruby", "Nora", "Lia", "Zoe"],
    "boy": ["Max", "Jude", "Kai", "Leo", "Finn", "Owen"],
}

HELPER_NAMES = ["Aunt June", "Uncle Sam", "Ms. Piper", "Mr. Clay", "Grandma Bea", "Grandpa Walt"]

TRAITS = ["brave", "kind", "quick", "gentle", "curious"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = ""
    owner: Optional[str] = None
    helper_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    carried: bool = False
    broken: bool = False
    fixed: bool = False

    helper: object | None = None
    hero: object | None = None
    problem: object | None = None
    tool: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)
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


class World:
    def __init__(self, location: Location):
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        other = World(self.location)
        other.entities = copy.deepcopy(self.entities)
        other.facts = dict(self.facts)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    location: str
    problem: str
    tool: str
    hero_name: str
    hero_gender: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
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


def valid_combo(location: Location, problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.used_for and problem.id in location.affordances


def explain_rejection(location: Location, problem: Problem, tool: Tool) -> str:
    if problem.id not in location.affordances:
        return f"(No story: {problem.label} doesn't fit this place's action, so it can't plausibly happen in {location.label}.)"
    if problem.id not in tool.used_for:
        return f"(No story: {tool.label} does not really solve {problem.label}, so the hero would not have a meaningful fix.)"
    return "(No story: the chosen setup is not reasonable.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
loc(tool_shed).
problem(spaghetti).
problem(cant).
tool(rag).
tool(oil).
tool(bucket).

affords(tool_shed, spaghetti).
affords(tool_shed, cant).

used_for(rag, spaghetti).
used_for(oil, cant).
used_for(bucket, spaghetti).

valid(L, P, T) :- affords(L, P), used_for(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("loc", "tool_shed"))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for lid, loc in LOCATIONS.items():
        for p in sorted(loc.affordances):
            lines.append(asp.fact("affords", lid, p))
    for tid, tool in TOOLS.items():
        for p in sorted(tool.used_for):
            lines.append(asp.fact("used_for", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, problem: Problem, tool: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.get(hero.id).memes["worry"] = sim.get(hero.id).meme("worry") + 1
    if problem.id == "spaghetti":
        sim.get(problem.id).meters["mess"] = 1
    if problem.id == "cant":
        sim.get(problem.id).broken = True
    if tool.id in ("rag", "bucket") and problem.id == "spaghetti":
        soiled = True
    else:
        soiled = False
    if tool.id == "oil" and problem.id == "cant":
        soiled = False
    return {"soiled": soiled}


def build_world(params: StoryParams) -> World:
    loc = _safe_lookup(LOCATIONS, params.location)
    prob = _safe_lookup(PROBLEMS, params.problem)
    tool_cfg = _safe_lookup(TOOLS, params.tool)
    world = World(loc)

    hero_kind = _safe_lookup(HERO_KINDS, params.hero_gender)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=hero_kind.id,
        label=params.hero_name,
        meters={},
        memes={"kindness": 0.0, "courage": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="helper",
        label=params.helper_name,
        meters={},
        memes={"kindness": 1.0, "patience": 1.0},
    ))
    problem = world.add(Entity(
        id=prob.id,
        kind="problem",
        label=prob.label,
        type=prob.id,
        meters={"mess": 1.0} if prob.id == "spaghetti" else {},
        broken=(prob.id == "cant"),
    ))
    tool = world.add(Entity(
        id=tool_cfg.id,
        kind="tool",
        label=tool_cfg.label,
        type=tool_cfg.id,
        owner=helper.id,
        carried=True,
    ))

    # Act 1: setup
    world.say(f"{hero.label} was a {params.trait} little superhero who liked to help in {loc.label}.")
    world.say(f"{hero.label} loved the shiny mask and cape, but {hero.pronoun if hasattr(hero, 'pronoun') else 'they'} loved kindness even more.")
    world.say(f"One day, {prob.label} made trouble in the shed, and {hero.label} wanted to fix it fast.")
    world.para()

    # Act 2: problem, flashback, and worry
    world.say(f"In the tool shed, {prob.label} could {prob.verb}, which meant the job was not simple.")
    world.say(f"{hero.label} picked up {tool.label}, but then {hero.label} paused.")
    world.say(f"A flashback came back: once, {helper.label} had said, 'Kindness helps hands work better than hurry.'")
    hero.memes["flashback"] = 1.0
    hero.memes["worry"] += 1
    world.say(f"That memory made {hero.label} slow down and think instead of rushing.")
    world.para()

    # Act 3: resolution based on the tool
    if problem.id == "spaghetti":
        hero.memes["kindness"] += 1
        hero.meters["helped"] = 1.0
        problem.meters["mess"] = 0.0
        tool.fixed = True
        world.say(f"{hero.label} used {tool.label} to {_safe_lookup(TOOLS, tool.id).fix}.")
        world.say(f"Then {helper.label} smiled because the floor was safe again.")
    else:
        hero.memes["kindness"] += 1
        hero.meters["helped"] = 1.0
        problem.broken = False
        problem.fixed = True
        world.say(f"{hero.label} used {tool.label} to {_safe_lookup(TOOLS, tool.id).fix}.")
        world.say(f"Then the stuck latch opened with a soft click, and the shed door swung wide.")
    hero.memes["joy"] += 1
    world.say(f"At the end, {hero.label} stood in {loc.label}, proud that the hero work had been gentle.")
    world.facts = {
        "hero": hero,
        "helper": helper,
        "problem": problem,
        "tool": tool,
        "location": loc,
        "trait": params.trait,
        "hero_gender": params.hero_gender,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prob = _safe_fact(world, f, "problem")
    loc = _safe_fact(world, f, "location")
    return [
        f'Write a short superhero story for a young child set in {loc.label} that includes "{prob.label}" and kindness.',
        f"Tell a story where {hero.label} helps in {loc.label}, remembers a flashback, and chooses a gentle fix with {helper.label}.",
        f"Write a simple hero story with a tool shed, a problem, and a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prob = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    loc = _safe_fact(world, f, "location")
    trait = _safe_fact(world, f, "trait")
    qs = [
        QAItem(
            question=f"Who is the superhero story about in {loc.label}?",
            answer=f"It is about {hero.label}, a {trait} little superhero who wants to help in {loc.label}.",
        ),
        QAItem(
            question=f"What problem was making trouble in {loc.label}?",
            answer=f"{prob.label} was making trouble in {loc.label}. That problem needed a gentle fix.",
        ),
        QAItem(
            question=f"What tool did {hero.label} use to help?",
            answer=f"{hero.label} used {tool.label} with care, and that helped solve the problem.",
        ),
        QAItem(
            question=f"Why did {hero.label} slow down before helping?",
            answer=f"{hero.label} remembered a flashback about kindness from {helper.label}, so {hero.label} chose to be gentle instead of rushing.",
        ),
        QAItem(
            question=f"How did the story end in the tool shed?",
            answer=f"The story ended with {loc.label} safe and calm, and {hero.label} feeling proud of a kind choice.",
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, caring, and helpful to other people.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="What is spaghetti?",
            answer="Spaghetti is a long, stringy kind of pasta that people often eat with sauce.",
        ),
        QAItem(
            question="What is a tool shed?",
            answer="A tool shed is a small building where people keep tools and supplies for fixing things.",
        ),
    ]


# ---------------------------------------------------------------------------
# Parsing / generation / output
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld set in a tool shed.")
    ap.add_argument("--location", choices=LOCATIONS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=HERO_KINDS.keys())
    ap.add_argument("--helper-name")
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
    location = getattr(args, "location", None) or "tool_shed"
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS.keys()))
    tool = getattr(args, "tool", None) or rng.choice([t.id for t in TOOLS.values() if t.id in {"rag", "oil", "bucket"}])
    loc = _safe_lookup(LOCATIONS, location)
    prob = _safe_lookup(PROBLEMS, problem)
    tl = _safe_lookup(TOOLS, tool)
    if not valid_combo(loc, prob, tl):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(list(HERO_KINDS.keys()))
    hero_name = getattr(args, "hero_name", None) or rng.choice(_safe_lookup(HERO_NAMES, gender))
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        location=location,
        problem=problem,
        tool=tool,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.kind == "tool":
            bits.append("carried=True" if e.carried else "carried=False")
        if e.kind == "problem":
            bits.append(f"broken={e.broken}")
            bits.append(f"fixed={e.fixed}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(location="tool_shed", problem="spaghetti", tool="rag", hero_name="Mina", hero_gender="girl", helper_name="Aunt June", trait="kind"),
    StoryParams(location="tool_shed", problem="cant", tool="oil", hero_name="Max", hero_gender="boy", helper_name="Mr. Clay", trait="brave"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (location, problem, tool) combos:")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
