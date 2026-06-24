#!/usr/bin/env python3
"""
A standalone storyworld script for a small rhyming tale of disillusion, brave speech,
and a surprise that changes the mood.

Seed imagination:
- A child expects a grand, shiny stage moment.
- The moment turns out small and a little disappointing.
- A brave choice to speak honestly opens a new surprise.
- The ending should feel warm, rhythmic, and child-facing.

The world model tracks:
- physical meters: how full, small, hidden, bright, or set-up things are
- emotional memes: hope, disillusion, bravery, surprise, relief, delight

The story engine builds a tiny classical arc:
setup -> letdown -> brave dialogue -> surprise -> resolution
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    traits: list = field(default_factory=list)
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
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
class Setting:
    place: str = "the little stage"
    indoors: bool = True
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
class Object:
    id: str
    label: str
    phrase: str
    type: str
    hidden: bool = False
    surprising: bool = False
    useful: bool = False
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
class Promise:
    """What the child expected would happen."""
    label: str
    meter_key: str
    meme_key: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.objects: dict[str, Object] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_object(self, o: Object) -> Object:
        self.objects[o.id] = o
        return o

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
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "stage": Setting(place="the little stage", indoors=True, affords={"speak", "sing"}),
    "kitchen": Setting(place="the warm kitchen", indoors=True, affords={"speak"}),
    "garden": Setting(place="the garden bench", indoors=False, affords={"speak", "whisper"}),
}

ACTIONS = {
    "speak": {
        "verb": "speak up",
        "noun": "speech",
        "sound": "said",
        "rhythm": "soft and bright",
        "tags": {"speak", "dialogue"},
    },
    "whisper": {
        "verb": "whisper the truth",
        "noun": "whisper",
        "sound": "whispered",
        "rhythm": "small and sweet",
        "tags": {"speak", "dialogue"},
    },
}

PROMISES = {
    "spotlight": Promise(label="spotlight", meter_key="bright", meme_key="hope"),
    "surprise_card": Promise(label="surprise card", meter_key="hidden", meme_key="surprise"),
    "applause": Promise(label="applause", meter_key="full", meme_key="joy"),
}

OBJECTS = {
    "card": Object(
        id="card",
        label="card",
        phrase="a folded card with a ribbon",
        type="card",
        hidden=True,
        surprising=True,
        useful=True,
    ),
    "bell": Object(
        id="bell",
        label="bell",
        phrase="a tiny bell with a silver shine",
        type="bell",
        hidden=False,
        surprising=False,
        useful=True,
    ),
}

NAMES = ["Mina", "Toby", "Nell", "Pip", "Aria", "Jude", "Ivy", "Owen"]
TRAITS = ["brave", "gentle", "curious", "tiny", "careful", "dreamy"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    action: str
    promise: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            for promise in PROMISES:
                combos.append((place, action, promise))
    return combos


def explain_rejection(place: str, action: str, promise: str) -> str:
    return f"(No story: {action} does not fit a small rhyming scene at {place} with {promise}.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

class StoryWorld(World):
    pass


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} ... {b}"


def _raise_emotion(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _raise_meter(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _event_disillusion(world: StoryWorld, child: Entity, promise: Promise, obj: Object) -> None:
    _raise_emotion(child, "hope", 1.0)
    _raise_emotion(child, "disillusion", 1.0)
    _raise_meter(child, "still", 1.0)
    world.say(
        f"{child.id} came to the {world.setting.place} with a happy grin, "
        f"expecting {promise.label} to shine."
    )
    world.say(
        f"But the scene felt small, not grand; the bright idea did not quite land."
    )
    if obj.hidden:
        _raise_meter(child, "searching", 1.0)
        world.say(
            f"{child.id} looked around and found a hush, as if the air had lost its rush."
        )


def _event_brave_speak(world: StoryWorld, child: Entity, grownup: Entity, action: str) -> None:
    _raise_emotion(child, "bravery", 1.0)
    _raise_emotion(child, "truth", 1.0)
    world.say(
        f"{child.id} took a breath and chose to speak, with a steady voice, not meek."
    )
    world.say(
        f'"{child.id} said, "This is not what I thought it would be."'
    )
    world.say(
        f"{grownup.id} listened close and did not scold; the honest words were brave and bold."
    )


def _event_surprise(world: StoryWorld, child: Entity, grownup: Entity, obj: Object) -> None:
    _raise_emotion(child, "surprise", 1.0)
    _raise_emotion(child, "relief", 1.0)
    _raise_emotion(child, "joy", 1.0)
    if obj.id not in world.objects:
        return
    world.say(
        f"Then came a surprise, with sparkle-size eyes: {obj.phrase} tucked inside."
    )
    world.say(
        f"{grownup.id} smiled and said, " 
        f'"We hid this treat for a later beat."'
    )


def _event_resolution(world: StoryWorld, child: Entity, obj: Object) -> None:
    _raise_emotion(child, "delight", 1.0)
    _raise_meter(child, "bright", 1.0)
    world.say(
        f"{child.id} laughed and felt quite light; the day turned sweet and warm and bright."
    )
    world.say(
        f"The letdown faded, the worry passed, and a good new ending came at last."
    )
    world.say(
        f"{child.id} held the {obj.label}, spoke a thank-you rhyme, and smiled in time."
    )


def tell(setting: Setting, action: str, promise: Promise, name: str, gender: str, trait: str) -> StoryWorld:
    world = StoryWorld(setting)
    child = world.add_entity(Entity(id=name, kind="character", type=gender, traits=[trait] if hasattr(Entity, "traits") else []))
    child.kind = "character"
    child.type = gender
    child.meters = {"still": 0.0, "searching": 0.0, "bright": 0.0}
    child.memes = {"hope": 0.0, "disillusion": 0.0, "bravery": 0.0, "surprise": 0.0, "relief": 0.0, "joy": 0.0, "truth": 0.0, "delight": 0.0}
    helper = world.add_entity(Entity(id="Guide", kind="character", type="adult"))
    helper.meters = {"bright": 0.0}
    helper.memes = {"calm": 0.0, "kindness": 0.0}
    obj = world.add_object(OBJECTS["card"])

    world.say(
        f"{child.id} was a {trait} little {gender} who loved a rhyme at play."
    )
    world.say(
        f"{child.id} went to {world.setting.place} hoping for {promise.label} that day."
    )
    world.para()
    _event_disillusion(world, child, promise, obj)
    world.para()
    _event_brave_speak(world, child, helper, action)
    world.para()
    _event_surprise(world, child, helper, obj)
    world.para()
    _event_resolution(world, child, obj)

    world.facts.update(
        child=child,
        helper=helper,
        obj=obj,
        promise=promise,
        action=action,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    promise = _safe_fact(world, f, "promise")
    return [
        f'Write a short rhyming story for a child named {child.id} with disillusion, speak, bravery, surprise, and dialogue.',
        f"Tell a gentle rhyming tale where {child.id} expects {promise.label}, feels let down, then speaks bravely and finds a surprise.",
        f"Write a tiny story with dialogue and a happy rhyme ending about honest speech and an unexpected gift.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    obj = _safe_fact(world, f, "obj")
    promise = _safe_fact(world, f, "promise")
    setting = _safe_fact(world, f, "setting")
    action = _safe_fact(world, f, "action")

    return [
        QAItem(
            question=f"What did {child.id} hope to find at {setting.place}?",
            answer=f"{child.id} hoped to find {promise.label}, but the first moment felt smaller than expected.",
        ),
        QAItem(
            question=f"Why did {child.id} feel disillusioned?",
            answer=f"{child.id} felt disillusioned because the scene was not as grand as {child.id} had imagined.",
        ),
        QAItem(
            question=f"What brave thing did {child.id} do next?",
            answer=f"{child.id} chose to speak up honestly instead of keeping the feeling inside.",
        ),
        QAItem(
            question=f"What surprise changed the mood in the end?",
            answer=f"A hidden {obj.label} appeared as a surprise, and that made the ending warm and happy.",
        ),
        QAItem(
            question=f"Who listened when {child.id} spoke?",
            answer=f"{helper.id} listened kindly and helped turn the disappointment into a good new moment.",
        ),
        QAItem(
            question=f"How did the story end after the dialogue?",
            answer=f"It ended with relief, delight, and a bright smile after the honest dialogue.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel nervous, because it is the right thing to do.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect to happen, so it makes you stop and look with fresh eyes.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is a conversation between people, where they take turns speaking and listening.",
        ),
        QAItem(
            question="What does it mean to speak up?",
            answer="To speak up means to say what you really think or feel in a clear voice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    for o in world.objects.values():
        lines.append(f"{o.id}: hidden={o.hidden} surprising={o.surprising} useful={o.useful}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(stage).
place(kitchen).
place(garden).

action(speak).
action(whisper).

promise(spotlight).
promise(surprise_card).
promise(applause).

affords(stage,speak).
affords(stage,sing).
affords(kitchen,speak).
affords(garden,speak).
affords(garden,whisper).

% A story is valid when the setting affords the action and the promise exists.
valid(P,A,R) :- place(P), action(A), promise(R), affords(P,A).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for action in ACTIONS:
        lines.append(asp.fact("action", action))
    for promise in PROMISES:
        lines.append(asp.fact("promise", promise))
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            lines.append(asp.fact("affords", place, act))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about disillusion, brave speech, surprise, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--promise", choices=PROMISES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for promise in PROMISES:
                out.append((place, act, promise))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "promise", None) is None or c[2] == getattr(args, "promise", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, promise = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, promise=promise, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), params.action, _safe_lookup(PROMISES, params.promise), params.name, params.gender, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = valid_asp_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, action, promise in valid_combos():
            params = StoryParams(
                place=place,
                action=action,
                promise=promise,
                name=_safe_lookup(NAMES, (len(samples)) % len(NAMES)),
                gender=["girl", "boy"][len(samples) % 2],
                trait=_safe_lookup(TRAITS, len(samples) % len(TRAITS)),
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
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
