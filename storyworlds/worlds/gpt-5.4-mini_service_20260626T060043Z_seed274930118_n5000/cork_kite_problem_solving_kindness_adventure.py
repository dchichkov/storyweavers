#!/usr/bin/env python3
"""
A standalone story world: a windy kite adventure where kindness and problem
solving turn a sticky problem into a happy flight.

The seed idea: a child wants to fly a kite, but the string keeps slipping.
A kind helper notices the trouble, offers a cork, and together they solve it.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core model
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
    traits: list[str] = field(default_factory=list)

    cork: object | None = None
    helper: object | None = None
    hero: object | None = None
    kite: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    place: str = "the windy hill"
    affords: set[str] = field(default_factory=set)
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
    issue: str
    verb: str
    result: str
    risk: str
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
class Fix:
    id: str
    label: str
    phrase: str
    helps: set[str]
    use: str
    outcome: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[list[str]] = [[]]
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
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.story = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    helper: str
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


SETTINGS = {
    "hill": Setting(place="the windy hill", affords={"kite"}),
    "beach": Setting(place="the bright beach", affords={"kite"}),
    "park": Setting(place="the open park", affords={"kite"}),
    "field": Setting(place="the green field", affords={"kite"}),
}

PROBLEMS = {
    "kite_string_slip": Problem(
        id="kite_string_slip",
        issue="the kite string kept slipping through little hands",
        verb="fly the kite",
        result="the kite wobbling and dipping",
        risk="the kite might crash and get stuck",
        keyword="kite",
        tags={"kite", "wind", "slip"},
    ),
    "kite_tangle": Problem(
        id="kite_tangle",
        issue="the kite line had gotten tangled in a low branch",
        verb="pull the kite free",
        result="the kite staying stuck and the string fraying",
        risk="the kite might tear",
        keyword="kite",
        tags={"kite", "tangle", "branch"},
    ),
}

FIXES = [
    Fix(
        id="cork_stopper",
        label="a cork",
        phrase="a smooth cork from a bottle",
        helps={"kite_string_slip"},
        use="thread the cork onto the string as a stopper",
        outcome="the line stopped sliding",
    ),
    Fix(
        id="gentle_pull",
        label="a careful pull",
        phrase="a careful pull together",
        helps={"kite_tangle"},
        use="lift the branch a little and pull the line slowly",
        outcome="the kite came loose without tearing",
    ),
    Fix(
        id="new_tail",
        label="a paper tail",
        phrase="a paper tail with bright strips",
        helps={"kite_string_slip"},
        use="tie on a short tail to steady the kite",
        outcome="the kite steadied in the breeze",
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Theo", "Ben", "Max", "Eli"]
TRAITS = ["curious", "brave", "cheerful", "patient", "thoughtful", "lively"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is reasonable for a place if the place supports kites.
problem_ok(P, Pr) :- setting(P), problem(Pr), gives_kite_wind(P).

% A fix is compatible if it helps that problem.
compatible(F, Pr) :- fix(F), problem(Pr), helps(F, Pr).

valid_story(P, Pr, F) :- problem_ok(P, Pr), compatible(F, Pr).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("gives_kite_wind", pid))
    for pr_id in PROBLEMS:
        lines.append(asp.fact("problem", pr_id))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for p in sorted(fx.helps):
            lines.append(asp.fact("helps", fx.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for prob_id in PROBLEMS:
            for fix in FIXES:
                if prob_id in fix.helps:
                    combos.append((place, prob_id, fix.id))
    return combos


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} does not really solve {problem.issue}. "
        f"Try a fix that actually matches the kite trouble.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def do_problem(world: World, hero: Entity, problem: Problem) -> None:
    if problem.id == "kite_string_slip":
        hero.meters["worry"] += 1
        hero.memes["frustration"] += 1
        world.say(
            f"At {world.setting.place}, {hero.id} tried to {problem.verb}, "
            f"but {problem.issue}."
        )
    elif problem.id == "kite_tangle":
        hero.meters["worry"] += 1
        hero.memes["frustration"] += 1
        world.say(
            f"At {world.setting.place}, {hero.id} tried to {problem.verb}, "
            f"but {problem.issue}."
        )


def choose_fix(problem: Problem) -> Fix:
    for fx in FIXES:
        if problem.id in fx.helps:
            return fx
    pass


def tell(setting: Setting, problem: Problem, fix: Fix,
         name: str, gender: str, parent: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=name, kind="character", type=gender, traits=["little", trait, "kind"],
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=parent, label=f"{parent}", traits=["kind", "helpful"]
    ))
    kite = world.add(Entity(id="kite", type="kite", label="kite", phrase="a bright kite"))
    cork = None

    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} was a little {trait} {gender} who loved adventure and liked to fly a kite."
    )
    world.say(
        f"{hero.id}'s {helper.label_word} smiled and said that a windy day was perfect for trying."
    )

    world.para()
    do_problem(world, hero, problem)
    world.say(
        f"{hero.id} frowned, because {problem.risk}."
    )

    world.para()
    helper.memes["kindness"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"Then the {helper.label_word} noticed the trouble and had a kind idea."
    )
    if fix.id == "cork_stopper":
        cork = world.add(Entity(
            id="cork", type="cork", label="cork", phrase="a smooth cork from a bottle"
        ))
        cork.owner = helper.id
        world.say(
            f"{helper.id} found {cork.phrase} in a pocket and showed {hero.id} how to use it."
        )
    elif fix.id == "gentle_pull":
        world.say(
            f"{helper.id} took a careful breath and told {hero.id} to pull together, slowly."
        )
    else:
        world.say(
            f"{helper.id} tied on a paper tail and said it would help the kite balance."
        )

    world.say(
        f"Together they chose to {fix.use}, and {fix.outcome}."
    )
    hero.memes["joy"] += 1
    hero.memes["gratitude"] += 1
    hero.meters["success"] += 1

    world.para()
    world.say(
        f"After that, the kite rose high and steady over {world.setting.place}, "
        f"and {hero.id} laughed beside the {helper.label_word}."
    )
    world.say(
        f"The little cork stayed tucked on the string, and the kite danced safely in the wind."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        kite=kite,
        cork=cork,
        problem=problem,
        fix=fix,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    return [
        f'Write a short adventure story about a child named {hero.id}, a kite, and a cork.',
        f"Tell a gentle problem-solving story where {hero.id} faces a kite problem and gets help.",
        f"Write a child-friendly adventure about kindness that includes the words 'kite' and 'cork'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    problem = _safe_fact(world, f, "problem")
    fix = _safe_fact(world, f, "fix")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to {problem.verb}.",
        ),
        QAItem(
            question=f"What was the trouble with the kite?",
            answer=f"The trouble was that {problem.issue}, so the kite could not stay easy and steady.",
        ),
        QAItem(
            question=f"Who noticed the problem and helped?",
            answer=f"The {helper.label_word} noticed the trouble and helped with a kind fix.",
        ),
        QAItem(
            question=f"What did they use to solve the problem?",
            answer=f"They used {fix.phrase} to make the kite work better.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the kite flying high and {hero.id} feeling happy and grateful.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kite?",
            answer="A kite is a light toy that catches the wind and can fly on a string.",
        ),
        QAItem(
            question="What is a cork?",
            answer="A cork is a light stopper, often made from bark, that can float and fit into a bottle.",
        ),
        QAItem(
            question="Why can kindness help solve problems?",
            answer="Kindness can help because a kind helper stays calm, notices trouble, and works together to fix it.",
        ),
        QAItem(
            question="Why do people like windy places for kites?",
            answer="People like windy places for kites because the wind can lift the kite and help it rise.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: kite, cork, kindness, problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=[f.id for f in FIXES])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "problem", None) and getattr(args, "fix", None):
        pr = _safe_lookup(PROBLEMS, getattr(args, "problem", None))
        fx = next(f for f in FIXES if f.id == getattr(args, "fix", None))
        if pr.id not in fx.helps:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, problem_id, fix_id = rng.choice(list(combos))
    problem = _safe_lookup(PROBLEMS, problem_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        problem=problem_id,
        helper=fix_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(PROBLEMS, params.problem),
        next(f for f in FIXES if f.id == params.helper),
        params.name, params.gender, params.parent, params.trait
    )
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


CURATED = [
    StoryParams(place="hill", problem="kite_string_slip", helper="cork_stopper", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="field", problem="kite_tangle", helper="gentle_pull", name="Leo", gender="boy", parent="father", trait="brave"),
]


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
        for p, pr, f in stories:
            print(f"  {p:10} {pr:16} {f}")
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
            header = f"### {p.name}: {p.problem} with {p.helper} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
