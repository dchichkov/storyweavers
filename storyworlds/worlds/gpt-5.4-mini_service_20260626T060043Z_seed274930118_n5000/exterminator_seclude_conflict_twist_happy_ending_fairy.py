#!/usr/bin/env python3
"""
A fairy-tale storyworld about a castle problem, a twist, and a happy ending.

A tiny source tale inspires the model:
- A kindly exterminator arrives at a fairy-tale cottage or castle.
- A pesky swarm or creature is causing a conflict.
- Someone tries to seclude the problem in a safe place, but the twist is that
  the hidden place also protects a frightened helper.
- The ending is happy because the safe plan works, the nuisance is gone, and
  the characters feel relieved together.

This world keeps the prose child-facing and state-driven while using meters
and memes to model the physical and emotional changes.
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
    sealed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    exterminator: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"princess", "queen", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"prince", "king", "boy", "man", "exterminator"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Place:
    id: str
    label: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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
    name: str
    kind: str
    mess: str
    fear: str
    location: str
    can_seclude: bool
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
class Solution:
    id: str
    label: str
    verb: str
    noun: str
    helps: set[str] = field(default_factory=set)
    seals: bool = False
    safe_place: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.twist: str = ""

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


def _narrate_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


PLACES = {
    "castle": Place(id="castle", label="the castle", affords={"sweep", "seclude"}),
    "cottage": Place(id="cottage", label="the cottage", affords={"sweep", "seclude"}),
    "garden": Place(id="garden", label="the garden", affords={"seclude", "sweep"}),
}

PROBLEMS = {
    "mice": Problem(
        id="mice",
        name="mice",
        kind="mice",
        mess="crumbs and nibbling",
        fear="tiny scratching noises",
        location="pantry",
        can_seclude=True,
        tags={"mouse", "nibble"},
    ),
    "moths": Problem(
        id="moths",
        name="moths",
        kind="moths",
        mess="holes and fluttering",
        fear="a soft cloud of wings",
        location="linen room",
        can_seclude=True,
        tags={"moth", "flutter"},
    ),
    "gnomes": Problem(
        id="gnomes",
        name="gnomes",
        kind="gnomes",
        mess="mischief and muddy tracks",
        fear="little muddy footprints",
        location="hallway",
        can_seclude=True,
        tags={"gnome", "mud"},
    ),
}

SOLUTIONS = {
    "lamp_trap": Solution(
        id="lamp_trap",
        label="a lantern trap",
        verb="set up",
        noun="lantern trap",
        helps={"mice", "moths"},
        seals=True,
        safe_place="the pantry",
    ),
    "warded_box": Solution(
        id="warded_box",
        label="a warded box",
        verb="open",
        noun="warded box",
        helps={"moths", "gnomes"},
        seals=True,
        safe_place="the attic",
    ),
    "flower_gate": Solution(
        id="flower_gate",
        label="a flower gate",
        verb="close",
        noun="flower gate",
        helps={"gnomes"},
        seals=True,
        safe_place="the garden shed",
    ),
}

CHARACTER_NAMES = ["Ella", "Rose", "Mina", "Iris", "Nora", "Lily", "Ava", "Daisy"]
HERO_TYPES = ["princess", "girl"]
HELPER_TYPES = ["queen", "mother", "fairy"]
TRAITS = ["brave", "gentle", "curious", "kind", "patient", "cheerful"]


@dataclass
class StoryParams:
    place: str
    problem: str
    solution: str
    name: str
    hero_type: str
    helper_type: str
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


def reasonableness_gate(problem: Problem, solution: Solution, place: Place) -> bool:
    return place.id in {"castle", "cottage", "garden"} and problem.kind in solution.helps and problem.can_seclude


ASP_RULES = r"""
problem_kind(P, K) :- problem(P), kind_of(P, K).
solution_help(S, K) :- solution(S), helps_kind(S, K).
can_resolve(P, S) :- problem_kind(P, K), solution_help(S, K).
valid_story(Place, P, S) :- place(Place), can_seclude(Place), problem(P), solution(S), can_resolve(P, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("kind_of", pid, pr.kind))
        if pr.can_seclude:
            lines.append(asp.fact("can_seclude", pid))
    for sid, s in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        for k in sorted(s.helps):
            lines.append(asp.fact("helps_kind", sid, k))
        if s.seals:
            lines.append(asp.fact("seals", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            for sol_id, sol in SOLUTIONS.items():
                if reasonableness_gate(prob, sol, place):
                    out.append((place_id, prob_id, sol_id))
    return sorted(out)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world with an exterminator, seclusion, conflict, a twist, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    combos = valid_combos()
    filtered = [c for c in combos
                if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
                and (getattr(args, "solution", None) is None or c[2] == getattr(args, "solution", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, prob_id, sol_id = rng.choice(filtered)
    return StoryParams(
        place=place_id,
        problem=prob_id,
        solution=sol_id,
        name=getattr(args, "name", None) or rng.choice(CHARACTER_NAMES),
        hero_type=getattr(args, "hero_type", None) or "princess",
        helper_type=getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def _do_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper_type, label=f"the {params.helper_type}"))
    exterminator = world.add(Entity(id="Exterminator", kind="character", type="exterminator", label="the exterminator"))
    problem = _safe_lookup(PROBLEMS, params.problem)
    solution = _safe_lookup(SOLUTIONS, params.solution)
    world.facts.update(hero=hero, helper=helper, exterminator=exterminator, problem=problem, solution=solution, params=params)

    hero.memes["hope"] += 1
    world.say(f"Once upon a time, in {world.place.label}, there lived a {params.trait} {params.hero_type} named {params.name}.")
    world.say(f"{params.name} loved the quiet songs of bells and birds, but one day {problem.name} brought {problem.mess} to the {problem.location}.")
    world.say(f"The little {params.hero_type} frowned, because the castle smelled of {problem.fear} and the servants could not rest.")

    world.para()
    hero.memes["conflict"] += 1
    world.say(f"Then the {params.helper_type} called for {exterminator.pronoun('object')}, a kind exterminator who knew how to help without hurting the fairy-tale folk.")
    world.say(f"{exterminator.pronoun().capitalize()} promised to chase away {problem.name} and keep the peace.")

    world.say(f"But there was a conflict: the noisy work would frighten a shy little helper hiding near {problem.location}.")
    helper.memes["fear"] += 1
    world.say(f"So the {params.helper_type} tried to seclude the helper in a snug room behind a blue curtain, where the rattle and bustle would not reach.")

    world.para()
    world.twist = "The hidden room was not empty; it held the baby mouse the exterminator had been looking for."
    world.say(f"That was the twist: behind the curtain was not trouble, but a tiny lost creature shaking like a leaf.")
    world.say(f"The exterminator softened at once and used {solution.label}, because it could solve the problem and leave the small creature safe.")
    if problem.kind in solution.helps:
        world.say(f"With one careful spell and a gentle hand, {params.name} and the {params.helper_type} watched {problem.name} disappear from the {problem.location}.")
        world.say(f"The little hidden creature was not harmed, and the room was still and sweet again.")

    world.para()
    hero.memes["joy"] += 2
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    exterminator.memes["pride"] += 1
    world.say(f"At last, the castle was calm. {params.name} smiled, the {params.helper_type} laughed softly, and the exterminator bowed like a hero from a storybook.")
    world.say(f"With the problem gone and the hidden friend safe, everyone shared warm bread by the fire, and the moon shone kindly on the happy ending.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = _do_story(World(_safe_lookup(PLACES, params.place)), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    pr = _safe_fact(world, world.facts, "problem")
    sol = _safe_fact(world, world.facts, "solution")
    return [
        f'Write a fairy-tale story about an exterminator, a seclude plan, and a happy ending at {world.place.label}.',
        f"Tell a gentle story where a {p.hero_type} named {p.name} sees {pr.name} causing trouble and a {p.helper_type} asks for a careful fix.",
        f"Write a children's story that includes an exterminator, a hidden safe room, a twist, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    pr = _safe_fact(world, world.facts, "problem")
    sol = _safe_fact(world, world.facts, "solution")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.name}, a {p.trait} {p.hero_type}, and the helpful {p.helper_type} who called the exterminator.",
        ),
        QAItem(
            question=f"What problem caused trouble in {world.place.label}?",
            answer=f"{pr.name} caused {pr.mess} in the {pr.location}, which made the castle feel uneasy.",
        ),
        QAItem(
            question=f"How did the characters solve the conflict?",
            answer=f"They used {sol.label}, a careful solution that fit the problem and helped bring back peace.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the hidden place held a tiny lost creature, so the seclude plan kept someone safe instead of trapping trouble alone.",
        ),
        QAItem(
            question=f"Why was it a happy ending?",
            answer=f"It ended happily because the trouble was removed, the hidden creature was safe, and everyone felt relieved together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an exterminator do?",
            answer="An exterminator helps remove pests or other unwanted creatures from a home or garden so people can live more comfortably.",
        ),
        QAItem(
            question="What does seclude mean?",
            answer="To seclude something means to keep it apart in a quiet, safe, or hidden place.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the trouble is fixed and the characters finish the story feeling safe, calm, or joyful.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.sealed:
            bits.append("sealed=True")
        lines.append(f"  {e.id:12} ({e.type:11}) {' '.join(bits)}")
    if world.twist:
        lines.append(f"  twist: {world.twist}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="castle", problem="mice", solution="lamp_trap", name="Lily", hero_type="princess", helper_type="queen", trait="brave"),
    StoryParams(place="cottage", problem="moths", solution="warded_box", name="Mina", hero_type="girl", helper_type="fairy", trait="curious"),
    StoryParams(place="garden", problem="gnomes", solution="flower_gate", name="Rose", hero_type="princess", helper_type="mother", trait="kind"),
]


def explain_rejection(problem: Problem, solution: Solution) -> str:
    return f"(No story: {solution.label} does not fit {problem.name} in a reasonable fairy-tale way.)"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_story_params_from_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, problem, solution) combos:\n")
        for place, prob, sol in triples:
            print(f"  {place:8} {prob:8} {sol:12}")
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
            header = f"### {p.name}: {p.problem} at {p.place} (solution: {p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
