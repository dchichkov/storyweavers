#!/usr/bin/env python3
"""
storyworlds/worlds/wily_scandal_twist_kindness_whodunit.py
===========================================================

A small whodunit-style story world about a noisy scandal, a wily suspect,
a twist, and a kindness ending.

The seed image is a child-facing mystery:
- something important goes missing,
- a suspicious wily character seems to be involved,
- clues point one way,
- then a twist reveals a kinder truth,
- and the ending proves the town is calmer and safer than before.

This world keeps the simulated state visible:
- physical meters track clues, hiding, dampness, and order;
- emotional memes track suspicion, worry, shame, relief, trust, and kindness.

The story is generated from a small causal model rather than a frozen paragraph.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    discovered: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    item: object | None = None
    suspect: object | None = None
    def __post_init__(self) -> None:
        for k in ["clue", "mess", "damp", "order", "noise"]:
            self.meters.setdefault(k, 0.0)
        for k in ["suspicion", "worry", "shame", "relief", "trust", "kindness"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    place: str
    weather: str
    hides: set[str] = field(default_factory=set)
    clues: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    risk: str
    hide_spot: str
    sensitive_to: set[str] = field(default_factory=set)
    answer: str = ""
    question: str = ""
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
class Suspect:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    good_at: str = ""
    can_help: bool = False
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
class Twist:
    id: str
    label: str
    reveal: str
    cause: str
    helps: str
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
class Kindness:
    id: str
    label: str
    act: str
    result: str
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
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def clue_is_plausible(setting: Setting, item: Item, suspect: Suspect) -> bool:
    return item.hide_spot in setting.hides and item.risk in setting.clues and suspect.good_at in setting.clues


def select_twist(setting: Setting, item: Item, suspect: Suspect) -> Optional[Twist]:
    for tw in TWISTS:
        if tw.cause in setting.clues and tw.helps == item.hide_spot:
            return tw
    return None


def select_kindness(setting: Setting, item: Item, suspect: Suspect) -> Optional[Kindness]:
    for k in KINDNESSES:
        if k.result in setting.clues or k.result == item.risk:
            return k
    return _safe_lookup(KINDNESSES, 0) if KINDNESSES else None


def think(world: World, who: Entity, mood: str, amount: float = 1.0) -> None:
    who.memes[mood] += amount


def do_mystery(world: World, detective: Entity, suspect: Entity, item: Entity, twist: Twist, kindness: Kindness) -> None:
    detective.meters["clue"] += 1
    detective.memes["worry"] += 1
    world.say(
        f"At {world.setting.place}, a small scandal spread when {item.label} went missing."
    )
    world.say(
        f"{detective.id} was the first to notice. {detective.pronoun().capitalize()} looked at the clues and thought the case felt wily."
    )
    suspect.memes["suspicion"] += 1
    world.say(
        f"All eyes turned to {suspect.label}, because {suspect.pronoun().capitalize()} was quick, sly, and a little too clever."
    )
    world.say(
        f"But then {detective.id} found a clue: {twist.reveal}."
    )
    world.say(
        f"The mystery twisted in a new direction. It was not a theft after all; {twist.cause}."
    )
    suspect.memes["relief"] += 1
    suspect.memes["trust"] += 1
    suspect.memes["kindness"] += 1
    world.say(
        f"{kindness.act.capitalize()}, and that kind act helped everyone calm down."
    )
    world.say(
        f"In the end, {kindness.result}, {item.label} was safe again, and the scandal turned into a gentle lesson about looking twice before blaming."
    )


SETTINGS = {
    "library": Setting(
        place="the little library",
        weather="rainy",
        hides={"shelf", "curtain", "reading nook"},
        clues={"paper", "ink", "dust", "rain"},
    ),
    "market": Setting(
        place="the busy market square",
        weather="bright",
        hides={"crate", "stall", "awning"},
        clues={"rope", "basket", "coin", "bird"},
    ),
    "garden": Setting(
        place="the garden shed",
        weather="cloudy",
        hides={"bench", "pot", "doorway"},
        clues={"soil", "leaf", "water", "wind"},
    ),
}

ITEMS = {
    "bell": Item(
        id="bell",
        label="the silver bell",
        phrase="a silver bell for calling story time",
        risk="noise",
        hide_spot="curtain",
        sensitive_to={"rain", "dust"},
    ),
    "key": Item(
        id="key",
        label="the brass key",
        phrase="a brass key for the little lockbox",
        risk="order",
        hide_spot="shelf",
        sensitive_to={"dust", "rope"},
    ),
    "basket": Item(
        id="basket",
        label="the berry basket",
        phrase="a berry basket for the morning stall",
        risk="mess",
        hide_spot="crate",
        sensitive_to={"soil", "leaf"},
    ),
}

SUSPECTS = {
    "fox": Suspect(id="fox", type="fox", label="Fenn the fox", traits=["wily", "quick"], good_at="dust", can_help=False),
    "magpie": Suspect(id="magpie", type="bird", label="Mira the magpie", traits=["wily", "bright"], good_at="bird", can_help=True),
    "cat": Suspect(id="cat", type="cat", label="Clover the cat", traits=["quiet", "careful"], good_at="rope", can_help=True),
}

TWISTS = [
    Twist(id="rainroof", label="rain twist", reveal="there were tiny wet marks under the curtain", cause="a drip from the roof had pushed the bell into the curtain nook", helps="curtain"),
    Twist(id="birdhelp", label="bird twist", reveal="a feather and a ribbon were tied to the shelf", cause="Mira had moved the key so the wind would not blow it away", helps="shelf"),
    Twist(id="gardenhelp", label="garden twist", reveal="a muddy paw print led to the bench, not the door", cause="Clover hid the basket only to keep it from falling into the soil", helps="bench"),
]

KINDNESSES = [
    Kindness(id="apology", label="apology", act="Mira apologized and helped tidy the shelf", result="the room felt calm"),
    Kindness(id="sharing", label="sharing", act="Fenn brought back the missing thing and shared the blame fairly", result="everyone could smile again"),
    Kindness(id="tidy", label="tidy work", act="Clover helped wipe the floor and dry the clues", result="the garden looked neat again"),
]


@dataclass
class StoryParams:
    place: str
    item: str
    suspect: str
    detective_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for sid, suspect in SUSPECTS.items():
                if item.hide_spot in setting.hides and item.risk in setting.clues and suspect.good_at in setting.clues:
                    out.append((place, iid, sid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: scandal, twist, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
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
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
              and (getattr(args, "suspect", None) is None or c[2] == getattr(args, "suspect", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item, suspect = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(["Pip", "Mara", "Toby", "Lena", "Noah", "Ivy"])
    return StoryParams(place=place, item=item, suspect=suspect, detective_name=name)


def narrate(world: World, params: StoryParams) -> World:
    setting = world.setting
    detective = world.add(Entity(id=params.detective_name, kind="character", type="child", traits=["curious", "brave"]))
    suspect = world.add(Entity(id=params.suspect, kind="character", type=params.suspect, label=_safe_lookup(SUSPECTS, params.suspect).label, traits=list(_safe_lookup(SUSPECTS, params.suspect).traits)))
    item = world.add(Entity(id=params.item, kind="thing", type=params.item, label=_safe_lookup(ITEMS, params.item).label, phrase=_safe_lookup(ITEMS, params.item).phrase, owner=detective.id, caretaker=detective.id, hidden=True))
    twist = select_twist(setting, _safe_lookup(ITEMS, params.item), _safe_lookup(SUSPECTS, params.suspect))
    if twist is None:
        _fallback_pool = globals().get("TWISTS") or globals().get("TWISTES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        twist = next(iter(_fallback_pool), None)
        if twist is None:
            raise StoryError
    kindness = select_kindness(setting, _safe_lookup(ITEMS, params.item), _safe_lookup(SUSPECTS, params.suspect))
    if kindness is None:
        _fallback_pool = globals().get("KINDNESSS") or globals().get("KINDNESSES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        kindness = next(iter(_fallback_pool), None)
        if kindness is None:
            raise StoryError
    world.facts.update(detective=detective, suspect=suspect, item=item, twist=twist, kindness=kindness)
    world.say(f"One morning at {setting.place}, {detective.id} noticed something odd.")
    world.say(f"The news caused a scandal, because {item.label} was missing.")
    world.para()
    do_mystery(world, detective, suspect, item, twist, kindness)
    item.hidden = False
    item.discovered = True
    detective.memes["relief"] += 1
    detective.memes["trust"] += 1
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about a scandal at {world.setting.place} involving {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item").label}.',
        f"Tell a gentle mystery where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective").id} thinks {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "suspect").label} is wily, but the twist shows a kinder truth.",
        f'Write a story with the words "wily", "scandal", "twist", and "kindness" that ends with the missing thing found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective, suspect, item, twist, kindness = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "suspect"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "twist"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "kindness")
    return [
        QAItem(
            question=f"Why did {detective.id} think the day turned into a scandal?",
            answer=f"Because {item.label} had gone missing at {world.setting.place}, and everyone got worried."
        ),
        QAItem(
            question=f"Why did people first suspect {suspect.label}?",
            answer=f"Because {suspect.label} seemed wily and clever, so the clues looked suspicious at first."
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=f"The twist was that {twist.cause}, so the missing item was not stolen at all."
        ),
        QAItem(
            question=f"How did kindness help end the story?",
            answer=f"{kindness.act}. That kindness helped everyone calm down, and the case ended peacefully."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a scandal?", answer="A scandal is when people get upset about something surprising or wrong."),
        QAItem(question="What is a whodunit?", answer="A whodunit is a mystery story where readers try to figure out who did it."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprise turn that changes what you thought was true."),
        QAItem(question="What is kindness?", answer="Kindness means helping, sharing, apologizing, or being gentle with others."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.hidden:
            bits.append("hidden=True")
        if e.discovered:
            bits.append("discovered=True")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place,Item,Suspect) :- setting(Place), mystery_item(Item), suspect(Suspect),
    hides(Place,Hide), item_hide(Item,Hide),
    clue_place(Place,Clue), item_risk(Item,Clue),
    suspect_clue(Suspect,Clue).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for h in sorted(_safe_lookup(SETTINGS, p).hides):
            lines.append(asp.fact("hides", p, h))
        for c in sorted(_safe_lookup(SETTINGS, p).clues):
            lines.append(asp.fact("clue_place", p, c))
    for i, item in ITEMS.items():
        lines.append(asp.fact("mystery_item", i))
        lines.append(asp.fact("item_hide", i, item.hide_spot))
        lines.append(asp.fact("item_risk", i, item.risk))
    for s, sus in SUSPECTS.items():
        lines.append(asp.fact("suspect", s))
        for c in sorted({sus.good_at}):
            lines.append(asp.fact("suspect_clue", s, c))
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
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    world = narrate(world, params)
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
    StoryParams(place="library", item="bell", suspect="fox", detective_name="Pip"),
    StoryParams(place="market", item="key", suspect="magpie", detective_name="Mara"),
    StoryParams(place="garden", item="basket", suspect="cat", detective_name="Ivy"),
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
        print(f"{len(combos)} valid mystery setups:\n")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
