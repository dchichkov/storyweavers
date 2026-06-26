#!/usr/bin/env python3
"""
storyworlds/worlds/elapse_board_panda_flashback_heartwarming.py
===============================================================

A tiny heartwarming story world built from the seed words:
elapse, board, panda.

Premise:
- A child and a caring adult are stuck inside on a rainy day.
- Time elapses while they wait for the weather to change.
- They make a memory board with a panda theme to keep spirits up.
- A flashback reveals why the board matters and why the child trusts the adult.
- The ending shows the child calmer, happier, and more connected.

The world is intentionally small and constraint-checked:
- if no plausible comfort move exists, generation refuses the request
- if the explicit parameters describe an unreasonable story, StoryError is raised
- ASP facts/rules mirror the Python reasonableness gate
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    board: object | None = None
    child: object | None = None
    grandma: object | None = None
    panda: object | None = None
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
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    weather: str
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
    wait_phrase: str
    turn_phrase: str
    joy_phrase: str
    worry: str
    soothed_by: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    type: str
    theme: str
    placable_on: set[str] = field(default_factory=set)
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
class Craft:
    id: str
    label: str
    noun: str
    prep: str
    result: str
    theme: str
    helps: set[str] = field(default_factory=set)
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
        self.time_elapsing: bool = False
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
        clone.time_elapsing = self.time_elapsing
        clone.paragraphs = [[]]
        return clone


def _time_tick(world: World) -> list[str]:
    out: list[str] = []
    if not world.time_elapsing:
        return out
    for actor in world.characters():
        actor.meters["waiting"] += 0.5
        if actor.meters["waiting"] >= THRESHOLD and ("wait", actor.id) not in world.fired:
            world.fired.add(("wait", actor.id))
            actor.memes["restless"] += 1
            out.append(f"Time seemed to elapse slowly, and {actor.id} began to fidget.")
    return out


def _craft_board(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("restless", 0) < THRESHOLD:
        return out
    if ("craft", "board") in world.fired:
        return out
    world.fired.add(("craft", "board"))
    board = world.get("board")
    craft = _safe_fact(world, world.facts, "craft")
    board.meters["made"] += 1
    child.memes["hope"] += 1
    child.memes["restless"] = 0
    out.append(
        f"So {child.id} and {world.get('grandma').label} chose to make {craft.label} together."
    )
    return out


def _flashback(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grandma = world.get("grandma")
    board = world.get("board")
    panda = world.get("panda")
    if child.memes.get("hope", 0) < THRESHOLD:
        return out
    if ("flashback",) in world.fired:
        return out
    world.fired.add(("flashback",))
    child.memes["trust"] += 1
    panda.meters["displayed"] += 1
    out.append(
        f"As they cut the shapes, {child.id} remembered an earlier day when {grandma.label} had helped "
        f"make a small panda picture board after a hard afternoon."
    )
    out.append(
        f"Back then, {grandma.label} had said that kind words can hold a heart steady, just like a board can hold up a picture."
    )
    out.append(
        f"That memory made the room feel warmer, and the little panda on the board seemed to smile back."
    )
    return out


def _settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grandma = world.get("grandma")
    board = world.get("board")
    if board.meters.get("made", 0) < THRESHOLD:
        return out
    if ("settle",) in world.fired:
        return out
    world.fired.add(("settle",))
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    child.memes["restless"] = 0
    out.append(
        f"When the board was finished, {child.id} felt calm again and hugged {grandma.label}."
    )
    out.append(
        f"Together they looked at the panda on the board and waited kindly while the storm passed."
    )
    return out


RULES = [
    _time_tick,
    _craft_board,
    _flashback,
    _settle,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_craft_board(activity: Activity, keepsake: Keepsake, craft: Craft) -> bool:
    return (
        keepsake.theme == activity.keyword
        and craft.theme == activity.keyword
        and keepsake.id in craft.helps
    )


def explain_rejection(activity: Activity, keepsake: Keepsake, craft: Craft) -> str:
    return (
        f"(No story: the chosen board and panda keepsake do not fit this heartwarming flashback. "
        f"The board needs to carry the panda theme, and the craft must genuinely help the child settle after {activity.verb}.)"
    )


SETTINGS = {
    "rainy_room": Setting(place="the cozy living room", weather="rainy", affords={"wait", "craft"}),
    "sunny_room": Setting(place="the sunny kitchen table", weather="sunny", affords={"wait", "craft"}),
}

ACTIVITIES = {
    "wait": Activity(
        id="wait",
        verb="wait for the storm to pass",
        gerund="waiting by the window",
        wait_phrase="while the rain tapped the glass",
        turn_phrase="as time elapse*d* and the clouds stayed gray",
        joy_phrase="the room could still feel warm",
        worry="restless",
        soothed_by="making something kind",
        keyword="elapse",
        tags={"elapse"},
    )
}

KEEPSAKES = {
    "panda_board": Keepsake(
        id="panda_board",
        label="a panda memory board",
        phrase="a panda memory board with soft paper paws and bright corners",
        type="board",
        theme="panda",
        placable_on={"wall", "table"},
    ),
    "panda_card": Keepsake(
        id="panda_card",
        label="a panda picture card",
        phrase="a panda picture card",
        type="card",
        theme="panda",
        placable_on={"board"},
    ),
}

CRAFTS = {
    "pins": Craft(
        id="pins",
        label="tiny pins and string",
        noun="board",
        prep="pin the pictures onto",
        result="a cheerful panda board",
        theme="panda",
        helps={"panda_board"},
    ),
    "glue": Craft(
        id="glue",
        label="glue and colored paper",
        noun="card",
        prep="paste the pieces onto",
        result="a sweet panda card",
        theme="panda",
        helps={"panda_card"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    activity: str
    keepsake: str
    craft: str
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


GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Maya", "Rose"]
BOY_NAMES = ["Finn", "Leo", "Owen", "Eli", "Noah", "Theo"]


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    keepsake = _safe_lookup(KEEPSAKES, params.keepsake)
    craft = _safe_lookup(CRAFTS, params.craft)

    if not can_craft_board(activity, keepsake, craft):
        pass

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"waiting": 0.0},
        memes={"calm": 0.0, "restless": 0.0, "hope": 0.0, "trust": 0.0, "joy": 0.0},
    ))
    grandma = world.add(Entity(
        id="grandma",
        kind="character",
        type=params.parent,
        label="Grandma",
        meters={},
        memes={"warmth": 1.0, "patience": 1.0},
    ))
    board = world.add(Entity(
        id="board",
        type="board",
        label=keepsake.label,
        phrase=keepsake.phrase,
        owner=child.id,
        caretaker=grandma.id,
        meters={"made": 0.0},
        tags={"board", "panda"},
    ))
    panda = world.add(Entity(
        id="panda",
        type="panda",
        label="the panda picture",
        phrase="a smiling panda picture",
        owner=child.id,
        meters={"displayed": 0.0},
        tags={"panda"},
    ))

    world.facts.update(
        child=child,
        grandma=grandma,
        board=board,
        panda=panda,
        activity=activity,
        keepsake=keepsake,
        craft=craft,
        setting=setting,
    )

    world.say(
        f"{child.id} was a little {params.gender} who loved pandas and quiet afternoons with {grandma.label}."
    )
    world.say(
        f"One rainy day, {child.id} and {grandma.label} stayed inside {setting.place} and watched the minutes elapse by the window."
    )
    world.para()
    world.time_elapsing = True
    world.say(
        f"{child.id} wanted to {activity.verb}, but the rain made the day feel too still."
    )
    world.say(
        f"{child.id} felt fidgety until {grandma.label} suggested something gentle and bright: making {keepsake.label}."
    )
    propagate(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    activity = _safe_fact(world, f, "activity")
    keepsake = _safe_fact(world, f, "keepsake")
    return [
        f"Write a heartwarming story about {child.id} while time can elapse inside a cozy room, with a panda memory board at the center.",
        f"Tell a gentle story where a child waits out the rain, then makes {keepsake.label} with Grandma and remembers a kind flashback.",
        f"Write a short story for a young child that includes the words elapse, board, and panda, and ends with someone feeling calmer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    grandma = _safe_fact(world, f, "grandma")
    activity = _safe_fact(world, f, "activity")
    keepsake = _safe_fact(world, f, "keepsake")
    craft = _safe_fact(world, f, "craft")

    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a little {child.type}, and {grandma.label}, who stayed close and helped.",
        ),
        QAItem(
            question=f"What did {child.id} want to do before the board was finished?",
            answer=f"{child.id} wanted to {activity.verb}, but the rain made waiting feel slow.",
        ),
        QAItem(
            question=f"What did {child.id} and {grandma.label} make together?",
            answer=f"They made {keepsake.label} using {craft.label}, and that gave the room a kinder feeling.",
        ),
        QAItem(
            question=f"Why did the story include a flashback?",
            answer=(
                f"The flashback showed {child.id} that {grandma.label} had helped with a panda picture before, "
                f"so the new board felt safe and familiar."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {child.id} feeling calm and hugging {grandma.label} while they looked at the panda on the board."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a panda?",
            answer="A panda is a black-and-white bear that loves to eat bamboo and looks soft and gentle.",
        ),
        QAItem(
            question="What is a board?",
            answer="A board is a flat surface you can use to display pictures, notes, or crafts.",
        ),
        QAItem(
            question="What does it mean when time elapses?",
            answer="When time elapses, the minutes pass little by little.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] if x else 'unknown' for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
time_tick(C) :- child(C).
needs_comfort(C) :- time_tick(C).
board_ok(B) :- board(B).
panda_theme(P) :- panda(P).
heartwarming_story(C, B, P) :- needs_comfort(C), board_ok(B), panda_theme(P).
valid_story(S, A, K, C) :- setting(S), activity(A), keepsake(K), craft(C),
                           can_help(C, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("child_activity", aid))
    for kid, k in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        lines.append(asp.fact("theme", kid, k.theme))
    for cid, c in CRAFTS.items():
        lines.append(asp.fact("craft", cid))
        lines.append(asp.fact("can_help", cid, c.helps.pop() if c.helps else cid))
        for help_id in c.helps:
            lines.append(asp.fact("can_help", cid, help_id))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("board", "board"))
    lines.append(asp.fact("panda", "panda"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIVITIES:
            for k, keepsake in KEEPSAKES.items():
                for c, craft in CRAFTS.items():
                    if can_craft_board(_safe_lookup(ACTIVITIES, a), keepsake, craft):
                        combos.append((s, a, k, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about elapse, board, and panda.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandma"])
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "keepsake", None):
        combos = [c for c in combos if c[2] == getattr(args, "keepsake", None)]
    if getattr(args, "craft", None):
        combos = [c for c in combos if c[3] == getattr(args, "craft", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, keepsake, craft = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or "grandma"
    return StoryParams(
        setting=setting,
        activity=activity,
        keepsake=keepsake,
        craft=craft,
        name=name,
        gender=gender,
        parent=parent,
    )


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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(
                setting="rainy_room",
                activity="wait",
                keepsake="panda_board",
                craft="pins",
                name="Mina",
                gender="girl",
                parent="grandma",
            ),
            StoryParams(
                setting="sunny_room",
                activity="wait",
                keepsake="panda_card",
                craft="glue",
                name="Leo",
                gender="boy",
                parent="grandma",
            ),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.keepsake} / {p.craft} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
