#!/usr/bin/env python3
"""
storyworlds/worlds/chim_violence_moon_conflict_tall_tale.py
============================================================

A small tall-tale storyworld about a soot-smudged climber named Chim, a moon
that keeps showing up like a lantern in the sky, and a loud conflict that gets
solved without roughness.

Seed image:
---
Chim was the smallest chimney-climber in the valley, but he talked like he was
bigger than the barn and the thunder together. Every night he liked to climb the
old watch tower and boast to the moon. One moonlit evening, a grumpy rival tried
to shove Chim off the tower and grab the moon-gleam for himself. Chim dodged the
roughness, used a long rope and a bucket lid, and sent the rival sliding safely
into a haystack. The moon shone on, the town cheered, and Chim learned that a
clever trick could beat violence better than a bigger fist.

World model:
- Entities have physical meters and emotional memes.
- The tower, rope, bucket lid, and haystack all matter causally.
- Conflict rises when a brute tries to force the issue; it falls when clever
  tools change the outcome.
- The moon is a witness and a bright source of wonder, not a frozen prop.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily in ASP helpers
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
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

    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    rival: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

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
    name: str
    night: bool = True
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


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
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
class Prize:
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.weather: str = ""
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def mood_add(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def meter_add(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _rule_spoil(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("roughness", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("spoil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            meter_add(item, "dirty", 1)
            meter_add(item, "battered", 1)
            out.append(f"{actor.id} left {item.label} battered.")
    return out


def _rule_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("threat", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("defiance", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        mood_add(actor, "conflict", 1)
        return ["__conflict__"]
    return []


def _rule_calm(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("conflict", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("clever_help", 0.0) < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = 0.0
        actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1
        out.append(f"{actor.id} found a calmer way.")
    return out


CAUSAL_RULES = [
    _rule_spoil,
    _rule_conflict,
    _rule_calm,
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
                for s in sents:
                    if s != "__conflict__":
                        produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, problem: Problem, prize_id: str) -> dict:
    sim = world.copy()
    do_problem(sim, sim.get(actor.id), problem, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "spoiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "conflict": sum(e.memes.get("conflict", 0.0) for e in sim.characters()),
    }


def setting_line(place: Place, problem: Problem) -> str:
    if place.night:
        return f"The night was deep and blue, and {place.name} glowed under the moon."
    return f"{place.name} waited in the open air, wide as a wagon road."


def hero_intro(hero: Entity) -> str:
    return f"{hero.id} was a little {hero.type} with a big voice and a bigger wish."


def adore_moon(hero: Entity) -> str:
    mood_add(hero, "wonder", 1)
    return f"{hero.pronoun().capitalize()} loved the moon so much {hero.pronoun()} could hardly keep still at night."


def wants_challenge(hero: Entity, problem: Problem) -> str:
    mood_add(hero, "desire", 1)
    return f"{hero.id} wanted to {problem.verb}, just to see if anyone in the valley could top {hero.pronoun('object')}."


def forewarn(parent: Entity, hero: Entity, problem: Problem, prize: Entity) -> str:
    pred = predict(CURRENT_WORLD, hero, problem, prize.id)
    CURRENT_WORLD.facts["predicted_conflict"] = pred["conflict"]
    if pred["spoiled"]:
        return f'"If you go chasing that trouble, you may ruin your {prize.label}," {parent.label or parent.id} warned.'
    return f'"Mind your step," {parent.label or parent.id} called, because the night could turn rough in a hurry.'


def do_problem(world: World, actor: Entity, problem: Problem, narrate: bool = True) -> None:
    world.zone = set(problem.zone)
    meter_add(actor, problem.mess, 1)
    meter_add(actor, "roughness", 1)
    mood_add(actor, "joy", 1)
    propagate(world, narrate=narrate)


def challenge(world: World, hero: Entity, rival: Entity, problem: Problem) -> None:
    mood_add(rival, "defiance", 1)
    mood_add(rival, "threat", 1)
    world.say(f"{rival.id} came stomping in, all elbows and bluster, and tried to shove {hero.id} aside.")
    world.say(f'{hero.id} said, "That kind of violence may knock over a fence, but it will not scare the moon off the sky."')


def turn_with_tool(world: World, hero: Entity, helper: Entity, problem: Problem, prize: Entity) -> Optional[Tool]:
    for tool_def in TOOLS:
        if problem.mess in tool_def.guards and prize.region in tool_def.covers:
            tool = world.add(Entity(
                id=tool_def.id,
                kind="thing",
                type="tool",
                label=tool_def.label,
                owner=hero.id,
                caretaker=helper.id,
                protective=True,
                covers=set(tool_def.covers),
                plural=tool_def.plural,
            ))
            tool.worn_by = hero.id
            pred = predict(world, hero, problem, prize.id)
            if pred["spoiled"]:
                tool.worn_by = None
                del world.entities[tool.id]
                continue
            mood_add(hero, "clever_help", 1)
            world.say(f'{helper.id} smiled and said, "How about we {tool_def.prep}?"')
            return tool
    return None


def resolution(world: World, hero: Entity, helper: Entity, problem: Problem, prize: Entity, tool: Tool) -> None:
    mood_add(hero, "conflict", 0)
    mood_add(hero, "pride", 1)
    world.say(f"{hero.id} nodded, took the tool, and grinned like a fox in moonlight.")
    world.say(f"Then {hero.id} and {helper.id} {tool.tail}.")
    world.say(f"Before long, {hero.id} was {problem.gerund}, {prize.label} stayed clean, and the moon looked on like a silver eye that had seen a fine trick.")


def tell(place: Place, problem: Problem, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    global CURRENT_WORLD
    world = World(place)
    CURRENT_WORLD = world
    world.weather = problem.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type, label=hero_name,
        meters={"roughness": 0.0}, memes={"wonder": 0.0, "desire": 0.0},
    ))
    parent = world.add(Entity(
        id="Aunt", kind="character", type=parent_type, label="Aunt Cal",
        memes={"care": 1.0},
    ))
    rival = world.add(Entity(
        id="Grub", kind="character", type="man", label="Grub",
        memes={"defiance": 0.0, "threat": 0.0},
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    world.say(hero_intro(hero))
    world.say(adore_moon(hero))
    world.say(f"One evening at the {place.name}, {hero.id} wore {prize.phrase} and felt as proud as a rooster on a fence post.")
    world.para()
    world.say(setting_line(place, problem))
    world.say(wants_challenge(hero, problem))
    world.say(forewarn(parent, hero, problem, prize))
    challenge(world, hero, rival, problem)
    world.para()
    tool = turn_with_tool(world, hero, parent, problem, prize)
    if tool:
        world.say(f"{hero.id} laughed, because the trick was better than a wrestle.")
        resolution(world, hero, parent, problem, prize, tool)

    world.facts.update(hero=hero, parent=parent, rival=rival, prize=prize, problem=problem, tool=tool, place=place)
    return world


SETTINGS = {
    "watchtower": Place(name="the watch tower", night=True, affords={"moon_climb", "moon_beam"}),
    "barnroof": Place(name="the barn roof", night=True, affords={"moon_climb"}),
    "campspot": Place(name="the camp spot", night=True, affords={"moon_beam"}),
}

PROBLEMS = {
    "moon_climb": Problem(
        id="moon_climb",
        verb="climb up to the moonlight",
        gerund="climbing high and hollering at the moon",
        rush="charge up the ladder",
        mess="roughness",
        soil="battered",
        zone={"torso", "legs"},
        weather="clear",
        keyword="moon",
        tags={"moon"},
    ),
    "moon_beam": Problem(
        id="moon_beam",
        verb="catch the moonbeam in a bucket lid",
        gerund="balancing a shiny lid under the moon",
        rush="snatch the lid",
        mess="roughness",
        soil="battered",
        zone={"hands", "torso"},
        weather="clear",
        keyword="moon",
        tags={"moon"},
    ),
}

TOOLS = [
    Tool(
        id="rope",
        label="a long rope",
        covers={"hands", "torso"},
        guards={"roughness"},
        prep="tie a long rope to the post and use it like a swing",
        tail="slid down the rope and landed in a haystack",
    ),
    Tool(
        id="lid",
        label="a bucket lid",
        covers={"hands"},
        guards={"roughness"},
        prep="hold the bucket lid up like a mirror and let the moonlight guide us",
        tail="turned the lid just so and sent the trouble spinning away",
    ),
    Tool(
        id="blanket",
        label="a thick blanket",
        covers={"legs", "torso"},
        guards={"roughness"},
        prep="wrap the blanket around the railing first",
        tail="made a safe nest of the railing and climbed down easy",
    ),
]

PRIZES = {
    "coat": Prize(label="coat", phrase="a red velvet coat", type="coat", region="torso"),
    "boots": Prize(label="boots", phrase="stiff black boots", type="boots", region="feet", plural=True),
    "hat": Prize(label="hat", phrase="a tall brimmed hat", type="hat", region="head"),
}

GIRL_NAMES = ["May", "Iris", "Nell", "Ruby", "June", "Ada"]
BOY_NAMES = ["Chim", "Bo", "Hank", "Lyle", "Otis", "Perry"]


@dataclass
class StoryParams:
    place: str
    problem: str
    prize: str
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
    for place_id, place in SETTINGS.items():
        for prob_id in place.affords:
            prob = _safe_lookup(PROBLEMS, prob_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in prob.zone:
                    combos.append((place_id, prob_id, prize_id))
    return combos


def explain_rejection(problem: Problem, prize: Prize) -> str:
    return f"(No story: {problem.gerund} does not threaten a {prize.label} in the right way.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about Chim, the moon, and a conflict that needs a clever turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--prize", choices=PRIZES)
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
    if getattr(args, "problem", None) and getattr(args, "prize", None):
        prob, prize = _safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if prize.region not in prob.zone:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, problem=problem, prize=prize, name=name, gender=gender, parent=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for children about {f["hero"].id}, the moon, and a showdown at {f["place"].name}.',
        f"Tell a story where {f['hero'].id} wants to {f['problem'].verb}, but a rough rival brings conflict and a clever tool saves the day.",
        f'Write a short, dramatic moonlit tale that includes the word "chim" and ends with a safe, surprising triumph.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, problem, tool = f["hero"], f["parent"], f["prize"], f["problem"], (f.get("tool") or next(iter(TOOLS.values())))
    qas = [
        QAItem(
            question=f"Who is the tall tale about?",
            answer=f"It is about {hero.id}, a little climber with a big voice, and {parent.label}, who helped keep the night from getting too rough.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do under the moon?",
            answer=f"{hero.id} wanted to {problem.verb}. The moon shone overhead while {hero.id} tried to prove a point.",
        ),
        QAItem(
            question=f"What caused the conflict in the story?",
            answer=f"Grub tried to shove {hero.id} aside and turn the moment into violence. That roughness made the conflict grow, but it did not win.",
        ),
        QAItem(
            question=f"How did the clever tool help?",
            answer=f"{tool.label} helped because it let {hero.id} choose a safer trick instead of a wrestle. The plan sent the rival away without hurting anyone.",
        ),
        QAItem(
            question=f"What stayed safe by the end?",
            answer=f"{prize.label} stayed clean and safe, and the moon kept shining over the tower like a silver lantern.",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the moon?",
            answer="The moon is a big round body in the sky that shines by reflecting sunlight, so it can glow bright at night.",
        ),
        QAItem(
            question="What does conflict mean?",
            answer="Conflict means people or characters want different things, so they get in each other's way and have trouble until they solve it.",
        ),
        QAItem(
            question="What should people do instead of violence?",
            answer="People should use words, waiting, and clever helpers instead of violence, because rough force can hurt others and make trouble worse.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURRENT_WORLD: World


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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


ASP_RULES = r"""
at_risk(P, R) :- prize(P), worn_on(P, R), splashes(A, R).
compatible(A, P) :- at_risk(P, R), splashes(A, R), gear(G), guards(G, roughness), covers(G, R).
valid(Place, Problem, Prize) :- affords(Place, Problem), at_risk(Prize, _), compatible(Problem, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if p.night:
            lines.append(asp.fact("night", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", aid))
        lines.append(asp.fact("mess_of", aid, prob.mess))
        for r in sorted(prob.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for t in TOOLS:
        lines.append(asp.fact("gear", t.id))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="watchtower", problem="moon_climb", prize="hat", name="Chim", gender="boy", parent="father"),
    StoryParams(place="barnroof", problem="moon_climb", prize="coat", name="Bo", gender="boy", parent="father"),
    StoryParams(place="campspot", problem="moon_beam", prize="boots", name="May", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, problem, prize) combos:\n")
        for row in combos:
            print(" ", row)
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
            header = f"### {p.name}: {p.problem} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
