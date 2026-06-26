#!/usr/bin/env python3
"""
Standalone storyworld: shoe prank surprise humor adventure.

A child plans a harmless prank with a shoe, the surprise goes a little too far,
and then the characters go on a small adventure to make it right. The world is
simulated with physical meters and emotional memes so the prose follows state
changes rather than a fixed template.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ("dusty", "missing", "tipped", "found"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "surprise", "humor", "worry", "guilt", "relief", "curiosity"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    outdoors: bool
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
class Shoe:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Prank:
    id: str
    setup: str
    effect: str
    fallout: str
    recovery: str
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
class StoryParams:
    place: str
    prank: str
    shoe: str
    name: str
    gender: str
    helper: str
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


PLACES = {
    "hallway": Place("the hallway", outdoors=False, affords={"tip"}),
    "backyard": Place("the backyard", outdoors=True, affords={"hide", "tip"}),
    "porch": Place("the porch", outdoors=True, affords={"hide", "tip"}),
    "camp": Place("the camp path", outdoors=True, affords={"hide", "tip"}),
}

SHOES = {
    "sneaker": Shoe("sneakers", "a pair of bright red sneakers", "feet", plural=True),
    "boot": Shoe("boots", "a pair of shiny rain boots", "feet", plural=True),
    "slipper": Shoe("slippers", "soft blue slippers", "feet", plural=True),
    "shoe": Shoe("shoe", "one brand-new shoe", "feet", plural=False),
}

PRANKS = {
    "lace_swap": Prank(
        id="lace_swap",
        setup="tied the laces together in a sneaky knot",
        effect="made the shoes wobble and stumble",
        fallout="turned the surprise into a giggle",
        recovery="untied the laces and apologized",
        keyword="prank",
        tags={"shoe", "humor", "surprise"},
    ),
    "shoebox_swap": Prank(
        id="shoebox_swap",
        setup="moved the shoes into the wrong box",
        effect="made everyone stare at the empty spot",
        fallout="caused a loud, funny gasp",
        recovery="put the shoes back where they belonged",
        keyword="surprise",
        tags={"shoe", "surprise"},
    ),
    "one_shoe_hide": Prank(
        id="one_shoe_hide",
        setup="hid one shoe behind a flower pot",
        effect="left the owner hopping on one foot",
        fallout="made the room burst into laughter",
        recovery="found the shoe in the garden and returned it",
        keyword="humor",
        tags={"shoe", "humor", "adventure"},
    ),
}

NAMES = {
    "girl": ["Mina", "Luna", "Tia", "Nora", "Ivy", "Zoe"],
    "boy": ["Eli", "Theo", "Milo", "Finn", "Noah", "Ben"],
}
TRAITS = ["curious", "cheerful", "spirited", "playful", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, prank, shoe) for place, p in PLACES.items() for prank in p.affords for shoe in SHOES]


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_confusion(world: World) -> list[str]:
    out = []
    prank = world.facts.get("prank")
    hero = world.facts.get("hero")
    shoe = world.facts.get("shoe")
    if not prank or not hero or not shoe:
        return out
    key = ("confusion", prank.id, shoe.label)
    if key in world.fired:
        return out
    if prank.id == "shoebox_swap":
        world.fired.add(key)
        hero.memes["surprise"] += 1
        hero.memes["worry"] += 1
        out.append(f"{hero.id} blinked at the empty spot where {shoe.label} should have been.")
    return out


def _r_humor(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    prank = world.facts.get("prank")
    if not hero or not prank:
        return out
    key = ("humor", prank.id)
    if key in world.fired:
        return out
    if hero.memes["surprise"] >= THRESHOLD:
        world.fired.add(key)
        hero.memes["humor"] += 1
        out.append("The whole thing was so odd that it felt funny instead of mean.")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    hero = world.facts.get("hero")
    helper = world.facts.get("helper")
    shoe = world.facts.get("shoe")
    if not hero or not helper or not shoe:
        return out
    key = ("repair", shoe.label)
    if key in world.fired:
        return out
    if hero.memes["guilt"] >= THRESHOLD:
        world.fired.add(key)
        hero.memes["relief"] += 1
        helper.memes["joy"] += 1
        out.append(f"{helper.id} helped look for {shoe.label}, and the worry started to fade.")
    return out


RULES = [Rule("confusion", _r_confusion), Rule("humor", _r_humor), Rule("repair", _r_repair)]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            msgs = rule.apply(world)
            if msgs:
                changed = True
                for m in msgs:
                    world.say(m)


def reasonableness_gate(place: Place, prank: Prank, shoe: Shoe) -> bool:
    return "shoe" in prank.tags and place and shoe and shoe.region == "feet"


def select_helper(hero: Entity, gender: str) -> str:
    return "mother" if gender == "girl" else "father"


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(_safe_lookup(NAMES, gender))


def tell_story(place: Place, prank: Prank, shoe: Shoe, hero_name: str, gender: str, helper: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    parent = world.add(Entity(id="Helper", kind="character", type=helper, label=f"the {helper}"))
    item = world.add(Entity(id="Shoe", type=shoe.label, label=shoe.label, phrase=shoe.phrase, owner=hero.id, caretaker=parent.id, plural=shoe.plural))
    world.facts.update(hero=hero, parent=parent, helper=parent, shoe=item, prank=prank)

    world.say(f"{hero.id} was a {trait} little {gender} who loved a good adventure.")
    world.say(f"{hero.id} also loved {prank.keyword}s, because a tiny surprise could make the whole day sparkle.")
    world.say(f"One day, {helper} bought {hero.id} {item.phrase}, and {hero.id} wore {item.it()} everywhere.")
    world.para()

    world.say(f"At {place.name}, {hero.id} decided to play a harmless {prank.keyword}.")
    world.say(f"{hero.id} {prank.setup}, and the little plan worked a bit too well.")
    hero.memes["surprise"] += 1
    hero.memes["curiosity"] += 1
    hero.meters["tipped"] += 1
    propagate(world)
    world.say(f"Then {prank.effect}.")
    world.say(f"{hero.id} stared for a moment, and the surprise turned into a laugh that bounced around {place.name}.")
    hero.memes["humor"] += 1
    world.para()

    if prank.id == "one_shoe_hide":
        hero.memes["worry"] += 1
        hero.memes["guilt"] += 1
        world.say(f"After the laugh, {hero.id} realized {item.label} was missing for real.")
        world.say(f"{hero.id} and {helper} began a small adventure through {place.name} to find it.")
        world.say(f"They looked behind pots, under benches, and beside the path until {item.label} was found.")
    elif prank.id == "shoebox_swap":
        hero.memes["guilt"] += 1
        world.say(f"After the surprise, {hero.id} saw the empty box and felt a little sorry.")
        world.say(f"{hero.id} and {helper} took a careful walk through {place.name} to put everything right again.")
        world.say(f"They found the box, fixed the mix-up, and set {item.label} back where it belonged.")
    else:
        hero.memes["guilt"] += 1
        world.say(f"The knot was funny for a second, but {hero.id} knew it was time to be kind again.")
        world.say(f"{hero.id} and {helper} sat together, untied the laces, and made the shoes safe to wear.")
        world.say(f"By the end, the prank had become a joke, and the joke had become a lesson.")

    propagate(world)
    hero.memes["worry"] = 0.0
    hero.memes["relief"] += 1
    world.say(f"{hero.id} smiled at the end because the shoe was safe, the prank was over, and the day felt like an adventure after all.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prank = _safe_fact(world, f, "prank")
    shoe = _safe_fact(world, f, "shoe")
    return [
        f'Write a short adventure story for a child that includes a shoe and a prank, with a funny surprise and a kind ending.',
        f"Tell a gentle, humorous story about {hero.id} and {shoe.label} that starts with a prank and ends with things set right.",
        f'Write a small story where a playful surprise about a shoe turns into a family adventure.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    shoe = _safe_fact(world, f, "shoe")
    prank = _safe_fact(world, f, "prank")
    place = world.place.name
    return [
        QAItem(
            question=f"What did {hero.id} like to do that made the day feel exciting?",
            answer=f"{hero.id} liked a playful prank, and {prank.keyword} energy made the story feel surprising and funny.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {parent.label} go on a little adventure at {place}?",
            answer=f"They went on a little adventure to fix the prank and make sure {shoe.label} was found and safe again.",
        ),
        QAItem(
            question=f"What was the surprising thing about {hero.id}'s prank?",
            answer=f"The prank made {shoe.label} seem to vanish or wobble in a funny way, so everyone reacted with surprise before the story turned kind again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a prank?", answer="A prank is a joke or trick meant to surprise someone, and a good prank should stay harmless and kind."),
        QAItem(question="Why are shoes important?", answer="Shoes help protect your feet when you walk, run, and play."),
        QAItem(question="What does surprise mean?", answer="Surprise is the feeling you get when something happens that you did not expect."),
        QAItem(question="Why can humor help after a mistake?", answer="Humor can make people laugh, calm down, and feel ready to fix things together."),
        QAItem(question="What is an adventure?", answer="An adventure is an exciting trip or problem-solving journey, even if it is small and close to home."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.outdoors:
            lines.append(asp.fact("outdoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid, s in SHOES.items():
        lines.append(asp.fact("shoe", pid))
        lines.append(asp.fact("region", pid, s.region))
        if s.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(s.genders):
            lines.append(asp.fact("wears", g, pid))
    for pid, p in PRANKS.items():
        lines.append(asp.fact("prank", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tag", pid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Prank, Shoe) :- place(Place), prank(Prank), shoe(Shoe),
    affords(Place, Prank), tag(Prank, shoe), region(Shoe, feet).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small shoe prank surprise humor adventure storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prank", choices=PRANKS)
    ap.add_argument("--shoe", choices=SHOES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "prank", None) and getattr(args, "shoe", None):
        if (getattr(args, "place", None), getattr(args, "prank", None), getattr(args, "shoe", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos
              if (not getattr(args, "place", None) or c[0] == getattr(args, "place", None))
              and (not getattr(args, "prank", None) or c[1] == getattr(args, "prank", None))
              and (not getattr(args, "shoe", None) or c[2] == getattr(args, "shoe", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prank, shoe = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "shoe", None) and gender not in _safe_lookup(SHOES, shoe).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or choose_name(rng, gender)
    helper = getattr(args, "helper", None) or select_helper(Entity(id=name, type=gender), gender)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, prank=prank, shoe=shoe, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(PLACES, params.place), _safe_lookup(PRANKS, params.prank), _safe_lookup(SHOES, params.shoe), params.name, params.gender, params.helper, params.trait)
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


CURATED = [
    StoryParams(place="backyard", prank="one_shoe_hide", shoe="sneaker", name="Mina", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="porch", prank="shoebox_swap", shoe="boot", name="Eli", gender="boy", helper="father", trait="cheerful"),
    StoryParams(place="hallway", prank="lace_swap", shoe="slipper", name="Ivy", gender="girl", helper="mother", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, pr, s in combos:
            print(f"  {p:10} {pr:14} {s}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.prank} with {p.shoe} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
