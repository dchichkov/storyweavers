#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tripod_alert_adenoid_reconciliation_slice_of_life.py
================================================================================================

A small slice-of-life story world about a child, a tiny interruption, and a
reconciliation that lands softly at home.

Seed image:
- A child keeps missing a friend because an adenoid appointment leaves them
  tired and snuffly.
- A phone alert reminds the family to send an apology.
- A tripod holds the tablet steady for a gentle video call.
- The story ends with a small, believable reconciliation.

This is a self-contained world: it models physical state with meters and
emotional state with memes, then lets those states drive the prose and Q&A.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_for: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adenoid: object | None = None
    alert: object | None = None
    child: object | None = None
    friend: object | None = None
    parent: object | None = None
    trip: object | None = None
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
    indoors: bool = True
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
class Gear:
    id: str
    label: str
    phrase: str
    supports: set[str]
    helps: set[str]
    prep: str
    tail: str
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
    setting: str
    activity: str
    name: str
    gender: str
    parent: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.alert_rang = False
        self.reconciled = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.alert_rang = self.alert_rang
        c.reconciled = self.reconciled
        return c


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"call", "video"}),
    "living_room": Setting(place="the living room", indoors=True, affords={"call", "video"}),
    "sunroom": Setting(place="the sunroom", indoors=True, affords={"call", "video"}),
}

ACTIVITIES = {
    "video_call": Activity(
        id="video_call",
        verb="make a video call",
        gerund="making a video call",
        rush="tap the call button",
        mess="glare",
        zone={"hands", "face"},
        keyword="video",
        tags={"call", "phone", "reconciliation"},
    ),
    "apology_note": Activity(
        id="apology_note",
        verb="write an apology note",
        gerund="writing an apology note",
        rush="start writing fast",
        mess="ink",
        zone={"hands"},
        keyword="note",
        tags={"note", "reconciliation"},
    ),
    "message_recording": Activity(
        id="message_recording",
        verb="record a message",
        gerund="recording a message",
        rush="press record",
        mess="glare",
        zone={"hands", "face"},
        keyword="recording",
        tags={"video", "reconciliation"},
    ),
}

GEAR = [
    Gear(
        id="tripod",
        label="a tripod",
        phrase="the camera tripod",
        supports={"hands"},
        helps={"video"},
        prep="set up the tripod and keep the tablet steady",
        tail="stayed steady on the tripod",
    ),
    Gear(
        id="stand",
        label="a little stand",
        phrase="the little stand",
        supports={"hands"},
        helps={"note"},
        prep="put the tablet on a little stand",
        tail="sat neatly on the little stand",
    ),
]

GIRL_NAMES = ["Maya", "Lina", "June", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Owen", "Max"]
TRAITS = ["quiet", "gentle", "thoughtful", "shy", "patient", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for setting_name, setting in SETTINGS.items():
        for act_id in setting.affords:
            for gear in GEAR:
                if act_id == "call" and gear.id == "tripod":
                    out.append((setting_name, "video_call"))
                if act_id == "call" and gear.id == "stand":
                    out.append((setting_name, "apology_note"))
    return sorted(set(out))


def supported_gear(activity: Activity) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.helps:
            return gear
    return None


def reasonableness_check(setting: Setting, activity: Activity) -> bool:
    return activity.id in {"video_call", "apology_note", "message_recording"} and bool(supported_gear(activity))


def predict(world: World, child: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(child.id), activity, narrate=False)
    return {
        "alert": sim.alert_rang,
        "reconciled": sim.reconciled,
        "stress": sum(e.memes.get("stress", 0) for e in sim.characters()),
    }


def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    child.meters[activity.mess] = child.meters.get(activity.mess, 0.0) + 1.0
    child.memes["focus"] = child.memes.get("focus", 0.0) + 1.0
    if activity.id == "message_recording":
        child.memes["nervous"] = child.memes.get("nervous", 0.0) + 1.0
    if narrate:
        propagate(world, narrate=True)


def _r_alert(world: World) -> list[str]:
    out: list[str] = []
    if world.alert_rang:
        return out
    child = next((e for e in world.characters() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not child:
        return out
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return out
    world.alert_rang = True
    out.append("The phone gave a soft alert.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    parent = next((e for e in world.characters() if e.kind == "character" and e.type in {"mother", "father"}), None)
    friend = world.entities.get("friend")
    if not child or not parent or not friend:
        return out
    if child.memes.get("apology", 0.0) < THRESHOLD:
        return out
    if world.reconciled:
        return out
    world.reconciled = True
    child.memes["peace"] = child.memes.get("peace", 0.0) + 1.0
    friend.memes["warmth"] = friend.memes.get("warmth", 0.0) + 1.0
    out.append("The little hurt between them started to soften.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_alert, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, activity: Activity, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"worry": 1.0}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    friend = world.add(Entity(id="friend", kind="character", type="girl", label="the neighbor friend", memes={"hurt": 1.0}))
    trip = world.add(Entity(id="tripod", type="tripod", label="tripod"))
    alert = world.add(Entity(id="alert", type="alert", label="alert"))
    adenoid = world.add(Entity(id="adenoid", type="adenoid", label="adenoid"))

    world.say(f"{child.id} was a {next((t for t in TRAITS if t != 'careful'), 'gentle')} {child.type} who had a quiet day at {setting.place}.")
    world.say(f"Earlier, the doctor had talked about an adenoid, and the word still felt big in {child.pronoun('possessive')} mouth.")
    world.say(f"{child.id} missed {friend.label} and wanted to fix the awkwardness.")
    world.para()
    world.say(f"At {setting.place}, {parent.label_word if hasattr(parent, 'label_word') else parent.label} noticed the mood and heard the phone alert.")
    world.say(f'"That might be the reminder," {parent.pronoun("subject")} said. "Let’s answer it kindly."')
    world.say(f"{child.id} wanted to {activity.verb}, but {child.pronoun('possessive')} hands shook a little.")
    child.memes["worry"] += 1.0
    propagate(world, narrate=False)

    gear = supported_gear(activity)
    if gear is None:
        pass
    if gear.id == "tripod":
        world.say(f"{parent.pronoun('possessive').capitalize()} {gear.label} came out of the cupboard, and soon the tablet {gear.tail}.")
    else:
        world.say(f"{parent.pronoun('possessive').capitalize()} little stand helped hold the tablet still.")
    world.para()
    world.say(f"{child.id} took a breath, looked at the screen, and said sorry about missing the message after the adenoid visit.")
    child.memes["apology"] += 1.0
    child.memes["worry"] = 0.0
    friend.memes["hurt"] = 0.0
    parent.memes["pride"] = parent.memes.get("pride", 0.0) + 1.0
    propagate(world, narrate=True)
    world.say(f"{friend.label} smiled, and the call ended with everyone feeling a little lighter than before.")

    world.facts.update(
        child=child,
        parent=parent,
        friend=friend,
        tripod=trip,
        alert=alert,
        adenoid=adenoid,
        activity=activity,
        setting=setting,
        gear=gear,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    act = _safe_fact(world, f, "activity")
    return [
        f"Write a small slice-of-life story about {child.id}, a phone alert, and a tripod that helps with {act.verb}.",
        f"Tell a gentle reconciliation story where a child named {child.id} feels better after an adenoid appointment and calls a friend.",
        f"Write a calm, everyday story that includes the words tripod, alert, and adenoid, and ends with people making up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    friend = _safe_fact(world, f, "friend")
    activity = _safe_fact(world, f, "activity")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Why did {child.id} want to use the tripod?",
            answer=f"{child.id} wanted to use the tripod so the tablet could stay steady while they {activity.verb}.",
        ),
        QAItem(
            question="What did the phone alert lead the family to do?",
            answer="The alert reminded the family to answer kindly and make the message instead of ignoring the awkward feeling.",
        ),
        QAItem(
            question=f"How did the story end between {child.id} and {friend.label}?",
            answer=f"They made up at the end, and {friend.label} smiled after hearing the apology.",
        ),
        QAItem(
            question=f"Why did the word adenoid matter in the story?",
            answer="The adenoid appointment had left the child feeling a little tired and sensitive, so the apology felt important.",
        ),
        QAItem(
            question=f"What did {gear.label} help with?",
            answer=f"{gear.label} helped keep the tablet steady for the call.",
        ),
    ]


KNOWLEDGE = {
    "tripod": [
        QAItem(
            question="What is a tripod for?",
            answer="A tripod is a stand with three legs that helps hold a camera or tablet still.",
        )
    ],
    "alert": [
        QAItem(
            question="What is an alert on a phone?",
            answer="An alert is a signal that tells you something needs your attention soon.",
        )
    ],
    "adenoid": [
        QAItem(
            question="What is an adenoid?",
            answer="An adenoid is a small bit of tissue in the back of the nose, and doctors sometimes talk about it when a child has breathing trouble.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after people have felt upset or apart.",
        )
    ],
}

KNOWLEDGE_ORDER = ["tripod", "alert", "adenoid", "reconciliation"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        out.extend(KNOWLEDGE.get(key, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"alert_rang={world.alert_rang}")
    lines.append(f"reconciled={world.reconciled}")
    return "\n".join(lines)


ASP_RULES = r"""
setting_place(kitchen).
setting_place(living_room).
setting_place(sunroom).

activity(video_call).
activity(apology_note).
activity(message_recording).

gear(tripod).
gear(stand).

helps(tripod, video).
helps(tripod, call).
helps(stand, note).

valid(S, A) :- setting_place(S), activity(A), A = video_call.
valid(S, A) :- setting_place(S), activity(A), A = message_recording.
valid(S, A) :- setting_place(S), activity(A), A = apology_note.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_place", s))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP and Python agree on {len(python_set)} combos.")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(python_set - asp_set))
    print("only asp:", sorted(asp_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with a tripod, an alert, and an adenoid.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "activity", None) and getattr(args, "activity", None) not in ACTIVITIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "activity", None) and getattr(args, "activity", None) not in _safe_lookup(SETTINGS, getattr(args, "place", None)).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    settings = [getattr(args, "place", None)] if getattr(args, "place", None) else list(SETTINGS)
    acts = [getattr(args, "activity", None)] if getattr(args, "activity", None) else list(ACTIVITIES)
    combos = [(s, a) for s in settings for a in acts if a in _safe_lookup(SETTINGS, s).affords]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, activity=activity, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ACTIVITIES, params.activity), params.name, params.gender, params.parent)
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
    StoryParams(setting="kitchen", activity="video_call", name="Maya", gender="girl", parent="mother"),
    StoryParams(setting="living_room", activity="apology_note", name="Theo", gender="boy", parent="father"),
    StoryParams(setting="sunroom", activity="message_recording", name="Nora", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for s, a in asp_valid_combos():
            print(s, a)
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
            header = f"### {p.name}: {p.activity} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
