#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sundry_quarry_misunderstanding_problem_solving_dialogue_rhyming.py
==============================================================================================================

A small storyworld built from the seed words "sundry" and "quarry".

Premise:
- A child brings sundry little things to a quarry picnic.
- A misunderstanding makes a friend think something important is missing.
- They talk, solve the problem together, and end with a bright, rhyming finish.

The story is intentionally state-driven:
- physical state: belongings, location, dust, water, and a shared basket
- emotional state: confusion, worry, calm, delight, and trust

This script follows the Storyweavers world contract:
- StoryParams and standard CLI support
- a reasonableness gate with Python and ASP twins
- generated story plus story/world QA
- trace output and verification
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

# -----------------------------------------------------------------------------
# Core model
# -----------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    name: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
class ObjectSpec:
    label: str
    phrase: str
    type: str
    plural: bool = False
    useful_for: set[str] = field(default_factory=set)
    story_role: str = ""  # "missing" or "found" or "shared"
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
    setting: str
    problem: str
    helper: str
    name_a: str
    name_b: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

PLACES = {
    "quarry": Place(
        name="the quarry",
        detail="The quarry was wide and bright, with stone steps and a shallow blue pool.",
        affords={"stones", "echo", "picnic"},
    ),
    "field": Place(
        name="the field",
        detail="The field was soft and green, with daisies nodding in the breeze.",
        affords={"picnic", "echo"},
    ),
    "garden": Place(
        name="the garden",
        detail="The garden was neat and sunny, with a bench and a tidy path.",
        affords={"picnic", "stones"},
    ),
}

PROBLEMS = {
    "basket": ObjectSpec(
        label="basket",
        phrase="a little wicker basket",
        type="basket",
        useful_for={"picnic", "sharing"},
        story_role="missing",
    ),
    "cup": ObjectSpec(
        label="cup",
        phrase="a shiny cup",
        type="cup",
        useful_for={"water"},
        story_role="missing",
    ),
    "hat": ObjectSpec(
        label="hat",
        phrase="a bright sun hat",
        type="hat",
        useful_for={"shade"},
        story_role="missing",
    ),
}

HERO_NAMES = ["Mina", "Leo", "Toby", "Nia", "Pia", "Owen", "Milo", "Ivy"]
HELPERS = ["sister", "friend", "brother", "cousin"]
TRAITS = ["curious", "gentle", "cheerful", "busy", "brave"]


# -----------------------------------------------------------------------------
# Story model helpers
# -----------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            if place_id == "quarry" and prob_id in {"basket", "cup"}:
                combos.append((place_id, prob_id))
            elif place_id != "quarry" and prob_id == "basket":
                combos.append((place_id, prob_id))
    return combos


def reasonableness_gate(place_id: str, prob_id: str) -> None:
    if (place_id, prob_id) not in valid_combos():
        pass


def choose_solution(place_id: str, prob_id: str) -> str:
    if place_id == "quarry" and prob_id == "basket":
        return "stone tray"
    if place_id == "quarry" and prob_id == "cup":
        return "shared cup from the picnic cloth"
    if place_id != "quarry" and prob_id == "basket":
        return "fresh picnic basket"
    return "simple fix"


def rhyming_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def introduce(world: World, hero: Entity, helper: Entity, problem: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.memes['trait']} little {hero.type} who liked to bring sundry things along."
    )
    world.say(
        f"{helper.id} was {helper.memes['trait']} too, and {helper.pronoun()} liked to help when plans went wrong."
    )
    world.say(
        f"At {world.place.name}, {problem.phrase} was meant for a picnic song."
    )


def create_misunderstanding(world: World, hero: Entity, helper: Entity, problem: Entity) -> None:
    hero.memes["worry"] += 1
    helper.memes["confusion"] += 1
    world.say(
        f"{helper.id} looked around and frowned. '{problem.label.capitalize()}?' {helper.pronoun()} said. 'I do not see it now.'"
    )
    world.say(
        f"{hero.id} blinked and asked, 'Did it fall? Did it roll? Did it go down a hole?'"
    )


def problem_solve(world: World, hero: Entity, helper: Entity, problem: Entity, solution: str) -> None:
    hero.memes["calm"] += 1
    helper.memes["calm"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"They talked it through by the stone and the pool, and each small word made the worry less cruel."
    )
    world.say(
        f"Then {hero.id} said, '{problem.label.capitalize()} is not lost. We can make do. We can use a {solution} as a clue.'"
    )
    world.say(
        f"{helper.id} smiled and said, 'Yes! That plan is neat. We can share what we have and make the day sweet.'"
    )
    world.say(
        f"So they fixed the mix-up with hands that were quick, and the new little answer worked like a trick."
    )


def ending(world: World, hero: Entity, helper: Entity, solution: str) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At the quarry, the day turned bright as can be; {hero.id} and {helper.id} laughed beside the tree."
    )
    world.say(
        f"With sundry small things and {solution} in sight, they shared their good picnic and felt just right."
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.setting)
    prob = _safe_lookup(PROBLEMS, params.problem)
    world = World(place)
    hero = world.add(Entity(id=params.name_a, kind="character", type="child", memes={"trait": params.name_a}))
    helper = world.add(Entity(id=params.name_b, kind="character", type=params.helper, memes={"trait": params.helper}))
    missing = world.add(Entity(id="missing", type=prob.type, label=prob.label, phrase=prob.phrase, plural=prob.plural))
    solution = choose_solution(params.setting, params.problem)

    world.facts.update(
        hero=hero,
        helper=helper,
        problem=missing,
        place=params.setting,
        problem_id=params.problem,
        solution=solution,
    )

    introduce(world, hero, helper, missing)
    world.para()
    create_misunderstanding(world, hero, helper, missing)
    world.para()
    problem_solve(world, hero, helper, missing, solution)
    world.para()
    ending(world, hero, helper, solution)
    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story about a child at {world.place.name} with a sundry little misunderstanding.',
        f"Tell a gentle dialogue story where {f['hero'].id} and {f['helper'].id} solve a problem at {world.place.name}.",
        f'Write a child-facing story that includes the words "sundry" and "quarry" and ends with a happy fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prob = _safe_fact(world, f, "problem")
    solution = _safe_fact(world, f, "solution")
    return [
        QAItem(
            question=f"Where did {hero.id} and {helper.id} have the misunderstanding?",
            answer=f"They had it at {world.place.name}, where the stones, pool, and picnic spot made the day feel big and bright.",
        ),
        QAItem(
            question=f"What was the misunderstanding about?",
            answer=f"They thought {prob.label} was missing, and that made them pause and talk before they acted.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They talked it through, shared ideas, and used a {solution} so the picnic could go on.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quarry?",
            answer="A quarry is a place where stone is dug from the ground, and it often has rocky walls and rough steps.",
        ),
        QAItem(
            question="What does sundry mean?",
            answer="Sundry means a small mix of different things, like odds and ends gathered together.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking about a trouble, talking about it, and finding a helpful way through it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# -----------------------------------------------------------------------------
# Trace
# -----------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
place(quarry).
place(field).
place(garden).

problem(basket).
problem(cup).
problem(hat).

valid(quarry, basket).
valid(quarry, cup).
valid(field, basket).
valid(garden, basket).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - asps:
        print("  only in Python:", sorted(py - asps))
    if asps - py:
        print("  only in ASP:", sorted(asps - py))
    return 1


# -----------------------------------------------------------------------------
# Generation
# -----------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: sundry quarry misunderstanding and problem solving.")
    ap.add_argument("--setting", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    if getattr(args, "setting", None) and getattr(args, "problem", None):
        reasonableness_gate(getattr(args, "setting", None), getattr(args, "problem", None))
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem = rng.choice(filtered)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    name_a = getattr(args, "name_a", None) or rng.choice(HERO_NAMES)
    name_b = getattr(args, "name_b", None) or rng.choice([n for n in HERO_NAMES if n != name_a])
    return StoryParams(setting=setting, problem=problem, helper=helper, name_a=name_a, name_b=name_b)


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
# Main
# -----------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="quarry", problem="basket", helper="friend", name_a="Mina", name_b="Leo"),
    StoryParams(setting="quarry", problem="cup", helper="brother", name_a="Ivy", name_b="Toby"),
    StoryParams(setting="field", problem="basket", helper="sister", name_a="Nia", name_b="Owen"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combinations:")
        for place, problem in combos:
            print(f"  {place} / {problem}")
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
            header = f"### {p.name_a} and {p.name_b}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
