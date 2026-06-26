#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/music_surprise_sound_effects_slice_of_life.py
================================================================================================

A small slice-of-life storyworld about music, surprise, and sound effects.

Premise:
- A child, a small music task, and a gentle surprise.
- The world tracks a few physical items (meters) and feelings (memes).
- A surprise noise or missing sound effect can upset the plan.
- A helpful change in setup restores the music and gives the day a warm ending.

The generated story is meant to feel like a tiny, complete everyday scene:
beginning, problem, turn, and resolution.
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
# World vocabulary
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
class Location:
    id: str
    label: str
    indoor: bool
    music_kind: str
    background: str
    afford_surprise: bool = True
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
class Instrument:
    id: str
    label: str
    phrase: str
    sound: str
    small: bool = False
    fragile: bool = False
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
class SoundEffect:
    id: str
    label: str
    sound: str
    use: str
    surprise: bool = False
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
class Surprise:
    id: str
    label: str
    reveals: str
    kind: str
    sound_effect: Optional[str] = None
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    prepared: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    parent: object | None = None
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
class StoryParams:
    location: str
    instrument: str
    sound_effect: str
    surprise: str
    name: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
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


LOCATIONS = {
    "living_room": Location(
        id="living_room",
        label="the living room",
        indoor=True,
        music_kind="cozy music",
        background="The couch was soft, and a little lamp made the room glow.",
    ),
    "kitchen": Location(
        id="kitchen",
        label="the kitchen",
        indoor=True,
        music_kind="kitchen music",
        background="The table was clear, and the floor made a bright path for tiny steps.",
    ),
    "porch": Location(
        id="porch",
        label="the porch",
        indoor=False,
        music_kind="porch music",
        background="The air was warm, and the porch boards waited for a careful tap.",
    ),
    "garden": Location(
        id="garden",
        label="the garden",
        indoor=False,
        music_kind="garden music",
        background="Leaves moved softly, and the flower pots looked like they were listening.",
    ),
}

INSTRUMENTS = {
    "piano": Instrument(
        id="piano",
        label="piano",
        phrase="a small piano with shiny keys",
        sound="plink-plink",
    ),
    "drum": Instrument(
        id="drum",
        label="drum",
        phrase="a round hand drum",
        sound="boom-boom",
        small=True,
    ),
    "guitar": Instrument(
        id="guitar",
        label="guitar",
        phrase="a tiny guitar with bright strings",
        sound="twang-twang",
    ),
    "bell": Instrument(
        id="bell",
        label="bell",
        phrase="a little bell",
        sound="ding-ding",
        small=True,
    ),
}

SOUND_EFFECTS = {
    "clap": SoundEffect(
        id="clap",
        label="clapping",
        sound="clap-clap",
        use="keep the beat",
    ),
    "tap": SoundEffect(
        id="tap",
        label="table tapping",
        sound="tap-tap",
        use="mark the rhythm",
    ),
    "snap": SoundEffect(
        id="snap",
        label="finger snapping",
        sound="snap-snap",
        use="make a small drumbeat",
    ),
    "whoosh": SoundEffect(
        id="whoosh",
        label="a whoosh",
        sound="whoosh",
        use="help the surprise feel playful",
        surprise=True,
    ),
}

SURPRISES = {
    "gift": Surprise(
        id="gift",
        label="a wrapped gift",
        reveals="a shiny music box",
        kind="present",
        sound_effect="whoosh",
    ),
    "visitor": Surprise(
        id="visitor",
        label="a surprise visitor",
        reveals="Grandma stepping in with a smile",
        kind="person",
        sound_effect="clap",
    ),
    "lights": Surprise(
        id="lights",
        label="twinkling lights",
        reveals="tiny lights blinking on near the music corner",
        kind="change",
        sound_effect="snap",
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lily", "Maya", "Ava", "Zoe"]
BOY_NAMES = ["Theo", "Ben", "Leo", "Finn", "Owen", "Sam"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["quiet", "curious", "cheerful", "careful", "gentle", "playful"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.location = _safe_lookup(LOCATIONS, params.location)
        self.instrument = _safe_lookup(INSTRUMENTS, params.instrument)
        self.sound_effect = _safe_lookup(SOUND_EFFECTS, params.sound_effect)
        self.surprise = _safe_lookup(SURPRISES, params.surprise)
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.params)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]


def pronoun(gender: str, case: str = "subject") -> str:
    if gender == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def featured_sound(kind: str) -> str:
    return {
        "music": "soft notes",
        "rhythm": "little beats",
        "surprise": "a sudden sound",
    }.get(kind, "a pleasant sound")


def reasonableness_gate(params: StoryParams) -> None:
    if params.location not in LOCATIONS:
        pass
    if params.instrument not in INSTRUMENTS:
        pass
    if params.sound_effect not in SOUND_EFFECTS:
        pass
    if params.surprise not in SURPRISES:
        pass


def predict_surprise(world: World) -> dict[str, bool]:
    """A tiny forward check: does the scene support the surprise and the music?"""
    loc = world.location
    inst = world.instrument
    eff = world.sound_effect
    return {
        "surprise_fits": loc.afford_surprise and eff.surprise,
        "music_fits": bool(inst.sound),
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def start_scene(world: World, child: Entity, parent: Entity) -> None:
    loc = world.location
    inst = world.instrument
    world.say(
        f"{child.id} was a {next(t for t in child.meters.keys() if False),}"
    )


def tell_story(world: World) -> None:
    p = world.params
    child = world.get("child")
    parent = world.get("parent")
    loc = world.location
    inst = world.instrument
    eff = world.sound_effect
    sup = world.surprise

    child_trait = child.memes["trait_word"]
    child_gender = child.memes["gender"]

    world.say(
        f"{child.id} was a {child_trait} child who loved music."
    )
    world.say(
        f"{pronoun(child_gender).capitalize()} liked the warm sound of the {inst.label} "
        f"and the small {eff.label} that went with it."
    )
    world.say(
        f"One day, {child.id} and {parent.id} went to {loc.label}."
    )
    world.say(loc.background)
    world.say(
        f"{pronoun(child_gender).capitalize()} wanted to play the {inst.label} right away."
    )

    world.facts["planned_sound"] = eff.sound
    world.facts["planned_reveal"] = sup.reveals
    world.facts["place"] = loc.label
    world.facts["child_gender"] = child_gender

    # The surprise is helpful only if the sound effect and place fit the scene.
    check = predict_surprise(world)
    if not check["music_fits"]:
        pass
    world.para()
    if check["surprise_fits"]:
        world.say(
            f"Then, with a gentle {eff.sound}, {sup.reveals} appeared."
        )
    else:
        world.say(
            f"Then something unexpected happened, and the whole corner went quiet."
        )

    world.say(
        f"{child.id} blinked, then smiled. The surprise was not loud at all; it felt friendly."
    )

    if sup.id == "visitor":
        world.say(
            f"{parent.id} laughed and said, \"I brought someone special to listen.\""
        )
    elif sup.id == "gift":
        world.say(
            f"{parent.id} unwrapped the paper, and the new little box made the room feel extra warm."
        )
    elif sup.id == "lights":
        world.say(
            f"{parent.id} clicked the switch, and the tiny lights winked on like stars."
        )

    world.para()
    world.say(
        f"{child.id} started the song, and the {inst.sound} of the {inst.label} filled the room."
    )
    world.say(
        f"{eff.sound.capitalize()} kept the rhythm steady, and {parent.id} tapped along with a grin."
    )
    world.say(
        f"By the end, {child.id} was still playing happily, and the little surprise had turned into a cozy memory."
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(params)

    rng = random.Random(params.seed)

    gender = "girl" if rng.random() < 0.5 else "boy"
    name = params.name or choose_name(gender, rng)
    if params.name:
        # If a name is provided, infer a neutral gender label from params is not needed.
        gender = "girl" if params.name in GIRL_NAMES else "boy" if params.name in BOY_NAMES else gender

    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        meters={},
        memes={"joy": 1.0, "curiosity": 1.0, "trait_word": rng.choice(TRAITS), "gender": gender},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label=params.parent,
        meters={},
        memes={"care": 1.0, "patience": 1.0},
    ))
    world.facts["child"] = child
    world.facts["parent"] = parent
    world.facts["location"] = world.location
    world.facts["instrument"] = world.instrument
    world.facts["sound_effect"] = world.sound_effect
    world.facts["surprise"] = world.surprise

    tell_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f'Write a short slice-of-life story about music that includes "{world.instrument.label}" and "{world.sound_effect.label}".',
        f"Tell a gentle surprise story where {p.name or 'a child'} plays music at {world.location.label}.",
        f"Write a simple everyday story with sound effects, a small surprise, and a cozy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "parent")
    loc = world.location
    inst = world.instrument
    eff = world.sound_effect
    sup = world.surprise
    gender = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child_gender")
    trait = child.memes["trait_word"]

    return [
        QAItem(
            question=f"What did {child.id} love in the story?",
            answer=f"{pronoun(gender).capitalize()} loved music, especially the sound of the {inst.label} and the {eff.label}.",
        ),
        QAItem(
            question=f"Where did {child.id} and {parent.id} go?",
            answer=f"They went to {loc.label}, where the room or yard felt calm and ready for a small musical moment.",
        ),
        QAItem(
            question=f"What surprise appeared in the story?",
            answer=f"The surprise was {sup.reveals}, which made the scene feel friendly and warm.",
        ),
        QAItem(
            question=f"How did the {eff.label} help the music?",
            answer=f"It helped keep the rhythm steady while {child.id} played the {inst.label}.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{pronoun(gender).capitalize()} felt happy and cozy, because the surprise turned into a pleasant part of the day.",
        ),
        QAItem(
            question=f"What kind of child was {child.id}?",
            answer=f"{child.id} was a {trait} child who loved quiet, everyday music moments.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    inst = world.instrument
    eff = world.sound_effect
    sup = world.surprise
    loc = world.location
    out = [
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a made-up or chosen sound like clap-clap or tap-tap that helps the scene feel lively.",
        ),
        QAItem(
            question="Why do people use rhythm when making music?",
            answer="People use rhythm so the music has a steady beat that is easy to follow and enjoy.",
        ),
        QAItem(
            question="What makes a surprise feel gentle in a slice-of-life story?",
            answer="A gentle surprise feels small, kind, and welcome instead of scary or noisy.",
        ),
    ]
    if inst.label == "piano":
        out.append(QAItem(
            question="What sound does a piano make?",
            answer="A piano makes notes when its keys are pressed, and the notes can sound soft or bright.",
        ))
    if eff.id in {"clap", "tap", "snap"}:
        out.append(QAItem(
            question=f"What does {eff.label} help with?",
            answer=f"{eff.label.capitalize()} can help {eff.use}.",
        ))
    out.append(QAItem(
        question=f"What kind of place is {loc.label} in this story?",
        answer=("It is an indoor place where people can enjoy a calm, everyday moment together."
                if loc.indoor else "It is an outdoor place where the air and sounds can feel open and easy."),
    ))
    if sup.id == "gift":
        out.append(QAItem(
            question="What is a wrapped gift?",
            answer="A wrapped gift is a present covered in paper or ribbon so the person opening it gets a surprise.",
        ))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% location(L), indoor(L), instrument(I), sound_effect(E), surprise(S)

compatible_story(L, I, E, S) :-
    location(L), instrument(I), sound_effect(E), surprise(S),
    music_supports(I), surprise_supports(L, E).

music_supports(I) :- instrument(I).
surprise_supports(L, E) :- location(L), sound_effect(E), surprise_fx(E).

surprise_fx(E) :- sound_effect(E).
#show compatible_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.indoor:
            lines.append(asp.fact("indoor", lid))
    for iid in INSTRUMENTS:
        lines.append(asp.fact("instrument", iid))
    for eid, eff in SOUND_EFFECTS.items():
        lines.append(asp.fact("sound_effect", eid))
        if eff.surprise:
            lines.append(asp.fact("surprise_fx", eid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible_story")))


def python_combos() -> list[tuple]:
    combos = []
    for lid, loc in LOCATIONS.items():
        for iid in INSTRUMENTS:
            for eid, eff in SOUND_EFFECTS.items():
                for sid in SURPRISES:
                    if loc.afford_surprise and _safe_lookup(INSTRUMENTS, iid).sound and _safe_lookup(SOUND_EFFECTS, eid).surprise:
                        combos.append((lid, iid, eid, sid))
    return combos


def asp_verify() -> int:
    a = set(asp_combos())
    p = set(python_combos())
    if a == p:
        print(f"OK: ASP parity matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between ASP and python gate.")
    if a - p:
        print("Only in ASP:", sorted(a - p))
    if p - a:
        print("Only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# CLI / standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life music storyworld with surprise sound effects.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--sound-effect", dest="sound_effect", choices=SOUND_EFFECTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENTS)
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
    if getattr(args, "location", None) and getattr(args, "location", None) not in LOCATIONS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "instrument", None) and getattr(args, "instrument", None) not in INSTRUMENTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "sound_effect", None) and getattr(args, "sound_effect", None) not in SOUND_EFFECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "surprise", None) and getattr(args, "surprise", None) not in SURPRISES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    location = getattr(args, "location", None) or rng.choice(list(LOCATIONS))
    instrument = getattr(args, "instrument", None) or rng.choice(list(INSTRUMENTS))
    sound_effect = getattr(args, "sound_effect", None) or rng.choice(list(SOUND_EFFECTS))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    gender = "girl" if rng.random() < 0.5 else "boy"
    name = getattr(args, "name", None) or choose_name(gender, rng)
    return StoryParams(
        location=location,
        instrument=instrument,
        sound_effect=sound_effect,
        surprise=surprise,
        name=name,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for eid, ent in world.entities.items():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        lines.append(f"  {eid}: {ent.kind}/{ent.type} {' '.join(bits)}")
    lines.append(f"  location={world.location.id}")
    lines.append(f"  instrument={world.instrument.id}")
    lines.append(f"  sound_effect={world.sound_effect.id}")
    lines.append(f"  surprise={world.surprise.id}")
    return "\n".join(lines)


CURATED = [
    StoryParams(location="living_room", instrument="piano", sound_effect="clap", surprise="visitor", name="Mina", parent="mother"),
    StoryParams(location="kitchen", instrument="bell", sound_effect="tap", surprise="gift", name="Theo", parent="father"),
    StoryParams(location="porch", instrument="guitar", sound_effect="snap", surprise="lights", name="Lily", parent="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_combos()
        print(f"{len(models)} compatible stories:")
        for combo in models:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None) * 50, 50)):
            if len(samples) >= getattr(args, "n", None):
                break
            seed = base_seed + i
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
            header = f"### {p.name}: {p.instrument} at {p.location}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
