#!/usr/bin/env python3
"""
A standalone storyworld for a small folk-tale domain about tranquility,
a condiment, sharing, rhyme, and a lesson learned.

The world is built from a simple seed-tale premise:
- A calm child or villager wants a tasty condiment.
- Another character fears there is not enough to share.
- A rhyme helps them pause, share, and learn a gentle lesson.
- The ending image proves the world changed: calm returned, and the jar is still enough.

This script follows the Storyweavers world contract.
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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid: object | None = None
    cond: object | None = None
    hero: object | None = None
    other: object | None = None
    def __post_init__(self) -> None:
        for k in ("full", "empty", "shared", "safe", "used", "spilled"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
    place: str = "the village green"
    indoor: bool = False
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
    weather: str
    keyword: str = ""
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
class Condiment:
    label: str
    phrase: str
    type: str
    taste: str
    size: str
    generous: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["sharing"] < THRESHOLD:
            continue
        jar = next((e for e in world.entities.values() if e.type == "condiment" and e.owner == actor.id), None)
        if not jar:
            continue
        sig = ("share", actor.id, jar.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        jar.meters["shared"] += 1
        actor.memes["tranquility"] += 1
        out.append(f"The {jar.label} was shared kindly.")
    return out


def _r_tranquility(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD:
            continue
        shared = any(e.type == "condiment" and e.meters["shared"] >= THRESHOLD for e in world.entities.values())
        sig = ("tranquility", actor.id)
        if sig in world.fired or not shared:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = 0.0
        actor.memes["tranquility"] += 1
        out.append(f"{actor.id} felt calm again.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["lesson"] >= THRESHOLD:
            continue
        if actor.meters["shared"] < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["lesson"] += 1
        out.append(f"{actor.id} learned that sharing can make a small thing last.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("share", "social", _r_share),
    Rule("tranquility", "emotional", _r_tranquility),
    Rule("lesson", "emotional", _r_lesson),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    actor.meters["used"] += 1
    actor.memes["joy"] += 1
    if activity.id == "spill":
        actor.meters["spilled"] += 1
    propagate(world, narrate=narrate)


def predict_story(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    jar = next((e for e in sim.entities.values() if e.type == "condiment"), None)
    return {
        "shared": bool(jar and jar.meters["shared"] >= THRESHOLD),
        "lesson": any(e.memes["lesson"] >= THRESHOLD for e in sim.characters()),
    }


def rhyme_line(activity: Activity, condiment: Condiment) -> str:
    return {
        "honey": "A spoon in the bowl makes the whole day sweet and full.",
        "salt": "A pinch of salt can lift a soup from small to bright and bold.",
        "jam": "A little jam makes bread sing like a warm and cheerful drum.",
    }.get(condiment.type, f"A little {condiment.label} can turn plain bread into a feast.")


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and a little table waited by the hearth."
    return f"{setting.place.capitalize()} was still and bright, like it was holding its breath."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved calm mornings.")


def love_condiment(world: World, hero: Entity, cond: Entity) -> None:
    hero.memes["love"] += 1
    cond.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {cond.label} and carried it carefully.")


def arrive(world: World, hero: Entity) -> None:
    where = "inside" if world.setting.indoor else "outside"
    world.say(f"One day, {hero.id} went {where} to {world.setting.place}.")
    world.say(setting_detail(world.setting))


def want_spread(world: World, hero: Entity, activity: Activity, cond: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} "
        f"{cond.label} was too special to waste."
    )


def worry_and_pause(world: World, hero: Entity, other: Entity, cond: Entity, activity: Activity) -> None:
    other.memes["worry"] += 1
    world.say(
        f"{other.id} frowned and said, \"If we use too much, there may be none left.\""
    )
    world.say(
        f"{hero.id} looked at the jar, then at {other.id}, and paused."
    )


def share_and_rhyme(world: World, hero: Entity, other: Entity, cond: Entity, aid: Aid, activity: Activity) -> None:
    hero.memes["sharing"] += 1
    other.memes["sharing"] += 1
    cond.meters["shared"] += 1
    world.say(
        f"Then {hero.id} smiled. \"We can share it,\" {hero.pronoun()} said, and {aid.prep}."
    )
    world.say(
        f"{hero.id} and {other.id} took tiny turns. {rhyme_line(activity, world.facts['condiment_cfg'])}"
    )
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, other: Entity, cond: Entity, activity: Activity) -> None:
    if hero.memes["lesson"] >= THRESHOLD or other.memes["lesson"] >= THRESHOLD:
        world.say(
            f"In the end, the jar was not empty at all. {hero.id} and {other.id} sat in quiet happiness, "
            f"and the little {cond.label} lasted because they had shared it."
        )


SETTINGS = {
    "village": Setting(place="the village green", indoor=False, affords={"share", "rhyme"}),
    "hearth": Setting(place="the hearth room", indoor=True, affords={"share", "rhyme"}),
    "orchard": Setting(place="the orchard path", indoor=False, affords={"share", "rhyme"}),
}

ACTIVITIES = {
    "share": Activity(
        id="share",
        verb="share the condiment",
        gerund="sharing the condiment",
        rush="grab the spoon",
        mess="smeared",
        soil="smeared on the cloth",
        zone={"hands"},
        weather="",
        keyword="sharing",
        tags={"share", "sharing", "lesson"},
    ),
    "rhyme": Activity(
        id="rhyme",
        verb="say a rhyme",
        gerund="singing a rhyme",
        rush="start the tune",
        mess="sung",
        soil="full of song",
        zone={"mouth"},
        weather="",
        keyword="rhyme",
        tags={"rhyme"},
    ),
}

CONDIMENTS = {
    "honey": Condiment(label="honey jar", phrase="a golden jar of honey", type="honey", taste="sweet", size="small"),
    "salt": Condiment(label="salt bowl", phrase="a little bowl of salt", type="salt", taste="sharp", size="small"),
    "jam": Condiment(label="jam pot", phrase="a bright pot of jam", type="jam", taste="fruity", size="small"),
}

AIDS = {
    "spoon": Aid(id="spoon", label="little spoon", prep="took turns with a little spoon", tail="used the little spoon together", helps={"share"}),
}

GIRL_NAMES = ["Mira", "Lina", "Tala", "Nina", "Pia"]
BOY_NAMES = ["Ravi", "Oren", "Milo", "Jon", "Eli"]
TRAITS = ["gentle", "curious", "cheerful", "patient", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    condiment: str
    name: str
    gender: str
    other: str
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
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for cond in CONDIMENTS:
                combos.append((place, act, cond))
    return combos


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    world.weather = ""

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    other = world.add(Entity(id=params.other, kind="character", type="person", label="neighbor"))
    cond_cfg = _safe_lookup(CONDIMENTS, params.condiment)
    cond = world.add(Entity(id="condiment", type="condiment", label=cond_cfg.label, phrase=cond_cfg.phrase, owner=hero.id))
    aid = world.add(Entity(id="aid", type="aid", label=AIDS["spoon"].label))

    world.facts.update(hero=hero, other=other, condiment=cond, condiment_cfg=cond_cfg, activity=_safe_lookup(ACTIVITIES, params.activity), aid=aid)

    introduce(world, hero)
    love_condiment(world, hero, cond)
    world.para()
    arrive(world, hero)
    want_spread(world, hero, _safe_lookup(ACTIVITIES, params.activity), cond)
    worry_and_pause(world, hero, other, cond, _safe_lookup(ACTIVITIES, params.activity))
    world.para()
    share_and_rhyme(world, hero, other, cond, AIDS["spoon"], _safe_lookup(ACTIVITIES, params.activity))
    ending(world, hero, other, cond, _safe_lookup(ACTIVITIES, params.activity))
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    other = _safe_fact(world, f, "other")
    act = _safe_fact(world, f, "activity")
    cond = _safe_fact(world, f, "condiment_cfg")
    return [
        f'Write a folk tale for a young child about {hero.id}, {other.id}, and a shared {cond.label}.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} and learns a lesson about sharing.",
        f'Write a rhyme-filled story that includes the word "tranquility" and ends with a calm table.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    other = _safe_fact(world, f, "other")
    cond = _safe_fact(world, f, "condiment_cfg")
    act = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"Who learned a lesson about sharing in the story?",
            answer=f"{hero.id} learned that sharing can make a small thing last, and {other.id} learned it too.",
        ),
        QAItem(
            question=f"What condiment did {hero.id} carry carefully?",
            answer=f"{hero.id} carried {cond.phrase} carefully.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before the two friends shared?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What kind of ending did the story have?",
            answer=f"It ended with calm sharing, a little rhyme, and a lesson learned.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    cond = _safe_fact(world, world.facts, "condiment_cfg")
    return [
        QAItem(
            question="What is a condiment?",
            answer="A condiment is a little extra food, like honey, salt, or jam, that people add to make other food taste better.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person enjoy the same thing, taking turns, or giving some to someone else.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words or lines that sound alike at the end, like a song or chant.",
        ),
        QAItem(
            question="What does tranquility mean?",
            answer="Tranquility means a quiet and peaceful feeling, when no one is rushing or quarreling.",
        ),
        QAItem(
            question=f"What sort of taste does {cond.label} usually have?",
            answer=f"{cond.label.capitalize()} usually tastes {cond.taste}.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village", activity="share", condiment="honey", name="Mira", gender="girl", other="Shit", trait="gentle"),
    StoryParams(place="hearth", activity="rhyme", condiment="jam", name="Ravi", gender="boy", other="Nori", trait="thoughtful"),
]


def explain_rejection() -> str:
    return "(No story: this world needs a setting that allows sharing and rhyme.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None)) and (getattr(args, "condiment", None) is None or c[2] == getattr(args, "condiment", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, condiment = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    other = "Shit" if getattr(args, "other", None) is None else getattr(args, "other", None)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, condiment=condiment, name=name, gender=gender, other=other, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld about tranquility, condiment sharing, rhyme, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--condiment", choices=CONDIMENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--other")
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


ASP_RULES = r"""
valid(P,A,C) :- setting(P), activity(A), condiment(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in _safe_lookup(SETTINGS, p).affords:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for c in CONDIMENTS:
        lines.append(asp.fact("condiment", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
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
