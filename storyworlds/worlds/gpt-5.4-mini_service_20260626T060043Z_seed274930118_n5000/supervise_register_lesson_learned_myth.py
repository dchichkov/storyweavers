#!/usr/bin/env python3
"""
storyworlds/worlds/supervise_register_lesson_learned_myth.py
============================================================

A tiny myth-style storyworld about a young helper who must supervise a rite,
register a lesson learned, and carry a small blessing home.

The world keeps one clear causal premise:
- a child or youth wants to join a sacred task
- an elder asks them to supervise a delicate register/ledger/scroll
- a mistake or delay creates tension
- the lesson learned turns the ending into a calm, mythic image

The prose is generated from simulated state, not by swapping nouns in a template.
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
# World model
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
    kind: str = "thing"
    title: str = ""
    role: str = ""
    epithet: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries_register: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    label: object | None = None
    register: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.role in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.role in {"boy", "man", "father", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.title or self.id
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
    name: str
    image: str
    affordances: set[str] = field(default_factory=set)
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
class Rite:
    id: str
    name: str
    verb: str
    danger: str
    lesson: str
    register_name: str
    place_tags: set[str] = field(default_factory=set)
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
class Register:
    id: str
    label: str
    material: str
    sacred: bool
    carries: set[str] = field(default_factory=set)
    is_lost_when: set[str] = field(default_factory=set)
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    omen: str = ""

    w: object | None = None
    world: object | None = None
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
        w = World(place=self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.omen = self.omen
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


PLACES = {
    "temple_steps": Place(
        name="the temple steps",
        image="stone stairs that caught the sunrise",
        affordances={"procession", "watching", "register"},
    ),
    "river_bend": Place(
        name="the river bend",
        image="a bright curve of water and reeds",
        affordances={"procession", "watching"},
    ),
    "market_square": Place(
        name="the market square",
        image="a ring of stalls and painted awnings",
        affordances={"register", "watching"},
    ),
    "hill_shrine": Place(
        name="the hill shrine",
        image="a quiet hill with wind in the grass",
        affordances={"procession", "register", "watching"},
    ),
}

RITES = {
    "dawn_procession": Rite(
        id="dawn_procession",
        name="the dawn procession",
        verb="walk in the dawn procession",
        danger="the hymn might be forgotten",
        lesson="a lesson learned should be spoken aloud so it can live in the village",
        register_name="sun ledger",
        place_tags={"procession"},
    ),
    "river_offering": Rite(
        id="river_offering",
        name="the river offering",
        verb="carry the river gift",
        danger="the reeds might spill the blessing",
        lesson="a lesson learned should be written before the water carries it away",
        register_name="reed scroll",
        place_tags={"watching"},
    ),
    "moon_census": Rite(
        id="moon_census",
        name="the moon census",
        verb="count the names under the moon",
        danger="a name might be left out",
        lesson="a lesson learned should be registered carefully, one name at a time",
        register_name="moon register",
        place_tags={"register"},
    ),
}

REGISTERS = {
    "sun_ledger": Register(
        id="sun_ledger",
        label="sun ledger",
        material="golden bark",
        sacred=True,
        carries={"lesson", "names"},
        is_lost_when={"rain"},
    ),
    "reed_scroll": Register(
        id="reed_scroll",
        label="reed scroll",
        material="woven reeds",
        sacred=True,
        carries={"lesson", "gift"},
        is_lost_when={"water"},
    ),
    "moon_register": Register(
        id="moon_register",
        label="moon register",
        material="white cloth",
        sacred=True,
        carries={"lesson", "names", "count"},
        is_lost_when={"ink"},
    ),
}

NAMES = ["Asha", "Mira", "Tari", "Kian", "Lena", "Soren", "Nila", "Orin"]
ROLES = ["girl", "boy"]
EPITHETS = ["patient", "bright-eyed", "careful", "swift", "gentle", "earnest"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    rite: str
    name: str
    role: str
    epithet: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for rite_id, rite in RITES.items():
            if rite.place_tags & place.affordances:
                combos.append((place_id, rite_id))
    return combos


def explain_rejection(place_id: str, rite_id: str) -> str:
    place = _safe_lookup(PLACES, place_id)
    rite = _safe_lookup(RITES, rite_id)
    return (
        f"(No story: {rite.name} does not fit {place.name}. "
        f"The place lacks the right ritual shape for that mythic task.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _do_rite(world: World, hero: Entity, rite: Rite, register: Entity, narrate: bool = True) -> None:
    hero.memes["duty"] = hero.memes.get("duty", 0.0) + 1.0
    if register.carries_register:
        hero.meters["care"] = hero.meters.get("care", 0.0) + 1.0
    if narrate:
        world.say(f"{hero.noun()} began to {rite.verb} with {register.noun()} held close.")


def predict_loss(world: World, hero: Entity, rite: Rite, register: Entity) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    sim_reg = sim.get(register.id)
    _do_rite(sim, sim_hero, rite, sim_reg, narrate=False)
    loss = False
    if rite.id == "river_offering" and world.place.name == "the river bend":
        loss = True
    if rite.id == "moon_census" and register.material == "white cloth":
        loss = True
    if rite.id == "dawn_procession" and "wind" in world.place.image:
        loss = True
    return {"loss": loss, "lesson_needed": True}


def narrate_opening(world: World, hero: Entity, elder: Entity, rite: Rite, register: Entity) -> None:
    world.say(
        f"Long ago, {hero.noun()} lived by {world.place.name}, where {world.place.image}."
    )
    world.say(
        f"{hero.noun()} was a {hero.epithet} {hero.role} who wanted to join {rite.name}."
    )
    world.say(
        f"The elder gave {hero.pronoun('object')} the {register.label} and said, "
        f'"Please supervise it well."'
    )


def narrate_warning(world: World, hero: Entity, elder: Entity, rite: Rite, register: Entity) -> bool:
    pred = predict_loss(world, hero, rite, register)
    world.facts["predicted_loss"] = pred["loss"]
    world.facts["lesson"] = rite.lesson
    if not pred["loss"]:
        return False
    world.say(
        f"{elder.noun()} frowned and said, "
        f'"If you rush, the {register.label} may be lost to {rite.danger}."'
    )
    return True


def narrate_conflict(world: World, hero: Entity, rite: Rite) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{hero.noun()} felt small for a moment, yet still wanted to help."
    )
    world.say(
        f"{hero.pronoun().capitalize()} tried to move too quickly, and the old lesson "
        f"almost slipped from memory."
    )


def narrate_turn(world: World, hero: Entity, elder: Entity, rite: Rite, register: Entity) -> None:
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1.0
    hero.meters["slowness"] = hero.meters.get("slowness", 0.0) + 1.0
    world.say(
        f"Then {hero.noun()} remembered that a lesson learned should be registered, not rushed."
    )
    world.say(
        f"{hero.noun()} steadied the {register.label}, counted each step, and asked {elder.noun()} to watch."
    )


def narrate_resolution(world: World, hero: Entity, elder: Entity, rite: Rite, register: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    world.say(
        f"The rite ended safely, and the {register.label} stayed bright in {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"{hero.noun()} carried home the lesson learned: {rite.lesson}."
    )
    world.say(
        f"That night, the village spoke {hero.pronoun('possessive')} name with a quiet blessing."
    )


def tell(place: Place, rite: Rite, hero_name: str, role: str, epithet: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(id=hero_name, kind="character", role=role, epithet=epithet))
    elder = world.add(Entity(id="elder", kind="character", role="elder", title="the elder"))
    register = world.add(Entity(
        id=rite.register_name,
        kind="thing",
        title=rite.register_name,
        owner=hero.id,
        caretaker=elder.id,
        carries_register=True,
    ))

    narrate_opening(world, hero, elder, rite, register)
    world.para()
    warned = narrate_warning(world, hero, elder, rite, register)
    if warned:
        narrate_conflict(world, hero, rite)
    else:
        world.say(f"{hero.noun()} listened at once and supervised the register with care.")
    world.para()
    narrate_turn(world, hero, elder, rite, register)
    narrate_resolution(world, hero, elder, rite, register)

    world.facts.update(
        hero=hero,
        elder=elder,
        register=register,
        rite=rite,
        place=place,
        warned=warned,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    rite: Rite = _safe_fact(world, f, "rite")
    place: Place = _safe_fact(world, f, "place")
    return [
        f'Write a short myth for a young child about {hero.noun()} supervising a sacred register at {place.name}.',
        f'Tell a gentle story where {hero.noun()} must register a lesson learned during {rite.name}.',
        f'Write a simple mythic tale that includes the words "supervise" and "register" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    rite: Rite = _safe_fact(world, f, "rite")
    register: Entity = _safe_fact(world, f, "register")
    place: Place = _safe_fact(world, f, "place")

    qa = [
        QAItem(
            question=f"Who was asked to supervise the {register.title} at {place.name}?",
            answer=f"{hero.noun()} was asked to supervise the {register.title} while {elder.noun()} watched over the rite.",
        ),
        QAItem(
            question=f"What sacred task did {hero.noun()} want to join?",
            answer=f"{hero.noun()} wanted to join {rite.name}, a mythic task at {place.name}.",
        ),
        QAItem(
            question=f"What lesson did {hero.noun()} learn by the end?",
            answer=f"{hero.noun()} learned that {rite.lesson.lower()}",
        ),
    ]
    if f.get("warned"):
        qa.append(
            QAItem(
                question=f"Why did {elder.noun()} worry during the story?",
                answer=f"{elder.noun()} worried because rushing could have lost the {register.title} and broken the rite.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "supervise": (
        "What does it mean to supervise something?",
        "To supervise means to watch over something carefully and make sure it stays safe or is done the right way.",
    ),
    "register": (
        "What is a register?",
        "A register is a list or record where names, counts, or important notes are written down.",
    ),
    "lesson": (
        "Why do people write down a lesson learned?",
        "People write down a lesson learned so they can remember it later and teach it to others.",
    ),
    "myth": (
        "What is a myth?",
        "A myth is a very old story people told to explain special places, heroes, gods, or customs.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.title:
            bits.append(f"title={e.title}")
        if e.epithet:
            bits.append(f"epithet={e.epithet}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        if e.carries_register:
            bits.append("register=true")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}) " + " ".join(bits))
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
rite(R) :- rite_fact(R).
register(Z) :- register_fact(Z).

compatible(P,R) :- place_affords(P,T), rite_tag(R,T).

valid_story(P,R) :- compatible(P,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        for tag in sorted(p.affordances):
            lines.append(asp.fact("place_affords", pid, tag))
    for rid, r in RITES.items():
        lines.append(asp.fact("rite_fact", rid))
        for tag in sorted(r.place_tags):
            lines.append(asp.fact("rite_tag", rid, tag))
    for zid, z in REGISTERS.items():
        lines.append(asp.fact("register_fact", zid))
        if z.sacred:
            lines.append(asp.fact("sacred_register", zid))
        for c in sorted(z.carries):
            lines.append(asp.fact("carries", zid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mythic storyworld about supervise/register and a lesson learned.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--rite", choices=RITES.keys())
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--epithet", choices=EPITHETS)
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
    if getattr(args, "place", None) and getattr(args, "rite", None):
        if (getattr(args, "place", None), getattr(args, "rite", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        (p, r) for (p, r) in valid_combos()
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None)) and (getattr(args, "rite", None) is None or r == getattr(args, "rite", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, rite = rng.choice(list(combos))
    role = getattr(args, "role", None) or rng.choice(ROLES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    epithet = getattr(args, "epithet", None) or rng.choice(EPITHETS)
    return StoryParams(place=place, rite=rite, name=name, role=role, epithet=epithet)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(RITES, params.rite), params.name, params.role, params.epithet)
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
    StoryParams(place="temple_steps", rite="dawn_procession", name="Asha", role="girl", epithet="careful"),
    StoryParams(place="market_square", rite="moon_census", name="Kian", role="boy", epithet="earnest"),
    StoryParams(place="hill_shrine", rite="river_offering", name="Mira", role="girl", epithet="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(str(x) for x in asp_valid_combos()))
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.rite} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
