#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/gamut_mercy_reserve_kitchen_repetition_dialogue_bedtime.py
=============================================================================================

A tiny bedtime storyworld set in a kitchen, built around a child who wants
one more treat before sleep. The story uses repetition and dialogue, and the
world model decides whether a gentle compromise can keep the bedtime peace.

Seed tale:
---
A little child in the kitchen wanted one more sweet snack before bed.
The parent worried that too much sugar would keep the child awake.
The child asked for mercy, saying they had been good all day.
The parent checked the reserve jar, then offered a tiny bedtime compromise:
a warm drink and one small reserved cookie after brushing teeth.

The story grows from that premise into a complete bedtime turn and resolution.
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
    treat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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


@dataclass
class Setting:
    place: str = "the kitchen"
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
class Treat:
    id: str
    label: str
    phrase: str
    type: str
    at_risk: str  # "mouth" or "sleep" or both
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
class Comfort:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    protects: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    treat: str
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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"snack", "cocoa", "tea"}),
}

ACTIVITIES = {
    "snack": Activity(
        id="snack",
        verb="have one more sweet snack",
        gerund="snacking on sweets",
        rush="reach for one more cookie",
        mess="crumbs",
        soil="crumbly and sticky",
        zone={"mouth", "hands"},
        keyword="cookie",
        tags={"cookie", "sweet", "reserve"},
    ),
    "cocoa": Activity(
        id="cocoa",
        verb="sip a warm cocoa",
        gerund="sipping warm cocoa",
        rush="grab the cocoa mug",
        mess="spills",
        soil="spilled",
        zone={"hands", "shirt"},
        keyword="cocoa",
        tags={"cocoa", "warm", "reserve"},
    ),
    "tea": Activity(
        id="tea",
        verb="have a warm bedtime tea",
        gerund="sipping bedtime tea",
        rush="reach for the tea cup",
        mess="spills",
        soil="spilled",
        zone={"hands", "shirt"},
        keyword="tea",
        tags={"tea", "warm", "mercy"},
    ),
}

TREATS = {
    "cookie": Treat(
        id="cookie",
        label="cookie",
        phrase="one small reserved cookie",
        type="cookie",
        at_risk="mouth",
    ),
    "cocoa": Treat(
        id="cocoa",
        label="mug of cocoa",
        phrase="a warm mug of cocoa",
        type="cocoa",
        at_risk="sleep",
    ),
    "tea": Treat(
        id="tea",
        label="cup of tea",
        phrase="a tiny cup of bedtime tea",
        type="tea",
        at_risk="sleep",
    ),
}

COMFORTS = [
    Comfort(
        id="brushing",
        label="tooth brushing",
        prep="brush your teeth first",
        tail="brushed their teeth before bedtime",
        guards={"crumbs"},
        protects={"mouth"},
    ),
    Comfort(
        id="tiny_sip",
        label="a tiny sip",
        prep="take only a tiny sip",
        tail="took only a tiny sip and set the mug down",
        guards={"spills"},
        protects={"sleep"},
    ),
    Comfort(
        id="reserve_cookie",
        label="the reserve jar",
        prep="check the reserve jar for one small cookie",
        tail="chose one small cookie from the reserve jar",
        guards={"crumbs"},
        protects={"mouth"},
    ),
]

GIRL_NAMES = ["Mia", "Lina", "Nora", "Lily", "Ava", "Maya"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Theo", "Max"]
TRAITS = ["sleepy", "curious", "gentle", "patient", "small", "soft-spoken"]


def prize_at_risk(activity: Activity, treat: Treat) -> bool:
    return treat.at_risk in {"sleep", "mouth"} and (
        (treat.at_risk == "mouth" and "mouth" in activity.zone)
        or (treat.at_risk == "sleep" and activity.id in {"cocoa", "tea"})
    )


def select_comfort(activity: Activity, treat: Treat) -> Optional[Comfort]:
    for c in COMFORTS:
        if treat.at_risk in c.protects and activity.mess in c.guards:
            return c
        if treat.at_risk == "mouth" and c.id in {"brushing", "reserve_cookie"} and activity.id == "snack":
            return c
        if treat.at_risk == "sleep" and c.id == "tiny_sip" and activity.id in {"cocoa", "tea"}:
            return c
    return None


def explain_rejection(activity: Activity, treat: Treat) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly threaten {treat.phrase}, "
        f"so there is no bedtime worry to solve.)"
    )


def explain_gender(treat_id: str, gender: str) -> str:
    return f"(No story: try a different name; this world does not pin {treat_id} to {gender}.)"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["want"] = actor.memes.get("want", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} did the thing they wanted to do.")


def predict_risk(world: World, actor: Entity, activity: Activity, treat_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    treat = sim.get(treat_id)
    return {
        "mess": sim.get(actor.id).meters.get(activity.mess, 0.0),
        "sleepy": sim.get(actor.id).memes.get("sleepy", 0.0),
        "ruined": activity.id == "snack" and activity.mess == "crumbs" and treat.label == "cookie",
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("traits", []) if t != "small"), "sleepy")
    world.say(f"{hero.id} was a small {trait} {hero.type} who lived for bedtime stories and warm light.")


def set_scene(world: World, setting: Setting, activity: Activity) -> None:
    world.say(
        f"The kitchen was quiet and cozy, with a soft lamp and a sleepy clock."
    )
    world.say(
        f"On the table sat the reserve jar, and in it was a tiny treat waiting for later."
    )


def desire(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(
        f"{hero.id} looked at the table and whispered, "
        f"\"One more, one more,\" because {hero.pronoun('subject')} still wanted to {activity.verb}."
    )


def warning(world: World, parent: Entity, hero: Entity, activity: Activity, treat: Entity) -> None:
    pred = predict_risk(world, hero, activity, treat.id)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    if activity.id == "snack":
        world.say(
            f"\"Not yet,\" said {parent.id}. \"Too many crumbs before bed can make a small stomach busy.\""
        )
    else:
        world.say(
            f"\"Not too much,\" said {parent.id}. \"A big mug late at night can keep sleepy eyes open.\""
        )
    world.facts["predicted"] = pred


def plea_for_mercy(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["plea"] = hero.memes.get("plea", 0.0) + 1.0
    world.say(
        f"\"Please,\" said {hero.id}. \"Please have mercy. I was good all day. Please, please.\""
    )


def reserve_turn(world: World, parent: Entity, treat: Entity) -> None:
    world.say(
        f"{parent.id} opened the reserve jar and smiled at the little treasure inside."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, treat: Entity) -> Optional[Comfort]:
    comfort = select_comfort(activity, treat)
    if comfort is None:
        return None
    world.say(
        f"\"How about this?\" said {parent.id}. \"{comfort.prep}.\""
    )
    return comfort


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, treat: Entity, comfort: Comfort) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    world.say(
        f"\"Okay,\" said {hero.id}. \"Okay, okay.\""
    )
    world.say(
        f"So {hero.id} and {parent.id} {comfort.tail}, and the kitchen stayed cozy and quiet."
    )
    if activity.id == "snack":
        world.say(
            f"{hero.id} had the reserve cookie after brushing their teeth, and the last crumb was gone before the yawn."
        )
    else:
        world.say(
            f"{hero.id} had a tiny bedtime drink, then tucked in with a warm, sleepy smile."
        )


def tell(setting: Setting, activity: Activity, treat_cfg: Treat, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"traits": hero_traits}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    treat = world.add(Entity(id=treat_cfg.id, type=treat_cfg.type, label=treat_cfg.label, phrase=treat_cfg.phrase, owner=hero.id))

    intro = f"{hero.id} was a small {hero_traits[0]} {hero.type}."
    world.say(intro)
    set_scene(world, setting, activity)
    world.para()
    desire(world, hero, activity)
    warning(world, parent, hero, activity, treat)
    plea_for_mercy(world, hero, parent)
    reserve_turn(world, parent, treat)
    world.para()
    comfort = compromise(world, parent, hero, activity, treat)
    if comfort:
        accept(world, hero, parent, activity, treat, comfort)
    world.facts.update(hero=hero, parent=parent, treat=treat, activity=activity, comfort=comfort, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    activity = _safe_fact(world, f, "activity")
    treat = _safe_fact(world, f, "treat")
    return [
        f"Write a bedtime story in the kitchen where {hero.id} keeps asking, 'one more, one more,' and a parent finds a gentle compromise.",
        f"Tell a cozy story using the words gamut, mercy, and reserve, where {hero.id} wants to {activity.verb} but bedtime is near.",
        f"Write a short bedtime tale with dialogue and repetition about a small child, a treat, and a calm reserve jar in the kitchen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    activity = _safe_fact(world, f, "activity")
    treat = _safe_fact(world, f, "treat")
    comfort = _safe_fact(world, f, "comfort")
    return [
        QAItem(
            question=f"Why did {hero.id} ask for mercy in the kitchen?",
            answer=f"{hero.id} asked for mercy because {hero.pronoun('subject')} wanted one more {activity.verb} before bed, but {parent.id} was trying to keep bedtime calm.",
        ),
        QAItem(
            question=f"What was in the reserve jar?",
            answer=f"The reserve jar held {treat.phrase}, and {parent.id} saved it for a gentle bedtime moment.",
        ),
        QAItem(
            question=f"How did {parent.id} answer {hero.id}'s repeated 'one more, one more'?",
            answer=f"{parent.id} answered with a calm rule and then offered {comfort.label if comfort else 'a gentle compromise'}, so the story could end softly instead of in a fuss.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{hero.id} accepted the bedtime compromise, and the kitchen ended quiet, cozy, and ready for sleep.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reserve?",
            answer="A reserve is a saved supply kept for later, like a treat put aside for a special time.",
        ),
        QAItem(
            question="What does mercy mean?",
            answer="Mercy means kindness when someone has made a mistake or is asking for one more chance.",
        ),
        QAItem(
            question="What is a gamut?",
            answer="A gamut is a whole range of things from one end to the other.",
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
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="snack", treat="cookie", name="Mia", gender="girl", parent="mother", trait="sleepy"),
    StoryParams(place="kitchen", activity="cocoa", treat="cocoa", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="kitchen", activity="tea", treat="tea", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for treat_id, treat in TREATS.items():
                if prize_at_risk(act, treat) and select_comfort(act, treat):
                    combos.append((place, act_id, treat_id))
    return combos


def explain_rejection_combo(activity: Activity, treat: Treat) -> str:
    return f"(No story: {activity.gerund} does not lead to a reasonable bedtime worry for {treat.phrase}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime kitchen storyworld with repetition and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treat", choices=TREATS)
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
    if getattr(args, "activity", None) and getattr(args, "treat", None):
        act, treat = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(TREATS, getattr(args, "treat", None))
        if not (prize_at_risk(act, treat) and select_comfort(act, treat)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "treat", None) is None or c[2] == getattr(args, "treat", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, treat_id = rng.choice(list(combos))
    treat = _safe_lookup(TREATS, treat_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, treat=treat_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(TREATS, params.treat), params.name, params.gender, [params.trait], params.parent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
place(kitchen).
affords(kitchen,snack).
affords(kitchen,cocoa).
affords(kitchen,tea).

activity(snack). mess_of(snack,crumbs). splashes(snack,mouth).
activity(cocoa). mess_of(cocoa,spills). splashes(cocoa,hands). splashes(cocoa,shirt).
activity(tea). mess_of(tea,spills). splashes(tea,hands). splashes(tea,shirt).

treat(cookie). worn_on(cookie,mouth).
treat(cocoa). worn_on(cocoa,sleep).
treat(tea). worn_on(tea,sleep).

gear(brushing). guards(brushing,crumbs). protects(brushing,mouth).
gear(reserve_cookie). guards(reserve_cookie,crumbs). protects(reserve_cookie,mouth).
gear(tiny_sip). guards(tiny_sip,spills). protects(tiny_sip,sleep).

prize_at_risk(A,T) :- activity(A), treat(T), splashes(A,R), worn_on(T,R).
has_fix(A,T) :- prize_at_risk(A,T), mess_of(A,M), guards(G,M), protects(G,Need), worn_on(T,Need).
valid(P,A,T) :- place(P), affords(P,A), prize_at_risk(A,T), has_fix(A,T).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([asp.fact("place", "kitchen"), asp.fact("affords", "kitchen", "snack"), asp.fact("affords", "kitchen", "cocoa"), asp.fact("affords", "kitchen", "tea")])


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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
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
            header = f"### {p.name}: {p.activity} in the kitchen (treat: {p.treat})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
