#!/usr/bin/env python3
"""
Standalone story world: an animal tale with misunderstanding, aversion, and a
gentle transformation.

Seed impression:
---
A small animal feels aversion toward a job or place, misunderstands another
animal's intent, then changes after a kind turn and resigns from the wrong path
or role.
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
    plurality: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"fox", "rabbit", "cat", "bird", "mouse", "dog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def cap_pronoun(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()
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
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)
    feels: str = ""
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
class Task:
    id: str
    verb: str
    gerund: str
    avoid: str
    misunderstanding: str
    turn_word: str
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
class Change:
    id: str
    label: str
    phrase: str
    fits: set[str]
    helps: set[str]
    is_transformation: bool = True
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    task: str
    change: str
    name: str
    friend_name: str
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


PLACES = {
    "barn": Place("the barn", "barn", affords={"stack_hay", "carry_water"}, feels="warm"),
    "river": Place("the riverbank", "riverbank", affords={"wash_paws", "cross_stones"}, feels="cool"),
    "garden": Place("the garden", "garden", affords={"pick_carrots", "dig_soft_soil"}, feels="bright"),
    "hill": Place("the hill", "hill", affords={"watch_clouds", "guard_lambs"}, feels="windy"),
}

TASKS = {
    "stack_hay": Task(
        id="stack_hay",
        verb="stack the hay",
        gerund="stacking hay",
        avoid="scratchy dust",
        misunderstanding="thinks the dust means trouble",
        turn_word="dust",
        tags={"hay", "dust", "barn"},
    ),
    "wash_paws": Task(
        id="wash_paws",
        verb="wash the muddy paws",
        gerund="washing muddy paws",
        avoid="cold water",
        misunderstanding="thinks the splashing means a punishment",
        turn_word="water",
        tags={"water", "river"},
    ),
    "pick_carrots": Task(
        id="pick_carrots",
        verb="pick carrots",
        gerund="picking carrots",
        avoid="getting pricked by thorns",
        misunderstanding="thinks the tug on the leaf means the plant is angry",
        turn_word="leaf",
        tags={"garden", "carrot", "leaf"},
    ),
    "guard_lambs": Task(
        id="guard_lambs",
        verb="guard the lambs",
        gerund="guarding lambs",
        avoid="the loud wind",
        misunderstanding="thinks the far-off call is a scolding",
        turn_word="call",
        tags={"hill", "wind", "lamb"},
    ),
}

CHANGES = {
    "rain_boots": Change(
        id="rain_boots",
        label="rain boots",
        phrase="a pair of rain boots",
        fits={"wash_paws", "cross_stones"},
        helps={"water"},
    ),
    "soft_gloves": Change(
        id="soft_gloves",
        label="soft gloves",
        phrase="soft gloves",
        fits={"stack_hay", "pick_carrots"},
        helps={"dust", "thorn"},
    ),
    "ear_warmers": Change(
        id="ear_warmers",
        label="ear warmers",
        phrase="warm ear warmers",
        fits={"guard_lambs", "watch_clouds"},
        helps={"wind", "call"},
    ),
    "river_cloak": Change(
        id="river cloak",
        label="a river cloak",
        phrase="a bright river cloak",
        fits={"wash_paws"},
        helps={"water"},
    ),
}

ANIMAL_TYPES = ["fox", "rabbit", "cat", "dog", "mouse", "bird"]
NAMES = ["Pip", "Milo", "Tia", "Luna", "Nori", "Bram", "Kiki", "Rolo"]


def reasonableness_gate(place: Place, task: Task, change: Change) -> bool:
    return task.id in place.affords and bool(task.tags & change.helps)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with misunderstanding and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--change", choices=CHANGES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    place_key = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    task_key = getattr(args, "task", None) or rng.choice(sorted(TASKS))
    change_key = getattr(args, "change", None) or rng.choice(sorted(CHANGES))
    place, task, change = _safe_lookup(PLACES, place_key), _safe_lookup(TASKS, task_key), _safe_lookup(CHANGES, change_key)
    if not reasonableness_gate(place, task, change):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in NAMES if n != name])
    return StoryParams(place=place_key, task=task_key, change=change_key, name=name, friend_name=friend_name)


def narrate(world: World, hero: Entity, friend: Entity, task: Task, change: Change) -> None:
    world.say(f"{hero.id} was a small {hero.type} who lived near {world.place.name}.")
    world.say(f"{hero.id} liked quiet mornings, but {hero.pronoun('possessive')} heart had an aversion to {task.gerund}.")
    world.say(f"One day, {hero.id} saw {friend.id} carrying {change.phrase} and got worried.")
    world.say(f"{hero.id} misunderstood {friend.id} and thought the kind offer meant more {task.avoid}.")
    world.say(f"So {hero.id} decided to resign from the task and hide behind a hay bale.")

    world.say(f"Then {friend.id} came closer and explained that {change.phrase} would make the work easier.")
    hero.memes["misunderstanding"] += 1
    if change.id == "rain_boots":
        world.say(f"The boots kept {hero.id}'s paws dry while {hero.id} tried {task.verb}.")
    elif change.id == "soft_gloves":
        world.say(f"The gloves made the rough bits feel gentle, so the task no longer seemed scary.")
    elif change.id == "ear_warmers":
        world.say(f"The ear warmers softened the windy sound, and the hill felt less stern.")
    else:
        world.say(f"The new change helped in exactly the right way, and {hero.id} could try again.")

    hero.meters["courage"] = hero.meters.get("courage", 0.0) + 1.0
    hero.memes["aversion"] = max(0.0, hero.memes.get("aversion", 1.0) - 1.0)
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1.0
    world.say(f"{hero.id} looked again, understood the mistake, and gave {friend.id} a small grateful nod.")
    world.say(f"In the end, {hero.id} did not stay resigned to fear; {hero.id} changed, tried the task, and felt proud.")
    world.say(f"The little animal story ended with {hero.id} and {friend.id} together in {world.place.name}, calmer than before.")


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=random.choice(ANIMAL_TYPES)))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=random.choice([t for t in ANIMAL_TYPES if t != hero.type])))
    task = _safe_lookup(TASKS, params.task)
    change = _safe_lookup(CHANGES, params.change)

    hero.memes["aversion"] = 1.0
    hero.memes["understanding"] = 0.0
    friend.memes["kindness"] = 1.0

    narrate(world, hero, friend, task, change)

    world.facts.update(hero=hero, friend=friend, task=task, change=change, place=world.place)

    prompts = [
        f"Write a short animal story about {params.name}, {params.friend_name}, and a misunderstanding at {world.place.name}.",
        f"Tell a gentle story where a small {hero.type} feels aversion to {task.verb} but learns to change.",
        f"Write an animal story with a resigning moment, a kind explanation, and a transformation.",
    ]

    story_qa = [
        QAItem(
            question=f"Why did {params.name} resign from the task at first?",
            answer=f"{params.name} resigned at first because {params.name} had an aversion to {task.gerund} and misunderstood {params.friend_name}'s offer.",
        ),
        QAItem(
            question=f"What mistake did {params.name} make about {params.friend_name}?",
            answer=f"{params.name} misunderstood {params.friend_name} and thought the kind help would cause more {task.avoid}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{params.name} changed from fear to understanding, and the aversion faded after the helpful {change.label}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks something means one thing, but it actually means something else.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form, feeling, or state into another.",
        ),
        QAItem(
            question="What does aversion mean?",
            answer="Aversion means a strong dislike or a feeling of wanting to stay away from something.",
        ),
        QAItem(
            question="What does resign mean?",
            answer="To resign means to give up a role or stop trying to do something, often because it feels too hard or unwanted.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
place(barn;river;garden;hill).
task(stack_hay;wash_paws;pick_carrots;guard_lambs).
change(rain_boots;soft_gloves;ear_warmers;river_cloak).

affords(barn,stack_hay). affords(barn,carry_water).
affords(river,wash_paws). affords(river,cross_stones).
affords(garden,pick_carrots). affords(garden,dig_soft_soil).
affords(hill,guard_lambs). affords(hill,watch_clouds).

helps(rain_boots,water). helps(river_cloak,water).
helps(soft_gloves,dust). helps(soft_gloves,thorn).
helps(ear_warmers,wind). helps(ear_warmers,call).

valid(P,T,C) :- affords(P,T), task(T), change(C), helps(C,_), reason(T,C).
reason(stack_hay,soft_gloves).
reason(wash_paws,rain_boots).
reason(wash_paws,river_cloak).
reason(pick_carrots,soft_gloves).
reason(guard_lambs,ear_warmers).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for c in CHANGES:
        lines.append(asp.fact("change", c))
    for p, place in PLACES.items():
        for t in place.affords:
            lines.append(asp.fact("affords", p, t))
    for c, change in CHANGES.items():
        for h in change.helps:
            lines.append(asp.fact("helps", c, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((p, t, c) for p in PLACES for t in TASKS for c in CHANGES if reasonableness_gate(_safe_lookup(PLACES, p), _safe_lookup(TASKS, t), _safe_lookup(CHANGES, c)))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches reasonableness gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="barn", task="stack_hay", change="soft_gloves", name="Pip", friend_name="Milo"),
    StoryParams(place="river", task="wash_paws", change="rain_boots", name="Tia", friend_name="Luna"),
    StoryParams(place="garden", task="pick_carrots", change="soft_gloves", name="Kiki", friend_name="Bram"),
    StoryParams(place="hill", task="guard_lambs", change="ear_warmers", name="Nori", friend_name="Rolo"),
]


def generate_world_knowledge() -> list[QAItem]:
    return [
        QAItem(question="What does a fox often do?", answer="A fox is a small animal that can run quickly and explore curious places."),
        QAItem(question="Why do animals need help sometimes?", answer="Animals need help when a job is hard, scary, or confusing."),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
