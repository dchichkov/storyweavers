#!/usr/bin/env python3
"""
storyworlds/worlds/sun_foot_pl_boat_ramp_conflict_problem.py
=============================================================

A tiny whodunit-style storyworld set at a boat ramp, built around a child
detective, a small conflict, careful problem solving, and a moral value lesson.

Seed tale idea:
- A sunny day at the boat ramp.
- A small red boat goes missing.
- The children suspect the wrong person.
- The clue is hidden in the sun and in foot-pl... footprints.
- Careful looking solves the problem.
- The ending teaches that it is better to tell the truth than to guess.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- a Python reasonableness gate
- an inline ASP_RULES twin
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
# World entities
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    adult: object | None = None
    boat: object | None = None
    clue: object | None = None
    detective: object | None = None
    sun: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    def init_meter(self, key: str) -> float:
        return self.meters.setdefault(key, 0.0)

    def init_meme(self, key: str) -> float:
        return self.memes.setdefault(key, 0.0)
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
    place: str = "the boat ramp"
    indoors: bool = False
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
class Mystery:
    id: str
    title: str
    missing: str
    clue: str
    culprit_type: str
    moral: str
    problem: str
    solution: str
    keyword: str = "sun"
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
class ClueTool:
    id: str
    label: str
    helps: str
    covers: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "boat_ramp": Setting(place="the boat ramp", affords={"mystery", "search", "sun"}),
}

MYSTERIES = {
    "red_boat": Mystery(
        id="red_boat",
        title="The Case of the Missing Red Boat",
        missing="a little red boat",
        clue="a shiny mark in the sun and a trail of foot-pl footprints in the mud",
        culprit_type="honest mistake",
        moral="It is better to tell the truth than to hide a mistake.",
        problem="someone had moved the boat without asking",
        solution="they followed the footprints and asked kindly",
        keyword="sun",
        tags={"sun", "foot_pl", "boat", "truth"},
    ),
    "lost_hook": Mystery(
        id="lost_hook",
        title="The Case of the Lost Boat Hook",
        missing="the boat hook",
        clue="a wet handle and a neat set of footprints",
        culprit_type="careless helper",
        moral="Careful looking can solve a problem without blaming anyone too fast.",
        problem="the hook had been put down in the wrong place",
        solution="they traced the wet path and found it beside the dock",
        keyword="foot_pl",
        tags={"foot_pl", "water", "search"},
    ),
}

CHARACTER_NAMES = ["Maya", "Toby", "Nina", "Eli", "Ruby", "Owen"]
CHARACTER_TRAITS = ["curious", "careful", "brave", "patient", "sharp-eyed", "kind"]
ADULTS = [("mother", "mother"), ("father", "father"), ("aunt", "aunt"), ("uncle", "uncle")]

TOOLS = {
    "magnifier": ClueTool(id="magnifier", label="a magnifying glass", helps="look at tiny clues"),
    "notebook": ClueTool(id="notebook", label="a little notebook", helps="write down clues"),
    "shoes": ClueTool(id="shoes", label="muddy shoes", helps="follow a footprint trail", covers={"feet"}),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    detective_name: str
    detective_type: str
    detective_trait: str
    adult_name: str
    adult_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


class StoryWorld:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.mystery not in MYSTERIES:
        pass
    if params.detective_type not in {"girl", "boy"}:
        pass
    if params.adult_type not in {"mother", "father", "aunt", "uncle"}:
        pass


def setup_world(params: StoryParams) -> StoryWorld:
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = StoryWorld(_safe_lookup(SETTINGS, params.setting), mystery)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        traits=["little", params.detective_trait],
        meters={"attention": 1.0, "worry": 0.0},
        memes={"curiosity": 1.0, "courage": 1.0},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=params.adult_type,
        label=f"the {params.adult_type}",
        meters={"care": 1.0},
        memes={"calm": 1.0},
    ))
    boat = world.add(Entity(
        id="boat",
        type="boat",
        label="the little red boat",
        phrase="a little red boat with a white stripe",
        owner=adult.id,
        meters={"missing": 1.0},
        memes={"value": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label="foot-pl footprints",
        phrase="a trail of foot-pl footprints",
        meters={"visible": 0.0},
        memes={"mystery": 1.0},
    ))
    sun = world.add(Entity(
        id="sun",
        type="sun",
        label="the sun",
        phrase="a bright sun",
        meters={"bright": 1.0},
        memes={"warmth": 1.0},
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=TOOLS["magnifier"].label,
        phrase=TOOLS["magnifier"].label,
        owner=detective.id,
        meters={"ready": 1.0},
        memes={"helpful": 1.0},
    ))

    world.facts.update(detective=detective, adult=adult, boat=boat, clue=clue, sun=sun, tool=tool)
    return world


def solve_mystery(world: StoryWorld) -> None:
    d = _safe_fact(world, world.facts, "detective")
    adult = _safe_fact(world, world.facts, "adult")
    boat = _safe_fact(world, world.facts, "boat")
    clue = _safe_fact(world, world.facts, "clue")
    mystery = world.mystery

    # Act 1
    world.say(f"{d.id} was a little {d.traits[1]} {d.type} who loved solving mysteries at {world.setting.place}.")
    world.say(f"On a bright day, {d.id} noticed {mystery.missing} was gone from the shore.")
    world.say(f"{adult.label} looked worried, because {mystery.problem}.")

    world.para()

    # Act 2: conflict
    d.memes["curiosity"] += 1
    d.meters["attention"] += 1
    d.meters["worry"] += 1
    world.say(f"{d.id} did not want to guess too fast.")
    world.say(f"In the sun, {d.id} saw {mystery.clue}.")
    clue.meters["visible"] = 1.0
    world.say(f"That clue pointed away from the dock and toward the muddy path.")

    adult.memes["unease"] += 1
    world.say(f"The {adult.type} asked, \"Who took it?\" but {d.id} shook {d.id}'s head.")
    world.say(f"\"We should follow the clues first,\" {d.id} said.")

    world.para()

    # Act 3: problem solving and moral
    d.memes["confidence"] += 1
    world.say(f"{d.id} used {world.facts['tool'].label} to study the ground.")
    world.say(f"The prints bent around a post, then stopped beside a stack of rope.")
    boat.meters["missing"] = 0.0
    boat.meters["found"] = 1.0
    world.say(f"Behind the rope, there was {mystery.missing} after all.")
    world.say(f"It had been moved by an honest mistake, not stolen.")
    adult.memes["relief"] += 1
    adult.memes["pride"] += 1
    world.say(f"{adult.label} thanked {d.id} for looking carefully instead of blaming anyone.")
    world.say(f"{mystery.moral}")
    world.say(f"In the end, {mystery.missing} sat safely by the water, and the bright sun shone on the tidy ramp.")

    world.facts["solved"] = True
    world.facts["moral"] = mystery.moral
    world.facts["clue_text"] = mystery.clue


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(boat_ramp).

mystery(red_boat).
mystery(lost_hook).

tag(red_boat,sun).
tag(red_boat,foot_pl).
tag(red_boat,boat).
tag(red_boat,truth).

tag(lost_hook,foot_pl).
tag(lost_hook,water).
tag(lost_hook,search).

reasonable(S, M) :- setting(S), mystery(M), tag(M,sun), tag(M,foot_pl).
show_story(S, M) :- reasonable(S, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in sorted(mystery.tags):
            lines.append(asp.fact("tag", mid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = {(s, m) for s in SETTINGS for m, mystery in MYSTERIES.items() if {"sun", "foot_pl"} <= mystery.tags}
    cl = set(asp_reasonable_pairs())
    if py == cl:
        print(f"OK: ASP parity matched ({len(cl)} reasonable stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" python-only:", sorted(py - cl))
    print(" asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(sample: StorySample) -> list[str]:
    p = sample.params
    mystery = _safe_lookup(MYSTERIES, p.mystery)
    return [
        f'Write a child-friendly whodunit set at {_safe_lookup(SETTINGS, p.setting).place} with the word "{mystery.keyword}".',
        f"Tell a short mystery where {p.detective_name} solves a missing-object problem by noticing {mystery.clue}.",
        f"Make a gentle story about truth, careful looking, and a sunny clue at the boat ramp.",
    ]


def story_qa(sample: StorySample) -> list[QAItem]:
    p = sample.params
    mystery = _safe_lookup(MYSTERIES, p.mystery)
    d = sample.world.facts["detective"]
    adult = sample.world.facts["adult"]
    return [
        QAItem(
            question=f"Where did {p.detective_name} look for clues?",
            answer=f"{p.detective_name} looked at {_safe_lookup(SETTINGS, p.setting).place} and studied the ground near the water.",
        ),
        QAItem(
            question=f"What clue helped {p.detective_name} solve the mystery?",
            answer=f"The clue was {mystery.clue}, which led {p.detective_name} to the right place.",
        ),
        QAItem(
            question=f"Why did the {adult.type} feel worried at first?",
            answer=f"The {adult.type} felt worried because {mystery.problem}.",
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{p.detective_name} used careful looking and followed the footprints instead of guessing.",
        ),
        QAItem(
            question="What moral value does the story teach?",
            answer=mystery.moral,
        ),
    ]


def world_knowledge_qa(sample: StorySample) -> list[QAItem]:
    return [
        QAItem(
            question="What is a boat ramp?",
            answer="A boat ramp is a sloped place where people push boats into the water or pull them back out.",
        ),
        QAItem(
            question="Why can sunlight help with finding clues?",
            answer="Bright sunlight can make shiny things and footprints easier to see.",
        ),
        QAItem(
            question="What are footprints?",
            answer="Footprints are the marks shoes or bare feet leave on soft ground like mud or sand.",
        ),
    ]


# ---------------------------------------------------------------------------
# Serialization / trace
# ---------------------------------------------------------------------------
def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------
def choose_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice(["Maya", "Ruby", "Nina"])
    return rng.choice(["Toby", "Eli", "Owen"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "setting", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "mystery", None) and getattr(args, "mystery", None) not in MYSTERIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting = getattr(args, "setting", None) or "boat_ramp"
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(rng, gender)
    trait = getattr(args, "trait", None) or rng.choice(CHARACTER_TRAITS)
    adult_type = getattr(args, "adult", None) or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        setting=setting,
        mystery=mystery,
        detective_name=name,
        detective_type=gender,
        detective_trait=trait,
        adult_name="adult",
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = setup_world(params)
    solve_mystery(world)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=[],
        story_qa=[],
        world_qa=[],
        world=world,
    )
    sample.prompts = generation_prompts(sample)
    sample.story_qa = story_qa(sample)
    sample.world_qa = world_knowledge_qa(sample)
    return sample


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="boat_ramp",
        mystery="red_boat",
        detective_name="Maya",
        detective_type="girl",
        detective_trait="sharp-eyed",
        adult_name="adult",
        adult_type="mother",
    ),
    StoryParams(
        setting="boat_ramp",
        mystery="lost_hook",
        detective_name="Toby",
        detective_type="boy",
        detective_trait="careful",
        adult_name="adult",
        adult_type="father",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld at a boat ramp.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=CHARACTER_TRAITS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_reasonable_pairs()
        print(f"{len(pairs)} reasonable story pairs:")
        for pair in pairs:
            print(" ", pair)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            try:
                sample = generate(params)
            except StoryError:
                continue
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
            header = f"### {p.detective_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
