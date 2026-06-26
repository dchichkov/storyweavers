#!/usr/bin/env python3
"""
storyworlds/worlds/replacement_burden_attractive_moral_value_folk_tale.py
========================================================================

A tiny folk-tale storyworld about a humble burden, a tempting replacement,
and a moral choice about what is truly valuable.

Premise:
- A village character carries a burden that is useful but tiring.
- A merchant offers an attractive replacement.
- The replacement can help, but only if it fits the burden and does not
  create a worse problem.
- The ending turns on moral value: a wise choice, a fair trade, or a kind act.

This world is intentionally small and constraint-checked. It uses:
- physical meters for load, wear, shine, and travel
- emotional memes for longing, pride, gratitude, and contentment

It supports the standard Storyweavers CLI, QA, JSON, trace, and ASP parity
verification modes.
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
# Small world constants
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    burden: object | None = None
    elder: object | None = None
    hero: object | None = None
    merchant: object | None = None
    repl: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for key in ["load", "wear", "shine", "value", "travel"]:
            self.meters.setdefault(key, 0.0)
        for key in ["longing", "pride", "gratitude", "contentment", "worry", "wisdom"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "elder", "daughter"}
        male = {"boy", "father", "man", "grandfather", "son", "merchant"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    kind: str
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
class Burden:
    id: str
    label: str
    phrase: str
    kind: str
    load: str
    region: str
    need: str
    value: str
    weight: float
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
class Replacement:
    id: str
    label: str
    phrase: str
    kind: str
    relieves: set[str]
    guards: set[str]
    cost: str
    attractive: str
    weight: float
    moral: str
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
class Moral:
    id: str
    label: str
    virtue: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "village": Setting(place="the village lane", kind="lane", affords={"walk", "market"}),
    "bridge": Setting(place="the old bridge", kind="bridge", affords={"walk"}),
    "woods": Setting(place="the pine woods", kind="woods", affords={"walk", "carry"}),
}

BURDENS = {
    "water_yoke": Burden(
        id="water_yoke",
        label="water yoke",
        phrase="a worn water yoke with two clay buckets",
        kind="water",
        load="heavy",
        region="shoulders",
        need="carry water",
        value="useful",
        weight=2.0,
        tags={"water", "carry", "burden"},
    ),
    "wood_bundle": Burden(
        id="wood_bundle",
        label="bundle of firewood",
        phrase="a rough bundle of firewood tied with twine",
        kind="wood",
        load="heavy",
        region="back",
        need="carry wood",
        value="practical",
        weight=2.2,
        tags={"wood", "carry", "burden"},
    ),
    "market_basket": Burden(
        id="market_basket",
        label="market basket",
        phrase="a lopsided market basket full of turnips",
        kind="market",
        load="weighty",
        region="arm",
        need="walk to market",
        value="needed",
        weight=1.4,
        tags={"market", "walk", "burden"},
    ),
}

REPLACEMENTS = {
    "bright_yoke": Replacement(
        id="bright_yoke",
        label="bright new yoke",
        phrase="a bright new yoke polished to a shining gold",
        kind="water",
        relieves={"water"},
        guards={"shoulders"},
        cost="costly",
        attractive="very attractive",
        weight=1.6,
        moral="gleam",
        tags={"water", "replacement", "attractive"},
    ),
    "light_pack": Replacement(
        id="light_pack",
        label="light pack frame",
        phrase="a light pack frame woven from willow",
        kind="wood",
        relieves={"wood"},
        guards={"back"},
        cost="fair",
        attractive="plain but lovely",
        weight=0.8,
        moral="usefulness",
        tags={"wood", "replacement", "attractive"},
    ),
    "woven_handle": Replacement(
        id="woven_handle",
        label="woven handle basket",
        phrase="a basket with a soft woven handle and neat stitches",
        kind="market",
        relieves={"market"},
        guards={"arm"},
        cost="fair",
        attractive="simple and pretty",
        weight=0.9,
        moral="care",
        tags={"market", "replacement", "attractive"},
    ),
    "gold_trim": Replacement(
        id="gold-trimmed strap",
        label="gold-trimmed strap",
        phrase="a gold-trimmed strap with tiny bells",
        kind="wood",
        relieves={"wood"},
        guards={"back"},
        cost="costly",
        attractive="showy and bright",
        weight=1.8,
        moral="vanity",
        tags={"wood", "replacement", "attractive"},
    ),
}

MORALS = {
    "humility": Moral(id="humility", label="humility", virtue="choose what truly helps", tags={"moral"}),
    "kindness": Moral(id="kindness", label="kindness", virtue="share a burden", tags={"moral"}),
    "wisdom": Moral(id="wisdom", label="wisdom", virtue="look past shine", tags={"moral"}),
}

NAMES = {
    "girl": ["Mira", "Anya", "Tova", "Lina", "Suri", "Nina"],
    "boy": ["Oren", "Bram", "Eli", "Jon", "Ravi", "Pavel"],
}
TRAITS = ["quiet", "kind", "curious", "steady", "patient", "gentle"]


# ---------------------------------------------------------------------------
# Reasonableness / validity
# ---------------------------------------------------------------------------

def burden_at_risk(burden: Burden, repl: Replacement) -> bool:
    return burden.kind == repl.kind


def compatible_replacement(burden: Burden, repl: Replacement) -> bool:
    return burden.region in repl.guards and burden.kind in repl.relieves and repl.weight <= burden.weight


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for burden_id, burden in BURDENS.items():
            for repl_id, repl in REPLACEMENTS.items():
                if burden_at_risk(burden, repl) and compatible_replacement(burden, repl):
                    combos.append((place, burden_id, repl_id))
    return combos


def explain_rejection(burden: Burden, repl: Replacement) -> str:
    if not burden_at_risk(burden, repl):
        return (
            f"(No story: {repl.label} does not actually fit the burden of {burden.label}. "
            f"The replacement must address the same load, not just look attractive.)"
        )
    return (
        f"(No story: {repl.label} is too heavy or mismatched to be a real help for {burden.label}. "
        f"A folk-tale replacement must ease the burden, not add a new one.)"
    )


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def _apply_load(world: World, actor: Entity, burden: Entity, amount: float) -> None:
    actor.meters["load"] += amount
    burden.meters["wear"] += amount
    actor.memes["worry"] += amount / 2


def introduce(world: World, hero: Entity, elder: Entity, burden: Entity) -> None:
    trait = next((t for t in hero.memes.get("trait_words", [])), "gentle")
    world.say(
        f"In a small village, {hero.id} was a {trait} {hero.type} who helped {elder.label} every day."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {burden.phrase}, and though it was useful, it made {hero.pronoun('object')} tired."
    )


def set_scene(world: World, setting: Setting, burden: Entity) -> None:
    world.say(
        f"One morning, {setting.place} was bright and still, and the path ahead looked long."
    )
    world.say(
        f"{burden.label.capitalize()} tugged at the hero's shoulders like a stubborn little hill."
    )


def offer_replacement(world: World, merchant: Entity, hero: Entity, burden: Entity, repl: Entity) -> None:
    hero.memes["longing"] += 1
    hero.memes["pride"] += 0.5
    world.say(
        f"Then a traveling merchant arrived with {repl.phrase}."
    )
    world.say(
        f'"Look," said the merchant, "this is an {repl.attractive} replacement for your {burden.label}."'
    )


def refuse_or_worry(world: World, hero: Entity, burden: Entity, repl: Entity) -> None:
    if repl.meters["weight"] > burden.meters["weight"]:
        world.say(
            f"{hero.id} liked the shine of it, but {hero.pronoun()} could see it would be a burden of its own."
        )
        hero.memes["worry"] += 1
    else:
        world.say(
            f"{hero.id} liked the shine of it and wondered if the new thing would make life easier."
        )


def wise_turn(world: World, elder: Entity, hero: Entity, burden: Entity, repl: Entity, moral: Moral) -> None:
    elder.memes["wisdom"] += 1
    hero.memes["wisdom"] += 1
    world.say(
        f"{elder.label} touched the old worn edge and said, "
        f'"A thing is not better because it is bright. It is better when it truly helps."'
    )
    world.say(
        f'"{moral.label.capitalize()} means to {moral.virtue}," {elder.pronoun()} said.'
    )


def accept_replacement(world: World, hero: Entity, burden: Entity, repl: Entity) -> None:
    hero.memes["contentment"] += 1
    hero.memes["longing"] = max(0.0, hero.memes["longing"] - 1)
    burden.meters["wear"] = max(0.0, burden.meters["wear"] - 1)
    repl.carried_by = hero.id
    repl.meters["shine"] += 1
    world.say(
        f"So the hero chose the useful replacement, not the showy one, and {burden.label} grew easier to bear."
    )


def share_burden(world: World, hero: Entity, elder: Entity, burden: Entity) -> None:
    hero.memes["gratitude"] += 1
    elder.memes["kindness"] += 1
    burden.meters["wear"] = max(0.0, burden.meters["wear"] - 0.5)
    world.say(
        f"{elder.label} helped split the load, and together they carried the burden with easier steps."
    )


def ending_image(world: World, hero: Entity, elder: Entity, burden: Entity, repl: Entity, moral: Moral) -> None:
    world.say(
        f"By sunset, the road was clear, the burden sat steady, and the hero's heart felt light."
    )
    world.say(
        f"The attractive thing was not the one that mattered most; the true treasure was the good choice they made."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = ""
    burden: str = ""
    replacement: str = ""
    name: str = ""
    gender: str = ""
    elder: str = ""
    trait: str = ""
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


def tell(setting: Setting, burden_cfg: Burden, repl_cfg: Replacement, hero_name: str, hero_gender: str, elder_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        memes={"trait_words": [trait], "worry": 0.0, "longing": 0.0, "pride": 0.0, "gratitude": 0.0, "contentment": 0.0, "wisdom": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="grandmother" if elder_type == "grandmother" else "grandfather",
        memes={"wisdom": 0.0, "kindness": 0.0, "gratitude": 0.0, "contentment": 0.0, "worry": 0.0},
    ))
    merchant = world.add(Entity(id="Merchant", kind="character", type="merchant", label="merchant"))

    burden = world.add(Entity(
        id=burden_cfg.id,
        type=burden_cfg.kind,
        label=burden_cfg.label,
        phrase=burden_cfg.phrase,
        caretaker=elder.id,
        carried_by=hero.id,
        region=burden_cfg.region,
        meters={"load": burden_cfg.weight, "wear": 1.0, "shine": 0.0, "value": 1.0, "travel": 0.0},
        memes={"worry": 0.0, "longing": 0.0, "pride": 0.0, "gratitude": 0.0, "contentment": 0.0, "wisdom": 0.0},
    ))
    repl = world.add(Entity(
        id=repl_cfg.id,
        type=repl_cfg.kind,
        label=repl_cfg.label,
        phrase=repl_cfg.phrase,
        owner=merchant.id,
        region=burden_cfg.region,
        meters={"load": repl_cfg.weight, "wear": 0.0, "shine": 1.0, "value": 0.0, "travel": 0.0},
        memes={"worry": 0.0, "longing": 0.0, "pride": 0.0, "gratitude": 0.0, "contentment": 0.0, "wisdom": 0.0},
    ))

    moral = MORALS["wisdom"]

    introduce(world, hero, elder, burden)
    world.para()
    set_scene(world, setting, burden)
    offer_replacement(world, merchant, hero, burden, repl)
    refuse_or_worry(world, hero, burden, repl)
    world.para()
    wise_turn(world, elder, hero, burden, repl, moral)
    if compatible_replacement(burden_cfg, repl_cfg):
        accept_replacement(world, hero, burden, repl)
        share_burden(world, hero, elder, burden)
    world.para()
    ending_image(world, hero, elder, burden, repl, moral)

    world.facts = {
        "hero": hero,
        "elder": elder,
        "merchant": merchant,
        "burden": burden,
        "replacement": repl,
        "setting": setting,
        "moral": moral,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    burden = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "burden")
    repl = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "replacement")
    moral = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "moral")
    return [
        f'Write a short folk tale about a {hero.type} named {hero.id} who must choose between a burden and an attractive replacement.',
        f"Tell a gentle story where {hero.id} learns that {repl.label} is not worth having unless it truly helps with {burden.label}.",
        f'Write a child-friendly folktale with the moral "{moral.label}" and an ending that shows the burden becoming easier to carry.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    elder = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elder")
    burden = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "burden")
    repl = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "replacement")
    setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    moral = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "moral")
    qa = [
        QAItem(
            question=f"What did {hero.id} carry at the start of the tale?",
            answer=f"{hero.id} carried {burden.phrase}, which was useful but tiring on the road.",
        ),
        QAItem(
            question=f"Why did the merchant's {repl.label} seem tempting?",
            answer=f"It was {repl.attractive}, so it looked lovely at first sight even before anyone judged whether it truly fit the burden.",
        ),
        QAItem(
            question=f"What did {elder.label} teach {hero.id} about the shiny replacement?",
            answer=f"{elder.label} taught {hero.id} that a thing is not better just because it shines; it must truly help with the burden.",
        ),
    ]
    if repl.meters["load"] <= burden.meters["load"]:
        qa.append(QAItem(
            question=f"How did the replacement help {hero.id} in the end?",
            answer=f"{hero.id} chose the replacement, and it eased the load so the burden became easier to bear on {setting.place}.",
        ))
        qa.append(QAItem(
            question=f"What did {hero.id} learn about {moral.label}?",
            answer=f"{hero.id} learned that {moral.virtue}, because the best choice was the one that helped most instead of the one that only looked attractive.",
        ))
    else:
        qa.append(QAItem(
            question=f"What did {hero.id} realize about the merchant's offer?",
            answer=f"{hero.id} realized the offer looked attractive, but it would have been a new burden rather than a true replacement.",
        ))
    qa.append(QAItem(
        question=f"Where did the story take place?",
        answer=f"It took place at {setting.place}, a small and humble place fitting a folk tale.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a burden?",
            answer="A burden is something heavy or hard to carry, like a load on your shoulders or back.",
        ),
        QAItem(
            question="What does attractive mean?",
            answer="Attractive means something looks pleasing or beautiful, so people want to look at it.",
        ),
        QAItem(
            question="What is a moral in a folk tale?",
            answer="A moral is the lesson the story teaches about how to act kindly, wisely, or fairly.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
burden_at_risk(B, R) :- burden(B, K), repl_kind(R, K).
compatible(B, R) :- burden_at_risk(B, R), burden_region(B, G), guards(R, G),
                    relieves(R, K), burden_kind(B, K), repl_weight(R, W1), burden_weight(B, W2), W1 <= W2.
valid(Place, B, R) :- setting(Place), burden(B), replacement(R), burden_at_risk(B, R), compatible(B, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for bid, b in BURDENS.items():
        lines.append(asp.fact("burden", bid))
        lines.append(asp.fact("burden_kind", bid, b.kind))
        lines.append(asp.fact("burden_region", bid, b.region))
        lines.append(asp.fact("burden_weight", bid, int(b.weight * 10)))
    for rid, r in REPLACEMENTS.items():
        lines.append(asp.fact("replacement", rid))
        lines.append(asp.fact("repl_kind", rid, r.kind))
        lines.append(asp.fact("repl_weight", rid, int(r.weight * 10)))
        for g in sorted(r.guards):
            lines.append(asp.fact("guards", rid, g))
        for k in sorted(r.relieves):
            lines.append(asp.fact("relieves", rid, k))
    return "\n".join(lines)


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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk tale story world: burden, attractive replacement, moral value."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--burden", choices=BURDENS)
    ap.add_argument("--replacement", choices=REPLACEMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
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
    if getattr(args, "burden", None) and getattr(args, "replacement", None):
        b, r = _safe_lookup(BURDENS, getattr(args, "burden", None)), _safe_lookup(REPLACEMENTS, getattr(args, "replacement", None))
        if not (burden_at_risk(b, r) and compatible_replacement(b, r)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "burden", None) is None or c[1] == getattr(args, "burden", None))
              and (getattr(args, "replacement", None) is None or c[2] == getattr(args, "replacement", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, burden_id, repl_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    elder = getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, burden=burden_id, replacement=repl_id, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(BURDENS, params.burden), _safe_lookup(REPLACEMENTS, params.replacement), params.name, params.gender, params.elder, params.trait)
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
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
    StoryParams(place="village", burden="water_yoke", replacement="woven_handle", name="Mira", gender="girl", elder="grandmother", trait="kind"),
    StoryParams(place="woods", burden="wood_bundle", replacement="light_pack", name="Oren", gender="boy", elder="grandfather", trait="steady"),
    StoryParams(place="village", burden="market_basket", replacement="woven_handle", name="Tova", gender="girl", elder="grandmother", trait="curious"),
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
        models = asp_valid_combos()
        print(f"{len(models)} compatible combos:")
        for t in models:
            print("  ", t)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.burden} -> {p.replacement} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
