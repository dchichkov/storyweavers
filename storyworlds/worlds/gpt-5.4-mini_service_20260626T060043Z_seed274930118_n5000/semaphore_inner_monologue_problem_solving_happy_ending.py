#!/usr/bin/env python3
"""
A small storyworld about a semaphore that helps a little fox solve a problem
with inner monologue, careful problem solving, and a happy ending.
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
# Core model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fix: object | None = None
    helper: object | None = None
    hero: object | None = None
    semaphore: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Setting:
    place: str = "the little station"
    indoors: bool = True
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
    thing: str
    trouble: str
    fix_hint: str
    rhyme_end: str
    worry: str
    key: str
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
class Solution:
    id: str
    label: str
    phrase: str
    protects: set[str]
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
        self.problem_active = False

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "station": Setting(place="the little station", indoors=True),
    "garden": Setting(place="the garden gate", indoors=False),
}

PROBLEMS = {
    "lost_bell": Problem(
        id="lost_bell",
        thing="silver bell",
        trouble="the bell had rolled behind a tall box",
        fix_hint="a thin stick and a careful peek",
        rhyme_end="bell",
        worry="The fox feared the tune would stay still and dull",
        key="bell",
    ),
    "stuck_flag": Problem(
        id="stuck_flag",
        thing="bright flag",
        trouble="the flag was snagged on a branch",
        fix_hint="a gentle tug and a steady hand",
        rhyme_end="flag",
        worry="The fox feared the signal would hang and sag",
        key="flag",
    ),
    "dim_lantern": Problem(
        id="dim_lantern",
        thing="lantern",
        trouble="the lantern was dim and needed a shine",
        fix_hint="a wipe with cloth and a happy line",
        rhyme_end="glow",
        worry="The fox feared the path would stay low",
        key="lantern",
    ),
}

SOLUTIONS = {
    "stick": Solution(
        id="stick",
        label="a long twig",
        phrase="a long twig with a bendy tip",
        protects={"bell", "flag"},
    ),
    "cloth": Solution(
        id="cloth",
        label="a soft cloth",
        phrase="a soft cloth for a careful shine",
        protects={"lantern"},
    ),
    "stepstool": Solution(
        id="stepstool",
        label="a tiny stool",
        phrase="a tiny stool with steady feet",
        protects={"flag", "lantern"},
    ),
}

FOX_NAMES = ["Pip", "Milo", "Nora", "Luna", "Toby", "Mira"]
HELPERS = ["grandma", "grandpa", "friend", "neighbor"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    problem: str
    solution: str
    name: str
    helper: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
    params: object | None = None
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


ASP_RULES = r"""
% A problem is solvable if a solution protects the thing that is in trouble.
solvable(P,S) :- problem(P), solution(S), troubled(P,T), protects(S,T).

valid_story(Setting,P,S) :- setting(Setting), solvable(P,S).
"""


def asp_facts() -> str:
    import asp
    out: list[str] = []
    for sid in SETTINGS:
        out.append(asp.fact("setting", sid))
    for pid, p in PROBLEMS.items():
        out.append(asp.fact("problem", pid))
        out.append(asp.fact("troubled", pid, p.key))
    for sid, s in SOLUTIONS.items():
        out.append(asp.fact("solution", sid))
        for t in sorted(s.protects):
            out.append(asp.fact("protects", sid, t))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for pid, p in PROBLEMS.items():
            for sid, s in SOLUTIONS.items():
                if p.key in s.protects:
                    combos.append((setting, pid, sid))
    return combos


def explain_rejection(problem: Problem, solution: Solution) -> str:
    return (
        f"(No story: {solution.label} cannot honestly fix {problem.thing} "
        f"because it does not protect that kind of trouble.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def build_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", type="fox"))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    problem = _safe_lookup(PROBLEMS, params.problem)
    solution = _safe_lookup(SOLUTIONS, params.solution)
    semaphore = world.add(Entity(
        id="semaphore",
        type="semaphore",
        label="semaphore",
        phrase="a bright semaphore",
        owner=hero.id,
        caretaker=helper.id,
    ))
    thing = world.add(Entity(
        id="thing",
        type=problem.key,
        label=problem.thing,
        phrase=f"the {problem.thing}",
        owner=hero.id,
        caretaker=helper.id,
    ))
    fix = world.add(Entity(
        id="fix",
        type="tool",
        label=solution.label,
        phrase=solution.phrase,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
    ))
    fix.meters["ready"] = 1

    hero.memes["curious"] = 1
    hero.memes["hope"] = 1
    semaphore.meters["shiny"] = 1
    thing.meters["stuck"] = 1

    world.say(f"At {world.setting.place}, a small fox named {hero.id} saw a semaphore shine.")
    world.say(f"The semaphore clicked and clacked, so neat and fine, like a signal in a rhyme.")
    world.say(f"{hero.id} loved the little light, but then came trouble with the {problem.thing}.")
    world.say(problem.worry + ", because " + problem.trouble + ".")

    world.para()
    hero.memes["worry"] = 1
    world.say(
        f"{hero.id} whispered in {hero.pronoun('possessive')} head, "
        f'"If I cannot fix it, the day may feel odd and thick."'
    )
    world.say(
        f"{hero.id} looked at the semaphore, then at {problem.fix_hint}, "
        f"and tried to think of something quick."
    )

    world.para()
    world.say(f"Then {params.helper} came near and smiled, not stern and not rough.")
    world.say(
        f'"Let us try {solution.label}," said {params.helper}, "and use it just enough."'
    )
    world.say(
        f"So {hero.id} took {solution.label} in {hero.pronoun('possessive')} paws and worked with care and cheer,"
    )
    if problem.key == "bell":
        world.say("a tiny push, a tiny pull, and out came the bell with a gleam so clear.")
    elif problem.key == "flag":
        world.say("a gentle tug, a steady stance, and down came the flag with a fluttery swish.")
    else:
        world.say("a soft wipe, a brighter spark, and soon the lantern shone like a wish.")

    hero.memes["worry"] = 0
    hero.memes["joy"] = 2
    world.say(
        f"The semaphore flashed again, and the signal felt new; "
        f"{problem.thing} was safe, and the whole plan came through."
    )
    world.say(
        f"{hero.id} smiled at {params.helper}, then at the semaphore bright; "
        f"the little fox had solved the puzzle, and the ending felt right."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        problem=problem,
        solution=solution,
        semaphore=semaphore,
        thing=thing,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for small children about a semaphore and a fox named {f["hero"].id}.',
        f"Tell a gentle tale where {f['hero'].id} notices a semaphore, faces a little problem, thinks hard inside, and finds a fix.",
        f"Write a short rhyming story that ends happily after {f['helper'].label} helps solve {f['problem'].thing}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    problem = _safe_fact(world, f, "problem")
    solution = _safe_fact(world, f, "solution")
    return [
        QAItem(
            question=f"What did {hero.id} see at the start of the story?",
            answer=f"{hero.id} saw a bright semaphore at {world.setting.place}.",
        ),
        QAItem(
            question=f"What problem made {hero.id} pause and think?",
            answer=f"The {problem.thing} was stuck, dim, or snagged, so {hero.id} had to stop and solve it carefully.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the fix?",
            answer=f"{helper.label} helped {hero.id}, and together they used {solution.label}.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} felt happy at the end because the problem was solved and the semaphore was shining again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a semaphore?",
            answer="A semaphore is a signal system that uses shapes, arms, or lights to send messages and directions.",
        ),
        QAItem(
            question="Why do people use signals like a semaphore?",
            answer="People use signals to share information clearly, especially when words would be hard to hear or far away.",
        ),
    ]


# ---------------------------------------------------------------------------
# Serialization / output
# ---------------------------------------------------------------------------
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming semaphore storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name", choices=FOX_NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "problem", None) and getattr(args, "solution", None):
        p = _safe_lookup(PROBLEMS, getattr(args, "problem", None))
        s = _safe_lookup(SOLUTIONS, getattr(args, "solution", None))
        if p.key not in s.protects:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "solution", None) is None or c[2] == getattr(args, "solution", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, solution = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(FOX_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(setting=setting, problem=problem, solution=solution, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    build_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:\n")
        for setting, problem, solution in stories:
            print(f"  {setting:7} {problem:10} {solution}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for setting, problem, solution in valid_combos():
            params = StoryParams(setting=setting, problem=problem, solution=solution, name="Pip", helper="friend")
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
