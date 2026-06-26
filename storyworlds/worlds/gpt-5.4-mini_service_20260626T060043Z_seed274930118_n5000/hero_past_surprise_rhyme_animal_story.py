#!/usr/bin/env python3
"""
storyworlds/worlds/hero_past_surprise_rhyme_animal_story.py
===========================================================

A small animal-story world with a hero, a remembered past, a surprise, and a
light rhyme turn.

Premise:
- A young animal hero remembers a past wish.
- A surprise arrives in the form of a note, gift, or clue.
- The hero must choose whether to trust the surprise.
- A rhyme helps the hero understand the turn and resolve the moment.

This script is self-contained and uses the shared StorySample / QAItem /
StoryError containers from storyworlds/results.py.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "rabbit", "fox", "cat", "kitten", "bird", "dog", "puppy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case] if self.memes.get("male", 0) >= self.memes.get("female", 0) else {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def subj(self) -> str:
        return self.pronoun("subject")

    def obj(self) -> str:
        return self.pronoun("object")

    def pos(self) -> str:
        return self.pronoun("possessive")
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
    id: str
    label: str
    mood: str
    supports: set[str] = field(default_factory=set)
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


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    kind: str
    reveals: str
    kind_of_good: str = "kind"
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
class Rhyme:
    id: str
    first: str
    second: str
    third: str
    fourth: str
    lesson: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "meadow": Place("meadow", "the meadow", "bright", {"surprise", "rhyme"}),
    "forest": Place("forest", "the forest path", "soft", {"surprise", "rhyme"}),
    "pond": Place("pond", "the pond bank", "still", {"surprise", "rhyme"}),
}

HERO_TYPES = {
    "rabbit": "rabbit",
    "fox": "fox",
    "mouse": "mouse",
    "bird": "bird",
    "cat": "cat",
}

SURPRISES = {
    "note": Surprise(
        "note",
        "a folded note",
        "a folded note with a bright ribbon",
        "note",
        "a hidden rhyme",
    ),
    "basket": Surprise(
        "basket",
        "a little basket",
        "a little basket under a leaf",
        "basket",
        "a shared treat",
    ),
    "song": Surprise(
        "song",
        "a soft song",
        "a soft song drifting from the trees",
        "song",
        "a friendly greeting",
    ),
}

RHYMES = {
    "bell": Rhyme(
        "bell",
        "When the bell sang ding,",
        "the rabbit heard a springy thing,",
        "the past came back in a tiny ring,",
        "and the hero smiled at what good news could bring.",
        "a gentle surprise can open a remembered wish",
    ),
    "trail": Rhyme(
        "trail",
        "Along the trail, a leaf spun low,",
        "the fox saw footprints in a row,",
        "the past said, 'Go, and do not slow,'",
        "and the hero found the kind hello.",
        "old clues can lead to a happy surprise",
    ),
    "pond": Rhyme(
        "pond",
        "By the pond, the water gleamed,",
        "the mouse found more than once had seemed,",
        "the past was kinder than it dreamed,",
        "and the surprise was just what friendship meant.",
        "a surprise can reveal a warm memory",
    ),
}

TRAITS = ["curious", "gentle", "brave", "cheerful", "patient"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    hero_type: str
    name: str
    trait: str
    surprise: str
    rhyme: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
hero(H) :- hero_type(H).
place(P) :- place_id(P).
surprise(S) :- surprise_id(S).
rhyme(R) :- rhyme_id(R).

compatible(P,S,R) :- place_supports(P,surprise), place_supports(P,rhyme),
                     surprise_kind(S, _), rhyme_kind(R, _).

compatible_story(P,H,S,R) :- hero(H), place(P), surprise(S), rhyme(R), compatible(P,S,R).
#show compatible_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_id", pid))
        for feat in sorted(place.supports):
            lines.append(asp.fact("place_supports", pid, feat))
    for hid in HERO_TYPES:
        lines.append(asp.fact("hero_type", hid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise_id", sid))
        lines.append(asp.fact("surprise_kind", sid, s.kind))
    for rid, r in RHYMES.items():
        lines.append(asp.fact("rhyme_id", rid))
        lines.append(asp.fact("rhyme_kind", rid, "lyric"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible_story")))


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def _hero_intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.traits[0]} {hero.type} who loved quiet paths and warm days.")


def _past_memory(world: World, hero: Entity) -> None:
    hero.memes["past"] += 1
    world.say(f"{hero.id} remembered a past day when a small wish had almost come true.")


def _arrival(world: World, hero: Entity, surprise: Surprise) -> None:
    world.say(f"Near {world.place.label}, {hero.id} found {surprise.phrase}.")
    hero.memes["surprised"] += 1
    hero.meters["attention"] = hero.meters.get("attention", 0) + 1


def _doubt(world: World, hero: Entity, surprise: Surprise) -> None:
    hero.memes["worry"] += 1
    world.say(f"At first, {hero.id} blinked. The surprise felt odd, and {hero.pronoun('possessive')} whiskers twitched.")


def _rhyme_turn(world: World, hero: Entity, rhyme: Rhyme, surprise: Surprise) -> None:
    world.say(rhyme.first)
    world.say(rhyme.second)
    world.say(rhyme.third)
    world.say(rhyme.fourth)
    hero.memes["understood"] += 1
    world.facts["lesson"] = rhyme.lesson
    world.say(f"Then {hero.id} understood: {rhyme.lesson}.")


def _resolution(world: World, hero: Entity, surprise: Surprise) -> None:
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0
    world.say(
        f"{hero.id} smiled and took the surprise gently. It was not a trick at all; "
        f"it was a kind gift meant for {hero.pronoun('object')}."
    )
    world.say(
        f"The little hero carried it home with a happy step, and the past wish felt true at last."
    )


def _trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  place: {world.place.id}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def generate_story_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    surprise = _safe_lookup(SURPRISES, params.surprise)
    rhyme = _safe_lookup(RHYMES, params.rhyme)

    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.hero_type,
        traits=[params.trait],
    ))
    hero.memes["past"] = 1
    hero.memes["female"] = 1 if params.hero_type in {"rabbit", "bird", "cat"} and params.name[0] in "AEIOU" else 0
    hero.memes["male"] = 1 if hero.memes["female"] == 0 else 0

    world.facts.update(hero=hero, surprise=surprise, rhyme=rhyme, place=place)

    _hero_intro(world, hero)
    _past_memory(world, hero)
    world.para()
    _arrival(world, hero, surprise)
    _doubt(world, hero, surprise)
    world.para()
    _rhyme_turn(world, hero, rhyme, surprise)
    _resolution(world, hero, surprise)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts_for(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    surprise: Surprise = _safe_fact(world, f, "surprise")
    rhyme: Rhyme = _safe_fact(world, f, "rhyme")
    return [
        f"Write a short animal story about a {hero.traits[0]} {hero.type} named {hero.id} who remembers the past and finds {surprise.label}.",
        f"Tell a gentle story with a surprise and a rhyme where {hero.id} learns that old wishes can return kindly.",
        f"Write a child-friendly animal tale set at {world.place.label} that ends with this rhyme feeling: {rhyme.lesson}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    surprise: Surprise = _safe_fact(world, f, "surprise")
    rhyme: Rhyme = _safe_fact(world, f, "rhyme")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.traits[0]} {hero.type} at {place.label}.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} find?",
            answer=f"{hero.id} found {surprise.phrase}, which made the day feel special.",
        ),
        QAItem(
            question=f"What helped {hero.id} understand the surprise?",
            answer=f"A rhyme helped {hero.id} understand it. The rhyme showed that {rhyme.lesson}.",
        ),
        QAItem(
            question=f"Why did {hero.id} pause at first?",
            answer=f"{hero.id} paused because the surprise felt strange at first, and {hero.id} remembered a past wish before trusting it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears or happens when you did not know it was coming.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a set of words or lines that sound alike at the ends, which can make a poem or song feel bouncy and fun.",
        ),
        QAItem(
            question="What does it mean to remember the past?",
            answer="To remember the past means to think about something that happened before, like an old day or a wish from earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with hero, past, surprise, and rhyme.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero-type", choices=sorted(HERO_TYPES))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
    ap.add_argument("--rhyme", choices=sorted(RHYMES))
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
    hero_type = getattr(args, "hero_type", None) or rng.choice(list(HERO_TYPES))
    name = getattr(args, "name", None) or rng.choice(["Pip", "Milo", "Nia", "Ruby", "Toby", "Luna"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    rhyme = getattr(args, "rhyme", None) or rng.choice(list(RHYMES))
    return StoryParams(place=place, hero_type=hero_type, name=name, trait=trait, surprise=surprise, rhyme=rhyme)


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for h in HERO_TYPES:
            for s in SURPRISES:
                for r in RHYMES:
                    combos.append((p, h, s, r))
    return combos


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: ASP gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if clingo_set - py_set:
        print("Only in ASP:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("Only in Python:", sorted(py_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        items = asp_valid()
        print(f"{len(items)} compatible stories")
        for item in items:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in PLACES:
            for hero_type in HERO_TYPES:
                for surprise in SURPRISES:
                    for rhyme in RHYMES:
                        params = StoryParams(
                            place=place,
                            hero_type=hero_type,
                            name="Pip",
                            trait="curious",
                            surprise=surprise,
                            rhyme=rhyme,
                            seed=base_seed,
                        )
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(100, getattr(args, "n", None) * 40):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
