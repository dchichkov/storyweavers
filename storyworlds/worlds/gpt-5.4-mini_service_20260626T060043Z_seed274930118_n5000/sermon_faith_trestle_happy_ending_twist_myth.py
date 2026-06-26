#!/usr/bin/env python3
"""
storyworlds/worlds/sermon_faith_trestle_happy_ending_twist_myth.py
==================================================================

A small myth-style story world about a sermon, faith, and a trestle.

Seed tale:
---
At dawn, a young pilgrim heard a sermon on the hill. The elder spoke of faith,
of crossing the broken trestle, and of the river below. The pilgrim feared the
wind and the creak of old boards.

Then came a twist: the trestle was not cursed at all. It was only loose rope
and weathered wood, and the elder knew a safer way. With faith and a careful
hand, the pilgrim crossed, found the lantern shrine, and the village cheered.

World model:
---
- The sermon raises faith and steadies fear.
- The trestle can sway when crossed.
- A rope and lantern can make the crossing safe if the pilgrim trusts the elder.
- The twist is that the danger is natural, not magical: old boards, wind, and
  shadows.
- The ending is happy when the pilgrim reaches the shrine and returns with hope.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    meme_count: int = 0
    elder: object | None = None
    hero: object | None = None
    lantern: object | None = None
    rope: object | None = None
    shrine: object | None = None
    trestle: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "priestess"}
        male = {"boy", "man", "father", "brother", "priest"}
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
    indoors: bool = False
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
    weather: str
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
class Fix:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
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
    fix: str
    name: str
    gender: str
    elder: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.twist_revealed: bool = False

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.twist_revealed = self.twist_revealed
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    RULES: list = field(default_factory=list)
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


def _r_sermon(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("heard_sermon", 0) < THRESHOLD:
            continue
        sig = ("sermon", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["faith"] = hero.memes.get("faith", 0) + 1
        hero.memes["fear"] = max(0, hero.memes.get("fear", 0) - 1)
        out.append(f"The words settled in {hero.id}'s heart like warm bread.")
    return out


def _r_crossing(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        trestle = world.entities.get("trestle")
        if not trestle:
            continue
        if hero.meters.get("crossing", 0) < THRESHOLD:
            continue
        sig = ("cross", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        trestle.meters["sway"] = trestle.meters.get("sway", 0) + 1
        if hero.memes.get("faith", 0) >= THRESHOLD:
            out.append("The old boards groaned, but the pilgrim kept the steps small and sure.")
        else:
            hero.memes["fear"] = hero.memes.get("fear", 0) + 1
            out.append("The trestle shivered, and the pilgrim's knees went weak.")
    return out


RULES = [Rule("sermon", _r_sermon), Rule("crossing", _r_crossing)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_crossing(world: World, hero: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["crossing"] = 1
    propagate(sim, narrate=False)
    trestle = sim.get("trestle")
    return {
        "sway": trestle.meters.get("sway", 0),
        "safe": sim.get(hero.id).memes.get("fear", 0) < 1,
    }


def setting_detail(setting: Setting) -> str:
    if setting.place == "the hill":
        return "The hill stood above the river, and the wind carried the smell of pine."
    if setting.place == "the shrine road":
        return "The road bent toward the shrine, where bells rang faintly in the morning."
    return f"{setting.place.capitalize()} waited in the bright, quiet air."


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    world.facts["params"] = params
    world.facts["activity"] = _safe_lookup(ACTIVITIES, params.activity)
    world.facts["fix"] = _safe_lookup(FIXES, params.fix)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meme_count=0,
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder,
        label=f"the {params.elder}",
    ))
    trestle = world.add(Entity(
        id="trestle",
        type="trestle",
        label="the trestle",
        meters={"sway": 0},
    ))
    shrine = world.add(Entity(
        id="shrine",
        type="shrine",
        label="the lantern shrine",
    ))
    rope = world.add(Entity(
        id="rope",
        type="rope",
        label="a braided rope",
        protective=True,
        covers={"crossing"},
        owner=elder.id,
    ))
    lantern = world.add(Entity(
        id="lantern",
        type="lantern",
        label="a small lantern",
        protective=True,
        covers={"dark"},
        owner=elder.id,
    ))

    hero.memes["fear"] = 1
    elder.memes["calm"] = 1

    world.say(f"{params.name} was a young {params.trait} {params.gender} who listened for old wisdom.")
    world.say(f"{params.name} loved to {_safe_lookup(ACTIVITIES, params.activity).gerund} when the day turned bright.")
    world.say(f"At dawn, {params.name} and {elder.label} came to {setting.place}.")
    world.say(setting_detail(setting))

    world.para()
    world.say(f"{elder.label} gave a sermon about faith, and the voice was steady as a drum.")
    hero.memes["heard_sermon"] = 1
    propagate(world)
    world.say(f"{params.name} wanted to {_safe_lookup(ACTIVITIES, params.activity).verb}, but the trestle looked old and high.")

    world.para()
    pred = predict_crossing(world, hero)
    world.facts["pred"] = pred
    if pred["sway"] > 0:
        world.say(f"The twist came with the wind: the trestle was not cursed at all, only worn by weather and time.")
    else:
        world.say("The elder smiled, because the way ahead was harder to see than it truly was.")
    world.say(f"{params.name} reached for the braided rope, and {elder.label} held up the lantern.")
    world.say(f'"Take the safe steps," {elder.label} said, "and trust what you have heard."')

    if params.fix == "rope":
        rope.worn_by = params.name
    if params.fix == "lantern":
        lantern.worn_by = elder.id
    hero.meters["crossing"] = 1
    hero.memes["faith"] = hero.memes.get("faith", 0) + 1
    propagate(world)

    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f"{params.name} crossed the trestle in careful steps, and the boards answered with a low song.")
    world.say(f"On the other side stood the lantern shrine, bright as a promise kept.")
    world.say(f"{params.name} laughed, and the river below seemed smaller than fear.")
    world.say(f"In the end, faith had been enough to carry {params.name} across.")

    world.facts.update(hero=hero, elder=elder, trestle=trestle, shrine=shrine, rope=rope, lantern=lantern)
    return world


SETTINGS = {
    "hill": Setting(place="the hill", affords={"sermon", "crossing"}),
    "riverbank": Setting(place="the riverbank", affords={"sermon", "crossing"}),
    "temple_path": Setting(place="the temple path", affords={"sermon", "crossing"}),
}

ACTIVITIES = {
    "sermon": Activity(
        id="sermon",
        verb="listen to the sermon",
        gerund="listening to sermons",
        rush="hurry toward the elder",
        weather="clear",
        keyword="sermon",
        tags={"faith", "speech"},
    ),
    "crossing": Activity(
        id="crossing",
        verb="cross the trestle",
        gerund="crossing trestles",
        rush="run onto the trestle",
        weather="windy",
        keyword="trestle",
        tags={"trestle", "wind", "fear"},
    ),
}

FIXES = {
    "rope": Fix(
        id="rope",
        label="braided rope",
        phrase="a braided rope",
        prep="use the braided rope for the crossing",
        tail="kept one hand on the rope and one eye on the lantern",
        guards={"falling"},
        covers={"crossing"},
    ),
    "lantern": Fix(
        id="lantern",
        label="lantern",
        phrase="a small lantern",
        prep="carry a lantern to light the way",
        tail="followed the light until the far side appeared",
        guards={"dark"},
        covers={"dark"},
    ),
}

GIRL_NAMES = ["Asha", "Mina", "Liora", "Nia", "Sera"]
BOY_NAMES = ["Arin", "Taro", "Darin", "Bren", "Oren"]
TRAITS = ["brave", "quiet", "curious", "patient", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for fix_id in FIXES:
                combos.append((place, act, fix_id))
    return combos


def explain_rejection(place: str, activity: str, fix: str) -> str:
    return f"(No story: the chosen tale cannot be built from {place}, {activity}, and {fix}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-style story world about sermon, faith, and a trestle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["priest", "priestess"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, fix = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    elder = getattr(args, "elder", None) or rng.choice(["priestess", "priest"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, fix=fix, name=name, gender=gender, elder=elder, trait=trait)


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    act = _safe_fact(world, world.facts, "activity")
    fix = _safe_fact(world, world.facts, "fix")
    return [
        f'Write a short myth for a young child about "{act.keyword}", "{fix.label}", and faith.',
        f"Tell a gentle legend where {p.name} hears a sermon, fears a trestle, and finds a happy ending.",
        f"Write a simple story with a twist in which the trestle seems dangerous, but wisdom makes the crossing safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    hero: Entity = _safe_fact(world, world.facts, "hero")
    elder: Entity = _safe_fact(world, world.facts, "elder")
    act: Activity = _safe_fact(world, world.facts, "activity")
    fix: Fix = _safe_fact(world, world.facts, "fix")
    return [
        QAItem(
            question=f"What did {p.name} hear before crossing the trestle?",
            answer=f"{p.name} heard a sermon from {elder.label}, and the words helped build faith in {hero.pronoun('possessive')} heart.",
        ),
        QAItem(
            question=f"Why was the trestle a problem in the story?",
            answer="The trestle was old and high, and the wind made it seem frightening. The twist was that it was weathered, not cursed.",
        ),
        QAItem(
            question=f"What helped {p.name} reach the other side safely?",
            answer=f"{elder.label} gave {p.name} {fix.phrase}, and {p.name} crossed with faith instead of panic.",
        ),
        QAItem(
            question=f"What was the happy ending?",
            answer=f"{p.name} reached the lantern shrine, smiled, and returned with hope. The village had a brave new story to tell.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sermon?",
            answer="A sermon is a spoken lesson or talk, often about how to live well and be brave or kind.",
        ),
        QAItem(
            question="What is faith?",
            answer="Faith is trust in something good, even when the way ahead feels uncertain.",
        ),
        QAItem(
            question="What is a trestle?",
            answer="A trestle is a bridge or support made from beams and wood, often used to cross water or a gap.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- person(H).
faithful(H) :- heard_sermon(H).
safe_cross(H) :- faithful(H), has_fix(H).

twist(T) :- trestle(T), old(T), windy_day.
happy_ending(H) :- safe_cross(H), reached_shrine(H).

valid_story(Place, Activity, Fix) :- setting(Place), affords(Place, Activity), usable_fix(Activity, Fix).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for act_id in ACTIVITIES:
        lines.append(asp.fact("activity", act_id))
    for fix_id in FIXES:
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("usable_fix", "crossing", fix_id))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="hill", activity="sermon", fix="rope", name="Asha", gender="girl", elder="priestess", trait="steady"),
    StoryParams(place="riverbank", activity="crossing", fix="lantern", name="Arin", gender="boy", elder="priest", trait="curious"),
    StoryParams(place="temple_path", activity="crossing", fix="rope", name="Mina", gender="girl", elder="priestess", trait="brave"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, fix) combos:\n")
        for t in combos:
            print("  ", t)
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
            header = f"### {p.name}: {p.activity} at {p.place} (fix: {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
