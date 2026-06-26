#!/usr/bin/env python3
"""
A standalone storyworld script for a small Space Adventure domain.

Premise:
- A curious space kid wants a crunchy snack while traveling between stars.
- The ship's caution system warns that a noisy snack choice could attract trouble.
- The crew finds a safer, quieter munchies solution and the trip ends happily.

This world uses typed entities with physical meters and emotional memes, with
state-driven narration, QA generation, and an inline ASP twin for the
reasonableness gate.
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

# Story tuning
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities / world model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    tags: object | None = None
    treat: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        for k in ["hunger", "noise", "risk", "distance", "crumbs", "cleanup"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "curiosity", "defiance", "relief", "caution"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
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
class Ship:
    name: str
    place: str
    quiet_mode: bool = False
    facts: dict = field(default_factory=dict)
    clone: object | None = None
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
class Snack:
    id: str
    label: str
    phrase: str
    crunch: str
    crumbs: str
    smell: str
    noisy: bool = False
    astronomic: bool = False
    safe: bool = False
    keyword: str = ""
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
class Fix:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards_noise: bool = False
    guards_crumbs: bool = False
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


class World:
    def __init__(self, ship: Ship) -> None:
        self.ship = ship
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        clone = World(Ship(self.ship.name, self.ship.place, self.ship.quiet_mode))
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SHIPS = {
    "orbiter": Ship(name="The Little Orbiter", place="the star lane"),
    "comet": Ship(name="The Comet Runner", place="the moon road"),
    "capsule": Ship(name="The Blue Capsule", place="the quiet dock"),
}

SNACKS = {
    "crackers": Snack(
        id="crackers",
        label="star crackers",
        phrase="a tin of star crackers",
        crunch="very crunchy",
        crumbs="full of crumbs",
        smell="buttery",
        noisy=True,
        astronomic=True,
        keyword="munchies",
        tags={"munchies", "sound_effects", "astronomic"},
    ),
    "moonbars": Snack(
        id="moonbars",
        label="moon bars",
        phrase="a packet of moon bars",
        crunch="softly crisp",
        crumbs="a little crumbly",
        smell="sweet",
        noisy=False,
        astronomic=True,
        keyword="astronomic",
        tags={"astronomic", "munchies"},
    ),
    "pebbles": Snack(
        id="pebbles",
        label="planet pebbles",
        phrase="a pouch of planet pebbles",
        crunch="loudly crunchy",
        crumbs="very crumbly",
        smell="salty",
        noisy=True,
        astronomic=False,
        keyword="munchies",
        tags={"munchies", "sound_effects"},
    ),
}

FIXES = {
    "wrap": Fix(
        id="wrap",
        label="a quiet wrap cloth",
        phrase="a quiet wrap cloth",
        prep="wrap the snack in a soft cloth",
        tail="kept the crumbs inside the cloth",
        guards_noise=True,
        guards_crumbs=True,
        tags={"cautionary"},
    ),
    "bag": Fix(
        id="bag",
        label="a crumb bag",
        phrase="a crumb bag",
        prep="seal the snack in a tiny bag",
        tail="kept the smell and crumbs tucked away",
        guards_crumbs=True,
        tags={"cautionary"},
    ),
    "straw": Fix(
        id="straw",
        label="a sip straw",
        phrase="a sip straw",
        prep="use a sip straw with the snack drink",
        tail="made the eating almost soundless",
        guards_noise=True,
        tags={"cautionary"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Ari", "Zia", "Sola"]
BOY_NAMES = ["Orbit", "Pax", "Taj", "Rook", "Elio", "Venn"]
TRAITS = ["curious", "brave", "careful", "lively", "stubborn", "gentle"]


@dataclass
class StoryParams:
    ship: str = ""
    snack: str = ""
    fix: str = ""
    name: str = ""
    gender: str = ""
    adult: str = ""
    trait: str = ""
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


def snack_at_risk(snack: Snack) -> bool:
    return snack.noisy or snack.crumbs != ""


def select_fix(snack: Snack) -> Optional[Fix]:
    for fix in FIXES.values():
        if (not snack.noisy or fix.guards_noise) and (not snack.crumbs or fix.guards_crumbs):
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for ship in SHIPS:
        for snack_id, snack in SNACKS.items():
            for fix_id, fix in FIXES.items():
                if snack_at_risk(snack) and ((not snack.noisy or fix.guards_noise) and (not snack.crumbs or fix.guards_crumbs)):
                    out.append((ship, snack_id, fix_id))
    return out


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def _nibble(world: World, hero: Entity, snack: Snack, narrate: bool = True) -> None:
    hero.meters["hunger"] += 1
    hero.meters["noise"] += 1 if snack.noisy else 0.3
    hero.meters["crumbs"] += 1
    hero.memes["joy"] += 1
    if snack.noisy and narrate:
        world.say(f"CRUNCH! {hero.id} bit into the {snack.label}, and the sound bounced around the cabin.")
    elif narrate:
        world.say(f"{hero.id} nibbled the {snack.label} while the ship hummed softly through space.")


def predict_mess(world: World, hero: Entity, snack: Snack) -> dict:
    sim = world.copy()
    _nibble(sim, sim.get(hero.id), snack, narrate=False)
    risk = sim.get(hero.id).meters["noise"] + sim.get(hero.id).meters["crumbs"]
    return {"risk": risk, "too_loud": sim.get(hero.id).meters["noise"] >= THRESHOLD}


def tell(ship: Ship, snack: Snack, fix: Fix, name: str, gender: str, adult: str, trait: str) -> World:
    world = World(ship)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    parent = world.add(Entity(id="Adult", kind="character", type=adult, label=f"the {adult}"))
    treat = world.add(Entity(
        id=snack.id,
        type="snack",
        label=snack.label,
        phrase=snack.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=False,
    ))
    gear = world.add(Entity(
        id=fix.id,
        type="gear",
        label=fix.label,
        phrase=fix.phrase,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        tags=set(fix.tags),
    ))

    world.say(f"{hero.id} was a little {trait} space {gender} who loved to watch the stars blink by.")
    world.say(f"{hero.pronoun().capitalize()} liked {snack.keyword} snacks, especially {treat.phrase}, because they felt like a tiny adventure.")
    world.say(f"On the {ship.place}, {hero.id}'s {adult} carried {hero.pronoun('object')} past glowing panels and humming tubes.")

    world.para()
    world.say(f"Then {hero.id} wanted to munch the {snack.label} right away.")
    pred = predict_mess(world, hero, snack)
    world.facts["predicted_risk"] = pred["risk"]
    if pred["too_loud"]:
        world.say(f'"That is too loud," {hero.pronoun("possessive")} {adult} said. "It could wake the whole deck."')
        hero.memes["defiance"] += 1
        hero.memes["worry"] += 1
        world.say(f"{hero.id} still leaned toward the snack, and the cabin filled with a risky little buzz.")
        if snack.noisy:
            world.say(f"Outside, the ship met an astronomic lane, and the caution lights blinked as if they were saying beware.")
    else:
        world.say(f"{hero.pronoun('possessive').capitalize()} {adult} gave a small nod, but still suggested a safer way.")

    world.para()
    maybe_fix = select_fix(snack)
    if maybe_fix and maybe_fix.id == gear.id:
        hero.memes["caution"] += 1
        hero.memes["relief"] += 1
        world.say(f'Then {hero.pronoun("possessive").capitalize()} {adult} smiled and said, "{maybe_fix.prep} first."')
        world.say(f"They did exactly that. The {snack.label} went inside {gear.label}, and the ship stayed calm.")
        world.say(f"{maybe_fix.tail.capitalize()}, so the munching stayed neat and quiet.")
        hero.memes["joy"] += 1
    else:
        pass

    world.facts.update(hero=hero, parent=parent, snack=treat, snack_cfg=snack, fix=gear, adult=adult, trait=trait)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A snack is risky if it is noisy or crumbly.
risky(S) :- snack(S), noisy(S).
risky(S) :- snack(S), crumbly(S).

% A fix is compatible if it handles every risky feature of the snack.
covers(F,S) :- fix(F), snack(S), noisy(S), guards_noise(F).
covers(F,S) :- fix(F), snack(S), crumbly(S), guards_crumbs(F).

has_fix(S) :- covers(_, S).
valid(Ship, Snack, Fix) :- ship(Ship), snack(Snack), fix(Fix), risky(Snack), covers(Fix, Snack).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHIPS:
        lines.append(asp.fact("ship", sid))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if s.noisy:
            lines.append(asp.fact("noisy", sid))
        if s.crumbs:
            lines.append(asp.fact("crumbly", sid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        if f.guards_noise:
            lines.append(asp.fact("guards_noise", fid))
        if f.guards_crumbs:
            lines.append(asp.fact("guards_crumbs", fid))
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
    print("MISMATCH between clingo and python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    snack = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "snack_cfg")
    return [
        f'Write a short Space Adventure story for a child named {hero.id} that includes "{snack.keyword}" and a cautious choice.',
        f"Tell a gentle story where {hero.id} wants to eat {snack.phrase} on a ship, but the adult warns about the sound effects.",
        f"Write a story with stars, snacks, and a safe fix that keeps the cabin quiet.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    adult = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "adult")
    snack = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "snack")
    snack_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "snack_cfg")
    fix = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "fix")
    trait = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trait")
    return [
        QAItem(
            question=f"Who wanted the {snack.label} on the ship?",
            answer=f"It was {hero.id}, a little {trait} space {hero.type}, who wanted the {snack.label}.",
        ),
        QAItem(
            question=f"Why did the {adult} say the snack was too loud?",
            answer=f"Because the {snack.label} made a big crunch, and the sound could echo through the ship's cabin.",
        ),
        QAItem(
            question=f"What cautious thing helped keep the munching safe?",
            answer=f"They used {fix.label}, which kept the snack quieter and neater for everyone on the ship.",
        ),
        QAItem(
            question=f"What word in the story points to the snack idea?",
            answer=f'The story uses the word "{snack_cfg.keyword}" for the snacky, adventurous feeling.',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    snack_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "snack_cfg")
    out = [
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are extra noises, like crunching or whooshing, that make a story feel lively.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means giving a warning so someone can avoid a problem or stay safe.",
        ),
    ]
    if snack_cfg.noisy:
        out.append(QAItem(
            question="Why can crunchy snacks be tricky in a quiet place?",
            answer="Crunchy snacks can be tricky because the loud noises may disturb other people or make more trouble.",
        ))
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with munchies, astronomic caution, and sound effects.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father", "captain", "pilot"])
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
    if getattr(args, "snack", None) and getattr(args, "fix", None):
        snack = _safe_lookup(SNACKS, getattr(args, "snack", None))
        fix = _safe_lookup(FIXES, getattr(args, "fix", None))
        if not ((not snack.noisy or fix.guards_noise) and (not snack.crumbs or fix.guards_crumbs)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "ship", None) is None or c[0] == getattr(args, "ship", None))
              and (getattr(args, "snack", None) is None or c[1] == getattr(args, "snack", None))
              and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    ship, snack_id, fix_id = rng.choice(list(combos))
    snack = _safe_lookup(SNACKS, snack_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(["mother", "father", "captain", "pilot"])
    trait = rng.choice(TRAITS)
    return StoryParams(ship=ship, snack=snack_id, fix=fix_id, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SHIPS, params.ship), _safe_lookup(SNACKS, params.snack), _safe_lookup(FIXES, params.fix), params.name, params.gender, params.adult, params.trait)
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
        print("\n--- world model state ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: type={e.type}, meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}, memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(ship="orbiter", snack="crackers", fix="wrap", name="Nova", gender="girl", adult="captain", trait="curious"),
    StoryParams(ship="comet", snack="pebbles", fix="bag", name="Rook", gender="boy", adult="pilot", trait="brave"),
    StoryParams(ship="capsule", snack="moonbars", fix="straw", name="Mira", gender="girl", adult="mother", trait="careful"),
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
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
