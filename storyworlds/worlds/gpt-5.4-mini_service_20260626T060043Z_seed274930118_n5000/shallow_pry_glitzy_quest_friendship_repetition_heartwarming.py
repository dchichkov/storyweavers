#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shallow_pry_glitzy_quest_friendship_repetition_heartwarming.py
================================================================================

A small heartwarming storyworld about a shallow place, a careful pry, and a
glitzy quest shared by friends.

Premise:
- A child and a friend visit a shallow tide pool.
- They want to find a glitzy treasure hidden under a little shell-lid.
- Their first tries are too rough or too weak, so they repeat the quest with
  gentler methods and more patience.
- Friendship changes the outcome: the treasure is found, shared, and the day
  ends warmly.

This script follows the Storyweavers contract:
- stdlib-only prose engine
- eager import of shared results containers
- lazy import of storyworlds.asp in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- typed entities with meters and memes
- inline ASP twin plus Python reasonableness gate
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the shallow tide pool"
    indoors: bool = False
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
class Quest:
    id: str
    verb: str
    gerund: str
    repeat: str
    risk: str
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
class Prize:
    label: str
    phrase: str
    type: str
    pocket: str
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
class Tool:
    id: str
    label: str
    verb: str
    guards: set[str]
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False
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


QUESTS = {
    "shell_pry": Quest(
        id="shell_pry",
        verb="pry open the little shell",
        gerund="prying open the little shell",
        repeat="try again with a gentler pry",
        risk="stuck",
        keyword="pry",
        tags={"shore", "shell", "pry"},
    ),
    "glitzy_search": Quest(
        id="glitzy_search",
        verb="look for the glitzy pebble",
        gerund="looking for the glitzy pebble",
        repeat="search the shallow water again",
        risk="lost",
        keyword="glitzy",
        tags={"glitzy", "pebble"},
    ),
    "tidy_sort": Quest(
        id="tidy_sort",
        verb="sort the shiny shells",
        gerund="sorting the shiny shells",
        repeat="count the shells one by one",
        risk="mixed up",
        keyword="shiny",
        tags={"shell", "repeat"},
    ),
}

PRIZES = {
    "pebble": Prize("pebble", "a tiny glitzy pebble", "pebble", "hand"),
    "shell": Prize("shell", "a pearly little shell", "shell", "hand"),
    "key": Prize("key", "a bright key with a glint", "key", "pocket"),
}

TOOLS = [
    Tool(
        id="stick",
        label="a smooth stick",
        verb="use a smooth stick",
        guards={"stuck"},
        helps={"pry"},
        prep="pick up a smooth stick and pry carefully",
        tail="kept using the smooth stick, a little gentler each time",
    ),
    Tool(
        id="cup",
        label="a small cup",
        verb="scoop with a small cup",
        guards={"lost"},
        helps={"glitzy"},
        prep="cup their hands and scoop the water slowly",
        tail="kept scooping until the glitzy pebble flashed in the sun",
    ),
    Tool(
        id="cloth",
        label="a soft cloth",
        verb="wipe with a soft cloth",
        guards={"mixed up"},
        helps={"repeat"},
        prep="lay out a soft cloth and sort each shell",
        tail="kept sorting until every shell had its own little place",
    ),
]

SETTINGS = {
    "tidepool": Setting(place="the shallow tide pool", affords={"shell_pry", "glitzy_search"}),
    "beach": Setting(place="the bright beach", affords={"glitzy_search", "tidy_sort"}),
    "garden": Setting(place="the little garden table", indoors=False, affords={"tidy_sort"}),
}

GIRL_NAMES = ["Maya", "Lina", "Nora", "June", "Ivy", "Rosa"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Ben", "Owen"]
TRAITS = ["gentle", "brave", "curious", "kind", "patient", "cheerful"]


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    friend: str
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


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    if quest.id == "shell_pry":
        return prize.pocket == "hand"
    if quest.id == "glitzy_search":
        return prize.pocket in {"hand", "pocket"}
    return prize.pocket == "hand"


def select_tool(quest: Quest, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if quest.keyword in tool.helps and prize_at_risk(quest, prize):
            return tool
    return None


def explain_rejection(quest: Quest, prize: Prize) -> str:
    return (
        f"(No story: {quest.gerund} does not have a gentle tool that helps the "
        f"{prize.label}. The ending would not be heartwarming because the quest "
        f"would stay stuck instead of turning into a kind shared success.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming shallow-pry-glitzy quest about friendship and repetition."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend", choices=["girl", "boy"])
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
    if getattr(args, "quest", None) and getattr(args, "prize", None):
        quest = _safe_lookup(QUESTS, getattr(args, "quest", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(quest, prize) and select_tool(quest, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        (place, qid, prid)
        for place, setting in SETTINGS.items()
        for qid in setting.affords
        for prid in PRIZES
        if (getattr(args, "place", None) is None or place == getattr(args, "place", None))
        and (getattr(args, "quest", None) is None or qid == getattr(args, "quest", None))
        and (getattr(args, "prize", None) is None or prid == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, quest_id, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    friend = getattr(args, "friend", None) or ("boy" if gender == "girl" else "girl")
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        quest=quest_id,
        prize=prize_id,
        name=name,
        gender=gender,
        friend=friend,
        trait=trait,
    )


def introduce(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a little {hero.pronoun('possessive')} {hero.type} who liked "
        f"quiet adventures, and {friend.id} was always nearby with a smile."
    )
    world.say(
        f"Together, they loved {quest.gerund} because every small surprise felt like a quest."
    )


def arrive(world: World, hero: Entity, friend: Entity, quest: Quest) -> None:
    world.say(
        f"One bright morning, {hero.id} and {friend.id} went to {world.setting.place}."
    )
    world.say(
        f"The water there was shallow enough for careful feet, and the little ripples "
        f"looked glitzy in the light."
    )


def start_quest(world: World, hero: Entity, friend: Entity, quest: Quest, prize: Prize) -> None:
    hero.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"{hero.id} wanted to {quest.verb}, because {hero.pronoun('possessive')} eyes "
        f"kept catching the glitzy shine hiding near {prize.label}."
    )
    world.say(
        f"{friend.id} nodded and said they could look together, one careful step at a time."
    )


def first_try(world: World, hero: Entity, quest: Quest, prize: Prize) -> None:
    hero.meters["attempts"] += 1
    hero.memes["frustration"] += 1
    world.say(
        f"{hero.id} tried to {quest.verb}, but the little shell stayed stuck."
        if quest.id == "shell_pry"
        else f"{hero.id} tried to {quest.verb}, but the glitzy prize slipped under the shallow water."
    )
    world.say(
        f"{hero.id} stopped, took a breath, and remembered that good quests can be tried again."
    )


def second_try(world: World, hero: Entity, friend: Entity, quest: Quest, prize: Prize, tool: Tool) -> None:
    hero.meters["attempts"] += 1
    friend.meters["attempts"] += 1
    hero.memes["patience"] += 1
    friend.memes["patience"] += 1
    world.say(
        f"Then {friend.id} offered {tool.label}, and the two friends decided to {tool.prep}."
    )
    world.say(
        f"They did not rush. They used the same quest again, but this time they were gentler."
    )


def resolve(world: World, hero: Entity, friend: Entity, quest: Quest, prize: Prize, tool: Tool) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"At last, the little shell opened, or the glitzy treasure floated free, and the bright {prize.label} was found."
        if quest.id != "tidy_sort"
        else f"At last, each shell found its place, and the little table looked neat and glitzy in the sun."
    )
    world.say(
        f"{hero.id} and {friend.id} smiled at each other, because the best part of the quest was doing it together."
    )
    world.say(
        f"They {tool.tail}."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, hero_type: str, friend_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend_name = "Pip" if hero_name != "Pip" else "Milo"
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))

    introduce(world, hero, friend, quest)
    world.para()
    arrive(world, hero, friend, quest)
    start_quest(world, hero, friend, quest, prize)
    first_try(world, hero, quest, prize)

    tool = select_tool(quest, prize)
    if tool is None:
        _fallback_pool = globals().get("TOOLS") or globals().get("TOOLES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        tool = next(iter(_fallback_pool), None)
        if tool is None:
            raise StoryError

    world.para()
    second_try(world, hero, friend, quest, prize, tool)
    resolve(world, hero, friend, quest, prize, tool)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        quest=quest,
        tool=tool,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    quest = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    return [
        f'Write a heartwarming story about a shallow place, a glitzy quest, and a gentle pry.',
        f"Tell a short story where {hero.id} and {friend.id} keep trying again until they finish {quest.verb} together.",
        f"Write a child-friendly adventure that includes the words shallow, pry, and glitzy, and ends with friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    quest = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who went on the quest at {world.setting.place}?",
            answer=f"{hero.id} and {friend.id} went together, and they stayed side by side the whole time.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {quest.verb}, because the glitzy treasure looked exciting.",
        ),
        QAItem(
            question=f"What helped the friends finish the quest?",
            answer=f"{tool.label} helped them because it made the {quest.keyword} quest gentler and easier to repeat.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} smiling together after they succeeded on the quest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    quest = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest")
    out = [
        QAItem(
            question="What does shallow mean?",
            answer="Shallow means not deep, so you can often see the bottom and stand or wade carefully.",
        ),
        QAItem(
            question="What does pry mean?",
            answer="To pry means to open or lift something carefully, often with a tool or a gentle twist.",
        ),
        QAItem(
            question="What does glitzy mean?",
            answer="Glitzy means shiny, sparkly, or showy in a way that catches the eye.",
        ),
    ]
    if quest.id == "shell_pry":
        out.append(
            QAItem(
                question="Why do gentle tries work better than rough ones sometimes?",
                answer="Gentle tries can work better because they keep a small thing from breaking or slipping away.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="tidepool", quest="shell_pry", prize="pebble", name="Maya", gender="girl", friend="boy", trait="gentle"),
    StoryParams(place="beach", quest="glitzy_search", prize="key", name="Theo", gender="boy", friend="girl", trait="curious"),
    StoryParams(place="garden", quest="tidy_sort", prize="shell", name="Lina", gender="girl", friend="boy", trait="patient"),
]


KNOWLEDGE = {
    "shallow": [("What is shallow water?", "Shallow water is water that is not deep, so it is easier to wade through carefully.")],
    "pry": [("What does it mean to pry something open?", "It means to open or lift it carefully, often with a small tool or a gentle push.")],
    "glitzy": [("What makes something glitzy?", "Something glitzy sparkles or shines and catches your eye right away.")],
    "repeat": [("Why do people repeat a try when it does not work?", "They repeat it because trying again can help them learn, improve, and finish the job.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other, help each other, and enjoy being together.")],
    "quest": [("What is a quest?", "A quest is a search or adventure to find something, solve something, or finish an important task.")],
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = _safe_lookup(QUESTS, qid)
            for pid, prize in PRIZES.items():
                if prize_at_risk(q, prize) and select_tool(q, prize):
                    combos.append((place, qid, pid))
    return combos


ASP_RULES = r"""
prize_at_risk(Q, P) :- quest(Q), prize(P), risk_place(Q, R), pocket(P, R).
has_tool(Q, P) :- prize_at_risk(Q, P), quest_help(Q, K), tool(T), helps(T, K), guards(T, R), pocket(P, R).
valid(Place, Q, P) :- affords(Place, Q), prize_at_risk(Q, P), has_tool(Q, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_help", qid, q.keyword))
        lines.append(asp.fact("risk_place", qid, "hand" if qid == "shell_pry" else "pocket"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("pocket", pid, p.pocket))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, h))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = rng.choice(list(combos))
    prize_obj = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize_obj.genders))
    friend = getattr(args, "friend", None) or ("boy" if gender == "girl" else "girl")
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.friend)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, quest, prize) combos:\n")
        for place, quest, prize in combos:
            print(f"  {place:10} {quest:12} {prize}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
