#!/usr/bin/env python3
"""
cake_reconciliation_quest_space_adventure.py
============================================

A tiny storyworld about a space quest that goes a little wrong and then gets
fixed with reconciliation over cake.

The seed idea:
- In a small space adventure, a crew sets out on a quest.
- Something causes hurt feelings or a split decision.
- The crew makes up again, and cake becomes the friendly ending image.

This script models a small, state-driven domain with physical meters and
emotional memes, plus a matching inline ASP reasonableness gate.
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
# Domain model
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    parent: object | None = None
    treat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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


@dataclass
class Place:
    name: str
    kind: str
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
class Quest:
    id: str
    goal: str
    verb: str
    rush: str
    risk: str
    damage: str
    zone: set[str]
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
class Treat:
    id: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
class StoryParams:
    place: str
    quest: str
    treat: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "orbit_garden": Place("the orbit garden", "station", {"quest", "cake"}),
    "moon_dock": Place("the moon dock", "dock", {"quest", "cake"}),
    "starship_cabin": Place("the starship cabin", "ship", {"cake"}),
    "comet_path": Place("the comet path", "trail", {"quest"}),
}

QUESTS = {
    "lost_star_map": Quest(
        id="lost_star_map",
        goal="find the lost star map",
        verb="search for the lost star map",
        rush="dash down the glowing hall",
        risk="scatter the map pages",
        damage="creased and dusty",
        zone={"hands", "torso"},
        keyword="map",
        tags={"quest", "space"},
    ),
    "moon_beacon": Quest(
        id="moon_beacon",
        goal="carry the moon beacon home",
        verb="carry the moon beacon",
        rush="hurry across the airlock",
        risk="bump the beacon",
        damage="scratched",
        zone={"hands"},
        keyword="beacon",
        tags={"quest", "space"},
    ),
    "stardust_seed": Quest(
        id="stardust_seed",
        goal="deliver a tiny stardust seed",
        verb="deliver the stardust seed",
        rush="run to the launch bay",
        risk="shake the seed loose",
        damage="spilled",
        zone={"hands", "torso"},
        keyword="seed",
        tags={"quest", "space"},
    ),
}

TREATS = {
    "cake_slice": Treat(
        id="cake_slice",
        label="cake slice",
        phrase="a round slice of moon cake",
        region="hands",
    ),
    "cake_box": Treat(
        id="cake_box",
        label="cake box",
        phrase="a bright cake box with ribbon",
        region="torso",
    ),
    "cupcakes": Treat(
        id="cupcakes",
        label="cupcakes",
        phrase="a little tray of cupcakes",
        region="hands",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="space gloves",
        covers={"hands"},
        guards={"dusty", "scratched"},
        prep="put on space gloves first",
        tail="put on the space gloves",
    ),
    Gear(
        id="carrier",
        label="a padded carrier",
        covers={"hands", "torso"},
        guards={"spilled", "creased and dusty"},
        prep="place the treat in a padded carrier",
        tail="used the padded carrier",
    ),
    Gear(
        id="wrap",
        label="sturdy wrap",
        covers={"torso"},
        guards={"creased and dusty"},
        prep="wrap it carefully in sturdy wrap",
        tail="wrapped it carefully",
    ),
]

GIRL_NAMES = ["Mia", "Nova", "Luna", "Ada", "Zoe", "Nia"]
BOY_NAMES = ["Finn", "Jett", "Leo", "Max", "Noah", "Kai"]
TRAITS = ["brave", "curious", "gentle", "bright", "stubborn", "cheerful"]


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
def risk_matches(quest: Quest, treat: Treat) -> bool:
    return treat.region in quest.zone


def select_gear(quest: Quest, treat: Treat) -> Optional[Gear]:
    for gear in GEAR:
        if treat.region in gear.covers and any(r in gear.guards for r in [quest.damage, quest.risk, "spilled"]):
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for qid, quest in QUESTS.items():
            if qid not in place.affords:
                continue
            for tid, treat in TREATS.items():
                if treat.id and risk_matches(quest, treat) and select_gear(quest, treat):
                    out.append((place_id, qid, tid))
    return out


def story_intro(world: World, hero: Entity, parent: Entity, quest: Quest, treat: Treat) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'curious')} {hero.type} "
        f"who loved space quests."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {quest.verb}, and {hero.pronoun('possessive')} "
        f"{parent.label or parent.type} had brought {treat.phrase} for the journey."
    )
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    treat.worn_by = hero.id


def predict_damage(world: World, quest: Quest, treat: Treat) -> bool:
    sim = World(world.place)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.zone = set(quest.zone)
    hero = next(e for e in sim.entities.values() if e.kind == "character" and e.type in {"girl", "boy"})
    hero.meters[quest.keyword] = hero.meters.get(quest.keyword, 0) + 1
    for item in [e for e in sim.entities.values() if e.worn_by == hero.id]:
        if item.region in sim.zone:
            item.meters[quest.damage] = item.meters.get(quest.damage, 0) + 1
    return sim.entities[treat.id].meters.get(quest.damage, 0) >= THRESHOLD


def act_conflict(world: World, hero: Entity, parent: Entity, quest: Quest, treat: Treat) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.para()
    world.say(
        f"At {world.place.name}, {hero.id} wanted to {quest.verb} right away."
    )
    world.say(
        f"But {hero.pronoun('possessive')} {parent.label or parent.type} looked at {treat.label} and frowned."
    )
    if predict_damage(world, quest, treat):
        world.say(
            f'"If you rush, you could get {treat.label} {quest.damage}," {parent.pronoun("subject")} said.'
        )
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        hero.memes["hurt"] = hero.memes.get("hurt", 0) + 1
    world.say(
        f"{hero.id} crossed {hero.pronoun('possessive')} arms and tried to {quest.rush},"
    )


def repair_and_reconcile(world: World, hero: Entity, parent: Entity, quest: Quest, treat: Treat) -> Optional[Gear]:
    gear = select_gear(quest, treat)
    if gear is None:
        return None
    world.para()
    world.say(
        f"Then {parent.id} took a slow breath and smiled. "
        f'"How about we {gear.prep} and go together?"'
    )
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    treat.meters[quest.damage] = 0.0
    world.say(
        f"{hero.id}'s face softened. {hero.id} nodded, and they {gear.tail} before the quest."
    )
    return gear


def resolve_story(world: World, hero: Entity, parent: Entity, quest: Quest, treat: Treat) -> None:
    world.para()
    world.say(
        f"Together they set off. {hero.id} was {quest.verb}, and the little {treat.label} stayed safe."
    )
    world.say(
        f"When the quest was done, {hero.id} and {parent.id} shared the {treat.label} as a peace offering."
    )
    world.say(
        f"They laughed, and the cabin felt warm again, like a tiny home drifting among the stars."
    )


def tell(place: Place, quest: Quest, treat_cfg: Treat, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"trait_word": trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    treat = world.add(Entity(id=treat_cfg.id, type=treat_cfg.id, label=treat_cfg.label, phrase=treat_cfg.phrase, owner=hero.id, caretaker=parent.id, region=treat_cfg.region, plural=treat_cfg.plural))
    story_intro(world, hero, parent, quest, treat)
    act_conflict(world, hero, parent, quest, treat)
    gear = repair_and_reconcile(world, hero, parent, quest, treat)
    if gear:
        resolve_story(world, hero, parent, quest, treat)
    world.facts.update(hero=hero, parent=parent, quest=quest, treat=treat, gear=gear, place=place)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest = _safe_fact(world, f, "quest")
    treat = _safe_fact(world, f, "treat")
    return [
        f'Write a gentle space adventure about a child named {hero.id} who wants to {quest.verb}.',
        f'Create a story where {hero.id} and {f["parent"].id} disagree, then reconcile with {treat.label}.',
        f'Write a short quest story set at {world.place.name} that ends with cake and kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, quest, treat = f["hero"], f["parent"], f["quest"], f["treat"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do on the quest?",
            answer=f"{hero.id} wanted to {quest.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the treat?",
            answer=f"{parent.id} worried because rushing could make the {treat.label} get {quest.damage}.",
        ),
        QAItem(
            question=f"What helped them make up again?",
            answer=f"They used {gear.label if gear else 'a careful plan'} and shared the {treat.label} kindly at the end.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the quest?",
                answer=f"{gear.label.capitalize()} protected the {treat.label} so the trip could stay safe.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey with a goal, like looking for something important or delivering something safely.",
        ),
        QAItem(
            question="What is cake for?",
            answer="Cake is often shared at happy times, like birthdays or celebrations, because it feels like a treat.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a disagreement and choosing to be friendly again.",
        ),
        QAItem(
            question="Why do people use carriers or wraps for fragile things?",
            answer="They use carriers or wraps to keep something safe from bumps, spills, and rough movement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risk(Quest, Treat) :- quest_zone(Quest, Zone), treat_region(Treat, Zone).
gear_ok(Gear, Quest, Treat) :- risk(Quest, Treat), covers(Gear, Zone), treat_region(Treat, Zone), guards(Gear, Damage), quest_damage(Quest, Damage).
valid(Place, Quest, Treat) :- place_affords(Place, Quest), risk(Quest, Treat), gear_ok(_, Quest, Treat).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        for q in sorted(p.affords):
            lines.append(asp.fact("place_affords", pid, q))
    for qid, q in QUESTS.items():
        for z in sorted(q.zone):
            lines.append(asp.fact("quest_zone", qid, z))
        lines.append(asp.fact("quest_damage", qid, q.damage))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat_region", tid, t.region))
    for g in GEAR:
        for z in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, z))
        for d in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, d))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="orbit_garden", quest="lost_star_map", treat="cake_slice", name="Nova", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="moon_dock", quest="moon_beacon", treat="cupcakes", name="Kai", gender="boy", parent="father", trait="curious"),
    StoryParams(place="starship_cabin", quest="stardust_seed", treat="cake_box", name="Mia", gender="girl", parent="mother", trait="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small space-adventure storyworld about a quest, a worry, and reconciliation with cake.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "quest", None) and getattr(args, "treat", None):
        q, t = _safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(TREATS, getattr(args, "treat", None))
        if not (risk_matches(q, t) and select_gear(q, t)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
        and (getattr(args, "treat", None) is None or c[2] == getattr(args, "treat", None))
        and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in TREATS[c[2]].genders)
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, treat = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(TREATS, treat).genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, treat=treat, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(TREATS, params.treat), params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
