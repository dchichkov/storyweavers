#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260623T073613Z_seed779406221_n50_script_constipate_rejoice_transformation_humor_mystery.py
=============================================================================================================

A small standalone storyworld about a mystery in a tiny theater room where a
missing script, a jammed prop box, and a surprising transformation lead to a
humorous ending.

Seed words: script, constipate, rejoice
Style: mystery
Features: transformation, humor

The world is built around one child-facing premise:
- A rehearsal script has gone missing.
- A prop box gets jammed and behaves like it is "constipated" in the silly,
  storybook sense of being clogged and unable to let things out.
- The characters follow clues, the box transforms into something useful, and
  everyone rejoices when the mystery is solved.

This file follows the Storyweavers contract:
- self-contained stdlib script
- imports shared results eagerly
- imports asp lazily only inside ASP helpers
- provides StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
            keys = [upper + "S", upper + "ES"]
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
    plural: bool = False
    jammed: bool = False
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    grown: object | None = None
    kid: object | None = None
    prob: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Place:
    id: str
    label: str
    setting: str
    clue: str
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
    phrase: str
    clue: str
    mess: str
    risk: str
    kind: str
    transforms_into: str
    can_jam: bool = False
    tags: set[str] = field(default_factory=set)
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
    method: str
    outcome: str
    tags: set[str] = field(default_factory=set)
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    child: str
    child_type: str
    adult: str
    adult_type: str
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


PLACES = {
    "school_stage": Place(
        id="school_stage",
        label="the school stage",
        setting="the school stage",
        clue="The velvet curtain and the prop table made the room feel like a mystery waiting to open.",
        affords={"script", "jam", "reveal"},
    ),
    "library_corner": Place(
        id="library_corner",
        label="the library corner",
        setting="the library corner",
        clue="The reading nook had posters, a tiny lamp, and a box of donated costumes.",
        affords={"script", "jam", "reveal"},
    ),
    "back_room": Place(
        id="back_room",
        label="the back room",
        setting="the back room",
        clue="The shelves were full of paint pots, masks, and rolled-up posters.",
        affords={"script", "jam", "reveal"},
    ),
}

PROBLEMS = {
    "missing_script": Problem(
        id="missing_script",
        label="missing script",
        phrase="the rehearsal script",
        clue="The pages had vanished from the table just before the show.",
        mess="gone",
        risk="the actors could not remember their lines",
        kind="script",
        transforms_into="a clue map",
        can_jam=False,
        tags={"script", "mystery"},
    ),
    "jammed_box": Problem(
        id="jammed_box",
        label="jammed prop box",
        phrase="the prop box",
        clue="The box would not open because something was stuck inside it.",
        mess="jammed",
        risk="the props could not come out",
        kind="jam",
        transforms_into="a costume stand",
        can_jam=True,
        tags={"jam", "mystery", "humor"},
    ),
    "stuck_tape": Problem(
        id="stuck_tape",
        label="stuck tape drawer",
        phrase="the tape drawer",
        clue="A roll of tape had swallowed the drawer key and wedged itself tight.",
        mess="stuck",
        risk="the clues could not be reached",
        kind="jam",
        transforms_into="a clue shelf",
        can_jam=True,
        tags={"jam", "mystery"},
    ),
}

FIXES = {
    "ask_clues": Fix(
        id="ask_clues",
        label="a clue hunt",
        phrase="a careful clue hunt",
        method="look for tiny hints around the room",
        outcome="found the clue",
        tags={"script", "mystery"},
    ),
    "open_and_tilt": Fix(
        id="open_and_tilt",
        label="a gentle tilt",
        phrase="a gentle tilt and a pat on the side",
        method="tilt the box and tap it loose",
        outcome="the stuck thing slid free",
        tags={"jam", "humor"},
    ),
    "turn_the_box": Fix(
        id="turn_the_box",
        label="a turning trick",
        phrase="a turning trick",
        method="turn the jammed box upside down",
        outcome="the box became something new",
        tags={"jam", "transformation"},
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ruby", "Sage", "Tia"]
BOY_NAMES = ["Theo", "Finn", "Eli", "Noah", "Max", "Owen"]
TRAITS = ["curious", "careful", "bright", "playful", "sharp"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for prob in PROBLEMS.values():
            for fix in FIXES.values():
                if prob.kind == "script" and fix.id == "turn_the_box":
                    continue
                if prob.can_jam and fix.id == "ask_clues":
                    continue
                out.append((place, prob.id, fix.id))
    return out


def explain_rejection(prob: Problem, fix: Fix) -> str:
    return f"(No story: {fix.label} does not fit {prob.label}.)"


def can_transform(prob: Problem, fix: Fix) -> bool:
    return prob.can_jam and fix.id == "turn_the_box"


def can_solve(prob: Problem, fix: Fix) -> bool:
    return not (prob.kind == "script" and fix.id == "turn_the_box")


ASP_RULES = r"""
valid(P, R, F) :- place(P), problem(R), fix(F), not banned(P, R, F).
banned(_, missing_script, turn_the_box).
banned(_, jammed_box, ask_clues) :- true.
banned(_, stuck_tape, ask_clues) :- true.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in PROBLEMS.values():
        lines.append(asp.fact("problem", r.id))
    for f in FIXES.values():
        lines.append(asp.fact("fix", f.id))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world with a silly transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-type", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, fix = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    adult_type = getattr(args, "adult_type", None) or rng.choice(["mother", "father"])
    child = getattr(args, "child", None) or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(["Mom", "Dad", "Ms. Pine", "Mr. Reed"])
    return StoryParams(place=place, problem=problem, fix=fix, child=child, child_type=child_type, adult=adult, adult_type=adult_type)


def _do_transform(world: World, problem: Problem) -> None:
    p = world.get(problem.id)
    p.transformed = True
    p.meters["change"] = 1.0


def tell(place: Place, problem: Problem, fix: Fix, child: str, child_type: str, adult: str, adult_type: str) -> World:
    world = World(place)
    kid = world.add(Entity(id=child, kind="character", type=child_type, label=child))
    grown = world.add(Entity(id=adult, kind="character", type=adult_type, label=adult))
    prob = world.add(Entity(id=problem.id, kind="thing", type=problem.kind, label=problem.label, phrase=problem.phrase, jammed=problem.can_jam))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label="clue", phrase="a tiny clue"))
    kid.memes["curiosity"] = 1.0
    world.say(f"{kid.id} and {grown.label} were at {place.label}.")
    world.say(place.clue)
    world.say(f"Something strange was wrong: {problem.clue}")
    world.para()
    if problem.kind == "script":
        world.say(f"The missing {problem.label} made everyone whisper, because the story could not start without it.")
        world.say(f"{kid.id} found one torn page behind the chair, and it read like a clue.")
        world.say(f'"Maybe the script is hiding," {kid.id} said, "or maybe it wants to be found."')
        world.say(f"{grown.label} smiled and said the best mysteries begin with careful looking.")
        world.say("They followed the pencil marks, and the page trail led to the prop box.")
        world.say(f"The prop box was not broken, just {problem.mess}; it looked almost constipated, which made {kid.id} giggle.")
        world.para()
        world.say(f"{kid.id} and {grown.label} chose {fix.phrase}.")
        world.say(f"They used it to {fix.method}, and soon {fix.outcome}.")
        world.say(f"Under the box lid, they found the missing script at last.")
        world.say(f"The pages were curled into a neat stack, as if they had been waiting to rejoice.")
    else:
        world.say(f"The trouble was the {problem.label}, and it made the room feel like a puzzle.")
        world.say(f"{kid.id} tried to open it, but it stayed {problem.mess}.")
        if fix.id == "turn_the_box":
            world.say(f"They tried {fix.phrase}, and the box transformed into {problem.transforms_into}.")
        else:
            world.say(f"They used {fix.phrase} and {fix.method}.")
        world.say(f"That worked, and {fix.outcome}.")
        world.say(f"The room became funny and bright again, as if the mystery had been smiling all along.")
    _do_transform(world, problem if problem.can_jam else prob)
    world.facts.update(child=kid, adult=grown, place=place, problem=problem, fix=fix, outcome="solved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that includes the word "script" and ends in a happy discovery.',
        f"Tell a funny little mystery where {f['child'].id} and {f['adult'].label} solve a problem at {f['place'].label}.",
        f'Write a story that uses the word "constipate" in a silly, child-friendly way and ends with everyone glad.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = f["child"]
    adult = f["adult"]
    place = f["place"]
    problem = f["problem"]
    fix = f["fix"]
    return [
        QAItem(question=f"Where did {kid.id} look for the mystery?", answer=f"They looked at {place.label}, where the clue felt hidden in plain sight."),
        QAItem(question=f"What was missing in the story?", answer=f"The missing thing was {problem.label}, so the rehearsal could not begin until it was found."),
        QAItem(question=f"How did {kid.id} and {adult.label} solve the problem?", answer=f"They used {fix.label} and worked carefully until the clue or the script came loose."),
        QAItem(question=f"Why did {kid.id} giggle?", answer=f"{problem.label.title()} looked so jammed that it seemed constipated in a silly, storybook way, which made the room feel funny instead of scary."),
        QAItem(question=f"What changed at the end?", answer=f"The mystery turned into a happy answer: the missing part was found, and everyone could rejoice."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a script?", answer="A script is the written plan for a play, movie, or show, with the lines the actors say."),
        QAItem(question="What does rejoice mean?", answer="Rejoice means to feel very happy and celebrate because something good happened."),
        QAItem(question="What is a mystery?", answer="A mystery is a puzzle or secret that people try to solve by looking for clues."),
        QAItem(question="What is transformation?", answer="Transformation means something changes into a new form or becomes different."),
        QAItem(question="How can a story be funny?", answer="A story can be funny when something surprising or silly happens, like a jammed box acting constipated in a playful way."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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
        if e.jammed:
            bits.append("jammed=True")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="school_stage", problem="missing_script", fix="ask_clues", child="Mia", child_type="girl", adult="Mom", adult_type="mother"),
    StoryParams(place="library_corner", problem="jammed_box", fix="open_and_tilt", child="Theo", child_type="boy", adult="Dad", adult_type="father"),
    StoryParams(place="back_room", problem="stuck_tape", fix="turn_the_box", child="Nora", child_type="girl", adult="Ms. Pine", adult_type="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(FIXES, params.fix), params.child, params.child_type, params.adult, params.adult_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(asp.atoms(model, 'valid'))} compatible combos")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.child} at {p.place} ({p.problem} -> {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
