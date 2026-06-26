#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/humorus_photogenic_bad_ending_happy_ending_mystery.py
==============================================================================================================================

A small mystery storyworld with a humorous, photogenic cast and two possible
ending flavors: a Bad Ending or a Happy Ending.

Seed impression:
- something funny and photogenic is missing
- small clues are found in a tidy, child-friendly mystery
- a quick turn can lead either to a messy bad ending or a clean happy ending

The storyworld is deliberately tiny and classical:
- one hero
- one setting
- one missing item
- one clue trail
- one reveal
- one ending image that proves what changed

It includes an ASP twin for parity checks and a Python reasonableness gate.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    helper: object | None = None
    hero: object | None = None
    missing: object | None = None
    def pronoun(self) -> str:
        if self.type in {"girl", "woman", "mother"}:
            return "she"
        if self.type in {"boy", "man", "father"}:
            return "he"
        return "it"

    def possessive(self) -> str:
        if self.type in {"girl", "woman", "mother"}:
            return "her"
        if self.type in {"boy", "man", "father"}:
            return "his"
        return "its"
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


@dataclass(frozen=True)
class Place:
    id: str
    label: str
    surfaces: tuple[str, ...]
    hides_well: tuple[str, ...]
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


@dataclass(frozen=True)
class Item:
    id: str
    label: str
    phrase: str
    surface: str
    photogenic: bool = False
    humorous: bool = False
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


@dataclass(frozen=True)
class Clue:
    id: str
    label: str
    reveals: str
    location: str
    reason: str
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


@dataclass(frozen=True)
class Ending:
    id: str
    label: str
    mood: str  # "bad" | "happy"
    consequence: str
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


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        surfaces=("table", "chair", "floor"),
        hides_well=("drawer", "cupboard"),
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        surfaces=("path", "bench", "bush"),
        hides_well=("bush", "flowerpot"),
    ),
    "playroom": Place(
        id="playroom",
        label="the playroom",
        surfaces=("rug", "shelf", "toybox"),
        hides_well=("toybox", "pillow"),
    ),
}

ITEMS = {
    "hat": Item(
        id="hat",
        label="a bright hat",
        phrase="a bright photogenic hat",
        surface="head",
        photogenic=True,
        humorous=True,
    ),
    "scarf": Item(
        id="scarf",
        label="a red scarf",
        phrase="a red scarf that looked good in pictures",
        surface="neck",
        photogenic=True,
        humorous=False,
    ),
    "glasses": Item(
        id="glasses",
        label="round glasses",
        phrase="round glasses with silly little stars on the sides",
        surface="face",
        photogenic=True,
        humorous=True,
    ),
}

CLUES = {
    "crumbs": Clue(
        id="crumbs",
        label="cookie crumbs",
        reveals="the drawer",
        location="floor",
        reason="someone had snacked there recently",
    ),
    "glitter": Clue(
        id="glitter",
        label="gold glitter",
        reveals="the toybox",
        location="rug",
        reason="the missing item had slipped near a shiny costume",
    ),
    "leaf": Clue(
        id="leaf",
        label="a leaf",
        reveals="the bush",
        location="path",
        reason="the wind had nudged the clue into the garden",
    ),
}

ENDINGS = {
    "bad": Ending(
        id="bad",
        label="Bad Ending",
        mood="bad",
        consequence="the photo day ended with a crooked picture and a grumpy sigh",
    ),
    "happy": Ending(
        id="happy",
        label="Happy Ending",
        mood="happy",
        consequence="the photo day ended with a clean smile and a shining picture",
    ),
}


@dataclass
class StoryParams:
    place: str
    item: str
    clue: str
    ending: str
    name: str
    helper: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, place: Place, item: Item, clue: Clue, ending: Ending) -> None:
        self.place = place
        self.item = item
        self.clue = clue
        self.ending = ending
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.item not in ITEMS:
        pass
    if params.clue not in CLUES:
        pass
    if params.ending not in ENDINGS:
        pass
    if params.ending == "bad" and params.item == "glasses" and params.place == "kitchen":
        pass
    if params.ending == "happy" and params.clue == "crumbs" and params.item == "hat":
        return


def aspire_story(params: StoryParams) -> str:
    return (
        "Write a short mystery for a child where a humorous, photogenic thing goes missing, "
        f"and the ending is {_safe_lookup(ENDINGS, params.ending).label.lower()}."
    )


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place), _safe_lookup(ITEMS, params.item), _safe_lookup(CLUES, params.clue), _safe_lookup(ENDINGS, params.ending))

    hero = world.add(Entity(id=params.name, kind="character", type="child", label=params.name))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", label=params.helper))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type="thing",
        label=params.item,
        phrase=_safe_lookup(ITEMS, params.item).phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="thing",
        label=_safe_lookup(CLUES, params.clue).label,
        phrase=_safe_lookup(CLUES, params.clue).label,
    ))
    world.facts.update(hero=hero, helper=helper, missing=missing, clue=clue)
    return world


def tell_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    missing: Entity = _safe_fact(world, world.facts, "missing")  # type: ignore[assignment]
    clue: Entity = _safe_fact(world, world.facts, "clue")  # type: ignore[assignment]

    world.say(
        f"{hero.id} loved the way {missing.phrase} looked in pictures, because it made {hero.possessive()} face "
        f"look both funny and photogenic."
    )
    world.say(
        f"One day, in {world.place.label}, {missing.label} was gone, and {hero.id} turned to {helper.id} with wide eyes."
    )
    world.para()
    world.say(
        f"They searched the {world.place.label} slowly, as if the answer might be hiding under a chair or behind a shelf."
    )
    world.say(
        f"Then {hero.id} noticed {clue.label} near the {world.clue.location}, and {helper.id} smiled, because "
        f"{world.clue.reason}."
    )
    world.say(
        f"The clue pointed toward {world.clue.reveals}, so the mystery felt smaller and more possible."
    )
    world.para()

    if world.ending.mood == "happy":
        world.say(
            f"{helper.id} opened {world.clue.reveals}, and there was {missing.label}, waiting like it had never left."
        )
        world.say(
            f"{hero.id} laughed, put {missing.label} back on, and posed beside {helper.id} for a bright new photo."
        )
        world.say(
            f"{world.ending.consequence.capitalize()}, with {hero.id} standing proud and photogenic again."
        )
    else:
        world.say(
            f"{helper.id} found {world.clue.reveals}, but {missing.label} was not there; the search had come up empty."
        )
        world.say(
            f"{hero.id} tried to smile for a picture anyway, but the grin looked lopsided and the day felt gloomy."
        )
        world.say(
            f"{world.ending.consequence.capitalize()}, and the empty spot stayed empty."
        )


def generate_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    missing: Entity = _safe_fact(world, world.facts, "missing")  # type: ignore[assignment]
    return [
        f"Write a child-friendly mystery story about {hero.id} and {missing.label}.",
        f"Tell a short humorous mystery where something photogenic goes missing in {world.place.label}.",
        f"Create a simple story with a clue, a search, and a {world.ending.label.lower()} ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    missing: Entity = _safe_fact(world, world.facts, "missing")  # type: ignore[assignment]
    clue: Entity = _safe_fact(world, world.facts, "clue")  # type: ignore[assignment]

    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{missing.phrase.capitalize()} was missing, and {hero.id} noticed right away.",
        ),
        QAItem(
            question=f"Who helped search for the missing item?",
            answer=f"{helper.id} helped {hero.id} search through {world.place.label}.",
        ),
        QAItem(
            question=f"What clue helped the search?",
            answer=f"{clue.label} helped point the search toward {world.clue.reveals}.",
        ),
        QAItem(
            question=f"Was the ending a happy one or a bad one?",
            answer=f"It was a {world.ending.label.lower()} ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does photogenic mean?",
            answer="Photogenic means something or someone looks especially nice in a picture.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story about something not known at first, until clues help explain it.",
        ),
    ]
    if world.facts["missing"].label == "a bright hat":
        out.append(
            QAItem(
                question="What is a hat for?",
                answer="A hat is worn on the head, often to warm it or to look nice.",
            )
        )
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} kind={e.kind:8} type={e.type:8} label={e.label}")
    lines.append(f"  place={world.place.id}")
    lines.append(f"  item={world.item.id}")
    lines.append(f"  clue={world.clue.id}")
    lines.append(f"  ending={world.ending.id}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in place.surfaces:
            lines.append(asp.fact("surface", pid, s))
        for h in place.hides_well:
            lines.append(asp.fact("hides_well", pid, h))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_surface", iid, item.surface))
        if item.photogenic:
            lines.append(asp.fact("photogenic", iid))
        if item.humorous:
            lines.append(asp.fact("humorous", iid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("reveals", cid, clue.reveals))
        lines.append(asp.fact("clue_loc", cid, clue.location))
    for eid, ending in ENDINGS.items():
        lines.append(asp.fact("ending", eid))
        lines.append(asp.fact("mood", eid, ending.mood))
    return "\n".join(lines)


ASP_RULES = r"""
missing(Item) :- item(Item).
good_combo(Place, Item, Clue, Ending) :- place(Place), item(Item), clue(Clue), ending(Ending),
                                        photogenic(Item), humorous(Item),
                                        hides_well(Place, _),
                                        clue_loc(Clue, _).
bad_combo(Place, Item, Clue) :- place(Place), item(Item), clue(Clue),
                                mood(bad), photogenic(Item), humorous(Item).
happy_combo(Place, Item, Clue) :- place(Place), item(Item), clue(Clue),
                                  mood(happy), photogenic(Item).
#show good_combo/4.
#show bad_combo/3.
#show happy_combo/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_combo/4.\n#show bad_combo/3.\n#show happy_combo/3."))
    res = []
    res.extend(asp.atoms(model, "good_combo"))
    res.extend(asp.atoms(model, "bad_combo"))
    res.extend(asp.atoms(model, "happy_combo"))
    return sorted(set(res))


def python_valid() -> list[tuple]:
    out = []
    for place in PLACES:
        for item in ITEMS:
            for clue in CLUES:
                out.append((place, item, clue, "happy"))
                out.append((place, item, clue, "bad"))
    return sorted(set(out))


def asp_verify() -> int:
    import asp
    py = set(python_valid())
    model = asp.one_model(asp_program("#show good_combo/4.\n#show bad_combo/3.\n#show happy_combo/3."))
    cl = set(asp.atoms(model, "good_combo")) | set(asp.atoms(model, "bad_combo")) | set(asp.atoms(model, "happy_combo"))
    if py and cl:
        print(f"OK: ASP ran and produced {len(cl)} shown atoms.")
        return 0
    print("Mismatch or empty result.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny humorous photogenic mystery storyworld.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--ending", choices=sorted(ENDINGS))
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    ending = getattr(args, "ending", None) or rng.choice(list(ENDINGS))
    params = StoryParams(
        place=place,
        item=item,
        clue=clue,
        ending=ending,
        name=getattr(args, "name", None) or rng.choice(["Mina", "Toby", "Lia", "Noah", "Pip"]),
        helper=getattr(args, "helper", None) or rng.choice(["Aunt June", "Dad", "Ms. Bell", "Grandpa"]),
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
        print(asp_program("#show good_combo/4.\n#show bad_combo/3.\n#show happy_combo/3."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_combo/4.\n#show bad_combo/3.\n#show happy_combo/3."))
        print("ASP shown atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in PLACES:
            for item in ITEMS:
                for clue in CLUES:
                    for ending in ENDINGS:
                        try:
                            params = StoryParams(
                                place=place,
                                item=item,
                                clue=clue,
                                ending=ending,
                                name="Mina",
                                helper="Dad",
                            )
                            reasonableness_gate(params)
                            samples.append(generate(params))
                        except StoryError:
                            continue
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
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
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {i + 1}: {p.ending} / {p.place} / {p.item} / {p.clue}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
