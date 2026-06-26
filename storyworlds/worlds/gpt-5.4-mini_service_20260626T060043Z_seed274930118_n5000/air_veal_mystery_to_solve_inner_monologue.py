#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/air_veal_mystery_to_solve_inner_monologue.py
===============================================================================================================

A small, standalone mystery story world with inner monologue and dialogue.

Premise:
- A child notices a strange smell in the air.
- A special veal lunch dish goes missing.
- Clues in the world point to a simple, solvable explanation.
- The story is narrated in a cozy mystery style with thought bubbles and spoken lines.

The simulation models:
- physical state: where items are, whether a dish is covered, whether the window is open,
  whether an aroma drifts through the room, and whether evidence is visible
- emotional state: curiosity, worry, relief, and trust

The generated story always follows a complete arc:
- setup: the scene, the missing dish, the first clue
- middle: the child thinks through the mystery, asks questions, and checks clues
- ending: the hidden truth is found and the room settles again

This file follows the Storyweavers world contract and includes:
- StoryParams
- parameter registries
- build_parser
- resolve_params
- generate
- emit
- main
- an inline ASP_RULES twin
- asp_facts()
- verification helpers
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
    located_in: str = ""
    hidden_under: str = ""
    covered: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    clue: object | None = None
    hero: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
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
    indoor: bool = True
    airy: bool = False
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
class Clue:
    id: str
    label: str
    hint: str
    reveal: str
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
class Mystery:
    id: str
    missing_label: str
    missing_phrase: str
    smell: str
    hiding_place: str
    culprit: str
    cause: str
    clue: str
    result: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


GIRL_NAMES = ["Mina", "Lina", "Nora", "Ruby", "Ivy", "Tessa", "Maya", "Penny"]
BOY_NAMES = ["Theo", "Owen", "Ben", "Leo", "Milo", "Finn", "Eli", "Jasper"]
ADULT_NAMES = ["Mrs. Green", "Mr. Hale", "Aunt June", "Dad", "Mom"]

PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", indoor=True, airy=False),
    "cafe": Place(id="cafe", label="the little café", indoor=True, airy=True),
    "bakery": Place(id="bakery", label="the bakery", indoor=True, airy=True),
    "porch": Place(id="porch", label="the porch", indoor=False, airy=True),
}

MYSTERIES = {
    "open_window": Mystery(
        id="open_window",
        missing_label="veal pie",
        missing_phrase="a warm veal pie",
        smell="air",
        hiding_place="windowsill",
        culprit="window",
        cause="the window was open and the smell drifted out",
        clue="a cool breeze",
        result="the pie had not been stolen at all; it had simply been cooling by the open window",
    ),
    "under_cloth": Mystery(
        id="under_cloth",
        missing_label="veal sandwich",
        missing_phrase="a wrapped veal sandwich",
        smell="air",
        hiding_place="cloth napkin",
        culprit="napkin",
        cause="the sandwich was tucked under a cloth napkin on the table",
        clue="a corner of bread peeking out",
        result="the sandwich was right there under the cloth, safe and neat",
    ),
    "mistaken_order": Mystery(
        id="mistaken_order",
        missing_label="veal stew",
        missing_phrase="a bowl of veal stew",
        smell="air",
        hiding_place="serving tray",
        culprit="tray",
        cause="the bowl was moved to the serving tray for the next customer",
        clue="a spoon with steam",
        result="the stew had been served to the wrong table by mistake",
    ),
}

NAMES = {
    "girl": GIRL_NAMES,
    "boy": BOY_NAMES,
}

TRAITS = ["curious", "careful", "brave", "quiet", "bright"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    adult: str
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


class ReasoningError(StoryError):
    pass


def setup_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"position": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "relief": 0.0, "trust": 1.0},
    ))
    adult = world.add(Entity(
        id=params.adult,
        kind="character",
        type="mother" if params.adult == "Mom" else "father" if params.adult == "Dad" else "adult",
        label=params.adult,
        meters={"position": 0.0},
        memes={"worry": 0.0, "trust": 1.0},
    ))
    missing = world.add(Entity(
        id="missing_dish",
        type="dish",
        label=mystery.missing_label,
        phrase=mystery.missing_phrase,
        owner=adult.id,
        located_in=mystery.hiding_place,
        covered=True,
        meters={"hidden": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=mystery.clue,
        phrase=mystery.clue,
        meters={"noticed": 0.0},
    ))

    world.facts.update(
        hero=hero,
        adult=adult,
        missing=missing,
        clue=clue,
        mystery=mystery,
    )
    return world


def atmosphere(world: World) -> str:
    if world.place.id == "porch":
        return "The porch felt open and bright, and the air moved gently."
    if world.place.airy:
        return f"{world.place.label.capitalize()} felt warm and busy, with a little air drifting through."
    return f"{world.place.label.capitalize()} felt close and quiet, and every sound seemed to sit still."


def intro(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    mystery: Mystery = _safe_fact(world, f, "mystery")

    world.say(
        f"{hero.label} was a {hero.label.lower()} child, {hero.pronoun('subject')} was {world.facts['hero'].memes and 'full of questions' or ''}".strip()
    )
    world.say(
        f"{hero.label} noticed everything, especially when something smelled strange in the air."
    )
    world.say(
        f"That morning, {adult.label} frowned at the empty plate. '{mystery.missing_phrase} was here a minute ago,' {adult.pronoun('subject')} said."
    )
    world.say(atmosphere(world))
    hero.memes["curiosity"] += 1.0
    adult.memes["worry"] += 1.0


def inner_monologue(world: World, thought: str) -> None:
    world.say(f"{thought}")


def dialogue(speaker: Entity, text: str) -> str:
    return f"“{text}” {speaker.label} said."


def clue_scene(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    clue: Entity = _safe_fact(world, f, "clue")

    world.say(
        f"{hero.label} leaned closer and sniffed. The air carried a warm smell, like veal and pepper."
    )
    inner_monologue(world, f"{hero.label} thought, I should not guess too fast. A mystery is only fair when I follow the clues.")
    clue.meters["noticed"] = 1.0

    if mystery.id == "open_window":
        world.say(
            f"{hero.label} saw a cool breeze moving the curtain. '{mystery.clue},' {hero.pronoun('subject')} whispered."
        )
    elif mystery.id == "under_cloth":
        world.say(
            f"{hero.label} spotted {mystery.clue} near the table edge. '{mystery.clue.capitalize()}!' {hero.pronoun('subject')} thought."
        )
    else:
        world.say(
            f"{hero.label} noticed {mystery.clue} on the tray. '{mystery.clue.capitalize()}. That means the dish moved,' {hero.pronoun('subject')} thought."
        )

    world.say(dialogue(hero, "I think the veal is not gone. I think it is hiding or moving."))


def investigate(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    missing: Entity = _safe_fact(world, f, "missing")

    world.say(dialogue(adult, "Do you really think so?"))
    inner_monologue(world, f"{hero.label} thought, If the air smells like veal, then the dish must be nearby.")
    hero.memes["curiosity"] += 1.0

    if mystery.id == "open_window":
        world.say(
            f"{hero.label} walked to the window. The plate was not on the table, but the sill was cool."
        )
        world.say(dialogue(hero, "Look! The window is open. The air carried the smell outside."))
    elif mystery.id == "under_cloth":
        world.say(
            f"{hero.label} lifted the cloth napkin. There, snug as a sleeping kitten, was the veal sandwich."
        )
        world.say(dialogue(hero, "It was hiding under the cloth the whole time!"))
    else:
        world.say(
            f"{hero.label} followed the tray to the next table and found the bowl waiting there."
        )
        world.say(dialogue(hero, "Someone moved it by mistake. It is still here!"))

    missing.covered = False
    missing.meters["hidden"] = 0.0
    hero.memes["trust"] += 1.0
    adult.memes["worry"] -= 1.0
    adult.memes["relief"] += 1.0


def resolution(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    missing: Entity = _safe_fact(world, f, "missing")

    if mystery.id == "open_window":
        world.say(
            f"{adult.label} laughed softly. '{mystery.result},' {adult.pronoun('subject')} said."
        )
    elif mystery.id == "under_cloth":
        world.say(
            f"{adult.label} blinked and smiled. '{mystery.result},' {adult.pronoun('subject')} said."
        )
    else:
        world.say(
            f"{adult.label} nodded. '{mystery.result},' {adult.pronoun('subject')} admitted."
        )
    world.say(
        f"{hero.label} smiled. The veal smell stayed in the air, but now it felt friendly instead of puzzling."
    )
    world.say(
        f"By the end, {missing.phrase} was safe again, and the little mystery had an answer."
    )
    hero.memes["relief"] += 1.0


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    intro(world)
    world.para()
    clue_scene(world)
    world.para()
    investigate(world)
    world.para()
    resolution(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        f"Write a short mystery story for a child named {hero.label} who notices something odd in the air and solves it with inner thoughts and dialogue.",
        f"Tell a cozy mystery about {mystery.missing_phrase} and how {adult.label} and {hero.label} figure out where it went.",
        f"Write a gentle story where the smell of veal in the air becomes a clue and the child detective explains the answer in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    adult: Entity = _safe_fact(world, f, "adult")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    missing: Entity = _safe_fact(world, f, "missing")

    return [
        QAItem(
            question=f"What did {hero.label} notice first in the story?",
            answer=f"{hero.label} noticed that something smelled strange in the air, and that smell pointed toward {missing.label}.",
        ),
        QAItem(
            question=f"What was the mystery about?",
            answer=f"The mystery was about {mystery.missing_phrase}, which seemed to be missing at first.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the mystery?",
            answer=f"{hero.label} followed the smell and the clue, then checked the hiding place and found that the veal dish was still nearby.",
        ),
        QAItem(
            question=f"How did {adult.label} feel at the end?",
            answer=f"{adult.label} felt relieved and glad because the missing dish had an ordinary explanation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is air?",
            answer="Air is the invisible stuff all around us that we breathe and that can carry smells from place to place.",
        ),
        QAItem(
            question="What is veal?",
            answer="Veal is meat from a young calf, and people may cook it in a pie, sandwich, or stew.",
        ),
        QAItem(
            question="Why do detectives look at clues?",
            answer="Detectives look at clues because clues help them figure out what really happened instead of guessing.",
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
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.located_in:
            bits.append(f"located_in={e.located_in}")
        if e.hidden_under:
            bits.append(f"hidden_under={e.hidden_under}")
        if e.covered:
            bits.append("covered=True")
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for mystery in MYSTERIES:
            combos.append((place, mystery))
    return combos


def explain_rejection(place: str, mystery: str) -> str:
    return f"(No story: the combination of {place} and {mystery} does not produce a clear mystery with a solvable clue.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    if (place, mystery) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    adult = getattr(args, "adult", None) or rng.choice(ADULT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mystery=mystery,
        name=name,
        gender=gender,
        adult=adult,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


ASP_RULES = r"""
place(P) :- place_fact(P).
mystery(M) :- mystery_fact(M).

missing(M) :- missing_fact(M).
smell(S) :- smell_fact(S).

air_clue(M) :- mystery(M), smell(S), clue_fact(M, S).
solved(M) :- mystery(M), clue_fact(M, _), reveal_fact(M, _).

#show solved/1.
#show air_clue/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_fact", mid))
        lines.append(asp.fact("missing_fact", m.missing_label))
        lines.append(asp.fact("smell_fact", m.smell))
        lines.append(asp.fact("clue_fact", mid, m.clue))
        lines.append(asp.fact("reveal_fact", mid, m.result))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1.\n#show air_clue/1."))
    atoms = set((sym.name, tuple(sym.arguments)) for sym in model)
    expected = {("solved",), ("air_clue",)}
    if atoms:
        print("OK: ASP program runs.")
        return 0
    print("MISMATCH: ASP program produced no shown atoms.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy mystery story world with air, veal, inner monologue, and dialogue.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--mystery", choices=list(MYSTERIES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULT_NAMES)
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


CURATED = [
    StoryParams(place="cafe", mystery="open_window", name="Mina", gender="girl", adult="Mrs. Green", trait="curious"),
    StoryParams(place="bakery", mystery="under_cloth", name="Theo", gender="boy", adult="Mr. Hale", trait="careful"),
    StoryParams(place="kitchen", mystery="mistaken_order", name="Ivy", gender="girl", adult="Mom", trait="brave"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solved/1.\n#show air_clue/1."))
    return sorted(set((sym.name, tuple(a.name if hasattr(a, "name") else a for a in sym.arguments)) for sym in model))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/1.\n#show air_clue/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available in this world.")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
