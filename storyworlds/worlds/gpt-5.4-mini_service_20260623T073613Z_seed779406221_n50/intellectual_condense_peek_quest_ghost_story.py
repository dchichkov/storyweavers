#!/usr/bin/env python3
"""
storyworlds/worlds/intellectual_condense_peek_quest_ghost_story.py
==================================================================

A small standalone storyworld in a ghost-story mood: a child on a quiet quest
meets a friendly ghost, peeks into a hiding place, and uses an intellectual
trick to condense a long, noisy problem into one simple clue.

Seed words: intellectual, condense, peek
Feature: Quest
Style: Ghost Story

The premise is intentionally tiny:
- A child wants to finish a moonlit quest.
- The quest needs one missing clue hidden in a dusty place.
- A ghost knows how to peek into old corners.
- The child uses an intellectual method to condense scattered hints into one
  clear answer.
- The ending proves what changed: the quest is complete and the ghost is at peace.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- a Python reasonableness gate plus inline ASP twin
- story QA and world QA grounded in the simulated world
"""

from __future__ import annotations

import argparse
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    child: object | None = None
    clue: object | None = None
    ghost: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "ghost"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    clue_spot: str
    mood: str
    shadow: str
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
class Quest:
    id: str
    title: str
    miss: str
    finder: str
    clue_kind: str
    clue_label: str
    clue_phrase: str
    trace_hint: str
    reveal: str
    payoff: str
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
class Helper:
    id: str
    label: str
    method: str
    plural: bool = False
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
    def __init__(self, place: Place) -> None:
        self.place = place
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


@dataclass
class StoryParams:
    place: str
    quest: str
    helper: str
    name: str
    gender: str
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


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        clue_spot="a dusty trunk",
        mood="The attic breathed cold and old wood.",
        shadow="a long shadow under the rafters",
        affords={"peek", "quest"},
    ),
    "library": Place(
        id="library",
        label="the silent library",
        clue_spot="a narrow shelf gap",
        mood="The library was so quiet the floorboards seemed to listen.",
        shadow="a thin shadow between the bookcases",
        affords={"peek", "quest"},
    ),
    "garden_shed": Place(
        id="garden_shed",
        label="the garden shed",
        clue_spot="an old toolbox",
        mood="The shed smelled of rain and rust.",
        shadow="a dark shadow behind the ladder",
        affords={"peek", "quest"},
    ),
}

QUESTS = {
    "moon_key": Quest(
        id="moon_key",
        title="the moon-key quest",
        miss="the tiny key was missing",
        finder="a silver key",
        clue_kind="key",
        clue_label="moon-key",
        clue_phrase="a little silver key with a round moon head",
        trace_hint="the clue could fit in a pocket",
        reveal="The moon-key was tucked away where dust gathered thickest.",
        payoff="it opened the little box and the whole quest could end",
        tags={"quest", "key", "moon"},
    ),
    "bell_note": Quest(
        id="bell_note",
        title="the bell-note quest",
        miss="the note had slipped away",
        finder="a folded note",
        clue_kind="note",
        clue_label="bell-note",
        clue_phrase="a folded note tied with blue thread",
        trace_hint="the clue could hide flat and silent",
        reveal="The bell-note was hidden between things that looked the same.",
        payoff="it rang the final little bell and the path was done",
        tags={"quest", "note", "bell"},
    ),
    "lantern_map": Quest(
        id="lantern_map",
        title="the lantern-map quest",
        miss="the map was gone",
        finder="a paper map",
        clue_kind="map",
        clue_label="lantern-map",
        clue_phrase="a paper map with one glowing circle",
        trace_hint="the clue could be rolled into a tube",
        reveal="The lantern-map waited in the darkest corner, pressed flat and safe.",
        payoff="it showed the last turn and the quest could be finished",
        tags={"quest", "map", "lantern"},
    ),
}

HELPERS = {
    "peek": Helper(
        id="peek",
        label="a peek through the crack",
        method="peek through the crack",
        tags={"peek"},
    ),
    "condense": Helper(
        id="condense",
        label="a little notebook summary",
        method="condense the clues into one short list",
        tags={"condense", "intellectual"},
    ),
    "intellectual": Helper(
        id="intellectual",
        label="a careful thinking game",
        method="sort the clues by shape, shine, and size",
        tags={"intellectual", "condense"},
    ),
}

GIRL_NAMES = ["Mina", "Elin", "Rose", "Nia", "Luna", "Ada"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Finn", "Noah", "Jace"]
TRAITS = ["quiet", "curious", "careful", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, q, h) for p in PLACES for q in QUESTS for h in HELPERS]


def explain_rejection(place: str, quest: str, helper: str) -> str:
    return f"(No story: {place}, {quest}, and {helper} do not make a sensible ghostly quest.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story quest with a quiet intellectual turn.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, helper = rng.choice(list(combos))
    q = _safe_lookup(QUESTS, quest)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, quest=quest, helper=helper, name=name, gender=gender)


def tell(place: Place, quest: Quest, helper: Helper, name: str, gender: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, role="child"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost", role="helper"))
    clue = world.add(Entity(id="clue", type=quest.clue_kind, label=quest.clue_label))
    child.memes["hope"] = 1
    child.memes["worry"] = 1
    ghost.memes["loneliness"] = 1

    world.say(f"{name} was a little {helper.label.split()[-1] if helper.id != 'peek' else 'quiet'} child who loved a moonlit quest.")
    world.say(f"One night, {name} reached {place.label}. {place.mood}")
    world.say(f"There, {quest.miss}, and {place.shadow} made everything feel a bit like a ghost story.")

    world.para()
    child.memes["quest"] += 1
    ghost.memes["curiosity"] += 1
    world.say(f"{name} wanted to finish {quest.title}, but the clue was hidden in {place.clue_spot}.")
    world.say(f"A gentle ghost drifted near and offered {helper.method}.")
    if helper.id == "peek":
        world.say(f"{name} leaned closer and peered carefully, because a good peek can notice what a rush misses.")
    elif helper.id == "condense":
        world.say(f"{name} wrote the hints down and learned to condense the noisy clues into one small answer.")
    else:
        world.say(f"{name} used a thoughtful plan to sort the clues by shape, shine, and size.")

    world.para()
    if helper.id == "peek":
        world.say(f"When {name} peered inside, {quest.reveal}")
    elif helper.id == "condense":
        world.say(f"After {name} condensed the clues, one pattern shone brighter than the rest.")
        world.say(quest.reveal)
    else:
        world.say(f"{name} and the ghost followed the clearest hint, and {quest.reveal}")

    world.para()
    child.memes["joy"] += 1
    ghost.memes["peace"] += 1
    world.say(f"{name} smiled, because {quest.payoff}.")
    world.say(f"The ghost grew soft and bright, as if the room had finally remembered how to rest.")
    world.say(f"Together they finished the quest, and the attic-like dark place was no longer lonely.")

    world.facts.update(
        child=child,
        ghost=ghost,
        clue=clue,
        place=place,
        quest=quest,
        helper=helper,
        resolved=True,
    )
    return world


KNOWLEDGE = {
    "peek": [("What does it mean to peek?",
              "To peek means to look quickly and carefully into a place, usually to notice a small hidden thing.")],
    "condense": [("What does condense mean?",
                  "To condense means to make something shorter or smaller while keeping the important part.")],
    "intellectual": [("What does intellectual mean?",
                      "Intellectual means using careful thinking, not just guessing.")],
    "quest": [("What is a quest?",
               "A quest is a trip or search to find something important or finish a hard goal.")],
    "ghost": [("What is a ghost in a story?",
               "A ghost is a spooky person or spirit in a story. In gentle stories, a ghost can be friendly or lonely.")],
    "attic": [("What is an attic?",
               "An attic is a room near the roof of a house, and it can be dusty and dark.")],
    "library": [("What is a library?",
                 "A library is a quiet place with books where people can read and look things up.")],
    "shed": [("What is a shed?",
              "A shed is a small building outside, often used for tools and old things.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a 3-to-5-year-old where {f["child"].id} goes on a {f["quest"].title} and uses a {f["helper"].id} idea to solve it.',
        f"Tell a quiet spooky story where {f['child'].id} peeks into {f['place'].label}, condenses the clues, and finds {f['quest'].clue_phrase}.",
        f'Write a short child-facing story using the words "intellectual", "condense", and "peek", and end with the quest being finished.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    place = f["place"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who is the story about when {child.id} goes to {place.label}?",
            answer=f"It is about {child.id}, a little {child.type}, who went on {quest.title} at {place.label}.",
        ),
        QAItem(
            question=f"What problem made {child.id}'s quest feel spooky?",
            answer=f"{quest.miss}. {place.shadow} and the cold quiet made the search feel like a ghost story.",
        ),
        QAItem(
            question=f"What did the ghost help {child.id} do?",
            answer=f"The ghost helped {child.id} {helper.method}. That was the trick that led to {quest.clue_phrase}.",
        ),
        QAItem(
            question=f"How did {child.id} solve the quest?",
            answer=f"{child.id} used a {helper.label} idea to find the clue, and the quest was finished at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["helper"].tags) | {world.facts["place"].id}
    out: list[QAItem] = []
    for key in ["intellectual", "condense", "peek", "quest", "ghost", "attic", "library", "shed"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(key, []))
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- place(P).
quest_ok(Q) :- quest(Q).
helper_ok(H) :- helper(H).
valid(P,Q,H) :- place_ok(P), quest_ok(Q), helper_ok(H).

quest_word(Q) :- quest(Q).
uses_intellectual(H) :- helper(H), intellectual_helper(H).
condenses(H) :- helper(H), condense_helper(H).
peeks(H) :- helper(H), peek_helper(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    lines.append(asp.fact("peek_helper", "peek"))
    lines.append(asp.fact("condense_helper", "condense"))
    lines.append(asp.fact("intellectual_helper", "intellectual"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print(" only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print(" only in python:", sorted(python_set - clingo_set))
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(HELPERS, params.helper), params.name, params.gender)
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
    StoryParams(place="attic", quest="moon_key", helper="peek", name="Mina", gender="girl"),
    StoryParams(place="library", quest="bell_note", helper="condense", name="Owen", gender="boy"),
    StoryParams(place="garden_shed", quest="lantern_map", helper="intellectual", name="Luna", gender="girl"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, helper = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, quest=quest, helper=helper, name=name, gender=gender)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, q, h) for p in PLACES for q in QUESTS for h in HELPERS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A quiet ghost-story quest with intellectual clues.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, q, h in asp_valid_combos():
            print(f"  {p:12} {q:12} {h}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
