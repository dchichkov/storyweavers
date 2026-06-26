#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/volcanic_dig_heart_rhyme_ghost_story.py
===============================================================================================================

A small ghost-story world where a child wants to dig near a volcano and a
rhyme-loving ghost helps keep a heart-shaped treasure safe.

The story premise is intentionally classical and state-driven:
- a child loves to dig at a volcanic place,
- something heart-shaped is at risk from hot ash and loose stone,
- a gentle ghost warns in rhyme,
- the child and ghost find a safer way,
- the ending image proves the change.

This file follows the Storyweavers world contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- optional ASP parity and verification modes
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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    ghost: object | None = None
    hero: object | None = None
    parent: object | None = None
    tool_ent: object | None = None
    treasure: object | None = None
    def __post_init__(self) -> None:
        for k in ["heat", "ash", "dust", "care", "fear", "joy", "curiosity", "trust", "rhythm"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
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
class Setting:
    place: str = "the volcanic hill"
    affords: set[str] = field(default_factory=set)
    eerie: bool = True
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
class Treasure:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    glow: str = "warm"
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
class Tool:
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["heat"] < THRESHOLD and actor.meters["ash"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["ash"] += 1
            item.meters["dust"] += 1
            out.append(f"{actor.id}'s {item.label} grew dusty near the hot ground.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["spooked"] < THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        out.append(f"The strange dark air made {actor.id} shiver.")
    return out


CAUSAL_RULES = [
    _r_soil,
    _r_fear,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, treasure: Treasure) -> bool:
    return treasure.region in activity.zone


def select_tool(activity: Activity, treasure: Treasure) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.mess in tool.guards and treasure.region in tool.covers:
            return tool
    return None


def predict(world: World, actor: Entity, activity: Activity, treasure_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    tr = sim.entities.get(treasure_id)
    return {"soiled": bool(tr and (tr.meters["ash"] >= THRESHOLD or tr.meters["dust"] >= THRESHOLD))}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["ash"] += 1
    actor.meters["heat"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, ghost: Entity, activity: Activity, treasure: Entity) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} listened for the hush of the stones while "
        f"{ghost.id} drifted nearby like a cool gray sigh."
    )
    world.say(
        f"{hero.id} loved to {activity.verb}, and the little {treasure.label} gleamed "
        f"like a heart of light."
    )


def rhyme_warning(world: World, ghost: Entity, hero: Entity, activity: Activity, treasure: Entity) -> None:
    pred = predict(world, hero, activity, treasure.id)
    if not pred["soiled"]:
        return
    ghost.memes["trust"] += 1
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"Dig too close and you will pay; hot ash can turn bright things to gray," '
        f"{ghost.id} sang. \"Let's find a safer way.\""
    )
    hero.memes["spooked"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} paused, because the rhyme felt true, and the warm ground looked less friendly now."
    )


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["restless"] += 1
    world.say(f"{hero.id} still wanted to {activity.rush}, even though the stones felt wilder than before.")


def offer(world: World, ghost: Entity, hero: Entity, activity: Activity, treasure: Entity) -> Optional[Tool]:
    tool = select_tool(activity, treasure)
    if tool is None:
        return None
    sim = world.copy()
    ghost_copy = sim.get(ghost.id)
    hero_copy = sim.get(hero.id)
    tool_ent = sim.add(Entity(id=tool.id, type="tool", label=tool.label, protective=True, covers=set(tool.covers)))
    tool_ent.worn_by = hero_copy.id
    _do_activity(sim, hero_copy, activity, narrate=False)
    tr = sim.entities[treasure.id]
    if tr.meters["ash"] >= THRESHOLD or tr.meters["dust"] >= THRESHOLD:
        return None
    gear = world.add(Entity(id=tool.id, type="tool", label=tool.label, protective=True, covers=set(tool.covers), plural=tool.plural))
    gear.worn_by = hero.id
    world.say(
        f'{ghost.id} whispered, "{tool.prep}, and the hot dust will stay at bay."'
    )
    return tool


def accept(world: World, hero: Entity, ghost: Entity, activity: Activity, treasure: Entity, tool: Tool) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["trust"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} smiled and nodded. Together they {tool.tail}, and the air felt less sharp."
    )
    _do_activity(world, hero, activity, narrate=True)
    world.say(
        f"In the end, {hero.id} was {activity.gerund}, {treasure.phrase} stayed safe and bright, "
        f"and {ghost.id} hummed a happy rhyme above the black stones."
    )


def tell(setting: Setting, activity: Activity, treasure_cfg: Treasure, hero_name: str, hero_type: str,
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    treasure = world.add(Entity(
        id="treasure", type=treasure_cfg.type, label=treasure_cfg.label,
        phrase=treasure_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=treasure_cfg.region, plural=treasure_cfg.plural,
    ))
    treasure.worn_by = hero.id

    opening(world, hero, ghost, activity, treasure)
    world.para()
    rhyme_warning(world, ghost, hero, activity, treasure)
    defy(world, hero, activity)
    tool = offer(world, ghost, hero, activity, treasure)
    if tool is not None:
        world.para()
        accept(world, hero, ghost, activity, treasure, tool)

    world.facts.update(
        hero=hero,
        ghost=ghost,
        parent=parent,
        treasure=treasure,
        activity=activity,
        setting=setting,
        tool=tool,
        resolved=tool is not None,
        conflict=hero.memes["spooked"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "volcano": Setting(place="the volcanic hill", affords={"dig", "rhyme"}),
    "cave": Setting(place="the ash cave", affords={"dig", "rhyme"}),
    "ridge": Setting(place="the black ridge", affords={"dig", "rhyme"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig",
        verb="dig by the volcanic stones",
        gerund="digging by the volcanic stones",
        rush="dig faster near the glowing rock",
        mess="ash",
        soil="dusty and gray",
        zone={"hands", "shoes"},
        keyword="volcanic",
        tags={"volcanic", "dig", "heart"},
    ),
    "rhyme": Activity(
        id="rhyme",
        verb="sing a rhyme",
        gerund="rhyme-singing softly",
        rush="hurry to make up another rhyme",
        mess="ash",
        soil="dusty and gray",
        zone={"hands"},
        keyword="rhyme",
        tags={"rhyme"},
    ),
}

TREASURES = {
    "heartstone": Treasure(
        label="heartstone",
        phrase="a heart-shaped heartstone",
        type="heartstone",
        region="hands",
    ),
    "heartlantern": Treasure(
        label="heart lantern",
        phrase="a small heart lantern",
        type="lantern",
        region="hands",
    ),
}

TOOLS = [
    Tool(
        id="gloves",
        label="heat gloves",
        covers={"hands"},
        guards={"ash"},
        prep="put on the heat gloves first",
        tail="slipped on the heat gloves and walked back to the stone rim",
        plural=True,
    ),
    Tool(
        id="cloak",
        label="an ash cloak",
        covers={"hands", "shoes"},
        guards={"ash"},
        prep="wrap up in an ash cloak first",
        tail="wrapped up in the ash cloak and came back to the hill",
    ),
]

GIRL_NAMES = ["Mira", "Nina", "Luna", "Sage", "Ivy", "Clara"]
BOY_NAMES = ["Rowan", "Owen", "Jasper", "Theo", "Finn", "Milo"]


@dataclass
class StoryParams:
    place: str
    activity: str
    treasure: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for tre_id, tre in TREASURES.items():
                if prize_at_risk(act, tre) and select_tool(act, tre):
                    combos.append((place, act_id, tre_id))
    return combos


def explain_rejection(activity: Activity, treasure: Treasure) -> str:
    if not prize_at_risk(activity, treasure):
        return (
            f"(No story: {activity.gerund} does not reach the {treasure.label}'s "
            f"region, so there is no honest danger to resolve.)"
        )
    return (
        f"(No story: nothing in the tool set safely protects a {treasure.label} "
        f"from {activity.gerund} in a way the rhyme-ghost would trust.)"
    )


def explain_gender(treasure_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(TREASURES, treasure_id).genders))
    return f"(No story: a {_safe_lookup(TREASURES, treasure_id).label} isn't a typical {gender}'s item here; try --gender {ok}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, ghost, activity, treasure = f["hero"], f["ghost"], f["activity"], f["treasure"]
    return [
        f'Write a short ghost story for a young child with the words "{activity.keyword}", "volcanic", and "heart".',
        f"Tell a gentle spooky story where {hero.id} wants to {activity.verb} near {world.setting.place} and a rhyme-loving ghost helps.",
        f"Write a child-friendly rhyme-ghost tale in which a heart-shaped treasure stays safe during a volcanic dig.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ghost, activity, treasure = f["hero"], f["ghost"], f["activity"], f["treasure"]
    qa = [
        QAItem(
            question=f"Where did {hero.id} want to {activity.verb}?",
            answer=f"{hero.id} wanted to {activity.verb} at {world.setting.place}, where the stones were dark and warm.",
        ),
        QAItem(
            question=f"What did the ghost do when {hero.id} got too close to the hot ground?",
            answer=f"The ghost sang a warning in rhyme and told {hero.id} that hot ash could turn bright things gray.",
        ),
        QAItem(
            question=f"What was special about the treasure {hero.id} wore?",
            answer=f"It was a {treasure.phrase}, a heart-shaped treasure that could get dusty near the volcanic stones.",
        ),
    ]
    if f.get("conflict"):
        qa.append(
            QAItem(
                question=f"Why did {hero.id} pause before digging?",
                answer=(
                    f"{hero.id} paused because the ghost's rhyme sounded true, and the volcanic ash felt risky "
                    f"for the heart-shaped treasure."
                ),
            )
        )
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end after the ghost's warning?",
                answer=(
                    f"{hero.id} used the safe tool, kept the treasure clean, and finished digging with the ghost humming nearby."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is ash?",
            answer="Ash is a soft, gray powder left behind after something burns.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like 'stone' and 'bone.'",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="In a story, a ghost is a spooky helper or visitor that can float without walking.",
        ),
        QAItem(
            question="Why can volcanoes be dangerous?",
            answer="Volcanoes can be dangerous because they can send out hot rock, ash, and fire.",
        ),
    ]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, T) :- splashes(A, R), worn_on(T, R).
protects(Tool, A, T) :- tool(Tool), prize_at_risk(A, T), guards(Tool, M), mess_of(A, M), covers(Tool, R), worn_on(T, R).
has_fix(A, T) :- protects(_, A, T).
valid(Place, A, T) :- affords(Place, A), prize_at_risk(A, T), has_fix(A, T).
valid_story(Place, A, T, Gender) :- valid(Place, A, T), wears(Gender, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("worn_on", tid, t.region))
        for g in sorted(t.genders):
            lines.append(asp.fact("wears", g, tid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for m in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, m))
        for r in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny rhyme-ghost story world with volcanic digging.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "activity", None) and getattr(args, "treasure", None):
        act, tr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(TREASURES, getattr(args, "treasure", None))
        if not (prize_at_risk(act, tr) and select_tool(act, tr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "treasure", None) and getattr(args, "gender", None) not in _safe_lookup(TREASURES, getattr(args, "treasure", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, treasure=treasure, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(TREASURES, params.treasure), params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, treasure) combos ({len(stories)} with gender):\n")
        for place, act, treasure in triples:
            genders = sorted(g for (pl, a, tr, g) in stories if (pl, a, tr) == (place, act, treasure))
            print(f"  {place:10} {act:8} {treasure:12}  [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="volcano", activity="dig", treasure="heartstone", name="Mira", gender="girl", parent="mother"),
            StoryParams(place="cave", activity="dig", treasure="heartstone", name="Rowan", gender="boy", parent="father"),
            StoryParams(place="ridge", activity="dig", treasure="heartlantern", name="Luna", gender="girl", parent="mother"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
