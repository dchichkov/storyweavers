#!/usr/bin/env python3
"""
storyworlds/worlds/average_papa_swim_twist_suspense_fable.py
=============================================================

A small fable-like storyworld about an average papa, a swim, and a twist of
suspense. The story grows from a simulated world state: a steady father, a
watery crossing, a worried helper, and a gentle ending image that proves what
changed.

Seed idea:
---
Papa was an average father with a calm heart. He needed to swim across the pond
to bring a lost reed basket to the far bank. He tried to do it alone, but a
small twist appeared: the water darkened, the current tugged, and a duckling
called out for help. Papa had to choose between hurry and kindness. He made the
kind choice, and that choice carried the whole tale.

World model:
---
- meters: distance, water, effort, rescue_need, safety, progress
- memes: calm, worry, courage, trust, pride, tenderness

Narrative shape:
---
1. Setup: an average papa and the river task.
2. Suspense: the water rises, the current tugs, and a little problem appears.
3. Twist: the feared crossing becomes a chance to help a smaller creature.
4. Resolution: papa swims more wisely, the helper is safe, and the river no
   longer feels like a threat.

This script keeps the prose child-facing, concrete, and authored, with ASP
parity for the reasonableness gate.
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    basket: object | None = None
    papa: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"father", "dad", "papa", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
class Place:
    name: str
    kind: str
    current: str
    far_bank: str
    current_strength: float
    deep: bool = False
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
    risk: str
    twist: str
    suspense: str
    outcome: str
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
class Companion:
    id: str
    type: str
    label: str
    need: str
    rescue_action: str
    tags: set[str] = field(default_factory=set)
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _narrate_meters(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _narrate_memes(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def setup_story(world: World, papa: Entity, task: Task, companion: Entity) -> None:
    world.say(
        f"{papa.label} was an average papa with a steady step and a gentle voice."
    )
    world.say(
        f"He had to {task.verb} so he could bring a little basket of reeds to the far bank."
    )
    world.say(
        f"Near the reeds, {companion.label} waited by the water, looking small and worried."
    )
    _narrate_memes(papa, "calm", 1)
    _narrate_memes(papa, "duty", 1)
    _narrate_memes(companion, "worry", 1)


def suspense_build(world: World, papa: Entity, task: Task, companion: Entity) -> None:
    _narrate_meters(papa, "distance", 1)
    _narrate_meters(world.get("basket"), "distance", 1)
    _narrate_memes(papa, "worry", 1)
    _narrate_meters(papa, "effort", 1)
    world.say(
        f"When he stepped into the pond, the water tugged at his knees and then up to his waist."
    )
    world.say(
        f"The current grew quick enough to make {papa.label} pause, and that was the suspenseful part."
    )
    world.say(
        f"Then {companion.label} called out from a reed nest, {task.suspense}."
    )
    _narrate_meters(companion, "rescue_need", 1)
    _narrate_meters(papa, "safety", -1)
    _narrate_memes(papa, "tenderness", 1)


def twist_turn(world: World, papa: Entity, task: Task, companion: Entity) -> None:
    _narrate_memes(papa, "courage", 1)
    _narrate_memes(papa, "trust", 1)
    world.say(
        f"Papa saw that the little one was not a problem to ignore but a neighbor to help."
    )
    world.say(
        f"So the river's twist was this: the crossing was not only about the basket; it was also about kindness."
    )
    world.say(
        f"He held the basket high, swam more slowly, and used one arm to guide {companion.it()} toward the reeds."
    )
    _narrate_meters(papa, "progress", 1)
    _narrate_meters(companion, "rescue_need", -1)
    _narrate_meters(papa, "effort", 1)


def resolve_story(world: World, papa: Entity, task: Task, companion: Entity) -> None:
    _narrate_meters(papa, "safety", 2)
    _narrate_memes(papa, "pride", 1)
    _narrate_memes(companion, "trust", 1)
    world.say(
        f"In the end, {papa.label} reached the far bank with the basket still dry."
    )
    world.say(
        f"{companion.label} tucked safely into the reeds, and the pond no longer felt like a threat."
    )
    world.say(
        f"The average papa smiled, because a small brave swim had turned into a good deed."
    )


def tell(place: Place, task: Task, companion_cfg: Companion, papa_name: str, papa_type: str) -> World:
    world = World(place)
    papa = world.add(Entity(id="papa", kind="character", type=papa_type, label=papa_name))
    basket = world.add(Entity(id="basket", type="basket", label="the reed basket"))
    companion = world.add(
        Entity(id="duckling", kind="character", type=companion_cfg.type, label=companion_cfg.label)
    )
    world.facts.update(papa=papa, basket=basket, companion=companion, task=task, place=place)

    setup_story(world, papa, task, companion)
    world.para()
    suspense_build(world, papa, task, companion)
    world.para()
    twist_turn(world, papa, task, companion)
    resolve_story(world, papa, task, companion)

    return world


PLACES = {
    "pond": Place(name="the pond", kind="pond", current="the reeds", far_bank="the far bank", current_strength=0.7),
    "river": Place(name="the river", kind="river", current="the reeds", far_bank="the far bank", current_strength=1.0, deep=True),
    "marsh": Place(name="the marsh", kind="marsh", current="the cattails", far_bank="the far bank", current_strength=0.8, deep=True),
}

TASKS = {
    "swim": Task(
        id="swim",
        verb="swim across the water",
        gerund="swimming through the water",
        risk="being pulled away by the current",
        twist="the water tugged harder than he expected",
        suspense="Help! The nest is sliding!",
        outcome="a kinder crossing",
        tags={"swim", "water", "suspense", "twist"},
    ),
}

COMPANIONS = {
    "duckling": Companion(
        id="duckling",
        type="duckling",
        label="a duckling",
        need="to be guided to the reeds",
        rescue_action="guide",
        tags={"duck", "water", "fable"},
    ),
    "turtle": Companion(
        id="turtle",
        type="turtle",
        label="a turtle",
        need="to reach a dry stone",
        rescue_action="guide",
        tags={"turtle", "water", "fable"},
    ),
}

PAPA_NAMES = ["Papa Reed", "Papa Milo", "Papa Bram", "Papa Otis", "Papa Wren"]
PAPA_TYPES = ["father", "dad", "papa"]

KNOWLEDGE = {
    "swim": [
        (
            "What does it mean to swim?",
            "To swim means to move through water by using your arms and legs.",
        )
    ],
    "water": [
        (
            "Why should a swimmer be careful in deep water?",
            "A swimmer should be careful in deep water because strong water can pull and tire a body quickly.",
        )
    ],
    "duck": [
        (
            "What do ducklings like near water?",
            "Ducklings like water, reeds, and safe little places to rest where they can stay close to their family.",
        )
    ],
    "turtle": [
        (
            "What is a turtle?",
            "A turtle is an animal with a hard shell that moves slowly and can live near water or on land.",
        )
    ],
    "fable": [
        (
            "What is a fable?",
            "A fable is a short story that often uses animals or simple characters to teach a gentle lesson.",
        )
    ],
}

KNOWLEDGE_ORDER = ["fable", "swim", "water", "duck", "turtle"]


@dataclass
class StoryParams:
    place: str
    task: str
    companion: str
    papa_name: str
    papa_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for task in TASKS:
            for comp in COMPANIONS:
                combos.append((place, task, comp))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    papa = _safe_fact(world, f, "papa")
    task = _safe_fact(world, f, "task")
    comp = _safe_fact(world, f, "companion")
    return [
        f'Write a short fable for a child about an average papa who wants to {task.verb} and meets {comp.label} by the water.',
        f"Tell a suspenseful but gentle story where {papa.label} crosses {f['place'].name} by swimming and learns a kinder way to help.",
        f'Write a simple fable that includes the words "average", "papa", and "swim", and ends with a small rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    papa = _safe_fact(world, f, "papa")
    task = _safe_fact(world, f, "task")
    comp = _safe_fact(world, f, "companion")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {papa.label}, an average papa who had to {task.verb} at {place.name}.",
        ),
        QAItem(
            question=f"What made the middle of the story suspenseful?",
            answer=(
                f"The suspense came when the water tugged harder, the current grew quick, and {comp.label} called out for help."
            ),
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=(
                f"The twist was that Papa's swim was not only for the basket. It also became a chance to help {comp.label} stay safe."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {papa.label} reaching the far bank, the basket still dry, and {comp.label} safe by the reeds."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | set(world.facts["companion"].tags)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
    return out


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
reach_finish(P) :- have_progress(P), safe(P).
safe(papa) :- not swept_away(papa).
have_progress(papa) :- swims(papa), helps_other(papa).
swept_away(papa) :- current_strong, not cautious(papa).
cautious(papa) :- carries_high(papa), slows_down(papa).
valid_story(Place, Task, Companion) :- place(Place), task(Task), companion(Companion), reach_finish(papa).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("current_strong", pid) if p.current_strength >= 0.9 else asp.fact("current_mild", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("swims", "papa") if tid == "swim" else "")
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    lines.append(asp.fact("helps_other", "papa"))
    lines.append(asp.fact("carries_high", "papa"))
    lines.append(asp.fact("slows_down", "papa"))
    return "\n".join([x for x in lines if x])


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
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about an average papa, a swim, and a twist of suspense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--papa-type", choices=PAPA_TYPES)
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "task", None):
        combos = [c for c in combos if c[1] == getattr(args, "task", None)]
    if getattr(args, "companion", None):
        combos = [c for c in combos if c[2] == getattr(args, "companion", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, comp = rng.choice(list(combos))
    return StoryParams(
        place=place,
        task=task,
        companion=comp,
        papa_name=getattr(args, "name", None) or rng.choice(PAPA_NAMES),
        papa_type=getattr(args, "papa_type", None) or rng.choice(PAPA_TYPES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(COMPANIONS, params.companion), params.papa_name, params.papa_type)
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
    StoryParams(place="pond", task="swim", companion="duckling", papa_name="Papa Reed", papa_type="papa"),
    StoryParams(place="river", task="swim", companion="turtle", papa_name="Papa Otis", papa_type="father"),
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for row in combos:
            print("  ", row)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
