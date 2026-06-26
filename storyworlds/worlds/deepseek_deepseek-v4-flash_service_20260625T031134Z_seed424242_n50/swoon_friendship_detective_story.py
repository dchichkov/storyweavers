#!/usr/bin/env python3
"""
storyworlds/worlds/swoon_friendship_detective_story.py
======================================================

A standalone story world sketch about a little detective who solves friendship
mysteries with gentle, emotional clues.  The domain models a friendship detective
who notices when a friend feels left out or sad (the "swoon" of loneliness) and
works to understand the cause and restore the friendship.

Initial story (used to build a world model):
---
Once upon a time, there was a little girl named Maya who loved being a detective.
She wore a little hat and carried a notebook to write down clues about feelings.
Her best friend was a boy named Leo. They played together every day in the sunny park.

But one day, Leo looked sad. He sat on the bench alone while other children played.
Maya noticed the swoon in his eyes - the heavy sigh and the droopy shoulders.
She sat beside him and asked, "What is wrong, my friend?"

Leo said, "I thought you forgot about me. You played with the new girl, Emma,
and I felt invisible." Maya's heart felt tight. She hugged Leo and said,
"I am sorry, Leo. You are my best friend, and I will never forget you again."

They walked to the swings together, and the swoon left Leo's face.
Friendship was like a puzzle, Maya thought, and every clue needed a kind answer.
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

# Make the shared result containers importable when this script is run directly
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Swoon is the emotional meter that tracks loneliness / feeling left out.
SWOON_KINDS = {"lonely", "forgotten", "invisible", "ignored"}


# ---------------------------------------------------------------------------
# Entities: characters and objects share one representation.
# ---------------------------------------------------------------------------

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
            keys = [upper, upper + "S", upper + "ES"]
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
    kind: str = "character"            # "character" | "thing"
    type: str = "person"               # girl, boy, detective
    label: str = ""                    # short reference, e.g. "detective hat"
    phrase: str = ""                   # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    detective_ent: object | None = None
    friend_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "Maya", "Emma"}
        male = {"boy", "father", "dad", "man", "Leo"}
        if self.type in female or self.id in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male or self.id in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
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
    place: str = "the park"
    indoor: bool = False
    details: str = "The sun was warm and the trees swayed gently."
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
class ClueType:
    """A kind of clue the detective notices about a friend's feelings."""
    id: str
    symptom: str         # what the detective sees: "a heavy sigh"
    swoon_label: str     # the emotion keyword: "lonely", "forgotten", "invisible"
    body: str            # body description: "droopy shoulders and sad eyes"
    question: str        # what the detective asks: "What is on your mind?"
    resolution: str      # how it gets better: "walked together to the swings"
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
class Friend:
    """A friend character with a name and personality."""
    name: str
    type: str
    trait: str
    activity: str        # what they love: "playing on the swings", "building sandcastles"
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
class Detective:
    """The detective character."""
    name: str
    type: str
    trait: str
    accessory: str       # hat, magnifying glass, notebook


# ---------------------------------------------------------------------------
# World: entity store + narration history.
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
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


def _r_swoon_spread(world: World) -> list[str]:
    """When a friend has a high swoon meter, the detective notices it."""
    out: list[str] = []
    for entity in world.characters():
        swoon_total = sum(entity.memes.get(k, 0) for k in SWOON_KINDS)
        if swoon_total < THRESHOLD:
            continue
        sig = ("noticed_swoon", entity.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The swoon was visible on {entity.id}'s face.")
    return out


def _r_detective_curiosity(world: World) -> list[str]:
    """Detective becomes curious when a swoon is noticed."""
    for entity in world.characters():
        if "detective" not in entity.traits:
            continue
        for other in world.characters():
            if other.id == entity.id:
                continue
            swoon_total = sum(other.memes.get(k, 0) for k in SWOON_KINDS)
            if swoon_total < THRESHOLD:
                continue
            sig = ("curious", entity.id, other.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            entity.memes["curiosity"] += 1
            return ["__curious__"]
    return []


def _r_friendship_heal(world: World) -> list[str]:
    """When the detective apologizes and the friend accepts, the swoon fades."""
    for entity in world.characters():
        if entity.memes.get("healed", 0) >= THRESHOLD:
            for k in SWOON_KINDS:
                entity.memes[k] = max(0, entity.memes[k] - 2)
            sig = ("healed_resolved", entity.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            return ["__healed__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="swoon_spread", tag="emotional", apply=_r_swoon_spread),
    Rule(name="detective_curiosity", tag="social", apply=_r_detective_curiosity),
    Rule(name="friendship_heal", tag="social", apply=_r_friendship_heal),
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
                produced.extend(s for s in sents if not s.startswith("__") or s == "__healed__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Prediction: run forward to see if a clue would actually cause a swoon.
# ---------------------------------------------------------------------------
def predict_swoon(world: World, friend: Entity, clue: ClueType) -> dict:
    sim = world.copy()
    _apply_clue(sim, sim.get(friend.id), clue, narrate=False)
    sq = {k: v for k, v in sim.get(friend.id).memes.items() if k in SWOON_KINDS}
    return {"swoon_level": sum(sq.values()) >= THRESHOLD, "swoon_kind": clue.swoon_label}


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, detective: Entity, friend: Entity) -> None:
    world.say(
        f"Once upon a time, there was a little {detective.type} named {detective.id}. "
        f"{detective.pronoun('possessive').capitalize()} best friend was {friend.id}."
    )
    world.say(
        f"They played together every day in {world.setting.place}. "
        f"{world.setting.details}"
    )


def detective_gear(world: World, detective: Entity) -> None:
    world.say(
        f"{detective.id} wore a little {detective.accessory} and always watched "
        f"for clues about how people felt."
    )


def friendship_activity(world: World, detective: Entity, friend: Entity) -> None:
    world.say(
        f"{detective.id} and {friend.id} loved {friend.activity} together."
    )


def swoon_appears(world: World, friend: Entity, clue: ClueType) -> None:
    friend.memes[clue.swoon_label] += 1
    world.say(
        f"But one day, {friend.id} looked sad. "
        f"{friend.pronoun('possessive').capitalize()} {clue.body} told "
        f"{detective_name(world)} something was wrong."
    )
    world.say(
        f"{detective_name(world)} noticed the swoon - the {clue.symptom} "
        f"and the way {friend.id} sat alone."
    )


def detective_name(world: World) -> str:
    for e in world.characters():
        if "detective" in e.traits:
            return e.id
    return "the detective"


def friend_name(world: World) -> str:
    for e in world.characters():
        if "detective" not in e.traits:
            return e.id
    return "the friend"


def approach(world: World, detective: Entity, friend: Entity, clue: ClueType) -> None:
    world.say(
        f"{detective.id} sat beside {friend.id} and asked, "
        f'"{clue.question}"'
    )


def confession(world: World, friend: Entity, detective: Entity, clue: ClueType) -> None:
    world.say(
        f'{friend.id} sighed. "I thought you forgot about me. '
        f'You played with someone else and I felt {clue.swoon_label}."'
    )


def apology(world: World, detective: Entity, friend: Entity) -> None:
    detective.memes["care"] += 1
    friend.memes["healed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{detective.id}'s heart felt tight. {detective.pronoun('possessive').capitalize()} "
        f"hugged {friend.id} and said, "
        f'"I am sorry, {friend.id}. You are my best friend, and I will never forget you again."'
    )


def resolution(world: World, detective: Entity, friend: Entity, clue: ClueType) -> None:
    world.say(
        f"They {clue.resolution} together, and the swoon left {friend.id}'s face."
    )
    world.say(
        f"Friendship was like a puzzle, {detective.id} thought, "
        f"and every clue needed a kind answer."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, clue: ClueType,
         det_name: str = "Maya", det_type: str = "girl",
         det_trait: str = "curious",
         det_accessory: str = "detective hat",
         friend_name_str: str = "Leo", friend_type: str = "boy",
         friend_trait: str = "kind",
         friend_activity: str = "playing on the swings") -> World:
    world = World(setting)

    detective_ent = world.add(Entity(
        id=det_name, kind="character", type=det_type,
        traits=["detective", det_trait],
    ))
    friend_ent = world.add(Entity(
        id=friend_name_str, kind="character", type=friend_type,
        traits=[friend_trait],
    ))

    # Act 1
    introduce(world, detective_ent, friend_ent)
    detective_gear(world, detective_ent)
    friendship_activity(world, detective_ent, friend_ent)

    # Act 2
    world.para()
    swoon_appears(world, friend_ent, clue)
    approach(world, detective_ent, friend_ent, clue)
    confession(world, friend_ent, detective_ent, clue)

    # Act 3
    world.para()
    apology(world, detective_ent, friend_ent)
    resolution(world, detective_ent, friend_ent, clue)

    world.facts.update(
        detective=detective_ent,
        friend=friend_ent,
        clue=clue,
        setting=setting,
        swoon_kind=clue.swoon_label,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "park": Setting(place="the park", details="The sun was warm and the trees swayed gently."),
    "playground": Setting(place="the playground", details="Children laughed and ran around the slides."),
    "garden": Setting(place="the garden", details="Colorful flowers bloomed and bees buzzed softly."),
    "beach": Setting(place="the beach", details="Waves lapped the shore and seagulls called overhead."),
    "schoolyard": Setting(place="the schoolyard", details="The bell would ring soon, but there was still time to play."),
}

CLUE_TYPES = [
    ClueType(id="lonely",
             symptom="heavy sigh",
             swoon_label="lonely",
             body="droopy shoulders and sad eyes",
             question="What is on your mind, my friend?",
             resolution="walked to the swings together"),
    ClueType(id="forgotten",
             symptom="quiet tear",
             swoon_label="forgotten",
             body="tight lips and a trembling chin",
             question="Are you feeling left out today?",
             resolution="sat under the big tree and shared a snack"),
    ClueType(id="invisible",
             symptom="small voice",
             swoon_label="invisible",
             body="turned back and a very quiet sigh",
             question="Did I make you feel like you disappeared?",
             resolution="played their favorite game together"),
    ClueType(id="ignored",
             symptom="long silence",
             swoon_label="ignored",
             body="folded arms and a downward gaze",
             question="What is in your heart, dear friend?",
             resolution="drew pictures together on the sidewalk"),
]

DETECTIVE_NAMES = ["Maya", "Finn", "Lily", "Theo", "Ava", "Sam"]
DETECTIVE_TYPES = ["girl", "boy"]
DETECTIVE_TRAITS = ["curious", "observant", "kind-hearted", "thoughtful"]
DETECTIVE_ACCESSORIES = ["detective hat", "magnifying glass", "notebook"]

FRIEND_NAMES_GIRL = ["Lucy", "Emma", "Zoe", "Ruby", "Ivy"]
FRIEND_NAMES_BOY = ["Leo", "Max", "Noah", "Eli", "Jack"]
FRIEND_TRAITS = ["kind", "loyal", "playful", "gentle", "brave"]
FRIEND_ACTIVITIES = [
    "playing on the swings",
    "building sandcastles",
    "climbing the slide",
    "chasing butterflies",
    "reading picture books",
]


def valid_combos() -> list[tuple[str, str]]:
    """(setting, clue_id) pairs that always work."""
    combos = []
    for place in SETTINGS:
        for clue in CLUE_TYPES:
            combos.append((place, clue.id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    detective_name: str
    detective_type: str
    detective_trait: str
    detective_accessory: str
    friend_name: str
    friend_type: str
    friend_trait: str
    friend_activity: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "friendship": [
        ("What is a good friend?",
         "A good friend is someone who listens, shares, and plays with you. "
         "They say sorry if they make a mistake and always want you to feel happy."),
    ],
    "swoon": [
        ("What does the word 'swoon' mean in this story?",
         "In this story, swoon means the sad, heavy feeling when someone feels "
         "lonely or forgotten. It is like a cloud over the heart."),
    ],
    "detective": [
        ("What does a friendship detective do?",
         "A friendship detective watches for clues about feelings. "
         "They notice when a friend is sad and ask kind questions to help."),
    ],
    "apology": [
        ("Why is saying sorry important in a friendship?",
         "Saying sorry shows you care about your friend's feelings. "
         "It makes the sad swoon go away and brings you closer."),
    ],
}
KNOWLEDGE_ORDER = ["friendship", "swoon", "detective", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det, friend, clue = f["detective"], f["friend"], f["clue"]
    sub = det.pronoun("subject")
    pos = det.pronoun("possessive")
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "friendship and feelings" '
        f'that includes the word "swoon."',
        f"Tell a gentle story where a little detective named {det.id} notices "
        f"that {friend.id} feels {clue.swoon_label} and uses {pos} {det.accessory} "
        f"to solve the mystery of friendship.",
        f'Write a simple story about a friendship that gets mended with a '
        f'kind apology and a shared game.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det, friend, clue, setting = f["detective"], f["friend"], f["clue"], f["setting"]
    det_sub, det_obj, det_pos = (det.pronoun("subject"), det.pronoun("object"),
                                 det.pronoun("possessive"))
    friend_sub = friend.pronoun("subject")
    place = setting.place
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who are the two friends in the story at {place}?"
            ),
            answer=(
                f"The two friends are {det.id} the {det.type} detective and "
                f"{friend.id}. They play together at {place} every day."
            ),
        ),
        QAItem(
            question=(
                f"What did {det.id} notice about {friend.id} at {place}?"
            ),
            answer=(
                f"{det_id_name(det)} noticed that {friend.id} looked sad. "
                f"{friend_sub} had {clue.body} and a {clue.symptom}. "
                f"That was the swoon - the feeling of being {clue.swoon_label}."
            ),
        ),
        QAItem(
            question=(
                f"Why did {friend.id} feel sad at {place}?"
            ),
            answer=(
                f"{friend_sub} felt {clue.swoon_label} because "
                f"{det_pos} detective played with someone else and {friend_sub} "
                f"felt left out. {friend_sub} thought {det_id_name(det)} forgot about {friend_sub}."
            ),
        ),
        QAItem(
            question=(
                f"How did {det_id_name(det)} help make {friend.id}'s swoon go away?"
            ),
            answer=(
                f"{det_id_name(det)} sat beside {friend.id}, asked what was wrong, "
                f"and said sorry. Then they {clue.resolution} together, "
                f"and the swoon left {friend.id}'s face."
            ),
        ),
        QAItem(
            question=(
                f"What lesson did {det_id_name(det)} learn about friendship?"
            ),
            answer=(
                f"{det_id_name(det)} learned that friendship is like a puzzle. "
                f"Every clue - like a sigh or sad eyes - needs a kind answer. "
                f"Saying sorry and playing together mends the heart."
            ),
        ),
    ]
    return qa


def det_id_name(detector: Entity) -> str:
    return detector.id


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
        bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="park",
        clue="lonely",
        detective_name="Maya",
        detective_type="girl",
        detective_trait="curious",
        detective_accessory="detective hat",
        friend_name="Leo",
        friend_type="boy",
        friend_trait="kind",
        friend_activity="playing on the swings",
    ),
    StoryParams(
        place="playground",
        clue="forgotten",
        detective_name="Finn",
        detective_type="boy",
        detective_trait="observant",
        detective_accessory="magnifying glass",
        friend_name="Ruby",
        friend_type="girl",
        friend_trait="loyal",
        friend_activity="climbing the slide",
    ),
    StoryParams(
        place="garden",
        clue="invisible",
        detective_name="Lily",
        detective_type="girl",
        detective_trait="thoughtful",
        detective_accessory="notebook",
        friend_name="Noah",
        friend_type="boy",
        friend_trait="playful",
        friend_activity="chasing butterflies",
    ),
]


def explain_rejection(clue: ClueType) -> str:
    return f"(No story: this clue '{clue.id}' would not produce a compatible swoon.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Friendship detective domain: every clue always produces a valid story.
valid_story(Place, Clue, DetName, DetType, FriendName, FriendType) :-
    setting(Place), clue(Clue),
    detective_type(DetType), friend_type(FriendType),
    detective_name(DetName), friend_name(FriendName).

detective_type("girl"). detective_type("boy").
friend_type("girl"). friend_type("boy").
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for clue_id in CLUE_TYPES:
        lines.append(asp.fact("clue", clue_id.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/6."))
    if model:
        print("OK: clingo gate validates all combinations.")
        return 0
    print("ERROR: clingo found no valid stories.")
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a friendship detective, a swoon, a mended bond.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=[c.id for c in CLUE_TYPES])
    ap.add_argument("--detective-type", choices=DETECTIVE_TYPES)
    ap.add_argument("--friend-type", choices=["girl", "boy"])
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
    if getattr(args, "clue", None):
        clue_ids = [getattr(args, "clue", None)]
    else:
        clue_ids = [c.id for c in CLUE_TYPES]

    combos = [(p, cl) for p in SETTINGS for cl in clue_ids]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, clue_id = rng.choice(combos)
    clue_obj = next(c for c in CLUE_TYPES if c.id == clue_id)

    det_type = getattr(args, "detective_type", None) or rng.choice(DETECTIVE_TYPES)
    det_name = rng.choice(DETECTIVE_NAMES)
    det_trait = rng.choice(DETECTIVE_TRAITS)
    det_acc = rng.choice(DETECTIVE_ACCESSORIES)

    friend_type = getattr(args, "friend_type", None) or rng.choice(["girl", "boy"])
    if friend_type == "girl":
        friend_name = rng.choice(FRIEND_NAMES_GIRL)
    else:
        friend_name = rng.choice(FRIEND_NAMES_BOY)
    friend_trait = rng.choice(FRIEND_TRAITS)
    friend_act = rng.choice(FRIEND_ACTIVITIES)

    return StoryParams(
        place=place,
        clue=clue_id,
        detective_name=det_name,
        detective_type=det_type,
        detective_trait=det_trait,
        detective_accessory=det_acc,
        friend_name=friend_name,
        friend_type=friend_type,
        friend_trait=friend_trait,
        friend_activity=friend_act,
    )


def generate(params: StoryParams) -> StorySample:
    clue = next(c for c in CLUE_TYPES if c.id == params.clue)
    world = tell(
        _safe_lookup(SETTINGS, params.place), clue,
        params.detective_name, params.detective_type,
        params.detective_trait, params.detective_accessory,
        params.friend_name, params.friend_type,
        params.friend_trait, params.friend_activity,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/6."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("All settings and clue types produce compatible stories.")
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective_name} the detective & {p.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
