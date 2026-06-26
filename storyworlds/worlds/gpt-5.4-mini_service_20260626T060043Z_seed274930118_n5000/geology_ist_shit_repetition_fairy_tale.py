#!/usr/bin/env python3
"""
storyworlds/worlds/geology_ist_shit_repetition_fairy_tale.py
============================================================

A small fairy-tale storyworld about a geology-ist, a stubborn little hill,
and a repeated yucky problem that must be solved by careful looking.

Premise seed:
- geology-ist
- shit
- Repetition
- Fairy Tale

This world keeps the story child-facing, concrete, and causal:
a geology-ist notices the same nasty clue again and again, then uses that clue
to find the truth hidden under the ground.

The simulated state models:
- physical meters: clues, dirt, patience, crack, shine, work
- emotional memes: wonder, worry, bravery, relief, pride

The repeated beat is important: the same clue appears in more than one place,
and the geology-ist learns that the repetition is not noise but evidence.
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

# -----------------------------------------------------------------------------
# Story model
# -----------------------------------------------------------------------------

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "king"}:
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
    id: str
    label: str
    kind: str = "place"
    layers: list[str] = field(default_factory=list)
    clues: list[str] = field(default_factory=list)
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
    sign: str
    repeated_sign: str
    cause: str
    fix: str
    place: str
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
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place, problem: Problem) -> None:
        self.place = place
        self.problem = problem
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace_notes: list[str] = []

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
        w = World(copy.deepcopy(self.place), copy.deepcopy(self.problem))
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.trace_notes = list(self.trace_notes)
        return w


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

PLACES = {
    "cave": Place(
        id="cave",
        label="the singing cave",
        layers=["stone", "sand", "clay"],
        clues=["damp walls", "echoing drops", "crumbly stone"],
    ),
    "hill": Place(
        id="hill",
        label="the hill of three hollows",
        layers=["grass", "soil", "pebbles"],
        clues=["windy grass", "small stones", "a narrow crack"],
    ),
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        layers=["mud", "sand", "river rock"],
        clues=["wet mud", "rounded stones", "a shiny seam"],
    ),
}

PROBLEMS = {
    "slip": Problem(
        id="slip",
        label="a slipping slope",
        sign="the ground kept sliding down",
        repeated_sign="the same little slide happened again and again",
        cause="water had loosened the soil",
        fix="stacking flat stones like little steps",
        place="outdoor",
    ),
    "crumbles": Problem(
        id="crumbles",
        label="crumbly stone",
        sign="tiny chips kept falling from the wall",
        repeated_sign="more chips fell every time the wind sighed",
        cause="the wall was cracked and weak",
        fix="marking the weak place and clearing a safe path",
        place="outdoor",
    ),
    "glow": Problem(
        id="glow",
        label="a hidden shining seam",
        sign="a faint sparkle peeked from under the dirt",
        repeated_sign="the sparkle appeared in the same place three times",
        cause="a vein of bright mineral lay under the soil",
        fix="careful brushing and gentle telling",
        place="either",
    ),
}


# -----------------------------------------------------------------------------
# Reasonableness gate
# -----------------------------------------------------------------------------

def is_reasonable(place: Place, problem: Problem) -> bool:
    if problem.id == "slip":
        return place.id in {"hill", "riverbank"}
    if problem.id == "crumbles":
        return place.id in {"cave", "hill"}
    if problem.id == "glow":
        return True
    return False


# -----------------------------------------------------------------------------
# AS P twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when a place and problem fit together.
valid(P, Prob) :- place(P), problem(Prob), fits(P, Prob).

% Repetition matters: the story must have the same sign appear more than once.
repeated(Prob) :- problem(Prob), sign_count(Prob, N), N >= 2.

% The geology-ist should have a reason to worry and a way to fix it.
story_ok(P, Prob) :- valid(P, Prob), repeated(Prob), has_fix(Prob).

#show valid/2.
#show story_ok/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for prob in PROBLEMS.values():
        lines.append(asp.fact("problem", prob.id))
    for pid, place in PLACES.items():
        for sign in place.clues:
            # only used as evidence that the place contains repeatable signs
            lines.append(asp.fact("has_clue", pid, sign))
    for prob in PROBLEMS.values():
        lines.append(asp.fact("fits", "cave" if prob.id == "crumbles" else "hill" if prob.id == "slip" else "riverbank", prob.id)) if False else None
    # explicit fit facts
    lines.append(asp.fact("fits", "cave", "crumbles"))
    lines.append(asp.fact("fits", "hill", "crumbles"))
    lines.append(asp.fact("fits", "hill", "slip"))
    lines.append(asp.fact("fits", "riverbank", "slip"))
    lines.append(asp.fact("fits", "cave", "glow"))
    lines.append(asp.fact("fits", "hill", "glow"))
    lines.append(asp.fact("fits", "riverbank", "glow"))
    for prob in PROBLEMS.values():
        lines.append(asp.fact("has_fix", prob.id))
    # repetition facts
    lines.append(asp.fact("sign_count", "slip", 2))
    lines.append(asp.fact("sign_count", "crumbles", 2))
    lines.append(asp.fact("sign_count", "glow", 3))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_ok() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = set((p.id, prob.id) for p, prob in valid_combos())
    ac = set(asp_valid_combos())
    if py != ac:
        print("MISMATCH between Python and ASP:")
        if py - ac:
            print("  only in python:", sorted(py - ac))
        if ac - py:
            print("  only in asp:", sorted(ac - py))
        return 1
    print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
    return 0


# -----------------------------------------------------------------------------
# Narration helpers
# -----------------------------------------------------------------------------

def intro_line(hero: Entity) -> str:
    return f"{hero.id} was a little geology-ist who loved listening to stones."


def repetition_line(problem: Problem) -> str:
    return f"Again and again, {problem.repeated_sign}."


def opening_scene(place: Place) -> str:
    return f"One bright morning, the road led to {place.label}, where the air felt old and patient."


def warning_line(hero: Entity, problem: Problem) -> str:
    return (
        f"{hero.id} knelt, looked, and frowned. "
        f"{problem.sign.capitalize()}, and that meant trouble."
    )


def turn_line(hero: Entity, problem: Problem) -> str:
    return (
        f"{hero.pronoun().capitalize()} touched the ground with two careful fingers. "
        f"Then {hero.pronoun()} listened, and listened again."
    )


def resolution_line(hero: Entity, problem: Problem) -> str:
    return (
        f"At last, {hero.id} found the cause: {problem.cause}. "
        f"{hero.pronoun().capitalize()} solved it by {problem.fix}."
    )


# -----------------------------------------------------------------------------
# Story logic
# -----------------------------------------------------------------------------

def predict(world: World) -> dict:
    sim = world.copy()
    problem = sim.problem
    return {
        "repeated": True,
        "cause_known": bool(problem.cause),
        "fixed": bool(problem.fix),
    }


def build_story(world: World) -> None:
    hero = world.get("hero")
    place = world.place
    problem = world.problem

    hero.memes["wonder"] += 1
    world.say(intro_line(hero))
    world.say(opening_scene(place))
    world.say(
        f"{hero.id} had come because {problem.sign}. "
        f"{repetition_line(problem)}"
    )

    world.para()
    hero.memes["worry"] += 1
    hero.meters["patience"] += 1
    world.say(warning_line(hero, problem))
    world.say(turn_line(hero, problem))
    world.say(
        f"Each time {hero.id} looked, the same clue came back. "
        f"{repetition_line(problem)}"
    )

    world.para()
    hero.memes["bravery"] += 1
    hero.meters["clues"] += 2
    world.say(
        f"That was not just a bother; it was a message. "
        f"{hero.id} followed the repeated sign to the hidden truth."
    )
    world.say(resolution_line(hero, problem))
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.meters["work"] += 1
    world.say(
        f"In the end, the path was safe, the stones were still, and "
        f"{hero.id} left with a clean notebook and a brave, quiet smile."
    )


def tell(place: Place, problem: Problem, hero_name: str, hero_type: str) -> World:
    world = World(place, problem)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    build_story(world)
    world.facts = {
        "hero": world.get("hero"),
        "place": place,
        "problem": problem,
        "repeated": True,
        "resolved": True,
    }
    return world


# -----------------------------------------------------------------------------
# Parameters / sampling
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None
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


GIRL_NAMES = ["Mira", "Nina", "Ava", "Lina", "Tessa", "Ruby"]
BOY_NAMES = ["Oren", "Milo", "Theo", "Finn", "Jasper", "Levi"]
HERO_TYPES = ["girl", "boy"]


def valid_combos() -> list[tuple[Place, Problem]]:
    combos = []
    for place in PLACES.values():
        for prob in PROBLEMS.values():
            if is_reasonable(place, prob):
                combos.append((place, prob))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale geology-ist storyworld with repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--name")
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
    combos = [
        (p, prob)
        for p, prob in valid_combos()
        if (getattr(args, "place", None) is None or p.id == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or prob.id == getattr(args, "problem", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem = rng.choice(combos)
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place.id, problem=problem.id, hero_name=name, hero_type=gender)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    world = tell(place, problem, params.hero_name, params.hero_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# -----------------------------------------------------------------------------
# QA
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    return [
        f"Write a fairy tale about a geology-ist named {hero.id} who notices a clue again and again.",
        f"Tell a gentle story where repeated signs in {world.place.label} help {hero.id} solve a stone problem.",
        f"Write a child-friendly tale using the words geology-ist, repetition, and the clue {world.problem.sign}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little geology-ist who listens to stones.",
        ),
        QAItem(
            question=f"What kept happening again and again?",
            answer=f"{world.problem.repeated_sign.capitalize()}. That repetition was the clue {hero.id} needed.",
        ),
        QAItem(
            question=f"What problem did {hero.id} solve?",
            answer=f"{hero.id} solved {world.problem.label} by noticing {world.problem.sign.lower()} and following the repeated clue.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the problem fixed, the path safe, and {hero.id} feeling proud and relieved.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a geology-ist study?",
            answer="A geology-ist studies rocks, stone, soil, and other things found in the ground.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens or is said again and again.",
        ),
        QAItem(
            question="Why can repeated clues be useful?",
            answer="Repeated clues can be useful because they help you notice a pattern and find out what is really happening.",
        ),
        QAItem(
            question="What does it mean when a path is safe?",
            answer="A path is safe when people can walk there without slipping, getting hurt, or stepping into danger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Trace / emit
# -----------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"place={world.place.id} problem={world.problem.id}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
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


# -----------------------------------------------------------------------------
# ASP verification
# -----------------------------------------------------------------------------

def asp_ok() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_story_ok_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify_full() -> int:
    py = set((p.id, prob.id) for p, prob in valid_combos())
    asv = set(asp_ok())
    if py != asv:
        print("Python/ASP mismatch for valid combos.")
        if py - asv:
            print(" only python:", sorted(py - asv))
        if asv - py:
            print(" only asp:", sorted(asv - py))
        return 1
    print(f"OK: ASP matches Python ({len(py)} valid combos).")
    return 0


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

CURATED = [
    StoryParams(place="hill", problem="slip", hero_name="Mira", hero_type="girl"),
    StoryParams(place="cave", problem="crumbles", hero_name="Oren", hero_type="boy"),
    StoryParams(place="riverbank", problem="glow", hero_name="Tessa", hero_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_full())
    if getattr(args, "asp", None):
        triples = asp_ok()
        print(f"{len(triples)} valid geology stories:\n")
        for p, prob in triples:
            print(f"  {p:10} {prob}")
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
            header = f"### {p.hero_name}: {p.place} / {p.problem}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
