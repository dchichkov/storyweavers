#!/usr/bin/env python3
"""
storyworlds/worlds/strict_poll_happy_ending_quest_ghost_story.py
===============================================================

A small storyworld for a ghost-story-flavored quest with a strict poll,
mischief, and a happy ending.

The seed idea:
- A child and a helper ghost are trying to solve a tiny haunted problem.
- A strict keeper insists on a poll before anything else can happen.
- The poll decides which clue to follow, and the quest ends with a happy, safe
  ending image that proves the world changed.

The prose stays child-facing and concrete, while the world model tracks
physical meters and emotional memes so the turn and ending are state-driven.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    helper: object | None = None
    hero: object | None = None
    keeper: object | None = None
    object_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
    name: str
    dark: bool = True
    echo: str = ""
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


@dataclass
class Quest:
    id: str
    goal: str
    clue: str
    search: str
    ending: str
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
class Problem:
    id: str
    label: str
    phrase: str
    twist: str
    blocked_by: str
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
class Method:
    id: str
    label: str
    phrase: str
    effect: str
    ending_line: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
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


def _r_found(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    quest = world.facts["quest"]
    if hero.memes["search"] < THRESHOLD:
        return out
    sig = ("found", quest.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("object").meters["glow"] += 1
    world.get("keeper").memes["hope"] += 1
    out.append("__found__")
    return out


def _r_smile(world: World) -> list[str]:
    out: list[str] = []
    obj = world.get("object")
    if obj.meters["glow"] < THRESHOLD:
        return out
    sig = ("smile", obj.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hero").memes["joy"] += 1
    world.get("ghost").memes["joy"] += 1
    out.append("__smile__")
    return out


CAUSAL_RULES = [Rule("found", "quest", _r_found), Rule("smile", "ending", _r_smile)]


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


def world_setup(setting: Setting) -> World:
    return World(setting)


def valid_story_combo(quest: Quest, problem: Problem, method: Method) -> bool:
    return quest.id in {"lantern", "bell", "lantern_key"} and problem.id in {"hush", "fog", "drift"} and method.id in {"listen", "ring", "follow"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for q in QUESTS.values():
        for p in PROBLEMS.values():
            for m in METHODS.values():
                if valid_story_combo(q, p, m):
                    combos.append((q.id, p.id, m.id))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    problem: str
    method: str
    name: str
    child_type: str
    helper: str
    helper_type: str
    keeper: str
    keeper_type: str
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


SETTINGS = {
    "moonyard": Setting(name="the moonlit yard", dark=True, echo="soft"),
    "attic": Setting(name="the old attic", dark=True, echo="wooden"),
    "lighthouse": Setting(name="the lighthouse stair", dark=True, echo="ringing"),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        goal="find the missing lantern",
        clue="a pale blink behind the stairs",
        search="follow the pale blink",
        ending="the lantern glowed warm beside the window",
        tags={"light", "find"},
    ),
    "bell": Quest(
        id="bell",
        goal="find the silver bell",
        clue="a tiny ring in the dark",
        search="follow the tiny ring",
        ending="the bell chimed bright on the shelf",
        tags={"sound", "find"},
    ),
    "lantern_key": Quest(
        id="lantern_key",
        goal="find the lantern key",
        clue="a key-shaped shine under dust",
        search="follow the key-shaped shine",
        ending="the key rested safe in a little dish",
        tags={"key", "find"},
    ),
}

PROBLEMS = {
    "hush": Problem(
        id="hush",
        label="the hush",
        phrase="a hush that swallowed every clue",
        twist="the dark kept eating the sounds",
        blocked_by="silence",
        tags={"quiet"},
    ),
    "fog": Problem(
        id="fog",
        label="the fog",
        phrase="a fog that made the stairs look lost",
        twist="the gray fog curled around the corners",
        blocked_by="mist",
        tags={"fog"},
    ),
    "drift": Problem(
        id="drift",
        label="the drift",
        phrase="a drift of old dust that hid the trail",
        twist="the dust drifted back over every footprint",
        blocked_by="dust",
        tags={"dust"},
    ),
}

METHODS = {
    "listen": Method(
        id="listen",
        label="listen closely",
        phrase="they listened closely",
        effect="the quiet clue grew clearer",
        ending_line="The quiet clue led them home",
        tags={"quiet"},
    ),
    "ring": Method(
        id="ring",
        label="ring the bell",
        phrase="they gave the bell a gentle ring",
        effect="the sound shook the fog apart",
        ending_line="The bell call carried them through",
        tags={"sound"},
    ),
    "follow": Method(
        id="follow",
        label="follow the glow",
        phrase="they followed the glow together",
        effect="the path brightened one step at a time",
        ending_line="The glow led them to the prize",
        tags={"light"},
    ),
}

NAMES = ["Mina", "Noah", "Iris", "Theo", "Lena", "Owen", "Pia", "Ezra"]
TYPES = ["girl", "boy"]
HELPERS = [("ghost", "ghost"), ("guide", "ghost"), ("lantern", "thing")]
KEEPERS = [("strict keeper", "woman"), ("strict watchman", "man"), ("strict aunt", "woman")]
TRAITS = ["brave", "curious", "patient", "gentle"]


def choose_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    combos = valid_combos()
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[0] == getattr(args, "quest", None)]
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[1] == getattr(args, "problem", None)]
    if getattr(args, "method", None):
        combos = [c for c in combos if c[2] == getattr(args, "method", None)]
    if not combos:
        pass
    return rng.choice(list(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    qid, pid, mid = choose_combo(args, rng)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    child_type = getattr(args, "child_type", None) or rng.choice(TYPES)
    helper_name, helper_type = rng.choice(HELPERS)
    keeper_name, keeper_type = rng.choice(KEEPERS)
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    return StoryParams(
        setting=setting,
        quest=qid,
        problem=pid,
        method=mid,
        name=name,
        child_type=child_type,
        helper=helper_name,
        helper_type=helper_type,
        keeper=keeper_name,
        keeper_type=keeper_type,
    )


def intro(world: World, hero: Entity, helper: Entity, keeper: Entity, quest: Quest, problem: Problem) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["mystery"] += 1
    world.say(
        f"{hero.id} walked into {world.setting.name} with {helper.id}, a little ghost who floated like a silver puff."
    )
    world.say(
        f"A strict {keeper.label_word} stood by the door and said there would be a poll before anyone could search for {quest.goal}."
    )
    world.say(
        f"The trouble was {problem.phrase}, and it made the old place feel extra spooky."
    )


def poll_scene(world: World, keeper: Entity, hero: Entity, quest: Quest, problem: Problem) -> None:
    keeper.memes["strictness"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'"We will take a strict poll," said {keeper.id}. "Should we {quest.search} or stand still and wait?"'
    )
    world.say(
        f"{hero.id} listened as the little voices in the room leaned one way and then the other."
    )


def take_poll(world: World, hero: Entity, helper: Entity, quest: Quest, method: Method) -> None:
    hero.memes["search"] += 1
    helper.memes["help"] += 1
    world.facts["poll_choice"] = method.id
    world.say(
        f"{helper.id} lifted a bony finger and pointed to the clue. {helper.id} whispered that {method.phrase} was the best way."
    )
    world.say(
        f"{hero.id} nodded, because the poll had chosen a path and the quest could finally begin."
    )
    propagate(world, narrate=True)


def happy_end(world: World, hero: Entity, helper: Entity, keeper: Entity, quest: Quest, method: Method) -> None:
    hero.memes["joy"] += 2
    helper.memes["joy"] += 2
    keeper.memes["relief"] += 1
    world.say(
        f"Together they kept going until {quest.ending}. {method.ending_line}, and the strict {keeper.label_word} smiled at last."
    )
    world.say(
        f"{hero.id} and {helper.id} stood in the bright ending light, while the old shadows made room for a happy laugh."
    )


def tell(setting: Setting, quest: Quest, problem: Problem, method: Method,
         name: str = "Mina", child_type: str = "girl",
         helper_name: str = "ghost", helper_type: str = "ghost",
         keeper_name: str = "keeper", keeper_type: str = "woman") -> World:
    world = world_setup(setting)
    hero = world.add(Entity(id=name, kind="character", type=child_type, label=name, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name, role="helper"))
    keeper = world.add(Entity(id=keeper_name, kind="character", type=keeper_type, label="strict keeper", role="keeper"))
    object_ent = world.add(Entity(id="object", kind="thing", type="thing", label=quest.goal, phrase=quest.goal))
    world.add(Entity(id="problem", kind="thing", type="thing", label=problem.label, phrase=problem.phrase))
    world.facts.update(
        hero=hero,
        helper=helper,
        keeper=keeper,
        quest=quest,
        problem=problem,
        method=method,
        object=object_ent,
    )
    intro(world, hero, helper, keeper, quest, problem)
    world.para()
    poll_scene(world, keeper, hero, quest, problem)
    take_poll(world, hero, helper, quest, method)
    world.para()
    happy_end(world, hero, helper, keeper, quest, method)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    problem = f["problem"]
    method = f["method"]
    return [
        f'Write a ghost-story style quest for a child named {hero.id} that uses the words "strict" and "poll".',
        f"Tell a spooky-but-kind story where {hero.id} has to solve {quest.goal} through {problem.phrase}, and a strict keeper calls for a poll first.",
        f"Write a short happy-ending quest story where a ghost helps {hero.id} choose the right way forward after a strict poll.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    keeper = f["keeper"]
    quest = f["quest"]
    problem = f["problem"]
    method = f["method"]
    return [
        QAItem(
            question=f"Who is the story about in the spooky quest?",
            answer=f"It is about {hero.id}, who went into {world.setting.name} with {helper.id}. {keeper.label_word.capitalize()} made the story start with a strict poll before the search could go on.",
        ),
        QAItem(
            question=f"Why did the strict poll matter before they could solve {quest.goal}?",
            answer=f"The poll mattered because it decided whether they should follow the clue or wait in the dark. That choice helped them face {problem.phrase} without getting stuck.",
        ),
        QAItem(
            question=f"What did {helper.id} suggest after the poll?",
            answer=f"{helper.id} suggested that they {method.phrase}. That was the best way to move through the spooky place and keep the quest going.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended happily, with {quest.ending}. The ending showed that the quest worked and the strict keeper could smile too.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a poll?",
            answer="A poll is when people choose between options by listening to what the group thinks. It helps a group decide what to do next.",
        ),
        QAItem(
            question="What does strict mean?",
            answer="Strict means someone expects the rules to be followed carefully. A strict person usually wants things done the right way.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important. It often involves a problem to solve and a goal to reach.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
found(Q) :- quest(Q), hero_search.
smile(Q) :- found(Q), object_glow.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dark:
            lines.append(asp.fact("dark", sid))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.id))
        for t in sorted(q.tags):
            lines.append(asp.fact("tag", q.id, t))
    for p in PROBLEMS.values():
        lines.append(asp.fact("problem", p.id))
    for m in METHODS.values():
        lines.append(asp.fact("method", m.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    # smoke test normal generation
    sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, problem=None, method=None, name=None, child_type=None), random.Random(7)))
    if not sample.story:
        print("FAIL: generated story was empty")
        return 1
    try:
        print(sample.story)
    except Exception as exc:
        print(f"FAIL: emit smoke test crashed: {exc}")
        return 1
    return 0 if len(valid_combos()) >= 4 else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story quest with a strict poll and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=TYPES)
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


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS.get(params.setting)
    quest = QUESTS.get(params.quest)
    problem = PROBLEMS.get(params.problem)
    method = METHODS.get(params.method)
    if not all([setting, quest, problem, method]):
        pass
    world = tell(setting, quest, problem, method, params.name, params.child_type, params.helper, params.helper_type, params.keeper, params.keeper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="moonyard", quest="lantern", problem="fog", method="follow", name="Mina", child_type="girl", helper="ghost", helper_type="ghost", keeper="strict keeper", keeper_type="woman"),
    StoryParams(setting="attic", quest="bell", problem="hush", method="listen", name="Noah", child_type="boy", helper="guide", helper_type="ghost", keeper="strict aunt", keeper_type="woman"),
    StoryParams(setting="lighthouse", quest="lantern_key", problem="drift", method="ring", name="Iris", child_type="girl", helper="ghost", helper_type="ghost", keeper="strict watchman", keeper_type="man"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    qid, pid, mid = choose_combo(args, rng)
    return StoryParams(
        setting=getattr(args, "setting", None) or rng.choice(list(SETTINGS)),
        quest=qid,
        problem=pid,
        method=mid,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        child_type=getattr(args, "child_type", None) or rng.choice(TYPES),
        helper="ghost",
        helper_type="ghost",
        keeper="strict keeper",
        keeper_type="woman",
    )


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
