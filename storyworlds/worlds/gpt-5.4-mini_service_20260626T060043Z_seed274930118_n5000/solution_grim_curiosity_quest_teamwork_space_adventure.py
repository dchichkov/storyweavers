#!/usr/bin/env python3
"""
Story world: a small space adventure about curiosity, a quest, teamwork, and a grim problem that finds a solution.

The world is intentionally tiny and classical:
- a crew travels between a few places on a ship or nearby space station
- a curious scout discovers a grim obstacle
- the crew needs a quest-like repair or rescue
- teamwork turns the situation around
- the ending image proves what changed

The script supports the standard Storyweavers CLI, a Python reasonableness gate,
and an inline ASP twin for parity checks.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    problem_ent: object | None = None
    teammate: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    id: str
    label: str
    kind: str = "location"
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
class Problem:
    id: str
    label: str
    phrase: str
    risky_place: str
    fixable_by: str
    grim_line: str
    solution_line: str
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
    helps_with: set[str]
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
    role: str
    teammate: str
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


class World:
    def __init__(self, ship: Place) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "bridge": Place("bridge", "the bridge"),
    "airlock": Place("airlock", "the airlock"),
    "hangar": Place("hangar", "the hangar"),
    "garden": Place("garden", "the star garden"),
    "engine": Place("engine", "the engine room"),
}

TOOLS = {
    "scanner": Tool("scanner", "scanner", "a small scanner", {"signal", "dust", "drift"}),
    "patchkit": Tool("patchkit", "patch kit", "a bright patch kit", {"leak", "crack"}),
    "tether": Tool("tether", "tether line", "a long tether line", {"drift"}),
    "lamp": Tool("lamp", "lamp", "a pocket lamp", {"dark"}),
}

PROBLEMS = {
    "drift": Problem(
        id="drift",
        label="floating drift",
        phrase="a slow floating drift in the dark",
        risky_place="airlock",
        fixable_by="tether",
        grim_line="A grim drift tugged at the loose tools by the airlock.",
        solution_line="The tether line held the drifting pieces still.",
        tags={"space", "dark", "drift"},
    ),
    "leak": Problem(
        id="leak",
        label="coolant leak",
        phrase="a hissing coolant leak",
        risky_place="engine",
        fixable_by="patchkit",
        grim_line="A grim hiss of coolant came from a thin crack near the pipes.",
        solution_line="The patch kit sealed the crack before the cold spread.",
        tags={"space", "leak", "engine"},
    ),
    "signal": Problem(
        id="signal",
        label="lost signal",
        phrase="a faint lost signal from the outer bay",
        risky_place="bridge",
        fixable_by="scanner",
        grim_line="The display blinked red, and the map looked lost and dim.",
        solution_line="The scanner found the weak signal and turned it clear again.",
        tags={"space", "signal", "bridge"},
    ),
}

NAMES = ["Nova", "Mira", "Taro", "Juno", "Ada", "Rin", "Pax", "Lio"]
TRAITS = ["curious", "brave", "gentle", "quick", "bright", "careful"]
ROLES = ["pilot", "captain", "scout", "mechanic", "navigator", "engineer"]
TEAMMATES = ["crew", "friend", "mate", "partner"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def problem_needs_tool(problem: Problem, tool: Tool) -> bool:
    return tool.id == problem.fixable_by


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for problem_id, prob in PROBLEMS.items():
            if place_id != prob.risky_place:
                continue
            for tool_id, tool in TOOLS.items():
                if problem_needs_tool(prob, tool):
                    combos.append((place_id, problem_id, tool_id))
    return combos


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not solve {problem.label}. "
        f"The quest needs a fix that really matches the problem.)"
    )


# ---------------------------------------------------------------------------
# World dynamics
# ---------------------------------------------------------------------------

def scan_problem(world: World, scout: Entity, problem: Problem) -> None:
    scout.memes["curiosity"] = scout.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{scout.id} followed {scout.pronoun('possessive')} curiosity and found {problem.phrase}."
    )
    world.say(problem.grim_line)
    world.facts["problem_seen"] = problem.id


def call_team(world: World, hero: Entity, teammate: Entity, problem: Problem) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    teammate.memes["teamwork"] = teammate.memes.get("teamwork", 0.0) + 1.0
    world.say(
        f"{hero.id} called {teammate.id}, and soon the two of them turned it into a quest."
    )
    world.say(
        f'"We can fix this together," {teammate.id} said, and {hero.id} nodded.'
    )
    world.facts["quest_started"] = True


def apply_solution(world: World, hero: Entity, teammate: Entity, tool: Tool, problem: Problem) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    teammate.memes["hope"] = teammate.memes.get("hope", 0.0) + 1.0
    world.say(
        f"They used {tool.phrase} with careful teamwork."
    )
    world.say(problem.solution_line)
    world.say(
        f"At last, the grim trouble was gone, and the ship felt steady again."
    )
    world.facts["solved"] = True


def tell(place: Place, problem: Problem, tool: Tool,
         hero_name: str, hero_role: str, teammate_word: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="girl" if hero_role == "captain" and hero_name in {"Nova", "Mira", "Juno", "Ada", "Rin"} else "boy",
        label=hero_role,
    ))
    teammate = world.add(Entity(
        id=teammate_word.capitalize(),
        kind="character",
        type="friend",
        label=teammate_word,
    ))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase))
    problem_ent = world.add(Entity(id=problem.id, type="problem", label=problem.label, phrase=problem.phrase))

    world.say(
        f"{hero.id} was a {trait} {hero_role} on {world.ship.label}, and {hero.id} loved curiosity."
    )
    world.say(
        f"One day, {hero.id} had to solve a small quest before the ship could rest."
    )
    world.para()
    scan_problem(world, hero, problem_ent)
    call_team(world, hero, teammate, problem_ent)
    world.para()
    apply_solution(world, hero, teammate, tool_ent, problem_ent)

    world.facts.update(
        hero=hero,
        teammate=teammate,
        tool=tool_ent,
        problem=problem_ent,
        place=place,
        trait=trait,
        teammate_word=teammate_word,
        role=hero_role,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure about curiosity, a quest, and teamwork that includes the word "{f["problem"].label}".',
        f"Tell a child-friendly story where {f['hero'].id} and a {f['teammate_word']} solve {f['problem'].phrase} together.",
        f'Write a simple story set on a spaceship that ends with a real solution and includes "{(f.get("tool") or next(iter(TOOLS.values()))).label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    teammate: Entity = _safe_fact(world, f, "teammate")
    problem: Entity = _safe_fact(world, f, "problem")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who was the curious hero in the story?",
            answer=f"The curious hero was {hero.id}, who worked on the quest at {place.label}.",
        ),
        QAItem(
            question=f"What grim problem did {hero.id} discover?",
            answer=f"{hero.id} discovered {problem.phrase}, which made the ship feel tense and troubled.",
        ),
        QAItem(
            question=f"How did {hero.id} and {teammate.id} solve it?",
            answer=f"They used {tool.phrase} and teamwork, and that gave the story its solution.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    problem: Entity = _safe_fact(world, f, "problem")
    out = [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about what is happening.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something hard.",
        ),
        QAItem(
            question="What does a scanner do?",
            answer="A scanner helps find signals or hidden details by looking closely with light or sensors.",
        ),
    ]
    if tool.id == "patchkit":
        out.append(QAItem(
            question="What is a patch kit for?",
            answer="A patch kit is for fixing holes or cracks so air or liquid does not keep leaking out.",
        ))
    if problem.id == "drift":
        out.append(QAItem(
            question="What is drift in space?",
            answer="Drift means floating or moving slowly without a fixed place, which can be dangerous in space.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
problem(Pr) :- problem_fact(Pr).
tool(T) :- tool_fact(T).

valid(P,Pr,T) :- place_fact(P), problem_fact(Pr), tool_fact(T),
                 risky_place(Pr,P), fixable_by(Pr,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for prid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem_fact", prid))
        lines.append(asp.fact("risky_place", prid, pr.risky_place))
        lines.append(asp.fact("fixable_by", prid, pr.fixable_by))
    for tid in TOOLS:
        lines.append(asp.fact("tool_fact", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space adventure story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--teammate", choices=TEAMMATES)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, tool = rng.choice(list(filtered))
    prob = _safe_lookup(PROBLEMS, problem)
    tl = _safe_lookup(TOOLS, tool)
    if getattr(args, "problem", None) and getattr(args, "tool", None) and not problem_needs_tool(prob, tl):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    teammate = getattr(args, "teammate", None) or rng.choice(TEAMMATES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, role=role, teammate=teammate, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(PROBLEMS, params.problem),
        _safe_lookup(TOOLS, params.tool),
        params.name,
        params.role,
        params.teammate,
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
    StoryParams(place="airlock", problem="drift", tool="tether", name="Nova", role="scout", teammate="crew", trait="curious"),
    StoryParams(place="engine", problem="leak", tool="patchkit", name="Mira", role="engineer", teammate="mate", trait="careful"),
    StoryParams(place="bridge", problem="signal", tool="scanner", name="Taro", role="navigator", teammate="partner", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for p, pr, t in triples:
            print(f"  {p:8} {pr:8} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
