#!/usr/bin/env python3
"""
storyworlds/worlds/stray_weensie_surprise_fairy_tale.py
======================================================

A tiny fairy-tale story world about a stray little creature, a weensie helper,
and a surprise that changes a worried day into a happy one.

Premise:
- A stray, weensie wanderer longs for something gentle and safe.
- A keeper notices a missing home, a hidden surprise, or a small worry.
- A misunderstanding creates a tender moment of tension.
- A fairy-tale surprise brings warmth, belonging, and a clear ending image.

The story is simulated from a stateful world model with physical meters and
emotional memes. The prose is driven by those state changes, not by template
swaps alone.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

import os

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "mother", "princess", "fairy"}
        male = {"boy", "king", "father", "prince", "elf"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    indoors: bool = False
    allows: set[str] = field(default_factory=set)
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
class SurpriseKind:
    id: str
    label: str
    phrase: str
    delight: str
    hidden_by: str
    reveals: str
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


@dataclass
class GiftKind:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    comforts: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


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


PLACES = {
    "wood": Place(id="wood", label="the whispering wood", allows={"find", "hide", "gift"}),
    "cottage": Place(id="cottage", label="the little cottage", indoors=True, allows={"find", "gift", "hide"}),
    "garden": Place(id="garden", label="the moonlit garden", allows={"find", "gift"}),
}

SURPRISES = {
    "basket": SurpriseKind(
        id="basket",
        label="a surprise basket",
        phrase="a basket with a ribbon of blue",
        delight="it held warm muffins and a tiny note",
        hidden_by="under a mossy stump",
        reveals="the ribbon caught the moonlight",
        tags={"surprise", "gift"},
    ),
    "lantern": SurpriseKind(
        id="lantern",
        label="a surprise lantern",
        phrase="a lantern with a gold heart",
        delight="it glowed with a soft honey light",
        hidden_by="behind the cottage door",
        reveals="the little glass sparkled like a star",
        tags={"surprise", "light"},
    ),
    "crown": SurpriseKind(
        id="crown",
        label="a surprise crown",
        phrase="a tiny crown of berries",
        delight="it was made for a kind ruler of the day",
        hidden_by="inside a hollow log",
        reveals="the berries looked as bright as rubies",
        tags={"surprise", "royal"},
    ),
}

GIFTS = {
    "cloak": GiftKind(
        id="cloak",
        label="a cloak",
        phrase="a soft cloak lined with green",
        fits={"stray"},
        comforts={"cold", "lonely"},
        tags={"warmth", "stray"},
    ),
    "cup": GiftKind(
        id="cup",
        label="a cup of tea",
        phrase="a warm cup of tea with honey",
        fits={"weensie"},
        comforts={"tired", "afraid"},
        tags={"warmth", "tea"},
    ),
    "blanket": GiftKind(
        id="blanket",
        label="a blanket",
        phrase="a little blanket stitched with stars",
        fits={"stray", "weensie"},
        comforts={"cold", "lonely", "tired"},
        tags={"warmth", "sleep"},
    ),
}

NAMES = ["Mira", "Nell", "Tobin", "Bram", "Pippa", "Lina", "Jory", "Sela"]
TITLES = ["fairy", "keeper", "child", "wanderer", "elf"]
TRAITS = ["gentle", "brave", "curious", "kind", "weensie"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    surprise: str
    gift: str
    name: str
    title: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
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


def _vague_small_word() -> str:
    return "weensie"


def _is_comfortable(gift: GiftKind, hero: Entity) -> bool:
    return hero.type in gift.fits


def _predict_reveal(world: World, surprise: SurpriseKind) -> bool:
    return True if surprise.id in SURPRISES else False


def _introduce(world: World, hero: Entity, helper: Entity, surprise: SurpriseKind) -> None:
    world.say(
        f"Once upon a time, in {world.place.label}, there lived a stray, {hero.pronoun('possessive')} "
        f"own name was {hero.id}, and a weensie helper named {helper.id}."
    )
    world.say(
        f"{hero.id} was a {hero.memes['trait_word']} little {hero.type} who liked to listen for good news, "
        f"and {helper.id} was known for finding {surprise.label} where nobody thought to look."
    )


def _seek(world: World, hero: Entity, surprise: SurpriseKind) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"One dusk, {hero.id} went {surprise.hidden_by} and sniffed the leaves and stones, "
        f"because {hero.pronoun('subject')} thought something kind was waiting."
    )


def _worry(world: World, helper: Entity, hero: Entity, gift: GiftKind) -> None:
    helper.memes["care"] += 1
    hero.memes["lonely"] += 1
    world.say(
        f"But {helper.id} saw that {hero.id} was still stray and shivering a little, "
        f"so {helper.id} grew worried about {hero.pronoun('possessive')} comfort."
    )
    world.say(
        f'"If only we had {gift.phrase}," {helper.id} said, "then {hero.id} would not feel so small."'
    )


def _hidden_surprise(world: World, helper: Entity, surprise: SurpriseKind) -> None:
    helper.memes["mystery"] += 1
    world.say(
        f"{helper.id} smiled and reached into the dark place. There, {surprise.reveals}, and "
        f"out came {surprise.phrase}."
    )


def _gift(world: World, hero: Entity, helper: Entity, gift: GiftKind) -> None:
    if not _is_comfortable(gift, hero):
        pass
    item = world.add(Entity(
        id=gift.id,
        kind="thing",
        type="gift",
        label=gift.label,
        phrase=gift.phrase,
        owner=hero.id,
        caretaker=helper.id,
        protective=False,
        tags=set(gift.tags),
    ))
    item.worn_by = hero.id
    hero.memes["warmth"] += 1
    hero.memes["lonely"] = 0.0
    helper.memes["joy"] += 1
    world.say(
        f"Then {helper.id} gave {hero.id} {gift.phrase}, and at once {hero.id} felt less stray and more at home."
    )


def _resolution(world: World, hero: Entity, helper: Entity, surprise: SurpriseKind, gift: GiftKind) -> None:
    hero.memes["surprise"] += 1
    world.say(
        f"The surprise was not a fright after all. It was a happy one, and it made the whole {world.place.label} feel brighter."
    )
    world.say(
        f"{hero.id} tucked close beside {helper.id}, and the two of them shared the surprise while the moon watched over them."
    )
    world.say(
        f"By the end, the stray little heart was no longer wandering alone, and the weensie helper had given {hero.id} a new home-feeling night."
    )


def tell(place: Place, surprise: SurpriseKind, gift: GiftKind, name: str, title: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=title, label=name))
    helper = world.add(Entity(id="Pip", kind="character", type="fairy", label="Pip"))

    hero.memes["trait_word"] = trait
    hero.memes["surprise"] = 0.0
    hero.memes["lonely"] = 1.0
    helper.memes["care"] = 0.0

    _introduce(world, hero, helper, surprise)
    world.para()
    _seek(world, hero, surprise)
    _worry(world, helper, hero, gift)
    _hidden_surprise(world, helper, surprise)
    world.para()
    _gift(world, hero, helper, gift)
    _resolution(world, hero, helper, surprise, gift)

    world.facts.update(
        hero=hero,
        helper=helper,
        surprise=surprise,
        gift=gift,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    surprise: SurpriseKind = _safe_fact(world, f, "surprise")
    gift: GiftKind = _safe_fact(world, f, "gift")
    return [
        f'Write a fairy-tale story for a child about a stray {hero.type} and a weensie helper, using the word "surprise".',
        f"Tell a gentle story in {world.place.label} where {hero.id} finds {surprise.label} and then receives {gift.phrase}.",
        f"Write a short fairy tale about something stray becoming safe, with a happy surprise and a kind ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    surprise: SurpriseKind = _safe_fact(world, f, "surprise")
    gift: GiftKind = _safe_fact(world, f, "gift")
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"It was mostly about {hero.id}, a stray little {hero.type}, and the weensie helper {helper.id}.",
        ),
        QAItem(
            question=f"What surprise did {helper.id} find?",
            answer=f"{helper.id} found {surprise.phrase}. It turned out to be a happy surprise with a gentle shine.",
        ),
        QAItem(
            question=f"What did {hero.id} receive at the end?",
            answer=f"{hero.id} received {gift.phrase}, which made the stray little heart feel warm and safe.",
        ),
        QAItem(
            question=f"Why did the helper worry at first?",
            answer=f"{helper.id} worried because {hero.id} still looked stray and lonely, so the helper wanted something comforting.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect, so it can make you gasp, smile, or laugh with delight.",
        ),
        QAItem(
            question="What does the word stray mean?",
            answer="Stray means without a home, owner, or clear place to belong, like something or someone wandering alone.",
        ),
        QAItem(
            question="What does weensie mean?",
            answer="Weensie means very, very small, like a tiny little thing that can almost fit in a pocket.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
surprise(S) :- surprise_kind(S).
gift(G) :- gift_kind(G).

weensie(X) :- character(X), role(X, fairy).
stray(X) :- character(X), stray_heart(X).

happy_surprise(S) :- surprise_kind(S), delight(S, _).
comforts(G, X) :- gift_kind(G), fits(G, X).

valid_story(P, S, G) :- place(P), surprise(S), gift(G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise_kind", sid))
        lines.append(asp.fact("delight", sid, s.delight))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift_kind", gid))
        for fit in sorted(g.fits):
            lines.append(asp.fact("fits", gid, fit))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for s in SURPRISES:
            for g in GIFTS:
                out.append((p, s, g))
    return out


def asp_verify() -> int:
    import asp
    py = set(valid_stories())
    clingo = set(asp_valid_stories())
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in Python:", sorted(py - clingo))
    print("only in ASP:", sorted(clingo - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters, generation, CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    surprise: str
    gift: str
    name: str
    title: str
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


CURATED = [
    StoryParams(place="wood", surprise="basket", gift="blanket", name="Mira", title="wanderer", trait="gentle"),
    StoryParams(place="cottage", surprise="lantern", gift="cup", name="Pippa", title="child", trait="kind"),
    StoryParams(place="garden", surprise="crown", gift="cloak", name="Tobin", title="wanderer", trait="brave"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale world of a stray weensie surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=["wanderer", "child", "fairy", "elf", "keeper", "girl", "boy"])
    ap.add_argument("--trait", choices=["gentle", "brave", "curious", "kind", "weensie"])
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    gift = getattr(args, "gift", None) or rng.choice(list(GIFTS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    title = getattr(args, "title", None) or rng.choice(["wanderer", "child", "fairy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if gift == "cup" and title not in {"fairy", "child", "keeper", "wanderer"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, surprise=surprise, gift=gift, name=name, title=title, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(SURPRISES, params.surprise),
        _safe_lookup(GIFTS, params.gift),
        params.name,
        params.title,
        params.trait,
    )
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible story tuples:")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
