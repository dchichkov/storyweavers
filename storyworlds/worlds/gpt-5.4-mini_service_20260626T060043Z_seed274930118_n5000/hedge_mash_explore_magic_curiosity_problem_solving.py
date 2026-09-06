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


@dataclass(frozen=True)
class StoryArc:
    id: str
    destination: str
    magic_sign: str
    mash_problem: str
    danger: str
    clue: str
    tool_phrase: str
    first_action: str
    helper_action: str
    result: str
    ending_image: str


STORY_ARCS = {
    arc.id: arc
    for arc in [
        StoryArc(
            id="singing_gate",
            destination="a gate where blue hedge-berries sang directions",
            magic_sign="three blue berries chimed whenever the correct path opened",
            mash_problem="sticky berry mash had sealed the singing gate's root-latch",
            danger="Pulling the gate would snap the roots that made the berries sing.",
            clue="one clean root twitched whenever a drop of rain touched it",
            tool_phrase="a curled dock leaf and a hollow acorn cup",
            first_action="lifted the thick mash with the dock leaf, one patient scoop at a time",
            helper_action="tapped a quiet rhythm while the acorn cup rinsed the latch",
            result="the root-latch loosened and the blue berries sang the left-hand path",
            ending_image="the open gate hummed behind them while three clean berries shone like tiny bells",
        ),
        StoryArc(
            id="moon_maze",
            destination="a moonlit maze said to hide a silver seed",
            magic_sign="pale arrows appeared on the hedge only when moonlight touched their leaves",
            mash_problem="purple mash had splashed over the first two moon-arrows",
            danger="Guessing at the turns could lead an explorer in circles until dawn.",
            clue="an uncovered arrow pointed toward a puddle clear enough to reflect the moon",
            tool_phrase="a fan of fern fronds and a shell of clear water",
            first_action="brushed away the lumpy mash without tearing the arrow-shaped leaves",
            helper_action="held moonlight in the water shell so each cleaned arrow gleamed",
            result="the restored arrows led to the silver seed and then safely home",
            ending_image="the silver seed rested in an acorn cap as moon-arrows glimmered all the way back",
        ),
        StoryArc(
            id="sleeping_topiary",
            destination="a round clearing where animal-shaped hedges woke to dance",
            magic_sign="a leafy rabbit yawned and wiggled one green ear",
            mash_problem="warm apple mash had glued the little wake-up bells together",
            danger="Shaking the bells hard would frighten the sleeping topiary animals.",
            clue="the mash softened where a patch of mint made the air cool",
            tool_phrase="cool mint leaves wrapped around a smooth twig",
            first_action="pressed the mint against each bell and eased the mash from its rim",
            helper_action="caught every loosened blob before it could fall on a sleeping animal",
            result="the bells rang softly and the leafy rabbit led a quiet green parade",
            ending_image="a fox-shaped hedge bowed beneath the stars while the clean bells tinkled good night",
        ),
        StoryArc(
            id="living_library",
            destination="a hidden library whose stories grew as words on leaves",
            magic_sign="golden letters traveled from leaf to leaf like patient fireflies",
            mash_problem="red mash had covered the vine that indexed every leafy book",
            danger="Wiping at random might mix the titles and send each story to the wrong branch.",
            clue="tiny stem marks divided the index into neat rows",
            tool_phrase="a grass blade used as a ruler and a pad of soft moss",
            first_action="cleaned one indexed row at a time, checking each stem mark before moving on",
            helper_action="read the returning golden titles aloud so none slipped onto the wrong branch",
            result="the index vine found every story and opened a tale about a cloud ship",
            ending_image="one clean story-leaf turned its own page as golden words drifted across it",
        ),
        StoryArc(
            id="cloud_bridge",
            destination="the hedge's high arch, where a leaf bridge crossed into a cloud garden",
            magic_sign="silver dew climbed upward instead of falling to the ground",
            mash_problem="oat mash had made the narrow leaf bridge heavy and slick",
            danger="Stepping onto it too soon could bend the bridge away from its supporting vines.",
            clue="the bridge rose a little whenever a breeze passed beneath a clean section",
            tool_phrase="two broad bark scrapers and a woven-grass basket",
            first_action="worked from the supported end, scraping the mash into the basket",
            helper_action="sent small guiding breezes beneath each newly cleaned section",
            result="the lightened bridge lifted level and carried them into the cloud garden",
            ending_image="the empty basket hung from the arch while cloud-flowers opened above the clean bridge",
        ),
        StoryArc(
            id="root_railway",
            destination="a root railway where seed-sized carriages toured the deepest hedge tunnels",
            magic_sign="a walnut carriage whistled although it had no driver",
            mash_problem="chestnut mash had packed around the switch that moved the root rails",
            danger="Forcing the switch could send the carriage toward a tunnel closed by stones.",
            clue="ants walked safely along the rail that led to the open tunnel",
            tool_phrase="a forked twig, a reed straw, and a folded leaf tray",
            first_action="loosened the mash with the twig and blew crumbs onto the leaf tray",
            helper_action="marked the safe rail with a dotted trail of beetle-light",
            result="the switch clicked toward the open tunnel and the walnut carriage rolled forward",
            ending_image="the tiny carriage carried them home with a fern ticket fluttering from its clean wheel",
        ),
        StoryArc(
            id="mirror_bower",
            destination="a mirror bower that showed which hedge creatures needed help",
            magic_sign="a dewdrop mirror briefly showed a wren beside an empty nest",
            mash_problem="blackberry mash had clouded the mirrors and joined three reflections into one blur",
            danger="Following the blurred image could send help to the wrong corner of the hedge.",
            clue="each mirror had a different flower carved beneath it",
            tool_phrase="petals matched to the carvings and a soft dandelion brush",
            first_action="cleaned the mirrors separately and set each matching petal below it",
            helper_action="shone a narrow beam on one mirror at a time",
            result="the clear wren mirror revealed a fallen twig beside the real nest",
            ending_image="the repaired nest appeared whole in one bright dewdrop as the wren tucked in a feather",
        ),
        StoryArc(
            id="winter_door",
            destination="a summer room hidden behind a frosty door in the hedge",
            magic_sign="warm green light leaked through a keyhole rimmed with snow",
            mash_problem="pear mash had frozen solid around the living wooden key",
            danger="Hot water would free the key quickly but might wake and crack the winter bark.",
            clue="sunlit pebbles melted tiny round holes without harming the bark",
            tool_phrase="a ring of sun-warmed pebbles and a strip of dry moss",
            first_action="placed the warm pebbles around the frozen mash and waited for it to soften",
            helper_action="wicked away each drop with dry moss before it froze again",
            result="the wooden key turned and the summer room breathed out the scent of strawberries",
            ending_image="snow rested beside one open summer flower while the unharmed wooden key curled back to sleep",
        ),
        StoryArc(
            id="whisper_post",
            destination="a whispering post that carried messages through the hedge roots",
            magic_sign="the post murmured half of a warning from somewhere beyond the garden",
            mash_problem="seed mash had clogged the listening holes and broken every message into riddles",
            danger="Poking the holes could push the mash deeper and silence the post completely.",
            clue="a family of ants carried loose crumbs from one hole without entering it",
            tool_phrase="a crumb trail, a paper cone, and a clean seed husk",
            first_action="used the crumb trail to draw the ants across the clogged holes",
            helper_action="caught the freed mash in the paper cone and tested each hole with the seed husk",
            result="the post clearly warned that a baby mole was lost near the orchard roots",
            ending_image="a grateful mole waved below as the whispering post carried its soft thank-you home",
        ),
        StoryArc(
            id="clockwork_hollow",
            destination="a clockwork hollow where hedge blossoms opened exactly at tea time",
            magic_sign="brass ladybugs marched around a clock with petals for hands",
            mash_problem="plum mash had gummed the smallest gear and stopped the blossom clock",
            danger="Turning the large hand would strip the tiny gear and spoil every flower's timing.",
            clue="one brass ladybug repeatedly pointed to a narrow cleaning notch",
            tool_phrase="a pine-needle hook and a twist of absorbent wool",
            first_action="drew mash through the cleaning notch instead of touching the gear teeth",
            helper_action="counted the clock's clicks and called stop when the tiny gear moved freely",
            result="the clock chimed and rows of hedge blossoms opened in a wave",
            ending_image="the last flower opened beneath the turning petal-hand as brass ladybugs rang acorn cups",
        ),
        StoryArc(
            id="floating_nursery",
            destination="a floating nursery where young hedge shoots learned to steer on the wind",
            magic_sign="three baby shrubs bobbed above the hedge in baskets of woven roots",
            mash_problem="banana mash had weighed down the lift-vines of the smallest basket",
            danger="Cutting the sticky vines would drop the basket instead of freeing it.",
            clue="clean lift-vines tightened whenever the floating seeds spun",
            tool_phrase="a spinning milkweed tuft and a spoon carved from bark",
            first_action="spun the tuft to lift one vine while scraping mash from the next",
            helper_action="balanced the basket with a thread of light as each vine tightened",
            result="the cleaned lift-vines raised the baby shrub beside its classmates",
            ending_image="three root baskets sailed across the sunset, and the smallest left a trail of clean green sparks",
        ),
        StoryArc(
            id="lantern_festival",
            destination="a lantern festival in the heart of the hedge",
            magic_sign="unlit flower lanterns whispered the colors they hoped to glow",
            mash_problem="golden mash had clogged the dew channels that fed every lantern",
            danger="Lighting dry lanterns by hand could scorch their delicate petals.",
            clue="one clear channel carried a bead of dew toward a dark blue lantern",
            tool_phrase="a hollow grass stem, a thistle brush, and a catching bowl",
            first_action="cleared each channel from the lantern end and caught the mash below",
            helper_action="sent a bead of glowing dew through every channel as it was tested",
            result="the lanterns filled safely and lit the hedge in twelve gentle colors",
            ending_image="the cleaned channels glittered under a roof of flower lanterns while the catching bowl held a golden moon",
        ),
    ]
}

OPENING_FORMS = [
    "{hero} had mapped the ordinary edge of {place}, but today {magic_sign}.",
    "At {place}, {hero} followed a question no map could answer: why had {magic_sign}?",
    "The hedge near {place} usually rustled like any hedge. Then {hero} saw that {magic_sign}.",
    "While others hurried past {place}, {hero} stopped, listened, and discovered that {magic_sign}.",
    "A curious explorer notices small impossibilities. That morning near {place}, {hero} noticed that {magic_sign}.",
    "Just after breakfast, the hedge beyond {place} performed its first bit of magic: {magic_sign}.",
]

QUESTION_FORMS = [
    '"What makes it do that?" {hero} wondered. "And where does it lead?"',
    '{hero} felt curiosity tug harder than caution, but asked, "What should we understand before we explore?"',
    'Instead of calling the sight impossible, {hero} whispered, "There must be a reason. Let us explore carefully."',
    '"A mystery is an invitation to look," said {hero}. "Not an invitation to rush."',
    '{hero} wanted to explore at once, yet took one slow breath and asked what the hedge might be showing them.',
    'Curiosity filled {hero} with questions: what had changed, what might break, and what clue had been left behind?',
]

PLAN_FORMS = [
    "{hero} compared the clean parts with the messy ones and noticed that {clue}.",
    "Kneeling beside the mash, {hero} checked the edges first. That careful search revealed that {clue}.",
    "They drew a little plan in the soil: observe, test one small spot, then repair. During the first step, {hero} saw that {clue}.",
    "Rather than blame the magic, {hero} traced cause and effect until it was clear that {clue}.",
    "{mentor} lit the scene from three sides while {hero} looked for a pattern. Soon they found that {clue}.",
    "{hero} asked what was different, what was still working, and what could be tested safely. The answer was that {clue}.",
    "A rushed solution would only move the mess. {hero} studied the hedge until it became apparent that {clue}.",
    "First {hero} watched. Next came a gentle test. Only then did the clue make sense: {clue}.",
]

DIALOGUE_FORMS = [
    '"So the mash is not the whole puzzle," {hero} said. "We must protect what is underneath it." "Exactly," replied {mentor}.',
    '"Tell me your plan before you begin," said {mentor}. {hero} explained it step by step, and together they found one risky step to change.',
    '"Could we force it?" asked {mentor}. "We could," said {hero}, "but solving a problem means fixing the cause without making a new one."',
    '"I will handle the tool," said {hero}. "Then I will watch the fragile part," {mentor} answered. Their two jobs fit together.',
    '{mentor} asked, "What will show us that the plan is working?" {hero} pointed to the clue and named the change they expected to see.',
    '"Small test first," {hero} decided. {mentor} nodded. "And if the hedge responds well, we continue."',
]

ACTION_FORMS = [
    "Using {tool}, {hero} {first_action}. Meanwhile, {mentor} {helper_action}.",
    "Their first careful test worked, so {hero} {first_action}. Beside them, {mentor} {helper_action}.",
    "The work took patience: {hero} {first_action}; at the same time, {mentor} {helper_action}.",
    "They divided the problem into two useful jobs. {hero} {first_action}, while {mentor} {helper_action}.",
    "With {tool}, the plan became action. {hero} {first_action}, and {mentor} {helper_action}.",
    "Nothing was yanked or hurried. {hero} {first_action}. To keep the repair safe, {mentor} {helper_action}.",
]

REFLECTION_FORMS = [
    "That was problem solving: curiosity had found the clue, but patience had turned it into a safe answer.",
    "{hero} understood that curiosity asks the first question, while problem solving tests the answer.",
    "The magic had not solved the difficulty for them. It had waited for curiosity, evidence, and a careful plan.",
    "Exploring meant more than going forward. Sometimes it meant stopping long enough to leave a place better than they found it.",
    "A clever answer was not merely quick; it explained the clue, protected the hedge, and repaired the real cause.",
    "{mentor} called it hedge magic. {hero} called it looking closely enough to know what to do next.",
]


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
    arc: str = "singing_gate"
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
         hero_name: str, hero_type: str, mentor_name: str, trait: str,
         arc: StoryArc, rng: random.Random) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["small", trait]))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="sprite", label="the glowing beetle"))
    prob = world.add(Entity(
        id=problem.id,
        kind="problem",
        type="problem",
        label="the mash problem",
        phrase=arc.mash_problem,
    ))
    t = world.add(Entity(
        id=tool.id,
        type="tool",
        label=arc.tool_phrase,
        phrase=arc.tool_phrase,
        protective=True,
    ))
    t.worn_by = hero.id

    place = setting.place
    mentor_ref = mentor.id.capitalize()
    opening = rng.choice(OPENING_FORMS).format(
        hero=hero.id,
        place=place,
        magic_sign=arc.magic_sign,
    )
    world.say(
        f"{hero.id} was a small {trait} {hero.type} who loved to explore; "
        "curiosity often led to the best questions."
    )
    world.say(f"Beside {hero.id} floated {mentor_ref}, a glowing beetle whose gentle magic lit hidden details.")
    world.say(opening)
    world.para()
    world.say(f"Beyond the outer hedge lay {arc.destination}.")
    world.say(rng.choice(QUESTION_FORMS).format(hero=hero.id))
    _to_memes(hero, "curiosity", 1.0)
    _to_meters(hero, "explore", 1.0)
    world.say(
        f"At the entrance, however, {arc.mash_problem}. "
        f"{mentor_ref} warned, \"{arc.danger}\""
    )
    _to_meters(prob, "blocked", 1.0)
    _to_memes(hero, "worry", 1.0)

    world.para()
    world.say(rng.choice(PLAN_FORMS).format(
        hero=hero.id,
        mentor=mentor_ref,
        clue=arc.clue,
    ))
    _to_meters(hero, "observed", 1.0)
    _to_memes(hero, "problem_solving", 1.0)
    world.say(rng.choice(DIALOGUE_FORMS).format(hero=hero.id, mentor=mentor_ref))
    world.say(rng.choice(ACTION_FORMS).format(
        hero=hero.id,
        mentor=mentor_ref,
        tool=arc.tool_phrase,
        first_action=arc.first_action,
        helper_action=arc.helper_action,
    ))
    _to_meters(prob, "blocked", -1.0)

    world.para()
    result_forms = [
        "Their reasoning proved sound: {result}.",
        "A final careful check confirmed the change. Now {result}.",
        "The hedge answered with a rustle of magic, and {result}.",
        "Cause by cause, the trouble was gone; {result}.",
        "For a breath, everything stayed still. Then {result}.",
        "The repair held. Better still, {result}.",
    ]
    world.say(rng.choice(result_forms).format(result=arc.result))
    world.say("Their problem solving had removed the cause of the trouble, not merely hidden the mash.")
    world.say(rng.choice(REFLECTION_FORMS).format(hero=hero.id, mentor=mentor_ref))
    world.say(f"When the exploring was done, {arc.ending_image}.")
    _to_memes(hero, "joy", 1.0)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        problem=prob,
        tool=t,
        activity=activity,
        setting=setting,
        arc=arc.id,
        destination=arc.destination,
        danger=arc.danger,
        clue=arc.clue,
        action=arc.first_action,
        helper_action=arc.helper_action,
        result=arc.result,
        ending=arc.ending_image,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    prob: Entity = _safe_fact(world, f, "problem")
    return [
        f"Write a child-friendly magical story about a curious {hero.type} exploring {f['destination']}.",
        f"Tell how {hero.id} investigates why {prob.phrase}, then solves the underlying problem without causing new harm.",
        f"Write a hedge adventure in which curiosity reveals that {f['clue']}, leading to careful problem solving.",
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
            question=f"What magical place did {hero.id} want to explore near {place}?",
            answer=f"{hero.id} wanted to explore {f['destination']} near {place}."
        ),
        QAItem(
            question="What mash problem blocked the exploration?",
            answer=f"The exploration was blocked because {prob.phrase}."
        ),
        QAItem(
            question=f"What clue rewarded {hero.id}'s curiosity?",
            answer=f"By looking closely, {hero.id} discovered that {f['clue']}."
        ),
        QAItem(
            question=f"How did {hero.id} and {mentor.id} solve the problem together?",
            answer=f"Using {tool.phrase}, {hero.id} {f['action']}, while {mentor.id} {f['helper_action']}."
        ),
        QAItem(
            question="What proved that their problem-solving plan worked?",
            answer=f"Their plan worked because {f['result']}; at the end, {f['ending']}."
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
                name="Pip", gender="boy", mentor="beetle", trait="curious", arc="singing_gate"),
    StoryParams(place="garden", activity="explore", problem="berry_mash", tool="leaf_scoop",
                name="Mina", gender="girl", mentor="beetle", trait="thoughtful", arc="moon_maze"),
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
    arc = getattr(args, "arc", None) or rng.choice(list(STORY_ARCS))
    return StoryParams(place=place, activity=activity, problem=problem, tool="leaf_scoop",
                       name=name, gender=hero_type, mentor=mentor, trait=trait, arc=arc)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else f"{params.name}:{params.arc}")
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PROBLEMS, params.problem),
                 _safe_lookup(TOOLS, params.tool), params.name, params.gender, params.mentor, params.trait,
                 _safe_lookup(STORY_ARCS, params.arc), rng)
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
    ap.add_argument("--arc", choices=STORY_ARCS)
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
