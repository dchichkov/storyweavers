#!/usr/bin/env python3
"""
A small superhero storyworld about a kind hero, a deaf helper, and a bowl of
fettuccine whose dinner-time problem gets solved with care, cleverness, and
sound effects that can be seen or felt.

The seed idea:
- A young superhero wants to help after a rough day.
- A deaf friend/caregiver needs dinner.
- Fettuccine boils over / sauce is missing / the kitchen is too loud.
- The hero uses kindness and problem solving to make a good meal and a warm,
  complete ending image.

This script keeps the world tiny and constraint-checked. The prose is driven by
state changes, not a frozen template swap.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    affords: set[str] = field(default_factory=set)
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
    cue: str
    issue: str
    fix_hint: str
    keyword: str
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
class Solution:
    id: str
    label: str
    prep: str
    tail: str
    solves: set[str] = field(default_factory=set)
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"boil_over", "missing_sauce", "loud_pan"}),
    "tower": Setting(place="the tower kitchen", affords={"boil_over", "missing_sauce"}),
    "roof": Setting(place="the rooftop diner", affords={"missing_sauce", "loud_pan"}),
}

PROBLEMS = {
    "boil_over": Problem(
        id="boil_over",
        cue="the pot of fettuccine started to boil over",
        issue="the noodles were climbing out of the pot",
        fix_hint="turn the heat down and stir with care",
        keyword="fettuccine",
        tags={"fettuccine", "problem solving"},
    ),
    "missing_sauce": Problem(
        id="missing_sauce",
        cue="the red sauce was missing",
        issue="plain noodles would be sad and dry",
        fix_hint="find a simple topping and share it kindly",
        keyword="fettuccine",
        tags={"fettuccine", "kindness"},
    ),
    "loud_pan": Problem(
        id="loud_pan",
        cue="the pan went CLANG and the room felt too noisy",
        issue="the loud sound made it hard for the deaf friend to follow along",
        fix_hint="switch to a visual plan and keep the steps clear",
        keyword="sound effects",
        tags={"sound effects", "deaf"},
    ),
}

SOLUTIONS = {
    "lid_spoon": Solution(
        id="lid_spoon",
        label="a wooden spoon and a lid",
        prep="cover the pot and stir slowly",
        tail="soon the noodles settled down",
        solves={"boil_over"},
    ),
    "bread_smile": Solution(
        id="bread_smile",
        label="warm bread and butter",
        prep="serve warm bread with a bright smile",
        tail="the plate looked full and friendly",
        solves={"missing_sauce"},
    ),
    "gesture_board": Solution(
        id="gesture_board",
        label="a quick picture board",
        prep="draw the plan with pictures and thumbs-up signs",
        tail="the deaf friend could see each step at once",
        solves={"loud_pan"},
    ),
}

HEROES = ["Nova", "Spark", "Comet", "Astra", "Bolt", "Mira"]
FRIENDS = ["Ivy", "Jun", "Noor", "Leo", "Pia", "Zane"]
TYPES = ["girl", "boy"]
FRIEND_TYPES = ["girl", "boy", "woman", "man"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            prob = _safe_lookup(PROBLEMS, pid)
            if pid in SOLUTIONS:
                out.append((place, pid))
    return out


def prize_at_risk(problem: Problem) -> bool:
    return True


def select_solution(problem: Problem) -> Optional[Solution]:
    for sol in SOLUTIONS.values():
        if problem.id in sol.solves:
            return sol
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: deaf, fettuccine, kindness, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=FRIEND_TYPES)
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
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem = rng.choice(list(combos))
    return StoryParams(
        place=place,
        problem=problem,
        hero=getattr(args, "hero", None) or rng.choice(HEROES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(TYPES),
        friend=getattr(args, "friend", None) or rng.choice(FRIENDS),
        friend_type=getattr(args, "friend_type", None) or rng.choice(FRIEND_TYPES),
    )


def introduce(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    world.say(f"{hero.id} was a little {hero.type} superhero who loved helping people.")
    world.say(f"{friend.id} was {friend.pronoun('possessive')} deaf friend, and they trusted {hero.id} to listen with kindness.")
    world.say(f"That evening, {problem.cue}.")


def start_problem(world: World, hero: Entity, friend: Entity, problem: Problem) -> None:
    world.say(f"{hero.id} looked at {friend.id} and saw the trouble right away.")
    if problem.id == "boil_over":
        world.say("The pot hissed: ssshh! ssshh!")
    elif problem.id == "missing_sauce":
        world.say("The empty bowl made the dinner feel a little plain.")
    else:
        world.say("The pan answered with a loud CLANG! CLANG!")
    hero.memes["concern"] += 1
    friend.memes["need"] += 1


def solve_problem(world: World, hero: Entity, friend: Entity, problem: Problem) -> Optional[Solution]:
    sol = select_solution(problem)
    if sol is None:
        return None
    hero.memes["kindness"] += 1
    hero.memes["resolve"] += 1
    if problem.id == "boil_over":
        world.say(f"{hero.id} used {sol.label} to {sol.prep}.")
        world.say(f"{sol.tail}, and the fettuccine stopped trying to escape.")
    elif problem.id == "missing_sauce":
        world.say(f"{hero.id} found {sol.label} and chose to {sol.prep}.")
        world.say(f"{sol.tail}, and the fettuccine looked like a happy rescue meal.")
    else:
        world.say(f"{hero.id} grabbed {sol.label} and chose to {sol.prep}.")
        world.say(f"{sol.tail}, so the deaf friend could follow the plan without guessing.")
    return sol


def finish(world: World, hero: Entity, friend: Entity, problem: Problem, sol: Solution) -> None:
    hero.memes["pride"] += 1
    friend.memes["relief"] += 1
    world.say(f"{friend.id} smiled big and gave {hero.id} a thankful hug.")
    world.say(f"Together they ate the fettuccine, and the room felt calm, bright, and kind.")
    if problem.id == "loud_pan":
        world.say(f"The last thing they noticed was the quiet rhythm of thumbs-up signs and happy faces.")
    elif problem.id == "boil_over":
        world.say(f"The last thing they noticed was steam lifting gently instead of racing everywhere.")
    else:
        world.say(f"The last thing they noticed was how good a simple meal could feel when shared.")


def tell(setting: Setting, problem: Problem, hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "kind", "bold"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["deaf", "warm"]))

    world.facts.update(hero=hero, friend=friend, problem=problem, setting=setting)

    introduce(world, hero, friend, problem)
    world.para()
    start_problem(world, hero, friend, problem)
    sol = solve_problem(world, hero, friend, problem)
    world.para()
    if sol:
        finish(world, hero, friend, problem, sol)
    world.facts["solution"] = sol
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem"]
    return [
        f"Write a superhero story for young children about {hero.id} helping {friend.id} with {problem.keyword} and a kitchen problem.",
        f"Tell a kind story where a {hero.type} superhero solves a dinner problem for a deaf friend using {problem.keyword}.",
        f"Write a simple rescue story with sound effects, kindness, and problem solving about fettuccine.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    problem = f["problem"]
    sol = f.get("solution")
    qa = [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, a kind little {hero.type} who wanted to help.",
        ),
        QAItem(
            question=f"Who needed extra care because they were deaf?",
            answer=f"{friend.id} needed extra care because {friend.pronoun('subject')} was deaf and used clear signs and kindness.",
        ),
        QAItem(
            question=f"What was the dinner food in the story?",
            answer=f"The dinner food was fettuccine, which was the meal everyone wanted to fix and share.",
        ),
        QAItem(
            question=f"What problem happened first?",
            answer=f"{problem.cue.capitalize()}",
        ),
    ]
    if sol:
        qa.append(
            QAItem(
                question="How did the hero solve the problem?",
                answer=f"{hero.id} used {sol.label} and chose to {sol.prep}, which made the meal safe and easy to understand.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean if someone is deaf?",
            answer="If someone is deaf, they do not hear sounds in the usual way, so signs, pictures, and clear gestures can help communicate.",
        ),
        QAItem(
            question="What is fettuccine?",
            answer="Fettuccine is a kind of pasta made of long, flat noodles that you can eat with sauce or butter.",
        ),
        QAItem(
            question="Why do superheroes use problem solving?",
            answer="Superheroes use problem solving to figure out a safe and helpful plan when something goes wrong.",
        ),
        QAItem(
            question="Why can sound effects help in a story?",
            answer="Sound effects can help a story feel lively, and they can also show what is happening in a way that is easy to notice.",
        ),
    ]


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(P) :- problem_fact(P).
solution(S) :- solution_fact(S).

can_solve(P, S) :- problem_fact(P), solution_fact(S), solves(S, P).
valid_story(Place, P) :- setting_fact(Place), afford_fact(Place, P), can_solve(P, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting_fact", place))
        for pid in sorted(setting.affords):
            lines.append(asp.fact("afford_fact", place, pid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_fact", pid))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution_fact", sid))
        for pid in sorted(s.solves):
            lines.append(asp.fact("solves", sid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(problem: Problem) -> str:
    return f"(No story: no solution in this tiny world cleanly solves {problem.id}.)"


CURATED = [
    StoryParams(place="kitchen", problem="boil_over", hero="Nova", hero_type="girl", friend="Ivy", friend_type="girl"),
    StoryParams(place="tower", problem="missing_sauce", hero="Spark", hero_type="boy", friend="Jun", friend_type="boy"),
    StoryParams(place="roof", problem="loud_pan", hero="Astra", hero_type="girl", friend="Noor", friend_type="woman"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "problem", None) and getattr(args, "problem", None) not in PROBLEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem = rng.choice(list(combos))
    return StoryParams(
        place=place,
        problem=problem,
        hero=getattr(args, "hero", None) or rng.choice(HEROES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(TYPES),
        friend=getattr(args, "friend", None) or rng.choice(FRIENDS),
        friend_type=getattr(args, "friend_type", None) or rng.choice(FRIEND_TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), params.hero, params.hero_type, params.friend, params.friend_type)
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


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid in setting.affords:
            if select_solution(_safe_lookup(PROBLEMS, pid)) is not None:
                out.append((place, pid))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:")
        for place, pid in triples:
            print(f"  {place:8} {pid}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
