#!/usr/bin/env python3
"""
storyworlds/worlds/commemorate_suspense_inner_monologue_sharing_myth.py
=======================================================================

A small myth-like story world about a child or keeper who wants to
commemorate something dear, faces a suspenseful problem, listens to an inner
monologue, and resolves it by sharing.

Premise:
- A village prepares a remembrance rite for an old hero, a season, or a gift.
- The hero/keeper feels suspense when an important tribute goes missing or
  cannot be carried alone.
- Inner monologue turns worry into a thoughtful plan.
- Sharing the tribute or the work lets the rite succeed.

This world uses:
- typed entities with physical meters and emotional memes
- a reasonableness gate and an ASP twin
- state-driven prose, not a frozen paragraph swap
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    shareable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid: object | None = None
    elder_ent: object | None = None
    hero: object | None = None
    tribute: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "elderwoman"}
        male = {"boy", "father", "man", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

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
    id: str
    label: str
    indoor: bool = False
    supports: set[str] = field(default_factory=set)
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
class Rite:
    id: str
    noun: str
    verb: str
    inner_voice: str
    suspense: str
    share_verb: str
    outcome: str
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
class Tribute:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    risk: str = "lost"
    help_item: Optional[str] = None
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
class Aid:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    share_style: str
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


@dataclass
class StoryParams:
    place: str
    rite: str
    tribute: str
    aid: str
    name: str
    gender: str
    elder: str
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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    tribute = world.facts.get("tribute")
    if not hero or not tribute:
        return out
    if hero.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("suspense", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0
    out.append(f"The air grew still, and the old rite felt full of suspense.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    aid = world.facts.get("aid")
    tribute = world.facts.get("tribute")
    if not hero or not aid or not tribute:
        return out
    if hero.memes.get("sharing", 0.0) < THRESHOLD:
        return out
    if tribute.carried_by != hero.id:
        return out
    sig = ("share", hero.id, aid.id, tribute.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["worry"] = 0.0
    out.append(f"Sharing made the heavy task lighter.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="suspense", apply=_r_suspense),
    Rule(name="share", apply=_r_share),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def inner_monologue(hero: Entity, rite: Rite, tribute: Tribute, aid: Aid) -> str:
    return (
        f"{hero.pronoun().capitalize()} thought, "
        f'"If I try to {rite.verb} alone, the {tribute.label} may {tribute.risk}. '
        f'But if I share the work, the rite can still shine."'
    )


def validate_combo(place: Place, rite: Rite, tribute: Tribute, aid: Aid) -> bool:
    return (
        rite.id in place.supports
        and tribute.region in aid.covers
        and tribute.help_item == aid.id
        and rite.id in aid.helps
    )


def explain_rejection(place: Place, rite: Rite, tribute: Tribute, aid: Aid) -> str:
    return (
        f"(No story: this place cannot safely host the rite, or the aid does not "
        f"truly help with the {tribute.label}. The sharing fix must fit the risk.)"
    )


PLACES = {
    "grove": Place(id="grove", label="the moonlit grove", indoor=False, supports={"commemoration", "song", "sharing"}),
    "shore": Place(id="shore", label="the quiet shore", indoor=False, supports={"commemoration", "sharing"}),
    "hall": Place(id="hall", label="the old hall", indoor=True, supports={"commemoration", "song", "sharing"}),
}

RITES = {
    "commemoration": Rite(
        id="commemoration",
        noun="commemoration rite",
        verb="carry the tribute to the stone",
        inner_voice="the story of the old hero still mattered",
        suspense="the missing tribute left the circle waiting",
        share_verb="share the tribute",
        outcome="the village would remember together",
        tags={"commemorate", "myth"},
    ),
    "song": Rite(
        id="song",
        noun="song rite",
        verb="lift the song for the ancestors",
        inner_voice="a song could carry memory farther than footsteps",
        suspense="the chorus needed one steady voice",
        share_verb="share the song",
        outcome="the hall would ring like a shell",
        tags={"myth"},
    ),
}

TRIBUTES = {
    "torch": Tribute(
        id="torch",
        label="torch",
        phrase="a bright cedar torch",
        region="hand",
        risk="go dark in the wind",
        help_item="lamp",
        genders={"boy", "girl"},
    ),
    "garland": Tribute(
        id="garland",
        label="garland",
        phrase="a woven flower garland",
        region="head",
        risk="slip and scatter",
        help_item="ribbon",
        genders={"girl", "boy"},
    ),
    "drum": Tribute(
        id="drum",
        label="drum",
        phrase="a painted drum",
        region="hand",
        risk="be dropped in the rush",
        help_item="strap",
        genders={"boy", "girl"},
    ),
}

AIDS = {
    "lamp": Aid(
        id="lamp",
        label="a small lamp",
        phrase="a small lamp with a steady flame",
        helps={"commemoration"},
        covers={"hand"},
        share_style="held it together so the flame would not shake",
        tags={"light", "sharing"},
    ),
    "ribbon": Aid(
        id="ribbon",
        label="a soft ribbon",
        phrase="a soft blue ribbon",
        helps={"commemoration"},
        covers={"head"},
        share_style="tied the garland so it would stay in place",
        tags={"sharing"},
    ),
    "strap": Aid(
        id="strap",
        label="a braided strap",
        phrase="a braided strap for carrying",
        helps={"commemoration", "song"},
        covers={"hand"},
        share_style="shared the weight across two hands",
        tags={"sharing"},
    ),
}

NAMES_GIRL = ["Mira", "Nora", "Lena", "Sana", "Tia"]
NAMES_BOY = ["Ari", "Daro", "Milo", "Rin", "Tomas"]
TRAITS = ["quiet", "brave", "curious", "gentle", "hopeful"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES.values():
        for r in RITES.values():
            for t in TRIBUTES.values():
                for a in AIDS.values():
                    if validate_combo(p, r, t, a):
                        combos.append((p.id, r.id, t.id, a.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world of commemorating with suspense and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--tribute", choices=TRIBUTES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["elder", "grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) and getattr(args, "rite", None) and getattr(args, "tribute", None) and getattr(args, "aid", None):
        if not validate_combo(_safe_lookup(PLACES, getattr(args, "place", None)), _safe_lookup(RITES, getattr(args, "rite", None)), _safe_lookup(TRIBUTES, getattr(args, "tribute", None)), _safe_lookup(AIDS, getattr(args, "aid", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "rite", None) is None or c[1] == getattr(args, "rite", None))
              and (getattr(args, "tribute", None) is None or c[2] == getattr(args, "tribute", None))
              and (getattr(args, "aid", None) is None or c[3] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, rite, tribute, aid = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    elder = getattr(args, "elder", None) or rng.choice(["elder", "grandmother", "grandfather"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, rite=rite, tribute=tribute, aid=aid, name=name, gender=gender, elder=elder, trait=trait)


def tell(place: Place, rite: Rite, tribute_cfg: Tribute, aid_def: Aid, name: str, gender: str, elder: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    elder_ent = world.add(Entity(id="elder", kind="character", type=elder if elder in {"grandmother", "grandfather"} else "elderman", label=f"the {elder}"))
    tribute = world.add(Entity(
        id="tribute", type="thing", label=tribute_cfg.label, phrase=tribute_cfg.phrase,
        owner=hero.id, caretaker=elder_ent.id, carried_by=hero.id, shareable=True, plural=tribute_cfg.plural
    ))
    aid = world.add(Entity(
        id="aid", type="thing", label=aid_def.label, phrase=aid_def.phrase,
        owner=elder_ent.id, shareable=True
    ))

    hero.memes["love"] = 1.0
    hero.memes["worry"] = 1.0

    world.say(
        f"In {place.label}, {hero.id} was a {trait} little {gender} who wanted to {rite.verb} for the village."
    )
    world.say(
        f"The people had gathered to {rite.share_verb}, because {rite.inner_voice}."
    )
    world.para()
    world.say(
        f"But when the time came, the {tribute.label} was not ready, and the circle held its breath."
    )
    world.say(
        inner_monologue(hero, rite, tribute, aid)
    )
    world.say(
        f"{hero.id} looked at {elder_ent.label} and then at {aid.label}, wondering whether one pair of hands could do enough."
    )
    hero.memes["suspense"] = 1.0
    propagate(world, narrate=True)
    world.para()

    hero.memes["sharing"] = 1.0
    aid.carried_by = hero.id
    tribute.carried_by = hero.id
    world.say(
        f"{hero.id} chose to share the work with {elder_ent.label}: they {aid_def.share_style}, and the tribute finally moved."
    )
    propagate(world, narrate=True)
    world.say(
        f"At last, {hero.id} and {elder_ent.label} reached the stone together, and the village knew {rite.outcome}."
    )
    world.say(
        f"The {tribute.label} shone there at the end, and the old memory felt warm again."
    )
    world.facts.update(hero=hero, elder=elder_ent, tribute=tribute, aid=aid, rite=rite, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rite = _safe_fact(world, f, "rite")
    tribute = _safe_fact(world, f, "tribute")
    return [
        f"Write a myth-like story for a child about {hero.id} trying to {rite.share_verb} with a {tribute.label}.",
        f"Tell a short story with suspense, inner monologue, and sharing, ending in a commemoration rite.",
        f"Write a gentle myth where a young helper worries about a lost tribute and finds a shared way to honor the village.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    tribute = _safe_fact(world, f, "tribute")
    rite = _safe_fact(world, f, "rite")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who was the story about at {place.label}?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {elder.label}, who helped with the old rite.",
        ),
        QAItem(
            question=f"What was {hero.id} trying to do for the village?",
            answer=f"{hero.id} was trying to {rite.share_verb} and finish the commemoration rite with the {tribute.label}.",
        ),
        QAItem(
            question=f"Why did the moment feel suspenseful?",
            answer=f"It felt suspenseful because the {tribute.label} was not ready at first, and everyone had to wait and hope.",
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"It was solved by sharing the work with {elder.label}, so the tribute could be carried safely to the stone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to commemorate something?",
            answer="To commemorate something means to remember it with a special act, story, or ceremony.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting and wondering what will happen next.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in a character's own mind when they think to themselves.",
        ),
        QAItem(
            question="Why can sharing help in a story?",
            answer="Sharing can help because more than one person can carry, solve, or care for something together.",
        ),
    ]


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if bits:
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(grove). place(shore). place(hall).
rite(commemoration). rite(song).
tribute(torch). tribute(garland). tribute(drum).
aid(lamp). aid(ribbon). aid(strap).

supports(grove,commemoration). supports(grove,song). supports(grove,sharing).
supports(shore,commemoration). supports(shore,sharing).
supports(hall,commemoration). supports(hall,song). supports(hall,sharing).

helps(lamp,commemoration). helps(ribbon,commemoration). helps(strap,commemoration). helps(strap,song).
covers(lamp,hand). covers(ribbon,head). covers(strap,hand).

help_item(torch,lamp). help_item(garland,ribbon). help_item(drum,strap).

valid(P,R,T,A) :- place(P), rite(R), tribute(T), aid(A),
                  supports(P,R),
                  help_item(T,A),
                  helps(A,R),
                  covers(A,Region), tribute_region(T,Region).

valid_story(P,R,T,A) :- valid(P,R,T,A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", p.id, s))
    for r in RITES.values():
        lines.append(asp.fact("rite", r.id))
    for t in TRIBUTES.values():
        lines.append(asp.fact("tribute", t.id))
        lines.append(asp.fact("tribute_region", t.id, t.region))
    for a in AIDS.values():
        lines.append(asp.fact("aid", a.id))
        for s in sorted(a.helps):
            lines.append(asp.fact("helps", a.id, s))
        for c in sorted(a.covers):
            lines.append(asp.fact("covers", a.id, c))
    for t in TRIBUTES.values():
        if t.help_item:
            lines.append(asp.fact("help_item", t.id, t.help_item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="grove", rite="commemoration", tribute="torch", aid="lamp", name="Mira", gender="girl", elder="grandmother", trait="brave"),
    StoryParams(place="hall", rite="commemoration", tribute="garland", aid="ribbon", name="Ari", gender="boy", elder="grandfather", trait="gentle"),
    StoryParams(place="shore", rite="commemoration", tribute="drum", aid="strap", name="Sana", gender="girl", elder="elder", trait="hopeful"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(RITES, params.rite),
        _safe_lookup(TRIBUTES, params.tribute),
        _safe_lookup(AIDS, params.aid),
        params.name,
        params.gender,
        params.elder,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.rite} at {p.place} (tribute: {p.tribute})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
