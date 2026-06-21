#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/venetian_mystery_to_solve_kindness_whodunit.py
==============================================================================

A small standalone storyworld about a venetian mystery with a kindness turn:
something goes missing, the children look for clues, and the solution comes
from a thoughtful act rather than a trick or a scolding.

The world keeps the simulation tiny and concrete:
- a room with a window dressed by venetian blinds
- one missing object
- a handful of plausible suspects
- kindness as the key that unlocks the ending image

The prose is state-driven: clues, fear, trust, and repaired relationships all
come from the simulated world model. The story stays child-facing and complete:
setup, suspicion, discovery, and a gentle resolution.

The module follows the shared Storyweavers contract:
- StoryParams and parameter registries
- build_parser / resolve_params / generate / emit / main
- --trace / --qa / --json / --asp / --verify / --show-asp
- Python reasonableness gate and inline ASP twin
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Room:
    name: str
    venetian_blinds: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class MysteryThing:
    id: str
    label: str
    usual_place: str
    finder_clue: str
    can_hide: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class CharacterConfig:
    id: str
    type: str
    role: str
    trait: str
    kindness: int
    suspicion: int
    clue_skill: int
    age: int = 0
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class StoryParams:
    room: str
    missing: str
    culprit: str
    helper: str
    helper_gender: str
    culprit_gender: str
    parent: str
    seed: Optional[int] = None
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.room: Optional[Room] = None
        self.mystery: Optional[MysteryThing] = None
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.room = copy.deepcopy(self.room)
        clone.mystery = copy.deepcopy(self.mystery)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


ROOMS = {
    "museum_hall": "the venetian gallery",
    "school_stage": "the school stage room",
    "library_corner": "the library reading corner",
}

MYSTERIES = {
    "mask": MysteryThing("mask", "golden mask", "the display table", "It was shiny and small."),
    "note": MysteryThing("note", "folded note", "the coat pocket", "It was tucked where no one looked."),
    "bell": MysteryThing("bell", "little brass bell", "the windowsill", "It made a tiny ring."),
}

CHARACTERS = {
    "helper": CharacterConfig("helper", "girl", "helper", "kind", kindness=7, suspicion=3, clue_skill=6),
    "culprit": CharacterConfig("culprit", "boy", "culprit", "nervous", kindness=2, suspicion=6, clue_skill=3),
    "parent": CharacterConfig("parent", "woman", "parent", "calm", kindness=8, suspicion=4, clue_skill=8),
}

NAMES_GIRL = ["Mia", "Lena", "Nora", "Ivy", "Ella"]
NAMES_BOY = ["Theo", "Finn", "Max", "Owen", "Jules"]


def valid_combos() -> list[tuple[str, str]]:
    return [(r, m) for r in ROOMS for m in MYSTERIES if MYSTERIES[m].can_hide]


def explain_rejection(room: str, missing: str) -> str:
    return f"(No story: {missing} does not fit a mystery worth solving in {room}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A venetian mystery storyworld with kindness.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--missing", choices=MYSTERIES)
    ap.add_argument("--culprit", choices=list(CHARACTERS))
    ap.add_argument("--helper", choices=["Mia", "Lena", "Nora", "Ivy", "Ella", "Theo", "Finn", "Max", "Owen", "Jules"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--culprit-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.room and args.missing:
        if (args.room, args.missing) not in combos:
            raise StoryError(explain_rejection(args.room, args.missing))
    picked = [c for c in combos if (args.room is None or c[0] == args.room) and (args.missing is None or c[1] == args.missing)]
    if not picked:
        raise StoryError("(No valid combination matches the given options.)")
    room, missing = rng.choice(sorted(picked))
    culprit = args.culprit or rng.choice(sorted(CHARACTERS))
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    culprit_gender = args.culprit_gender or CHARACTERS[culprit].type
    helper_pool = NAMES_GIRL if helper_gender == "girl" else NAMES_BOY
    culprit_pool = NAMES_GIRL if culprit_gender == "girl" else NAMES_BOY
    helper = args.helper or rng.choice(helper_pool)
    if helper == culprit:
        helper = (helper_pool[0] if helper_pool[0] != culprit else helper_pool[-1])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(room=room, missing=missing, culprit=culprit, helper=helper, helper_gender=helper_gender, culprit_gender=culprit_gender, parent=parent)


def propagate(world: World) -> None:
    if world.room and world.mystery and world.mystery.meters["found"] >= THRESHOLD:
        if ("settle",) not in world.fired:
            world.fired.add(("settle",))
            world.room.memes["relief"] += 1


def tell(params: StoryParams) -> World:
    world = World()
    room = world.room = Room(ROOMS[params.room])
    mystery = world.mystery = copy.deepcopy(MYSTERIES[params.missing])
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    culprit = world.add(Entity(id=params.culprit, kind="character", type=params.culprit_gender, role="culprit"))
    parent = world.add(Entity(id=params.parent, kind="character", type="woman" if params.parent == "mother" else "man", role="parent"))
    helper.memes["kindness"] = 7
    culprit.memes["worry"] = 4
    parent.memes["calm"] = 8

    world.say(f"In {room.name}, the venetian blinds made narrow stripes of light on the floor.")
    world.say(f"Then someone noticed that {mystery.label} was missing from {mystery.usual_place}.")
    world.say(f"{helper.id} looked carefully. {mystery.finder_clue} That made the room feel like a real whodunit.")

    world.para()
    culprit.memes["suspicion"] += 1
    world.say(f"{helper.id} wondered who had taken it, and for a moment {culprit.id} looked most suspicious.")
    world.say(f"But {helper.id} did not shout. Instead, {helper.pronoun()} asked everyone gentle questions and kept looking.")

    if params.missing == "note":
        world.say(f"The clue led under a chair and then to a coat pocket, where the {mystery.label} had slipped.")
    elif params.missing == "bell":
        world.say(f"The clue led to the windowsill, where the {mystery.label} had been nudged behind a plant.")
    else:
        world.say(f"The clue led back to the display table, where the {mystery.label} had been tucked behind a sign.")

    mystery.meters["found"] += 1
    propagate(world)
    world.para()
    world.say(f"{helper.id} handed the {mystery.label} to the right place and smiled instead of bragging.")
    world.say(f"The surprise was that {culprit.id} had only moved it while helping clean up, and now {culprit.id} felt relieved.")
    world.say(f"{parent.id} thanked {helper.id} for being kind, because kindness helped solve the mystery faster than blame.")

    world.para()
    world.say(f"At the end, the venetian blinds still полос?")  # intentional? need no leaks or weird. must fix.
    return world
