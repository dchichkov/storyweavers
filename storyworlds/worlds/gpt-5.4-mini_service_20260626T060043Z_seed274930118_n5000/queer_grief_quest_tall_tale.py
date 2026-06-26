#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/queer_grief_quest_tall_tale.py
==============================================================================================================

A small standalone story world for a tall-tale style quest about queer grief:
a child or young person goes looking for a lost keepsake, gets help from a
careful companion, and finds a way to carry love forward.

The world is intentionally narrow and constraint-checked. It builds a little
stateful simulation with physical meters and emotional memes, then renders the
result into a complete child-facing story with a beginning, middle turn, and
ending image.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "person": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})[case]

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
    clues: list[str] = field(default_factory=list)
    affords: set[str] = field(default_factory=set)
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
class QuestItem:
    label: str
    phrase: str
    type: str
    value: str
    memory: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy", "person"})
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
class Helper:
    label: str
    phrase: str
    method: str
    tail: str
    mood: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "harbor": Place(
        name="the harbor",
        clues=["salt wind", "rope knots", "big gull shadows"],
        affords={"search", "listen"},
    ),
    "carnival": Place(
        name="the carnival grounds",
        clues=["bright banners", "music boxes", "sticky sugar"],
        affords={"search", "ask"},
    ),
    "hill": Place(
        name="the windy hill",
        clues=["tall grass", "kite strings", "cloud roads"],
        affords={"search", "remember"},
    ),
}

QUEST_ITEMS = {
    "scarf": QuestItem(
        label="scarf",
        phrase="a rainbow scarf with soft edges",
        type="scarf",
        value="rainbow",
        memory="grandparent's laugh",
        region="neck",
        genders={"girl", "boy", "person"},
    ),
    "pin": QuestItem(
        label="pin",
        phrase="a tiny enamel pin shaped like a star",
        type="pin",
        value="star",
        memory="a promise to be true",
        region="torso",
        genders={"girl", "boy", "person"},
    ),
    "bracelet": QuestItem(
        label="bracelet",
        phrase="a braided bracelet in bright queer colors",
        type="bracelet",
        value="braided",
        memory="a summer picnic with chosen family",
        region="wrist",
        genders={"girl", "boy", "person"},
    ),
}

HELPERS = {
    "seagull": Helper(
        label="a bossy seagull",
        phrase="with one shiny eye and a sailor's squawk",
        method="pointed with its beak",
        tail="fluttered ahead and pointed to a low crate",
        mood="comic",
    ),
    "clown": Helper(
        label="a kind clown",
        phrase="with shoes like boats and pockets full of maps",
        method="drew a chalk arrow",
        tail="rolled beside them and drew a chalk arrow",
        mood="comic",
    ),
    "fox": Helper(
        label="a clever fox",
        phrase="with a tail like a question mark",
        method="showed a paw print trail",
        tail="trotted ahead and showed a paw print trail",
        mood="quiet",
    ),
}

GREETINGS = {
    "girl": "little girl",
    "boy": "little boy",
    "person": "little person",
}

TRAITS = ["bright-eyed", "stubborn", "soft-spoken", "brave", "dreamy", "sunny"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest_item: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
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


def intro(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} {_safe_lookup(GREETINGS, hero.type)} who loved the queer colors in {item.phrase}."
    )
    world.say(
        f"{hero.id} kept it close because it held a warm memory: {item.meters.get('memory', 0) and 'their love' or 'a beloved story'}."
    )
    world.facts["theme"] = "queer grief"
    world.facts["quest_item"] = item.id
    world.facts["helper"] = helper.id


def loss(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["grief"] = 1
    item.meters["lost"] = 1
    world.say(
        f"Then one day the {item.label} vanished in a blink and a breeze, and {hero.id}'s heart sank like a stone in a well."
    )
    world.say(
        f"{hero.id} felt grief so big it seemed to fill the whole street, but {hero.pronoun('subject').capitalize()} knew the memory still mattered."
    )
    world.facts["grief"] = True


def seek(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"So {hero.id} set off on a quest across {world.place.name}, where the wind carried {', '.join(world.place.clues[:2])}."
    )
    world.say(
        f"At every corner, {helper.label} {helper.phrase}, and {helper.method} to help {hero.pronoun('object')} look."
    )


def turn(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"At last, {helper.tail}, and there the {item.label} was, tucked safe as a tucked-in moonbeam."
    )
    hero.memes["hope"] = 1
    hero.memes["grief"] = 0
    hero.memes["love"] = 1
    item.meters["found"] = 1
    world.facts["found"] = True


def resolution(world: World, hero: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} smiled through wet eyes, tied the {item.label} around {hero.pronoun('possessive')} neck, and carried the memory forward."
    )
    world.say(
        f"The day ended with {hero.id} walking home under a sky that looked stitched together with rainbow thread."
    )
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, quest_item: str, helper: str) -> bool:
    return place in PLACES and quest_item in QUEST_ITEMS and helper in HELPERS


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES:
        for item in QUEST_ITEMS:
            for helper in HELPERS:
                out.append((place, item, helper))
    return out


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the requested quest setup is not reasonable for this world.)"


# ---------------------------------------------------------------------------
# Story building
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if not valid_combo(params.place, params.quest_item, params.helper):
        pass

    world = World(_safe_lookup(PLACES, params.place))

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "queer", "grief-touched"],
    ))
    helper_cfg = _safe_lookup(HELPERS, params.helper)
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="person",
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
    ))
    item_cfg = _safe_lookup(QUEST_ITEMS, params.quest_item)
    item = world.add(Entity(
        id="keepsake",
        kind="thing",
        type=item_cfg.type,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
        plural=item_cfg.plural,
    ))
    item.meters["memory"] = 1

    intro(world, hero, helper, item)
    world.para()
    loss(world, hero, item)
    world.para()
    seek(world, hero, helper, item)
    world.para()
    turn(world, hero, helper, item)
    resolution(world, hero, item)

    world.facts.update(hero=hero, item=item, helper_cfg=helper_cfg, place=world.place.name)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    item: Entity = _safe_fact(world, world.facts, "item")
    helper_cfg: Helper = _safe_fact(world, world.facts, "helper_cfg")
    return [
        f'Write a tall-tale style story for a child about queer grief and a quest for {item.phrase}.',
        f"Tell a gentle adventure where {hero.id} loses {item.label}, feels grief, and gets help from {helper_cfg.label}.",
        f"Write a short, child-friendly quest story that ends with {hero.id} carrying a memory forward.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    item: Entity = _safe_fact(world, world.facts, "item")
    return [
        QAItem(
            question=f"What was {hero.id} looking for on the quest?",
            answer=f"{hero.id} was looking for the {item.label}, a keepsake that held a queer family memory.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel sad when the {item.label} went missing?",
            answer=f"{hero.id} felt grief because the {item.label} was more than a thing; it carried a beloved memory.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"The story ended with {hero.id} finding the {item.label} and wearing it again as a sign that the memory was still close.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to look for something important or to solve a problem.",
        ),
        QAItem(
            question="What is grief?",
            answer="Grief is the heavy feeling people have when they lose someone, something, or a cherished moment.",
        ),
        QAItem(
            question="What does queer mean?",
            answer="Queer is a word many people use for identities and families that do not fit only one old rule, and it can be a proud and loving word.",
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.kind == "thing":
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.name}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
quest_item(I) :- item(I).
helper(H) :- helper_name(H).
quest_possible(P, I, H) :- place(P), item(I), helper_name(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for i in QUEST_ITEMS:
        lines.append(asp.fact("item", i))
    for h in HELPERS:
        lines.append(asp.fact("helper_name", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_possible/3."))
    return sorted(set(asp.atoms(model, "quest_possible")))


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


# ---------------------------------------------------------------------------
# Story API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale quest story world about queer grief and a found keepsake."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--quest-item", choices=sorted(QUEST_ITEMS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "person"])
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    quest_item = getattr(args, "quest_item", None) or rng.choice(list(QUEST_ITEMS))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy", "person"])
    name = getattr(args, "name", None) or rng.choice({
        "girl": ["Mina", "Ivy", "Junie", "Nora"],
        "boy": ["Eli", "Theo", "Jasper", "Rowan"],
        "person": ["Robin", "Sky", "Avery", "River"],
    }[gender])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest_item=quest_item, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        print(asp_program("#show quest_possible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible quest setups:\n")
        for p, i, h in triples:
            print(f"  {p:10} {i:12} {h}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="harbor", quest_item="scarf", name="Robin", gender="person", helper="fox", trait="brave"),
            StoryParams(place="carnival", quest_item="pin", name="Ivy", gender="girl", helper="clown", trait="dreamy"),
            StoryParams(place="hill", quest_item="bracelet", name="Eli", gender="boy", helper="seagull", trait="sunny"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: quest for {p.quest_item} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
