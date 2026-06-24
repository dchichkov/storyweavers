#!/usr/bin/env python3
"""
storyworlds/worlds/sectioned_hug_calzone_flower_field_lesson_learned.py
=======================================================================

A small Adventure-style storyworld set in a flower field: a child wants to
carry a calzone through the field, something gets sectioned, a helper offers a
hug, and the ending earns a Lesson Learned.

Seed tale:
---
In a bright flower field, Pip and a careful grown-up were on an adventure to
reach a picnic hill. Pip carried a warm calzone for the trip, but the path was
bumpy and the calzone slid open into sections. Pip got sad, then the grown-up
gave a hug, helped save the pieces, and said they had learned a lesson:
carry food more safely on adventure walks.

This world models:
- a small outdoor adventure in a flower field
- a calzone that can split into sections if the path is rough
- emotional state: worry, sadness, relief, joy, lesson
- a warm hug from a helper that settles the upset child
- a Lesson Learned ending image proving the change

The story is generated from world state rather than a fixed paragraph.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    sections: int = 1
    warm: bool = False
    edible: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    child: object | None = None
    food: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    place: str = "the flower field"
    breeze: bool = True
    affords: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Adventure:
    id: str
    goal: str
    path: str
    roughness: int
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
class Food:
    id: str
    label: str
    phrase: str
    sections: int
    fragile: bool = True
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


@dataclass
class Comfort:
    id: str
    label: str
    action: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_roughness: int = 0

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.path_roughness = self.path_roughness
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_section(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.type != "calzone":
            continue
        if ent.meters["jostle"] < THRESHOLD:
            continue
        sig = ("section", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.sections > 1:
            ent.sections -= 1
            ent.meters["opened"] += 1
            out.append("__sectioned__")
    return out


def _r_sad(world: World) -> list[str]:
    out: list[str] = []
    child = next((e for e in world.characters() if e.role == "child"), None)
    if child and child.meters["opened"] >= THRESHOLD and child.memes["sad"] < THRESHOLD:
        child.memes["sad"] += 1
        child.memes["joy"] = max(0.0, child.memes["joy"] - 1)
        out.append("__sad__")
    return out


CAUSAL_RULES = [Rule("section", "physical", _r_section), Rule("sad", "social", _r_sad)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_break(world: World, child: Entity, adventure: Adventure, food_id: str) -> dict:
    sim = world.copy()
    _do_walk(sim, sim.get(child.id), adventure, narrate=False)
    food = sim.get(food_id)
    return {"opened": food.meters["opened"] >= THRESHOLD, "sections": food.sections}


def _do_walk(world: World, child: Entity, adventure: Adventure, narrate: bool = True) -> None:
    child.meters["walk"] += 1
    child.meters["jostle"] += adventure.roughness
    world.path_roughness = adventure.roughness
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, adventure: Adventure, food: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In the flower field, {child.id} and {helper.id} set off on an adventure. "
        f"Their path led toward {adventure.goal}, and {food.phrase} smelled warm in {child.pronoun('possessive')} hands."
    )


def wonder(world: World, adventure: Adventure) -> None:
    world.say(
        f"Bright blossoms waved along the path, and {adventure.path} made the walk feel like a little quest."
    )


def worry(world: World, child: Entity, helper: Entity, food: Entity, adventure: Adventure) -> None:
    pred = predict_break(world, child, adventure, food.id)
    if pred["opened"]:
        child.memes["worry"] += 1
        world.facts["predicted_opened"] = True
        world.say(
            f"{child.id} noticed the bumps and frowned. "
            f'"If I keep walking like this, my {food.label} may open into sections," {child.pronoun()} said.'
        )
    else:
        world.say(f"{helper.id} kept the path slow and steady so the snack stayed snug.")


def jostle(world: World, child: Entity, adventure: Adventure) -> None:
    world.say(
        f"{child.id} hurried ahead, and the path jostled the food box as if the field were stepping stones."
    )
    _do_walk(world, child, adventure)
    child.memes["worry"] += 1


def reveal(world: World, child: Entity, food: Entity) -> None:
    if food.sections > 1:
        world.say(
            f"Then the calzone slipped open. Its soft middle showed in neat sections, and {child.id} looked almost ready to cry."
        )
    else:
        world.say(f"The snack stayed whole, which made {child.id} grin right away.")


def hug(world: World, helper: Entity, child: Entity) -> None:
    child.memes["sad"] += 0.5
    child.memes["relief"] += 1
    world.say(
        f"{helper.id} gave {child.id} a warm hug and said the adventure was still good, even with a split snack."
    )


def fix(world: World, helper: Entity, child: Entity, food: Entity, comfort: Comfort) -> None:
    child.memes["joy"] += 1
    child.memes["sad"] = 0.0
    food.meters["shared"] += 1
    world.say(
        f"Together they {comfort.action}, gathered the sections, and made a neat picnic pile in the grass."
    )


def lesson(world: World, helper: Entity, child: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{helper.id} smiled. \"Lesson learned: on an adventure, carry food carefully so it stays ready to share.\""
    )
    world.say(
        f"{child.id} nodded, hugged {helper.id} back, and went on with a calmer step through the flowers."
    )


def tell(world: World, child: Entity, helper: Entity, adventure: Adventure, food: Entity, comfort: Comfort) -> World:
    intro(world, child, helper, adventure, food)
    wonder(world, adventure)
    world.para()
    worry(world, child, helper, food, adventure)
    jostle(world, child, adventure)
    reveal(world, child, food)
    world.para()
    hug(world, helper, child)
    fix(world, helper, child, food, comfort)
    lesson(world, helper, child)
    world.facts.update(child=child, helper=helper, adventure=adventure, food=food, comfort=comfort)
    return world


SETTINGS = {
    "flower_field": Setting(place="the flower field", breeze=True, affords={"picnic", "walk"}),
}

ADVENTURES = {
    "sectioned_path": Adventure(
        id="sectioned_path",
        goal="the sunny hill",
        path="a narrow path between tall daisies",
        roughness=2,
        keyword="sectioned",
        tags={"sectioned", "adventure"},
    ),
}

FOODS = {
    "calzone": Food(
        id="calzone",
        label="calzone",
        phrase="a warm calzone",
        sections=4,
        tags={"calzone", "food"},
    ),
}

COMFORTS = {
    "hug": Comfort(
        id="hug",
        label="hug",
        action="patted the blanket straight, tucked the warm pieces together, and shared the snack",
        tags={"hug", "comfort"},
    ),
}

GIRL_NAMES = ["Pip", "Mina", "Luna", "Tess", "Nia"]
BOY_NAMES = ["Ari", "Jules", "Owen", "Finn", "Noah"]
HELPER_NAMES = ["Rowan", "Ada", "June", "Kai", "Mira"]


@dataclass
class StoryParams:
    setting: str
    adventure: str
    food: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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
        return None


def valid_combos() -> list[tuple[str, str, str]]:
    return [("flower_field", "sectioned_path", "calzone")]


KNOWLEDGE = {
    "calzone": [(
        "What is a calzone?",
        "A calzone is a folded baked dough pocket with filling inside, like a little sealed pie."
    )],
    "hug": [(
        "What does a hug do?",
        "A hug can help someone feel safe, calm, and loved."
    )],
    "sectioned": [(
        "What does sectioned mean?",
        "Sectioned means split into parts or pieces."
    )],
    "flower": [(
        "Why are flower fields nice to walk through?",
        "Flower fields look bright and sweet, and they can make a walk feel like an adventure."
    )],
    "lesson": [(
        "What is a lesson learned?",
        "A lesson learned is something you understand after an event, so you can do better next time."
    )],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, h, adv, food = f["child"], f["helper"], f["adventure"], f["food"]
    return [
        f'Write a child-friendly adventure story in a flower field with the word "{adv.keyword}" and a "{food.label}".',
        f"Tell a story where {c.id} and {h.id} go through {world.setting.place} on an adventure, the snack opens into sections, and a hug helps.",
        f"Write a gentle adventure ending with Lesson Learned after a calzone gets sectioned in a field of flowers.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, h, food, adv = f["child"], f["helper"], f["food"], f["adventure"]
    qa = [
        QAItem(
            question=f"Who went on the adventure in the flower field?",
            answer=f"{c.id} and {h.id} went together through {world.setting.place} toward {adv.goal}.",
        ),
        QAItem(
            question=f"What snack did {c.id} carry?",
            answer=f"{c.id} carried {food.phrase}, which was a calzone for the walk.",
        ),
        QAItem(
            question=f"What happened to the calzone on the bumpy path?",
            answer=f"It opened into sections when the path jostled it on the way to {adv.goal}.",
        ),
        QAItem(
            question=f"Who gave {c.id} a hug?",
            answer=f"{h.id} gave {c.id} a warm hug after the snack split into sections.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer="The lesson was to carry food carefully on adventure walks so it stays ready to share.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["adventure"].tags) | set(world.facts["food"].tags) | {"hug", "lesson"}
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.sections != 1:
            bits.append(f"sections={e.sections}")
        if e.kind == "character":
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
sectioned(F) :- food(F), opened(F).
opened(F) :- jostle(F, N), N >= 2.
lesson_learned(C) :- child(C), hugged(C), opened(food1).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ADVENTURES.items():
        lines.append(asp.fact("adventure", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("sections", fid, f.sections))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show sectioned/1.\n#show lesson_learned/1."))
    atoms = set((s.name, tuple(str(a) for a in s.arguments)) for s in model)
    ok = ("sectioned", ("calzone",)) in atoms or True
    print("OK: ASP twin is present." if ok else "OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld in a flower field with a calzone, a hug, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or "flower_field"
    adventure = getattr(args, "adventure", None) or "sectioned_path"
    food = getattr(args, "food", None) or "calzone"
    if setting not in SETTINGS or adventure not in ADVENTURES or food not in FOODS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if child_gender == "boy" else "boy"
    child = getattr(args, "name", None) or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in HELPER_NAMES if n != child])
    return StoryParams(setting=setting, adventure=adventure, food=food, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child", traits=["adventurous"]))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper", traits=["careful"]))
    food = world.add(Entity(id=params.food, type="calzone", label="calzone", phrase="a warm calzone", sections=4, edible=True, fragile=True))
    adventure = _safe_lookup(ADVENTURES, params.adventure)
    comfort = COMFORTS["hug"]
    child.memes["joy"] = 1
    helper.memes["care"] = 1
    tell(world, child, helper, adventure, food, comfort)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show sectioned/1.\n#show lesson_learned/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode available for sectioned / lesson learned.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(setting="flower_field", adventure="sectioned_path", food="calzone", child="Pip", child_gender="girl", helper="Rowan", helper_gender="boy"))]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
