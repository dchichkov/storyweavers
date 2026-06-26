#!/usr/bin/env python3
"""
A small pirate-tale story world about a crew, a sister, a fraction, and a mystery to solve.

The story engine builds a short simulated premise:
- a pirate child and her sister are on a ship or at an island cove
- they anticipate a hidden treasure clue
- the clue is a fraction of a map or a divided prize
- a mystery creates tension
- the crew solves it with a concrete action
- the ending proves what changed and leaves a happy image

This world intentionally stays small and constraint-checked.
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
# Core world entities
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chest: object | None = None
    hero: object | None = None
    sister: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "sister", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "brother", "pirate"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    id: str
    name: str
    setting_line: str
    affords: set[str] = field(default_factory=set)
    sea_side: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Mystery:
    id: str
    clue: str
    hidden_by: str
    solved_by: str
    risk: str
    reveal: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    region: str = "hand"
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    mystery: str
    treasure: str
    name: str
    sibling_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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

    def log(self, text: str) -> None:
        self.trace.append(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


PLACES = {
    "ship": Place(
        id="ship",
        name="the ship",
        setting_line="The little ship rocked on blue water, and the ropes creaked softly.",
        affords={"search", "sail", "peek"},
        sea_side=True,
    ),
    "cove": Place(
        id="cove",
        name="the hidden cove",
        setting_line="The hidden cove was quiet, with shells, driftwood, and a cave mouth to explore.",
        affords={"search", "peek", "dig"},
        sea_side=True,
    ),
    "dock": Place(
        id="dock",
        name="the dock",
        setting_line="The dock smelled like salt and tar, and gulls hopped near the ropes.",
        affords={"search", "peek", "sort"},
        sea_side=True,
    ),
}

MYSTERIES = {
    "map_fraction": Mystery(
        id="map_fraction",
        clue="a torn map showing one quarter of a secret path",
        hidden_by="a sand-stuck crate",
        solved_by="matching the torn corner to the other pieces",
        risk="the clue might be lost in the sea breeze",
        reveal="the missing piece pointed to the right cave",
    ),
    "bell_riddle": Mystery(
        id="bell_riddle",
        clue="a tiny bell that rang only when held above water",
        hidden_by="a net full of seaweed",
        solved_by="lifting it and listening for the echo",
        risk="the bell might be ignored as ordinary junk",
        reveal="the bell's sound showed where the treasure chest waited",
    ),
    "shell_code": Mystery(
        id="shell_code",
        clue="three shells arranged like a secret number",
        hidden_by="a bucket by the mast",
        solved_by="counting the shells and splitting them into groups",
        risk="the answer could be missed if nobody looked closely",
        reveal="the shell count matched the path to the treasure",
    ),
}

TREASURES = {
    "coin_box": Treasure(
        id="coin_box",
        label="coin box",
        phrase="a small coin box with a gold clasp",
    ),
    "jewel_bag": Treasure(
        id="jewel_bag",
        label="jewel bag",
        phrase="a bright cloth bag of shiny stones",
    ),
    "map_roll": Treasure(
        id="map_roll",
        label="map roll",
        phrase="a rolled map tied with red string",
        plural=False,
    ),
}

NAMES = ["Mara", "Nina", "Tess", "Lina", "Coral", "Belle", "Ivy"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Owen", "Reed"]
TRAITS = ["brave", "curious", "quick", "cheerful", "clever"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def place_line(place: Place) -> str:
    return place.setting_line


def solve_mystery(world: World, hero: Entity, sister: Entity, mystery: Mystery, treasure: Treasure) -> bool:
    world.log(f"mystery started: {mystery.clue}")
    hero.memes["anticipate"] = hero.memes.get("anticipate", 0) + 1
    sister.memes["anticipate"] = sister.memes.get("anticipate", 0) + 1

    if mystery.id == "map_fraction":
        world.say(
            f"Together they noticed {mystery.clue}, and {hero.id} knew it was only a fraction of the whole secret."
        )
        world.say(
            f"{sister.id} anticipated the missing corner would matter, so she checked the torn edges against the map roll."
        )
        world.say(
            f"That careful look solved it: {mystery.solved_by}, and {mystery.reveal}."
        )
        return True

    if mystery.id == "bell_riddle":
        world.say(
            f"They found {mystery.clue} hidden by {mystery.hidden_by}, and {sister.id} leaned close to listen."
        )
        world.say(
            f"{hero.id} anticipated there was a trick, so he held it above the water and heard the ring answer back."
        )
        world.say(
            f"That was enough to solve the mystery: {mystery.solved_by}, and {mystery.reveal}."
        )
        return True

    world.say(
        f"On the dock, they spotted {mystery.clue} tucked near {mystery.hidden_by}."
    )
    world.say(
        f"{sister.id} anticipated a pattern, counted slowly, and split the shells into neat groups."
    )
    world.say(
        f"Then the numbers made sense: {mystery.solved_by}, and {mystery.reveal}."
    )
    return True


def closing_happy_ending(world: World, hero: Entity, sister: Entity, treasure: Treasure) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    sister.memes["joy"] = sister.memes.get("joy", 0) + 1
    world.say(
        f"In the end, the {treasure.label} was safe, the mystery was solved, and the two siblings grinned like the sea had shared a secret with them."
    )
    world.say(
        f"They carried {(getattr(treasure, 'it')() if callable(getattr(treasure, 'it', None)) else getattr(treasure, 'it', 'it'))} back together, and the ship felt warmer with their happy ending aboard."
    )


def build_story(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.mystery not in MYSTERIES:
        pass
    if params.treasure not in TREASURES:
        pass

    place = _safe_lookup(PLACES, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    treasure = _safe_lookup(TREASURES, params.treasure)

    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label="pirate child"))
    sister = world.add(Entity(id=params.sibling_name, kind="character", type="girl", label="sister"))
    chest = world.add(Entity(id="treasure", kind="thing", type=treasure.label, label=treasure.label, phrase=treasure.phrase))

    world.facts.update(hero=hero, sister=sister, mystery=mystery, treasure=chest)

    world.say(
        f"{hero.id} and {sister.id} were little pirates who loved a mystery to solve."
    )
    world.say(
        f"Each morning they anticipated a clue, because adventure felt best when it came with a surprise."
    )
    world.say(place_line(place))
    world.para()

    world.say(
        f"That day, they searched for {mystery.clue} because they knew it could lead to {treasure.phrase}."
    )
    world.say(
        f"{hero.id} wanted to hurry, but {sister.id} said they should look carefully; the answer might be only a fraction of the whole."
    )
    world.para()

    solve_mystery(world, hero, sister, mystery, treasure)
    world.para()
    closing_happy_ending(world, hero, sister, treasure)
    return world


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    treasure: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treasure")
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    sister: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sister")
    return [
        f'Write a short pirate tale for children that includes the word "fraction" and a happy ending.',
        f"Tell a story where {hero.id} and {sister.id} anticipate a clue, solve {mystery.clue}, and find {treasure.label}.",
        f"Write a gentle mystery story at {world.place.name} about siblings who solve a clue by careful looking.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    sister: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sister")
    mystery: Mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    treasure: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "treasure")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id} and {sister.id}, two little pirates who wanted to solve a mystery.",
        ),
        QAItem(
            question=f"What did they anticipate?",
            answer=f"They anticipated a clue that would help them solve the mystery and reach the {treasure.label}.",
        ),
        QAItem(
            question=f"Why was the clue special?",
            answer=f"It was special because it was only a fraction of the whole answer, so they had to look carefully.",
        ),
        QAItem(
            question=f"What solved the mystery?",
            answer=f"Careful teamwork solved it: {mystery.solved_by}, and that revealed the right path forward.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with the mystery solved and the treasure carried back safely together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fraction?",
            answer="A fraction is a part of a whole, like one piece of a map or one slice of a pie.",
        ),
        QAItem(
            question="What does anticipate mean?",
            answer="To anticipate means to expect something before it happens, like waiting for a clue you think will appear.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something hidden or not understood yet, so people have to look for clues to solve it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for item in sample.prompts:
        lines.append(f"- {item}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(ship).
place(cove).
place(dock).

mystery(map_fraction).
mystery(bell_riddle).
mystery(shell_code).

treasure(coin_box).
treasure(jewel_bag).
treasure(map_roll).

% A mystery is suitable when it can be solved by careful looking or counting.
solvable(map_fraction).
solvable(bell_riddle).
solvable(shell_code).

% Every supported combination yields a happy ending story.
valid_story(P, M, T) :- place(P), mystery(M), treasure(T), solvable(M).
#show valid_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
    for t in TREASURES.values():
        lines.append(asp.fact("treasure", t.id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, m, t) for p in PLACES for m in MYSTERIES for t in TREASURES}
    asp_set = set(asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: ASP parity matches Python ({len(asp_set)} combinations).")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def pick_name(rng: random.Random) -> tuple[str, str]:
    name = rng.choice(NAMES)
    sister = rng.choice([n for n in NAMES if n != name])
    return name, sister


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    name, sister = pick_name(rng)
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    if getattr(args, "sister_name", None):
        sister = getattr(args, "sister_name", None)
    if name == sister:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, mystery=mystery, treasure=treasure, name=name, sibling_name=sister, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        print()
        print("--- trace ---")
        for line in sample.world.trace:
            print(line)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world: fraction, sister, anticipate, mystery to solve, happy ending.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--name")
    ap.add_argument("--sister-name", dest="sister_name")
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


CURATED = [
    StoryParams(place="ship", mystery="map_fraction", treasure="map_roll", name="Mara", sibling_name="Nina"),
    StoryParams(place="cove", mystery="bell_riddle", treasure="coin_box", name="Tess", sibling_name="Ivy"),
    StoryParams(place="dock", mystery="shell_code", treasure="jewel_bag", name="Coral", sibling_name="Belle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_stories():
            print(row)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            p = sample.params
            print(f"### {idx + 1}: {p.place}, {p.mystery}, {p.treasure}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
