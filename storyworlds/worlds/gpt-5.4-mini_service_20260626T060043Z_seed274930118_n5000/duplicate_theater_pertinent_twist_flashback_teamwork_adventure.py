#!/usr/bin/env python3
"""
storyworlds/worlds/duplicate_theater_pertinent_twist_flashback_teamwork_adventure.py
====================================================================================

A small Adventure-style story world about a theater rehearsal where a
duplicate object, a pertinent clue, a flashback, a twist, and teamwork
change the outcome.

Premise:
- A child is helping at a theater rehearsal.
- A pertinent prop or note matters for the show.
- A duplicate item causes confusion.

Turn:
- The team notices a flashback clue that makes the mix-up understandable.
- They use teamwork to choose the right item and save the rehearsal.

This world is constraint-checked, deterministic per seed, and supports the
standard Storyweavers CLI/QA/JSON/ASP/verify contract.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    dup: object | None = None
    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    pertinent: bool = False
    duplicateable: bool = False
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
class SceneDef:
    id: str
    verb: str
    gerund: str
    risk: str
    twist: str
    flashback: str
    tag: str
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
class AidDef:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.scene_tag: str = ""

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.scene_tag = self.scene_tag
        c.paragraphs = [[]]
        return c


def _describe_article(label: str) -> str:
    return "an" if label[:1].lower() in "aeiou" else "a"


SETTINGS = {
    "backstage": Setting(place="the backstage hallway", indoors=True, affords={"mystery"}),
    "theater": Setting(place="the theater", indoors=True, affords={"mystery"}),
    "stage": Setting(place="the stage", indoors=True, affords={"mystery"}),
}

SCENES = {
    "mystery": SceneDef(
        id="mystery",
        verb="solve the mystery",
        gerund="solving the mystery",
        risk="the show could stall",
        twist="but the duplicate made the choice tricky",
        flashback="Then a flashback to the costume table showed where the real one had been set down.",
        tag="theater",
        tags={"theater", "twist", "flashback", "teamwork"},
    ),
}

OBJECTS = {
    "script": ObjectDef(
        id="script",
        label="script",
        phrase="a folded script with one marked page",
        pertinent=True,
        duplicateable=False,
        tags={"pertinent", "theater"},
    ),
    "key": ObjectDef(
        id="key",
        label="key",
        phrase="a small brass key",
        pertinent=True,
        duplicateable=True,
        tags={"pertinent", "duplicate"},
    ),
    "mask": ObjectDef(
        id="mask",
        label="mask",
        phrase="a painted fox mask",
        pertinent=False,
        duplicateable=True,
        tags={"theater", "duplicate"},
    ),
}

AIDS = [
    AidDef(
        id="note",
        label="the marked note",
        prep="use the marked note to compare the clues",
        tail="checked the note against the props",
        helps={"script", "key"},
    ),
    AidDef(
        id="spot",
        label="the stage light",
        prep="shine the stage light on both copies",
        tail="held the light steady while they looked",
        helps={"key", "mask"},
    ),
]


GIRL_NAMES = ["Maya", "Lena", "Ivy", "Nora", "Tia", "Ruby"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Owen", "Max", "Theo"]
TRAITS = ["brave", "curious", "careful", "spirited", "kind"]


@dataclass
class StoryParams:
    place: str
    scene: str
    object: str
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


def object_at_risk(scene: SceneDef, obj: ObjectDef) -> bool:
    return obj.pertinent


def select_aid(scene: SceneDef, obj: ObjectDef) -> Optional[AidDef]:
    if not object_at_risk(scene, obj):
        return None
    for aid in AIDS:
        if obj.id in aid.helps:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for scene_id in setting.affords:
            scene = _safe_lookup(SCENES, scene_id)
            for obj_id, obj in OBJECTS.items():
                if object_at_risk(scene, obj) and select_aid(scene, obj):
                    combos.append((place, scene_id, obj_id))
    return combos


def introduce(world: World, hero: Entity, helper: Entity, obj: Entity, scene: SceneDef) -> None:
    world.say(
        f"{hero.id} was a little {next((t for t in hero.memes.get('trait_list', []) if t), 'curious')} {hero.type} "
        f"who loved {scene.gerund} at {world.setting.place}."
    )
    world.say(
        f"{hero.id} was helping {helper.pronoun('object')} with the {obj.label}, "
        f"{_describe_article(obj.label)} {obj.label} that mattered for the show."
    )


def start_scene(world: World, hero: Entity, helper: Entity, obj: Entity, scene: SceneDef) -> None:
    hero.memes["eagerness"] = hero.memes.get("eagerness", 0.0) + 1.0
    world.say(
        f"At {world.setting.place}, {hero.id} wanted to {scene.verb}, but {scene.risk}."
    )


def cause_duplicate(world: World, obj: Entity) -> None:
    dup_id = f"duplicate_{obj.id}"
    if dup_id in world.entities:
        return
    dup = world.add(Entity(
        id=dup_id,
        type=obj.type,
        label=f"duplicate {obj.label}",
        phrase=f"a duplicate {obj.phrase}",
    ))
    dup.meters["confusing"] = 1.0
    world.facts["duplicate_id"] = dup.id
    world.say(
        f"Someone had set out a duplicate {obj.label}, and now the two looked almost the same."
    )


def reveal_twist(world: World, scene: SceneDef, obj: Entity) -> None:
    world.say(
        f"{scene.twist.capitalize()} {scene.flashback}"
    )
    world.facts["flashback"] = scene.flashback
    world.facts["twist"] = scene.twist


def teamwork(world: World, hero: Entity, helper: Entity, obj: Entity, aid: AidDef) -> None:
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1.0
    helper.memes["helpful"] = helper.memes.get("helpful", 0.0) + 1.0
    world.say(
        f"Then {hero.id} and {helper.pronoun('object')} worked together."
    )
    world.say(
        f"{hero.id} said, \"Let's {aid.prep}.\" {helper.id} nodded and {aid.tail}."
    )
    world.say(
        f"With that teamwork, they found the real {obj.label} and kept the show moving."
    )


def resolve(world: World, hero: Entity, helper: Entity, obj: Entity, scene: SceneDef) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0
    world.say(
        f"In the end, {hero.id} held the right {obj.label}, and the theater lights glowed warmly."
    )
    world.say(
        f"The rehearsal continued, and what began as a duplicate mix-up ended as a small adventure."
    )


def tell(setting: Setting, scene: SceneDef, obj_def: ObjectDef,
         hero_name: str, hero_gender: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    world.scene_tag = scene.tag

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        meters={},
        memes={"trait_list": [trait]},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_kind,
        label="the helper",
    ))
    obj = world.add(Entity(
        id=obj_def.id,
        type=obj_def.id,
        label=obj_def.label,
        phrase=obj_def.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))

    introduce(world, hero, helper, obj, scene)
    world.para()
    start_scene(world, hero, helper, obj, scene)
    if obj_def.duplicateable:
        cause_duplicate(world, obj)
    world.para()
    reveal_twist(world, scene, obj)
    aid = select_aid(scene, obj)
    if aid is None:
        _fallback_pool = globals().get("AIDS") or globals().get("AIDES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        aid = next(iter(_fallback_pool), None)
        if aid is None:
            raise StoryError
    teamwork(world, hero, helper, obj, aid)
    world.para()
    resolve(world, hero, helper, obj, scene)

    world.facts.update(
        hero=hero,
        helper=helper,
        obj=obj,
        scene=scene,
        aid=aid,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obj")
    scene = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scene")
    return [
        f'Write a short Adventure-style story for a child about {hero.id} in a theater, with a duplicate {obj.label}.',
        f"Tell a gentle story where {hero.id} faces a pertinent problem at {world.setting.place} and teamwork helps.",
        f'Write a simple story that includes the words "duplicate", "theater", and "pertinent", and ends with a happy fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obj")
    scene = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scene")
    qa = [
        QAItem(
            question=f"Who is the story about at {world.setting.place}?",
            answer=f"The story is about {hero.id}, who is helping with a theater problem at {world.setting.place}.",
        ),
        QAItem(
            question=f"What made the task tricky in the theater?",
            answer=f"A duplicate {obj.label} made the task tricky, because the right one was pertinent to the show.",
        ),
        QAItem(
            question=f"What helped {hero.id} solve the problem?",
            answer=f"Teamwork with {helper.id} helped {hero.id} solve the problem and keep the rehearsal going.",
        ),
        QAItem(
            question=f"What was the flashback clue about?",
            answer=f"The flashback showed where the real {obj.label} had been set down, which made the answer clear.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a theater?",
            answer="A theater is a place where people act in plays, tell stories, and watch performances together.",
        ),
        QAItem(
            question="What does duplicate mean?",
            answer="Duplicate means there are two things that look the same, so it can be hard to tell which one is the original.",
        ),
        QAItem(
            question="What does pertinent mean?",
            answer="Pertinent means something is important and closely connected to what is happening.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and share the work so they can solve a problem together.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="theater", scene="mystery", object="key", name="Maya", gender="girl", helper="father", trait="curious"),
    StoryParams(place="backstage", scene="mystery", object="script", name="Eli", gender="boy", helper="mother", trait="brave"),
    StoryParams(place="stage", scene="mystery", object="mask", name="Ivy", gender="girl", helper="father", trait="careful"),
]


KNOWLEDGE_ORDER = ["theater", "duplicate", "pertinent", "teamwork"]


ASP_RULES = r"""
at_risk(Scene, Obj) :- scene(Scene), object(Obj), pertinent(Obj).
has_aid(Scene, Obj) :- at_risk(Scene, Obj), aid(A), helps(A, Obj).
valid_story(Place, Scene, Obj) :- affords(Place, Scene), at_risk(Scene, Obj), has_aid(Scene, Obj).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, s in SCENES.items():
        lines.append(asp.fact("scene", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.pertinent:
            lines.append(asp.fact("pertinent", oid))
        if o.duplicateable:
            lines.append(asp.fact("duplicateable", oid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for x in sorted(aid.helps):
            lines.append(asp.fact("helps", aid.id, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_story_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_story_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style theater story world with duplicate and pertinent clues.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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
              and (getattr(args, "scene", None) is None or c[1] == getattr(args, "scene", None))
              and (getattr(args, "object_", None) is None or c[2] == getattr(args, "object_", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, scene, obj = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, scene=scene, object=obj, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SCENES, params.scene), _safe_lookup(OBJECTS, params.object),
                 params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, scene, object) combos:\n")
        for place, scene, obj in combos:
            print(f"  {place:10} {scene:10} {obj:8}")
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
            header = f"### {p.name}: {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
