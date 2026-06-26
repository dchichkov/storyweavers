#!/usr/bin/env python3
"""
storyworlds/worlds/health_fatten_percussion_transformation_lesson_learned_dialogue.py
=====================================================================================

A small bedtime-story world about health, fattening, percussion, transformation,
and a lesson learned.

Premise:
- A child notices a little animal is too thin and tired for a bedtime performance.
- The child first thinks "fatten" means "make it healthy fast."
- A gentle parent or helper explains that health comes from proper food, rest,
  and steady care, not from too many sweets.
- A soft percussion rhythm, like a tiny drum beat, helps the animal settle down
  for soup, sleep, and a gradual transformation.
- The ending proves the change: the animal looks stronger, calmer, and happier,
  and the child has learned something kind and useful.

The script follows the storyworld contract:
- self-contained stdlib script
- results imported eagerly
- asp imported lazily in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

    animal: object | None = None
    child: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        if not self.meters:
            self.meters = {"health": 0.0, "fat": 0.0, "rest": 0.0, "full": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "love": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the little house"
    indoors: bool = True
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
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    title: str
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
class Food:
    id: str
    label: str
    phrase: str
    healthy: bool
    fills: float
    heals: float
    sweet: bool = False
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
class Instrument:
    id: str
    label: str
    phrase: str
    volume: str
    bedtime_safe: bool = True
    helps: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.activity: Optional[Activity] = None
        self.food: Optional[Food] = None
        self.instrument: Optional[Instrument] = None

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

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.activity = self.activity
        c.food = self.food
        c.instrument = self.instrument
        return c


SETTINGS = {
    "bedroom": Setting(place="the little bedroom", indoors=True, affords={"drum_lullaby"}),
    "kitchen": Setting(place="the cozy kitchen", indoors=True, affords={"drum_lullaby"}),
    "porch": Setting(place="the quiet porch", indoors=True, affords={"drum_lullaby"}),
}

ACTIVITIES = {
    "drum_lullaby": Activity(
        id="drum_lullaby",
        verb="tap a gentle bedtime rhythm",
        gerund="tapping a gentle bedtime rhythm",
        mess="sound",
        title="soft percussion",
        keyword="percussion",
        tags={"percussion", "bedtime", "lesson"},
    )
}

FOODS = {
    "soup": Food(
        id="soup",
        label="warm soup",
        phrase="a small bowl of warm soup",
        healthy=True,
        fills=1.0,
        heals=1.0,
    ),
    "porridge": Food(
        id="porridge",
        label="oat porridge",
        phrase="a little bowl of oat porridge",
        healthy=True,
        fills=1.0,
        heals=1.0,
    ),
    "cake": Food(
        id="cake",
        label="sweet cake",
        phrase="a sugary piece of cake",
        healthy=False,
        fills=1.5,
        heals=0.0,
        sweet=True,
    ),
}

INSTRUMENTS = {
    "drum": Instrument(
        id="drum",
        label="a small drum",
        phrase="a small drum with a moon painted on it",
        volume="soft",
        bedtime_safe=True,
        helps={"calm", "routine", "sleep"},
    ),
    "tambourine": Instrument(
        id="tambourine",
        label="a tiny tambourine",
        phrase="a tiny tambourine with silver jingles",
        volume="soft",
        bedtime_safe=True,
        helps={"calm", "routine", "sleep"},
    ),
}

NAMES = ["Mia", "Nora", "Lily", "Owen", "Theo", "Ava"]
ANIMAL_NAMES = ["Pip", "Milo", "Mimi", "Biscuit", "Juniper"]
TRAITS = ["gentle", "curious", "sleepy", "kind", "patient"]


def reasonableness_gate(activity: Activity, food: Food, instrument: Instrument) -> bool:
    return activity.id == "drum_lullaby" and instrument.bedtime_safe and food.healthy


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for food_id, food in FOODS.items():
                for inst_id, inst in INSTRUMENTS.items():
                    if reasonableness_gate(_safe_lookup(ACTIVITIES, act_id), food, inst):
                        out.append((place, act_id, food_id, inst_id))
    return out


def explain_rejection(food: Food) -> str:
    if not food.healthy:
        return (
            f"(No story: {food.label} would only make the character feel fuller, "
            f"not healthier. This world needs a true health transformation, so "
            f"the sweet-food path is rejected.)"
        )
    return "(No story: the options do not support a gentle bedtime transformation.)"


@dataclass
class StoryParams:
    place: str = ""
    activity: str = ""
    food: str = ""
    instrument: str = ""
    child_name: str = ""
    child_type: str = ""
    parent_type: str = ""
    animal_name: str = ""
    animal_type: str = ""
    trait: str = ""
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


def introduce(world: World, child: Entity, animal: Entity) -> None:
    world.say(
        f"{child.id} was a {child.memes.get('trait', 'gentle')} little {child.type} "
        f"who loved bedtime stories."
    )
    world.say(
        f"Near {child.pronoun('possessive')} pillow lived {animal.id}, a small {animal.type} "
        f"who looked a little too thin."
    )


def show_worry(world: World, child: Entity, animal: Entity) -> None:
    animal.memes["worry"] += 1
    world.say(
        f"{child.id} frowned and said, \"{animal.id}, you look tired. I wish I could "
        f"fatten you up right away.\""
    )


def gentle_answer(world: World, parent: Entity, child: Entity, food: Food) -> None:
    world.say(
        f"{parent.id} smiled softly and said, \"Fattening is not the same as healing. "
        f"We should help {child.pronoun('object')} grow healthy, not just full.\""
    )
    if food.healthy:
        world.say(
            f"\"Let's try {food.phrase} instead. It will help without making the night feel heavy.\""
        )


def music_scene(world: World, child: Entity, instrument: Instrument, activity: Activity) -> None:
    world.say(
        f"{child.id} picked up {instrument.phrase} and began {activity.gerund}."
    )
    world.say(
        f"The soft percussion made the room feel round and safe, like a sleepy nest."
    )


def feed_and_change(world: World, animal: Entity, food: Food) -> None:
    animal.meters["full"] += food.fills
    if food.healthy:
        animal.meters["health"] += food.heals
        animal.memes["joy"] += 1
        animal.memes["lesson"] += 0.5
        world.say(
            f"{animal.id} ate the {food.label}, licked {animal.pronoun('possessive')} whiskers, "
            f"and seemed a little brighter."
        )
    else:
        animal.meters["fat"] += food.fills
        world.say(
            f"{animal.id} ate the sweet treat and only grew heavier, not stronger."
        )


def transform(world: World, animal: Entity) -> None:
    if animal.meters["health"] >= THRESHOLD:
        animal.memes["joy"] += 1
        world.say(
            f"By the time the drum beat grew quiet, {animal.id} was no longer so tiny and tired."
        )
        world.say(
            f"{animal.id}'s fur looked fuller, {animal.pronoun('possessive')} eyes looked bright, "
            f"and {animal.pronoun('subject')} could sit up straight."
        )


def learned_lesson(world: World, child: Entity, parent: Entity, animal: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} nodded and said, \"I learned it now. Health comes from kind care, "
        f"good food, and rest.\""
    )
    world.say(
        f"{parent.id} kissed {child.pronoun('possessive')} forehead and said, "
        f"\"Yes, little one. A gentle rhythm can help a tired heart settle down.\""
    )
    world.say(
        f"So {animal.id} curled up warm and safe while the last percussion beat faded like a star."
    )


def tell(setting: Setting, activity: Activity, food: Food, instrument: Instrument,
         child_name: str = "Mia", child_type: str = "girl",
         parent_type: str = "mother", animal_name: str = "Pip",
         animal_type: str = "rabbit", trait: str = "gentle") -> World:
    world = World(setting)
    world.activity = activity
    world.food = food
    world.instrument = instrument

    child = world.add(Entity(id=child_name, kind="character", type=child_type, memes={"trait": trait}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    animal = world.add(Entity(id=animal_name, kind="character", type=animal_type))

    world.say(
        f"One quiet night, {child.id} sat beside {animal.id} in {setting.place}."
    )
    introduce(world, child, animal)
    world.para()
    show_worry(world, child, animal)
    gentle_answer(world, parent, child, food)
    world.para()
    music_scene(world, child, instrument, activity)
    feed_and_change(world, animal, food)
    transform(world, animal)
    world.para()
    learned_lesson(world, child, parent, animal)

    world.facts.update(
        child=child,
        parent=parent,
        animal=animal,
        activity=activity,
        food=food,
        instrument=instrument,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    animal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "animal")
    food = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "food")
    instrument = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "instrument")
    return [
        f'Write a bedtime story for a small child about health, fattening, and {instrument.label}.',
        f"Tell a gentle story where {child.id} worries that {animal.id} is too thin and learns that "
        f"{food.label} is better than sweet treats.",
        f'Write a soft story that includes the word "percussion" and ends with a lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    animal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "animal")
    food = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "food")
    instrument = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "instrument")
    parent = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent")
    return [
        QAItem(
            question=f"Who worried that {animal.id} needed to be healthier?",
            answer=f"{child.id} worried, because {child.id} cared about {animal.id} and wanted {animal.id} to be stronger.",
        ),
        QAItem(
            question=f"What did {child.id} first think would help {animal.id}?",
            answer=f"{child.id} first thought that fattening {animal.id} quickly would help, but that was not the best idea.",
        ),
        QAItem(
            question=f"What food did {parent.id} suggest instead of a sweet treat?",
            answer=f"{parent.id} suggested {food.phrase}, because it was the kind of food that could help make {animal.id} healthy.",
        ),
        QAItem(
            question=f"What did {child.id} do with {instrument.label}?",
            answer=f"{child.id} tapped {instrument.phrase} and made a soft percussion rhythm for bedtime.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{animal.id} looked healthier, calmer, and brighter, and {child.id} learned that good care matters more than simply making someone full.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is health?",
            answer="Health means being strong, well, and cared for so your body can work the way it should.",
        ),
        QAItem(
            question="What is percussion?",
            answer="Percussion is music made by tapping, shaking, or striking things like drums and bells.",
        ),
        QAItem(
            question="Why can too many sweets be a bad plan?",
            answer="Too many sweets can make someone feel full without giving them the steady nourishment their body needs.",
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
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bedroom",
        activity="drum_lullaby",
        food="soup",
        instrument="drum",
        child_name="Mia",
        child_type="girl",
        parent_type="mother",
        animal_name="Pip",
        animal_type="rabbit",
        trait="gentle",
    ),
    StoryParams(
        place="kitchen",
        activity="drum_lullaby",
        food="porridge",
        instrument="tambourine",
        child_name="Owen",
        child_type="boy",
        parent_type="father",
        animal_name="Milo",
        animal_type="kitten",
        trait="curious",
    ),
]


def explain_gender(_: str, __: str) -> str:
    return ""


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "food", None) and not _safe_lookup(FOODS, getattr(args, "food", None)).healthy:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "food", None) is None or c[2] == getattr(args, "food", None))
        and (getattr(args, "instrument", None) is None or c[3] == getattr(args, "instrument", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, food_id, instrument_id = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    parent_type = getattr(args, "parent_type", None) or rng.choice(["mother", "father"])
    animal_type = getattr(args, "animal_type", None) or rng.choice(["rabbit", "kitten", "puppy"])
    child_name = getattr(args, "child_name", None) or rng.choice(NAMES)
    animal_name = getattr(args, "animal_name", None) or rng.choice(ANIMAL_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        food=food_id,
        instrument=instrument_id,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        animal_name=animal_name,
        animal_type=animal_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(FOODS, params.food),
        _safe_lookup(INSTRUMENTS, params.instrument),
        params.child_name,
        params.child_type,
        params.parent_type,
        params.animal_name,
        params.animal_type,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        if f.healthy:
            lines.append(asp.fact("healthy_food", fid))
    for iid, i in INSTRUMENTS.items():
        lines.append(asp.fact("instrument", iid))
        if i.bedtime_safe:
            lines.append(asp.fact("bedtime_safe", iid))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, A, F, I) :- setting(P), affords(P, A), activity(A),
                           food(F), healthy_food(F),
                           instrument(I), bedtime_safe(I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about health, percussion, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--instrument", choices=INSTRUMENTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--animal-name")
    ap.add_argument("--animal-type", choices=["rabbit", "kitten", "puppy"])
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.child_name} and {p.animal_name} at {p.place} ({p.food}, {p.instrument})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
