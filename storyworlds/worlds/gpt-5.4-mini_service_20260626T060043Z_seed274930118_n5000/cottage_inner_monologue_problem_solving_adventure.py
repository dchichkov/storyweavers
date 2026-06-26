#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cottage_inner_monologue_problem_solving_adventure.py
==============================================================================================================

A compact storyworld about a child at a cottage who uses inner monologue and
problem solving to turn a small obstacle into an adventure.

Seed tale sketch:
---
A child staying at a cottage wants to follow a little map into the woods.
A gate is stuck, the path is getting dark, and the child can feel worry rise
up. The child thinks through the problem, notices a useful tool, makes a plan,
and solves the obstacle. The final image is not just that the child got to the
destination, but that they became braver by thinking it through.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "grandfather", "man"}:
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
class Adventure:
    id: str
    goal: str
    route: str
    delight: str
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
class Problem:
    id: str
    obstacle: str
    risk: str
    meter: str
    clue: str
    zone: str
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
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    helps: set[str]
    action: str
    result: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        return clone


def _gate_risk(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    prob = world.facts.get("problem")
    if not prob:
        return out
    if hero.meters.get(prob.meter, 0.0) < THRESHOLD:
        return out
    sig = ("risk", prob.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    out.append(f"The obstacle felt bigger for a moment.")
    return out


CAUSAL_RULES = [ _gate_risk ]


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


@dataclass
class StoryParams:
    setting: str
    adventure: str
    problem: str
    tool: str
    name: str
    gender: str
    companion: str
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


SETTINGS = {
    "cottage": Setting(place="the cottage", indoor=True, affords={"map", "lantern", "gate"}),
    "garden": Setting(place="the cottage garden", indoor=False, affords={"gate", "path"}),
    "woods": Setting(place="the woods behind the cottage", indoor=False, affords={"path", "river"}),
}

ADVENTURES = {
    "woods_path": Adventure(
        id="woods_path",
        goal="follow the little map to the old oak in the woods",
        route="walk from the cottage path toward the trees",
        delight="the leaves sounded like tiny whispers",
        weather="dusk",
        keyword="woods",
        tags={"woods", "path", "map"},
    ),
    "garden_gate": Adventure(
        id="garden_gate",
        goal="reach the moonlit garden beyond the gate",
        route="step out into the garden path",
        delight="the flowers looked silver in the evening light",
        weather="dusk",
        keyword="garden",
        tags={"garden", "gate"},
    ),
    "river_walk": Adventure(
        id="river_walk",
        goal="follow the river trail and find where it curved around the hill",
        route="head down the path past the cottage fence",
        delight="the water flashed like ribbon",
        weather="dusk",
        keyword="river",
        tags={"river", "path"},
    ),
}

PROBLEMS = {
    "dark_path": Problem(
        id="dark_path",
        obstacle="the path was getting too dark to read",
        risk="the child could miss a root or step off the trail",
        meter="darkness",
        clue="a lantern by the door would help",
        zone="path",
        tags={"dark", "lantern", "path"},
    ),
    "stuck_gate": Problem(
        id="stuck_gate",
        obstacle="the garden gate was stuck shut",
        risk="the child could not reach the adventure trail",
        meter="stuck",
        clue="a key on the hook by the window could open it",
        zone="gate",
        tags={"gate", "key"},
    ),
    "high_shelf": Problem(
        id="high_shelf",
        obstacle="the map sat too high on the shelf to grab",
        risk="the child would not know which way to go",
        meter="reach",
        clue="a stool could lift the child up",
        zone="shelf",
        tags={"map", "stool"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="the lantern by the door",
        solves={"dark_path"},
        helps={"path"},
        action="light the lantern and hold it close",
        result="the trail became easy to read",
    ),
    "key": Tool(
        id="key",
        label="a brass key",
        phrase="the key on the hook by the window",
        solves={"stuck_gate"},
        helps={"gate"},
        action="turn the key in the gate lock",
        result="the gate swung open with a small creak",
    ),
    "stool": Tool(
        id="stool",
        label="a wooden stool",
        phrase="the little stool beside the pantry",
        solves={"high_shelf"},
        helps={"shelf"},
        action="stand on the stool and reach up carefully",
        result="the map came down safely",
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Luna", "Nora", "Elsie", "Ruby"]
BOY_NAMES = ["Finn", "Jasper", "Theo", "Nico", "Eli", "Otis"]
TRAITS = ["curious", "brave", "careful", "spirited", "patient", "hopeful"]
COMPANIONS = ["grandmother", "grandfather"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for a in ADVENTURES:
            for p in PROBLEMS:
                t = next((tid for tid, tool in TOOLS.items() if p in tool.solves), None)
                if t:
                    combos.append((s, a, p))
    return combos


def reasoned_fix(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS.values():
        if problem.id in tool.solves:
            return tool
    return None


def _maybe_risk(world: World) -> list[str]:
    hero = world.entities["hero"]
    problem: Problem = _safe_fact(world, world.facts, "problem")
    if hero.meters.get(problem.meter, 0.0) >= THRESHOLD:
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
        return [f"{hero.id} felt a little worry knot in {hero.pronoun('possessive')} chest."]
    return []


def tell(setting: Setting, adventure: Adventure, problem: Problem, tool: Tool,
         name: str, gender: str, companion: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=gender, label=name))
    guide = world.add(Entity(id="guide", kind="character", type=companion, label=companion))
    item = world.add(Entity(id="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))
    hero.meters["curiosity"] = 1
    hero.memes["hope"] = 1
    world.facts.update(hero=hero, guide=guide, tool=item, problem=problem, adventure=adventure, setting=setting)

    world.say(f"{name} was a {trait} {gender} staying at {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved adventure, especially when {adventure.delight}.")
    world.say(f"That evening, {hero.id} wanted to {adventure.goal}, but {problem.obstacle}.")
    world.para()
    world.say(f'Inside {hero.id}\'s head, a quiet thought began: "{problem.clue}."')
    world.say(f"{hero.id} looked again and thought, \"What can I use to {tool.action.replace(' and hold it close', '').replace(' and reach up carefully', '').replace(' in the gate lock', '')}?\"")
    hero.meters[problem.meter] = 1
    propagate(world, narrate=True)
    world.para()
    hero.memes["determination"] = hero.memes.get("determination", 0.0) + 1
    world.say(f"{hero.id} took {tool.phrase} and decided to try.")
    if tool.id == "lantern":
        world.say(f"{hero.id} {tool.action}, and {tool.result}.")
    elif tool.id == "key":
        world.say(f"{hero.id} {tool.action}, and {tool.result}.")
    else:
        world.say(f"{hero.id} {tool.action}, and {tool.result}.")
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(f"Then {hero.id} could {adventure.route}, and {guide.label} smiled beside {hero.pronoun('object')}.")
    world.say(f"At the end, {hero.id} was still in the cottage world, but now the problem was solved and the adventure could go on.")
    return world


KNOWLEDGE = {
    "cottage": [("What is a cottage?", "A cottage is a small house, often cozy and close to nature.")],
    "lantern": [("What does a lantern do?", "A lantern gives light so people can see in the dark.")],
    "key": [("What is a key for?", "A key opens a lock or a door.")],
    "stool": [("What is a stool?", "A stool is a small seat, and people can also stand on one to reach higher places carefully.")],
    "map": [("What is a map?", "A map is a picture that shows where places are and how to get there.")],
    "woods": [("What are woods?", "Woods are a place with many trees, where paths can twist and turn.")],
    "gate": [("What is a gate?", "A gate is a door in a fence or wall that can open and close.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    adv: Adventure = _safe_fact(world, f, "adventure")
    prob: Problem = _safe_fact(world, f, "problem")
    return [
        f'Write a short adventure story for a young child about {hero.id} at a cottage, using a quiet inner thought and a practical fix.',
        f"Tell a gentle story where {hero.id} wants to {adv.goal} but {prob.obstacle}, and the child solves it by thinking.",
        f'Write a story that includes the word "{adv.keyword}" and ends with a solved problem near the cottage.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    adv: Adventure = _safe_fact(world, f, "adventure")
    prob: Problem = _safe_fact(world, f, "problem")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    qa = [
        QAItem(
            question=f"What did {hero.label} want to do at the cottage?",
            answer=f"{hero.label} wanted to {adv.goal}.",
        ),
        QAItem(
            question=f"What was the problem that made the adventure hard?",
            answer=f"{prob.obstacle.capitalize()}, so {hero.label} needed to think of a solution.",
        ),
        QAItem(
            question=f"What did {hero.label} notice that helped with the problem?",
            answer=f"{tool.phrase} helped, because it was the right thing to {tool.action}.",
        ),
        QAItem(
            question=f"Who was nearby while {hero.label} solved the problem?",
            answer=f"{guide.label.capitalize()} was nearby and smiled when the problem was solved.",
        ),
        QAItem(
            question=f"How did {hero.label} solve the trouble in the story?",
            answer=f"{hero.label} paused, thought it through, and used {tool.label} to fix the problem.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    adv: Adventure = _safe_fact(world, world.facts, "adventure")
    prob: Problem = _safe_fact(world, world.facts, "problem")
    tags |= adv.tags
    tags |= prob.tags
    if world.facts["tool"].id in KNOWLEDGE:
        tags.add(world.facts["tool"].id)
    out: list[QAItem] = []
    for tag in ["cottage", "map", "woods", "gate", "lantern", "key", "stool"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="cottage", adventure="woods_path", problem="dark_path", tool="lantern",
                name="Mina", gender="girl", companion="grandmother", trait="curious"),
    StoryParams(setting="cottage", adventure="garden_gate", problem="stuck_gate", tool="key",
                name="Finn", gender="boy", companion="grandfather", trait="brave"),
    StoryParams(setting="cottage", adventure="woods_path", problem="high_shelf", tool="stool",
                name="Luna", gender="girl", companion="grandmother", trait="careful"),
]


def explain_rejection(problem: Problem, tool: Tool) -> str:
    return f"(No story: {tool.label} does not solve {problem.id}; the fix would not be honest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a cottage adventure powered by inner monologue and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "problem", None) and getattr(args, "tool", None):
        if getattr(args, "problem", None) not in _safe_lookup(TOOLS, getattr(args, "tool", None)).solves:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "adventure", None) is None or c[1] == getattr(args, "adventure", None))
        and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, adventure, problem = rng.choice(list(filtered))
    tool_id = getattr(args, "tool", None) or next(t.id for t in TOOLS.values() if problem in t.solves)
    tool = _safe_lookup(TOOLS, tool_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, adventure=adventure, problem=problem, tool=tool.id,
                       name=name, gender=gender, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ADVENTURES, params.adventure), _safe_lookup(PROBLEMS, params.problem),
                 _safe_lookup(TOOLS, params.tool), params.name, params.gender, params.companion, params.trait)
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
adventure(A) :- adventure_id(A).
problem(P) :- problem_id(P).
tool(T) :- tool_id(T).

fixable(P,T) :- solves(T,P).
valid(S,A,P,T) :- setting(S), adventure(A), problem(P), tool(T), fixable(P,T).
#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ADVENTURES:
        lines.append(asp.fact("adventure_id", aid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_id", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        for p in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((s, a, p) for s, a, p in valid_combos())
    cl = set((s, a, p) for s, a, p, _t in asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, a, p, t in combos:
            print(f"  {s:8} {a:12} {p:10} {t}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
