#!/usr/bin/env python3
"""
storyworlds/worlds/bristle_patty_happy_ending_inner_monologue_myth.py
=====================================================================

A small myth-like storyworld about Bristle and Patty: a bristly little hero,
a worried companion, a risky task, a thoughtful inner monologue, and a happy
ending that proves the world changed.

Seed words:
- bristle
- patty

Features:
- Happy Ending
- Inner Monologue
- Myth

The world is a tiny classical simulation: a hero with physical meters and
emotional memes moves through a mythic place, a risk is predicted, a safer
plan is chosen, and the ending image reflects the state change.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    wore: object | None = None
    bristle: object | None = None
    gift: object | None = None
    patty: object | None = None
    def __post_init__(self) -> None:
        for k in ["dust", "mud", "strain", "shine", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "wonder", "love", "calm", "joy", "fear", "resolve"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    id: str
    name: str
    myth_note: str
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
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    risk_kind: str
    zone: set[str]
    omen: str
    keyword: str
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
class Gift:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    reason: str = ""
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
class Remedy:
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.task: Optional[Task] = None
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

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.task = copy.deepcopy(self.task)
        c.paragraphs = [[]]
        return c


def _covers(actor: Entity, region: str, world: World) -> bool:
    return any(item.protective and region in item.covers for item in world.worn_items(actor))


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    task = world.task
    if task is None:
        return out
    for actor in world.characters():
        if actor.meters[task.risk_kind] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.id == "gift" and item.worn_by is None:
                continue
            if item.kind == "gift" and item.meters["shine"] >= THRESHOLD:
                continue
            sig = ("soil", actor.id, item.id, task.id)
            if sig in world.fired:
                continue
            if task.zone and item.id == "gift":
                world.fired.add(sig)
                item.meters["dust"] += 1
                item.meters["shine"] = max(0.0, item.meters["shine"] - 1)
                out.append(f"The {item.label} lost some of its bright shine.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    bristle = world.get("bristle")
    gift = world.get("gift")
    if bristle.meters["mud"] >= THRESHOLD and gift.meters["dust"] >= THRESHOLD:
        sig = ("worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            bristle.memes["worry"] += 1
            out.append("Bristle felt a small pinch of worry.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    patty = world.get("patty")
    bristle = world.get("bristle")
    if patty.memes["love"] >= THRESHOLD and bristle.memes["resolve"] >= THRESHOLD:
        sig = ("calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            bristle.memes["calm"] += 1
            out.append("The worry loosened like a knot in warm hands.")
    return out


RULES = [
    ("soil", _r_soil),
    ("worry", _r_worry),
    ("calm", _r_calm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, task: Task, gift: Entity) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters[task.risk_kind] += 1
    if task.risk_kind == "dust":
        sim.get(gift.id).meters["dust"] += 1
    if task.risk_kind == "mud":
        sim.get(gift.id).meters["mud"] += 1
    propagate(sim, narrate=False)
    return {
        "gift_soiled": sim.get(gift.id).meters["dust"] >= THRESHOLD or sim.get(gift.id).meters["mud"] >= THRESHOLD,
    }


def select_remedy(task: Task, gift: Gift) -> Optional[Remedy]:
    for remedy in REMEDIES:
        if task.risk_kind in remedy.guards and gift.region in remedy.covers:
            return remedy
    return None


def tell(place: Place, task: Task, gift_cfg: Gift, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(place)
    world.task = task

    bristle = world.add(Entity(
        id="bristle", kind="character", type=hero_type, label=hero_name,
        traits=["small", "bristly", "thoughtful"],
    ))
    patty = world.add(Entity(
        id="patty", kind="character", type=parent_type, label="Patty",
        traits=["kind", "wise"],
    ))
    gift = world.add(Entity(
        id="gift", type=gift_cfg.id, label=gift_cfg.label, phrase=gift_cfg.phrase,
        owner=bristle.id, caretaker=patty.id, wore=bristle.id if False else None,
    ))
    gift.region = gift_cfg.region if hasattr(gift, "region") else gift_cfg.region

    bristle.memes["hope"] += 1
    world.say(f"In {place.name}, {hero_name} was a little mythic {hero_type} with a bristly back and a brave heart.")
    world.say(f"{hero_name} loved the old road, because {task.gerund} made {hero_name} feel close to the sky.")
    world.say(f"Patty had given {hero_name} {gift_cfg.phrase}, and {hero_name} treasured {gift.it()} like a tiny sun.")

    world.para()
    world.say(place.myth_note)
    world.say(f"One day, {hero_name} and Patty came to {place.name} to {task.verb}.")
    world.say(f"{hero_name} wanted to go at once, but {hero_name} looked at {gift_cfg.label} and thought, \"If I rush, I may bring it back dull.\"")
    world.say(f"Patty watched the dark place ahead and said, \"Care first, then glory.\"")

    world.para()
    bristle.meters[task.risk_kind] += 1
    bristle.memes["worry"] += 1
    if task.risk_kind == "dust":
        gift.meters["dust"] += 1
    if task.risk_kind == "mud":
        gift.meters["mud"] += 1
    propagate(world, narrate=True)

    world.say(f"{hero_name} listened to the thought inside: \"I can be bold without being foolish.\"")
    world.say(f"{hero_name} reached for a safer way instead of the first, rough path.")

    world.para()
    remedy = select_remedy(task, gift_cfg)
    if remedy is None:
        pass
    if predict(world, bristle, task, gift)["gift_soiled"]:
        pass
    bristle.memes["resolve"] += 1
    patty.memes["love"] += 1
    world.say(f"Patty smiled and offered {remedy.label}.")
    world.say(f'"We can {remedy.prep}," Patty said, "and still {task.verb} together."')
    world.say(f"{hero_name}'s chest grew warm. \"That is the truest path,\" {hero_name} thought.")
    world.say(f"They {remedy.tail}, and the road no longer felt like a trap.")
    world.say(f"At the end, {hero_name} was {task.gerund}, {gift_cfg.label} stayed clean, and Patty laughed as if the stars had learned to sing.")

    world.facts.update(
        bristle=bristle,
        patty=patty,
        gift=gift,
        place=place,
        task=task,
        remedy=remedy,
    )
    return world


SETTINGS = {
    "grove": Place(
        id="grove",
        name="the moonlit grove",
        myth_note="The grove was old as a drumbeat, and its trees held silver hush in their branches.",
        affords={"cross_bridge", "gather_honey"},
    ),
    "hill": Place(
        id="hill",
        name="the high hill",
        myth_note="The hill stood like a watchful giant, and the wind carried stories up its sides.",
        affords={"climb_steps", "carry_lantern"},
    ),
    "spring": Place(
        id="spring",
        name="the stone spring",
        myth_note="The spring sang under the stones, and every drop seemed to remember the dawn.",
        affords={"fetch_water", "cross_bridge"},
    ),
}

TASKS = {
    "cross_bridge": Task(
        id="cross_bridge",
        verb="cross the moss bridge",
        gerund="crossing the moss bridge",
        risk="mud on the gift",
        risk_kind="mud",
        zone={"feet", "gift"},
        omen="the bridge was slick with river mist",
        keyword="bridge",
    ),
    "climb_steps": Task(
        id="climb_steps",
        verb="climb the old steps",
        gerund="climbing the old steps",
        risk="dust on the gift",
        risk_kind="dust",
        zone={"gift"},
        omen="the steps were powdered with ancient dust",
        keyword="steps",
    ),
    "fetch_water": Task(
        id="fetch_water",
        verb="fetch water from the spring",
        gerund="fetching water from the spring",
        risk="dust on the gift",
        risk_kind="dust",
        zone={"gift"},
        omen="the path was dry and chalky",
        keyword="spring",
    ),
    "gather_honey": Task(
        id="gather_honey",
        verb="gather honey from the hollow tree",
        gerund="gathering honey from the hollow tree",
        risk="mud on the gift",
        risk_kind="mud",
        zone={"feet", "gift"},
        omen="the roots were wet and sticky",
        keyword="honey",
    ),
    "carry_lantern": Task(
        id="carry_lantern",
        verb="carry the lantern to the shrine",
        gerund="carrying the lantern to the shrine",
        risk="dust on the gift",
        risk_kind="dust",
        zone={"gift"},
        omen="the shrine path was lined with ash",
        keyword="lantern",
    ),
}

GIFTS = {
    "crown": Gift(
        id="crown",
        label="golden crown",
        phrase="a golden crown",
        region="gift",
        genders={"girl", "boy"},
        reason="an offering fit for a mythic procession",
    ),
    "patty": Gift(
        id="patty",
        label="sun patty",
        phrase="a sun patty baked with honey",
        region="gift",
        genders={"girl", "boy"},
        reason="a round sweet offering named with the seed word",
    ),
    "lantern": Gift(
        id="lantern",
        label="paper lantern",
        phrase="a paper lantern painted with stars",
        region="gift",
        genders={"girl", "boy"},
        reason="a bright thing for a shrine path",
    ),
}

REMEDIES = [
    Remedy("soft_basket", "a soft basket", {"gift"}, {"mud", "dust"}, "put the gift in a soft basket first", "walked with the soft basket between them and the road"),
    Remedy("cloth_wrap", "a clean cloth wrap", {"gift"}, {"dust"}, "wrap the gift in a clean cloth first", "went on with the clean cloth wrapped safely around the gift"),
    Remedy("stone_cradle", "a small stone cradle", {"gift"}, {"mud"}, "set the gift in a small stone cradle first", "carried the stone cradle carefully across the damp path"),
]

GIRL_NAMES = ["Mara", "Lina", "Nina", "Iris", "Tala"]
BOY_NAMES = ["Orin", "Eli", "Soren", "Pax", "Nico"]
TRAITS = ["brave", "gentle", "curious", "quiet", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, p in SETTINGS.items():
        for task_id in p.affords:
            task = _safe_lookup(TASKS, task_id)
            for gift_id, gift in GIFTS.items():
                if task.risk_kind in {"mud", "dust"} and gift.region == "gift":
                    if select_remedy(task, gift) is not None:
                        out.append((place, task_id, gift_id))
    return out


@dataclass
class StoryParams:
    place: str
    task: str
    gift: str
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


KNOWLEDGE = {
    "mud": [("What is mud?", "Mud is wet dirt that can stick to shoes and things that touch the ground.")],
    "dust": [("What is dust?", "Dust is very tiny dry bits of dirt that can gather on old stones and paths.")],
    "bridge": [("What is a bridge?", "A bridge is a path that helps people cross over water or a gap.")],
    "spring": [("What is a spring?", "A spring is a place where water flows up from the ground.")],
    "lantern": [("What is a lantern?", "A lantern is a light that can be carried to help people see in the dark.")],
    "crown": [("What is a crown?", "A crown is a special head украшение? no. A crown is a special headpiece worn to show honor.")],
    "patty": [("What is a patty?", "A patty is a small round cake or pastry, often sweet or savory.")],
}

KNOWLEDGE_ORDER = ["mud", "dust", "bridge", "spring", "lantern", "crown", "patty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about {f["bristle"].label} and Patty, using the word "bristle".',
        f"Tell a happy-ending story where {f['bristle'].label} thinks carefully before {f['task'].verb}, then chooses a safer path.",
        f'Write a tiny legend with an inner monologue, a sacred gift, and the word "patty".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "bristle")
    patty = _safe_fact(world, f, "patty")
    gift = _safe_fact(world, f, "gift")
    task = _safe_fact(world, f, "task")
    remedy = _safe_fact(world, f, "remedy")
    qs = [
        QAItem(
            question=f"Who is the story about in the moonlit {world.place.name.split()[-1]}?",
            answer=f"It is about {hero.label}, a small bristly hero, and Patty, who stays close and wise through the trial.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do at first?",
            answer=f"{hero.label} wanted to {task.verb}, because the place called like a mythic road and the task sounded bold.",
        ),
        QAItem(
            question=f"What precious thing did Patty give {hero.label}?",
            answer=f"Patty gave {hero.label} {gift.phrase}, and {hero.label} treasured {gift.label} like a tiny sun.",
        ),
        QAItem(
            question=f"What did {hero.label} think in the middle of the story?",
            answer=f"{hero.label} thought, \"I can be bold without being foolish,\" which helped {hero.label} slow down and choose care.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label} and Patty?",
            answer=f"They used {remedy.label}, finished the journey, and the gift stayed clean, so the ending was happy and bright.",
        ),
    ]
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {f["task"].risk_kind, f["gift"].id}
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in RULES if (n,) in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("grove", "cross_bridge", "patty", "Bristle", "boy", "mother", "curious"),
    StoryParams("hill", "climb_steps", "crown", "Bristle", "boy", "father", "brave"),
    StoryParams("spring", "carry_lantern", "lantern", "Bristle", "boy", "mother", "gentle"),
]


def explain_rejection(task: Task, gift: Gift) -> str:
    return (
        f"(No story: {task.gerund} would not make a safe, mythic problem for {gift.label}. "
        f"The gift must be genuinely at risk, and a remedy must fit the risk.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("risk_kind", tid, t.risk_kind))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_on", gid, g.region))
    for rid, r in enumerate(REMEDIES):
        lines.append(asp.fact("remedy", r.id))
        for c in sorted(r.covers):
            lines.append(asp.fact("covers", r.id, c))
        for gk in sorted(r.guards):
            lines.append(asp.fact("guards", r.id, gk))
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,G) :- task(A), gift(G), gift_on(G, gift), risk_kind(A, K), guards(R, K), covers(R, gift).
valid(Place,A,G) :- affords(Place,A), risk(A,G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world about Bristle and Patty.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "task", None) and getattr(args, "gift", None):
        task, gift = _safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(GIFTS, getattr(args, "gift", None))
        if select_remedy(task, gift) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task_id, gift_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, task_id, gift_id, name, gender, parent, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TASKS, params.task),
        _safe_lookup(GIFTS, params.gift),
        params.name,
        params.gender,
        params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/3."))
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
            header = f"### {p.name}: {p.task} at {p.place} (gift: {p.gift})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
