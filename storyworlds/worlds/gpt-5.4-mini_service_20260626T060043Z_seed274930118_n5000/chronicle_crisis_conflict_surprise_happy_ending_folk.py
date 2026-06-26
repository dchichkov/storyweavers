#!/usr/bin/env python3
"""
A small folk-tale storyworld: a village chronicle, a sudden crisis, a surprise
helper, and a happy ending.

The seed words "chronicle" and "crisis" shape the domain: the village keeps a
chronicle book, a crisis interrupts a market day, and the ending turns happy
when the right helper arrives.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chronicle: object | None = None
    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "daughter"}
        male = {"boy", "father", "man", "king", "son"}
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
    place: str = "the village square"
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
    hazard: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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
        self.zone: set[str] = set()
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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.meters.get("covers", set()) for item in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("trouble", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if not world.zone:
                continue
            sig = ("damage", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damaged"] = item.meters.get("damaged", 0.0) + 1
            out.append(f"Their {item.label} was caught in the trouble.")
    return out


def _r_burden(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("damaged", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("burden", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["burden"] = carer.meters.get("burden", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_surprise(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("surprise", 0.0) < THRESHOLD:
            continue
        sig = ("surprise", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
        return ["__surprise__"]
    return []


CAUSAL_RULES = [
    Rule("damage", _r_damage),
    Rule("burden", _r_burden),
    Rule("surprise", _r_surprise),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if x != "__surprise__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def crisis_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.hazard in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"damaged": bool(prize.meters.get("damaged", 0.0) >= THRESHOLD)}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["trouble"] = actor.meters.get("trouble", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "kind")
    world.say(f"{hero.id} was a little {trait} {hero.type} in the village, and {hero.pronoun('subject')} loved listening to old tales.")


def loves_chronicle(world: World, hero: Entity, chronicle: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id} loved the village chronicle, because it kept every brave and silly day safe on its pages.")


def arrives(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(f"The air felt busy, as if the whole square was waiting for a tale to begin.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb} at once, but a sudden hush drifted over the square.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_damage(world, hero, activity, prize.id)
    if not pred["damaged"]:
        return False
    world.facts["predicted_damage"] = True
    world.say(f'"If you do that now, your {prize.label} may be ruined," {parent.label} said.')
    return True


def conflict(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1
    world.say(f"{hero.id} frowned and tried to {activity.rush}, though the warning still rang in {hero.pronoun('possessive')} ears.")


def surprise_helper(world: World, hero: Entity) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say("Then a surprise came with the wind: a small helper from the mill arrived carrying the right kind of gear.")


def offer(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
    ))
    gear.meters["covers"] = gear_def.covers  # used only internally
    gear.worn_by = hero.id
    world.say(f'"How about we {gear_def.prep}?" {parent.label} asked, and the surprise helper nodded.')
    return gear_def


def accept(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    hero.memes["frustration"] = 0.0
    world.say(f"{hero.id}'s face brightened, and {hero.id} hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(f'They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, and {prize.label} stayed safe and sound.')


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mira", hero_type: str = "girl", parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
    ))
    chronicle = world.add(Entity(id="chronicle", type="book", label="chronicle book"))

    introduce(world, hero)
    loves_chronicle(world, hero, chronicle)
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} as carefully as a page in a king's book.")

    world.para()
    arrives(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    conflict(world, hero, activity)
    surprise_helper(world, hero)

    world.para()
    gear_def = offer(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, hero, parent, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        chronicle=chronicle,
        activity=activity,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "square": Setting(place="the village square", affords={"dance", "market", "run"}),
    "bridge": Setting(place="the old bridge", affords={"cross", "run"}),
    "orchard": Setting(place="the orchard lane", affords={"pick", "run"}),
    "mill": Setting(place="the mill yard", affords={"carry", "run"}),
}

ACTIVITIES = {
    "dance": Activity(
        id="dance",
        verb="dance with the bells",
        gerund="dancing with the bells",
        rush="spin toward the bellcart",
        hazard="dusty",
        zone={"torso", "feet"},
        keyword="chronicle",
        tags={"festival", "dust"},
    ),
    "market": Activity(
        id="market",
        verb="help with the market baskets",
        gerund="helping with the market baskets",
        rush="dash to the stalls",
        hazard="muddy",
        zone={"hands", "feet"},
        keyword="crisis",
        tags={"market", "mud"},
    ),
    "run": Activity(
        id="run",
        verb="run through the lane",
        gerund="running through the lane",
        rush="run fast across the square",
        hazard="windy",
        zone={"feet"},
        keyword="wind",
        tags={"wind", "road"},
    ),
    "cross": Activity(
        id="cross",
        verb="cross the bridge",
        gerund="crossing the bridge",
        rush="hurry across the boards",
        hazard="wet",
        zone={"feet"},
        keyword="bridge",
        tags={"water", "bridge"},
    ),
    "pick": Activity(
        id="pick",
        verb="pick apples",
        gerund="picking apples",
        rush="climb toward the low branch",
        hazard="sticky",
        zone={"hands", "torso"},
        keyword="apple",
        tags={"orchard", "fruit"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry bread to the mill",
        gerund="carrying bread to the mill",
        rush="hurry with the basket",
        hazard="crumbly",
        zone={"hands", "torso"},
        keyword="bread",
        tags={"bread", "work"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a bright red cloak", type="cloak", region="torso"),
    "apron": Prize(label="apron", phrase="a clean white apron", type="apron", region="torso"),
    "boots": Prize(label="boots", phrase="soft brown boots", type="boots", region="feet", plural=True),
    "ribbon": Prize(label="ribbon", phrase="a blue ribbon", type="ribbon", region="head"),
    "basket": Prize(label="basket", phrase="a woven basket", type="basket", region="hands"),
}

GEAR = [
    Gear(id="rainboots", label="sturdy rain boots", covers={"feet"}, guards={"wet", "muddy"}, prep="put on the rain boots first", tail="walked on with the rain boots"),
    Gear(id="apronwrap", label="a waxed apron", covers={"torso"}, guards={"sticky", "crumbly", "dusty"}, prep="tie on a waxed apron first", tail="went on with the waxed apron"),
    Gear(id="gloves", label="work gloves", covers={"hands"}, guards={"sticky", "crumbly", "muddy"}, prep="wear work gloves first", tail="carried on with the work gloves"),
    Gear(id="cloakcover", label="a cloak cover", covers={"torso"}, guards={"wet", "windy", "dusty"}, prep="fasten a cloak cover first", tail="went ahead with the cloak cover"),
]

GIRL_NAMES = ["Mira", "Lena", "Anya", "Lila", "Nora", "Sana", "Ivy"]
BOY_NAMES = ["Otto", "Eli", "Nico", "Bram", "Taro", "Pavel", "Milo"]
TRAITS = ["curious", "brave", "cheerful", "stubborn", "gentle", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if crisis_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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


KNOWLEDGE = {
    "chronicle": [("What is a chronicle?", "A chronicle is a record of events written down in order, so people can remember what happened.")],
    "crisis": [("What is a crisis?", "A crisis is a serious problem that needs careful help right away.")],
    "bridge": [("What is a bridge for?", "A bridge helps people cross over water or a gap safely.")],
    "market": [("What is a market?", "A market is a place where people bring things to sell or trade.")],
    "orchard": [("What is an orchard?", "An orchard is a place where fruit trees grow together.")],
    "mill": [("What does a mill do?", "A mill is a place where people turn grain into flour or do other useful work.")],
    "boots": [("What are boots for?", "Boots protect your feet and help keep them dry or clean.")],
    "apron": [("What is an apron for?", "An apron helps keep clothes clean while you work or cook.")],
    "gloves": [("What are gloves for?", "Gloves help protect your hands from dirt, rough things, or cold air.")],
}
KNOWLEDGE_ORDER = ["chronicle", "crisis", "bridge", "market", "orchard", "mill", "boots", "apron", "gloves"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    return [
        f'Write a short folk tale about a child named {hero.id}, a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")}, and the word "{act.keyword}".',
        f"Tell a story where {hero.id} wants to {act.verb}, but {hero.pronoun('possessive')} {parent.label} worries about {hero.pronoun('possessive')} {prize.label}.",
        f"Write a village chronicle story with a crisis, a surprise helper, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "parent"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "activity")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}, and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}, because the day felt full of chance and motion.",
        ),
        QAItem(
            question=f"Why was there a crisis?",
            answer=f"There was a crisis because if {hero.id} did that, the {prize.label} would likely be ruined.",
        ),
    ]
    if f.get("resolved"):
        gear = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gear")
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when they used {gear.label} and {hero.id} got to {act.verb} without ruining the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "activity").tags)
    tags.add("chronicle")
    if world.facts.get("gear"):
        tags.add(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "gear").id)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="square", activity="market", prize="apron", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="bridge", activity="cross", prize="boots", name="Otto", gender="boy", parent="father", trait="brave"),
    StoryParams(place="orchard", activity="pick", prize="cloak", name="Lila", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="mill", activity="carry", prize="basket", name="Eli", gender="boy", parent="father", trait="lively"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} would not honestly threaten the {prize.label} in this world.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s item here.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.hazard))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    ap = argparse.ArgumentParser(description="Folk-tale story world with chronicle, crisis, surprise, and happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (crisis_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
