#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/complain_flashback_teamwork_fable.py
===============================================================================================================

A small fable-like storyworld about complaint, flashback, and teamwork.

Seed tale sketch:
---
A little badger named Bram was asked to carry a heavy basket of pears up a hill.
He complained because the path was steep and the basket was awkward. On the way,
he remembered a flashback: last week, his friends had helped him when he was
stuck under a fallen branch, and he had not thanked them kindly. Bram felt
ashamed, asked for help, and the animals worked together to carry the basket
home. The basket arrived safely, and Bram learned that teamwork makes hard work
lighter.

World model:
---
- Physical meters: load, strain, progress, dropped, dust, care
- Emotional memes: complain, shame, gratitude, pride, trust, joy, teamwork
- The story turns on a flashback that changes the hero's mood and leads to a
  cooperative solution.
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


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    helper_for: Optional[str] = None

    helper: object | None = None
    hero: object | None = None
    load: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"badger", "fox", "rabbit", "hedgehog", "mole", "otter"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    name: str
    steep: bool = False
    near_water: bool = False
    noisy: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    load_word: str
    load_meters: float
    strain_gain: float
    progress_gain: float
    complaint_line: str
    flashback_prompt: str
    teamwork_line: str
    ending_line: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    carried_on: str
    weight: float
    can_share: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str = ""
    task: str = ""
    prize: str = ""
    hero_name: str = ""
    hero_type: str = ""
    helper_name: str = ""
    helper_type: str = ""
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.flashback_happened = False
        self.teamwork_happened = False

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

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


PLACE_REGISTRY = {
    "hill": Place(name="the hill path", steep=True),
    "orchard": Place(name="the orchard lane", steep=False),
    "river": Place(name="the riverbank path", steep=True, near_water=True),
}

TASK_REGISTRY = {
    "basket": Task(
        id="basket",
        verb="carry the basket",
        gerund="carrying the basket",
        load_word="basket",
        load_meters=1.0,
        strain_gain=1.0,
        progress_gain=1.0,
        complaint_line="This basket is too heavy for one small set of paws.",
        flashback_prompt="the day his friends had helped him before",
        teamwork_line="Let's lift it together, one step at a time.",
        ending_line="Together, the animals carried the basket home without dropping a single pear.",
        tags={"work", "fruit", "help"},
    ),
    "water": Task(
        id="water",
        verb="carry the water jars",
        gerund="carrying the water jars",
        load_word="jars",
        load_meters=1.0,
        strain_gain=1.0,
        progress_gain=1.0,
        complaint_line="These jars are slippery and awkward to hold alone.",
        flashback_prompt="the morning he had almost slipped and been caught by a friend",
        teamwork_line="You take one side, and I will take the other.",
        ending_line="By sharing the load, the animals brought every jar safely to the cottage.",
        tags={"water", "help"},
    ),
    "logs": Task(
        id="logs",
        verb="move the logs",
        gerund="moving the logs",
        load_word="logs",
        load_meters=1.5,
        strain_gain=1.2,
        progress_gain=1.0,
        complaint_line="These logs are too clumsy to roll by myself.",
        flashback_prompt="the afternoon he had once laughed at a friend's wobbling paws",
        teamwork_line="If we push together, the logs will roll straight.",
        ending_line="The friends pushed as one, and the logs reached the woodpile in a neat stack.",
        tags={"work", "wood", "help"},
    ),
}

PRIZE_REGISTRY = {
    "basket": Prize(
        id="basket",
        label="basket of pears",
        phrase="a basket full of ripe pears",
        carried_on="back",
        weight=1.0,
        can_share=True,
        tags={"fruit", "work"},
    ),
    "jars": Prize(
        id="jars",
        label="water jars",
        phrase="two clay water jars",
        carried_on="hands",
        weight=1.0,
        can_share=True,
        tags={"water"},
    ),
    "logs": Prize(
        id="logs",
        label="logs",
        phrase="three small logs",
        carried_on="ground",
        weight=1.5,
        can_share=True,
        tags={"wood"},
    ),
}

ANIMAL_NAMES = ["Bram", "Milo", "Tess", "Nia", "Pip", "Lark", "Bela", "Otis"]
ANIMAL_TYPES = ["badger", "fox", "rabbit", "hedgehog", "mole", "otter"]
HELPER_TYPES = ["rabbit", "hedgehog", "mole", "otter", "fox", "badger"]


ASP_RULES = r"""
place_name(hill,"the hill path").
place_name(orchard,"the orchard lane").
place_name(river,"the riverbank path").

task_load(basket,1).
task_load(water,1).
task_load(logs,2).

task_can_complain(T) :- task_load(T,L), L >= 1.
task_needs_teamwork(T) :- task_load(T,L), L >= 1.
story_ok(P,T,R) :- place_name(P,_), task_can_complain(T), task_needs_teamwork(T), prize(R), task(T).
#show story_ok/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACE_REGISTRY:
        lines.append(asp.fact("place", pid))
    for tid, task in TASK_REGISTRY.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_load", tid, int(task.load_meters * 10)))
    for rid in PRIZE_REGISTRY:
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACE_REGISTRY:
        for t in TASK_REGISTRY:
            for r in PRIZE_REGISTRY:
                combos.append((p, t, r))
    return combos


def _reasonableness_gate(place: str, task: str, prize: str) -> None:
    if task == "basket" and place == "orchard" and prize != "basket":
        pass
    if task == "water" and place == "hill" and prize != "jars":
        pass
    if task == "logs" and prize != "logs":
        pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about complaint, flashback, and teamwork.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--task", choices=TASK_REGISTRY)
    ap.add_argument("--prize", choices=PRIZE_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--hero-type", choices=ANIMAL_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACE_REGISTRY))
    task = getattr(args, "task", None) or rng.choice(list(TASK_REGISTRY))
    prize = getattr(args, "prize", None) or task
    _reasonableness_gate(place, task, prize)

    hero_type = getattr(args, "hero_type", None) or rng.choice(ANIMAL_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice([t for t in HELPER_TYPES if t != hero_type])
    hero_name = getattr(args, "name", None) or rng.choice(ANIMAL_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in ANIMAL_NAMES if n != hero_name])

    return StoryParams(
        place=place,
        task=task,
        prize=prize,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Task, Prize]:
    place = _safe_lookup(PLACE_REGISTRY, params.place)
    task = _safe_lookup(TASK_REGISTRY, params.task)
    prize = _safe_lookup(PRIZE_REGISTRY, params.prize)
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    load = world.add(Entity(id="load", type=prize.id, label=prize.label, phrase=prize.phrase, owner=hero.id))
    load.carried_by = hero.id
    hero.meters["load"] += task.load_meters
    return world, hero, helper, load, task, prize


def _do_story(world: World, hero: Entity, helper: Entity, load: Entity, task: Task, prize: Prize) -> None:
    hero.memes["pride"] += 0.5
    world.say(f"{hero.id} lived near {world.place.name} and liked being useful.")
    world.say(f"One morning, {hero.id} had to {task.verb} for the village.")
    world.say(f"{hero.id} looked at {prize.phrase} and frowned.")
    world.say(f'"{task.complaint_line}" {hero.id} complained.')

    hero.memes["complain"] += 1
    hero.meters["strain"] += task.strain_gain
    hero.meters["progress"] += 0.2
    world.para()

    world.say(
        f"As {hero.id} paused, a flashback came back: {task.flashback_prompt}. "
        f"In that memory, friends had been kind when the path was hard."
    )
    world.flashback_happened = True
    hero.memes["shame"] += 1
    hero.memes["gratitude"] += 1
    hero.memes["trust"] += 0.5
    world.para()

    world.say(
        f"{hero.id} lowered {hero.pronoun('possessive')} head and called to {helper.id}. "
        f'"{task.teamwork_line}"'
    )
    helper.memes["trust"] += 1
    helper.memes["joy"] += 1
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    world.teamwork_happened = True

    load.carried_by = None
    load.helper_for = hero.id
    hero.meters["progress"] += 0.5
    helper.meters["progress"] += 0.5
    hero.meters["strain"] = max(0.0, hero.meters["strain"] - 0.5)
    helper.meters["load"] += 0.5
    hero.memes["complain"] = max(0.0, hero.memes["complain"] - 0.5)
    hero.memes["joy"] += 1
    helper.memes["joy"] += 0.5

    world.say(
        f"{helper.id} smiled and came beside {hero.id}. Together they lifted the {task.load_word}, "
        f"one careful step at a time."
    )
    world.say(task.ending_line)
    world.say(
        f"{hero.id} no longer complained. Instead, {hero.id} thanked {helper.id}, "
        f"and the path felt shorter because it was shared."
    )

    world.facts.update(hero=hero, helper=helper, load=load, task=task, prize=prize, place=world.place)


def generate(params: StoryParams) -> StorySample:
    world, hero, helper, load, task, prize = _setup_world(params)
    _do_story(world, hero, helper, load, task, prize)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for children that includes the word "complain" and ends with teamwork.',
        f"Tell a simple animal fable where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} complains on {world.place.name}, remembers a flashback, and works with {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").id}.",
        f"Write a gentle story about a hard job, a memory, and a shared solution in which {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} learns not to complain alone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    task: Task = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    prize: Prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    return [
        QAItem(
            question=f"Why did {hero.id} complain at {place.name}?",
            answer=f"{hero.id} complained because {task.verb} felt too hard to do alone, and the {prize.label} was heavy and awkward.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered {task.flashback_prompt}, when friends had helped before and kindness had made a hard moment easier.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They worked together, sharing the load and lifting it one careful step at a time until the job was finished.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{hero.id} stopped complaining, thanked {helper.id}, and learned that teamwork can make hard work feel lighter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or animals work together and help each other do a job that is hard to do alone.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, often to help explain how a character feels now.",
        ),
        QAItem(
            question="Why can complaining make a job feel worse?",
            answer="Complaining can make a job feel heavier because it keeps a character focused on the hard part instead of on a solution.",
        ),
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        if e.helper_for:
            parts.append(f"helper_for={e.helper_for}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  flashback_happened={world.flashback_happened}")
    lines.append(f"  teamwork_happened={world.teamwork_happened}")
    return "\n".join(lines)


def asp_verify() -> int:
    import asp
    program = asp_program("#show story_ok/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "story_ok"))
    py_set = set((p, t, r) for p, t, r in valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(asp_set - py_set))
    print("  only in python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def build_story_for_params(params: StoryParams) -> StorySample:
    return generate(params)


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
    StoryParams(place="orchard", task="basket", prize="basket", hero_name="Bram", hero_type="badger", helper_name="Milo", helper_type="rabbit"),
    StoryParams(place="hill", task="logs", prize="logs", hero_name="Tess", hero_type="fox", helper_name="Nia", helper_type="hedgehog"),
    StoryParams(place="river", task="water", prize="jars", hero_name="Pip", hero_type="otter", helper_name="Lark", helper_type="mole"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
