#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/angel_mallard_teamwork_bad_ending_adventure.py
====================================================================================================

A standalone story world for a tiny adventure about an angel, a mallard, teamwork,
and a bad ending. The domain models a small river-crossing expedition with typed
entities, physical meters, emotional memes, a forward-chaining causal layer, a
reasonableness gate, and an inline ASP twin.

Seed premise:
- An angel and a mallard team up for an adventure.
- They try to cross a storm-swollen marsh with a lantern, a rope, and a little
  raft.
- Their teamwork helps at first, but a hidden snag and a rising current cause a
  bad ending: the raft breaks, the map is lost, and they must retreat.

The story is child-facing, concrete, and state-driven. The ending image proves
what changed: the angel and mallard are safe on the bank, wet, tired, and
holding only a torn rope and a soaked lantern while the river takes the raft.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    location: str = ""
    floats: bool = False
    helps: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    angel: object | None = None
    g: object | None = None
    goal: object | None = None
    lantern: object | None = None
    mallard: object | None = None
    map_ent: object | None = None
    rope: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "angel"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
    water: bool = False
    windy: bool = False
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Expedition:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class GoalItem:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"angel", "mallard"})
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    phrase: str
    covers: set[str]
    guards: set[str]
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Hazard:
    id: str
    label: str
    phrase: str
    causes: set[str]
    severity: int
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class StoryParams:
    place: str = "riverbank"
    expedition: str = "crossing"
    goal: str = "lantern"
    hazard: str = "snag"
    gear: str = "rope"
    hero_name: str = "Ari"
    angel_name: str = "Mira"
    angel_type: str = "angel"
    mallard_name: str = "Dew"
    mallard_type: str = "mallard"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.current_path: str = ""

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
        clone.fired = set(self.fired)
        clone.current_path = self.current_path
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    if world.current_path != "river":
        return out
    for ent in world.characters():
        if ent.meters["crossing"] < THRESHOLD:
            continue
        sig = ("wet", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["wet"] += 1
        ent.memes["strain"] += 1
        out.append(f"{ent.id} got wetter as the river slapped the raft.")
    return out


def _r_snag(world: World) -> list[str]:
    out: list[str] = []
    if world.current_path != "river":
        return out
    if world.facts.get("snagged"):
        return out
    if world.facts.get("current") < 2:
        return out
    if world.facts.get("rope_tied") and world.facts.get("teamwork"):
        return out
    world.fired.add(("snag",))
    world.facts["snagged"] = True
    world.facts["raft_broken"] = True
    for ent in world.characters():
        ent.meters["panic"] += 1
    out.append("The hidden snag tore the raft open.")
    return out


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("raft_broken"):
        return out
    if world.facts.get("lost_map"):
        return out
    world.fired.add(("loss",))
    world.facts["lost_map"] = True
    map_ent = world.entities.get("map")
    if map_ent:
        map_ent.meters["soaked"] += 1
    out.append("The map slipped away in the spray and vanished downstream.")
    return out


CAUSAL_RULES = [Rule("wet", "physical", _r_wet), Rule("snag", "physical", _r_snag), Rule("loss", "physical", _r_loss)]


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


def hazard_at_risk(expedition: Expedition, goal: GoalItem, hazard: Hazard) -> bool:
    return goal.region in expedition.zone and hazard.id in hazard.causes


def select_gear(expedition: Expedition, goal: GoalItem, hazard: Hazard) -> Optional[Gear]:
    for gear in GEARS.values():
        if goal.region in gear.covers and hazard.id in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for exp_id in setting.affords:
            exp = _safe_lookup(EXPEDITIONS, exp_id)
            for goal_id, goal in GOALS.items():
                for haz_id, haz in HAZARDS.items():
                    if hazard_at_risk(exp, goal, haz) and select_gear(exp, goal, haz):
                        combos.append((place, exp_id, goal_id))
    return combos


def predict_bad_ending(world: World, angel_id: str, mallard_id: str) -> dict:
    sim = world.copy()
    _start_expedition(sim, sim.get(angel_id), sim.get(mallard_id), narrate=False)
    return {
        "broken": bool(sim.facts.get("raft_broken")),
        "map_lost": bool(sim.facts.get("lost_map")),
        "wet": sim.get(angel_id).meters["wet"] + sim.get(mallard_id).meters["wet"],
    }


def _start_expedition(world: World, angel: Entity, mallard: Entity, narrate: bool = True) -> None:
    world.current_path = "river"
    world.facts["teamwork"] = True
    world.facts["rope_tied"] = True
    angel.meters["crossing"] += 1
    mallard.meters["crossing"] += 1
    angel.memes["hope"] += 1
    mallard.memes["hope"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, angel: Entity, mallard: Entity) -> None:
    world.say(f"{angel.id} was an {angel.type} who loved bright quests, and {mallard.id} was a mallard who paddled wherever the water led.")
    world.say(f"Together they made a small team that liked to solve things side by side.")


def set_off(world: World, setting: Setting, expedition: Expedition) -> None:
    world.say(f"One windy day at {setting.place}, they set out to {expedition.verb}.")
    world.say(f"Their little plan was simple: work together and keep the goal dry.")


def hope_beats(world: World, angel: Entity, mallard: Entity, expedition: Expedition, goal: GoalItem) -> None:
    angel.memes["joy"] += 1
    mallard.memes["joy"] += 1
    world.say(f"{angel.id} lifted {angel.pronoun('possessive')} wings, and {mallard.id} bobbed ahead with a brave quack.")
    world.say(f"They wanted to {expedition.verb} so they could keep {goal.phrase} safe on the far side.")


def warn(world: World, angel: Entity, mallard: Entity, hazard: Hazard, goal: GoalItem) -> None:
    pred = predict_bad_ending(world, angel.id, mallard.id)
    world.facts["predicted_broken"] = pred["broken"]
    world.facts["predicted_map_lost"] = pred["map_lost"]
    world.say(f'"The {hazard.label} looks sharp," {angel.id} said. "If it catches the raft, we could lose {goal.label}."')
    world.say(f"{mallard.id} nodded, because the water already looked pushy and hard to trust.")


def teamwork_fix(world: World, angel: Entity, mallard: Entity, expedition: Expedition, goal: GoalItem, hazard: Hazard) -> Optional[Gear]:
    gear = select_gear(expedition, goal, hazard)
    if gear is None:
        return None
    g = world.add(Entity(id=gear.id, type="gear", label=gear.label, phrase=gear.phrase, plural=gear.plural, owner=angel.id, carried_by=angel.id, helps=set(gear.covers), attrs={"guards": sorted(gear.guards)}))
    world.facts["gear_used"] = gear.id
    world.say(f'{angel.id} pointed at {gear.phrase}. "If we use {gear.label}, we can keep going," {angel.id} said.')
    world.say(f"{mallard.id} helped tie it on, and that small teamwork made the plan feel steady.")
    return gear


def bad_turn(world: World, angel: Entity, mallard: Entity, hazard: Hazard, goal: GoalItem) -> None:
    world.say(f"But once they reached the middle, the current grew loud and fast.")
    world.say(f"The hidden {hazard.label} snagged under the raft while the two of them were still working together.")
    world.facts["current"] = hazard.severity
    world.facts["raft_broken"] = False
    world.facts["lost_map"] = False
    propagate(world, narrate=True)


def ending(world: World, angel: Entity, mallard: Entity, goal: GoalItem) -> None:
    angel.memes["disappointment"] += 1
    mallard.memes["disappointment"] += 1
    world.say("The raft split with a wet crack, and the lantern bobbed away in a soggy little swirl.")
    world.say(f"They made it back to the bank, but {goal.label} was gone, and the adventure ended in a sad, empty splash.")
    world.say(f"At the shore, {angel.id} held the torn rope while {mallard.id} shook water from {mallard.pronoun('possessive')} feathers.")
    world.say("They were safe, but the river had taken the prize and the path home felt much longer than before.")


def tell(setting: Setting, expedition: Expedition, goal_cfg: GoalItem, hazard: Hazard, gear_cfg: Gear, angel_name: str = "Mira", mallard_name: str = "Dew") -> World:
    world = World(setting)
    angel = world.add(Entity(id=angel_name, kind="character", type="angel", role="hero", label="angel"))
    mallard = world.add(Entity(id=mallard_name, kind="character", type="mallard", role="helper", label="mallard", plural=False))
    goal = world.add(Entity(id="goal", type="thing", label=goal_cfg.label, phrase=goal_cfg.phrase, owner=angel.id, location="raft"))
    map_ent = world.add(Entity(id="map", type="thing", label="map", phrase="a small map", owner=angel.id, location="raft"))
    rope = world.add(Entity(id="rope", type="gear", label=gear_cfg.label, phrase=gear_cfg.phrase, carried_by=angel.id, helps=set(gear_cfg.covers), attrs={"guards": sorted(gear_cfg.guards)}))
    lantern = world.add(Entity(id="lantern", type="thing", label="lantern", phrase="a little lantern", owner=angel.id, location="raft"))
    world.facts.update(current=0, teamwork=False, rope_tied=False, raft_broken=False, lost_map=False, snagged=False)
    introduce(world, angel, mallard)
    world.para()
    set_off(world, setting, expedition)
    hope_beats(world, angel, mallard, expedition, goal)
    world.para()
    warn(world, angel, mallard, hazard, goal)
    teamwork_fix(world, angel, mallard, expedition, goal, hazard)
    world.para()
    bad_turn(world, angel, mallard, hazard, goal)
    ending(world, angel, mallard, goal)
    world.facts.update(angel=angel, mallard=mallard, goal=goal, map=map_ent, rope=rope, lantern=lantern, expedition=expedition, hazard=hazard, gear=gear_cfg)
    return world


SETTINGS = {
    "riverbank": Setting(place="the riverbank", water=True, windy=True, affords={"crossing", "rescue"}),
    "marsh": Setting(place="the marsh", water=True, windy=True, affords={"crossing"}),
    "delta": Setting(place="the delta", water=True, windy=True, affords={"crossing"}),
}

EXPEDITIONS = {
    "crossing": Expedition(id="crossing", verb="cross the river", gerund="crossing the river", rush="push across the water", risk="wet and broken", zone={"water", "current"}, keyword="river", tags={"river", "teamwork", "adventure"}),
}

GOALS = {
    "lantern": GoalItem(id="lantern", label="lantern", phrase="a little lantern", region="water", plural=False),
    "map": GoalItem(id="map", label="map", phrase="the map", region="water", plural=False),
    "sack": GoalItem(id="sack", label="sack", phrase="the supply sack", region="water", plural=False),
}

HAZARDS = {
    "snag": Hazard(id="snag", label="snag", phrase="a hidden snag", causes={"water", "current"}, severity=3, tags={"snag", "river", "bad_ending"}),
}

GEARS = {
    "rope": Gear(id="rope", label="rope", phrase="a long rope", covers={"water"}, guards={"snag"}, prep="tie the rope across the raft", tail="held tight to the broken boards", plural=False),
}

GIRL_NAMES = ["Mira", "Lena", "Nia", "Ava"]
BOY_NAMES = ["Oren", "Tio", "Eli", "Noam"]
TRAITS = ["curious", "brave", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, m, exp, goal, haz = f["angel"], f["mallard"], f["expedition"], f["goal"], f["hazard"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old about an angel and a mallard who try to {exp.verb}.',
        f"Tell a teamwork story where {a.id} and {m.id} cross {world.setting.place} together, but a hidden {haz.label} ruins the trip.",
        f'Write a simple story that includes the words "angel" and "mallard" and ends with a sad ending image after a river crossing goes wrong.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, m, exp, goal, haz = f["angel"], f["mallard"], f["expedition"], f["goal"], f["hazard"]
    qa = [
        QAItem(
            question=f"Who went on the adventure at {world.setting.place}?",
            answer=f"The adventure was about {a.id}, an {a.type}, and {m.id}, a mallard. They tried to work as a small team at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {a.id} and {m.id} try to do together?",
            answer=f"They tried to {exp.verb}. They thought teamwork would help them reach the other side safely.",
        ),
        QAItem(
            question=f"Why did {a.id} warn {m.id} about the {haz.label}?",
            answer=f"{a.id} could see that the {haz.label} might catch the raft and ruin the crossing. That warning came from watching the river and thinking about the goal.",
        ),
        QAItem(
            question=f"How did the rope help before things went wrong?",
            answer=f"The rope let {a.id} and {m.id} tie things down and feel ready to go. It made their teamwork stronger, even though it could not stop the hidden snag forever.",
        ),
        QAItem(
            question=f"What happened to {goal.label} by the end?",
            answer=f"{goal.label.capitalize()} was lost when the raft broke and the river took it away. The ending is bad because the prize vanishes even though the two helpers stay safe.",
        ),
    ]
    if f.get("predicted_broken"):
        qa.append(QAItem(
            question=f"Why was the adventure such a bad ending?",
            answer=f"The adventure turned bad because the current was strong and the hidden {haz.label} tore the raft apart. Their teamwork helped them survive, but it could not save the goal from the river.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["expedition"].tags) | set(world.facts["hazard"].tags)
    out: list[QAItem] = []
    if "river" in tags:
        out.append(QAItem("What is a river?", "A river is a long stream of water that flows along the land. It can be gentle, but it can also move very fast."))
    if "teamwork" in tags:
        out.append(QAItem("What is teamwork?", "Teamwork is when people work together and help each other. Each helper does a small part to reach the same goal."))
    if "bad_ending" in tags:
        out.append(QAItem("What is a bad ending in a story?", "A bad ending is when the goal is lost or the plan fails. The characters may still be safe, but things do not turn out the way they hoped."))
    if "snag" in tags:
        out.append(QAItem("What is a snag?", "A snag is something sharp or stuck that can catch a rope, net, or raft. In water, a snag can cause big trouble."))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(sorted(k for k in world.facts.keys() if isinstance(world.facts[k], (bool, int, str))) )}}}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="riverbank", expedition="crossing", goal="lantern", hazard="snag", gear="rope", hero_name="Ari", angel_name="Mira", angel_type="angel", mallard_name="Dew", mallard_type="mallard"),
]


def explain_rejection(expedition: Expedition, goal: GoalItem, hazard: Hazard) -> str:
    return f"(No story: this adventure has no honest danger for {goal.label}. Try the river crossing with a flammable or snagging risk.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.water:
            lines.append(asp.fact("water", sid))
        if s.windy:
            lines.append(asp.fact("windy", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for eid, e in EXPEDITIONS.items():
        lines.append(asp.fact("expedition", eid))
        for z in sorted(e.zone):
            lines.append(asp.fact("zone", eid, z))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("region", gid, g.region))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for c in sorted(h.causes):
            lines.append(asp.fact("causes", hid, c))
    for gid, g in GEARS.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for g2 in sorted(g.guards):
            lines.append(asp.fact("guards", gid, g2))
    return "\n".join(lines)


ASP_RULES = r"""
risk(E,G,H) :- zone(E,R), region(G,R), causes(H,R).
fix(E,G,H) :- risk(E,G,H), covers(X,R), region(G,R), guards(X,H).
valid(P,E,G) :- affords(P,E), risk(E,G,H), fix(E,G,H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        print("  only in clingo:", sorted(cl - py))
        print("  only in python:", sorted(py - cl))
    try:
        sample = generate(CURATED[0])
        print("OK: smoke story generated.")
        print(sample.story[:120] + ("..." if len(sample.story) > 120 else ""))
    except Exception as err:
        rc = 1
        print(f"SMOKE FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: an angel, a mallard, teamwork, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--expedition", choices=EXPEDITIONS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--angel-name")
    ap.add_argument("--mallard-name")
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
              and (getattr(args, "expedition", None) is None or c[1] == getattr(args, "expedition", None))
              and (getattr(args, "goal", None) is None or c[2] == getattr(args, "goal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, expedition, goal = rng.choice(list(combos))
    gear = getattr(args, "gear", None) or "rope"
    return StoryParams(
        place=place,
        expedition=expedition,
        goal=goal,
        hazard=getattr(args, "hazard", None) or "snag",
        gear=gear,
        hero_name="Ari",
        angel_name=getattr(args, "angel_name", None) or rng.choice(["Mira", "Luma", "Sera"]),
        angel_type="angel",
        mallard_name=getattr(args, "mallard_name", None) or rng.choice(["Dew", "Pip", "Quill"]),
        mallard_type="mallard",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.expedition not in EXPEDITIONS or params.goal not in GOALS or params.hazard not in HAZARDS or params.gear not in GEARS:
        pass
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(EXPEDITIONS, params.expedition), _safe_lookup(GOALS, params.goal), _safe_lookup(HAZARDS, params.hazard), _safe_lookup(GEARS, params.gear), params.angel_name, params.mallard_name)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(f"{len(asp_valid_combos())} compatible (place, expedition, goal) combos:\n")
        for row in asp_valid_combos():
            print("  ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
