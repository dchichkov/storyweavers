#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pump_tatter_duet_moral_value_inner_monologue.py
====================================================================================================

A small comedy-leaning story world about a child, a pump, a tattered prop, and
a duet that goes a little sideways before ending kindly.

Core premise
------------
A child and a friend are getting ready to perform a duet. A pump is used to
inflate or power a stage prop. If the pump is used too close to a delicate item,
it can tatter that item. The emotional turn is moral: the child must choose
whether to hide the damage or admit it, then fix it with help.

This world includes:
- physical state in meters: puff, tatter, shine, repair, clutter
- emotional state in memes: pride, worry, honesty, giggle, guilt, relief
- inner monologue as a story instrument
- a moral value theme centered on honesty, accountability, and repair

The generated story is intentionally small, concrete, and child-facing.
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    partner: object | None = None
    prize: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def inc_m(self, key: str, amt: float = 1.0) -> None:
        self.meters[key] = self.m(key) + amt

    def inc_e(self, key: str, amt: float = 1.0) -> None:
        self.memes[key] = self.e(key) + amt

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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


@dataclass
class Setting:
    place: str
    indoor: bool
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_tatter(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("puff", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.label in {"paper banner", "stage ribbon"}:
                if item.label == "paper banner" and not world.covered(actor, "torso"):
                    sig = ("tatter", actor.id, item.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    item.inc_m("tatter", 1)
                    item.inc_m("ruined", 1)
                    out.append(f"The {item.label} went into tatters.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("repair_kit"):
        banner = world.entities.get("banner")
        if banner and banner.m("tatter") >= THRESHOLD and banner.m("repair") < THRESHOLD:
            sig = ("repair", banner.id)
            if sig in world.fired:
                return out
            world.fired.add(sig)
            banner.inc_m("repair", 1)
            out.append("They patched the torn banner with tape and a cheerful sticker.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if hero and hero.memes.get("honesty", 0.0) >= THRESHOLD and hero.memes.get("guilt", 0.0) >= THRESHOLD:
        sig = ("relief", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.inc_e("relief", 1)
        hero.memes["guilt"] = 0.0
        out.append("The truth made the room feel lighter.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_tatter, _r_repair, _r_relief):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_tatter(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict[str, object]:
    sim = world.copy()
    sim.get(actor.id).inc_m("puff", 1)
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"tattered": bool(prize and prize.m("tatter") >= THRESHOLD)}


def choose_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fix in FIXES:
        if activity.mess in fix.guards and prize.region in fix.covers:
            return fix
    return None


SETTINGS = {
    "music_room": Setting(place="the music room", indoor=True, affords={"duet"}),
    "gym_stage": Setting(place="the gym stage", indoor=True, affords={"duet", "pump"}),
    "backyard_stage": Setting(place="the backyard stage", indoor=False, affords={"duet", "pump"}),
}

ACTIVITIES = {
    "duet": Activity(
        id="duet",
        verb="sing a duet",
        gerund="singing a duet",
        rush="start the duet too fast",
        mess="tatter",
        soil="all tattered",
        zone={"torso"},
        keyword="duet",
        tags={"music", "duet"},
    ),
    "pump": Activity(
        id="pump",
        verb="pump up the stage prop",
        gerund="pumping up the stage prop",
        rush="pump harder and harder",
        mess="tatter",
        soil="torn to tatters",
        zone={"torso"},
        keyword="pump",
        tags={"pump", "comedy"},
    ),
}

PRIZES = {
    "banner": Prize(
        label="banner",
        phrase="a shiny paper banner",
        type="banner",
        region="torso",
    ),
    "cape": Prize(
        label="cape",
        phrase="a bright costume cape",
        type="cape",
        region="torso",
    ),
    "poster": Prize(
        label="poster",
        phrase="a fancy song poster",
        type="poster",
        region="torso",
    ),
}

FIXES = [
    Fix(
        id="tape",
        label="tape",
        prep="grab some tape and a marker",
        tail="fixed the banner with tape and a doodle",
        guards={"tatter"},
        covers={"torso"},
    ),
    Fix(
        id="stapler",
        label="a stapler",
        prep="borrow a stapler from the teacher",
        tail="stapled the corner and smoothed it flat",
        guards={"tatter"},
        covers={"torso"},
    ),
]

NAMES = ["Mina", "Owen", "Nora", "Theo", "Lena", "Pip", "Zoe", "Max"]
TRAITS = ["goofy", "brave", "curious", "jumpy", "cheery"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    partner: str
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
        for aid in setting.affords:
            act = _safe_lookup(ACTIVITIES, aid)
            for pid, prize in PRIZES.items():
                if prize.region in act.zone and choose_fix(act, prize):
                    combos.append((place, aid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about a duet, a pump, and a tattered prop.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--partner")
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


def explain_rejection(act: Activity, prize: Prize) -> str:
    if prize.region not in act.zone:
        return f"(No story: {act.gerund} does not reach the {prize.label}, so it would not cause a real tatter problem.)"
    if not choose_fix(act, prize):
        return f"(No story: nothing in the fix catalog can patch a {prize.label} after {act.gerund}.)"
    return "(No story: invalid combination.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, prize = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if prize.region not in act.zone or not choose_fix(act, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    partner = getattr(args, "partner", None) or rng.choice([n for n in NAMES if n != name])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, partner=partner, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, partner_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name))
    partner = world.add(Entity(id="partner", kind="character", type="boy" if gender == "girl" else "girl", label=partner_name))
    prize = world.add(Entity(id="banner", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    world.add(Entity(id="pump", type="pump", label="pump"))
    world.facts["repair_kit"] = True

    world.say(f"{name} was a {trait} {gender} who loved the school talent show.")
    world.say(f"{name} and {partner_name} had a duet to sing, and they were trying very hard not to wobble the notes.")
    world.say(f"They also had a shiny paper banner, because every comedy needs one unnecessary shiny thing.")

    world.para()
    world.say(f"Before the duet, {name} tried to {activity.verb}.")
    world.say(f"{name}'s inner monologue went, \"Easy, easy... just one little pump. What could possibly go wrong?\"")
    hero.inc_m("puff", 1)
    world.zone = set(activity.zone)
    if prize.region in activity.zone:
        prop = world.get("banner")
        prop.inc_m("tatter", 1)
        world.say("The pump blew a silly gust across the banner, and the paper went flutter-flutter into tatters.")
        hero.inc_e("worry", 1)
        hero.inc_e("guilt", 1)
        world.say(f"{name} thought, \"Oh crumbs. That was my idea. I should say so.\"")

    world.para()
    world.say(f"{name} took a breath and told the truth to {partner_name} and the teacher.")
    hero.inc_e("honesty", 1)
    propagate(world, narrate=True)

    fix = choose_fix(activity, prize_cfg)
    if fix:
        world.say(f"They did not panic. Instead, they decided to {fix.prep}.")
        world.say(f"{name}'s inner monologue cheered, \"Aha! A fix is a much better trick than a fib.\"")
        world.say(f"Together they {fix.tail}.")
        world.get("banner").meters["repair"] = 1

    world.para()
    hero.inc_e("relief", 1)
    world.say(f"At last, {name} and {partner_name} sang their duet anyway, and the audience laughed at the tiny patched banner waving like a proud flag.")
    world.say(f"{name} felt much better after telling the truth, because being honest turned the trouble into a joke instead of a secret.")
    world.facts.update(hero=hero, partner=partner, prize=prize, activity=activity, setting=setting, fix=fix)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    partner = _safe_fact(world, f, "partner")
    activity = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short comedy story for a young child about a "{activity.keyword}" moment, a tattered {prize.label}, and a duet.',
        f"Tell a gentle story where {hero.label} and {partner.label} prepare a duet, use a pump, and then choose honesty after something gets torn.",
        f'Write a simple story that includes the words "pump", "tatter", and "duet" and ends with a kind repair.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    partner: Entity = _safe_fact(world, f, "partner")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    qa = [
        QAItem(
            question=f"What were {hero.label} and {partner.label} trying to do?",
            answer=f"They were getting ready to sing a duet together.",
        ),
        QAItem(
            question=f"What did {hero.label} use that caused the trouble?",
            answer=f"{hero.label} used a pump, and the air puffed the paper banner into tatters.",
        ),
        QAItem(
            question=f"What did {hero.label} think about in the middle of the problem?",
            answer=f"{hero.label}'s inner monologue was to tell the truth instead of hiding the damage.",
        ),
        QAItem(
            question=f"How did they fix the torn {prize.label}?",
            answer=f"They used tape and a marker, so the {prize.label} could still be part of the show.",
        ),
        QAItem(
            question=f"What moral value does the story show?",
            answer="It shows honesty and responsibility, because admitting a mistake helped everyone solve it kindly.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pump?",
            answer="A pump is a tool that pushes air or liquid from one place to another.",
        ),
        QAItem(
            question="What does tatter mean?",
            answer="To tatter something means to tear it into ragged pieces or make it look torn.",
        ),
        QAItem(
            question="What is a duet?",
            answer="A duet is a song or performance by two people together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    bits = ["--- world ---"]
    for e in list(world.entities.values()):
        bits.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(bits)


ASP_RULES = r"""
at_risk(A,P) :- splashes(A,R), worn_on(P,R).
can_fix(A,P) :- at_risk(A,P), fix(F), guards(F,M), mess_of(A,M), covers(F,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), at_risk(A,P), can_fix(A,P).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in s.affords:
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in a.zone:
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for f in FIXES:
        lines.append(asp.fact("fix", f.id))
        for g in f.guards:
            lines.append(asp.fact("guards", f.id, g))
        for c in f.covers:
            lines.append(asp.fact("covers", f.id, c))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.partner, params.trait)
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
    StoryParams(place="music_room", activity="pump", prize="banner", name="Mina", gender="girl", partner="Owen", trait="goofy"),
    StoryParams(place="gym_stage", activity="duet", prize="cape", name="Theo", gender="boy", partner="Lena", trait="cheery"),
    StoryParams(place="backyard_stage", activity="pump", prize="poster", name="Zoe", gender="girl", partner="Max", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program())
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, prize = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if prize.region not in act.zone or not choose_fix(act, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    partner = getattr(args, "partner", None) or rng.choice([n for n in NAMES if n != name])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, partner=partner, trait=trait)


if __name__ == "__main__":
    main()
