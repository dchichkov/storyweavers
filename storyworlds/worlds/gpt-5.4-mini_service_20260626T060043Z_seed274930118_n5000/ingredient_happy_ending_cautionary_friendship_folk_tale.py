#!/usr/bin/env python3
"""
ingredient_happy_ending_cautionary_friendship_folk_tale.py
==========================================================

A small folk-tale storyworld about an ingredient, a friendship, and a warning
that leads to a happy ending.

Premise:
- A humble cook or helper has a single important ingredient.
- A friend wants to rush, share, or improve the dish.
- Their good intentions create a small risk: the ingredient may be ruined,
  wasted, or over-seasoned.
- The friend listens to a caution, adjusts the method, and the story ends in a
  warm shared meal.

The world is intentionally compact: a few ingredients, a few vessels, a few
helpers, and a few sensible fixes. Story state drives the prose and QA.
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



def _safe_next(iterable, fallback=None):
    return next(iter(iterable), fallback)


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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    vessel: Optional[str] = None
    edible: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    ing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "grandfather"}:
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
    label: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
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
class Ingredient:
    id: str
    label: str
    phrase: str
    taste: str
    fragile: bool = False
    needs: set[str] = field(default_factory=set)
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
class Vessel:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
    prep: str = ""
    ending: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def safe_join(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def ingredient_at_risk(place: Place, ingredient: Ingredient, vessel: Vessel) -> bool:
    return ingredient.id in place.affords and ingredient.needs.intersection(vessel.helps)


def select_vessel(ingredient: Ingredient, vessels: list[Vessel]) -> Optional[Vessel]:
    for v in vessels:
        if ingredient.needs.issubset(v.helps) and ingredient.fragile and "gentle" in v.protects:
            return v
    for v in vessels:
        if ingredient.needs.issubset(v.helps):
            return v
    return None


def reasonableness_gate(place: Place, ingredient: Ingredient, vessel: Vessel) -> bool:
    return ingredient_at_risk(place, ingredient, vessel)


def _apply_spoil(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "thing" or ent.label != "ingredient":
            continue
        if ent.meters.get("bitter", 0.0) < THRESHOLD:
            continue
        if ent.vessel is None:
            sig = ("spoil", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.meters["ruined"] = 1.0
            out.append(f"The ingredient went wrong and lost its good taste.")
    return out


def _apply_friend_help(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes.get("care", 0.0) < THRESHOLD:
            continue
        sig = ("help", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{ent.id} offered a gentler way.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for rule in (_apply_spoil, _apply_friend_help):
        msgs = rule(world)
        produced.extend(msgs)
    if narrate:
        for m in produced:
            world.say(m)
    return produced


def build_story_world(place: Place, hero_name: str, hero_kind: str, friend_name: str, friend_kind: str,
                      ingredient: Ingredient, vessel: Vessel, helper_vessel: Optional[Vessel]) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_kind))
    ing = world.add(Entity(
        id=ingredient.id,
        kind="thing",
        type="ingredient",
        label="ingredient",
        phrase=ingredient.phrase,
        edible=True,
        fragile=ingredient.fragile,
    ))
    ing.vessel = vessel.id

    # Setup.
    hero.memes["hope"] = 1.0
    friend.memes["care"] = 1.0
    world.say(f"Once, near {place.label.lower()}, there lived {hero_name}, who treasured a fine ingredient: {ingredient.phrase}.")
    world.say(f"{hero_name} meant to make a little dish for {friend_name}, and the two were friends with kind hearts.")
    world.say(f"They had {vessel.phrase} ready, because the ingredient asked for care.")

    # Conflict.
    world.para()
    world.say(f"But {friend_name} grew eager and wanted to hurry the cooking.")
    hero.memes["worry"] = 1.0
    ing.meters["bitter"] = 1.0
    propagate(world, narrate=False)
    world.say(f"{hero_name} warned, “Easy now. This ingredient can turn plain if we are rough with it.”")
    world.say(f"{friend_name} paused, listening closely instead of rushing ahead.")

    # Resolution.
    world.para()
    if helper_vessel is not None:
        world.say(f"Then they chose {helper_vessel.phrase} as the gentler way.")
        ing.vessel = helper_vessel.id
        world.say(f"{helper_vessel.prep.capitalize()} and work slowly.")
        world.say(f"{friend_name} stirred with care, and {hero_name} smiled at the quiet teamwork.")
        ing.meters["bitter"] = 0.0
        ing.meters["ruined"] = 0.0
        ing.meters["sweet"] = 1.0
        world.say(f"At last, the ingredient kept its flavor, and the little dish smelled warm and good.")
        world.say(f"The friends shared it together, and the evening ended with full bellies and brighter faces.")
    else:
        world.say(f"They changed the plan and chose patience over haste.")
        ing.meters["bitter"] = 0.0
        ing.meters["sweet"] = 1.0
        world.say(f"The ingredient stayed useful, and the dish came out fine after all.")
        world.say(f"That made the friends laugh, because listening had saved the supper.")

    world.facts.update(
        hero=hero,
        friend=friend,
        ingredient=ing,
        vessel=vessel,
        helper_vessel=helper_vessel,
        place=place,
    )
    return world


PLACES = {
    "cottage": Place(id="cottage", label="the cottage kitchen", indoors=True, affords={"stew", "porridge"}),
    "garden": Place(id="garden", label="the garden hearth", indoors=False, affords={"stew"}),
    "bakery": Place(id="bakery", label="the bakery corner", indoors=True, affords={"bread", "soup"}),
}

INGREDIENTS = {
    "berry": Ingredient(id="berry", label="berries", phrase="a bowl of bright berries", taste="sweet", fragile=True, needs={"gentle"}),
    "honey": Ingredient(id="honey", label="honey", phrase="a small jar of honey", taste="sweet", fragile=False, needs={"warm"}),
    "herb": Ingredient(id="herb", label="herbs", phrase="a handful of green herbs", taste="fresh", fragile=False, needs={"gentle"}),
    "grain": Ingredient(id="grain", label="grain", phrase="a sack of grain", taste="plain", fragile=False, needs={"mild"}),
}

VESSELS = [
    Vessel(id="wooden_bowl", label="wooden bowl", phrase="a smooth wooden bowl", helps={"gentle", "mild"}, protects={"gentle"}, prep="They set the wooden bowl on the table"),
    Vessel(id="stone_pot", label="stone pot", phrase="a heavy stone pot", helps={"warm", "mild"}, protects={"warm"}, prep="They warmed the stone pot by the fire"),
    Vessel(id="woven_basket", label="woven basket", phrase="a woven basket", helps={"gentle"}, protects={"gentle"}, prep="They lined the woven basket with clean cloth"),
]

HELPER_VESSELS = {
    "berry": "wooden_bowl",
    "honey": "stone_pot",
    "herb": "woven_basket",
    "grain": "wooden_bowl",
}

HERO_NAMES = ["Aina", "Milo", "Sora", "Niko", "Pella", "Rowan"]
FRIEND_NAMES = ["Brin", "Jessa", "Toma", "Lina", "Edda", "Pip"]
KINDS = ["girl", "boy", "woman", "man"]


@dataclass
class StoryParams:
    place: str = ""
    ingredient: str = ""
    hero_name: str = ""
    hero_kind: str = ""
    friend_name: str = ""
    friend_kind: str = ""
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place in PLACES.values():
        for ing in INGREDIENTS.values():
            if any(v for v in VESSELS if reasonableness_gate(place, ing, v)):
                combos.append((place.id, ing.id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about a friendship, a caution, and an ingredient: "{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ingredient").phrase}".',
        f"Tell a warm story in which {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend").id} work together near {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").label.lower()} and choose the safer cooking vessel.",
        f"Write a happy-ending tale where a friend listens to a warning so the ingredient stays good.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    ing = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ingredient")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper_vessel")
    qa = [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {hero.id} and {friend.id}. They cared about the dish and worked together.",
        ),
        QAItem(
            question=f"What ingredient did they protect?",
            answer=f"They protected {ing.phrase}, so it would keep its taste and not be ruined by haste.",
        ),
        QAItem(
            question=f"Why did the first plan need a warning?",
            answer=f"The first plan was too rushed for {ing.phrase}. {hero.id} warned that rough handling could make it go plain or bitter.",
        ),
    ]
    if helper:
        qa.append(
            QAItem(
                question=f"How did {helper.phrase} help at the end?",
                answer=f"They chose {helper.phrase} because it was gentler, and that let the ingredient stay safe while they finished the meal.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    ing: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ingredient")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    out = [
        QAItem(
            question="What is an ingredient?",
            answer="An ingredient is something you put into food to help make a meal, like fruit, grain, herbs, or honey.",
        ),
        QAItem(
            question="Why should some ingredients be handled gently?",
            answer="Some ingredients are fragile or delicate, so gentle handling helps them keep their taste, shape, or smell.",
        ),
        QAItem(
            question="What does a friend do in a folk tale?",
            answer="A friend helps, listens, and stays loyal, especially when there is a problem to solve together.",
        ),
    ]
    if ing.type == "ingredient":
        out.append(QAItem(
            question=f"What kind of place was {place.label.lower()}?",
            answer=f"{place.label.capitalize()} was a cooking place, and the story used it as the setting for a careful meal.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.vessel:
            bits.append(f"vessel={e.vessel}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", ingredient="berry", hero_name="Aina", hero_kind="girl", friend_name="Brin", friend_kind="boy"),
    StoryParams(place="bakery", ingredient="honey", hero_name="Milo", hero_kind="boy", friend_name="Jessa", friend_kind="girl"),
    StoryParams(place="garden", ingredient="herb", hero_name="Sora", hero_kind="woman", friend_name="Toma", friend_kind="man"),
]


ASP_RULES = r"""
% A story is valid when a place affords an ingredient-type situation and at
% least one vessel matches the ingredient's needs.
valid(P, I) :- place(P), ingredient(I), place_affords(P, I), has_fix(I).

has_fix(I) :- ingredient_needs(I, N), vessel_helps(V, N), vessel_safe(V, I).
vessel_safe(V, I) :- vessel(V), not blocked(V, I).
blocked(V, I) :- fragile(I), vessel(V), not vessel_protects(V, gentle).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        if p.indoors:
            lines.append(asp.fact("indoors", p.id))
        for a in sorted(p.affords):
            lines.append(asp.fact("place_affords", p.id, a))
    for i in INGREDIENTS.values():
        lines.append(asp.fact("ingredient", i.id))
        if i.fragile:
            lines.append(asp.fact("fragile", i.id))
        for n in sorted(i.needs):
            lines.append(asp.fact("ingredient_needs", i.id, n))
    for v in VESSELS:
        lines.append(asp.fact("vessel", v.id))
        for h in sorted(v.helps):
            lines.append(asp.fact("vessel_helps", v.id, h))
        for p in sorted(v.protects):
            lines.append(asp.fact("vessel_protects", v.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about an ingredient, friendship, and caution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ingredient", choices=INGREDIENTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-kind", choices=KINDS)
    ap.add_argument("--friend-kind", choices=KINDS)
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
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "ingredient", None) is None or c[1] == getattr(args, "ingredient", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, ingredient = rng.choice(list(combos))
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(KINDS)
    friend_kind = getattr(args, "friend_kind", None) or rng.choice(KINDS)
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, ingredient=ingredient, hero_name=hero_name, hero_kind=hero_kind, friend_name=friend_name, friend_kind=friend_kind)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    ing = _safe_lookup(INGREDIENTS, params.ingredient)
    vessel = _safe_next((v for v in VESSELS if reasonableness_gate(place, ing, v)), next(iter(VESSELS), None))
    helper_vessel = next((v for v in VESSELS if v.id == HELPER_VESSELS.get(ing.id)), None)
    world = build_story_world(place, params.hero_name, params.hero_kind, params.friend_name, params.friend_kind, ing, vessel, helper_vessel)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, i in combos:
            print(f"  {p} {i}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
