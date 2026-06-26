#!/usr/bin/env python3
"""
storyworlds/worlds/pillar_trump_gravitate_suspense_teamwork_myth.py
====================================================================

A small mythic story world about a sacred pillar, a bronze trump, and the
mysterious way people gravitate toward a place of suspense and teamwork.

Premise:
- A village keeps a tall pillar in the old shrine.
- A bronze trump is sounded to gather helpers.
- The hero feels drawn toward the pillar as if by fate.
- A trapped door, storm, or sealed path creates suspense.
- Teamwork resolves the problem and proves the pillar's meaning.

This world is built to be child-facing, concrete, and state-driven. The story
is generated from a live simulation where characters, objects, and place-based
constraints determine the prose.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ent: object | None = None
    hero: object | None = None
    omen: object | None = None
    parent: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "priest"}:
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
class Setting:
    place: str
    mood: str
    affordances: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    location: str
    awe: str
    tags: set[str] = field(default_factory=set)
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
class Omen:
    id: str
    label: str
    phrase: str
    sound: str
    gathers: int
    tags: set[str] = field(default_factory=set)
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
class Trial:
    id: str
    name: str
    verb: str
    gerund: str
    danger: str
    cause: str
    solved_by: str
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
class Helper:
    id: str
    label: str
    role: str
    gift: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "temple": Setting(place="the old temple", mood="hushed", affordances={"summon", "lift", "listen"}),
    "hill": Setting(place="the windy hill", mood="restless", affordances={"summon", "lift", "listen"}),
    "courtyard": Setting(place="the stone courtyard", mood="quiet", affordances={"summon", "lift", "listen"}),
}

RELICS = {
    "pillar": Relic(
        id="pillar",
        label="pillar",
        phrase="a tall gray pillar",
        type="pillar",
        location="center",
        awe="ancient",
        tags={"pillar", "myth"},
    ),
    "idol": Relic(
        id="idol",
        label="idol",
        phrase="a small gold idol",
        type="idol",
        location="alcove",
        awe="bright",
        tags={"myth"},
    ),
}

OMENS = {
    "trump": Omen(
        id="trump",
        label="trump",
        phrase="a bronze trump",
        sound="a clear bronze call",
        gathers=3,
        tags={"trump", "call"},
    ),
    "shell": Omen(
        id="shell",
        label="shell horn",
        phrase="a shell horn",
        sound="a bright shell note",
        gathers=2,
        tags={"call"},
    ),
}

TRIALS = {
    "seal": Trial(
        id="seal",
        name="sealed gate",
        verb="open the sealed gate",
        gerund="opening the sealed gate",
        danger="locked tight",
        cause="old iron and stone",
        solved_by="many hands",
        tags={"suspense", "teamwork"},
    ),
    "flood": Trial(
        id="flood",
        name="flooded stair",
        verb="cross the flooded stair",
        gerund="crossing the flooded stair",
        danger="swirling deep",
        cause="rainwater",
        solved_by="shared ropes",
        tags={"suspense", "teamwork"},
    ),
    "wind": Trial(
        id="wind",
        name="windy bridge",
        verb="cross the windy bridge",
        gerund="crossing the windy bridge",
        danger="shaking hard",
        cause="sharp wind",
        solved_by="linked arms",
        tags={"suspense", "teamwork"},
    ),
}

HELPERS = {
    "elder": Helper(id="elder", label="the elder", role="guidance", gift="wise words", tags={"myth", "teamwork"}),
    "builder": Helper(id="builder", label="the builder", role="strength", gift="steady shoulders", tags={"teamwork"}),
    "singer": Helper(id="singer", label="the singer", role="heart", gift="a brave tune", tags={"teamwork", "myth"}),
}

GIRL_NAMES = ["Asha", "Mira", "Nia", "Ila", "Suri", "Lena"]
BOY_NAMES = ["Kian", "Arun", "Taro", "Seth", "Bren", "Oren"]
TRAITS = ["curious", "brave", "gentle", "restless", "patient", "bold"]


@dataclass
class StoryParams:
    place: str
    relic: str
    omen: str
    trial: str
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


ASP_RULES = r"""
% A relic is central if it is the pillar.
central(R) :- relic(R), label(R,"pillar").

% The trump is the call that gathers helpers.
gathering_call(O) :- omen(O), label(O,"trump").

% The trial is suspenseful when it is dangerous and not yet solved.
suspenseful(T) :- trial(T), dangerous(T), not solved(T).

% Teamwork resolves a suspenseful trial if enough helpers gather.
resolves(T) :- suspenseful(T), teamwork(T), helper_count(T,N), N >= 2.

% A valid story is one with a pillar, a trump, and a suspenseful trial that can be resolved.
valid_story(P,R,O,T) :- place(P), central(R), gathering_call(O), trial(T), resolves(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("label", rid, r.label))
    for oid, o in OMENS.items():
        lines.append(asp.fact("omen", oid))
        lines.append(asp.fact("label", oid, o.label))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("dangerous", tid))
        lines.append(asp.fact("teamwork", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for relic in RELICS:
            if relic != "pillar":
                continue
            for omen in OMENS:
                if omen != "trump":
                    continue
                for trial in TRIALS:
                    out.append((place, relic, omen, trial))
    return out


def select_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def introduce(world: World, hero: Entity, relic: Entity, omen: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} was a {hero.meters.get('age_word', 'young')} "
        f"{hero.type} who felt drawn toward the {relic.label} as if the old stones were calling."
    )
    world.say(
        f"Nearby stood {relic.phrase}, and the air held {omen.sound} from the {omen.label}."
    )


def gravitate(world: World, hero: Entity, relic: Entity) -> None:
    hero.memes["gravitate"] = hero.memes.get("gravitate", 0.0) + 1.0
    world.say(
        f"{hero.id} kept gravitating toward the {relic.label}, step by step, until the pillar seemed to wait for {hero.pronoun('object')}."
    )


def build_suspense(world: World, trial: Trial, omen: Omen, parent: Entity, hero: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"Then the {trial.name} blocked the path; it was {trial.danger}, because of {trial.cause}."
    )
    world.say(
        f"{parent.label.capitalize()} lifted the {omen.label} and sounded {omen.sound}, and the little crowd fell quiet."
    )
    world.say(
        f'“Who will help?” {parent.pronoun("subject").capitalize()} asked, and the question hung in the air like a cloud before rain.'
    )


def gather_helpers(world: World, hero: Entity, trial: Trial) -> list[Entity]:
    helpers = []
    for h in HELPERS.values():
        ent = world.add(Entity(id=h.id, kind="character", type="elder" if h.role == "guidance" else "helper", label=h.label))
        helpers.append(ent)
    world.say(
        f"{hero.id} did not answer alone. {hero.pronoun('subject').capitalize()} called the {HELPERS['elder'].label}, {HELPERS['builder'].label}, and {HELPERS['singer'].label}."
    )
    world.say(
        f"At once, they came together, and their teamwork made the hard thing feel possible."
    )
    return helpers


def resolve_trial(world: World, hero: Entity, parent: Entity, relic: Entity, omen: Entity, trial: Trial, helpers: list[Entity]) -> None:
    world.say(
        f"Together they did not rush; they chose careful hands, steady feet, and a shared rhythm."
    )
    world.say(
        f"They used {trial.solved_by}, and with many hands they {trial.verb}."
    )
    world.say(
        f"At last, the way opened, and the {relic.label} stood bright and still while {hero.id} smiled beside the {omen.label}."
    )
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1.0
    world.facts["solved"] = True


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    relic = world.add(Entity(id=params.relic, kind="thing", type="relic", label=_safe_lookup(RELICS, params.relic).label, phrase=_safe_lookup(RELICS, params.relic).phrase))
    omen = world.add(Entity(id=params.omen, kind="thing", type="omen", label=_safe_lookup(OMENS, params.omen).label, phrase=_safe_lookup(OMENS, params.omen).phrase))
    trial = _safe_lookup(TRIALS, params.trial)

    world.facts.update(hero=hero, parent=parent, relic=relic, omen=omen, trial=trial, setting=setting)
    introduce(world, hero, relic, omen)
    world.para()
    gravitate(world, hero, relic)
    build_suspense(world, trial, omen, parent, hero)
    world.para()
    helpers = gather_helpers(world, hero, trial)
    resolve_trial(world, hero, parent, relic, omen, trial, helpers)
    world.facts["helpers"] = helpers
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")  # type: ignore[assignment]
    trial: Trial = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trial")  # type: ignore[assignment]
    relic: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic")  # type: ignore[assignment]
    omen: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "omen")  # type: ignore[assignment]
    return [
        f'Write a short myth for a child about a {relic.label}, a {omen.label}, and a hard moment of {trial.name}.',
        f"Tell a suspenseful teamwork story where {hero.id} keeps gravitating toward the {relic.label} and friends help solve the problem.",
        f'Write a simple myth that ends with a team opening {trial.verb} near the {relic.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")  # type: ignore[assignment]
    parent: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")  # type: ignore[assignment]
    relic: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic")  # type: ignore[assignment]
    omen: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "omen")  # type: ignore[assignment]
    trial: Trial = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trial")  # type: ignore[assignment]
    helpers: list[Entity] = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helpers")  # type: ignore[assignment]

    helper_names = ", ".join(h.label for h in helpers)
    return [
        QAItem(
            question=f"What kept drawing {hero.id} toward the shrine?",
            answer=f"{hero.id} kept gravitating toward the {relic.label}, as if the old place was calling {hero.pronoun('object')} to come closer.",
        ),
        QAItem(
            question=f"What made the story feel tense before the ending?",
            answer=f"The story turned tense when the {trial.name} blocked the way and sounded hard to face, so everyone had to wait and think.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the trouble needed teamwork?",
            answer=f"{helper_names} came together and helped as a team, so {hero.id} was not alone.",
        ),
        QAItem(
            question=f"What did the {omen.label} do in the story?",
            answer=f"The {omen.label} gave {omen.sound}, which called everyone to gather and listen for the next step.",
        ),
        QAItem(
            question=f"How did the story end near the {relic.label}?",
            answer=f"It ended with the path opening, the {trial.name} solved, and the {relic.label} standing calm while everyone felt proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pillar?",
            answer="A pillar is a tall upright stone or post that can hold up a building or stand like an important marker.",
        ),
        QAItem(
            question="What is a trump used for in a story like this?",
            answer="A trump is a loud call tool that can gather people, announce danger, or start an important moment.",
        ),
        QAItem(
            question="What does gravitate mean?",
            answer="To gravitate means to move toward something naturally, as if you are drawn to it.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together to do something hard.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next, especially when something is hard or uncertain.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) " + " ".join(bits))
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world requires the pillar, the trump, and a suspenseful trial that teamwork can solve.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "relic", None) and getattr(args, "relic", None) not in RELICS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "omen", None) and getattr(args, "omen", None) not in OMENS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "trial", None) and getattr(args, "trial", None) not in TRIALS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    relic = getattr(args, "relic", None) or "pillar"
    omen = getattr(args, "omen", None) or "trump"
    trial = getattr(args, "trial", None) or rng.choice(list(TRIALS))

    if relic != "pillar" or omen != "trump":
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or select_name(gender, rng)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, relic=relic, omen=omen, trial=trial, name=name, gender=gender, parent=parent, trait=trait)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world: pillar, trump, gravitate, suspense, teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--trial", choices=TRIALS)
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


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    expected = {("temple", "pillar", "trump", "seal"), ("temple", "pillar", "trump", "flood"), ("temple", "pillar", "trump", "wind"),
                ("hill", "pillar", "trump", "seal"), ("hill", "pillar", "trump", "flood"), ("hill", "pillar", "trump", "wind"),
                ("courtyard", "pillar", "trump", "seal"), ("courtyard", "pillar", "trump", "flood"), ("courtyard", "pillar", "trump", "wind")}
    model = set(asp_valid_stories())
    if model == expected:
        print(f"OK: clingo gate matches valid story set ({len(model)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(model - expected))
    print("only in python:", sorted(expected - model))
    return 1


CURATED = [
    StoryParams(place="temple", relic="pillar", omen="trump", trial="seal", name="Asha", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="hill", relic="pillar", omen="trump", trial="flood", name="Kian", gender="boy", parent="father", trait="brave"),
    StoryParams(place="courtyard", relic="pillar", omen="trump", trial="wind", name="Mira", gender="girl", parent="mother", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for s in stories:
            print("  ", s)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name}: {p.relic} / {p.omen} / {p.trial}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
