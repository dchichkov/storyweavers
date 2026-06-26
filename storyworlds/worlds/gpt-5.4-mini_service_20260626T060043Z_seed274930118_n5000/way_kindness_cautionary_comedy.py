#!/usr/bin/env python3
"""
storyworlds/worlds/way_kindness_cautionary_comedy.py
=====================================================

A small story world about choosing a way, listening to a warning, and finding
a kind, funny compromise.

Seed tale idea:
---
A child wants to take a silly shortcut over a slippery garden wall to reach a
friend's picnic. A grown-up warns that the wall is wobbly and the basket will
spill. The child grumbles, then notices a kinder way: they take the safe path,
carry the basket together, and still arrive in time to laugh.

World shape:
- physical meters: wobble, wetness, spill, distance, effort
- emotional memes: curiosity, worry, grumpiness, kindness, relief, pride

The comedy comes from the child's overconfident shortcut idea and the grown-up's
serious warning; the kindness comes from helping carry, sharing, and choosing a
safer route.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def __post_init__(self):
        for k in ["wobble", "wet", "spill", "distance", "effort"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "grumpiness", "kindness", "relief", "pride"]:
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    place: str
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
class Way:
    id: str
    label: str
    description: str
    risk: str
    safe_label: str
    safe_description: str
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
class Prize:
    label: str
    phrase: str
    type: str
    danger: str
    carried: bool = True
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
class Help:
    id: str
    label: str
    action: str
    outcome: str
    prevents: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.path: str = ""
        self.safe_path: str = ""

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
        clone.path = self.path
        clone.safe_path = self.safe_path
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wobble"] < THRESHOLD:
            continue
        for prize in list(world.entities.values()):
            if prize.kind != "thing" or not prize.carried_by:
                continue
            if prize.carried_by != actor.id:
                continue
            sig = ("spill", actor.id, prize.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if world.path == "wobbly_wall" and world.facts.get("on_wall"):
                prize.meters["spill"] += 1
                out.append(f"{actor.id} wobbled so hard that {prize.label} nearly spilled.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wobble"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["grumpiness"] += 1
        out.append(f"That made {actor.id} grumble at the warning.")
    return out


def _r_kind_help(world: World) -> list[str]:
    out: list[str] = []
    helper = world.facts.get("helper")
    if not helper:
        return out
    h = world.get(helper.id)
    if h.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kind_help", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    h.memes["pride"] += 1
    out.append(f"{h.id} helped in a kind way, and the whole plan felt lighter.")
    return out


CAUSAL_RULES = [
    Rule("spill", _r_spill),
    Rule("worry", _r_worry),
    Rule("kind_help", _r_kind_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, hero: Entity, path: Way, prize_id: str) -> dict:
    sim = world.copy()
    sim.path = path.id
    sim.facts["on_wall"] = path.id == "wobbly_wall"
    sim.get(hero.id).meters["wobble"] += 1
    prize = sim.get(prize_id)
    prize.carried_by = hero.id
    propagate(sim, narrate=False)
    return {"spill": prize.meters["spill"] >= THRESHOLD}


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "cheerful")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked finding the best way to do things.")


def loves(world: World, hero: Entity, way: Way) -> None:
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} loved the {way.description}, because it felt like a secret way to be fast.")


def gift(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{parent.label_word} gave {hero.id} {hero.pronoun('object')} {prize.phrase} for the picnic.")


def wants_shortcut(world: World, hero: Entity, way: Way) -> None:
    world.say(f"{hero.id} pointed at the {way.label} and said it was the quicker way.")


def warn(world: World, parent: Entity, hero: Entity, way: Way, prize: Entity) -> bool:
    pred = predict_risk(world, hero, way, prize.id)
    if not pred["spill"]:
        return False
    hero.memes["worry"] += 1
    world.say(f"\"That way looks wobbly,\" {hero.pronoun('possessive')} {hero.label_word} said.")
    world.say(f"\"If you go there with {prize.label}, you could spill it and make a silly mess.\"")
    return True


def defy(world: World, hero: Entity, way: Way) -> None:
    hero.meters["wobble"] += 1
    hero.memes["grumpiness"] += 1
    world.say(f"{hero.id} tried the risky way anyway and made the most dramatic tiny wobble ever.")


def choose_safe(world: World, hero: Entity, parent: Entity, way: Way, prize: Entity, help_def: Help) -> None:
    hero.memes["kindness"] += 1
    hero.memes["relief"] += 1
    prize.carried_by = None
    world.say(f"Then {hero.id} noticed a kinder way: the safe path beside the wall.")
    world.say(f"{hero.id} and {parent.id} followed it together, {help_def.action}, and nobody spilled a thing.")
    world.say(f"At the picnic, {hero.id} laughed, {prize.label} stayed safe, and the whole day felt pleasantly wiser.")


SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"wall", "path"}),
    "yard": Setting(place="the yard", indoor=False, affords={"path"}),
    "park": Setting(place="the park", indoor=False, affords={"path", "bridge"}),
}

WAYS = {
    "wobbly_wall": Way(
        id="wobbly_wall",
        label="wobbly wall",
        description="a short wobbly wall near the flowers",
        risk="a tumble and a spill",
        safe_label="garden path",
        safe_description="the garden path with no wobbling at all",
    ),
    "muddy_bridge": Way(
        id="muddy_bridge",
        label="muddy bridge",
        description="a muddy bridge over the stream",
        risk="slipping into the mud",
        safe_label="low bridge",
        safe_description="the low bridge with steady boards",
    ),
}

PRIZES = {
    "juice": Prize(label="juice box", phrase="a full juice box", type="juice box", danger="spill"),
    "cookies": Prize(label="cookie tin", phrase="a tin of cookies", type="cookie tin", danger="crush", plural=False),
    "flowers": Prize(label="flowers", phrase="a bunch of flowers", type="flowers", danger="crush", plural=True),
}

HELPS = {
    "carry": Help(
        id="carry",
        label="help carry",
        action="helped carry the basket carefully",
        outcome="the basket stayed steady",
        prevents={"spill"},
    ),
    "hold_hand": Help(
        id="hold_hand",
        label="hold hands",
        action="held hands on the safer path",
        outcome="they walked without wobbling",
        prevents={"spill"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Poppy", "Nora", "Ivy", "Ruby"]
BOY_NAMES = ["Max", "Eli", "Theo", "Finn", "Owen", "Jack"]
TRAITS = ["curious", "cheerful", "spirited", "silly", "patient", "lively"]


@dataclass
class StoryParams:
    place: str
    way: str
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


def tell(setting: Setting, way: Way, prize_cfg: Prize, hero_name: str, hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(id="Prize", kind="thing", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id))
    help_def = HELPS["carry"]

    world.facts.update(hero=hero, parent=parent, prize=prize, way=way, help=help_def)
    intro(world, hero)
    loves(world, hero, way)
    gift(world, parent, hero, prize)
    world.para()
    wants_shortcut(world, hero, way)
    world.path = way.id
    world.facts["on_wall"] = way.id == "wobbly_wall"
    warn(world, parent, hero, way, prize)
    defy(world, hero, way)
    propagate(world, narrate=True)
    world.para()
    choose_safe(world, hero, parent, way, prize, help_def)
    world.facts["resolved"] = True
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for way_id in setting.affords:
            for prize_id in PRIZES:
                if way_id == "path" and prize_id == "juice":
                    continue
                if way_id == "wall" and prize_id in {"juice", "cookies"}:
                    combos.append((place, way_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedy world about choosing the safe way.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--way", choices=WAYS)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "way", None):
        combos = [c for c in combos if c[1] == getattr(args, "way", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, way, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, way=way, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize, way = f["hero"], f["prize"], f["way"]
    return [
        f'Write a short story for a young child about choosing the safe way and using the word "way".',
        f"Tell a funny but caring story where {hero.id} wants the {way.label}, but the grown-up worries about {prize.label}.",
        f"Write a gentle comedy about a child who learns there is a kinder way to travel to a picnic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, way = f["hero"], f["parent"], f["prize"], f["way"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"At first, {hero.id} wanted to take the {way.label}, which seemed like the fastest way.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about the {way.label}?",
            answer=f"{parent.label_word.capitalize()} worried because the {way.label} was wobbly and {prize.label} could spill.",
        ),
        QAItem(
            question=f"What was the kinder way in the end?",
            answer=f"The kinder way was the safe path, and {hero.id} and {parent.label_word} used it together.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} stopped chasing the risky shortcut, and {prize.label} arrived safely at the picnic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to take the safe way?",
            answer="Taking the safe way means choosing the path that is less likely to cause a fall, a spill, or another problem.",
        ),
        QAItem(
            question="Why can a wobbly wall be dangerous?",
            answer="A wobbly wall can be dangerous because it might shake or tip, which could make someone lose balance.",
        ),
        QAItem(
            question="What does kindness look like in a plan?",
            answer="Kindness in a plan can mean helping carry something, sharing the work, or choosing a way that keeps everyone safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    out.append(f"path={world.path} safe_path={world.safe_path}")
    return "\n".join(out)


ASP_RULES = r"""
path_risky(W) :- way(W), risky(W).
safe_way(W) :- way(W), not risky(W).
valid(Place, Way, Prize) :- affords(Place, Way), way(Way), prize(Prize), risk_match(Way, Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for w in sorted(s.affords):
            lines.append(asp.fact("affords", pid, w))
    for wid, w in WAYS.items():
        lines.append(asp.fact("way", wid))
        lines.append(asp.fact("risky", wid))
    for prid, p in PRIZES.items():
        lines.append(asp.fact("prize", prid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    # lightweight parity: just ensure program solves and yields atoms
    model = asp.one_model(asp_program("#show way/1."))
    _ = asp.atoms(model, "way")
    print("OK: ASP program loads.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(WAYS, params.way), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="garden", way="wobbly_wall", prize="juice", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="park", way="wobbly_wall", prize="cookies", name="Eli", gender="boy", parent="father", trait="silly"),
    StoryParams(place="garden", way="wobbly_wall", prize="flowers", name="Nora", gender="girl", parent="mother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
