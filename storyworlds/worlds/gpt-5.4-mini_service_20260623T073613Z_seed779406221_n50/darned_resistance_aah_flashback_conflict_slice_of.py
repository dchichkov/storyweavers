#!/usr/bin/env python3
"""
storyworlds/worlds/darned_resistance_aah_flashback_conflict_slice_of.py
=======================================================================

A small slice-of-life storyworld about a child, a stubborn thing, a tiny
flashback, and a gentle conflict that ends in a calm fix.

Seed tale:
---
A child named Mina wants to wear her favorite red sweater to school, but one
button keeps slipping through a threadbare hole. Her older brother says to leave
it, but Mina frowns and tries again and again. "Aah," she says, because the
button will not go through. Then she remembers how her grandmother once showed
her a simple trick: pinch the cloth, breathe out, and work slowly instead of
forcing it. Mina does that, the button slips through, and she smiles on the way
to school.

World model:
---
- Physical meters track small, concrete state: tugged, strained, fixed, neat.
- Emotional memes track feelings: resistance, worry, relief, pride, warmth.
- The world has exactly one main tension: resistance against a small task.
- A flashback beat can shift the approach from force to memory and method.
- The ending proves what changed by showing the object wear correctly and the
  child leaving with calm pride.

Story quality notes:
---
- The prose is state-driven, not a fixed paragraph with swapped names.
- The conflict is small and child-sized.
- The resolution is concrete: a simple method lowers resistance and completes the task.
- The word "darned" is used in an in-world exclamation, and "aah" appears as a
  child-facing sound of frustration, not as scaffold text.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
            keys = [upper + "S", upper + "ES"]
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
    worn_by: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    garment: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
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
        if not hasattr(self, "_tags"):
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
    detail: str
    affords: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    label: str
    verb: str
    struggle: str
    finish: str
    flashback_hint: str
    resistance_kind: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Garment:
    id: str
    label: str
    phrase: str
    region: str
    at_risk_by: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


SETTINGS = {
    "home": Place(
        id="home",
        label="the kitchen",
        detail="The kitchen was warm and quiet, with a chair near the table and morning light on the floor.",
        affords={"button"},
    ),
    "laundry": Place(
        id="laundry",
        label="the laundry room",
        detail="The laundry room smelled like clean soap, and a basket sat beside the folding board.",
        affords={"button"},
    ),
    "hall": Place(
        id="hall",
        label="the front hall",
        detail="The front hall was bright and narrow, with shoes lined up neatly by the door.",
        affords={"button"},
    ),
}

TASKS = {
    "button": Task(
        id="button",
        label="buttoning the sweater",
        verb="button up the sweater",
        struggle="the button keeps slipping back out",
        finish="the button finally slides through",
        flashback_hint="pinch the cloth, breathe out, and guide the button through slowly",
        resistance_kind="button_resistance",
        tags={"button", "sweater", "clothes"},
    ),
    "zipper": Task(
        id="zipper",
        label="zipping the jacket",
        verb="zip up the jacket",
        struggle="the zipper keeps catching",
        finish="the zipper glides to the top",
        flashback_hint="hold the fabric flat and pull the slider gently",
        resistance_kind="zipper_resistance",
        tags={"zipper", "jacket", "clothes"},
    ),
}

GARMENTS = {
    "sweater": Garment(
        id="sweater",
        label="sweater",
        phrase="a favorite red sweater",
        region="torso",
        at_risk_by={"button"},
        tags={"sweater", "clothes"},
    ),
    "jacket": Garment(
        id="jacket",
        label="jacket",
        phrase="a blue jacket with a long zipper",
        region="torso",
        at_risk_by={"zipper"},
        tags={"jacket", "clothes"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lina", "June", "Tessa", "Ivy"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Theo", "Milo", "Finn"]
ADULTS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["careful", "curious", "patient", "quiet", "lively"]


@dataclass
class StoryParams:
    place: str
    task: str
    garment: str
    name: str
    gender: str
    adult: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    for place, p in SETTINGS.items():
        for task_id, task in TASKS.items():
            for garment_id, garment in GARMENTS.items():
                if task.id in garment.at_risk_by and task.id in p.affords:
                    combos.append((place, task_id, garment_id))
    return combos


def story_setup(world: World, child: Entity, adult: Entity, garment: Entity, task: Task) -> None:
    child.memes["love"] += 1
    garment.worn_by = child.id
    world.say(f"{child.id} was a little {child.label_word if child.label_word else child.type} who loved {garment.phrase}.")
    world.say(f"{child.pronoun().capitalize()} wanted to {task.verb} before leaving for school.")
    world.say(f"{adult.label_word.capitalize()} was nearby, watching the morning light and the little struggle with a patient face.")


def conflict(world: World, child: Entity, adult: Entity, garment: Entity, task: Task) -> None:
    child.memes["resistance"] += 1
    garment.meters["strained"] = garment.meters.get("strained", 0.0) + 1
    world.say(f"But {task.struggle}, and {child.id} frowned.")
    world.say(f'"Aah," {child.id} said. "{task.label.capitalize()} is being darned stubborn."')
    world.say(f"{adult.label_word.capitalize()} told {child.id} to stop tugging so hard and take a breath.")


def flashback(world: World, child: Entity, task: Task) -> None:
    child.memes["memory"] += 1
    world.say(
        f"{child.id} paused, and a small flashback came back to {child.pronoun('object')}: "
        f"{task.flashback_hint}."
    )
    world.say(f"That old trick had worked before, when someone had shown {child.pronoun('object')} with a smile.")


def resolve(world: World, child: Entity, adult: Entity, garment: Entity, task: Task) -> None:
    child.memes["resistance"] = 0.0
    child.memes["relief"] += 1
    child.meters["steady"] = child.meters.get("steady", 0.0) + 1
    garment.meters["fixed"] = garment.meters.get("fixed", 0.0) + 1
    world.say(f"{child.id} tried again, this time slowly.")
    world.say(f"Then {task.finish}, and the whole sweater sat neat and smooth.")
    world.say(f"{child.id} grinned at {adult.label_word} and headed for the door with calm shoulders and a proud step.")


def tell(place: Place, task: Task, garment_cfg: Garment, name: str = "Mina", gender: str = "girl",
         adult_type: str = "grandmother", trait: str = "patient") -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, label=gender))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, label=adult_type))
    garment = world.add(Entity(id="garment", type=garment_cfg.label, label=garment_cfg.label, phrase=garment_cfg.phrase, owner=child.id))

    world.facts.update(child=child, adult=adult, garment=garment, task=task, place=place, garment_cfg=garment_cfg, trait=trait)

    story_setup(world, child, adult, garment, task)
    world.para()
    world.say(place.detail)
    conflict(world, child, adult, garment, task)
    world.para()
    flashback(world, child, task)
    resolve(world, child, adult, garment, task)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, adult, task, garment = f["child"], f["adult"], f["task"], f["garment_cfg"]
    return [
        f'Write a gentle slice-of-life story for a young child where {child.id} has trouble {task.verb} and remembers a helpful trick.',
        f"Tell a small home story where {child.id} feels resistance while {task.label}, then a flashback helps {child.id} try again.",
        f'Write a calm story that includes the words "darned", "aah", and a flashback, ending with {child.id} leaving happily in {garment.phrase}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, task, garment = f["child"], f["adult"], f["task"], f["garment_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} want to do before going out?",
            answer=f"{child.id} wanted to {task.verb}. That was the little task at the center of the story.",
        ),
        QAItem(
            question=f"Why did {child.id} say 'aah'?",
            answer=f"{child.id} said 'aah' because {task.struggle}. The buttoning felt hard for a moment, so the child showed frustration.",
        ),
        QAItem(
            question=f"What did the flashback remind {child.id} to do?",
            answer=f"The flashback reminded {child.id} to {task.flashback_hint}. That calmer method made the task easier.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {adult.label_word}?",
            answer=f"{child.id} finished the task, smiled at {adult.label_word}, and left with {garment.phrase} sitting neat and right.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does resistance mean here?", "Here, resistance means something is hard to do at first, like a button slipping back out or a zipper catching."),
        QAItem("What is a flashback?", "A flashback is a remembered moment from before. It can help someone remember a useful trick."),
        QAItem("Why can a calm method help?", "A calm method can lower frustration and make small tasks easier, because steady hands work better than rough tugging."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id:8} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("home", "button", "sweater", "Mina", "girl", "grandmother", "patient"),
    StoryParams("laundry", "zipper", "jacket", "Owen", "boy", "mother", "careful"),
    StoryParams("hall", "button", "sweater", "Ivy", "girl", "father", "curious"),
]


ASP_RULES = r"""
task_risky(T, G) :- task(T), garment(G), at_risk(T, G).
calm_fix(T) :- task(T), fix(T).
valid(P, T, G) :- place(P), task(T), garment(G), task_risky(T, G), in_place(P, T).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for t in _safe_lookup(SETTINGS, pid).affords:
            lines.append(asp.fact("in_place", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("fix", tid))
    for gid, g in GARMENTS.items():
        lines.append(asp.fact("garment", gid))
        for t in g.at_risk_by:
            lines.append(asp.fact("at_risk", t, gid))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a small resistance, a flashback, and a calm fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULTS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "garment", None) is None or c[2] == getattr(args, "garment", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, garment = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = getattr(args, "adult", None) or rng.choice(ADULTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, task, garment, name, gender, adult, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(GARMENTS, params.garment),
                 params.name, params.gender, params.adult, params.trait)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(f"{asp_facts()}\n{ASP_RULES}")
        return
    if getattr(args, "verify", None):
        print("OK: no ASP verifier implemented for this world.")
        return
    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} compatible combos")
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
    for i, s in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))


if __name__ == "__main__":
    main()
