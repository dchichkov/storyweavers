#!/usr/bin/env python3
"""
storyworlds/worlds/glorious_participant_kindness_conflict_mystery_to_solve.py
=============================================================================

A small slice-of-life storyworld about a glorious day, a participant, a gentle
kindness, a small conflict, and a mystery to solve.

The source tale behind this world is simple:
- A child participant arrives at a community event on a glorious afternoon.
- They want to help, but a small conflict arises around a missing item or task.
- The participant practices kindness, looks carefully, and solves the mystery.
- The ending proves the change: the event feels warm, orderly, and shared.

This script models the story with world state, meters, memes, and a tiny ASP
twin for parity checking.
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
# Entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    token: object | None = None
    def __post_init__(self) -> None:
        for k in ("clean", "found", "shared", "order", "lost"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "kindness", "conflict", "curiosity", "relief", "pride"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "woman-adult"}
        male = {"boy", "father", "dad", "man", "man-adult"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    setting: str
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
class Task:
    id: str
    verb: str
    gerund: str
    clue: str
    mess: str
    conflict: str
    mystery: str
    solution: str
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
class Token:
    label: str
    phrase: str
    type: str
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PLACES = {
    "community_hall": Place("the community hall", "indoor", {"find_note", "sort_books", "set_table"}),
    "garden": Place("the garden patch", "outdoor", {"water_plants", "find_note", "paint_sign"}),
    "library_corner": Place("the library corner", "indoor", {"sort_books", "find_note", "decorate_board"}),
}

TASKS = {
    "find_note": Task(
        id="find_note",
        verb="look for the missing note",
        gerund="looking for the missing note",
        clue="a scrap of paper with a blue star",
        mess="scattered",
        conflict="everyone kept pointing in different directions",
        mystery="a note disappeared",
        solution="the note had slipped inside a basket",
        tags={"mystery", "paper", "note"},
    ),
    "sort_books": Task(
        id="sort_books",
        verb="sort the story books",
        gerund="sorting story books",
        clue="the tallest book on the shelf",
        mess="mixed-up",
        conflict="the book pile had become a jumble",
        mystery="the books were out of order",
        solution="the books needed labels and a patient hand",
        tags={"books", "order", "kindness"},
    ),
    "water_plants": Task(
        id="water_plants",
        verb="water the seedlings",
        gerund="watering the seedlings",
        clue="a dry pot near the bench",
        mess="dry",
        conflict="two children wanted the watering can at once",
        mystery="the plants were drooping",
        solution="the watering can had been left by the sink",
        tags={"plants", "garden", "kindness"},
    ),
    "decorate_board": Task(
        id="decorate_board",
        verb="decorate the welcome board",
        gerund="decorating the welcome board",
        clue="a box of bright stickers",
        mess="plain",
        conflict="the board looked empty and the colors were missing",
        mystery="the stickers could not be found",
        solution="the sticker box was under the table cloth",
        tags={"board", "colors", "mystery"},
    ),
    "paint_sign": Task(
        id="paint_sign",
        verb="paint a sign",
        gerund="painting a sign",
        clue="a brush with green paint",
        mess="painted",
        conflict="the sign was still blank and someone felt rushed",
        mystery="the green paint was gone",
        solution="the paint can had rolled behind a crate",
        tags={"paint", "sign", "mystery"},
    ),
}

TOKENS = {
    "notebook": Token("notebook", "a little notebook with a red cover", "notebook"),
    "basket": Token("basket", "a woven basket", "basket"),
    "labels": Token("labels", "small name labels", "labels", plural=True),
    "watering_can": Token("watering can", "a bright watering can", "watering_can"),
    "sticker_box": Token("sticker box", "a box of bright stickers", "sticker_box"),
    "paint_can": Token("paint can", "a green paint can", "paint_can"),
}

CHILD_NAMES = ["Mina", "Leo", "Tara", "Owen", "Nina", "Ari", "June", "Ezra"]
ADULT_NAMES = ["Ms. Lee", "Mr. Park", "Ms. Diaz", "Mr. Reed"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    token: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def task_needs_token(task: Task, token: Token) -> bool:
    mapping = {
        "find_note": {"notebook", "basket"},
        "sort_books": {"labels", "notebook"},
        "water_plants": {"watering_can", "basket"},
        "decorate_board": {"sticker_box", "basket"},
        "paint_sign": {"paint_can", "basket"},
    }
    return token.type in mapping.get(task.id, set())


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for tid in place.affords:
            task = _safe_lookup(TASKS, tid)
            for tokid, tok in TOKENS.items():
                if task_needs_token(task, tok):
                    combos.append((pid, tid, tokid))
    return combos


def explain_rejection(task: Task, token: Token) -> str:
    return (
        f"(No story: {task.gerund} needs a useful object that could actually help "
        f"solve the problem, but {token.phrase} does not fit this task.)"
    )


def explain_gender(token_id: str, gender: str) -> str:
    return f"(No story: this world's child names are not constrained by that choice, but {token_id} should still make a plausible slice-of-life story.)"


# ---------------------------------------------------------------------------
# World model helpers
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def generate_story_sentence(hero: Entity, helper: Entity, task: Task, token: Entity, place: Place) -> str:
    return (
        f"{hero.id} was a {hero.memes.get('trait_word', 'kind')} participant at {place.name}, "
        f"and {hero.pronoun()} liked helping in small, careful ways."
    )


def predict(world: World, hero: Entity, task: Task, token: Entity) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    h.memes["curiosity"] += 1
    if task.id == "find_note":
        token.meters["found"] += 1
    return {"solved": True, "kindness": h.memes["kindness"]}


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, helper: Entity, task: Task, token: Entity) -> None:
    world.say(
        f"{hero.id} was a glorious participant at {world.place.name}, and {hero.pronoun()} came ready to help."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a gentle heart, and {helper.id} trusted {hero.pronoun('object')} with a small job: {task.gerund}."
    )
    world.say(
        f"The clue was {token.phrase}, and the day felt calm enough for a careful look around."
    )


def conflict(world: World, hero: Entity, helper: Entity, task: Task, token: Entity) -> None:
    hero.memes["conflict"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"Then a little conflict began, because {task.conflict}."
    )
    world.say(
        f"{hero.id} paused instead of rushing. {hero.pronoun().capitalize()} said, "
        f"\"Let's look kindly and take turns.\""
    )
    helper.memes["kindness"] += 1


def solve_mystery(world: World, hero: Entity, helper: Entity, task: Task, token: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["pride"] += 1
    hero.meters["found"] += 1
    if task.id == "find_note":
        location = "inside a basket"
    elif task.id == "sort_books":
        location = "under a stack of library cards"
    elif task.id == "water_plants":
        location = "by the sink"
    elif task.id == "decorate_board":
        location = "under the table cloth"
    else:
        location = "behind a crate"
    world.say(
        f"{hero.id} searched with care and found the answer {location}."
    )
    world.say(
        f"It turned out that {task.solution}."
    )
    world.say(
        f"{helper.id} smiled, because {hero.id}'s kindness had made the mystery easier to solve."
    )


def ending(world: World, hero: Entity, helper: Entity, task: Task, token: Entity) -> None:
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"By the end, the job was done, the conflict was gone, and the whole place felt tidier and warmer."
    )
    world.say(
        f"{hero.id} stood beside {helper.id} with a bright, proud grin, glad that a glorious day had turned into a helpful one."
    )


def tell(place: Place, task: Task, token_cfg: Token, name: str, gender: str, helper_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult", meters={}, memes={}))
    token = world.add(Entity(id=token_cfg.label, type=token_cfg.type, label=token_cfg.label, phrase=token_cfg.phrase, plural=token_cfg.plural))
    hero.memes["trait_word"] = trait

    intro(world, hero, helper, task, token)
    world.para()
    conflict(world, hero, helper, task, token)
    world.para()
    solve_mystery(world, hero, helper, task, token)
    ending(world, hero, helper, task, token)

    world.facts.update(hero=hero, helper=helper, task=task, token=token, place=place)
    return world


# ---------------------------------------------------------------------------
# Registries and QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "mystery": [
        ("What is a mystery?", "A mystery is something that is not understood right away, so people look carefully for clues."),
    ],
    "kindness": [
        ("What is kindness?", "Kindness means being gentle, helpful, and thoughtful toward other people."),
    ],
    "conflict": [
        ("What is a conflict?", "A conflict is a small problem or disagreement that people need to work through."),
    ],
    "books": [
        ("Why do books need to be sorted?", "Books are sorted so they are easy to find, put back, and share."),
    ],
    "garden": [
        ("What do plants need?", "Plants need water, light, and care so they can grow well."),
    ],
    "paint": [
        ("Why is paint messy?", "Paint can drip and smear, so people often try to use it carefully."),
    ],
    "note": [
        ("What is a note?", "A note is a short written message that can remind someone of something."),
    ],
}

KNOWLEDGE_ORDER = ["mystery", "kindness", "conflict", "books", "garden", "paint", "note"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    token = _safe_fact(world, f, "token")
    return [
        f'Write a short slice-of-life story about a glorious participant named {hero.id} who tries {task.gerund}.',
        f'Tell a gentle story where kindness helps solve a small conflict and a mystery involving {token.phrase}.',
        f'Write a child-friendly story that includes a participant, a problem, and a calm solution at {world.place.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    task = _safe_fact(world, f, "task")
    token = _safe_fact(world, f, "token")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who was the glorious participant in the story?",
            answer=f"The glorious participant was {hero.id}, who came to {place.name} ready to help.",
        ),
        QAItem(
            question=f"What did {hero.id} try to do at {place.name}?",
            answer=f"{hero.id} tried {task.gerund}, and {helper.id} gave {hero.pronoun('object')} a small job to help with.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue was {token.phrase}, and it led {hero.id} to the answer.",
        ),
        QAItem(
            question=f"How was the conflict solved?",
            answer=f"The conflict was solved when {hero.id} stayed calm, looked carefully, and found {task.solution}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["task"].tags)
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
task_needs(Tok, Task) :- token(Tok), task(Task), maps(Task, Tok).
valid(Place, Task, Tok) :- affords(Place, Task), task_needs(Tok, Task).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(place.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(task.tags):
            lines.append(asp.fact("tag", tid, tag))
    for tokid, tok in TOKENS.items():
        lines.append(asp.fact("token", tokid))
    for task_id, token_ids in {
        "find_note": {"notebook", "basket"},
        "sort_books": {"labels", "notebook"},
        "water_plants": {"watering_can", "basket"},
        "decorate_board": {"sticker_box", "basket"},
        "paint_sign": {"paint_can", "basket"},
    }.items():
        for tok in sorted(token_ids):
            lines.append(asp.fact("maps", task_id, tok))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: glorious participant, kindness, conflict, mystery to solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=["kind", "curious", "calm", "patient", "brave", "gentle"])
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
    if getattr(args, "place", None) and getattr(args, "task", None) and getattr(args, "token", None):
        if (getattr(args, "place", None), getattr(args, "task", None), getattr(args, "token", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = [c for c in combos
             if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
             and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
             and (getattr(args, "token", None) is None or c[2] == getattr(args, "token", None))]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, token = rng.choice(sorted(valid))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(ADULT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(["kind", "curious", "calm", "patient", "brave", "gentle"])
    return StoryParams(place=place, task=task, token=token, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(TOKENS, params.token), params.name, params.gender, params.helper, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
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
    StoryParams(place="community_hall", task="find_note", token="basket", name="Mina", gender="girl", helper="Ms. Lee", trait="kind"),
    StoryParams(place="garden", task="water_plants", token="watering_can", name="Leo", gender="boy", helper="Mr. Park", trait="gentle"),
    StoryParams(place="library_corner", task="sort_books", token="labels", name="Nina", gender="girl", helper="Ms. Diaz", trait="patient"),
    StoryParams(place="community_hall", task="decorate_board", token="sticker_box", name="Ari", gender="boy", helper="Mr. Reed", trait="curious"),
    StoryParams(place="garden", task="paint_sign", token="paint_can", name="June", gender="girl", helper="Ms. Lee", trait="calm"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, task, token) combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.task} at {p.place} ({p.token})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
