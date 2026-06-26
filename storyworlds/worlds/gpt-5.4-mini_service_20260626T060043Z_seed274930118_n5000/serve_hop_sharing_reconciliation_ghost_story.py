#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/serve_hop_sharing_reconciliation_ghost_story.py
=============================================================================================================

A small ghost-story world about a child, a spooky helper, sharing, and
reconciliation.

Premise:
- A child and a ghost meet in a quiet setting.
- They want to serve a warm treat and hop through a tiny nighttime game.
- One character worries about sharing the only lantern, the only blanket, or
  the only cookie tray.
- A small conflict grows until the characters make up and share.

The state model keeps track of:
- physical meters: lantern light, chill, crumbs, distance, etc.
- emotional memes: fear, loneliness, generosity, trust, relief.

The story should feel like a gentle ghost story: eerie but kind, with a clear
turn from misunderstanding to reconciliation.
"""

from __future__ import annotations

import argparse
import dataclasses
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

SETTING_WORDS = {
    "attic": "the attic",
    "porch": "the front porch",
    "kitchen": "the kitchen",
    "garden": "the moonlit garden",
}

SERVICE_WORDS = {
    "serve tea": {
        "verb": "serve tea",
        "scene": "pour tea into two tiny cups",
        "object": "tea",
        "item": "teacups",
        "warmth": 1.0,
        "shareable": True,
    },
    "serve cocoa": {
        "verb": "serve cocoa",
        "scene": "ladle cocoa into two mugs",
        "object": "cocoa",
        "item": "mugs",
        "warmth": 1.0,
        "shareable": True,
    },
    "serve soup": {
        "verb": "serve soup",
        "scene": "spoon soup into a bowl",
        "object": "soup",
        "item": "bowl",
        "warmth": 1.0,
        "shareable": True,
    },
}

HOP_WORDS = {
    "hop over shadows": {
        "verb": "hop over the shadows",
        "scene": "hop from tile to tile",
        "risk": "spooky",
        "joy": 1.0,
    },
    "hop on the rug": {
        "verb": "hop on the rug",
        "scene": "bounce on the braided rug",
        "risk": "bumpy",
        "joy": 1.0,
    },
    "hop in circles": {
        "verb": "hop in circles",
        "scene": "make little circles around the lantern glow",
        "risk": "silly",
        "joy": 1.0,
    },
}

NAMES = ["Mina", "Lena", "Arlo", "Noah", "Pip", "Ivy", "June", "Theo"]
GHOST_NAMES = ["Mister Pale", "Mallow Ghost", "Aunt Whisper", "Little Echo"]
TRAITS = ["curious", "brave", "gentle", "shy", "sprightly", "careful"]



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
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    shares_with: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    child: object | None = None
    ghost: object | None = None
    lantern: object | None = None
    treat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    spooky: bool = True
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
class Action:
    id: str
    service: str
    hop: str
    object_word: str
    scene_word: str
    warmth_gain: float = 1.0
    joy_gain: float = 1.0
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
class StoryParams:
    setting: str
    service: str
    hop: str
    name: str
    ghost_name: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.turns: list[str] = []

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
        nw = World(self.place)
        nw.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        nw.paragraphs = [[]]
        nw.facts = dict(self.facts)
        nw.fired = set(self.fired)
        return nw


def positive_meter(x: float) -> bool:
    return x >= 1.0


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.setting)
    action = _safe_lookup(ACTIONS, params.service)
    hop = _safe_lookup(HOPS, params.hop)
    world = World(place)

    child = world.add(Entity(
        id=params.name, kind="character", type="child", label=params.name,
        meters={"cold": 0.0, "light": 0.0, "distance": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "loneliness": 0.0, "joy": 0.0, "generosity": 0.0, "relief": 0.0},
    ))
    ghost = world.add(Entity(
        id=params.ghost_name, kind="character", type="ghost", label=params.ghost_name,
        meters={"cold": 1.0, "light": 0.0, "distance": 0.0},
        memes={"fear": 0.0, "trust": 0.0, "loneliness": 1.0, "joy": 0.0, "generosity": 0.0, "relief": 0.0},
    ))
    lantern = world.add(Entity(id="lantern", type="lantern", label="a small lantern", owner=child.id,
                                meters={"light": 1.0}, plural=False))
    treat = world.add(Entity(id="treat", type=action.object_word, label=action.object_word, owner=child.id, plural=False))
    world.facts.update(child=child, ghost=ghost, lantern=lantern, treat=treat, action=action, hop=hop, place=place)
    return world


def intro(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    g = _safe_fact(world, world.facts, "ghost")
    place = _safe_fact(world, world.facts, "place")
    trait = _safe_fact(world, world.facts, "trait")
    world.say(
        f"{c.id} was a {trait} child who liked quiet places, especially {place.label} after dark."
    )
    world.say(
        f"One pale night, {g.id} drifted by the doorway like a bit of fog that had learned a name."
    )


def meet_and_serve(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    g = _safe_fact(world, world.facts, "ghost")
    action = _safe_fact(world, world.facts, "action")
    world.say(
        f"{c.id} wanted to {action.service} for a friendly visit, and {g.id} wished to stay near the warm light."
    )
    c.memes["generosity"] += 1
    c.meters["light"] += 1
    g.memes["loneliness"] += 0.0
    world.say(
        f"{c.id} set out the cups and said, \"You can have the first sip.\""
    )


def conflict(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    g = _safe_fact(world, world.facts, "ghost")
    action = _safe_fact(world, world.facts, "action")
    hop = _safe_fact(world, world.facts, "hop")
    if not positive_meter(c.memes["generosity"]):
        pass
    c.memes["fear"] += 1
    g.memes["fear"] += 1
    c.memes["trust"] += 0.0
    world.say(
        f"But when {g.id} reached for the lantern, {c.id} pulled it closer."
    )
    world.say(
        f"{c.id} wanted to {action.service}, but also to keep the light all to {c.id.lower()}self."
    )
    world.say(
        f"The ghost answered by trying to {hop.hop} too fast, and the floorboards gave a tiny moan."
    )
    c.memes["fear"] += 1
    g.memes["loneliness"] += 1


def reconciliation(world: World) -> None:
    c = _safe_fact(world, world.facts, "child")
    g = _safe_fact(world, world.facts, "ghost")
    action = _safe_fact(world, world.facts, "action")
    hop = _safe_fact(world, world.facts, "hop")
    c.memes["fear"] = 0.0
    g.memes["fear"] = 0.0
    c.memes["trust"] += 1
    g.memes["trust"] += 1
    c.memes["joy"] += 1
    g.memes["joy"] += 1
    c.memes["relief"] += 1
    g.memes["relief"] += 1
    world.say(
        f"{c.id} stopped, took a breath, and smiled in the lantern glow. \"We can share,\" {c.id} said."
    )
    world.say(
        f"{g.id} drifted closer, and together they decided to {action.service} while taking turns with the light."
    )
    world.say(
        f"Then they {hop.scene_word}, one after the other, until the spooky house felt more like a home."
    )
    world.say(
        f"At the end, the lantern shone between them, and the ghost's pale outline looked warm instead of lonely."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    world.facts["trait"] = params.trait
    intro(world)
    world.para()
    meet_and_serve(world)
    world.para()
    conflict(world)
    world.para()
    reconciliation(world)
    return world


def generation_prompts(world: World) -> list[str]:
    c = _safe_fact(world, world.facts, "child")
    g = _safe_fact(world, world.facts, "ghost")
    action = _safe_fact(world, world.facts, "action")
    hop = _safe_fact(world, world.facts, "hop")
    return [
        f"Write a gentle ghost story about {c.id} and {g.id} learning to share a lantern while they {action.service}.",
        f"Tell a child-friendly spooky tale where someone wants to {hop.verb} and also learns reconciliation.",
        f"Write a short story with the words 'serve' and 'hop' that ends with sharing instead of fear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    g = _safe_fact(world, world.facts, "ghost")
    action = _safe_fact(world, world.facts, "action")
    hop = _safe_fact(world, world.facts, "hop")
    place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"Where did {c.id} meet {g.id}?",
            answer=f"{c.id} met {g.id} at {place.label}, where the room felt quiet and a little spooky.",
        ),
        QAItem(
            question=f"What did {c.id} want to do for the visit?",
            answer=f"{c.id} wanted to {action.service} and share a warm treat with the ghost.",
        ),
        QAItem(
            question=f"What did the ghost try to do when the story turned tense?",
            answer=f"The ghost tried to {hop.hop}, which made the floorboards creak and the moment feel more spooky.",
        ),
        QAItem(
            question="How did the problem get fixed?",
            answer="The child and the ghost agreed to share the lantern and take turns, which calmed the fear and brought them back together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something too, instead of keeping it only for yourself.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, make up, and feel friendly again.",
        ),
        QAItem(
            question="Why can a ghost story feel spooky but still be kind?",
            answer="A ghost story can be spooky because of dark rooms, whispers, and creaks, but it can still be kind when the ghost is friendly and everyone feels safe in the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'empty'}")
    return "\n".join(lines)


PLACES = {
    "attic": Place("attic", SETTING_WORDS["attic"], spooky=True, affords={"serve tea", "hop over shadows"}),
    "porch": Place("porch", SETTING_WORDS["porch"], spooky=True, affords={"serve cocoa", "hop on the rug"}),
    "kitchen": Place("kitchen", SETTING_WORDS["kitchen"], spooky=False, affords={"serve soup", "hop in circles"}),
    "garden": Place("garden", SETTING_WORDS["garden"], spooky=True, affords={"serve tea", "hop over shadows", "hop in circles"}),
}

ACTIONS = {
    "serve tea": Action("serve tea", "serve tea", "hop over the shadows", "teacups", "steaming tea"),
    "serve cocoa": Action("serve cocoa", "serve cocoa", "hop on the rug", "mugs", "warm cocoa"),
    "serve soup": Action("serve soup", "serve soup", "hop in circles", "bowl", "brothy soup"),
}

HOPS = {
    "hop over shadows": Action("hop over shadows", "serve tea", "hop over the shadows", "teacups", "shadowy tiles"),
    "hop on the rug": Action("hop on the rug", "serve cocoa", "hop on the rug", "mugs", "braided rug"),
    "hop in circles": Action("hop in circles", "serve soup", "hop in circles", "bowl", "lantern glow"),
}

TRAITS = ["curious", "brave", "gentle", "shy", "careful", "sprightly"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for service in place.affords:
            for hop_id in HOPS:
                combos.append((place_id, service, hop_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world about serving, hopping, sharing, and reconciliation.")
    ap.add_argument("--setting", choices=PLACES)
    ap.add_argument("--service", choices=ACTIONS)
    ap.add_argument("--hop", choices=HOPS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--ghost-name", choices=GHOST_NAMES)
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "service", None):
        combos = [c for c in combos if c[1] == getattr(args, "service", None)]
    if getattr(args, "hop", None):
        combos = [c for c in combos if c[2] == getattr(args, "hop", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, service, hop = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        service=service,
        hop=hop,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        ghost_name=getattr(args, "ghost_name", None) or rng.choice(GHOST_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


ASP_RULES = r"""
setting_choice(S) :- place(S).
service_choice(A) :- action(A).
hop_choice(H) :- hop(H).

compatible(S,A,H) :- place(S), action(A), hop(H), affords(S,A).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.spooky:
            lines.append(asp.fact("spooky", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for hid in HOPS:
        lines.append(asp.fact("hop", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    aset = set(asp.atoms(model, "compatible"))
    pset = set(valid_combos())
    if aset == pset:
        print(f"OK: clingo gate matches valid_combos() ({len(aset)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(aset - pset))
    print("only in python:", sorted(pset - aset))
    return 1


CURATED = [
    StoryParams(setting="attic", service="serve tea", hop="hop over shadows", name="Mina", ghost_name="Mister Pale", trait="curious"),
    StoryParams(setting="porch", service="serve cocoa", hop="hop on the rug", name="Theo", ghost_name="Aunt Whisper", trait="gentle"),
    StoryParams(setting="garden", service="serve tea", hop="hop in circles", name="Ivy", ghost_name="Little Echo", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        for combo in combos:
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            params.seed = base_seed + i
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
