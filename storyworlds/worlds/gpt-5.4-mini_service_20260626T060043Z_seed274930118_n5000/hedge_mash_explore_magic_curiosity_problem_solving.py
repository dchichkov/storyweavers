#!/usr/bin/env python3
"""
storyworlds/worlds/hedge_mash_explore_magic_curiosity_problem_solving.py
=========================================================================

A small fable-like storyworld about a curious explorer, a magical hedge,
and a messy mash that can only be handled with patience and problem solving.

Seed tale:
---
Once there was a small mouse named Pip who loved to explore the hedge behind the
old field. In the middle of the hedge lived a tiny glowing beetle who could make
berries sing when it tapped them with a bright spark.

One morning, Pip found a bowl of berry mash stuck near the hedge gate. The mash
had spilled into the path and blocked the way. Pip wanted to explore anyway, but
the glowing beetle warned that stomping through would smear the mash everywhere
and ruin the path for everyone.

Pip felt curious, then frustrated, then thoughtful. It looked closely, found a
flat leaf, used it like a scoop, and gently moved the mash aside. The path
opened, the hedge shimmered, and Pip learned that a small problem can be solved
with a careful mind.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    prob: object | None = None
    t: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king", "mouse"}
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
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
class Problem:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    action_block: str
    fix_hint: str
    solution_tool: str
    tags: set[str] = field(default_factory=set)
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
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _to_meters(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _to_memes(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _has(ent: Entity, key: str) -> bool:
    return ent.meters.get(key, 0.0) >= THRESHOLD or ent.memes.get(key, 0.0) >= THRESHOLD


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


def _r_mash_spread(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mash", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.worn_by != actor.id:
                continue
            sig = ("mash_spread", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _to_meters(item, "stained", 1.0)
            out.append(f"{item.label or item.type} got smeared with mash.")
    return out


def _r_problem_rises(world: World) -> list[str]:
    out: list[str] = []
    for problem in list(world.entities.values()):
        if problem.kind != "problem":
            continue
        if problem.meters.get("blocked", 0.0) < THRESHOLD:
            continue
        sig = ("problem_rises", problem.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for actor in world.characters():
            _to_memes(actor, "worry", 1.0)
        out.append(f"The path stayed blocked.")
    return out


def _r_curiosity_turns_to_problem_solving(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("observed", 0.0) < THRESHOLD:
            continue
        sig = ("turn", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _to_memes(actor, "problem_solving", 1.0)
        out.append(f"{actor.id} looked closely instead of rushing ahead.")
    return out


CAUSAL_RULES = [
    Rule("mash_spread", _r_mash_spread),
    Rule("problem_rises", _r_problem_rises),
    Rule("turn", _r_curiosity_turns_to_problem_solving),
]


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


def _do_explore(world: World, actor: Entity, activity: Activity, problem: Problem, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    world.zone = set(activity.zone)
    _to_meters(actor, "explore", 1.0)
    _to_memes(actor, "curiosity", 1.0)
    _to_meters(problem, "blocked", 1.0)
    propagate(world, narrate=narrate)


def predict_outcome(world: World, actor: Entity, activity: Activity, problem: Problem) -> dict:
    sim = world.copy()
    _do_explore(sim, sim.get(actor.id), activity, sim.get(problem.id), narrate=False)
    return {
        "blocked": sim.get(problem.id).meters.get("blocked", 0.0) >= THRESHOLD,
        "problem_solving": sim.get(actor.id).memes.get("problem_solving", 0.0) >= THRESHOLD,
    }


def setting_line(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place} was quiet, and the hedge of thought waited in the corner."
    return f"Beyond {setting.place}, a hedge curled like a green wall."



def introduce(world: World, hero: Entity, mentor: Entity) -> None:
    trait = next((t for t in hero.traits if t != "small"), "curious")
    world.say(f"{hero.id} was a small {trait} {hero.type} who loved to explore.")
    world.say(f"Near the hedge lived {mentor.id}, a tiny light who seemed almost magical.")

def want_explore(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} wanted to {activity.verb}, because every path held a new question.")

def show_problem(world: World, problem: Problem) -> None:
    world.say(f"But a bowl of {problem.phrase} had spilled near the hedge gate and blocked the way.")

def warn(world: World, mentor: Entity, hero: Entity, activity: Activity, problem: Problem) -> None:
    pred = predict_outcome(world, hero, activity, problem)
    if pred["blocked"]:
        world.say(
            f'"If you {activity.verb}, you will smear the {problem.label} all over the path," '
            f"{mentor.id} said. "
            f'"A small problem is best met with a clear mind."'
        )

def hesitate(world: World, hero: Entity) -> None:
    _to_memes(hero, "frustration", 1.0)
    world.say(f"{hero.id} paused, because wanting something did not make the block disappear.")

def observe(world: World, hero: Entity, problem: Problem) -> None:
    _to_meters(hero, "observed", 1.0)
    world.say(f"{hero.id} looked closely and noticed {problem.fix_hint}.")

def solve(world: World, hero: Entity, tool: Tool, problem: Problem) -> None:
    _to_memes(hero, "problem_solving", 1.0)
    world.say(f"{hero.id} used {tool.phrase} to {tool.prep}.")
    world.say(f"Carefully, {hero.id} {tool.tail}, and the {problem.label} moved aside.")
    _to_meters(problem, "blocked", -1.0)

def finish(world: World, hero: Entity, mentor: Entity, activity: Activity, problem: Problem) -> None:
    _to_memes(hero, "joy", 1.0)
    world.say(f"The hedge shimmered softly, and the path opened at last.")
    world.say(
        f"{hero.id} could keep exploring, and the little light by the hedge glowed brighter, "
        f"as if it approved."
    )


SETTINGS = {
    "field": Setting(place="the field", indoor=False, affords={"explore"}),
    "garden": Setting(place="the garden", indoor=False, affords={"explore"}),
    "orchard": Setting(place="the orchard", indoor=False, affords={"explore"}),
}

ACTIVITIES = {
    "explore": Activity(
        id="explore",
        verb="explore the hedge",
        gerund="exploring the hedge",
        rush="dash into the hedge",
        mess="scuff",
        soil="all scuffed",
        zone={"path", "feet"},
        keyword="hedge",
        tags={"hedge", "explore"},
    ),
    "mash_step": Activity(
        id="mash_step",
        verb="step into the mash",
        gerund="stepping into the mash",
        rush="plunge into the mash",
        mess="mash",
        soil="smeared with mash",
        zone={"path", "feet"},
        keyword="mash",
        tags={"mash"},
    ),
}

PROBLEMS = {
    "berry_mash": Problem(
        id="berry_mash",
        label="berry mash",
        phrase="bright berry mash",
        region="path",
        mess="mash",
        action_block="explore",
        fix_hint="a wide leaf lay nearby like a tiny shovel",
        solution_tool="leaf_scoop",
        tags={"mash"},
    )
}

TOOLS = {
    "leaf_scoop": Tool(
        id="leaf_scoop",
        label="a broad leaf",
        phrase="a broad leaf",
        helps={"mash"},
        covers={"path"},
        prep="scoop the berry mash aside",
        tail="nudged the mash to the side in small careful pushes",
        tags={"mash", "problem_solving"},
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Pia", "Nora", "Tess"]
BOY_NAMES = ["Pip", "Finn", "Rufus", "Milo", "Theo"]
TRAITS = ["curious", "gentle", "brave", "thoughtful", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    problem: str
    tool: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prob_id, prob in PROBLEMS.items():
                if prob.action_block == act_id:
                    combos.append((place, act_id, prob_id))
    return combos


def tell(setting: Setting, activity: Activity, problem: Problem, tool: Tool,
         hero_name: str, hero_type: str, mentor_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["small", trait]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="sprite", label="the glowing beetle"))
    prob = world.add(Entity(id=problem.id, kind="problem", type="problem", label=problem.label, phrase=problem.phrase))
    t = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, protective=True))
    t.worn_by = hero.id

    introduce(world, hero, mentor)
    world.para()
    world.say(setting_line(setting))
    want_explore(world, hero, activity)
    show_problem(world, problem)
    warn(world, mentor, hero, activity, problem)
    hesitate(world, hero)
    world.say(f"{hero.id} did not give up. {hero.id} chose to look for a better answer.")
    observe(world, hero, problem)
    solve(world, hero, tool, problem)
    finish(world, hero, mentor, activity, problem)

    world.facts.update(hero=hero, mentor=mentor, problem=prob, tool=t, activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prob: Entity = _safe_fact(world, f, "problem")
    return [
        f'Write a short fable about a curious {hero.type} who wants to explore a hedge.',
        f"Tell a simple story in which {hero.id} meets {prob.label}, feels curious, and solves the problem wisely.",
        "Write a child-friendly fable with magic, curiosity, and problem solving near a hedge.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    mentor: Entity = _safe_fact(world, f, "mentor")
    prob: Entity = _safe_fact(world, f, "problem")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    act: Activity = _safe_fact(world, f, "activity")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who wanted to {act.verb} near {place}?",
            answer=f"{hero.id}, a small {next(t for t in hero.traits if t != 'small')} {hero.type}, wanted to {act.verb}."
        ),
        QAItem(
            question=f"What blocked the way by the hedge?",
            answer=f"A bowl of {prob.phrase} blocked the way by the hedge gate."
        ),
        QAItem(
            question=f"Who warned {hero.id} about the mess?",
            answer=f"{mentor.id}, the glowing beetle, warned {hero.id} that the mash would smear the path."
        ),
        QAItem(
            question=f"What tool helped solve the problem?",
            answer=f"{tool.phrase} helped {hero.id} scoop the berry mash aside."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The path opened, the hedge shimmered, and {hero.id} kept exploring."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hedge?",
            answer="A hedge is a thick row of bushes or small shrubs that can form a green wall."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn more by looking, asking, and exploring."
        ),
        QAItem(
            question="What does problem solving mean?",
            answer="Problem solving means noticing what is wrong and finding a careful way to fix it."
        ),
        QAItem(
            question="What is magic in a fable?",
            answer="Magic is a special kind of wonder that can make ordinary things feel alive and meaningful."
        ),
    ]


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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="field", activity="explore", problem="berry_mash", tool="leaf_scoop",
                name="Pip", gender="boy", mentor="beetle", trait="curious"),
    StoryParams(place="garden", activity="explore", problem="berry_mash", tool="leaf_scoop",
                name="Mina", gender="girl", mentor="beetle", trait="thoughtful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "problem", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        prob = _safe_lookup(PROBLEMS, getattr(args, "problem", None))
        if prob.action_block != act.id:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, problem = rng.choice(list(combos))
    hero_type = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if hero_type == "boy" else GIRL_NAMES)
    mentor = getattr(args, "mentor", None) or "beetle"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, problem=problem, tool="leaf_scoop",
                       name=name, gender=hero_type, mentor=mentor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PROBLEMS, params.problem),
                 _safe_lookup(TOOLS, params.tool), params.name, params.gender, params.mentor, params.trait)
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
valid(Place, Act, Prob) :- affords(Place, Act), problem(Prob), blocks(Prob, Act).
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
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("blocks", pid, p.action_block))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
    ap = argparse.ArgumentParser(description="A fable-like world of hedge, mash, explore, magic, curiosity, and problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
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
