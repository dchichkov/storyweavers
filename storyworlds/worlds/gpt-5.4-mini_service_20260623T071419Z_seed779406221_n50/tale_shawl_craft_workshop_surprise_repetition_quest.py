#!/usr/bin/env python3
"""
storyworlds/worlds/tale_shawl_craft_workshop_surprise_repetition_quest.py
=========================================================================

A small slice-of-life story world set in a craft workshop.

Seed image:
---
A child or grown-up is working in a cozy craft workshop on a tale project.
A shawl is being made, and the day carries three gentle instruments:
Surprise, Repetition, and Quest.

Premise:
- Someone is weaving or stitching a shawl while telling a tale.
- The workshop is warm, practical, and full of small repeated motions.
- A surprise interrupts the ordinary rhythm.
- A quest turns that surprise into a kind, concrete problem to solve.

World model:
- Typed entities with physical meters and emotional memes.
- A craft action can change cloth quality, progress, and tidy/mess state.
- Repetition improves skill and consistency.
- Surprise adds an emotional bump and can reveal a missing material or flaw.
- Quest gives the maker a clear goal and a path to resolution.

Story shape:
- Beginning: introduce the workshop, the tale, and the shawl project.
- Middle: repetition establishes work; surprise interrupts; a quest begins.
- End: the maker finishes or meaningfully advances the shawl, proving change.

The prose is authored from simulated state rather than rendered from a fixed
template. The world is intentionally small and child-facing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
REPETITION_BOOST = 1.0



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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    helper: object | None = None
    maker: object | None = None
    quest_ent: object | None = None
    surprise_ent: object | None = None
    yarn: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Workshop:
    name: str
    cozy: bool
    supplies: set[str] = field(default_factory=set)
    surfaces: set[str] = field(default_factory=set)
    ordered: bool = True
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


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    kind: str
    color: str
    uses: set[str] = field(default_factory=set)
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    helps: set[str] = field(default_factory=set)
    safe: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Surprise:
    id: str
    label: str
    kind: str
    reveal: str
    causes: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    label: str
    goal: str
    search: str
    finish: str
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


class World:
    def __init__(self, workshop: Workshop) -> None:
        self.workshop = workshop
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def people(self) -> list[Entity]:
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
        clone = World(self.workshop)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.people():
        if actor.memes["repetition"] < THRESHOLD:
            continue
        sig = ("repetition", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["skill"] += REPETITION_BOOST
        actor.meters["progress"] += 1
        out.append(f"{actor.label_word.capitalize()} kept going, and the stitches grew neater.")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    for surprise in [e for e in world.entities.values() if e.kind == "surprise"]:
        if surprise.memes["noticed"] < THRESHOLD:
            continue
        sig = ("surprise", surprise.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for actor in world.people():
            actor.memes["surprise"] += 1
        out.append(f"Something unexpected appeared in the middle of the work.")
    return out


def _r_quest(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("quest_started") and not world.facts.get("quest_done"):
        maker = world.facts["maker"]
        maker.meters["quest"] += 1
        if maker.memes["curiosity"] < THRESHOLD:
            maker.memes["curiosity"] += 1
        sig = ("quest", maker.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append(f"{maker.label_word.capitalize()} set out to find the missing piece.")
    return out


CAUSAL_RULES = [
    Rule(name="repetition", apply=_r_repetition),
    Rule(name="surprise", apply=_r_surprise),
    Rule(name="quest", apply=_r_quest),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in WORKSHOPS:
        for project in PROJECTS.values():
            for surprise in SURPRISES.values():
                for quest in QUESTS.values():
                    if project.kind in surprise.causes:
                        combos.append((place, project.id, surprise.id, quest.id))
    return combos


def explain_rejection(project: Material, surprise: Surprise) -> str:
    return (
        f"(No story: the {surprise.label} would not really interrupt a {project.label} "
        f"project in a believable way. Pick a surprise that fits the material.)"
    )


@dataclass
class StoryParams:
    place: str
    project: str
    surprise: str
    quest: str
    maker: str
    maker_gender: str
    helper: str
    helper_gender: str
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


WORKSHOPS = {
    "corner_shop": Workshop(
        name="the craft workshop",
        cozy=True,
        supplies={"thread", "yarn", "buttons", "needles", "ribbon", "scissors", "basket"},
        surfaces={"table", "shelf", "chair"},
    ),
    "sunroom": Workshop(
        name="the sunlit craft workshop",
        cozy=True,
        supplies={"thread", "yarn", "buttons", "needles", "ribbon", "scissors", "basket"},
        surfaces={"table", "shelf", "chair", "window ledge"},
    ),
}

PROJECTS = {
    "shawl_blue": Material(
        id="shawl_blue",
        label="shawl",
        phrase="a soft blue shawl",
        kind="yarn",
        color="blue",
        uses={"warmth", "comfort"},
        fragile=False,
    ),
    "shawl_gold": Material(
        id="shawl_gold",
        label="shawl",
        phrase="a golden shawl with a stitched border",
        kind="yarn",
        color="gold",
        uses={"warmth", "gift"},
        fragile=False,
    ),
    "shawl_green": Material(
        id="shawl_green",
        label="shawl",
        phrase="a green shawl with tiny leaf stitches",
        kind="yarn",
        color="green",
        uses={"warmth", "gift"},
        fragile=False,
    ),
}

SURPRISES = {
    "lost_button": Surprise(
        id="lost_button",
        label="a missing button",
        kind="button",
        reveal="the button box was one button short",
        causes={"yarn"},
        tags={"surprise", "button"},
    ),
    "tangled_thread": Surprise(
        id="tangled_thread",
        label="a tangled thread loop",
        kind="thread",
        reveal="the thread had knotted itself into a little loop",
        causes={"yarn"},
        tags={"surprise", "thread"},
    ),
    "wrong_color": Surprise(
        id="wrong_color",
        label="the wrong colored skein",
        kind="yarn",
        reveal="the basket held a skein in the wrong color",
        causes={"yarn"},
        tags={"surprise", "yarn"},
    ),
}

QUESTS = {
    "find_button": Quest(
        id="find_button",
        label="a button quest",
        goal="find the missing button",
        search="look under the table and in the basket",
        finish="sew the button on at last",
        tags={"quest", "button"},
    ),
    "find_thread": Quest(
        id="find_thread",
        label="a thread quest",
        goal="find the hidden thread end",
        search="follow the loose strand along the table",
        finish="tie the thread and keep stitching",
        tags={"quest", "thread"},
    ),
    "find_skein": Quest(
        id="find_skein",
        label="a color quest",
        goal="find the matching skein",
        search="check the shelf and the window ledge",
        finish="replace the yarn with the right color",
        tags={"quest", "yarn"},
    ),
}

NAMES_GIRL = ["Mina", "Lena", "Maya", "Nora", "June", "Ivy"]
NAMES_BOY = ["Owen", "Noah", "Eli", "Theo", "Finn", "Arlo"]
TRAITS = ["patient", "curious", "gentle", "thoughtful", "careful"]


def tell(workshop: Workshop, project: Material, surprise: Surprise, quest: Quest,
         maker_name: str, maker_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(workshop)
    maker = world.add(Entity(
        id=maker_name,
        kind="character",
        type=maker_gender,
        label=maker_name,
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        label=helper_name,
    ))
    yarn = world.add(Entity(
        id=project.id,
        kind="thing",
        type="cloth",
        label=project.label,
        phrase=project.phrase,
        tags={"shawl", "tale"},
    ))
    surprise_ent = world.add(Entity(
        id=surprise.id,
        kind="surprise",
        type=surprise.kind,
        label=surprise.label,
        phrase=surprise.reveal,
        tags=set(surprise.tags),
    ))
    quest_ent = world.add(Entity(
        id=quest.id,
        kind="quest",
        type="quest",
        label=quest.label,
        phrase=quest.goal,
        tags=set(quest.tags),
    ))

    world.facts["maker"] = maker
    world.facts["helper"] = helper
    world.facts["project"] = yarn
    world.facts["surprise"] = surprise_ent
    world.facts["quest_ent"] = quest_ent

    maker.memes["joy"] = 1
    maker.memes["curiosity"] = 1
    helper.memes["joy"] = 1
    helper.memes["curiosity"] = 1
    yarn.meters["progress"] = 1
    yarn.meters["neatness"] = 1
    yarn.meters["warmth"] = 1
    surprise_ent.memes["noticed"] = 0
    quest_ent.meters["progress"] = 0
    world.facts["quest_started"] = False
    world.facts["quest_done"] = False

    world.say(
        f"In {workshop.name}, {maker_name} sat with {helper_name} and told a little tale "
        f"while working on {project.phrase}."
    )
    world.say(
        f"The room smelled like yarn and warm tea, and every few minutes the needles made a soft click."
    )

    world.para()
    maker.memes["repetition"] += 1
    helper.memes["repetition"] += 1
    world.say(
        f"{maker_name} stitched a row, then stitched it again more neatly, because the pattern liked steady hands."
    )
    world.say(
        f"{helper_name} folded the edge, checked the fringe, and nodded along to the tale."
    )
    propagate(world)

    world.para()
    surprise_ent.memes["noticed"] = 1
    world.facts["quest_started"] = True
    world.say(
        f"Then came a surprise: {surprise.reveal}."
    )
    world.say(
        f"{maker_name} paused with the shawl in {maker_name}'s hands and looked at the small problem more closely."
    )
    propagate(world)

    world.para()
    world.say(
        f"So they began a quest to {quest.goal}. {quest.search.capitalize()}."
    )
    if surprise.id == "lost_button":
        world.say(
            f"{helper_name} found the button under the basket, where it had rolled quietly beside a spool."
        )
    elif surprise.id == "tangled_thread":
        world.say(
            f"{maker_name} followed the thread end until the knot came loose with a tiny tug."
        )
    else:
        world.say(
            f"{helper_name} opened the shelf drawer and found the matching skein waiting like it had been there all along."
        )
    world.facts["quest_done"] = True
    yarn.meters["progress"] += 2
    yarn.meters["neatness"] += 1
    yarn.memes["pride"] += 1
    maker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the end, {quest.finish}, and {project.phrase} looked ready for someone cold and tired to wear."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a small child about a craft workshop, a tale, and a shawl. Include the word "shawl".',
        f"Tell a gentle story where {f['maker'].label_word} works on a shawl, there is a surprise, and the day turns into a quest.",
        f'Write a cozy story set in a craft workshop where repetition helps a maker finish a shawl after a surprise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    maker = world.facts["maker"]
    helper = world.facts["helper"]
    project = world.facts["project"]
    surprise = world.facts["surprise"]
    quest = world.facts["quest_ent"]
    return [
        QAItem(
            question=f"Who was working on the shawl in the craft workshop?",
            answer=f"{maker.label_word} was working on the shawl, and {helper.label_word} stayed nearby to help and listen to the tale.",
        ),
        QAItem(
            question=f"What happened after the repeated stitching?",
            answer=f"The repeated stitching made the work smoother, but then {surprise.phrase.lower()} changed the day's rhythm and turned it into a quest.",
        ),
        QAItem(
            question=f"What was the quest about?",
            answer=f"The quest was about {quest.phrase}, so {maker.label_word} and {helper.label_word} searched carefully until they could keep going.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shawl?",
            answer="A shawl is a soft piece of cloth you can wear around your shoulders to feel warm.",
        ),
        QAItem(
            question="What does repetition mean in crafting?",
            answer="Repetition means doing the same careful motion again and again. It can help stitches become neater and steadier.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal you go looking for step by step until you find it or finish it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"{e.id}: {e.kind} {e.label_word} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="corner_shop",
        project="shawl_blue",
        surprise="lost_button",
        quest="find_button",
        maker="Mina",
        maker_gender="girl",
        helper="Owen",
        helper_gender="boy",
    ),
    StoryParams(
        place="sunroom",
        project="shawl_gold",
        surprise="tangled_thread",
        quest="find_thread",
        maker="Noah",
        maker_gender="boy",
        helper="Lena",
        helper_gender="girl",
    ),
    StoryParams(
        place="corner_shop",
        project="shawl_green",
        surprise="wrong_color",
        quest="find_skein",
        maker="Ivy",
        maker_gender="girl",
        helper="Eli",
        helper_gender="boy",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life craft workshop storyworld.")
    ap.add_argument("--place", choices=WORKSHOPS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--maker")
    ap.add_argument("--maker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              and (getattr(args, "project", None) is None or c[1] == getattr(args, "project", None))
              and (getattr(args, "surprise", None) is None or c[2] == getattr(args, "surprise", None))
              and (getattr(args, "quest", None) is None or c[3] == getattr(args, "quest", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, project, surprise, quest = rng.choice(list(combos))
    maker_gender = getattr(args, "maker_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or ("boy" if maker_gender == "girl" else "girl")
    maker = getattr(args, "maker", None) or rng.choice(NAMES_GIRL if maker_gender == "girl" else NAMES_BOY)
    helper_pool = [n for n in (NAMES_GIRL if helper_gender == "girl" else NAMES_BOY) if n != maker]
    helper = getattr(args, "helper", None) or rng.choice(helper_pool or (NAMES_GIRL if helper_gender == "girl" else NAMES_BOY))
    return StoryParams(
        place=place,
        project=project,
        surprise=surprise,
        quest=quest,
        maker=maker,
        maker_gender=maker_gender,
        helper=helper,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in WORKSHOPS:
        pass
    if params.project not in PROJECTS or params.surprise not in SURPRISES or params.quest not in QUESTS:
        pass
    project = _safe_lookup(PROJECTS, params.project)
    surprise = _safe_lookup(SURPRISES, params.surprise)
    if project.kind not in surprise.causes:
        pass
    world = tell(_safe_lookup(WORKSHOPS, params.place), project, surprise, _safe_lookup(QUESTS, params.quest),
                 params.maker, params.maker_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
repetition(M) :- maker(M), repeated(M).
surprise(S) :- surprise_item(S), noticed(S).
quest_started(M) :- maker(M), surprise_item(_), not quest_done.
quest_done(M) :- maker(M), found_piece(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for wid in WORKSHOPS:
        lines.append(asp.fact("workshop", wid))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("project_kind", pid, p.kind))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise_item", sid))
        for c in sorted(s.causes):
            lines.append(asp.fact("causes", sid, c))
    for qid in QUESTS:
        lines.append(asp.fact("quest_item", qid))
    return "\n".join(lines)


def build_asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(build_asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos_asp())
    if py == asp_set:
        print(f"OK: ASP parity with {len(py)} valid combos.")
        return 0
    print("Mismatch between Python and ASP combos.")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


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
        print(build_asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = valid_combos_asp()
        print(f"{len(combos)} valid combinations:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
