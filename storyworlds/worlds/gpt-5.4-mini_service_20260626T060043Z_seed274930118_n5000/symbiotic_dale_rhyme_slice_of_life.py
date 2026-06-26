#!/usr/bin/env python3
"""
storyworlds/worlds/symbiotic_dale_rhyme_slice_of_life.py
========================================================

A small, slice-of-life storyworld in a quiet dale, where a child and a grown-up
make space for a symbiotic little garden and use a rhyme to solve a tiny daily
problem.

Seed image:
- A child in the dale loves a rhyme.
- A bee and a clover patch need each other.
- A small choice about picking or keeping flowers creates a gentle tension.
- The ending shows the dale a little fuller, not just tidier.

This world models:
- physical meters: things like fullness, bloom, sweetness, buzz, wear, and tidy
- emotional memes: things like joy, worry, patience, pride, and warmth
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    bee: object | None = None
    child: object | None = None
    grownup: object | None = None
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


@dataclass
class Setting:
    place: str = "the dale"
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
    rush: str
    mess: str
    soil: str
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
class Prize:
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
class Symbiosis:
    id: str
    left: str
    right: str
    left_gain: str
    right_gain: str
    note: str
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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


def _r_symbiosis(world: World) -> list[str]:
    out: list[str] = []
    for sym in SYMBIOSES.values():
        if (sym.id,) in world.fired:
            continue
        left = world.entities.get(sym.left)
        right = world.entities.get(sym.right)
        if not left or not right:
            continue
        if left.meters.get("bloom", 0.0) >= THRESHOLD and right.meters.get("buzz", 0.0) >= THRESHOLD:
            world.fired.add((sym.id,))
            left.meters["fed"] = left.meters.get("fed", 0.0) + 1
            right.meters["fed"] = right.meters.get("fed", 0.0) + 1
            out.append(sym.note)
    return out


def _r_overpick(world: World) -> list[str]:
    out: list[str] = []
    clover = world.entities.get("clover")
    if not clover:
        return out
    if clover.meters.get("picked", 0.0) < THRESHOLD:
        return out
    if ("overpick",) in world.fired:
        return out
    world.fired.add(("overpick",))
    clover.meters["bloom"] = max(0.0, clover.meters.get("bloom", 0.0) - 1)
    out.append("The clover patch looked a little sparse after too much picking.")
    return out


def _r_apology(world: World) -> list[str]:
    child = world.entities.get("child")
    if not child or child.memes.get("worry", 0.0) < THRESHOLD:
        return []
    if ("apology",) in world.fired:
        return []
    partner = world.entities.get("bee")
    if not partner:
        return []
    world.fired.add(("apology",))
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1)
    child.memes["warmth"] = child.memes.get("warmth", 0.0) + 1
    partner.meters["buzz"] = partner.meters.get("buzz", 0.0) + 1
    return ["The rhyme made the buzzing soft and friendly again."]


CAUSAL_RULES: list[Rule] = [
    Rule("symbiosis", "physical", _r_symbiosis),
    Rule("overpick", "physical", _r_overpick),
    Rule("apology", "social", _r_apology),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def rhyme_line(name: str, object_word: str) -> str:
    return f"{name} sang, 'Be kind to the clover; don't pull it over. Leave some for the bee, and it will help thee.'"


def intro(world: World, child: Entity, grownup: Entity, setting: Setting) -> None:
    world.say(
        f"{child.id} lived in the dale with {grownup.label}."
        f" {child.pronoun().capitalize()} loved quiet mornings and little songs."
    )
    world.say(
        f"Near their path, a clover patch grew by the stones, and a bee zipped from flower to flower."
    )


def show_symbiosis(world: World) -> None:
    world.say(
        "The grown-up said the bee and the clover were good neighbors: "
        "the bee carried pollen, and the clover gave sweet nectar back."
    )


def want_pick(world: World, child: Entity, prize: Entity) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    world.say(
        f"{child.id} wanted to pick a handful of {prize.label} for a small crown, "
        f"but the patch was full of busy bees."
    )


def warn(world: World, grownup: Entity, child: Entity, prize: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f'"If we take too much," {grownup.label} said, '
        f'"the {prize.label} patch will have less to offer the bee."'
    )


def defy(world: World, child: Entity, activity: Activity) -> None:
    child.memes["stubborn"] = child.memes.get("stubborn", 0.0) + 1
    world.say(
        f"{child.id} frowned and reached anyway, then stopped and looked at the buzzing sky."
    )
    world.say(f"{child.pronoun().capitalize()} tried to {activity.rush}.")


def rhyme_and_pause(world: World, child: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    world.say(rhyme_line(child.id, "clover"))
    world.say("The little rhyme made the moment feel gentle, like a hand on a shoulder.")


def compromise(world: World, child: Entity, grownup: Entity, prize: Entity) -> None:
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1)
    prize.meters["picked"] = prize.meters.get("picked", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"Then they chose one small stem, left the rest swaying in the breeze, "
        f"and made the crown from only a few blossoms."
    )
    world.say(
        f"{child.id} smiled at the bee and said sorry in a rhyme, "
        f"while {grownup.label} tied the green stems together."
    )


def ending(world: World, child: Entity, grownup: Entity, prize: Prize) -> None:
    world.say(
        f"By afternoon, the dale was calm again: the bee still had flowers, "
        f"the clover still bloomed, and {child.id} wore a tiny crown that felt just right."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina",
         hero_type: str = "girl", parent_type: str = "grandmother", trait: str = "gentle") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait, "curious"],
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=parent_type,
        label="Grandma",
    ))
    prize = world.add(Entity(
        id="clover",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=child.id,
        caretaker=grownup.id,
        meters={"bloom": 1.0},
    ))
    bee = world.add(Entity(
        id="bee",
        type="bee",
        label="bee",
        meters={"buzz": 1.0},
        memes={"busy": 1.0},
    ))
    world.add(Entity(
        id="song",
        type="song",
        label="rhyme",
        phrase="a tiny rhyme",
    ))

    intro(world, child, grownup, setting)
    show_symbiosis(world)
    world.para()
    want_pick(world, child, prize)
    warn(world, grownup, child, prize)
    defy(world, child, activity)
    rhyme_and_pause(world, child)
    compromise(world, child, grownup, prize)
    ending(world, child, grownup, prize)

    world.facts.update(
        child=child,
        grownup=grownup,
        prize=prize,
        bee=bee,
        activity=activity,
        setting=setting,
    )
    return world


SETTINGS = {
    "dale": Setting(place="the dale", affords={"pick_clover", "sing_rhyme"}),
}

ACTIVITIES = {
    "pick_clover": Activity(
        id="pick_clover",
        verb="pick clover",
        gerund="picking clover",
        rush="pick too many blossoms",
        mess="sparse",
        soil="thin",
        zone={"plant"},
        keyword="clover",
        tags={"clover", "bee", "garden"},
    ),
    "sing_rhyme": Activity(
        id="sing_rhyme",
        verb="sing a rhyme",
        gerund="singing a rhyme",
        rush="sing louder and louder",
        mess="soft",
        soil="soft",
        zone={"air"},
        keyword="rhyme",
        tags={"rhyme", "song"},
    ),
}

PRIZES = {
    "clover": Prize(
        label="clover",
        phrase="a patch of clover",
        type="plant",
        region="plant",
    )
}

SYMBIOSES = {
    "bee_clover": Symbiosis(
        id="bee_clover",
        left="clover",
        right="bee",
        left_gain="pollination",
        right_gain="nectar",
        note="The bee and the clover helped each other in the old, easy way nature likes.",
    )
}

GIRL_NAMES = ["Mina", "Nina", "Lila", "Tess", "Rosa", "June", "Pia", "Ivy"]
BOY_NAMES = ["Eli", "Jude", "Finn", "Owen", "Noah", "Theo", "Bram", "Max"]
TRAITS = ["gentle", "curious", "patient", "cheerful", "quiet", "bright"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("dale", "pick_clover", "clover")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life in a dale, with rhyme and symbiosis.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother", "grandfather"])
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
    if getattr(args, "place", None) and getattr(args, "place", None) != "dale":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "activity", None) != "pick_clover":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "prize", None) and getattr(args, "prize", None) != "clover":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["grandmother", "grandfather"])
    trait = getattr(args, "trait", None) if hasattr(args, "trait") and getattr(args, "trait", None) else rng.choice(TRAITS)
    return StoryParams(
        place="dale",
        activity="pick_clover",
        prize="clover",
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    return [
        f'Write a short slice-of-life story in a dale that includes the word "symbiotic".',
        f"Tell a gentle story where {child.id} loves a rhyme, worries about the clover patch, and learns to share with the bee.",
        f'Write a simple story about a child in the dale who pauses to choose a kinder way to handle the clover.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    grownup = _safe_fact(world, f, "grownup")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"Where does {child.id} live in this story?",
            answer=f"{child.id} lives in the dale with {grownup.label}.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the {prize.label} at first?",
            answer=f"{child.id} wanted to {activity.verb} for a small crown.",
        ),
        QAItem(
            question=f"How did the story end for the bee and the {prize.label}?",
            answer=f"The bee still had flowers to visit, and the {prize.label} still bloomed in the dale.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does symbiotic mean?",
            answer="Symbiotic means two living things help each other in a close, useful way.",
        ),
        QAItem(
            question="Why do bees visit flowers?",
            answer="Bees visit flowers to collect nectar and pollen, and while they move around, they help the flowers make seeds.",
        ),
        QAItem(
            question="Why can clover be good for a bee?",
            answer="Clover can give bees nectar, which is a sweet drink they use for food.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little pattern of sound in words, like when two words end with the same sound.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n,) in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), A = pick_clover, P = clover.
compatible_story(Place, A, P) :- setting(Place), prize_at_risk(A, P).
#show compatible_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


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
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.parent,
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


CURATED = [
    StoryParams(
        place="dale",
        activity="pick_clover",
        prize="clover",
        name="Mina",
        gender="girl",
        parent="grandmother",
        trait="gentle",
    )
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
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
            header = f"### {p.name}: {p.activity} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
