#!/usr/bin/env python3
"""
storyworlds/worlds/embroidery_quest_myth.py
===========================================

A small myth-styled story world about an embroidery quest:
a young maker, a cherished cloth, a simple wound, and a wise repair.

The premise is deliberately classical and constraint-checked:
someone wants to finish a sacred embroidery, but a flaw in the cloth or thread
threatens the work. A helper, tool, or rite offers a reasonable fix, and the
world model drives the prose.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "order": 0.0, "finished": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "dread": 0.0, "pride": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen", "priestess"}
        male = {"boy", "man", "father", "king", "priest"}
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
class Place:
    name: str
    setting: str
    affords: set[str] = field(default_factory=set)
    sacred: bool = False
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
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    damage: str
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
    worn: bool = False
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
    guards: set[str]
    covers: set[str]
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        w.lines = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    hero: str
    hero_type: str
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


PLACES = {
    "temple_yard": Place("the temple yard", "mythic courtyard", affords={"stitch", "dye", "loom"}, sacred=True),
    "moon_hall": Place("the moon hall", "silver chamber", affords={"stitch", "mend"}, sacred=True),
    "river_bank": Place("the river bank", "windy shore", affords={"stitch", "wash", "dye"}),
}

TASKS = {
    "embroidery": Task(
        id="embroidery",
        verb="embroider the sacred cloth",
        gerund="embroidering the sacred cloth",
        risk="fray",
        damage="frayed and loosened",
        zone={"cloth"},
        keyword="embroidery",
        tags={"thread", "cloth", "needle"},
    ),
    "gold_thread": Task(
        id="gold_thread",
        verb="stitch the golden border",
        gerund="stitching the golden border",
        risk="snap",
        damage="snapped and dull",
        zone={"cloth"},
        keyword="gold thread",
        tags={"thread", "gold"},
    ),
    "banner": Task(
        id="banner",
        verb="finish the banner of the house",
        gerund="finishing the banner",
        risk="tear",
        damage="torn at the edge",
        zone={"banner"},
        keyword="banner",
        tags={"cloth", "house"},
    ),
}

PRIZES = {
    "cloak": Prize("cloak", "a bright cloak of ceremony", "cloak", "body"),
    "banner": Prize("banner", "a long temple banner", "banner", "cloth"),
    "veil": Prize("veil", "a thin veil for the rite", "veil", "cloth"),
}

GEAR = [
    Gear(
        id="wax",
        label="beeswax",
        guards={"snap", "fray"},
        covers={"thread", "cloth"},
        prep="rub the thread with beeswax first",
        tail="rubbed the thread with beeswax",
    ),
    Gear(
        id="hoop",
        label="a carved hoop",
        guards={"fray", "tear"},
        covers={"cloth"},
        prep="stretch the cloth in a carved hoop",
        tail="held the cloth in a carved hoop",
    ),
    Gear(
        id="patch",
        label="a gold patch",
        guards={"tear"},
        covers={"cloth"},
        prep="set a gold patch over the torn place",
        tail="set the gold patch over the torn place",
    ),
]


GIRL_NAMES = ["Alya", "Nera", "Mira", "Sana", "Ila", "Tessa"]
BOY_NAMES = ["Orin", "Kian", "Pavel", "Rian", "Tomas", "Aren"]
HELPERS = ["mother", "father", "grandmother", "mentor", "priest"]
TITLES = ["brave", "gentle", "patient", "curious", "steadfast", "luminous"]


def at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def select_gear(task: Task, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if task.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p, place in PLACES.items():
        for t, task in TASKS.items():
            if t not in place.affords:
                continue
            for pr, prize in PRIZES.items():
                if at_risk(task, prize) and select_gear(task, prize):
                    out.append((p, t, pr))
    return out


def introduce(world: World, hero: Entity, title: str) -> None:
    world.say(f"In the old days, {hero.id} was a {title} {hero.type} who loved patient work.")


def praise_task(world: World, hero: Entity, task: Task) -> None:
    hero.memes["hope"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {task.gerund}, because each stitch could hold a small wonder together.")


def present_prize(world: World, helper: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"Then {helper.id} brought {hero.pronoun('object')} {prize.phrase}, and the cloth gleamed like a little sky.")


def claim_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    hero.memes["pride"] += 1
    world.say(f"{hero.id} held {hero.pronoun('possessive')} {prize.label} close, as if guarding a vow.")


def approach(world: World, hero: Entity) -> None:
    world.say(f"One dawn they went to {world.place.name}, where the air was still and the stones remembered prayers.")


def want_and_warn(world: World, helper: Entity, hero: Entity, task: Task, prize: Entity) -> bool:
    hero.memes["resolve"] += 1
    world.say(f"{hero.id} wanted to {task.verb}, but {helper.id} looked at {prize.label} with a worried face.")
    sim = world.copy()
    do_task(sim, sim.get(hero.id), task, narrate=False)
    ruined = any(e.meters["damage"] >= THRESHOLD for e in sim.entities.values() if e.id == prize.id)
    if ruined:
        world.facts["predicted_damage"] = task.damage
        world.say(f'"If you do that now, {hero.id}, the {prize.label} will become {task.damage}," {helper.id} said.')
        return True
    return False


def do_task(world: World, hero: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.place.affords:
        pass
    world.zone = set(task.zone)
    hero.meters["order"] += 1
    hero.memes["resolve"] += 1
    for item in world.worn_items(hero):
        if item.protective:
            continue
        if item.region not in task.zone:
            continue
        if any(item.region in g.covers for g in world.worn_items(hero) if g.protective):
            continue
        item.meters["damage"] += 1
        if narrate:
            world.say(f"{hero.id}'s {item.label} began to show the mark of the work.")
    hero.meters["finished"] += 1


def offer_fix(world: World, helper: Entity, hero: Entity, task: Task, prize: Entity) -> Optional[Gear]:
    gear = select_gear(task, prize)
    if gear is None:
        return None
    world.say(f"Then {helper.id} smiled and said, \"First, {gear.prep}.\"")
    obj = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        owner=hero.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    obj.worn_by = hero.id
    sim = world.copy()
    sim.get(hero.id).memes["resolve"] += 1
    do_task(sim, sim.get(hero.id), task, narrate=False)
    sim_prize = sim.get(prize.id)
    if sim_prize.meters["damage"] >= THRESHOLD:
        obj.worn_by = None
        del world.entities[obj.id]
        return None
    return gear


def accept_fix(world: World, hero: Entity, helper: Entity, task: Task, prize: Entity, gear: Gear) -> None:
    hero.memes["hope"] += 1
    hero.memes["dread"] = 0.0
    world.say(f"{hero.id} nodded, and the fear left {hero.pronoun('possessive')} face like mist from a pond.")
    world.say(f"They {gear.tail}, and then {hero.id} could {task.verb} while {prize.label} stayed whole.")
    world.say(f"At the end, the cloth shone brighter than before, as if the wound had become part of the beauty.")


def tell(place: Place, task: Task, prize_cfg: Prize, hero_name: str, hero_type: str, helper_type: str, title: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_type, kind="character", type=helper_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region, plural=prize_cfg.plural))
    introduce(world, hero, title)
    praise_task(world, hero, task)
    present_prize(world, helper, hero, prize)
    claim_prize(world, hero, prize)
    world.para()
    approach(world, hero)
    warned = want_and_warn(world, helper, hero, task, prize)
    gear = offer_fix(world, helper, hero, task, prize) if warned else None
    if gear:
        world.para()
        accept_fix(world, hero, helper, task, prize, gear)
        do_task(world, hero, task, narrate=False)
    world.facts.update(hero=hero, helper=helper, prize=prize, task=task, place=place, gear=gear, warned=warned)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a myth-like story about embroidery, a warning, and a wise fix, using the word "{task.keyword}".',
        f"Tell a small story where {hero.id} wants to {task.verb} but must protect {prize.phrase}.",
        f"Write a gentle quest story about cloth, thread, and a helper who offers a safer way to continue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    task = _safe_fact(world, f, "task")
    prize = _safe_fact(world, f, "prize")
    qs = [
        QAItem(
            question=f"What did {hero.id} want to do on the quest?",
            answer=f"{hero.id} wanted to {task.verb}. That was the heart of the journey.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about {prize.label}?",
            answer=f"{helper.id} worried because the work could leave {prize.label} {task.damage}.",
        ),
        QAItem(
            question=f"What helped {hero.id} continue the work safely?",
            answer=f"A careful tool or covering was offered first, so {hero.id} could keep working without ruining {prize.label}.",
        ),
    ]
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qs.append(QAItem(
            question=f"How did {gear.label} help during the quest?",
            answer=f"{gear.label.capitalize()} protected the right part of the work so the quest could continue in safety.",
        ))
    return qs


WORLD_KNOWLEDGE = {
    "embroidery": (
        "What is embroidery?",
        "Embroidery is making patterns on cloth with needle and thread.",
    ),
    "thread": (
        "What is thread used for?",
        "Thread is used to sew and stitch things together.",
    ),
    "cloth": (
        "What is cloth?",
        "Cloth is woven fabric that can become clothing, banners, or veils.",
    ),
    "needle": (
        "What does a needle do?",
        "A needle is a sharp tool that makes small holes so thread can pass through cloth.",
    ),
    "gold": (
        "Why is gold special in stories?",
        "Gold often stands for something precious, bright, and honored.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out = []
    for k, pair in WORLD_KNOWLEDGE.items():
        if k in tags or k in world.facts["task"].keyword:
            out.append(QAItem(question=pair[0], answer=pair[1]))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(T,P) :- zone(T,R), prize_on(P,R).
fix(G,T,P) :- gear(G), at_risk(T,P), guards(G,M), risk_of(T,M), covers(G,R), prize_on(P,R).
valid(Pe,T,Pr) :- place(Pe), affords(Pe,T), at_risk(T,Pr), fix(_,T,Pr).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("risk_of", tid, t.risk))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("prize_on", prid, pr.region))
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
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic embroidery quest story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("--title", choices=TITLES)
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
    if getattr(args, "task", None) and getattr(args, "prize", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (at_risk(task, prize) and select_gear(task, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPERS)
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    title = getattr(args, "title", None) or rng.choice(TITLES)
    return StoryParams(place=place, task=task, prize=prize, hero=name, hero_type=hero_type, helper=helper_type, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(TASKS, params.task),
        _safe_lookup(PRIZES, params.prize),
        params.hero,
        params.hero_type,
        params.helper,
        "steadfast",
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
    StoryParams("temple_yard", "embroidery", "banner", "Alya", "girl", "mother"),
    StoryParams("moon_hall", "gold_thread", "veil", "Orin", "boy", "mentor"),
    StoryParams("river_bank", "banner", "cloak", "Mira", "girl", "grandmother"),
]


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
        vals = sorted(set(asp.atoms(model, "valid")))
        for item in vals:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.hero}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
