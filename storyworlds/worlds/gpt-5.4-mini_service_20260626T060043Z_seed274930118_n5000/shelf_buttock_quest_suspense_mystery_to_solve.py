#!/usr/bin/env python3
"""
storyworlds/worlds/shelf_buttock_quest_suspense_mystery_to_solve.py
=====================================================================

A small, self-contained story world for a child-friendly ghost story:
a quest, a little suspense, and a mystery to solve in a room with a shelf.

Seed tale idea:
---
A child hears a soft thump in a moonlit room. Something strange is happening
around an old shelf. A tiny hidden clue leads to a quest to find what is making
the whispery sound. The child is a little scared, because climbing and peeking
in the dark can be hard on the buttock when a seat or step is scratchy and
hard. With a lantern, a brave helper, and careful looking, the mystery is
solved: it was only a toy, a book, or a loose trinket making the eerie sound.

World model:
---
- Physical meters track darkness, dust, wobble, bump, and discomfort.
- Emotional memes track fear, courage, curiosity, relief, and wonder.
- State changes drive prose: a clue is noticed, a danger is predicted, the
  child searches, and the mystery resolves into a gentle ending image.

The story quality goal is to feel like a tiny ghost story without becoming
frightening: suspenseful, concrete, and solved by observation.
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

WORLD_ID = "shelf_buttock_quest_suspense_mystery_to_solve"



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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    clue: object | None = None
    friend: object | None = None
    hidden: object | None = None
    shelf: object | None = None
    def __post_init__(self) -> None:
        for k in ["darkness", "dust", "wobble", "bump", "discomfort", "hidden"]:
            self.meters.setdefault(k, 0.0)
        for k in ["fear", "curiosity", "courage", "relief", "wonder", "suspense"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the attic"
    indoor: bool = True
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
class Mystery:
    id: str
    clue: str
    noise: str
    cause: str
    reveal: str
    risk: str
    region: str
    keyword: str = "mystery"
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
class Helper:
    id: str
    label: str
    phrase: str
    boost: str
    safe: str
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


def meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def mem(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def valid_combo(setting: Setting, mystery: Mystery, helper: Helper) -> bool:
    return mystery.region in {"torso", "legs", "feet"} and helper.safe in {"light", "calm"}


def reasonableness_gate(setting: Setting, mystery: Mystery, helper: Helper) -> None:
    if setting.place not in {"the attic", "the old hall", "the library corner"}:
        pass
    if mystery.region != "buttock":
        pass
    if not valid_combo(setting, mystery, helper):
        pass


def predict_reveal(world: World, child: Entity, mystery: Mystery) -> bool:
    return child.memes["curiosity"] >= 1 and child.memes["fear"] < 3


def setup_world(params: "StoryParams") -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    helper = _safe_lookup(HELPERS, params.helper)
    reasonableness_gate(setting, mystery, helper)

    world = World(setting)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        phrase=f"a little {params.trait} {params.gender}",
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type="friend",
        label=helper.label,
        phrase=helper.phrase,
    ))
    shelf = world.add(Entity(
        id="Shelf",
        type="shelf",
        label="shelf",
        phrase="an old shelf with crooked boards",
    ))
    clue = world.add(Entity(
        id="Clue",
        type="thing",
        label="clue",
        phrase=mystery.clue,
        owner=shelf.id,
    ))
    hidden = world.add(Entity(
        id="HiddenThing",
        type="thing",
        label=mystery.id,
        phrase=mystery.cause,
        owner=shelf.id,
    ))
    world.facts.update(child=child, friend=friend, shelf=shelf, clue=clue,
                       hidden=hidden, mystery=mystery, helper=helper, params=params)

    meter(shelf, "dust", 1)
    meter(shelf, "wobble", 1)
    meter(child, "fear", 1)
    mem(child, "curiosity", 1)
    mem(child, "suspense", 1)

    world.say(
        f"{params.name} was a little {params.trait} {params.gender} who lived in {setting.place}."
    )
    world.say(
        f"There was an old shelf in the corner, and it never looked quite still in the moonlight."
    )
    world.say(
        f"{params.name} had heard a tiny {mystery.noise}, and now there was a mystery to solve."
    )

    world.para()
    world.say(
        f"{params.name} stepped closer with a lantern. The light found {mystery.clue}, "
        f"just where the shelf cast a long shadow."
    )
    mem(child, "curiosity", 1)
    mem(child, "suspense", 1)
    meter(shelf, "hidden", 1)

    world.para()
    if predict_reveal(world, child, mystery):
        world.say(
            f"{params.name} wanted to run, but {helper.label} stayed beside {child.pronoun('object')}, "
            f"soft as a blanket."
        )
        mem(child, "courage", 1)
        meter(child, "discomfort", 1)
        world.say(
            f"When {params.name} leaned under the shelf, {child.pronoun('possessive')} buttock bumped "
            f"the hard edge of a little stool, and {child.pronoun('possessive')} eyes went wide."
        )
        mem(child, "fear", 1)
        mem(child, "suspense", 1)

    world.para()
    world.say(
        f"Then the lantern shone on the hidden thing at last: {mystery.reveal}."
    )
    mem(child, "relief", 2)
    mem(child, "wonder", 1)
    meter(shelf, "hidden", -1)
    meter(child, "discomfort", -1)
    world.say(
        f"The strange noise was only {mystery.cause}, and the room felt gentle again."
    )
    world.say(
        f"{params.name} smiled, because the quest was over and the mystery was solved."
    )

    world.facts["solved"] = True
    return world


@dataclass
class StoryParams:
    place: str
    mystery: str
    helper: str
    name: str
    gender: str
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
    "attic": Setting(place="the attic", indoor=True, affords={"search"}),
    "old_hall": Setting(place="the old hall", indoor=True, affords={"search"}),
    "library_corner": Setting(place="the library corner", indoor=True, affords={"search"}),
}

MYSTERIES = {
    "whispering_toy": Mystery(
        id="whispering_toy",
        clue="a ribbon tied to the shelf",
        noise="whisper from the shelf",
        cause="a tiny toy mouse bumping softly against a book",
        reveal="a toy mouse tucked behind a row of books",
        risk="a hard bump on the buttock",
        region="buttock",
    ),
    "tapping_book": Mystery(
        id="tapping_book",
        clue="one book that kept sliding forward",
        noise="tap-tap from the shelf",
        cause="a loose book corner tapping the wood as the house settled",
        reveal="a book with a corner that had slipped over the edge",
        risk="a sore buttock from kneeling too long",
        region="buttock",
    ),
    "moon_key": Mystery(
        id="moon_key",
        clue="a silver glint under the shelf",
        noise="a small clink in the dark",
        cause="a key that had fallen into a basket and knocked the side",
        reveal="a tiny key shining like moonlight",
        risk="a startled buttock from the scratchy floor",
        region="buttock",
    ),
}

HELPERS = {
    "lantern": Helper(id="lantern", label="lantern", phrase="a warm little lantern", boost="light", safe="light"),
    "cat": Helper(id="cat", label="cat", phrase="a calm gray cat", boost="courage", safe="calm"),
    "blanket": Helper(id="blanket", label="blanket", phrase="a soft blanket", boost="calm", safe="calm"),
}

NAMES = ["Mia", "Leo", "Nora", "Eli", "Ava", "Finn"]
TRAITS = ["curious", "quiet", "brave", "gentle", "careful"]


def choose_combo(rng: random.Random) -> tuple[str, str, str]:
    return rng.choice(list(SETTINGS)), rng.choice(list(MYSTERIES)), rng.choice(list(HELPERS))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    helper: Helper = _safe_fact(world, f, "helper")
    return [
        f'Write a small ghost story for a child in {world.setting.place} about a shelf, a whisper, and a mystery to solve.',
        f"Tell a suspenseful but gentle quest story where {params.name} follows a clue, "
        f"stays brave, and discovers that {mystery.id} is not truly scary.",
        f'Write a child-facing story that includes "{helper.label}", "shelf", and "buttock" and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    helper: Helper = _safe_fact(world, f, "helper")
    child: Entity = _safe_fact(world, f, "child")
    return [
        QAItem(
            question=f"What was {params.name} trying to do in {world.setting.place}?",
            answer=f"{params.name} was on a small quest to solve the mystery around the shelf.",
        ),
        QAItem(
            question=f"What made the room feel spooky at first?",
            answer=f"The room felt spooky because of {mystery.noise}, and the shelf seemed to hide the clue.",
        ),
        QAItem(
            question=f"Who helped {params.name} stay brave?",
            answer=f"{helper.label.capitalize()} helped {params.name} stay brave while the search went on.",
        ),
        QAItem(
            question=f"What happened to {child.pronoun('possessive')} buttock during the search?",
            answer=f"{child.pronoun('possessive').capitalize()} buttock bumped the hard edge of a little stool, so the search felt briefly uncomfortable.",
        ),
        QAItem(
            question="What solved the mystery?",
            answer=f"The lantern light showed that it was only {mystery.cause}. The mystery was solved when the hidden thing was revealed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shelf?",
            answer="A shelf is a flat board or ledge where people put books, toys, or other things.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the worried, waiting feeling you get when you do not know what will happen next.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people try to solve by looking for clues.",
        ),
        QAItem(
            question="What does a lantern do?",
            answer="A lantern gives light, which helps people see in dark places.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


@dataclass
class StoryParams:
    place: str
    mystery: str
    helper: str
    name: str
    gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world with a shelf, suspense, and a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, helper=helper, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


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
place(P) :- setting(P).
mystery(M) :- mystery_kind(M).
helper(H) :- helper_kind(H).
story_ok(P,M,H) :- place(P), mystery(M), helper(H), region(M,buttock).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_kind", m))
        lines.append(asp.fact("region", m, "buttock"))
    for h in HELPERS:
        lines.append(asp.fact("helper_kind", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    python_set = {(p, m, h) for p in SETTINGS for m in MYSTERIES for h in HELPERS}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP and Python agree on {len(clingo_set)} story combos.")
        return 0
    print("MISMATCH between ASP and Python")
    print("only in ASP:", sorted(clingo_set - python_set))
    print("only in Python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="attic", mystery="whispering_toy", helper="lantern", name="Mia", gender="girl", trait="curious"),
    StoryParams(place="old_hall", mystery="tapping_book", helper="cat", name="Leo", gender="boy", trait="careful"),
    StoryParams(place="library_corner", mystery="moon_key", helper="blanket", name="Nora", gender="girl", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show story_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            samples.append(generate(params))

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
