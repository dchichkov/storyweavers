#!/usr/bin/env python3
"""
storyworlds/worlds/firm_mold_lesson_learned_problem_solving_ghost.py
=====================================================================

A small ghost-story world about a firm old building, a patch of mold, and a
lesson learned through gentle problem solving.

Premise:
- A child notices something in an old place that should stay firm and safe.
- Mold starts to spread on a stored item.
- A ghostly helper can't clean it alone, so the characters solve the problem
  with a careful, child-friendly plan.
- The ending proves the lesson learned: keeping things dry, sealed, and aired
  out prevents the mold from coming back.

The world is designed to stay close to a classic ghost-story shape while still
being a concrete, state-driven simulation.
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
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandpa"}:
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
    label: str
    is_firm: bool
    has_musty_corners: bool
    has_windows: bool = True
    has_basement: bool = False
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
    cause: str
    fix: str
    spread: str
    damage: str
    clue: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps_with: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.is_dark: bool = True
        self.rained_recently: bool = False

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.is_dark = self.is_dark
        clone.rained_recently = self.rained_recently
        return clone


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    child_name: str
    child_type: str
    helper_type: str
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


PLACES = {
    "old_house": Place(label="the old house", is_firm=True, has_musty_corners=True, has_windows=True),
    "cellar": Place(label="the cellar", is_firm=True, has_musty_corners=True, has_windows=False, has_basement=True),
    "attic": Place(label="the attic", is_firm=True, has_musty_corners=True, has_windows=False),
    "lighthouse": Place(label="the lighthouse", is_firm=True, has_musty_corners=False, has_windows=True),
}

PROBLEMS = {
    "mold": Problem(
        id="mold",
        label="mold",
        cause="a damp, forgotten corner",
        fix="fresh air and a dry cloth",
        spread="it can spread over food and paper",
        damage="it makes food go fuzzy and unsafe to eat",
        clue="a green-gray patch that smells musty",
        tags={"mold", "damp", "musty"},
    ),
    "wet_wall": Problem(
        id="wet_wall",
        label="a wet wall",
        cause="rain seeping in through a crack",
        fix="a patch, a bucket, and better sealing",
        spread="it leaves puddles on the floor",
        damage="it can make the room smell stale and weak",
        clue="water beads sliding down the stone",
        tags={"wet", "rain", "crack"},
    ),
}

TOOLS = {
    "cloth": Tool(id="cloth", label="a firm dry cloth", phrase="a firm dry cloth", use="wipe the fuzzy spots away", helps_with={"mold"}),
    "box": Tool(id="box", label="a tight box", phrase="a tight box with a good lid", use="seal the snack so no damp air gets in", helps_with={"mold"}),
    "patch": Tool(id="patch", label="a patch kit", phrase="a patch kit and some tape", use="seal the crack", helps_with={"wet_wall"}),
    "lamp": Tool(id="lamp", label="a bright lamp", phrase="a bright lamp", use="show the dark corner clearly", helps_with={"mold", "wet_wall"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Maya", "Rose"]
BOY_NAMES = ["Theo", "Ben", "Finn", "Leo", "Milo", "Eli"]
TRAITS = ["careful", "curious", "brave", "patient", "gentle", "thoughtful"]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.is_firm:
            lines.append(asp.fact("firm", pid))
        if place.has_musty_corners:
            lines.append(asp.fact("musty_corner", pid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for tag in sorted(prob.tags):
            lines.append(asp.fact("problem_tag", pid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(tool.helps_with):
            lines.append(asp.fact("helps_with", tid, p))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, Pr, T) :- place(P), problem(Pr), tool(T), firm(P), helps_with(T, Pr).
"""

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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for pr in PROBLEMS:
            for t in TOOLS:
                if _safe_lookup(PLACES, p).is_firm and pr in _safe_lookup(TOOLS, t).helps_with:
                    out.append((p, pr, t))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world about mold, lessons, and problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["ghost", "grandma"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or "ghost"
    return StoryParams(place=place, problem=problem, tool=tool, child_name=name, child_type=gender, helper_type=helper)


def _voice(hero: Entity, helper: Entity) -> str:
    return f"{hero.id} and the {helper.type}"


def _intro(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(f"{hero.id} lived in {world.place.label}, a firm old place with shadows in the corners.")
    world.say(f"{hero.pronoun().capitalize()} was {hero.memes['trait_word']} and liked quiet nights, even when the house creaked.")
    world.say(f"One evening, {helper.label} drifted in and pointed at {problem.clue} on a shelf.")
    world.say(f"It was mold, and it looked like a tiny green-gray cloud that did not belong there.")


def _problem_turn(world: World, hero: Entity, helper: Entity, problem: Problem, item: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} saw that the mold could spread to the snack box because {problem.spread}.")
    world.say(f"{helper.label} whispered that this was a problem to solve, not a thing to fear.")
    world.say(f"Together they looked at the damp corner and decided to fix the source instead of just hiding it.")


def _use_tool(world: World, hero: Entity, helper: Entity, tool: Tool, problem: Problem, item: Entity) -> None:
    if tool.id == "cloth":
        world.say(f"{hero.id} wiped the fuzzy spots away with {tool.phrase}.")
        world.say(f"Then {helper.label} showed {hero.id} how to open the window wide so the room could breathe.")
    elif tool.id == "box":
        world.say(f"{hero.id} tucked the snack into {tool.phrase}, and the lid shut with a firm click.")
        world.say(f"{helper.label} said a dry box keeps mold from sneaking back in.")
    elif tool.id == "patch":
        world.say(f"{hero.id} and {helper.label} used {tool.phrase} to seal the crack.")
        world.say(f"After that, the dripping stopped, and the wall felt strong again.")
    else:
        world.say(f"{hero.id} aimed {tool.phrase} at the dark corner so they could work carefully.")


def _lesson(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["understanding"] += 1
    hero.memes["calm"] += 1
    world.say(f"{hero.id} learned that mold likes damp, closed-up places.")
    world.say(f"{helper.label} smiled and said the lesson was simple: keep things dry, sealed, and checked often.")


def tell(place: Place, problem: Problem, tool: Tool, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"trait_word": random.choice(TRAITS)}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the ghost" if helper_type == "ghost" else "grandma", meters={}, memes={}))
    item = world.add(Entity(id="snack", type="snack", label="the snack box", phrase="a snack box", caretaker=hero.id))

    world.facts.update(hero=hero, helper=helper, problem=problem, tool=tool, item=item)

    _intro(world, hero, helper, problem)
    world.para()
    _problem_turn(world, hero, helper, problem, item)
    _use_tool(world, hero, helper, tool, problem, item)
    world.para()
    _lesson(world, hero, helper, problem)
    world.say(f"In the end, the room felt cleaner, the air felt lighter, and the firm old house stayed safe.")
    world.say(f"{hero.id} went to sleep knowing the mold would not win tonight.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a young child about {f["hero"].id}, a firm old place, and mold in a dark corner.',
        f'Tell a short story where {f["hero"].id} and a ghost solve a mold problem with a careful tool and learn a lesson.',
        f'Write a child-friendly spooky story that ends with a lesson learned about keeping things dry and sealed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, problem, tool = f["hero"], f["helper"], f["problem"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Where did {hero.id} find the mold?",
            answer=f"{hero.id} found the mold in {world.place.label}, in a dark corner that felt damp and musty.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the problem?",
            answer=f"The {helper.type} helped {hero.id} solve the problem by pointing out the mold and staying calm.",
        ),
        QAItem(
            question=f"What tool did {hero.id} use to fix it?",
            answer=f"{hero.id} used {tool.phrase} to deal with the mold problem.",
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer="The child learned that mold likes damp, closed-up places, so things should be kept dry, sealed, and checked often.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mold?",
            answer="Mold is a kind of fuzzy growth that can appear in damp places and on old food.",
        ),
        QAItem(
            question="Why is a firm house useful?",
            answer="A firm house stays strong and safe, so it can protect the people inside even when the corners are spooky.",
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means looking at a trouble, thinking carefully, and choosing a good way to fix it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="old_house", problem="mold", tool="cloth", child_name="Mina", child_type="girl", helper_type="ghost"),
    StoryParams(place="cellar", problem="mold", tool="box", child_name="Theo", child_type="boy", helper_type="ghost"),
    StoryParams(place="attic", problem="wet_wall", tool="patch", child_name="Nora", child_type="girl", helper_type="ghost"),
]


def resolve_helper_story(world: World, params: StoryParams) -> StorySample:
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(TOOLS, params.tool),
                 params.child_name, params.child_type, params.helper_type)
    return resolve_helper_story(world, params)


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
        print(f"{len(stories)} compatible stories:")
        for p, pr, t in stories:
            print(f"  {p:10} {pr:10} {t:10}")
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.problem} at {p.place} using {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
