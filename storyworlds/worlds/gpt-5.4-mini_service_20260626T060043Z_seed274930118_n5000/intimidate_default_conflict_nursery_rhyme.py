#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a timid child, a bossy bully, and a
gentle default choice that breaks a conflict.

Seed premise:
- A little child is in a nursery-like room with toys and bedtime things.
- A louder character tries to intimidate the child into giving up a cherished
  toy or turn.
- The child's default response is to freeze or hand over the thing.
- A helper changes the default with a brave, simple rhyme: share, ring a bell,
  or call the grown-up, and the conflict resolves.

The story reads like a short nursery rhyme rather than an event log.
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
# Entities
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    move: object | None = None
    threat: object | None = None
    toy: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Params / registries
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
    label: str
    nursery: bool
    affordance: str
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
class Threat:
    label: str
    verb: str
    noun: str
    force: str
    topic: str
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
class DefaultMove:
    label: str
    response: str
    shift: str
    cue: str
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
class StoryParams:
    place: str
    threat: str
    move: str
    name: str
    gender: str
    helper: str
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


PLACES = {
    "nursery": Place(label="the nursery", nursery=True, affordance="bedtime play"),
    "playroom": Place(label="the playroom", nursery=False, affordance="toy play"),
    "corner": Place(label="the cozy corner", nursery=True, affordance="quiet play"),
}

THREATS = {
    "bully": Threat(label="the bully", verb="intimidate", noun="mean words", force="loud", topic="mean"),
    "cat": Threat(label="the hissing cat", verb="intimidate", noun="a puffed-up stare", force="sharp", topic="cat"),
    "shadow": Threat(label="the shadow", verb="intimidate", noun="a long stretch", force="sudden", topic="shadow"),
}

DEFAULT_MOVES = {
    "freeze": DefaultMove(label="freeze", response="stood still and stared at the floor", shift="took one small breath", cue="breathe"),
    "share": DefaultMove(label="share", response="offered the toy back", shift="held the toy out with both hands", cue="share"),
    "bell": DefaultMove(label="bell", response="rang the little bell", shift="called for a grown-up", cue="ring"),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "nurse": "nurse",
    "teacher": "teacher",
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Theo", "Max"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def introduce(world: World, child: Entity, helper: Entity, toy: Entity) -> None:
    world.say(
        f"In {world.place.label}, there was little {child.id}, bright-eyed and sweet, "
        f"who loved {toy.label} with tidy little feet."
    )
    world.say(
        f"{helper.label.capitalize()} kept watch nearby, warm and kind, "
        f"for nursery days should be gentle-minded."
    )


def threat_arrives(world: World, child: Entity, threat: Entity, toy: Entity, move: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    threat.meters["closeness"] = threat.meters.get("closeness", 0.0) + 1
    world.say(
        f"Then came {threat.label}, {threat.force} and grim, "
        f"and tried to {threat.pronoun('subject')} {threat.memes.get('verb', threat.id)}? "
    )
    world.say(
        f'"Give me that {toy.label}," said the threat, "or I will make a fuss and dim the room."'
    )


def default_choice(world: World, child: Entity, move: Entity) -> None:
    child.memes["default"] = child.memes.get("default", 0.0) + 1
    if move.id == "freeze":
        world.say(
            f"{child.id} did the default thing: {move.response}, as small as a crumb."
        )
    elif move.id == "share":
        world.say(
            f"{child.id} did the default thing: {move.response}, "
            f"though {child.pronoun('subject')} wanted to hide."
        )
    else:
        world.say(
            f"{child.id} did the default thing: {move.response}, and a tiny bell went ding."
        )


def helper_turn(world: World, child: Entity, helper: Entity, threat: Entity, toy: Entity, move: Entity) -> None:
    child.memes["bravery"] = child.memes.get("bravery", 0.0) + 1
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1
    world.say(
        f"But {helper.label} came near and spoke in rhyme, "
        f'"Small hearts can be brave in a nursery time."'
    )
    if move.id == "bell":
        world.say(
            f"{helper.label.capitalize()} said, " \
            f'"Ring the little bell, and do not yield; grown-up help is near the field."'
        )
    elif move.id == "share":
        world.say(
            f"{helper.label.capitalize()} said, "
            f'"Share the toy, but keep your voice; kindness makes a sturdy choice."'
        )
    else:
        world.say(
            f"{helper.label.capitalize()} said, "
            f'"Take one breath and lift your chin; the loudest mouth does not always win."'
        )


def resolve(world: World, child: Entity, helper: Entity, threat: Entity, toy: Entity, move: Entity) -> None:
    child.memes["conflict"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    threat.meters["closeness"] = 0.0
    if move.id == "bell":
        world.say(
            f"The bell rang clear, and the bully backed away; "
            f"{helper.label} came close, and the room felt safe all day."
        )
    elif move.id == "share":
        world.say(
            f"{child.id} shared the toy, and the bully's grin grew small; "
            f"there was no room for bossy words at all."
        )
    else:
        world.say(
            f"{child.id} took one breath, and the bully lost its spell; "
            f"the mean old words grew faint and fell."
        )
    world.say(
        f"At last {child.id} held {toy.it()} and smiled so wide, "
        f"with {helper.label} nearby and peace inside."
    )


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def compatible(place: Place, threat: Threat, move: DefaultMove) -> bool:
    if place.nursery and threat.topic in {"mean", "shadow"}:
        return True
    return move.id in {"bell", "share", "freeze"}


def explain_rejection(place: Place, threat: Threat, move: DefaultMove) -> str:
    return (
        f"(No story: in {place.label}, {move.label} does not plausibly answer "
        f"{threat.label}'s attempt to intimidate. Pick a gentler nursery conflict.)"
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    threat_cfg = _safe_lookup(THREATS, params.threat)
    move_cfg = _safe_lookup(DEFAULT_MOVES, params.move)

    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"small": 1.0},
        memes={"default": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"kind": 1.0},
    ))
    threat = world.add(Entity(
        id="threat",
        kind="character",
        type="thing",
        label=threat_cfg.label,
        meters={"loud": 1.0},
        memes={"verb": 1.0},
    ))
    toy = world.add(Entity(
        id="toy",
        kind="thing",
        type="toy",
        label="red wagon",
        phrase="a shiny red wagon",
        owner=child.id,
    ))
    move = world.add(Entity(
        id=move_cfg.label,
        kind="thing",
        type="move",
        label=move_cfg.label,
        phrase=move_cfg.response,
    ))

    world.facts.update(child=child, helper=helper, threat=threat, toy=toy, move=move, place=place)

    introduce(world, child, helper, toy)
    world.para()
    threat_arrives(world, child, threat, toy, move)
    default_choice(world, child, move)
    helper_turn(world, child, helper, threat, toy, move)
    resolve(world, child, helper, threat, toy, move)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    threat = _safe_fact(world, f, "threat")
    move = _safe_fact(world, f, "move")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short nursery-rhyme story about {child.id} in {place.label} when {threat.label} tries to intimidate them.',
        f"Tell a gentle rhyme where a small child does the default response, then a helper changes the ending.",
        f'Write a child-friendly story using the word "{threat.label}" and the idea of "{move.label}" as the default choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    threat = _safe_fact(world, f, "threat")
    toy = _safe_fact(world, f, "toy")
    move = _safe_fact(world, f, "move")
    return [
        QAItem(
            question=f"Who did {threat.label} try to intimidate in the nursery?",
            answer=f"{threat.label} tried to intimidate {child.id}, who loved the red wagon.",
        ),
        QAItem(
            question=f"What was {child.id}'s default response when the trouble started?",
            answer=f"{child.id}'s default response was to {move.label}, which meant {move.phrase if hasattr(move, 'phrase') else 'doing the usual small thing'}.",
        ),
        QAItem(
            question=f"How did {helper.label} help {child.id} after the conflict began?",
            answer=f"{helper.label} came with a rhyming reminder, and that changed the moment so {child.id} could keep {toy.label} and feel safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The conflict faded, the loud threatening words lost their power, and {child.id} ended the story smiling with {toy.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nursery?",
            answer="A nursery is a soft, child-friendly room or place for little ones to play, rest, and feel safe.",
        ),
        QAItem(
            question="What does it mean to intimidate someone?",
            answer="To intimidate someone is to scare them with loud, bossy, or mean behavior.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a moment when two sides want different things and the tension needs a calm solution.",
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
    parts = ["--- world trace ---"]
    for e in list(world.entities.values()):
        parts.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}"
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts:
% place(P). child(C). threat(T). move(M).
% nursery(P). intimidates(T). default_move(M).

compatible(P,T,M) :- nursery(P), intimidates(T), default_move(M).
compatible(P,T,M) :- place(P), threat(T), move(M), not impossible(P,T,M).

% This tiny world says a nursery-rhyme conflict is reasonable if the threat is
% an intimidation attempt and the default move can lead to a safer turn.
reasonable(P,T,M) :- compatible(P,T,M).

#show reasonable/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.nursery:
            lines.append(asp.fact("nursery", pid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        if t.verb == "intimidate":
            lines.append(asp.fact("intimidates", tid))
    for mid, m in DEFAULT_MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("default_move", mid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_reasonable() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "reasonable"))


def py_reasonable() -> set[tuple]:
    out = set()
    for pid, p in PLACES.items():
        for tid, t in THREATS.items():
            for mid, m in DEFAULT_MOVES.items():
                if compatible(p, t, m):
                    out.add((pid, tid, mid))
    return out


def asp_verify() -> int:
    a = asp_reasonable()
    b = py_reasonable()
    if a == b:
        print(f"OK: ASP matches Python reasonableness gate ({len(a)} triples).")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme conflict storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--move", choices=DEFAULT_MOVES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=list(HELPERS))
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
    threat = getattr(args, "threat", None) or rng.choice(list(THREATS))
    move = getattr(args, "move", None) or rng.choice(list(DEFAULT_MOVES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    p = _safe_lookup(PLACES, place)
    t = _safe_lookup(THREATS, threat)
    m = _safe_lookup(DEFAULT_MOVES, move)
    if not compatible(p, t, m):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, threat=threat, move=move, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="nursery", threat="bully", move="bell", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="corner", threat="shadow", move="freeze", name="Leo", gender="boy", helper="father"),
    StoryParams(place="playroom", threat="cat", move="share", name="Nora", gender="girl", helper="teacher"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = sorted(py_reasonable())
        print(f"{len(triples)} reasonable triples:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
