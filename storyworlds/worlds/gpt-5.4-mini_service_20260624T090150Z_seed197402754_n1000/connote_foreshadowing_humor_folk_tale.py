#!/usr/bin/env python3
"""
storyworlds/worlds/connote_foreshadowing_humor_folk_tale.py
============================================================

A small folk-tale story world with foreshadowing, humor, and a gentle turn.

The seed idea is a tiny village tale: someone carries a prized thing past a
warning sign, the world gives a funny omen, trouble arrives in a concrete way,
and a sensible helper or tool makes the ending safe.

This world keeps the prose child-facing and state-driven:
- physical meters: risk, strain, spoil, luck, distance
- emotional memes: worry, pride, humor, relief, affection

The seed word "connote" is used in the story logic and in the prompts: the
omen or little sign does not merely happen; it connotes what may come next.
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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    ent: object | None = None
    hero: object | None = None
    pr: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
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
    id: str
    label: str
    type: str
    indoors: bool = False
    safe_tags: set[str] = field(default_factory=set)
    foreshadow: str = ""
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    omen: str
    tag: str
    zone: set[str]
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
class Prize:
    id: str
    label: str
    phrase: str
    type: str
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
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
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


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    gender: str
    elder: str
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


SETTINGS = {
    "market": Place("market", "the market square", "market", False, {"crowd", "food"}, "A rooster on the fence crowed three times, as if it knew something."),
    "river": Place("river", "the river path", "river", False, {"water", "bridge"}, "The bridge boards creaked like old knees."),
    "orchard": Place("orchard", "the orchard", "orchard", False, {"fruit", "wind"}, "A pear dropped early with a tiny plop."),
    "hearth": Place("hearth", "the warm hearth room", "hearth", True, {"bread", "smoke"}, "The kettle chuckled before the tale began."),
}

CHALLENGES = {
    "goose": Challenge(
        id="goose",
        verb="cross the yard with the pie",
        gerund="crossing with the pie",
        rush="hurry past the goose",
        risk="pecked and smudged",
        omen="A goose hissed from behind the pump, which seemed to connote trouble.",
        tag="goose",
        zone={"hands"},
        tags={"animal", "crowd"},
    ),
    "mud": Challenge(
        id="mud",
        verb="carry the berries home",
        gerund="carrying the berries",
        rush="dash across the muddy path",
        risk="splashed and muddied",
        omen="A muddy bootprint lay by the gate, as if the lane was warning everybody.",
        tag="mud",
        zone={"feet", "hem"},
        tags={"mud", "water"},
    ),
    "wind": Challenge(
        id="wind",
        verb="bring the bread basket to grandma",
        gerund="bringing the bread basket",
        rush="run before the wind could snatch it",
        risk="blown apart and scattered",
        omen="A little hat spun in a circle on the road, which connoted a windy trick ahead.",
        tag="wind",
        zone={"hands", "head"},
        tags={"wind"},
    ),
    "crowd": Challenge(
        id="crowd",
        verb="carry the honey jar through the fair",
        gerund="carrying the honey jar",
        rush="push through the jostling crowd",
        risk="jiggled and spilled",
        omen="Two sparrows hopped along the signpost, looking like they were pointing at the lane.",
        tag="crowd",
        zone={"hands"},
        tags={"crowd", "food"},
    ),
}

PRIZES = {
    "pie": Prize("pie", "a berry pie", "a berry pie", "pie", "hands"),
    "berries": Prize("berries", "a basket of berries", "a basket of berries", "berries", "hands", plural=True),
    "bread": Prize("bread", "a warm loaf of bread", "a warm loaf of bread", "bread", "hands"),
    "honey": Prize("honey", "a little honey jar", "a little honey jar", "honey jar", "hands"),
}

HELPERS = [
    Helper("basket_lid", "a wicker lid", "cover the basket with a wicker lid", "walk home with the lid snug on the basket", {"wind", "crowd"}, {"hands"}),
    Helper("wooden_board", "a flat wooden board", "set the pie on a flat wooden board", "carried the pie on the board like a tiny tray", {"goose", "crowd"}, {"hands"}),
    Helper("towel_wrap", "a thick towel", "wrap the berries in a thick towel", "went home with the berries tucked in the towel", {"mud", "wind"}, {"feet", "hem"}),
]


GIRL_NAMES = ["Mina", "Tessa", "Lina", "Nora", "Ayla", "Pia", "Sana"]
BOY_NAMES = ["Ben", "Rafi", "Owen", "Jace", "Tom", "Milo", "Theo"]
ELDERS = ["grandmother", "grandfather"]
TRAITS = ["clever", "brave", "bright", "cheerful", "spry", "kind"]


def challenge_at_risk(ch: Challenge, pr: Prize) -> bool:
    return pr.region in ch.zone


def select_helper(ch: Challenge, pr: Prize) -> Optional[Helper]:
    for h in HELPERS:
        if ch.tag in h.guards and pr.region in h.covers:
            return h
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for cid, ch in CHALLENGES.items():
            for pid, pr in PRIZES.items():
                if place in SETTINGS and challenge_at_risk(ch, pr) and select_helper(ch, pr):
                    out.append((place, cid, pid))
    return out


def activity_delight(ch: Challenge) -> str:
    return {
        "goose": "the goose's huffing made the day sound more serious than it really was",
        "mud": "the muddy lane glistened like chocolate syrup in the sun",
        "wind": "the wind made the leaves clap their hands",
        "crowd": "the fair hummed like a nest full of happy bees",
    }[ch.id]


def introduce(world: World, hero: Entity, trait: str) -> None:
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved a tidy errand and a good joke.")


def setup(world: World, hero: Entity, elder: Entity, prize: Entity, ch: Challenge) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(f"One morning, {hero.id} carried {hero.pronoun('possessive')} {prize.label} and laughed at how shiny it looked.")
    world.say(f"{hero.pronoun('possessive').capitalize()} {elder.type} said, '{ch.omen}'")
    world.say(f"The old saying around the village was that such signs connoted a twist before supper.")


def tension(world: World, hero: Entity, elder: Entity, prize: Entity, ch: Challenge) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(f"Still, {hero.id} wanted to {ch.verb}, and {hero.pronoun('possessive')} feet began to hurry.")
    world.say(f"Then {hero.id} saw the problem at once: if {hero.pronoun('subject')} tried to {ch.rush}, {prize.label} might be {ch.risk}.")
    world.say(f"That made {hero.pronoun('object')} pause with a puzzled face, and even the goose would have laughed at that.")


def fix(world: World, hero: Entity, elder: Entity, prize: Entity, ch: Challenge) -> Optional[Helper]:
    helper = select_helper(ch, prize)
    if helper is None:
        return None
    ent = world.add(Entity(
        id=helper.id,
        kind="thing",
        type="helper",
        label=helper.label,
        protective=True,
        covers=set(helper.covers),
        owner=hero.id,
        caretaker=elder.id,
    ))
    ent.worn_by = hero.id
    world.say(f"{hero.pronoun('possessive').capitalize()} {elder.type} smiled and found {helper.label}: {helper.prep}.")
    return helper


def resolve(world: World, hero: Entity, elder: Entity, prize: Entity, ch: Challenge, helper: Helper) -> None:
    hero.memes["worry"] = 0
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    world.say(f"So {hero.id} did it the funny way, and the goose only blinked as {hero.pronoun('subject')} went by.")
    world.say(f"They {helper.tail}, and {hero.id}'s {prize.label} stayed safe.")
    world.say(f"By the end, even the old lane seemed to grin, as if it had only been teasing all along.")


def tell(place: Place, ch: Challenge, prize: Prize, name: str, gender: str, elder_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label=f"the {elder_type}"))
    pr = world.add(Entity(id="Prize", kind="thing", type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id, caretaker=elder.id, plural=prize.plural))
    introduce(world, hero, trait)
    setup(world, hero, elder, pr, ch)
    world.para()
    tension(world, hero, elder, pr, ch)
    helper = fix(world, hero, elder, pr, ch)
    world.para()
    if helper:
        resolve(world, hero, elder, pr, ch, helper)
    world.facts.update(hero=hero, elder=elder, prize=pr, challenge=ch, helper=helper, trait=trait, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    pr = _safe_fact(world, f, "prize")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short folk-tale for a child about {hero.id} and a {ch.id} omen at {place.label}, and make the sign connote what comes next.',
        f"Tell a humorous story where {hero.id} wants to {ch.verb} while carrying {pr.phrase}, and an elder helps with a sensible fix.",
        f'Write a gentle village tale using the word "connote" and ending with {hero.id} safely keeping {pr.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    prize = _safe_fact(world, f, "prize")
    ch = _safe_fact(world, f, "challenge")
    helper = _safe_fact(world, f, "helper")
    trait = _safe_fact(world, f, "trait")
    place = _safe_fact(world, f, "place")
    qs = [
        QAItem(
            question=f"Who was the story about at {place.label}?",
            answer=f"It was about {hero.id}, a little {trait} {hero.type}, and {hero.pronoun('possessive')} {elder.type}, who helped keep the errand safe.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with {prize.label}?",
            answer=f"{hero.id} wanted to {ch.verb}. That sounded fine at first, but the old sign and the waiting trouble made it risky.",
        ),
        QAItem(
            question=f"What warning sign seemed to connote trouble?",
            answer=f"{ch.omen}",
        ),
    ]
    if helper:
        qs.append(QAItem(
            question=f"How did the elder help {hero.id} keep {prize.label} safe?",
            answer=f"{hero.pronoun('possessive').capitalize()} {elder.type} used {helper.label} and told {hero.id} to {helper.prep}. That matched the trouble and kept {prize.label} safe.",
        ))
        qs.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and amused. The joke of the moment was that the scary sign only led to a clever fix, and the errand ended well.",
        ))
    return qs


KNOWLEDGE = {
    "goose": [("What is a goose?", "A goose is a bird with a strong neck and a loud voice. Geese can hiss when they feel bothered.")],
    "mud": [("What is mud?", "Mud is soft, wet earth. It can stick to shoes and make things dirty.")],
    "wind": [("What does wind do?", "Wind is moving air. It can rustle leaves, move hats, and push light things around.")],
    "crowd": [("What is a crowd?", "A crowd is a group of many people in one place. Crowds can be noisy and busy.")],
    "pie": [("Why do people like pie?", "Many people like pie because it can be sweet, warm, and full of fruit.")],
    "bread": [("What is bread?", "Bread is a food made from dough and baked until it is firm and tasty.")],
    "honey": [("What is honey?", "Honey is a sweet golden food made by bees from flower nectar.")],
    "connote": [("What does connote mean?", "Connote means to suggest or hint at something without saying it directly.")],
}
KNOWLEDGE_ORDER = ["connote", "goose", "mud", "wind", "crowd", "pie", "bread", "honey"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["challenge"].tags) | {world.facts["prize"].type, "connote"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(C, P) :- challenge(C), prize(P), zone(C, R), region(P, R).
helper_ok(C, P, H) :- challenge(C), prize(P), helper(H), tag_of(C, T), guards(H, T), zone(C, R), covers(H, R).
valid(Place, C, P) :- place(Place), challenge(C), prize(P), place_has(Place, C), prize_at_risk(C, P), helper_ok(C, P, _).
valid_story(Place, C, P, Gender) :- valid(Place, C, P), wears(Gender, P).
#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for cid in sorted(CHALLENGES):
            lines.append(asp.fact("place_has", pid, cid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("tag_of", cid, c.tag))
        for r in sorted(c.zone):
            lines.append(asp.fact("zone", cid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for t in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, t))
        for r in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale story world with foreshadowing and humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDERS)
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
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(ELDERS)
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, gender=gender, elder=elder)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for cid, ch in CHALLENGES.items():
            for pid, pr in PRIZES.items():
                if challenge_at_risk(ch, pr) and select_helper(ch, pr):
                    out.append((place, cid, pid))
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.elder, "clever")
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
    StoryParams(place="market", challenge="goose", prize="pie", name="Mina", gender="girl", elder="grandmother"),
    StoryParams(place="river", challenge="mud", prize="berries", name="Ben", gender="boy", elder="grandfather"),
    StoryParams(place="orchard", challenge="wind", prize="bread", name="Lina", gender="girl", elder="grandmother"),
    StoryParams(place="hearth", challenge="crowd", prize="honey", name="Theo", gender="boy", elder="grandfather"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):")
        for place, ch, pr in triples:
            genders = sorted(g for (pl, c, p, g) in stories if (pl, c, p) == (place, ch, pr))
            print(f"  {place:8} {ch:8} {pr:8} [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
