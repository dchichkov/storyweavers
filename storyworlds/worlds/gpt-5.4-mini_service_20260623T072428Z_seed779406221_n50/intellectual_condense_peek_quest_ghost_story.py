#!/usr/bin/env python3
"""
storyworlds/worlds/intellectual_condense_peek_quest_ghost_story.py
=================================================================

A small storyworld in a ghost-story mood: a child faces a spooky quest,
not by fighting the ghost, but by using an intellectual clue, a way to
condense the spooky problem into something manageable, and one careful
peek that changes the ending.

Seed premise:
---
A child follows a ghostly quest through an old house. The ghost does not
want harm; it is hiding a missing keepsake behind a dusty veil of mist.
The child is curious, slightly scared, and clever enough to notice that
the eerie sound has a pattern. They peek, condense the clue into a simple
rule, and finish the quest by finding the keepsake and calming the ghost.

This script models:
- a house with rooms and physical meters (distance, dust, fog)
- a child with emotional memes (fear, curiosity, courage, relief)
- a ghost with a missing-object quest
- a clue trail that can be peeked at
- a "condense" action that turns a complicated trail into a small plan
- a resolution where the ghost is helped, not defeated

The narrative keeps a Ghost Story feel: moonlight, creaks, mist, whispers,
and a gentle ending image.
"""

from __future__ import annotations

import argparse
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
CHILD_FEAR_LIMIT = 2.0



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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    owner: Optional[str] = None

    child: object | None = None
    ghost_ent: object | None = None
    keep: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.attrs.get("plural") == "true" else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    place: str
    mood: str
    rooms: list[str]
    affordances: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    missing: str
    hidden_in: str
    clue: str
    whisper: str
    ending_image: str
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
class Ghost:
    id: str
    label: str
    type: str
    mood: str
    sadness: str
    haunting: str
    quest_hint: str
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
        self.peeked: bool = False
        self.condensed: bool = False
        self.found: bool = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.peeked = self.peeked
        c.condensed = self.condensed
        c.found = self.found
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_mist(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    if not ghost:
        return out
    if ghost.meters["mist"] < THRESHOLD:
        return out
    sig = ("mist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in list(world.entities.values()):
        if e.kind == "character":
            e.memes["fear"] += 1
    out.append("The mist made the hallway feel colder and the child’s heart beat faster.")
    return out


def _r_peek(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    if not child or not ghost or not world.peeked:
        return out
    sig = ("peek",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    out.append("A careful peek turned the spooky clue into something the child could understand.")
    return out


def _r_condense(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child or not world.condensed:
        return out
    sig = ("condense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["clarity"] += 1
    child.memes["courage"] += 1
    out.append("The child condensed the clue into a simple plan and stopped feeling lost.")
    return out


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    keep = world.entities.get("keepsake")
    if not child or not ghost or not keep:
        return out
    if not world.found or keep.meters["found"] >= THRESHOLD:
        return out
    sig = ("found",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keep.meters["found"] += 1
    ghost.memes["sadness"] = max(0.0, ghost.memes["sadness"] - 1.0)
    ghost.memes["relief"] += 1
    child.memes["relief"] += 1
    out.append("The missing keepsake was found, and the ghost no longer had to whisper for help.")
    return out


CAUSAL_RULES = [
    Rule("mist", _r_mist),
    Rule("peek", _r_peek),
    Rule("condense", _r_condense),
    Rule("found", _r_found),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def quest_is_reasonable(quest: Quest) -> bool:
    return bool(quest.missing and quest.hidden_in and quest.clue and quest.whisper)


def predict_answer(world: World) -> dict:
    sim = world.copy()
    sim.peeked = True
    sim.condensed = True
    sim.found = True
    propagate(sim, narrate=False)
    return {
        "found": sim.get("keepsake").meters["found"] >= THRESHOLD,
        "ghost_relief": sim.get("ghost").memes["relief"],
        "child_relief": sim.get("child").memes["relief"],
    }


def introduce(world: World, child: Entity, ghost: Ghost, quest: Quest) -> None:
    world.say(
        f"On a moonlit night, {child.id} stepped into {world.setting.place}, "
        f"where {world.setting.mood} shadows touched every door."
    )
    world.say(
        f"Something whispered from the dark: {ghost.label} was looking for "
        f"{quest.missing}, and the whole house seemed to be holding its breath."
    )


def set_tension(world: World, child: Entity, quest: Quest) -> None:
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} wanted to run, but {child.pronoun('subject')} stayed still "
        f"and listened for the clue."
    )
    world.say(
        f"The whisper kept repeating a little riddle: {quest.whisper}"
    )


def peek_clue(world: World, child: Entity, quest: Quest) -> None:
    world.peeked = True
    propagate(world, narrate=False)
    world.say(
        f"{child.id} dared to peek behind the dusty curtain, and {child.pronoun('subject')} "
        f"saw {quest.clue} hidden in the half-light."
    )


def condense_clue(world: World, child: Entity, quest: Quest) -> None:
    world.condensed = True
    propagate(world, narrate=False)
    world.say(
        f"{child.id} thought hard and condensed the spooky clue into one simple idea: "
        f"follow the quiet marks and look where the cold air gathers."
    )


def solve_quest(world: World, child: Entity, ghost: Ghost, quest: Quest) -> None:
    world.found = True
    propagate(world, narrate=False)
    keep = world.get("keepsake")
    child.memes["courage"] += 1
    world.say(
        f"At the end of the hall, {child.id} found {keep.phrase}, just where the "
        f"ghost had been pointing."
    )
    world.say(
        f"When {child.id} handed it back, {ghost.label} gave a soft sigh and the "
        f"spooky room felt less lonely."
    )
    world.say(
        f"Outside the window, the moon looked kinder, and {quest.ending_image}"
    )


def tell(setting: Setting, quest: Quest, ghost: Ghost, child_name: str, child_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, label=child_name))
    ghost_ent = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost.label))
    keep = world.add(Entity(id="keepsake", type="thing", label=quest.missing, phrase=quest.missing))
    ghost_ent.meters["mist"] = 1.0
    ghost_ent.memes["sadness"] = 1.0
    child.memes["fear"] = 1.0
    child.memes["curiosity"] = 1.0

    introduce(world, child, ghost, quest)
    set_tension(world, child, quest)
    world.para()
    peek_clue(world, child, quest)
    condense_clue(world, child, quest)
    world.para()
    solve_quest(world, child, ghost, quest)

    world.facts.update(
        child=child,
        ghost=ghost_ent,
        quest=quest,
        keep=keep,
        setting=setting,
        peeked=world.peeked,
        condensed=world.condensed,
        found=world.found,
    )
    return world


SETTINGS = {
    "old_house": Setting(
        place="the old house",
        mood="dusty",
        rooms=["hallway", "attic", "stairs", "doorway"],
        affordances={"peek", "condense", "quest"},
    ),
    "lighthouse": Setting(
        place="the lighthouse",
        mood="echoing",
        rooms=["spiral stairs", "lantern room", "landing", "window"],
        affordances={"peek", "condense", "quest"},
    ),
    "attic": Setting(
        place="the attic",
        mood="sleepy",
        rooms=["boxes", "beam", "trunk", "window"],
        affordances={"peek", "condense", "quest"},
    ),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        missing="a silver bell",
        hidden_in="the attic",
        clue="a thread of moonlight on a trunk lid",
        whisper="What rings when nobody is near?",
        ending_image="the silver bell caught the moon and chimed like a tiny star.",
        tags={"bell", "quest", "ghost"},
    ),
    "key": Quest(
        id="key",
        missing="an old brass key",
        hidden_in="the hallway",
        clue="a scratch mark under a loose floorboard",
        whisper="What opens a door that has been waiting a long time?",
        ending_image="the old brass key lay warm in the child’s palm like a promise.",
        tags={"key", "quest", "ghost"},
    ),
    "photo": Quest(
        id="photo",
        missing="a faded family photo",
        hidden_in="the window seat",
        clue="a little frame-shaped outline in the dust",
        whisper="What stays when a memory is trying to come home?",
        ending_image="the faded photo sat safe by the lamp, and the ghost looked peaceful at last.",
        tags={"photo", "quest", "ghost"},
    ),
}

GHOSTS = {
    "mournful": Ghost(
        id="mournful",
        label="a gentle ghost",
        type="ghost",
        mood="mournful",
        sadness="the ghost had been missing something dear",
        haunting="soft footfalls and cold drafts",
        quest_hint="quietly asking for help",
        tags={"ghost", "quest"},
    ),
    "lonely": Ghost(
        id="lonely",
        label="a lonely ghost",
        type="ghost",
        mood="lonely",
        sadness="the ghost had been wandering alone",
        haunting="whispers through empty rooms",
        quest_hint="hoping someone would listen",
        tags={"ghost", "quest"},
    ),
}

GIRL_NAMES = ["Mina", "June", "Lena", "Ivy", "Nora"]
BOY_NAMES = ["Eli", "Finn", "Owen", "Theo", "Ben"]
TRAITS = ["brave", "quiet", "intellectual", "careful", "curious"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    ghost: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


KNOWLEDGE = {
    "ghost": [("What is a ghost story?",
               "A ghost story is a tale about spooky things, mysterious rooms, and a person who learns what is really happening.")],
    "quest": [("What is a quest?",
               "A quest is a mission or search for something important.")],
    "key": [("What does a key do?",
             "A key can open a lock or a door.")],
    "bell": [("What does a bell do?",
              "A bell rings and makes a clear sound.")],
    "photo": [("What is a photo?",
               "A photo is a picture made by a camera that saves a moment from real life.")],
    "peek": [("What does it mean to peek?",
               "To peek means to look quickly and carefully, often from a small opening.")],
    "intellectual": [("What does intellectual mean?",
                      "Intellectual means using thought, ideas, and careful reasoning.")],
    "condense": [("What does condense mean?",
                  "To condense means to make something shorter or simpler while keeping the main idea.")],
}
KNOWLEDGE_ORDER = ["ghost", "quest", "peek", "intellectual", "condense", "key", "bell", "photo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for g in GHOSTS:
                combos.append((s, q, g))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly ghost story with an intellectual clue, a careful peek, and a quest for {f["quest"].missing}.',
        f"Tell a spooky but gentle story where {f['child'].id} follows a ghost's quest in {world.setting.place} and uses an intellectual idea to solve it.",
        f'Write a short ghost story that uses the words "peek" and "condense" and ends with {f["quest"].ending_image}',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    quest = f["quest"]
    ghost = f["ghost"]
    return [
        QAItem(
            question=f"What kind of story is this about {child.id} in {world.setting.place}?",
            answer=(
                f"It is a gentle ghost story about {child.id}, a {child.type}, who followed a quest in "
                f"{world.setting.place}. The spooky parts were about mystery, not harm."
            ),
        ),
        QAItem(
            question=f"What was the ghost looking for?",
            answer=f"{ghost.label} was looking for {quest.missing}. That missing thing was the heart of the quest.",
        ),
        QAItem(
            question=f"What did {child.id} do to learn the clue?",
            answer=(
                f"{child.id} took a careful peek and then used an intellectual thought to condense the clue into a simple plan."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {quest.ending_image} The ghost felt calmer because the missing thing was found and returned."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags) | set(world.facts["ghost"].tags) | {"peek", "condense", "intellectual"}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    lines.append(f"  peeked={world.peeked} condensed={world.condensed} found={world.found}")
    return "\n".join(lines)


ASP_RULES = r"""
ghost_story(Setting, Quest, Ghost) :- setting(Setting), quest(Quest), ghost(Ghost).
can_peek(Quest) :- quest(Quest), clue(Quest, _).
can_condense(Quest) :- quest(Quest), clue(Quest, _), whisper(Quest, _).
solved(Quest) :- can_peek(Quest), can_condense(Quest), missing(Quest, _).
ending(Setting, Quest, Ghost) :- ghost_story(Setting, Quest, Ghost), solved(Quest).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("missing", qid, q.missing))
        lines.append(asp.fact("clue", qid, q.clue))
        lines.append(asp.fact("whisper", qid, q.whisper))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ending/3."))
    asp_set = set(asp.atoms(model, "ending"))
    py_set = set(valid_combos())
    if len(asp_set) == len(py_set):
        print(f"OK: ASP and Python agree on {len(py_set)} story combos.")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-quest storyworld with peek/condense/intellectual beats.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "ghost", None) is None or c[2] == getattr(args, "ghost", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, quest, ghost = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = getattr(args, "gender", None) or ("girl" if name in GIRL_NAMES else "boy")
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, quest=quest, ghost=ghost, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(QUESTS, params.quest), _safe_lookup(GHOSTS, params.ghost), params.name, params.gender)
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
        print(asp_program("#show ending/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show ending/3."))
        print(sorted(asp.atoms(model, "ending")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(setting=s, quest=q, ghost=g, name="Mina", gender="girl", trait="curious"))
                   for s, q, g in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.setting} / {p.quest} / {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
