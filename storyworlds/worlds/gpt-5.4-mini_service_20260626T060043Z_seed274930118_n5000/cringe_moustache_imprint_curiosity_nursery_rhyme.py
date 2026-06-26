#!/usr/bin/env python3
"""
storyworlds/worlds/cringe_moustache_imprint_curiosity_nursery_rhyme.py
======================================================================

A tiny nursery-rhyme storyworld about curiosity, a fake moustache, and a
cringe-worthy imprint left behind.

Premise:
- A curious little child finds a disguise kit with a curly moustache.
- The child wants to try the moustache because it looks funny and grand.
- The moustache leaves an imprint on a clean prop, which feels cringe at first.
- A gentle helper turns the mishap into play by making a proper costume print.

The story is modeled with physical meters and emotional memes, and the prose is
driven by the simulated state rather than a frozen template.
"""

from __future__ import annotations

import argparse
import copy
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
    mounted_on: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    costume: object | None = None
    helper: object | None = None
    prop: object | None = None
    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))
        if not self.meters:
            self.meters = {"clean": 0.0, "imprinted": 0.0, "cringe": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "curiosity": 0.0, "embarrassment": 0.0, "love": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mom"}
        male = {"boy", "father", "man", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
class Room:
    name: str
    place: str
    rhyme_vibe: str = "nursery"
    has_mirror: bool = True
    has_table: bool = True
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
class Prop:
    id: str
    label: str
    phrase: str
    kind: str
    cleanable: bool = True
    imprint_kind: str = "moustache"
    children_use: bool = True
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
class Costume:
    id: str
    label: str
    phrase: str
    kind: str
    leaves_imprint: bool = True
    brave: bool = False
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
class StoryParams:
    room: str = ""
    prop: str = ""
    costume: str = ""
    name: str = ""
    gender: str = ""
    helper: str = ""
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


ROOMS = {
    "nursery": Room(name="nursery", place="the nursery", rhyme_vibe="nursery", has_mirror=True, has_table=True),
    "playroom": Room(name="playroom", place="the playroom", rhyme_vibe="nursery", has_mirror=True, has_table=True),
    "parlor": Room(name="parlor", place="the little parlor", rhyme_vibe="nursery", has_mirror=False, has_table=True),
}

PROPS = {
    "paper_star": Prop(
        id="paper_star",
        label="paper star",
        phrase="a bright paper star",
        kind="paper star",
        imprint_kind="moustache",
    ),
    "tea_cup": Prop(
        id="tea_cup",
        label="teacup",
        phrase="a tiny teacup",
        kind="teacup",
        imprint_kind="moustache",
    ),
    "mirror_card": Prop(
        id="mirror_card",
        label="mirror card",
        phrase="a shiny mirror card",
        kind="card",
        imprint_kind="moustache",
    ),
}

COSTUMES = {
    "moustache": Costume(
        id="moustache",
        label="curly moustache",
        phrase="a curly black moustache",
        kind="moustache",
        leaves_imprint=True,
        brave=False,
    ),
    "paint_moustache": Costume(
        id="paint_moustache",
        label="painted moustache",
        phrase="a painted moustache",
        kind="paint",
        leaves_imprint=True,
        brave=True,
    ),
    "cloth_moustache": Costume(
        id="cloth_moustache",
        label="cloth moustache",
        phrase="a soft cloth moustache",
        kind="cloth",
        leaves_imprint=False,
        brave=True,
    ),
}

NAMES = ["Mia", "Nora", "Lily", "Theo", "Finn", "Ava", "Milo", "Rose"]
GENDERS = ["girl", "boy"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["curious", "cheerful", "tiny", "bouncy", "gentle"]


class World:
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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
        clone = World(self.room)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _emotional_gate(value: float) -> bool:
    return value >= THRESHOLD


def _touch_imprint(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    costume = world.get("costume")
    prop = world.get("prop")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    if costume.worn_by != child.id:
        return out
    if prop.meters["imprinted"] >= THRESHOLD:
        return out
    sig = "touch_imprint"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    prop.meters["imprinted"] += 1.0
    costume.meters["imprinted"] += 1.0
    child.memes["embarrassment"] += 1.0
    child.memes["cringe"] += 1.0
    out.append("A little moustache imprint showed up at once.")
    return out


def _mirror_cringe(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    prop = world.get("prop")
    if child.memes["cringe"] < THRESHOLD:
        return out
    sig = "mirror_cringe"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if world.room.has_mirror:
        out.append("In the mirror, the sight felt cringe, like a funny face that would not stay still.")
    else:
        out.append("The sight felt cringe, as if the room itself were holding in a giggle.")
    return out


def _helper_fix(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    prop = world.get("prop")
    costume = world.get("costume")
    if prop.meters["imprinted"] < THRESHOLD:
        return out
    if child.memes["embarrassment"] < THRESHOLD:
        return out
    sig = "helper_fix"
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["joy"] += 1.0
    child.memes["cringe"] = 0.0
    child.memes["embarrassment"] = 0.0
    prop.meters["clean"] += 1.0
    out.append(
        f"{helper.type.capitalize()} smiled and showed how to turn the moustache imprint into a neat costume mark."
    )
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_touch_imprint, _mirror_cringe, _helper_fix):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a little {next((t for t in child.memes if False), '')}".strip()
    )


def setting_open(world: World, child: Entity, helper: Entity) -> None:
    world.say(f"Once in {world.room.place}, {child.id} and {helper.pronoun('possessive')} {helper.type} were near a little table.")
    if world.room.has_mirror:
        world.say("A shiny mirror stood nearby like a quiet moon.")


def child_loves_curiosity(world: World, child: Entity, costume: Entity) -> None:
    child.memes["curiosity"] += 1.0
    world.say(
        f"{child.id} had a great Curiosity for funny things, and {child.pronoun('subject')} loved the curly moustache in the dress-up box."
    )
    world.say(
        f"It looked grand and silly all at once, as if a tiny king had winked from the cloth."
    )


def helper_warns(world: World, helper: Entity, child: Entity, costume: Entity, prop: Entity) -> None:
    world.say(
        f"{helper.pronoun('subject').capitalize()} said, \"That moustache may make an imprint on your shiny {prop.label}, dear one.\""
    )


def child_tries_it(world: World, child: Entity, costume: Entity) -> None:
    child.memes["joy"] += 1.0
    costume.worn_by = child.id
    world.say(f"{child.id} put on the moustache anyway and tried to look very grand.")
    propagate(world, narrate=True)


def helper_turns_it(world: World, helper: Entity, child: Entity, prop: Entity, costume: Entity) -> None:
    if prop.meters["imprinted"] < THRESHOLD:
        return
    world.say(
        f"{helper.pronoun('subject').capitalize()} brushed the prop clean, then brought out a soft cloth moustache so the game could still go on."
    )
    costume.worn_by = None
    world.say(
        f"{child.id} laughed, because the new moustache was gentler and left no bad imprint at all."
    )


def resolve_story(world: World, child: Entity, helper: Entity, prop: Entity, costume: Entity) -> None:
    if prop.meters["imprinted"] >= THRESHOLD:
        helper_turns_it(world, helper, child, prop, costume)
    world.say(
        f"In the end, {child.id} wore the kinder moustache, and the little prop stayed neat and bright."
    )


def tell(room: Room, prop_cfg: Prop, costume_cfg: Costume, hero_name: str, hero_gender: str, helper_kind: str, trait: str) -> World:
    world = World(room)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=hero_gender,
        label=hero_name,
        meters={"clean": 1.0, "imprinted": 0.0, "cringe": 0.0},
        memes={"joy": 0.0, "curiosity": 0.0, "embarrassment": 0.0, "love": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_kind,
        label=helper_kind,
        meters={"clean": 1.0, "imprinted": 0.0, "cringe": 0.0},
        memes={"joy": 0.0, "curiosity": 0.0, "embarrassment": 0.0, "love": 0.0},
    ))
    prop = world.add(Entity(
        id="prop",
        kind="thing",
        type=prop_cfg.kind,
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
        meters={"clean": 1.0, "imprinted": 0.0, "cringe": 0.0},
    ))
    costume = world.add(Entity(
        id="costume",
        kind="thing",
        type=costume_cfg.kind,
        label=costume_cfg.label,
        phrase=costume_cfg.phrase,
        meters={"clean": 1.0, "imprinted": 0.0, "cringe": 0.0},
    ))
    child.memes["curiosity"] += 1.0
    world.facts.update(child=child, helper=helper, prop=prop, costume=costume, trait=trait)

    world.say(
        f"{hero_name} was a little {trait} {hero_gender} who loved a nursery game with dress-up and rhyme."
    )
    world.say(
        f"One day, {hero_name} found {costume.phrase} and peeped at {prop.phrase} on the table."
    )
    setting_open(world, child, helper)
    child_loves_curiosity(world, child, costume)
    helper_warns(world, helper, child, costume, prop)

    world.para()
    child_tries_it(world, child, costume)

    world.para()
    resolve_story(world, child, helper, prop, costume)

    world.facts["resolved"] = True
    return world


def prize_at_risk(costume: Costume, prop: Prop) -> bool:
    return costume.leaves_imprint and prop.cleanable and prop.imprint_kind == costume.kind or costume.leaves_imprint and prop.cleanable


def select_fix(costume: Costume, prop: Prop) -> bool:
    return costume.leaves_imprint and prop.cleanable


@dataclass
class StoryParamsRegistry:
    pass
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_name, room in ROOMS.items():
        for prop_name in PROPS:
            for costume_name in COSTUMES:
                if prize_at_risk(_safe_lookup(COSTUMES, costume_name), _safe_lookup(PROPS, prop_name)) and select_fix(_safe_lookup(COSTUMES, costume_name), _safe_lookup(PROPS, prop_name)):
                    combos.append((room_name, prop_name, costume_name))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prop")
    costume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "costume")
    return [
        f'Write a short nursery-rhyme-style story about Curiosity, a moustache, and an imprint.',
        f"Tell a gentle story where {child.label} tries {costume.phrase} near {prop.phrase} and a helper makes the mishap feel okay.",
        f'Write a rhyme-like story that includes the words "cringe", "moustache", and "imprint".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prop")
    costume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "costume")
    return [
        QAItem(
            question=f"What did {child.label} find in the dress-up box?",
            answer=f"{child.label} found {costume.phrase}, and that made the curious child want to try it on right away.",
        ),
        QAItem(
            question=f"Why did the little scene feel cringe at first?",
            answer=f"It felt cringe because the moustache left an imprint on {prop.phrase}, and the child felt embarrassed for a moment.",
        ),
        QAItem(
            question=f"Who helped turn the mistake into play?",
            answer=f"{helper.type.capitalize()} helped by cleaning the prop and offering a gentler moustache so the game could continue happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a moustache?",
            answer="A moustache is hair that grows above a person's upper lip, and sometimes children use a fake one for dress-up play.",
        ),
        QAItem(
            question="What does imprint mean?",
            answer="An imprint is a mark that one thing leaves on another thing, like a stamp or a pressed shape.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to look, ask, and learn about something new.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
risky(C,P) :- costume(C), prop(P).
fixable(C,P) :- risky(C,P).
valid(R,P,C) :- room(R), prop(P), costume(C), risky(C,P), fixable(C,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for r in ROOMS:
        lines.append(asp.fact("room", r))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    for c in COSTUMES:
        lines.append(asp.fact("costume", c))
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
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery rhyme storyworld about curiosity, a moustache, and an imprint.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "room", None):
        combos = [c for c in combos if c[0] == getattr(args, "room", None)]
    if getattr(args, "prop", None):
        combos = [c for c in combos if c[1] == getattr(args, "prop", None)]
    if getattr(args, "costume", None):
        combos = [c for c in combos if c[2] == getattr(args, "costume", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    room, prop, costume = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(room=room, prop=prop, costume=costume, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(ROOMS, params.room), _safe_lookup(PROPS, params.prop), _safe_lookup(COSTUMES, params.costume), params.name, params.gender, params.helper, params.trait)
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
    StoryParams(room="nursery", prop="paper_star", costume="moustache", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(room="playroom", prop="mirror_card", costume="paint_moustache", name="Theo", gender="boy", helper="father", trait="bouncy"),
    StoryParams(room="parlor", prop="tea_cup", costume="cloth_moustache", name="Rose", gender="girl", helper="grandmother", trait="gentle"),
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
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
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
            header = f"### {p.name}: {p.costume} in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
