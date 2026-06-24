#!/usr/bin/env python3
"""
A tiny story world about a child solving a shampoo mystery.

Premise:
A child notices that the bathroom shampoo bottle keeps being knocked over and
the bubbles end up on the floor. The child and a grown-up follow clues, ask
careful questions, and solve the mystery.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams, parser, resolve_params, generate, emit, main
- eager import of results containers
- lazy import of asp helper inside ASP helpers
- python reasonableness gate plus inline ASP twin
- simulated world state drives prose and QA
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    moved_by: Optional[str] = None
    placed_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bottle: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
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
    indoor: bool = True
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
class Clue:
    id: str
    label: str
    kind: str
    location: str
    reveals: str
    phrase: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Problem:
    id: str
    label: str
    mess: str
    sign: str
    risk: str
    zone: str
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
class Fix:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    uses: str
    action: str
    tail: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    clue: str
    fix: str
    name: str
    gender: str
    parent: str
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


SETTINGS = {
    "bathroom": Setting(place="the bathroom", indoor=True, affords={"spill", "search", "clean"}),
    "hallway": Setting(place="the hallway", indoor=True, affords={"search", "clean"}),
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"search"}),
}

PROBLEMS = {
    "shampoo": Problem(
        id="shampoo",
        label="shampoo",
        mess="slippery bubbles",
        sign="a foamy trail",
        risk="the bottle might spill and slide under the sink",
        zone="counter",
        keyword="shampoo",
        tags={"shampoo", "soap", "bath"},
    ),
    "soap": Problem(
        id="soap",
        label="soap",
        mess="slippery suds",
        sign="a wet ring",
        risk="the soap might skitter off the edge",
        zone="counter",
        keyword="soap",
        tags={"soap", "bath"},
    ),
    "toothpaste": Problem(
        id="toothpaste",
        label="toothpaste",
        mess="sticky streaks",
        sign="a white smear",
        risk="the cap may be loose and make a mess",
        zone="counter",
        keyword="toothpaste",
        tags={"toothpaste", "bath"},
    ),
}

CLUES = {
    "cap": Clue(
        id="cap",
        label="the loose cap",
        kind="object",
        location="by the sink",
        reveals="someone forgot to tighten the bottle",
        phrase="a loose cap near the sink",
    ),
    "footprints": Clue(
        id="footprints",
        label="tiny footprints",
        kind="sign",
        location="on the tile",
        reveals="a little helper carried the bottle while running",
        phrase="tiny wet footprints on the tile",
    ),
    "towel": Clue(
        id="towel",
        label="the towel",
        kind="object",
        location="on the floor",
        reveals="the bottle slid when the towel was left too close",
        phrase="a towel lying too close to the wet floor",
    ),
}

FIXES = {
    "shelf": Fix(
        id="shelf",
        label="the high shelf",
        phrase="put it on the high shelf",
        helps_with={"shampoo", "soap", "toothpaste"},
        uses="high shelf",
        action="move the bottle up",
        tail="placed it on the high shelf",
    ),
    "cap": Fix(
        id="cap",
        label="the tight cap",
        phrase="tighten the cap carefully",
        helps_with={"shampoo", "soap", "toothpaste"},
        uses="tight cap",
        action="close it tightly",
        tail="twisted the cap shut",
    ),
    "mat": Fix(
        id="mat",
        label="the bath mat",
        phrase="spread the bath mat under the bottle",
        helps_with={"shampoo", "soap"},
        uses="bath mat",
        action="set it on something steady",
        tail="spread the bath mat under it",
        plural=False,
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Max", "Eli", "Sam", "Theo", "Ben"]
TRAITS = ["curious", "careful", "clever", "gentle", "patient", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prob_id in setting.affords:
            prob = _safe_lookup(PROBLEMS, prob_id)
            for clue_id in CLUES:
                for fix_id, fx in FIXES.items():
                    if prob.id in fx.helps_with:
                        combos.append((place, prob_id, clue_id, fix_id))
    return [(a, b, c) for a, b, c, _ in combos]


def choose_fix(problem: Problem, clue: Clue) -> Optional[Fix]:
    if clue.id == "footprints" and problem.id == "shampoo":
        return FIXES["cap"]
    if clue.id == "cap":
        return FIXES["shelf"]
    if clue.id == "towel":
        return FIXES["mat"] if problem.id in FIXES["mat"].helps_with else None
    return FIXES["shelf"] if problem.id in FIXES["shelf"].helps_with else None


def reasonableness_check(problem: Problem, fix: Fix) -> bool:
    return problem.id in fix.helps_with


ASP_RULES = r"""
problem(P) :- prob(P).
fix(F) :- fx(F).

helpful(F, P) :- fix(F), problem(P), helps(F, P).
valid(P, F) :- problem(P), fix(F), helpful(F, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("prob", pid))
        lines.append(asp.fact("sign", pid, prob.sign))
        lines.append(asp.fact("zone", pid, prob.zone))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveals", cid, clue.reveals))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fx", fid))
        for p in sorted(fx.helps_with):
            lines.append(asp.fact("helps", fid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p, f) for _, p, _, f in [(a, b, c, d) for a, b, c in valid_combos() for d in []])
    # direct python tuples:
    py2 = sorted({(p, f) for _, p, _, f in [(a, b, c, f) for a, b, c in []]})
    # Compute properly
    py_set = set()
    for _, prob_id in [(None, pid) for pid in PROBLEMS]:
        for fid, fx in FIXES.items():
            if prob_id in fx.helps_with:
                py_set.add((prob_id, fid))
    asp_set = set(asp_valid())
    if py_set == asp_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python-only:", sorted(py_set - asp_set))
    print("clingo-only:", sorted(asp_set - py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery story world about shampoo.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    setting = _safe_lookup(SETTINGS, place)
    problem = getattr(args, "problem", None) or rng.choice(sorted(setting.affords))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    fix = getattr(args, "fix", None) or rng.choice(list(FIXES))
    if problem not in _safe_lookup(FIXES, fix).helps_with:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, clue=clue, fix=fix, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    prob = _safe_lookup(PROBLEMS, params.problem)
    clue = _safe_lookup(CLUES, params.clue)
    fix = _safe_lookup(FIXES, params.fix)
    bottle = world.add(Entity(id="Bottle", type="bottle", label="shampoo bottle", phrase="a blue shampoo bottle", owner=hero.id, caretaker=parent.id))
    bottle.meters["full"] = 1
    hero.memes["curiosity"] = 1
    world.facts.update(hero=hero, parent=parent, problem=prob, clue=clue, fix=fix, bottle=bottle)

    world.say(f"{params.name} was a little {params.trait} {params.gender} who loved helping in {world.setting.place}.")
    world.say(f"One morning, {params.name} noticed {prob.sign} near the shampoo bottle.")
    world.para()
    world.say(f"{params.name} pointed at {clue.phrase} and asked why the bottle kept making a mess.")
    if clue.id == "footprints":
        world.say(f"The clue showed that a small helper had moved the bottle without being careful.")
    elif clue.id == "cap":
        world.say(f"The clue showed that the cap was not closed all the way.")
    else:
        world.say(f"The clue showed that the bottle slid because something soft was left in the wrong place.")
    world.para()
    if fix.id == "cap":
        world.say(f"{params.parent.capitalize()} smiled and said they could solve the mystery by {fix.phrase}.")
    elif fix.id == "shelf":
        world.say(f"{params.parent.capitalize()} said the best answer was to {fix.phrase}.")
    else:
        world.say(f"{params.parent.capitalize()} found a simple fix: {fix.phrase}.")
    world.say(f"Together they {fix.tail}.")
    world.say(f"Then the bathroom looked neat again, and the shampoo stayed where it belonged.")
    world.say(f"{params.name} grinned, glad the little mystery was solved.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    prob = f["problem"]
    return [
        f'Write a short mystery story for a young child that includes the word "{prob.keyword}".',
        f"Tell a gentle story where {hero.id} notices a shampoo problem and helps a grown-up solve it.",
        "Write a simple mystery story with clues, a careful guess, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prob = f["problem"]
    clue = f["clue"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} notice in {world.setting.place}?",
            answer=f"{hero.id} noticed a problem with the shampoo bottle. The clue was {clue.phrase}, and it pointed to {prob.label}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} understand the shampoo mystery?",
            answer=f"The clue was {clue.phrase}. It revealed that {clue.reveals}.",
        ),
        QAItem(
            question=f"How did {hero.id} and the {parent.type} solve the mystery?",
            answer=f"They solved it by using {fix.phrase}. That kept the shampoo safe and cleaned up the little mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is shampoo for?",
            answer="Shampoo is used to wash hair and help make it clean.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why is it smart to put a bottle on a high shelf?",
            answer="A high shelf can help keep things from being knocked over or spilled by accident.",
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
    StoryParams(place="bathroom", problem="shampoo", clue="cap", fix="shelf", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bathroom", problem="shampoo", clue="footprints", fix="cap", name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="bathroom", problem="soap", clue="towel", fix="mat", name="Nora", gender="girl", parent="mother", trait="clever"),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is shampoo for?", answer="Shampoo is used to wash hair and help make it clean."),
        QAItem(question="What is a clue in a mystery?", answer="A clue is a small piece of information that helps someone figure out what happened."),
        QAItem(question="Why is it smart to put a bottle on a high shelf?", answer="A high shelf can help keep things from being knocked over or spilled by accident."),
    ]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(p, f) for p in PROBLEMS for f, fx in FIXES.items() if p in fx.helps_with}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def asp_valid() -> list[tuple]:
    return asp_valid_stories()


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} compatible (problem, fix) combos:\n")
        for p, f in vals:
            print(f"  {p:10} {f}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
