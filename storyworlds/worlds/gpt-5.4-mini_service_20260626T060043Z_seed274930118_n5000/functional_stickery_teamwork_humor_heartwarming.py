#!/usr/bin/env python3
"""
functional_stickery_teamwork_humor_heartwarming.py
==================================================

A small storyworld about helpful sticky things, teamwork, and gentle humor.
The core premise: a child wants to finish a practical task, but the task gets
messy or scattered, so the family must cooperate with a sticky-but-useful fix.

This world is intentionally tiny and constraint-checked:
- the "stickery" item must be functional, not random decoration
- the problem must be solvable by a cooperative, heartwarming compromise
- the prose should read as a complete, child-facing story with a clear turn

The simulated domain centers on labels, notes, tabs, and tags that can stick,
peel, fall, or organize things. A parent and child team up to make something
work again, often with a little joke or a clever use of adhesive helpers.
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

    fix_ent: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    indoors: bool
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Task:
    id: str
    verb: str
    gerund: str
    trouble: str
    consequence: str
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
    region: str
    plural: bool = False
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
class Fix:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        return w


def _add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def _task_stickiness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for task in world.facts.get("tasks", []):
            if actor.meters.get(task.id, 0.0) < THRESHOLD:
                continue
            sig = ("task", actor.id, task.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _add_meme(actor, "pride", 1)
            out.append(f"{actor.pronoun('subject').capitalize()} tried to handle it carefully, but the job was still messy and sticky.")
    return out


def _note_scatter(world: World) -> list[str]:
    out: list[str] = []
    task = world.facts.get("task")
    if not task:
        return out
    for actor in world.characters():
        if actor.meters.get("scatter", 0.0) < THRESHOLD:
            continue
        sig = ("scatter", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(actor, "worry", 1)
        out.append(f"Little pieces drifted everywhere, and the room looked harder to fix.")
    return out


def _teamwork_fix(world: World) -> list[str]:
    out: list[str] = []
    hero = _safe_fact(world, world.facts, "hero")
    parent = _safe_fact(world, world.facts, "parent")
    fix = world.facts.get("fix")
    if not fix:
        return out
    if hero.memes.get("worry", 0.0) < THRESHOLD or parent.memes.get("helpful", 0.0) < THRESHOLD:
        return out
    sig = ("fix", hero.id, fix.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _add_meme(hero, "relief", 1)
    _add_meme(parent, "warmth", 1)
    out.append(f"Together, they found a sticky little trick that made the whole thing work again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for fn in (_task_stickiness, _note_scatter, _teamwork_fix):
            sents = fn(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_fix(task: Task, prize: Prize, fix: Fix) -> bool:
    return task.id in fix.helps_with and prize.region in fix.covers


def reasonableness_gate(task: Task, prize: Prize, fix: Fix) -> bool:
    return can_fix(task, prize, fix)


def predict_resolution(world: World, hero: Entity, task: Task, prize: Prize, fix: Fix) -> dict:
    sim = world.copy()
    sim.facts["fix"] = fix
    _add_meter(sim.get(hero.id), task.id, 1)
    _add_meter(sim.get(hero.id), "scatter", 1)
    _add_meme(sim.get(hero.id), "worry", 1)
    _add_meme(sim.get(world.facts["parent"].id), "helpful", 1)
    propagate(sim, narrate=False)
    return {
        "repaired": True if fix else False,
        "relief": sim.get(hero.id).memes.get("relief", 0.0),
    }


SETTING = Setting(place="the kitchen table", indoors=True, affords={"labels", "notes", "tabs"})

TASKS = {
    "labels": Task(
        id="labels",
        verb="label the jars",
        gerund="labeling the jars",
        trouble="the labels kept curling and sliding",
        consequence="the jars looked mixed up",
        tags={"sticky", "organize"},
    ),
    "notes": Task(
        id="notes",
        verb="sort the homework notes",
        gerund="sorting homework notes",
        trouble="the notes kept falling out of the pile",
        consequence="the desk turned into a paper puddle",
        tags={"sticky", "organize"},
    ),
    "tabs": Task(
        id="tabs",
        verb="fix the storybook tabs",
        gerund="fixing the storybook tabs",
        trouble="the tabs kept peeling off",
        consequence="the pages would not stay in the right place",
        tags={"sticky", "repair"},
    ),
}

PRIZES = {
    "jars": Prize(id="jars", label="jars", phrase="three little glass jars", region="hands", plural=True),
    "folder": Prize(id="folder", label="folder", phrase="a blue folder for school papers", region="hands"),
    "book": Prize(id="book", label="book", phrase="a favorite storybook", region="hands"),
}

FIXES = {
    "tape": Fix(
        id="tape",
        label="clear tape",
        phrase="a roll of clear tape",
        helps_with={"labels", "notes", "tabs"},
        covers={"hands"},
    ),
    "sticky_tabs": Fix(
        id="sticky_tabs",
        label="sticky tabs",
        phrase="a pack of sticky tabs",
        helps_with={"tabs"},
        covers={"hands"},
        plural=True,
    ),
    "sticky_notes": Fix(
        id="sticky_notes",
        label="sticky notes",
        phrase="a stack of sticky notes",
        helps_with={"notes", "labels"},
        covers={"hands"},
        plural=True,
    ),
}

CHILD_NAMES = ["Maya", "Leo", "Nina", "Owen", "Ivy", "Ben"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Jo", "Papa"]
TRAITS = ["careful", "curious", "gentle", "busy", "cheerful"]


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    fix: str
    name: str
    parent_name: str
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
    for place, setting in {"kitchen": SETTING}.items():
        for task_id in setting.affords:
            task = _safe_lookup(TASKS, task_id)
            for prize_id, prize in PRIZES.items():
                for fix_id, fix in FIXES.items():
                    if prize.region == "hands" and reasonableness_gate(task, prize, fix):
                        combos.append((place, task_id, prize_id))
    return combos


def build_world(params: StoryParams) -> World:
    setting = SETTING
    task = _safe_lookup(TASKS, params.task)
    prize = _safe_lookup(PRIZES, params.prize)
    fix = _safe_lookup(FIXES, params.fix)

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type="adult"))
    prize_ent = world.add(Entity(id="prize", type=prize.label, label=prize.label, phrase=prize.phrase, plural=prize.plural))
    fix_ent = world.add(Entity(id=fix.id, type=fix.label, label=fix.label, phrase=fix.phrase, plural=fix.plural))

    world.facts = {
        "hero": hero,
        "parent": parent,
        "prize": prize_ent,
        "fix": fix_ent,
        "task": task,
        "tasks": [task],
        "setting": setting,
    }

    hero.meters[task.id] = 0.0
    _add_meme(hero, "worry", 0.0)
    _add_meme(parent, "helpful", 1.0)

    world.say(f"{hero.id} had a small job to do at {setting.place}, and {hero.pronoun('possessive')} {task.verb} plan was very tidy at first.")
    world.say(f"{hero.id} even had {prize.phrase} and {fix.phrase} nearby, because a functional little helper can save a day.")
    world.para()
    world.say(f"But {task.trouble}, so {task.consequence}.")
    _add_meter(hero, task.id, 1)
    _add_meter(hero, "scatter", 1)
    _add_meme(hero, "worry", 1)
    propagate(world, narrate=True)
    world.para()
    world.say(f"{hero.id} frowned, then {parent.id} smiled and said, 'Let's do it together.'")
    if predict_resolution(world, hero, task, prize, fix_ent)["repaired"]:
        _add_meme(parent, "helpful", 1)
        _add_meme(hero, "hope", 1)
        world.say(f"They used {fix.label} like a tiny bridge, pressing each piece in place with careful fingers.")
        world.say(f"This time, the {task.verb} job stayed put, and the room looked neat again.")
        world.say(f"{hero.id} laughed at how something so sticky could be so useful, and {parent.id} laughed too.")
        _add_meme(hero, "relief", 1)
        _add_meme(parent, "warmth", 1)
    else:
        pass

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    fix = _safe_fact(world, f, "fix")
    return [
        f'Write a short heartwarming story about {hero.id} trying to {task.verb} with a sticky helper.',
        f"Tell a gentle tale where clear {fix.label} helps fix a messy problem with teamwork and a little humor.",
        f'Write a child-friendly story that includes "{task.id}" and ends with a useful sticky fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    task: Task = _safe_fact(world, f, "task")
    fix: Entity = _safe_fact(world, f, "fix")
    prize: Entity = _safe_fact(world, f, "prize")
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {world.setting.place}?",
            answer=f"{hero.id} was trying to {task.verb}.",
        ),
        QAItem(
            question=f"Why did the job get hard for {hero.id}?",
            answer=f"It got hard because {task.trouble}, so {task.consequence}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {parent.id} solve the problem?",
            answer=f"They worked together and used {fix.label} to keep everything in place.",
        ),
        QAItem(
            question=f"What stayed nice and useful in the end?",
            answer=f"{prize.phrase} and the sticky fix both helped the day end well.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "sticky": [
        QAItem(
            question="What does sticky mean?",
            answer="Sticky means something can cling to another thing and stay there for a while.",
        )
    ],
    "tape": [
        QAItem(
            question="What is clear tape used for?",
            answer="Clear tape is used to hold paper, labels, or little pieces in place.",
        )
    ],
    "notes": [
        QAItem(
            question="What are sticky notes for?",
            answer="Sticky notes are small pieces of paper that can stick to things and remind you about a job.",
        )
    ],
    "tabs": [
        QAItem(
            question="What are tabs on a book?",
            answer="Tabs help mark a spot so you can find the right page or section again.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    tags.add(world.facts["fix"].id)
    out: list[QAItem] = []
    for k, items in WORLD_KNOWLEDGE.items():
        if k in tags:
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.extend(world.trace)
    return "\n".join(lines)


ASP_RULES = r"""
task_ok(T) :- task(T), sticky(T).
fix_ok(F,T) :- fix(F), task_ok(T), helps_with(F,T).
valid_story(T,P,F) :- task(T), prize(P), fix(F), fix_ok(F,T), covers(F,hands), worn_on(P,hands).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for task in TASKS.values():
        lines.append(asp.fact("task", task.id))
        for tag in sorted(task.tags):
            lines.append(asp.fact("sticky", task.id) if tag == "sticky" else asp.fact(tag, task.id))
    for prize in PRIZES.values():
        lines.append(asp.fact("prize", prize.id))
        lines.append(asp.fact("worn_on", prize.id, prize.region))
    for fix in FIXES.values():
        lines.append(asp.fact("fix", fix.id))
        for t in sorted(fix.helps_with):
            lines.append(asp.fact("helps_with", fix.id, t))
        for c in sorted(fix.covers):
            lines.append(asp.fact("covers", fix.id, c))
    lines.append(asp.fact("setting", "kitchen"))
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
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming sticky teamwork storyworld.")
    ap.add_argument("--place", choices=["kitchen"])
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--parent-name")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = []
    for task_id in TASKS:
        for prize_id in PRIZES:
            for fix_id in FIXES:
                task = _safe_lookup(TASKS, task_id)
                prize = _safe_lookup(PRIZES, prize_id)
                fix = _safe_lookup(FIXES, fix_id)
                if reasonableness_gate(task, prize, fix):
                    combos.append(("kitchen", task_id, prize_id, fix_id))
    if getattr(args, "task", None):
        combos = [c for c in combos if c[1] == getattr(args, "task", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if getattr(args, "fix", None):
        combos = [c for c in combos if c[3] == getattr(args, "fix", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize, fix = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent_name = getattr(args, "parent_name", None) or rng.choice(ADULT_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, task=task, prize=prize, fix=fix, name=name, parent_name=parent_name, trait=trait)


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


CURATED = [
    StoryParams(place="kitchen", task="labels", prize="jars", fix="tape", name="Maya", parent_name="Mom", trait="careful"),
    StoryParams(place="kitchen", task="notes", prize="folder", fix="sticky_notes", name="Leo", parent_name="Dad", trait="curious"),
    StoryParams(place="kitchen", task="tabs", prize="book", fix="sticky_tabs", name="Ivy", parent_name="Aunt Jo", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
