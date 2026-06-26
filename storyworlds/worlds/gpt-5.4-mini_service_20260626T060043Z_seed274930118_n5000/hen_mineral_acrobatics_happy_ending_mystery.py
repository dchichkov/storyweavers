#!/usr/bin/env python3
"""
storyworlds/worlds/hen_mineral_acrobatics_happy_ending_mystery.py
==================================================================

A tiny mystery-flavored story world about a hen, a missing mineral, and a
gentle acrobatics setup that ends happily.

Premise:
- A careful hen prepares for a small acrobatics show.
- A shiny mineral is part of the show costume or prop.
- The mineral goes missing, which creates a mystery.
- The hen investigates with clues from the coop, the garden, and the tool box.
- The truth is discovered, the mineral is returned, and the show ends well.

This script follows the storyworld contract:
- self-contained stdlib script
- imports shared results eagerly
- imports asp lazily only in ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    caregiver: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hen: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "hen":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"child", "girl", "boy"}:
            if self.type == "boy":
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
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
class Place:
    id: str
    label: str
    indoors: bool = False
    clues: set[str] = field(default_factory=set)
    hides: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    clue: str
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
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    region: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: str
    hides: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

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

        other = World(self.place)
        other.entities = _copy.deepcopy(self.entities)
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


THRESHOLD = 1.0


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    hen = world.entities.get("hen")
    mineral = world.entities.get("mineral")
    if not hen or not mineral:
        return out
    if hen.memes.get("searching", 0.0) < THRESHOLD:
        return out
    if mineral.carried_by:
        sig = ("found", mineral.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.facts["found"] = True
        out.append(f"That was the clue: {mineral.label} was not lost at all.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_found,):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
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
    "coop": Place(
        id="coop",
        label="the coop yard",
        clues={"feather", "scratch", "dust"},
        hides={"nest", "hay"},
    ),
    "garden": Place(
        id="garden",
        label="the garden path",
        clues={"soil", "leaf", "shine"},
        hides={"stone", "bucket"},
    ),
    "barn": Place(
        id="barn",
        label="the barn loft",
        clues={"rope", "dust", "beam"},
        hides={"box", "basket"},
    ),
}

ACTIVITIES = {
    "acrobatics": Activity(
        id="acrobatics",
        verb="practice acrobatics",
        gerund="practicing acrobatics",
        mess="tumble",
        clue="a tiny trail of chalk",
        risk="the show would feel unfinished",
        keyword="acrobatics",
        tags={"acrobatics", "show", "chalk"},
    ),
    "balance": Activity(
        id="balance",
        verb="walk the balance beam",
        gerund="walking the beam",
        mess="dust",
        clue="a straight line of dust",
        risk="the beam routine would look plain",
        keyword="balance",
        tags={"acrobatics", "beam"},
    ),
}

PRIZES = {
    "mineral": Prize(
        id="mineral",
        label="mineral",
        phrase="a bright mineral for the show",
        type="mineral",
        region="beak",
    ),
    "stone": Prize(
        id="stone",
        label="stone",
        phrase="a smooth stone with a shiny face",
        type="stone",
        region="wing",
    ),
    "crystal": Prize(
        id="crystal",
        label="crystal",
        phrase="a clear crystal that caught the light",
        type="crystal",
        region="neck",
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="a magnifying glass",
        phrase="a little magnifying glass",
        helps="look closely at clues",
    ),
    "lamp": Tool(
        id="lamp",
        label="a lamp",
        phrase="a warm little lamp",
        helps="see in dark corners",
    ),
    "rake": Tool(
        id="rake",
        label="a rake",
        phrase="a small rake",
        helps="move hay aside",
    ),
}

HEN_NAMES = ["Hattie", "Pippa", "Mabel", "Sunny", "Dot", "Pearl"]
NEST_NAMES = ["nest", "hay", "basket", "box"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, act in ACTIVITIES.items():
            for prid in PRIZES:
                if pid == "barn" or prid == "mineral":
                    combos.append((pid, aid, prid))
    return combos


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.id == "mineral" or activity.id == "acrobatics"


def select_tool(place: Place, activity: Activity, prize: Prize) -> Optional[Tool]:
    if place.id == "barn":
        return TOOLS["lamp"]
    if prize.id == "mineral":
        return TOOLS["magnifier"]
    if activity.id == "balance":
        return TOOLS["rake"]
    return None


def introduce(world: World, hen: Entity) -> None:
    world.say(f"{hen.id} was a careful hen who loved noticing small things.")


def set_up(world: World, hen: Entity, activity: Activity, prize: Entity, tool: Entity) -> None:
    world.say(
        f"{hen.pronoun().capitalize()} was getting ready for {activity.gerund} "
        f"when {prize.phrase} went missing."
    )
    world.say(
        f"She had planned to use {tool.phrase} because it could {tool.helps}."
    )


def mystery_turn(world: World, hen: Entity, prize: Entity) -> None:
    hen.memes["searching"] = 1.0
    world.say(
        f"{hen.id} looked under the hay, behind the basket, and beside the feed tin."
    )
    world.say(
        f"Everywhere she checked, she found clues, but not the mineral."
    )


def clue_scene(world: World, place: Place, activity: Activity) -> None:
    if "shine" in place.clues:
        world.say("A tiny shine on the floor caught her eye.")
    elif "dust" in place.clues:
        world.say("A line of dust made her stop and think.")
    else:
        world.say("A small feather pointed her toward the next spot.")


def reveal(world: World, hen: Entity, prize: Entity) -> None:
    prize.carried_by = hen.id
    prize.hidden_in = ""
    world.say(
        f"At last, {hen.id} found the mineral tucked in a safe little nook where the light had missed it."
    )
    world.say(
        f"It had never been stolen; it had simply rolled away and vanished in the clutter."
    )


def happy_ending(world: World, hen: Entity, activity: Activity, prize: Entity, tool: Entity) -> None:
    hen.memes["joy"] = hen.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{hen.id} carried the mineral back to the stage, and the acrobatics show could begin."
    )
    world.say(
        f"With {tool.label} nearby and the prize safe again, she finished {activity.gerund} with a proud cluck."
    )
    world.say(
        f"By the end, the little mystery was solved, and the shiny mineral sparkled right where it belonged."
    )


def tell(place: Place, activity: Activity, prize_cfg: Prize, tool: Tool, name: str) -> World:
    world = World(place)
    hen = world.add(Entity(id="hen", kind="character", type="hen", label=name or "Hen"))
    prize = world.add(Entity(
        id="mineral",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hen.id,
    ))
    helper = world.add(Entity(id=tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase))

    introduce(world, hen)
    world.say(
        f"{hen.id} loved {activity.gerund}, especially when a bright {prize.label} could shine in the show."
    )
    world.para()
    set_up(world, hen, activity, prize, helper)
    clue_scene(world, place, activity)
    mystery_turn(world, hen, prize)
    reveal(world, hen, prize)
    world.para()
    happy_ending(world, hen, activity, prize, helper)

    world.facts.update(
        hen=hen,
        prize=prize,
        activity=activity,
        tool=helper,
        place=place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly mystery story about a hen, a missing mineral, and acrobatics, with a happy ending.',
        f"Tell a short story where {f['hen'].id} searches for {f['prize'].label} before {f['activity'].verb}.",
        f"Write a gentle mystery in which a hen uses {(f.get('tool') or next(iter(TOOLS.values()))).label} to solve a small problem in {f['place'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hen: Entity = _safe_fact(world, f, "hen")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What was missing when {hen.id} wanted to {activity.verb}?",
            answer=f"The missing thing was the {prize.label}. It was the bright mineral needed for the show.",
        ),
        QAItem(
            question=f"How did {hen.id} try to solve the mystery in {place.label}?",
            answer=f"She looked carefully for clues and used {tool.label} to search the quiet spots more closely.",
        ),
        QAItem(
            question=f"What happened after the mineral was found?",
            answer=f"{hen.id} brought it back, and the acrobatics show could begin happily at the end.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is a mineral?",
        answer="A mineral is a natural solid found in the ground, such as a shiny stone or crystal.",
    ),
    QAItem(
        question="What do acrobatics mean?",
        answer="Acrobatics are movements like balancing, turning, and flipping that take careful practice.",
    ),
    QAItem(
        question="Why use a magnifying glass?",
        answer="A magnifying glass helps someone look closely at tiny details and small clues.",
    ),
    QAItem(
        question="What makes a mystery story?",
        answer="A mystery story has a question, clues to follow, and an answer at the end.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="coop", activity="acrobatics", prize="mineral", tool="magnifier"),
    StoryParams(place="garden", activity="balance", prize="mineral", tool="magnifier"),
    StoryParams(place="barn", activity="acrobatics", prize="crystal", tool="lamp"),
]


KNOWLEDGE_ORDER = ["mineral", "acrobatics", "mystery"]


ASP_RULES = r"""
place(coop). place(garden). place(barn).
activity(acrobatics). activity(balance).
prize(mineral). prize(stone). prize(crystal).
tool(magnifier). tool(lamp). tool(rake).

valid(Place,Act,Prize) :- place(Place), activity(Act), prize(Prize), Act = acrobatics.
valid(Place,Act,Prize) :- place(Place), activity(Act), prize(Prize), Place = barn.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for prid in PRIZES:
        lines.append(asp.fact("prize", prid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
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
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A hen, a mineral, acrobatics, and a small mystery with a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
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
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    tool = getattr(args, "tool", None) or ("magnifier" if prize == "mineral" else "lamp")
    return StoryParams(place=place, activity=activity, prize=prize, tool=tool, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), _safe_lookup(TOOLS, params.tool), params.name or "Hattie")
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
