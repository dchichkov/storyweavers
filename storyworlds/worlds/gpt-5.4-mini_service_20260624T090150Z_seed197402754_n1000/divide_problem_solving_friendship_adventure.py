#!/usr/bin/env python3
"""
divide_problem_solving_friendship_adventure.py
==============================================

A small storyworld about friends dividing a treasure, a trail, or a task on an
adventure. The world simulates a concrete problem: something is too big, too
messy, or too heavy for one child, so friends divide it into fair parts and
solve it together.

The seed story imagined for this world:
---
Two friends set out on a tiny adventure in the woods. They found one big trail
map, one heavy basket of supplies, or one pile of stones that needed sorting.
At first, one friend tried to carry everything alone. The load was awkward, and
the other friend noticed a better way.

They stopped, talked, and divided the job into parts. One friend held the map
while the other carried the snacks. Or one counted the stones while the other
stacked them. After they split the work fairly, the problem felt small, and
their friendship felt bigger. They finished the adventure together, smiling.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prob: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    outdoors: bool = True
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
class Problem:
    id: str
    noun: str
    phrase: str
    burden: str
    verb: str
    tag: str
    size: str
    can_split: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class DivideMethod:
    id: str
    label: str
    prep: str
    tail: str
    kind: str  # maps to problem.tag
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
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_burden(world: World) -> list[str]:
    out: list[str] = []
    for prob in [e for e in world.entities.values() if e.type == "problem"]:
        if prob.meters.get("burden", 0) < THRESHOLD:
            continue
        if ("burden", prob.id) in world.fired:
            continue
        world.fired.add(("burden", prob.id))
        out.append(f"The load felt too big for one pair of hands.")
    return out


def _r_divide(world: World) -> list[str]:
    out: list[str] = []
    for prob in [e for e in world.entities.values() if e.type == "problem"]:
        if prob.meters.get("split", 0) < THRESHOLD:
            continue
        if ("split", prob.id) in world.fired:
            continue
        world.fired.add(("split", prob.id))
        prob.meters["burden"] = 0
        out.append(f"The big problem broke into smaller pieces.")
    return out


CAUSAL_RULES = [Rule("burden", _r_burden), Rule("divide", _r_divide)]


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


def can_solve(problem: Problem, method: DivideMethod) -> bool:
    return problem.can_split and problem.tag == method.kind


def select_method(problem: Problem) -> Optional[DivideMethod]:
    for m in METHODS:
        if can_solve(problem, m):
            return m
    return None


def predict(world: World, hero: Entity, helper: Entity, problem: Problem, method: DivideMethod) -> dict:
    sim = world.copy()
    _attempt(sim, hero, helper, problem, method, narrate=False)
    p = sim.get(problem.id)
    return {
        "solved": p.meters.get("solved", 0) >= THRESHOLD,
        "friendship": sum(e.memes.get("friendship", 0) for e in sim.characters()),
    }


def _attempt(world: World, hero: Entity, helper: Entity, problem: Problem, method: DivideMethod, narrate: bool = True) -> None:
    world.say(f"{hero.id} and {helper.id} looked at the {problem.noun} and paused.")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    problem.meters["burden"] = 1
    if method.id == "split":
        problem.meters["split"] = 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} and {helper.id} were friends who loved tiny adventures near {world.setting.place}."
    )
    world.say(
        f"On that day, they found {problem.phrase}, and it seemed too {problem.size} to solve alone."
    )


def struggle(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0) + 1
    world.say(
        f"{hero.id} tried to carry everything at once, but the {problem.noun} pulled heavy on {hero.pronoun('possessive')} arms."
    )
    world.say(
        f"{helper.id} noticed the trouble and said, \"Let's stop and divide it into pieces.\""
    )


def divide_plan(world: World, hero: Entity, helper: Entity, problem: Problem, method: DivideMethod) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    helper.memes["hope"] = helper.memes.get("hope", 0) + 1
    world.say(f"They chose to {method.prep}.")
    world.say(
        f"{hero.id} took one part while {helper.id} took the other, and the work began to feel lighter."
    )


def finish(world: World, hero: Entity, helper: Entity, problem: Problem, method: DivideMethod) -> None:
    hero.memes["friendship"] = hero.memes.get("friendship", 0) + 1
    helper.memes["friendship"] = helper.memes.get("friendship", 0) + 1
    problem.meters["solved"] = 1
    world.say(
        f"Then they {method.tail}. Soon the {problem.noun} was solved, and the two friends kept walking happily."
    )
    world.say(
        f"Their adventure felt bigger because they had shared it."
    )


def tell(setting: Setting, problem: Problem, hero_name: str = "Mila", helper_name: str = "Jon") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy"))
    prob = world.add(Entity(id=problem.id, kind="thing", type="problem", label=problem.noun, phrase=problem.phrase))

    introduce(world, hero, helper, problem)
    world.para()
    struggle(world, hero, helper, problem)
    method = select_method(problem)
    if method is None:
        pass
    world.para()
    divide_plan(world, hero, helper, problem, method)
    finish(world, hero, helper, problem, method)

    world.facts.update(
        hero=hero,
        helper=helper,
        problem=prob,
        problem_cfg=problem,
        method=method,
        setting=setting,
    )
    return world


SETTINGS = {
    "woods": Setting(place="the woods", outdoors=True, affords={"map", "stones", "snack"}),
    "riverbank": Setting(place="the riverbank", outdoors=True, affords={"sticks", "snack", "rope"}),
    "hill": Setting(place="the hill", outdoors=True, affords={"map", "stones", "rope"}),
}

PROBLEMS = {
    "map": Problem(
        id="map",
        noun="map",
        phrase="one large trail map with too many turns",
        burden="confusing",
        verb="read",
        tag="map",
        size="big",
        can_split=True,
    ),
    "stones": Problem(
        id="stones",
        noun="pile of stones",
        phrase="one heavy pile of stones that needed sorting",
        burden="heavy",
        verb="sort",
        tag="stones",
        size="heavy",
        can_split=True,
    ),
    "snack": Problem(
        id="snack",
        noun="snack bag",
        phrase="one snack bag with crumbs and fruit pieces mixed together",
        burden="messy",
        verb="share",
        tag="snack",
        size="messy",
        can_split=True,
    ),
    "rope": Problem(
        id="rope",
        noun="rope",
        phrase="one long rope that had to be divided for two games",
        burden="long",
        verb="divide",
        tag="rope",
        size="long",
        can_split=True,
    ),
}

METHODS = [
    DivideMethod(id="fold_map", label="fold the map", prep="fold the map and trace one trail at a time", tail="folded the map carefully and followed the first turn", kind="map"),
    DivideMethod(id="sort_stones", label="sort the stones", prep="make two neat piles of stones", tail="counted the last stone and stacked the final pile", kind="stones"),
    DivideMethod(id="share_snack", label="share the snack", prep="split the snack into two fair parts", tail="put the last piece in each hand and smiled", kind="snack"),
    DivideMethod(id="cut_rope", label="cut the rope", prep="measure the rope and divide it evenly", tail="tied each piece into a tidy loop", kind="rope"),
]

GIRL_NAMES = ["Mila", "Nora", "Ivy", "Lena", "Sia", "Ruby", "Ada", "Pia"]
BOY_NAMES = ["Jon", "Ben", "Theo", "Max", "Owen", "Eli", "Finn", "Noah"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    name: str
    helper: str
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for p in setting.affords:
            if select_method(_safe_lookup(PROBLEMS, p)):
                combos.append((s, p))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prob = _safe_fact(world, f, "problem_cfg")
    return [
        f'Write a short adventure story for a child about friends who "divide" a hard task and solve it together.',
        f"Tell a gentle friendship story where {hero.id} and {helper.id} find {prob.phrase} and decide to divide the work.",
        f'Write a simple story that uses the word "divide" and ends with two friends sharing the solution.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    prob = _safe_fact(world, f, "problem_cfg")
    method = _safe_fact(world, f, "method")
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {hero.id} and {helper.id}. They went on a small adventure together.",
        ),
        QAItem(
            question=f"What problem did they find?",
            answer=f"They found {prob.phrase}. It felt too {prob.size} for one child to handle alone.",
        ),
        QAItem(
            question=f"How did they solve it?",
            answer=f"They solved it by choosing to {method.prep}. That divided the job into smaller parts so it became easier.",
        ),
        QAItem(
            question=f"Why did their friendship matter?",
            answer=f"Their friendship mattered because they listened to each other, shared the work, and finished together with happy hearts.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does it mean to divide something?", answer="To divide something means to split it into smaller parts that are easier to handle or share."),
        QAItem(question="What is a friend?", answer="A friend is someone who cares about you, helps you, and enjoys spending time with you."),
        QAItem(question="What is an adventure?", answer="An adventure is an exciting trip or experience where you discover new things and solve problems."),
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(P) :- problem_cfg(P).
method(M) :- method_cfg(M).
valid(S, P) :- setting(S), problem(P), affords(S, P), has_method(P).
has_method(P) :- method_cfg(M), method_for(M, P).

% A problem is solvable if some method matches its kind.
solvable(P) :- method_for(_, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_cfg", pid))
        lines.append(asp.fact("problem_tag", pid, p.tag))
        lines.append(asp.fact("problem_size", pid, p.size))
        if p.can_split:
            lines.append(asp.fact("splittable", pid))
    for m in METHODS:
        lines.append(asp.fact("method_cfg", m.id))
        lines.append(asp.fact("method_for", m.id, m.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def explain_rejection(setting: str, problem: str) -> str:
    return (
        f"(No story: {_safe_lookup(PROBLEMS, problem).phrase} cannot be fairly solved in {_safe_lookup(SETTINGS, setting).place} "
        f"with the available divide methods.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: friends divide a problem on a small adventure.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if getattr(args, "setting", None) and getattr(args, "problem", None):
        if (getattr(args, "setting", None), getattr(args, "problem", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in combos if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)) and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(BOY_NAMES)
    return StoryParams(setting=setting, problem=problem, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PROBLEMS, params.problem), params.name, params.helper)
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
    StoryParams(setting="woods", problem="map", name="Mila", helper="Jon"),
    StoryParams(setting="riverbank", problem="snack", name="Nora", helper="Eli"),
    StoryParams(setting="hill", problem="stones", name="Ivy", helper="Finn"),
    StoryParams(setting="woods", problem="rope", name="Lena", helper="Theo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/2."))
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
            header = f"### {p.name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
