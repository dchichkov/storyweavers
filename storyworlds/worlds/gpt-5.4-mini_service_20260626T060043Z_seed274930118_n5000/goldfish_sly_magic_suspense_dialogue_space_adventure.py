#!/usr/bin/env python3
"""
A standalone story world for a tiny space-adventure tale:
a sly goldfish, a little magic, a suspenseful problem, and dialogue
that drives the turn and resolution.

This world models a small child-facing premise:
- a goldfish wants to explore space beyond its tank
- a careful/sly helper knows a magical way to do it safely
- suspense comes from a missing key/door/route in the ship
- dialogue resolves the problem with a clever plan

The world is intentionally small and constraint-checked so every
generated sample reads like a complete story rather than a template.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    protective: bool = False
    covers: set[str] = field(default_factory=set)

    region: object | None = None
    gear: object | None = None
    helper: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str
    background: str
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
    risk: str
    consequence: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    offer: str
    ending: str
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for activity_key in world.facts.get("active_tags", set()):
            if actor.meters.get(activity_key, 0.0) < THRESHOLD:
                continue
            sig = ("spark", actor.id, activity_key)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["wonder"] = actor.memes.get("wonder", 0.0) + 1
            out.append(f"A tiny spark of magic shimmered around {actor.id}.")
    return out


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("magic", 0.0) < THRESHOLD and actor.meters.get("suspense", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.location not in world.zone:
                continue
            if world.covered(actor, item.location):
                continue
            sig = ("soil", item.id, actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirt"] = item.meters.get("dirt", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got smudged.")
    return out


CAUSAL_RULES = [Rule("spark", _r_spark), Rule("soil", _r_soil)]


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


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return prize.meters.get("dirt", 0.0) >= THRESHOLD


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.id] = actor.meters.get(activity.id, 0.0) + 1
    actor.meters[activity.keyword] = actor.meters.get(activity.keyword, 0.0) + 1
    actor.memes["want"] = actor.memes.get("want", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_line(setting: Setting) -> str:
    return setting.background


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a sly grin, and {helper.id} knew every quiet corner of the ship."
    )


def desire(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} and dreamed about the stars beyond the glass dome."
    )


def setup_item(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(
        f"{parent.label} had given {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} proudly."
    )


def arrive(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    world.say(
        f"One evening, {hero.id} and {helper.id} slipped into {world.setting.place}, where {setting_line(world.setting)}."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the way ahead looked tricky."
    )


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    if not predict_risk(world, hero, activity, prize.id):
        return False
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.facts["risk"] = True
    world.say(
        f'"If we rush in now, your {prize.label} could get {activity.risk}," said {helper.id}.'
    )
    return True


def search(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    world.say(
        f"They peered through the dim tunnel, and for a moment {hero.id} could only hear the ship hum."
    )
    world.say(
        f'"Where is the path?" whispered {hero.id}. "And why does it feel so quiet?"'
    )


def reveal(world: World, helper: Entity, activity: Activity) -> None:
    world.say(
        f'{helper.id} gave a sly little smile. "I hid the star-key so we would have to use magic instead," {helper.id} said.'
    )


def offer_gear(world: World, helper: Entity, hero: Entity, prize: Entity, gear_def: Gear) -> Optional[Gear]:
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        owner=hero.id,
    ))
    gear.worn_by = hero.id
    if predict_risk(world, hero, world.facts["activity"], prize.id):
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'"Then put this on," said {helper.id}. "It will keep your {prize.label} safe while you {world.facts["activity"].verb}."'
    )
    return gear


def resolve(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["suspense"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f'{hero.id} nodded. "That is clever," {hero.id} said. "I can do that!"'
    )
    world.say(
        f"They used the {gear_def.label}, and soon {hero.id} was {activity.gerund}, while {prize.label} stayed bright and clean."
    )
    world.say(
        f"The ship lights glowed softly, and {hero.id} swam forward like a tiny captain among the stars."
    )


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id in gear.guards and prize.region in gear.covers:
            return gear
    return None


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone and select_gear(activity, prize) is not None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="goldfish", traits=["little", "sly"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="child", label="the friend"))
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label="the caretaker"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=parent.id,
        owner=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    world.facts.update(activity=activity, prize=prize, hero=hero, helper=helper, parent=parent, active_tags=set(activity.tags))
    introduce(world, hero, helper)
    desire(world, hero, activity)
    setup_item(world, parent, hero, prize)

    world.para()
    arrive(world, hero, helper, activity)
    warn(world, helper, hero, activity, prize)
    search(world, hero, helper, activity)
    reveal(world, helper, activity)

    world.para()
    gear_def = select_gear(activity, prize)
    if gear_def is not None:
        gear = offer_gear(world, helper, hero, prize, gear_def)
        if gear is not None:
            resolve(world, hero, helper, activity, prize, gear_def)
            world.facts["gear"] = gear_def
            world.facts["resolved"] = True
        else:
            world.facts["gear"] = None
            world.facts["resolved"] = False
    else:
        world.facts["gear"] = None
        world.facts["resolved"] = False

    return world


SETTINGS = {
    "dock": Setting(
        place="the moon dock",
        background="a silver hatch opened onto a floating tunnel of stars",
        affords={"glow", "drift", "spell"},
    ),
    "tankship": Setting(
        place="the tankship",
        background="the walls were clear glass, and little lights blinked like faraway moons",
        affords={"glow", "drift", "spell"},
    ),
    "observatory": Setting(
        place="the observatory bubble",
        background="the telescope spun slowly while the ceiling showed a tiny galaxy map",
        affords={"glow", "drift", "spell"},
    ),
}

ACTIVITIES = {
    "glow": Activity(
        id="glow",
        verb="follow the glowing trail",
        gerund="gliding through glowing water",
        rush="dart toward the glow",
        risk="lost in the dark",
        consequence="the trail would disappear",
        zone={"head", "body"},
        keyword="magic",
        tags={"magic"},
    ),
    "drift": Activity(
        id="drift",
        verb="drift through the tunnel",
        gerund="drifting through the tunnel",
        rush="swim after the moving current",
        risk="scuffed by the metal wall",
        consequence="the current would bump the tank",
        zone={"body"},
        keyword="suspense",
        tags={"suspense"},
    ),
    "spell": Activity(
        id="spell",
        verb="cast the bubble spell",
        gerund="spinning in a bubble of magic",
        rush="swirl toward the bubble spell",
        risk="popped by a sharp edge",
        consequence="the bubble would burst",
        zone={"head", "body"},
        keyword="dialogue",
        tags={"magic", "dialogue"},
    ),
}

PRIZES = {
    "cape": Prize(
        label="cape",
        phrase="a small silver cape",
        type="cape",
        region="body",
    ),
    "helmet": Prize(
        label="helmet",
        phrase="a tiny clear helmet",
        type="helmet",
        region="head",
    ),
    "finwrap": Prize(
        label="fin wrap",
        phrase="a sparkly fin wrap",
        type="finwrap",
        region="body",
    ),
}

GEAR = [
    Gear(
        id="moonbubble",
        label="a moon-bubble",
        covers={"head", "body"},
        guards={"glow", "spell"},
        offer='put on a moon-bubble first',
        ending="floated on the moon-bubble",
    ),
    Gear(
        id="starglass",
        label="starglass goggles",
        covers={"head"},
        guards={"glow", "drift"},
        offer='wear starglass goggles first',
        ending="wore the starglass goggles",
        plural=True,
    ),
    Gear(
        id="softshell",
        label="a soft shell suit",
        covers={"body"},
        guards={"drift", "spell"},
        offer='wear a soft shell suit first',
        ending="slipped into the soft shell suit",
    ),
]

GOLDISH_NAMES = ["Bloop", "Coral", "Milo", "Nori", "Peep", "Tansy"]
HELPER_NAMES = ["Pip", "Nova", "Juno", "Kite", "Mina", "Toby"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    helper: str
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
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            activity = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if reasonableness_gate(activity, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space-adventure story for a small child about a {f["hero"].type} named {f["hero"].id} and the word "{f["activity"].keyword}".',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb}, but a sly helper notices a problem and speaks up.",
        f'Write a suspenseful but cozy story in a spaceship with magic, dialogue, and a safe ending that includes a "{f["prize"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who wanted to {activity.verb} in the story?",
            answer=f"It was {hero.id}, the little sly goldfish.",
        ),
        QAItem(
            question=f"What did the helper warn might happen to the {prize.label}?",
            answer=f"The helper warned that the {prize.label} could get {activity.risk}.",
        ),
        QAItem(
            question=f"How did the characters solve the problem?",
            answer=(
                f"They used {gear.label if gear else 'a safe plan'} so {hero.id} could keep going without ruining the {prize.label}."
            ),
        ),
        QAItem(
            question=f"What did {helper.id} do that made the story feel suspenseful?",
            answer=f"{helper.id} spoke up about the hidden risk and led the way through the quiet ship.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"What changed at the end of the story?",
                answer=f"{hero.id} was still exploring, but now the {prize.label} stayed clean and the ship felt friendly again.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a goldfish?",
            answer="A goldfish is a small fish that lives in water and can swim with quick flicks of its fins.",
        ),
        QAItem(
            question="What does sly mean?",
            answer="Sly means clever in a sneaky or tricky way, like someone who notices things and plans ahead.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special story power that can make surprising things happen, like glowing water or floating bubbles.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what will happen next when a problem is not solved yet.",
        ),
        QAItem(
            question="Why do characters talk to each other in stories?",
            answer="Characters talk to each other so they can share worries, make plans, and solve problems together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protected(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, A), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), protected(_, A, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a sly goldfish, magic, suspense, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    if getattr(args, "place", None) or getattr(args, "activity", None) or getattr(args, "prize", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
            and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        hero=getattr(args, "hero", None) or rng.choice(GOLDISH_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.hero, params.helper)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("dock", "glow", "helmet", "Bloop", "Nova"),
            StoryParams("tankship", "spell", "cape", "Coral", "Pip"),
            StoryParams("observatory", "drift", "finwrap", "Nori", "Juno"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
