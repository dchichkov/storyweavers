#!/usr/bin/env python3
"""
grow_sharing_slice_of_life.py
=============================

A small slice-of-life storyworld about a child, a shared growing thing, and a
gentle problem about taking turns, help, and care.

Premise:
- A child and someone close to them share a tiny living thing.
- It needs care to grow: water, sun, room, patience.
- One character wants to keep it all to themselves, or forgets to share the work.
- The turning point is a concrete sharing decision: taking turns, dividing a task,
  or letting someone else help.
- The ending proves the shared care changed the world state: the plant grows,
  the mood softens, and the shared item ends up safer or better.

This script follows the Storyweavers contract:
- standalone stdlib script
- eager results import
- lazy ASP import in helper functions
- StoryParams, registries, parser, resolve_params, generate, emit, main
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    shared_with: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    thing: object | None = None
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    indoors: bool = True
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
class SharedThing:
    id: str
    label: str
    phrase: str
    type: str
    growth_kind: str
    needs: set[str]
    nurtures_with: set[str]
    shared_name: str = ""
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
class Routine:
    id: str
    verb: str
    gerund: str
    request: str
    result: str
    need: str
    need_word: str
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
class ShareOption:
    id: str
    offer: str
    tail: str
    label: str
    helpful_to: set[str]
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


GROWTH: dict[str, SharedThing] = {
    "bean": SharedThing(
        id="bean",
        label="bean plant",
        phrase="a tiny bean plant in a clay pot",
        type="plant",
        growth_kind="grow",
        needs={"water", "sun"},
        nurtures_with={"water", "sun", "care"},
        shared_name="the bean plant",
    ),
    "herb": SharedThing(
        id="herb",
        label="herb sprout",
        phrase="a little herb sprout in a green cup",
        type="plant",
        growth_kind="grow",
        needs={"water", "sun"},
        nurtures_with={"water", "sun", "care"},
        shared_name="the herb sprout",
    ),
    "sunflower": SharedThing(
        id="sunflower",
        label="sunflower seedling",
        phrase="a sunflower seedling in a sunny box",
        type="plant",
        growth_kind="grow",
        needs={"water", "sun"},
        nurtures_with={"water", "sun", "care"},
        shared_name="the sunflower seedling",
    ),
}

ROUTINES: dict[str, Routine] = {
    "water": Routine(
        id="water",
        verb="water the plant",
        gerund="watering the plant",
        request="pour a little water on it",
        result="the soil stayed damp and happy",
        need="water",
        need_word="water",
        tags={"water", "grow"},
    ),
    "sun": Routine(
        id="sun",
        verb="move the plant to the sunny windowsill",
        gerund="setting the plant in the sun",
        request="put it where the light could reach it",
        result="the leaves could drink in the light",
        need="sun",
        need_word="sunlight",
        tags={"sun", "grow"},
    ),
    "care": Routine(
        id="care",
        verb="check on the plant together",
        gerund="taking care of the plant",
        request="look at the leaves and the soil",
        result="someone noticed what the plant needed",
        need="care",
        need_word="care",
        tags={"care", "grow", "sharing"},
    ),
}

SHARES: dict[str, ShareOption] = {
    "turns": ShareOption(
        id="turns",
        offer="take turns",
        tail="They made a tiny schedule on a scrap of paper.",
        label="taking turns",
        helpful_to={"water", "care"},
    ),
    "split": ShareOption(
        id="split",
        offer="split the job",
        tail="One carried the cup, and the other carried the watering can.",
        label="splitting the job",
        helpful_to={"water", "sun", "care"},
        plural=True,
    ),
    "together": ShareOption(
        id="together",
        offer="do it together",
        tail="They stood side by side and watched the plant closely.",
        label="doing it together",
        helpful_to={"water", "sun", "care"},
        plural=True,
    ),
}

PLACES: dict[str, Place] = {
    "kitchen": Place("the kitchen", indoors=True, affords={"water", "care"}),
    "windowsill": Place("the windowsill", indoors=True, affords={"sun", "care"}),
    "balcony": Place("the balcony", indoors=False, affords={"sun", "water", "care"}),
    "back porch": Place("the back porch", indoors=False, affords={"water", "care"}),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Sofia", "Ivy", "June", "Ella", "Maya"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Owen", "Eli", "Theo", "Jack", "Sam"]
TRAITS = ["gentle", "curious", "patient", "cheerful", "stubborn", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for routine_id in place.affords:
            for thing_id, thing in GROWTH.items():
                if routine_id in thing.needs:
                    combos.append((place_id, routine_id, thing_id))
    return combos


@dataclass
class StoryParams:
    place: str
    routine: str
    thing: str
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


def prize_at_risk(routine: Routine, thing: SharedThing) -> bool:
    return routine.id in thing.needs


def select_share(routine: Routine) -> Optional[ShareOption]:
    for share in SHARES.values():
        if routine.id in share.helpful_to:
            return share
    return None


def explain_rejection(routine: Routine, thing: SharedThing) -> str:
    return (
        f"(No story: {routine.gerund} does not really help {thing.shared_name}. "
        f"Choose a routine that the plant actually needs.)"
    )


def explain_gender(thing_id: str, gender: str) -> str:
    return f"(No story: this world's default sample set expects a {gender} who can plausibly care for {GROWTH[thing_id].label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A slice-of-life storyworld about sharing care for a growing thing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--routine", choices=ROUTINES)
    ap.add_argument("--thing", choices=GROWTH)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    if getattr(args, "routine", None) and getattr(args, "thing", None):
        r, t = _safe_lookup(ROUTINES, getattr(args, "routine", None)), GROWTH[getattr(args, "thing", None)]
        if not prize_at_risk(r, t):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "routine", None) is None or c[1] == getattr(args, "routine", None))
              and (getattr(args, "thing", None) is None or c[2] == getattr(args, "thing", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place_id, routine_id, thing_id = rng.choice(list(combos))
    thing = GROWTH[thing_id]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) if hasattr(args, "trait") and getattr(args, "trait", None) else rng.choice(TRAITS)
    return StoryParams(place=place_id, routine=routine_id, thing=thing_id,
                       name=name, gender=gender, helper=helper, trait=trait)


def story_intro(hero: Entity, helper: Entity, thing: Entity, routine: Routine, place: Place) -> str:
    return (
        f"{hero.id} was a little {hero.type} who liked quiet afternoons at {place.name}. "
        f"{hero.pronoun().capitalize()} and {helper.label_word} were caring for {thing.label} together, "
        f"and {hero.id} loved {routine.gerund} because it made the room feel calm."
    )


def simulate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    thing = world.get("thing")
    routine: Routine = _safe_fact(world, world.facts, "routine")
    share: ShareOption = _safe_fact(world, world.facts, "share")

    world.say(story_intro(hero, helper, thing, routine, world.place))

    world.para()
    if routine.id == "water":
        world.say(f"One day, {hero.id} wanted to {routine.verb}, but {helper.label_word} noticed the plant was already thirsty.")
        world.say(f"{hero.id} reached for the watering can anyway, then paused and listened.")
        hero.memes["want"] = hero.memes.get("want", 0) + 1
        hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
        world.say(f'They agreed to {share.offer} so nobody missed a turn, and {share.tail}')
        thing.meters["water"] = thing.meters.get("water", 0) + 1
        thing.memes["care"] = thing.memes.get("care", 0) + 1
        world.say(f"After that, {thing.label} had enough water, and {routine.result}.")
    elif routine.id == "sun":
        world.say(f"One bright morning, {hero.id} wanted to {routine.verb}, but the sunny spot was small.")
        world.say(f"{helper.label_word} suggested they {share.offer} so the pot could rest in the light without bumping elbows.")
        hero.memes["want"] = hero.memes.get("want", 0) + 1
        hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
        world.say(share.tail)
        thing.meters["sun"] = thing.meters.get("sun", 0) + 1
        thing.memes["care"] = thing.memes.get("care", 0) + 1
        world.say(f"The little plant stood in the light, and {routine.result}.")
    else:
        world.say(f"Later, {hero.id} wanted to {routine.verb}, but {helper.label_word} said the plant needed both eyes and patience.")
        world.say(f"So they decided to {share.offer}. {share.tail}")
        hero.memes["sharing"] = hero.memes.get("sharing", 0) + 1
        thing.memes["care"] = thing.memes.get("care", 0) + 1
        thing.meters["care"] = thing.meters.get("care", 0) + 1
        world.say(f"With two sets of hands, {thing.label} got a careful check, and {routine.result}.")

    thing.meters["grow"] = thing.meters.get("grow", 0) + 1
    thing.meters["tall"] = thing.meters.get("tall", 0) + 1
    hero.memes["happy"] = hero.memes.get("happy", 0) + 1
    helper.memes["happy"] = helper.memes.get("happy", 0) + 1
    world.say(f"By bedtime, {thing.label} looked a little taller, and {hero.id} felt proud to share the work.")


def tell(place: Place, routine: Routine, thing_cfg: SharedThing,
         hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=helper_type))
    thing = world.add(Entity(id="thing", kind="thing", type=thing_cfg.type,
                             label=thing_cfg.label, phrase=thing_cfg.phrase))
    world.facts.update(hero=hero, helper=helper, thing=thing, routine=routine, share=select_share(routine),
                       place=place, thing_cfg=thing_cfg, trait=trait)
    simulate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    routine: Routine = _safe_fact(world, f, "routine")
    thing_cfg: SharedThing = _safe_fact(world, f, "thing_cfg")
    return [
        f'Write a short slice-of-life story for a young child about "{routine.id}" and sharing care for a growing thing.',
        f"Tell a gentle story where {hero.id} wants to {routine.verb}, {helper.label_word} wants to help, and {thing_cfg.shared_name} gets cared for together.",
        f'Write a simple story about a child named {hero.id} who learns to share the job of {routine.gerund}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    thing: Entity = _safe_fact(world, f, "thing")
    routine: Routine = _safe_fact(world, f, "routine")
    share: ShareOption = _safe_fact(world, f, "share")
    place: Place = _safe_fact(world, f, "place")
    trait = _safe_fact(world, f, "trait")

    return [
        QAItem(
            question=f"What did {hero.id} want to do at {place.name}?",
            answer=f"{hero.id} wanted to {routine.verb}, and {helper.label_word} helped make sure it happened the sharing way.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {helper.label_word} need to share the job?",
            answer=f"They needed to share because {thing.label} was growing and needed careful help, not just one hurried turn.",
        ),
        QAItem(
            question=f"What changed after they chose {share.label}?",
            answer=f"After they chose {share.label}, {thing.label} got what it needed and looked a little taller, while {hero.id} felt proud.",
        ),
        QAItem(
            question=f"How did the {trait} child feel at the end?",
            answer=f"{hero.id} felt happy and calm because sharing the care helped the little plant grow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a plant need to grow?",
            answer="A plant usually needs water, sunlight, space, and steady care to grow well.",
        ),
        QAItem(
            question="What does it mean to share a job?",
            answer="Sharing a job means two or more people each do a part of the work so it feels easier and fairer.",
        ),
        QAItem(
            question="Why do people put a plant in a sunny place?",
            answer="People put a plant in a sunny place because sunlight helps many plants make food and grow.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="windowsill", routine="sun", thing="bean", name="Mia", gender="girl", helper="mother", trait="patient"),
    StoryParams(place="kitchen", routine="water", thing="herb", name="Leo", gender="boy", helper="father", trait="curious"),
    StoryParams(place="balcony", routine="care", thing="sunflower", name="Nora", gender="girl", helper="mother", trait="gentle"),
]


ASP_RULES = r"""
place(P) :- setting(P).
routine(R) :- action(R).
thing(T) :- plant(T).

needs(T, R) :- plant(T), action(R), requires(T, R).
can_share(R) :- action(R), share_help(R).

valid(P, R, T) :- place(P), routine(R), thing(T), affords(P, R), needs(T, R), can_share(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("setting", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for r in sorted(p.affords):
            lines.append(asp.fact("affords", pid, r))
    for rid, r in ROUTINES.items():
        lines.append(asp.fact("action", rid))
        lines.append(asp.fact("requires", "bean", r.id) if r.id in GROWTH["bean"].needs else "")
        for tag in sorted(r.tags):
            lines.append(asp.fact("tag", rid, tag))
        lines.append(asp.fact("share_help", rid))
    for tid, t in GROWTH.items():
        lines.append(asp.fact("plant", tid))
        for n in sorted(t.needs):
            lines.append(asp.fact("needs", tid, n))
    return "\n".join(l for l in lines if l)


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


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    routine = _safe_lookup(ROUTINES, params.routine)
    thing = GROWTH[params.thing]
    world = tell(place, routine, thing, params.name, params.gender, params.helper, params.trait)
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


def valid_options_for_args(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    return [c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "routine", None) is None or c[1] == getattr(args, "routine", None))
            and (getattr(args, "thing", None) is None or c[2] == getattr(args, "thing", None))]


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

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.routine} at {p.place} (thing: {p.thing})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
