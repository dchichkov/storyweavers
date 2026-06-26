#!/usr/bin/env python3
"""
storyworlds/worlds/oar_gunk_dim_reconciliation_friendship_lesson_learned.py
============================================================================

A small superhero storyworld about a dim, gunky harbor rescue where an oar,
friendship, and reconciliation turn a tense moment into a lesson learned.

Seed premise:
---
A young superhero and a best friend patrol a foggy harbor at gunk-dim. They
find a stuck skiff, a slippery oar, and a misunderstanding that makes the
friends argue just when they need each other most. After the rescue, they make
up, learn to trust each other, and carry the oar home together.

Core beats:
---
setup:      hero + friend + harbor + oar + gunk-dim
tension:    a snag, a spill of gunk, and a mistaken blame
turn:       the hero apologizes and the friend helps with a steady oar
resolution: they rescue the skiff, reconcile, and learn a lesson about teamwork

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- typed entities with physical meters and emotional memes
- generated prose driven by simulated state
- reasonableness gate and inline ASP twin
- QA sets and trace support
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
    kind: str = "thing"
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
    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str
    dim: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_gunk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("gunk", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.worn_by != actor.id:
                continue
            if item.region not in world.zone:
                continue
            if ("gunk", item.id) in world.fired:
                continue
            world.fired.add(("gunk", item.id))
            item.meters["gunk"] = item.meters.get("gunk", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.id}'s {item.label} got gunky in the dim harbor spray.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["work"] = carer.meters.get("work", 0.0) + 1
        out.append(f"That would mean more cleanup for {carer.label}.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes.get("blame", 0.0) >= THRESHOLD and friend.memes.get("hurt", 0.0) >= THRESHOLD:
        sig = ("fight",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
            friend.memes["conflict"] = friend.memes.get("conflict", 0.0) + 1
            return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_gunk, _r_work, _r_misunderstanding):
            out = rule(world)
            if out:
                changed = True
                produced.extend(s for s in out if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone and activity.id in setting.affords


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def predict_mess(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get("hero"), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "dirty": prize.meters.get("dirty", 0.0) >= THRESHOLD,
        "work": sim.get("friend").meters.get("work", 0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["energy"] = actor.memes.get("energy", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a little superhero with a bright cape, and {friend.id} was "
        f"{hero.pronoun('possessive')} best friend on patrol."
    )
    world.say(
        f"Together they loved the harbor, because even at gunk-dim it could still glow with small brave jobs."
    )


def setup_item(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like a promise, and the oar leaned nearby against the dock."
    )


def arrive(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(
        f"One gunk-dim evening, {hero.id} and {friend.id} went to {world.setting.place}."
    )
    world.say(
        f"The water looked dim and green, and a little skiff rocked by itself near the pilings."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away."
    )


def warn(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["dirty"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_work"] = pred["work"]
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {friend.id} said.'
    )
    return True


def blame_spill(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["blame"] = hero.memes.get("blame", 0.0) + 1
    friend.memes["hurt"] = friend.memes.get("hurt", 0.0) + 1
    world.say(
        f"{hero.id} thought {friend.id} had caused the mess, and that made the air feel sharp."
    )
    world.say(
        f"{hero.id} rushed forward, but the slick dock made the oar slip from {hero.pronoun('possessive')} hands."
    )


def apology(world: World, hero: Entity, friend: Entity) -> None:
    if hero.memes.get("conflict", 0.0) < THRESHOLD and friend.memes.get("hurt", 0.0) < THRESHOLD:
        return
    hero.memes["reconciliation"] = hero.memes.get("reconciliation", 0.0) + 1
    friend.memes["reconciliation"] = friend.memes.get("reconciliation", 0.0) + 1
    hero.memes["blame"] = 0.0
    friend.memes["hurt"] = 0.0
    hero.memes["conflict"] = 0.0
    friend.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} took a breath and said sorry to {friend.id}."
    )
    world.say(
        f"{friend.id} nodded, and just like that the friendship felt stronger than the gunk-dim gloom."
    )


def rescue(world: World, hero: Entity, friend: Entity, activity: Activity, gear: Gear, prize: Entity) -> None:
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
    friend.memes["teamwork"] = friend.memes.get("teamwork", 0.0) + 1
    world.say(
        f"{friend.id} picked up the oar and steadied the skiff while {hero.id} cleared the way."
    )
    world.say(
        f"They worked together, and soon the boat was free."
    )
    world.say(
        f"Then they used {gear.label} to keep {prize.it()} safe, so {hero.id} could still {activity.verb} without ruining it."
    )
    world.say(
        f"At the end, {hero.id} and {friend.id} carried the oar home side by side, smiling like the night had turned bright."
    )


def lesson(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["lesson"] = hero.memes.get("lesson", 0.0) + 1
    friend.memes["lesson"] = friend.memes.get("lesson", 0.0) + 1
    world.say(
        f"{hero.id} learned that a quick apology can open the door to help."
    )
    world.say(
        f"{friend.id} learned that real friends can fix mistakes together, even when the harbor is dim and messy."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="boy", label=hero_name))
    friend = world.add(Entity(id="friend", kind="character", type="girl", label=friend_name))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=friend.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    intro(world, hero, friend)
    setup_item(world, hero, prize)
    world.para()
    arrive(world, hero, friend, activity)
    wants(world, hero, activity)
    warn(world, friend, hero, activity, prize)
    blame_spill(world, hero, friend)
    world.para()
    apology(world, hero, friend)
    gear = select_gear(activity, prize)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    rescue(world, hero, friend, activity, gear, prize)
    lesson(world, hero, friend)
    world.facts.update(hero=hero, friend=friend, prize=prize, activity=activity, gear=gear)
    return world


SETTINGS = {
    "harbor": Setting(place="the harbor", dim="gunk-dim", affords={"oar"}),
}

ACTIVITIES = {
    "oar": Activity(
        id="oar",
        verb="row the skiff with the oar",
        gerund="rowing with the oar",
        rush="grab the oar and push off",
        mess="gunk",
        soil="gunk-dim and sticky",
        zone={"hands", "arms"},
        keyword="oar",
        tags={"oar", "gunk-dim", "friendship"},
    )
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright blue cape", type="cape", region="torso"),
    "gloves": Prize(label="gloves", phrase="clean hero gloves", type="gloves", region="hands", plural=True),
}

GEAR = [
    Gear(
        id="grips",
        label="rubber grip wraps",
        covers={"hands"},
        guards={"gunk"},
        prep="wrap up the hands",
        tail="wrapped their hands for the last stretch",
    ),
    Gear(
        id="towel",
        label="a drying towel",
        covers={"torso", "hands"},
        guards={"gunk"},
        prep="use a drying towel first",
        tail="finished with the drying towel",
    ),
]

HERO_NAMES = ["Nova", "Sky", "Milo", "Jett", "Aria", "Piper"]
FRIEND_NAMES = ["Ruby", "June", "Tess", "Bea", "Mara", "Luna"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    friend_name: str
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
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if reasonableness_gate(setting, act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


KNOWLEDGE = {
    "oar": [("What is an oar?", "An oar is a long tool used to push water and move a boat.")],
    "gunk-dim": [("What does gunk-dim mean?", "Gunk-dim means the light is low and the place feels murky or a little dirty.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other, help each other, and stay kind after mistakes.")],
    "reconciliation": [("What is reconciliation?", "Reconciliation is when people make up after a disagreement and feel close again.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is a helpful idea someone understands after an experience.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a superhero story about a gunk-dim harbor, an oar, and two friends who make up.',
        f"Tell a child-friendly superhero story where {f['hero'].label} and {f['friend'].label} argue, then reconcile, while using an oar at the harbor.",
        'Write a short story that includes the words "oar" and "gunk-dim" and ends with a lesson learned about friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, activity = f["hero"], f["friend"], f["prize"], f["activity"]
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who went to the harbor at gunk-dim?",
            answer=f"{hero.label} the superhero and {friend.label} the friend went to the harbor together.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do with the oar?",
            answer=f"{hero.label} wanted to {activity.verb}, but the harbor was slippery and messy.",
        ),
        QAItem(
            question=f"What happened to the friendship after they talked?",
            answer=f"They apologized, made up, and their friendship felt stronger.",
        ),
        QAItem(
            question=f"How did the {prize.label} stay safe?",
            answer=f"They used {gear.label} so the {prize.label} would not get ruined while {hero.label} kept going.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{hero.label} learned that a quick apology and teamwork can fix a problem and help friends work together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["oar", "gunk-dim", "friendship", "reconciliation", "lesson"]:
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.kind:9} {e.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", activity="oar", prize="cape", hero_name="Nova", friend_name="Ruby"),
    StoryParams(place="harbor", activity="oar", prize="gloves", hero_name="Sky", friend_name="June"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not plausibly threaten a {prize.label} in this world.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("dim", sid, s.dim))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


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
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about gunk-dim friendship and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, hero_name=hero_name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.hero_name, params.friend_name)
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
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:8} {act:8} {prize:8}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
