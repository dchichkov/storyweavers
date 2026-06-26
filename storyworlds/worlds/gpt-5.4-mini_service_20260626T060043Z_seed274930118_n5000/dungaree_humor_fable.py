#!/usr/bin/env python3
"""
storyworlds/worlds/dungaree_humor_fable.py
==========================================

A tiny fable-style story world about a dungaree, a bit of humor, and a small
moral choice.

Premise:
- A young character loves wearing a cherished dungaree.
- The dungaree makes the character feel bold and funny.
- A tempting choice risks ruining the dungaree.
- A wiser, playful compromise keeps the story gentle and ends in a laugh.

The world model tracks physical state in meters and social-emotional state in
memes, then narrates from those changing facts.
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
# Data model
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

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    temp: object | None = None
    def __post_init__(self) -> None:
        for k in ["dirty", "sprayed", "torn", "bright"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "humor", "worry", "pride", "relief", "wisdom"]:
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    joke: str
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
class Prize:
    label: str
    phrase: str
    region: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.label in {"a rain cape", "the apron"} and region in getattr(item, "covers", set())
                   for item in self.worn_items(actor))

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "barn": Place(name="the barn", affords={"mud", "splash"}),
    "kitchen": Place(name="the kitchen", affords={"flour"}),
    "garden": Place(name="the garden", affords={"mud", "splash", "paint"}),
}

ACTIONS = {
    "mud": Activity(
        id="mud",
        verb="jump in the muddy patch",
        gerund="jumping in the muddy patch",
        rush="run to the muddy patch",
        mess="muddy",
        zone={"legs"},
        keyword="mud",
        joke="the mud had better manners than a silent pig",
    ),
    "splash": Activity(
        id="splash",
        verb="splash in the puddle",
        gerund="splashing in the puddle",
        rush="dash into the puddle",
        mess="wet",
        zone={"legs", "torso"},
        keyword="splash",
        joke="the puddle looked like a silver bowl of giggles",
    ),
    "flour": Activity(
        id="flour",
        verb="toss flour in the air",
        gerund="tossing flour in the air",
        rush="grab the flour sack",
        mess="dusty",
        zone={"torso"},
        keyword="flour",
        joke="the flour puffed up like a sleepy cloud",
    ),
    "paint": Activity(
        id="paint",
        verb="paint the fence with bright stripes",
        gerund="painting bright stripes",
        rush="fetch the paint pot",
        mess="painted",
        zone={"torso"},
        keyword="paint",
        joke="the fence looked as if a rainbow had practiced a joke",
    ),
}

PRIZES = {
    "dungaree": Prize(
        label="dungaree",
        phrase="a sturdy blue dungaree with brass buttons",
        region="torso",
        plural=False,
    )
}

GEAR = [
    Gear(
        id="apron",
        label="the apron",
        covers={"torso"},
        guards={"painted", "dusty"},
        prep="put on the apron",
        tail="went back with the apron on",
    ),
    Gear(
        id="cape",
        label="a rain cape",
        covers={"torso", "legs"},
        guards={"wet", "muddy"},
        prep="wear a rain cape first",
        tail="went back wearing the rain cape",
    ),
]


GIRL_NAMES = ["Mina", "Nora", "Lila", "Zia", "Poppy", "Maya"]
BOY_NAMES = ["Toby", "Owen", "Finn", "Rafi", "Ezra", "Jude"]
TRAITS = ["cheerful", "curious", "mischievous", "bright-eyed", "gentle", "sly"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narration helpers
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def setting_line(place: Place, act: Activity) -> str:
    if place.name == "the kitchen":
        return "The kitchen smelled of warm bread, and the floor shone like a patient spoon."
    if act.id == "flour":
        return "The table waited by the window, where the light could catch every silly puff."
    return f"{place.name.capitalize()} looked ready for trouble, as fables often do."


def moral_line() -> str:
    return "The cleverest laughter is the kind that keeps a good coat clean."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.place.affords:
        return
    world.zone = set(activity.zone)
    actor.memes["joy"] += 1
    actor.memes["humor"] += 1
    if activity.mess in {"muddy", "wet", "painted", "dusty"}:
        actor.meters[activity.mess] += 1
    for item in world.worn_items(actor):
        if item.label == "dungaree" and not world.covered(actor, "torso") and "torso" in world.zone:
            item.meters[activity.mess] += 1
            item.meters["dirty"] += 1
            if narrate:
                world.say(f"{actor.pronoun('possessive').capitalize()} dungaree picked up {activity.mess} and looked sad.")
    if narrate and actor.meters.get(activity.mess, 0) >= 1:
        world.say(f"The place filled with the sort of mess that makes children grin and adults sigh.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= 1, "mess": activity.mess}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.memes['humor'] and 'small' or 'small'} {hero.type} who loved a good joke and a tidy hem.")
    world.say(f"{hero.pronoun().capitalize()} thought the dungaree made every step look brave.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["pride"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} wore {prize.phrase}, and {prize.it()} fit as if it had been sewn by a kind moonbeam.")


def wants(world: World, hero: Entity, parent: Entity, act: Activity) -> None:
    hero.memes["worry"] += 0.5
    world.say(f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} {parent.type} lifted a careful eyebrow.")


def warn(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, act, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_mess"] = act.mess
    world.say(f'"If you {act.verb}, your {prize.label} will get {act.mess}," {parent.pronoun("possessive")} {parent.type} said.')
    return True


def joke_before_warning(world: World, hero: Entity, act: Activity) -> None:
    world.say(f"{hero.id} gave a tiny grin. \"{act.joke},\" {hero.pronoun()} whispered, and even the barn seemed to chuckle.")


def defies(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(f"Still, {hero.id} tried to {act.rush}, certain the day could not be serious for long.")


def resolve(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(act, prize)
    if gear is None:
        return None
    temp = world.add(Entity(id=gear.id, kind="thing", type="gear", label=gear.label, owner=hero.id))
    temp.worn_by = hero.id
    setattr(temp, "covers", set(gear.covers))
    if predict_mess(world, hero, act, prize.id)["soiled"]:
        temp.worn_by = None
        del world.entities[temp.id]
        return None
    world.say(f'{parent.id} smiled. "How about you {gear.prep} and still {act.verb}?"')
    return gear


def accept(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["wisdom"] += 1
    world.say(f"{hero.id} laughed, and the laugh was so bright that it sounded like a spoon tapping a cup.")
    world.say(f'They {gear.tail}. Soon {hero.id} was {act.gerund}, {prize.label} stayed clean, and the joke followed them like a friendly dog.')
    world.say(moral_line())


def tell(
    place: Place,
    act: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mina",
    hero_type: str = "girl",
    parent_type: str = "mother",
    hero_traits: Optional[list[str]] = None,
) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"humor": 1.0, "pride": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="dungaree", type="dungaree", label="dungaree", phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id))
    hero.memes["humor"] += 0.5 if hero_traits and "mischievous" in hero_traits else 0

    world.say(f"{hero.id} was a {', '.join(hero_traits or ['cheerful'])} little {hero.type}.")
    introduce(world, hero)
    loves_prize(world, hero, prize)

    world.para()
    world.say(setting_line(place, act))
    wants(world, hero, parent, act)
    warn(world, parent, hero, act, prize)
    joke_before_warning(world, hero, act)
    defies(world, hero, act)

    world.para()
    gear = resolve(world, parent, hero, act, prize)
    if gear:
        accept(world, parent, hero, act, prize, gear)
    else:
        world.say(f"In the end, they chose a quieter game, and the dungaree stayed bright.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=act, place=place, gear=gear, resolved=gear is not None)
    return world


# ---------------------------------------------------------------------------
# Q&A and knowledge
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "dungaree": [(
        "What is a dungaree?",
        "A dungaree is a sturdy piece of clothing, often with straps or buttons, that people wear to play and work in."
    )],
    "mud": [(
        "What does mud do to clothes?",
        "Mud can stick to clothes and make them dirty, which is why people often try to avoid it on nice outfits."
    )],
    "wet": [(
        "Why do people keep clothes dry in the rain?",
        "Wet clothes can feel heavy and cold, so people use rain gear to stay dry."
    )],
    "paint": [(
        "Why is paint messy?",
        "Paint can drip and smear, so it often leaves bright stains on hands and clothes."
    )],
    "flour": [(
        "What happens when flour is tossed in the air?",
        "Flour can puff up into a white cloud and settle on everything nearby."
    )],
    "humor": [(
        "What is humor?",
        "Humor is when something makes people smile or laugh."
    )],
}

KNOWLEDGE_ORDER = ["dungaree", "mud", "wet", "paint", "flour", "humor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    return [
        f'Write a short fable for a child about "{f["prize"].label}" and a funny mistake.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but keeps the dungaree safe.",
        "Write a tiny moral tale with a joke, a warning, and a happier choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who wore the dungaree in the story?",
            answer=f"{hero.id} wore the dungaree, and {hero.pronoun('possessive')} {parent.type} watched carefully.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry when {hero.id} wanted to {act.verb}?",
            answer=f"{parent.id} worried because the dungaree could get {act.mess} if {hero.id} went ahead.",
        ),
        QAItem(
            question=f"What did the child think was funny about the moment?",
            answer=f"{hero.id} noticed {act.joke} and tried to keep the mood light, even before deciding what to do.",
        ),
    ]
    if f.get("resolved"):
        gear = _safe_fact(world, f, "gear")
        qa.append(QAItem(
            question=f"How did the parent help keep the dungaree clean?",
            answer=f"They offered {gear.label} first, so {hero.id} could still {act.verb} without ruining the dungaree.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with laughter, a safe choice, and the dungaree staying bright.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {world.facts["prize"].label, world.facts["activity"].keyword, world.facts["activity"].mess, "humor"}
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), gear(G), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for aid in p.affords:
            act = _safe_lookup(ACTIONS, aid)
            for pr_id, pr in PRIZES.items():
                if prize_at_risk(act, pr) and select_gear(act, pr):
                    combos.append((pid, aid, pr_id))
    return sorted(combos)


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
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
    ap = argparse.ArgumentParser(description="A tiny fable about a dungaree and a funny compromise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(ACTIONS, params.activity),
        _safe_lookup(PRIZES, params.prize),
        hero_name=params.name,
        hero_type=params.gender,
        parent_type=params.parent,
        hero_traits=[params.trait, "funny"],
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
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
    StoryParams(place="barn", activity="mud", prize="dungaree", name="Mina", gender="girl", parent="mother", trait="mischievous"),
    StoryParams(place="garden", activity="paint", prize="dungaree", name="Toby", gender="boy", parent="father", trait="bright-eyed"),
    StoryParams(place="kitchen", activity="flour", prize="dungaree", name="Lila", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
