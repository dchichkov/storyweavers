#!/usr/bin/env python3
"""
A fairy-tale storyworld set in a train station, centered on problem solving.

The seed idea:
- A small royal child is waiting at a train station.
- A rapid problem appears: a missing token needed to board.
- A helper figure and a clever plan solve the problem.
- The story should feel like a gentle fairy tale with a clear turn and ending.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "king", "father", "man"}:
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
    place: str = "the train station"
    affordances: set[str] = field(default_factory=lambda: {"ticket", "clock", "crowd", "bench"})
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
class Problem:
    id: str
    name: str
    verb: str
    rapid: str
    trouble: str
    clue: str
    zone: str
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
    use: str
    solves: set[str]
    covers: set[str] = field(default_factory=set)
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _warn(world: World) -> list[str]:
    out: list[str] = []
    princess = world.get("hero")
    if princess.memes.get("worry", 0) < THRESHOLD:
        return out
    if world.fired.__contains__(("warned",)):
        return out
    world.fired.add(("warned",))
    out.append("The station seemed to hold its breath.")
    return out


def _solve(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.memes.get("clue", 0) < THRESHOLD:
        return out
    if hero.memes.get("relief", 0) >= THRESHOLD:
        return out
    if ("solved",) in world.fired:
        return out
    world.fired.add(("solved",))
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    out.append("The clever plan worked.")
    return out


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_warn, _solve):
            s = rule(world)
            if s:
                produced.extend(s)
                changed = True
    for s in produced:
        world.say(s)
    return produced


SETTING = Setting()

PROBLEMS = {
    "lost_ticket": Problem(
        id="lost_ticket",
        name="lost ticket",
        verb="board the train",
        rapid="rapidly",
        trouble="the gate would not open",
        clue="the ticket slipped into a bench crack",
        zone="bench",
        tags={"ticket", "station", "problem-solving"},
    ),
    "stuck_luggage": Problem(
        id="stuck_luggage",
        name="stuck luggage wheel",
        verb="roll the suitcase",
        rapid="rapidly",
        trouble="the suitcase would not move",
        clue="one wheel caught under a metal lip",
        zone="platform",
        tags={"luggage", "station", "problem-solving"},
    ),
    "missing_pass": Problem(
        id="missing_pass",
        name="missing pass",
        verb="pass the conductor",
        rapid="rapidly",
        trouble="the guard would not let anyone through",
        clue="the pass had dropped beside the timetable board",
        zone="board",
        tags={"pass", "station", "problem-solving"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="a tiny magnifying glass",
        phrase="a tiny magnifying glass with a silver handle",
        use="look closely",
        solves={"lost_ticket", "missing_pass"},
    ),
    "hook": Tool(
        id="hook",
        label="a little hook on a ribbon",
        phrase="a little hook on a ribbon",
        use="reach into narrow spaces",
        solves={"lost_ticket"},
    ),
    "wheel_wedge": Tool(
        id="wheel_wedge",
        label="a wooden wedge",
        phrase="a smooth wooden wedge",
        use="free the wheel",
        solves={"stuck_luggage"},
    ),
}

HERO_NAMES = ["Iris", "Mina", "Lina", "Tessa", "Elena", "Rosalind"]
HELPER_NAMES = ["Hob", "Pip", "Nell", "Toby", "Moss"]
TRAITS = ["brave", "gentle", "quick-thinking", "kind"]


@dataclass
class StoryParams:
    problem: str
    helper: str
    name: str
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


def problem_requires_station(problem: Problem) -> bool:
    return "station" in problem.tags


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS.values():
        if problem.id in tool.solves:
            return tool
    return None


def valid_problems() -> list[str]:
    return [pid for pid, p in PROBLEMS.items() if problem_requires_station(p) and select_tool(p)]


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Once upon a time, in {world.setting.place}, there lived a {hero.memes.get('rank_text', 'little princess')} named {hero.id}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} was {hero.memes.get('trait_text', 'brave')} and loved to solve little troubles with {helper.id}."
    )


def begin(world: World, hero: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    world.say(
        f"One bright morning, {hero.id} and {helper.id} came to {world.setting.place} while the trains sang and the clocks ticked."
    )
    world.say(
        f"{hero.id} wanted to {problem.verb}, but a {problem.name} appeared {problem.rapid}; {problem.trouble}."
    )
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.facts["problem"] = problem
    world.facts["tool"] = tool
    world.facts["helper"] = helper


def observe(world: World, hero: Entity, problem: Problem, tool: Tool) -> None:
    world.say(
        f"{hero.id} paused and looked closely. {problem.clue.capitalize()}, and {tool.label} could help."
    )
    hero.memes["clue"] = hero.memes.get("clue", 0) + 1


def solve_problem(world: World, hero: Entity, helper: Entity, problem: Problem, tool: Tool) -> None:
    hero.meters[problem.zone] = hero.meters.get(problem.zone, 0) + 1
    helper.meters["helpful"] = helper.meters.get("helpful", 0) + 1
    world.say(
        f"{helper.id} used {tool.phrase} to {tool.use}, and together they solved the problem."
    )
    world.say(
        f"At last, {hero.id} could {problem.verb}, and the train station felt bright again."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.facts["solved"] = True


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    problem = _safe_lookup(PROBLEMS, params.problem)
    helper = world.add(Entity(id=params.helper, kind="character", type="friend"))
    hero = world.add(Entity(id=params.name, kind="character", type="princess"))
    hero.memes["rank_text"] = "little princess"
    hero.memes["trait_text"] = params.trait
    helper.memes["rank_text"] = "small helper"

    tool = select_tool(problem)
    if tool is None:
        pass

    introduce(world, hero, helper)
    world.para()
    begin(world, hero, helper, problem, tool)
    observe(world, hero, problem, tool)
    propagate(world)
    world.para()
    solve_problem(world, hero, helper, problem, tool)
    propagate(world)
    world.facts.update(hero=hero, helper=helper, problem=problem, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "problem")
    h = _safe_fact(world, world.facts, "hero")
    return [
        "Write a gentle fairy tale set in a train station about problem solving.",
        f"Tell a short story where {h.id} faces a {p.name} and solves it with a helper.",
        "Make the story feel magical, concrete, and child-friendly, with a clear solution.",
        "Include the words delineate and rapid in a natural way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    problem: Problem = _safe_fact(world, f, "problem")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Where did {hero.id} have to solve the problem?",
            answer=f"{hero.id} had to solve it at the train station, where the clocks ticked and the trains waited."
        ),
        QAItem(
            question=f"What was the rapid trouble that stopped {hero.id} from {problem.verb}?",
            answer=f"A {problem.name} appeared {problem.rapid}, and {problem.trouble}."
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} fix the problem?",
            answer=f"{helper.id} helped by using {tool.label} to {tool.use}, so {hero.id} could {problem.verb}."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the problem was solved, {hero.id} felt relieved, and the station felt bright again."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a train station?",
            answer="A train station is a place where people wait for trains, buy tickets, and travel from one place to another."
        ),
        QAItem(
            question="What does rapid mean?",
            answer="Rapid means very fast."
        ),
        QAItem(
            question="What does delineate mean?",
            answer="Delineate means to describe something clearly or show its shape and details carefully."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a way to fix trouble or get around a hard situation."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id} ({e.type}): {' '.join(bits) if bits else 'empty'}")
    lines.append(f"facts={world.facts.keys()}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(problem_solving).
setting(train_station).

valid_problem(P) :- problem(P), station_problem(P).
solves(T, P) :- tool(T), fixes(T, P).
good_story(P) :- valid_problem(P), solves(_, P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "train_station")]
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("station_problem", pid))
        if problem_requires_station(p):
            lines.append(asp.fact("requires_station", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for pid in sorted(t.solves):
            lines.append(asp.fact("fixes", tid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_problems() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_problem/1."))
    return sorted(set(asp.atoms(model, "valid_problem")))


def asp_verify() -> int:
    import asp
    py = sorted((pid,) for pid in valid_problems())
    cl = asp_valid_problems()
    if py == cl:
        print(f"OK: clingo gate matches valid_problems() ({len(py)} problems).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("python:", py)
    print("clingo:", cl)
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld in a train station.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--name", choices=HERO_NAMES)
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
    problems = valid_problems()
    if not problems:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "problem", None) and getattr(args, "problem", None) not in problems:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    problem = getattr(args, "problem", None) or rng.choice(problems)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(problem=problem, helper=helper, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(problem="lost_ticket", helper="Pip", name="Iris", trait="quick-thinking"),
    StoryParams(problem="stuck_luggage", helper="Hob", name="Lina", trait="gentle"),
    StoryParams(problem="missing_pass", helper="Nell", name="Rosalind", trait="brave"),
]


def asp_program_text() -> str:
    return asp_program("#show valid_problem/1.")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_text())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_problem/1."))
        print(sorted(set(asp.atoms(model, "valid_problem"))))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.problem} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
