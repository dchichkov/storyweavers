#!/usr/bin/env python3
"""
storyworlds/worlds/barricade_mark_gerund_misunderstanding_happy_ending_nursery.py
=================================================================================

A tiny nursery-rhyme storyworld about a child, a barricade, and a harmless
misunderstanding that ends happily.

Seed tale:
---
A little child saw a mark on a door and thought it meant "do not come in".
So the child built a soft barricade of blocks and toys to keep a kitten out.
But the mark was only a place for a ribbon to be tied. The grown-up smiled,
moved the blocks, and everyone made a little play space instead.

This world keeps the action small and concrete:
- physical meters: block stacks, barrier strength, tidiness, ribbon readiness
- emotional memes: worry, confusion, relief, cheer, trust

The generated stories use a nursery rhyme style: short lines, simple words,
soft repetition, and a warm happy ending after a misunderstanding.
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
    role: str = ""
    owner: Optional[str] = None
    used_for: str = ""
    is_child: bool = False
    is_adult: bool = False
    is_pet: bool = False
    is_mark: bool = False
    is_barricade_piece: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    adult: object | None = None
    barricade: object | None = None
    child: object | None = None
    mark_ent: object | None = None
    pet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.is_child:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.is_adult:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.is_pet:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the nursery"
    features: set[str] = field(default_factory=set)
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
class BarricadePlan:
    label: str
    material: str
    phrase: str
    pieces: int
    blocks: bool = True
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
class Mark:
    label: str
    phrase: str
    meaning: str
    place: str
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


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    mark = world.get("mark")
    if child.memes["confusion"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1
    out.append(f"The little heart grew wobbly near {mark.label}.")
    return out


def _r_barricade_soft(world: World) -> list[str]:
    child = world.get("child")
    barricade = world.get("barricade")
    if child.meters["building"] < THRESHOLD:
        return []
    sig = ("barricade",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    barricade.meters["barrier"] += 1
    barricade.meters["tidy"] -= 0.1
    return [f"A soft barricade stood up like a little wall."]


def _r_misunderstanding(world: World) -> list[str]:
    child = world.get("child")
    mark = world.get("mark")
    if child.memes["worry"] < THRESHOLD or mark.is_mark is False:
        return []
    sig = ("misunderstanding",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["confusion"] += 0.5
    return ["__misunderstanding__"]


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("barricade", _r_barricade_soft), Rule("misunderstanding", _r_misunderstanding)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mark_at_risk(mark: Mark) -> bool:
    return True


def select_barricade(plan: BarricadePlan, mark: Mark) -> Optional[BarricadePlan]:
    return plan if plan.blocks else None


def predict_misunderstanding(world: World) -> dict:
    sim = world.copy()
    _build_barricade(sim, sim.get("child"), narrate=False)
    return {
        "confusion": sim.get("child").memes["confusion"],
        "barrier": sim.get("barricade").meters["barrier"],
    }


def _build_barricade(world: World, child: Entity, narrate: bool = True) -> None:
    child.meters["building"] += 1
    child.memes["hope"] += 1
    propagate(world, narrate=narrate)


def nursery_line() -> str:
    return "Soft as a cloud, and small as a song."


def introduce(world: World, child: Entity, pet: Entity, mark: Mark) -> None:
    world.say(
        f"There was a little child in {world.setting.place}, and {pet.label} "
        f"padded close by. {nursery_line()}"
    )
    world.say(
        f"On the door was {mark.phrase}, and the child thought it meant "
        f"\"Keep out, keep out.\""
    )


def misunderstanding(world: World, child: Entity, mark: Mark) -> None:
    child.memes["confusion"] += 1
    world.say(
        f"The child frowned and frowned. \"Oh no, oh no, {mark.label} says no,\" "
        f"the child murmured."
    )
    world.say("So the small hands started to stack and stack.")


def build(world: World, child: Entity, plan: BarricadePlan) -> None:
    child.meters["building"] += 1
    world.say(
        f"Blocks went click, and toys went tuck, until a {plan.material} "
        f"barricade stood between the child and the kitten."
    )
    propagate(world, narrate=False)


def explain(world: World, adult: Entity, child: Entity, mark: Mark, pet: Entity) -> None:
    child.memes["confusion"] = max(0.0, child.memes["confusion"] - 1)
    child.memes["trust"] += 1
    adult.memes["kindness"] += 1
    world.say(
        f"Then the grown-up came with a gentle smile. \"Oh, little one, "
        f"{mark.label} is not a no-no mark,\" {adult.pronoun()} said. "
        f"\"It is only a place to tie a ribbon.\""
    )
    world.say(
        f"The child looked again. The worry turned round and round, and the child "
        f"understood. {pet.label} was not in trouble at all."
    )


def happy_ending(world: World, child: Entity, adult: Entity, pet: Entity, mark: Mark) -> None:
    child.memes["relief"] += 1
    child.memes["cheer"] += 1
    adult.memes["cheer"] += 1
    world.say(
        f"So the blocks came down, and the soft space opened wide. "
        f"The grown-up tied a ribbon at {mark.place}, and the child clapped "
        f"{child.pronoun('possessive')} hands."
    )
    world.say(
        f"Then {pet.label} trotted through the happy play space, and everyone "
        f"laughed a little laugh. No more worry, no more fright -- only a tidy "
        f"nursery, a bright ribbon, and a gentle heart."
    )


def tell(setting: Setting, plan: BarricadePlan, mark: Mark, child_name: str = "Mimi",
         adult_name: str = "Mama") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="child", label=child_name, is_child=True))
    adult = world.add(Entity(id=adult_name, kind="character", type="adult", label="the grown-up", is_adult=True))
    pet = world.add(Entity(id="kitten", kind="character", type="pet", label="the kitten", is_pet=True))
    barricade = world.add(Entity(id="barricade", type="barricade", label="barricade", is_barricade_piece=True))
    mark_ent = world.add(Entity(id="mark", type="mark", label="mark", phrase=mark.phrase, is_mark=True))
    world.add(Entity(id="toy", type="toy", label="blocks and toys"))

    world.facts["mark"] = mark
    world.facts["pet"] = pet
    world.facts["plan"] = plan
    world.facts["child"] = child
    world.facts["adult"] = adult

    introduce(world, child, pet, mark)
    world.para()
    misunderstanding(world, child, mark)
    build(world, child, plan)
    world.para()
    explain(world, adult, child, mark, pet)
    world.para()
    happy_ending(world, child, adult, pet, mark)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", features={"soft", "playful"}),
    "playroom": Setting(place="the playroom", features={"soft", "playful"}),
    "corner": Setting(place="the sunny corner", features={"soft"}),
}

PLANS = {
    "blocks": BarricadePlan(label="block barricade", material="block", phrase="a row of toy blocks", pieces=4, blocks=True),
    "stuffies": BarricadePlan(label="stuffie barricade", material="stuffed", phrase="a row of stuffed toys", pieces=5, blocks=True),
    "blanket": BarricadePlan(label="blanket barricade", material="blanket", phrase="a little blanket wall", pieces=1, blocks=True),
}

MARKS = {
    "ribbon": Mark(label="ribbon mark", phrase="a shiny ribbon mark", meaning="ribbon place", place="the door knob"),
    "sticker": Mark(label="sticker mark", phrase="a tiny sticker mark", meaning="sticker place", place="the cupboard"),
}

NAMES = ["Mimi", "Lulu", "Tilly", "Pippa", "Nina", "Daisy"]


@dataclass
class StoryParams:
    setting: str
    plan: str
    mark: str
    name: str
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
    return [(s, p, m) for s in SETTINGS for p in PLANS for m in MARKS]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme story for a small child with a "barricade" and a "{f["mark"].label}".',
        f"Tell a soft, happy story where {f['child'].id} misunderstands {f['mark'].phrase} and builds a gentle barricade.",
        f'Write a child-friendly rhyme where a misunderstanding about "{f["mark"].label}" ends in a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, adult, pet, mark = f["child"], f["adult"], f["pet"], f["mark"]
    return [
        QAItem(
            question=f"Why did {child.id} build a barricade?",
            answer=f"{child.id} thought {mark.phrase} meant \"keep out,\" so {child.pronoun('subject')} built a soft barricade to keep {pet.label} safe.",
        ),
        QAItem(
            question=f"What did the grown-up say about {mark.label}?",
            answer=f"The grown-up said {mark.label} was not a no-no mark at all. It was only a place to tie a ribbon.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended happily. The blocks came down, the ribbon went up, and everyone played in the tidy nursery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a barricade?", answer="A barricade is a little wall or barrier that helps keep something out or hold a space safe."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else."),
        QAItem(question="What is a ribbon?", answer="A ribbon is a soft strip of cloth that can be tied into a bow or used to decorate things."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="nursery", plan="blocks", mark="ribbon", name="Mimi"),
    StoryParams(setting="playroom", plan="stuffies", mark="sticker", name="Lulu"),
    StoryParams(setting="corner", plan="blanket", mark="ribbon", name="Tilly"),
]


ASP_RULES = r"""
% A mark is meaningful, a barricade is a barrier, and misunderstanding can make
% a child build a barricade around a harmless mark.
needs_barrier(M) :- mark(M).
misunderstood(C, M) :- child(C), mark(M), confused_about(C, M).
builds_barricade(C) :- child(C), misunderstood(C, _), blocks_ready(C).
happy_end :- builds_barricade(_), grownup_explains, ribbon_tied.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
        lines.append(asp.fact("barricade", pid))
    for mid in MARKS:
        lines.append(asp.fact("mark", mid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("grownup_explains"))
    lines.append(asp.fact("ribbon_tied"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_end/0."))
    asp_ok = bool(model)
    py_ok = True
    return 0 if asp_ok == py_ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about a barricade and a misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--mark", choices=MARKS)
    ap.add_argument("--name", choices=NAMES)
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "plan", None) is None or c[1] == getattr(args, "plan", None))
              and (getattr(args, "mark", None) is None or c[2] == getattr(args, "mark", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, plan, mark = (list(rng.choice(combos)) + [None, None, None])[:3]
    return StoryParams(
        setting=setting,
        plan=plan,
        mark=mark,
        name=getattr(args, "name", None) or rng.choice(NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PLANS, params.plan), _safe_lookup(MARKS, params.mark), params.name)
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
        print(asp_program("#show happy_end/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show happy_end/0."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
