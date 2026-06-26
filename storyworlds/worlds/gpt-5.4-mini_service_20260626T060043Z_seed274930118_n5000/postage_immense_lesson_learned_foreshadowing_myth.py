#!/usr/bin/env python3
"""
A mythic story world about postage, immense gifts, and the lesson learned from
a warning seen before the trouble arrives.

The seed tale imagined here:
- A child or young keeper wants to send a message or offering.
- The thing to be sent is immense, or the postage is too small.
- A foreshadowing sign warns that the road or gate will refuse the parcel.
- A wiser helper teaches the lesson learned: weigh it, seal it, and add enough
  postage before sending.
- The ending proves the change by showing the message safely on its way.

This script follows the Storyweavers world contract:
- stdlib only for prose mode
- lazy clingo import through storyworlds/asp.py
- StoryParams + parser + resolve_params + generate + emit + main
- inline ASP twin plus Python reasonableness gate
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    parcel: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" and self.type == "crow":
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
    afford: set[str] = field(default_factory=set)
    mood: str = ""
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
class Parcel:
    id: str
    label: str
    phrase: str
    size: str
    weight: str
    needs: set[str] = field(default_factory=set)
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
class PostageKit:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fixes: set[str]
    prep: str
    tail: str
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
class StoryParams:
    place: str
    activity: str
    parcel: str
    name: str
    gender: str
    mentor: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        return w


def _r_return(world: World) -> list[str]:
    out: list[str] = []
    for parcel in list(world.entities.values()):
        if parcel.kind != "parcel":
            continue
        if parcel.meters.get("underpaid", 0.0) < THRESHOLD:
            continue
        sig = ("return", parcel.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        parcel.meters["rejected"] = 1
        out.append("The gate would not open for it.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ch in world.characters():
        if ch.memes.get("warning", 0.0) < THRESHOLD:
            continue
        sig = ("worry", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["worry"] += 1
        out.append(f"{ch.id} frowned, as if a storm had already spoken.")
    return out


RULES = [
    ("return", _r_return),
    ("worry", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.mood == "dawn":
        return f"At dawn, {setting.place} glimmered like a bowl of copper."
    if setting.mood == "rain":
        return f"After rain, {setting.place} smelled of stone and moss."
    return f"{setting.place.capitalize()} waited in a hush that felt old as songs."


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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
class ParcelConfig:
    label: str
    phrase: str
    size: str
    weight: str
    needs: set[str]
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
class Kit:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fixes: set[str]
    prep: str
    tail: str
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


def is_at_risk(activity: Activity, parcel: Parcel) -> bool:
    return parcel.size in activity.risk or parcel.weight in activity.risk


def select_kit(activity: Activity, parcel: Parcel) -> Optional[Kit]:
    for kit in KITS:
        if parcel.size in kit.covers and (activity.keyword in kit.fixes or parcel.weight in kit.fixes):
            return kit
    return None


def predict_block(world: World, actor: Entity, activity: Activity, parcel_id: str) -> dict:
    sim = world.copy()
    do_send(sim, sim.get(actor.id), activity, narrate=False)
    parcel = sim.entities[parcel_id]
    return {"rejected": bool(parcel.meters.get("rejected", 0.0) >= THRESHOLD)}


def do_send(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.afford:
        return
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
    world.say(f"{actor.id} went to the post gate to {activity.verb}.")
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next((t for t in hero.meters if False), 'keeper')} who listened for omens.")


def build_story(world: World, hero: Entity, mentor: Entity, parcel: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} loved to send letters and offerings, especially when the road felt like a tale.")
    world.say(f"One day, {hero.id} brought {hero.pronoun('possessive')} {parcel.label} to the post gate.")
    world.say(setting_detail(world.setting, activity))
    world.say(f"{hero.id} wanted to {activity.verb}, but {mentor.label} lifted a hand and looked uneasy.")
    world.say(f'"Your {parcel.label} is {parcel.phrase}," {mentor.label} said. "It needs more postage than this."')
    parcel.meters["underpaid"] = 1
    hero.memes["warning"] = 1
    propagate(world, narrate=True)
    world.say(f"{hero.id} saw a row of empty shells by the gate, a foreshadowing sign that the road would refuse a light stamp.")
    world.say(f"{hero.id} tried to {activity.rush}, yet the gate stayed closed.")
    world.say(f"Then the lesson was learned: when a thing is {parcel.phrase}, wisdom weighs it first and seals it well.")
    kit = select_kit(activity, parcel)
    if kit is not None:
        world.say(f"{mentor.label} brought {kit.label} and said, \"Use this before you try again.\"")
        parcel.meters["underpaid"] = 0
        hero.memes["lesson"] = 1
        world.say(f"{hero.id} added the right postage, {kit.prep}, and the gate opened at last.")
        world.say(f"They {kit.tail}. Soon the {parcel.label} was on its way, and the whole road seemed taller for it.")
    else:
        world.say(f"No fitting postage was found, so the tale ended at the gate with a quiet promise to return tomorrow.")


SETTINGS = {
    "village_gate": Setting(place="the village gate", afford={"send_letter", "send_gift"}, mood="dawn"),
    "river_post": Setting(place="the river posthouse", afford={"send_letter"}, mood="rain"),
    "hill_temple": Setting(place="the hill temple", afford={"send_gift", "send_letter"}, mood="dawn"),
}

ACTIVITIES = {
    "send_letter": Activity(
        id="send_letter",
        verb="send the letter",
        gerund="sending letters",
        rush="carry the letter to the gate",
        risk="light postage",
        keyword="letter",
        tags={"postage", "lesson"},
    ),
    "send_gift": Activity(
        id="send_gift",
        verb="send the gift",
        gerund="sending gifts",
        rush="lift the bundle toward the gate",
        risk="small postage",
        keyword="gift",
        tags={"postage", "immense"},
    ),
}

PARCELS = {
    "scroll": ParcelConfig(
        label="scroll",
        phrase="a careful scroll",
        size="small",
        weight="light",
        needs={"seal"},
    ),
    "parcel": ParcelConfig(
        label="parcel",
        phrase="an immense parcel",
        size="immense",
        weight="heavy",
        needs={"seal", "cord"},
    ),
    "offering": ParcelConfig(
        label="offering",
        phrase="an immense offering basket",
        size="immense",
        weight="heavy",
        needs={"seal", "cord"},
    ),
}

KITS = [
    Kit(
        id="great_stamp",
        label="the great stamp",
        phrase="a wide bronze stamp",
        covers={"small", "immense"},
        fixes={"send_letter", "send_gift", "light", "heavy"},
        prep="pressed the great stamp onto the wax",
        tail="walked back from the gate with the seal shining",
    ),
    Kit(
        id="extra_postage",
        label="extra postage",
        phrase="more postage shells",
        covers={"small", "immense"},
        fixes={"send_letter", "send_gift"},
        prep="added the extra shells and tied the cord again",
        tail="carried the message forward with steady feet",
    ),
    Kit(
        id="wax_and_cord",
        label="wax and cord",
        phrase="warm wax and a strong cord",
        covers={"small"},
        fixes={"send_letter"},
        prep="sealed the fold with wax and tied it tight",
        tail="sent the letter where the river could not reach it",
    ),
]

GIRL_NAMES = ["Mira", "Asha", "Lina", "Tara", "Nia", "Sera", "Kala", "Rin"]
BOY_NAMES = ["Orin", "Bram", "Kian", "Jori", "Nilo", "Perrin", "Tavi", "Eli"]
TRAITS = ["patient", "bright", "curious", "steady", "brave", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.afford:
            activity = _safe_lookup(ACTIVITIES, act)
            for parcel_id, parcel in PARCELS.items():
                if is_at_risk(activity, parcel) and select_kit(activity, Parcel(parcel_id, parcel.label, parcel.phrase, parcel.size, parcel.weight, parcel.needs, parcel.genders)):
                    combos.append((place, act, parcel_id))
    return combos


def explain_rejection(activity: Activity, parcel: ParcelConfig) -> str:
    return f"(No story: {activity.verb} and {parcel.phrase} do not make a workable mythic problem here.)"


def explain_gender(parcel_id: str, gender: str) -> str:
    return f"(No story: {_safe_lookup(PARCELS, parcel_id).label} is not a typical {gender}'s task in this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world of postage, immense things, foreshadowing, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mentor", choices=["mother", "father", "grandmother", "old sage", "crow"])
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
    if getattr(args, "activity", None) and getattr(args, "parcel", None):
        act, par = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PARCELS, getattr(args, "parcel", None))
        if not is_at_risk(act, par) or not select_kit(act, Parcel(getattr(args, "parcel", None), par.label, par.phrase, par.size, par.weight, par.needs, par.genders)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "parcel", None) and getattr(args, "gender", None) not in _safe_lookup(PARCELS, getattr(args, "parcel", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "parcel", None) is None or c[2] == getattr(args, "parcel", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, parcel = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = getattr(args, "mentor", None) or rng.choice(["mother", "father", "grandmother", "old sage", "crow"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, parcel=parcel, name=name, gender=gender, mentor=mentor, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    mentor = world.add(Entity(id="mentor", kind="character", type=params.mentor, label=f"the {params.mentor}"))
    parcel_cfg = _safe_lookup(PARCELS, params.parcel)
    parcel = world.add(Entity(id="parcel", kind="parcel", type=parcel_cfg.label, label=parcel_cfg.label, phrase=parcel_cfg.phrase, owner=hero.id, caretaker=mentor.id))
    activity = _safe_lookup(ACTIVITIES, params.activity)

    world.say(f"{hero.id} was a {params.trait} child who watched the roads like a sky watcher watches stars.")
    world.say(f"{hero.id} loved the old custom of postage, because every stamped thing felt like a promise.")
    world.para()
    build_story(world, hero, mentor, parcel, activity)
    world.facts.update(hero=hero, mentor=mentor, parcel=parcel, activity=activity, setting=world.setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mentor, parcel, act = f["hero"], f["mentor"], f["parcel"], f["activity"]
    return [
        f'Write a short myth for children about {hero.id}, postage, and an {parcel.phrase}.',
        f"Tell a gentle legend where {hero.id} learns a lesson learned about {act.verb} and enough postage.",
        f'Write a story with foreshadowing, a warning, and a happy ending, using the word "postage".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mentor, parcel, act = f["hero"], f["mentor"], f["parcel"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {parcel.label}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the {mentor.type} warn {hero.id} at the gate?",
            answer=f"The {mentor.label} warned {hero.id} because the {parcel.phrase} needed more postage, and the first seal was not enough.",
        ),
        QAItem(
            question="What was the lesson learned in the story?",
            answer="The lesson learned was to weigh the thing first and add enough postage before sending it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is postage?",
            answer="Postage is the payment or stamp used to send a letter or parcel through the mail.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is a clue or sign that hints something important may happen later.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village_gate", activity="send_gift", parcel="parcel", name="Mira", gender="girl", mentor="old sage", trait="curious"),
    StoryParams(place="river_post", activity="send_letter", parcel="scroll", name="Orin", gender="boy", mentor="mother", trait="patient"),
    StoryParams(place="hill_temple", activity="send_gift", parcel="offering", name="Tavi", gender="boy", mentor="grandmother", trait="brave"),
]


ASP_RULES = r"""
parcel_risk(A,P) :- activity(A), parcel(P), risk_of(A,R), needs_size(P,S), risk_hits(R,S).
has_kit(A,P) :- parcel_risk(A,P), kit(K), covers(K,S), needs_fix(A,F), fixes(K,F).
valid_story(Place,A,P) :- affords(Place,A), parcel_risk(A,P), has_kit(A,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("risk_of", aid, a.risk))
        lines.append(asp.fact("needs_fix", aid, a.keyword))
    for pid, p in PARCELS.items():
        lines.append(asp.fact("parcel", pid))
        lines.append(asp.fact("needs_size", pid, p.size))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for k in KITS:
        lines.append(asp.fact("kit", k.id))
        for c in sorted(k.covers):
            lines.append(asp.fact("covers", k.id, c))
        for f in sorted(k.fixes):
            lines.append(asp.fact("fixes", k.id, f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} valid stories:\n")
        for place, act, parcel in combos:
            print(place, act, parcel)
        return

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
            header = f"### {p.name}: {p.activity} at {p.place} (parcel: {p.parcel})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
