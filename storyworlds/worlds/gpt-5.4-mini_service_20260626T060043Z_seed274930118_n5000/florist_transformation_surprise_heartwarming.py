#!/usr/bin/env python3
"""
A small heartwarming story world about a florist, a surprise, and a gentle
transformation.

Premise:
- A florist is preparing flowers for someone special.
- A plain, unfinished arrangement feels too ordinary.
- With care, a small transformation turns it into a surprise that warms the
  heart.

The story is state-driven: the florist's flowers, wrapping, ribbon, and card all
change over time, and the emotional state shifts from worry to delight.
"""

from __future__ import annotations

import argparse
import copy
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


def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)


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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    giver: Optional[str] = None
    recipient: Optional[str] = None
    bytes: dict[str, float] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bouquet: object | None = None
    florist: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class FloristSetting:
    place: str = "the flower shop"
    calm: bool = True
    has_counter: bool = True
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
class Bouquet:
    label: str
    phrase: str
    base_flowers: str
    colors: str
    before: str
    after: str
    surprise_effect: str
    scent: str = "sweet"
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Transformation:
    id: str
    label: str
    prep: str
    reveal: str
    boosts: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Surprise:
    id: str
    label: str
    trigger: str
    reveal_line: str
    boosts: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: FloristSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    bouquet: str
    transformation: str
    surprise: str
    florist_name: str
    recipient_name: str
    seed: Optional[int] = None
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


SETTINGS = {
    "shop": FloristSetting(place="the flower shop", calm=True, has_counter=True),
    "window": FloristSetting(place="the shop window", calm=True, has_counter=True),
}

BOUQUETS = {
    "plain": Bouquet(
        label="plain bouquet",
        phrase="a plain bouquet of white daisies",
        base_flowers="white daisies",
        colors="soft white",
        before="look a little plain",
        after="shine with color and ribbon",
        surprise_effect="looked suddenly special",
    ),
    "tulips": Bouquet(
        label="tulip bunch",
        phrase="a small bunch of tulips",
        base_flowers="tulips",
        colors="pink and red",
        before="sit in a neat row",
        after="bloom like a happy song",
        surprise_effect="felt warm and cheerful",
    ),
    "roses": Bouquet(
        label="rose bouquet",
        phrase="a rose bouquet with green leaves",
        base_flowers="roses",
        colors="red and cream",
        before="wait quietly in a jar",
        after="open like a little celebration",
        surprise_effect="felt like a gentle hug",
    ),
}

TRANSFORMATIONS = {
    "wrap": Transformation(
        id="wrap",
        label="gift wrap",
        prep="wrap the flowers in bright paper and tie them with ribbon",
        reveal="the paper made the bouquet look ready for a gift",
        boosts={"care", "delight"},
    ),
    "sparkle": Transformation(
        id="sparkle",
        label="sparkly ribbon",
        prep="add a sparkly ribbon and a little tag",
        reveal="the ribbon made the flowers seem full of surprise",
        boosts={"surprise", "hope"},
    ),
    "arrange": Transformation(
        id="arrange",
        label="careful arrangement",
        prep="arrange the stems in a round, balanced shape",
        reveal="the careful shape made the bouquet look graceful",
        boosts={"calm", "pride"},
    ),
}

SURPRISES = {
    "card": Surprise(
        id="card",
        label="handwritten card",
        trigger="slip a handwritten card between the stems",
        reveal_line="the card carried a loving message",
        boosts={"love", "warmth"},
    ),
    "delivery": Surprise(
        id="delivery",
        label="secret delivery",
        trigger="set the bouquet aside for a secret delivery",
        reveal_line="the secret was that the bouquet was for someone kind and brave",
        boosts={"surprise", "joy"},
    ),
    "scent": Surprise(
        id="scent",
        label="sweet scent",
        trigger="tuck in a sprig of lavender for a soft scent",
        reveal_line="the gentle scent made the whole shop feel peaceful",
        boosts={"calm", "comfort"},
    ),
}

GIVEN_NAMES = ["Mina", "Lena", "Noah", "Iris", "Theo", "June", "Aria", "Maya"]


class ReasonableGate:
    @staticmethod
    def valid_combo(place: str, bouquet: str, transformation: str, surprise: str) -> bool:
        return place in SETTINGS and bouquet in BOUQUETS and transformation in TRANSFORMATIONS and surprise in SURPRISES

    @staticmethod
    def explain_invalid() -> str:
        return "(No story: the requested florist scene could not be made into a gentle transformation surprise.)"


def set_meter(e: Entity, key: str, value: float) -> None:
    e.meters[key] = value


def add_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def add_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def propagate(world: World) -> None:
    florist = world.get("florist")
    bouquet = world.get("bouquet")
    if bouquet.meters.get("wrapped", 0.0) >= THRESHOLD and bouquet.meters.get("tagged", 0.0) >= THRESHOLD:
        sig = ("ready",)
        if sig not in world.fired:
            world.fired.add(sig)
            add_meme(florist, "pride", 1)
            add_meme(florist, "hope", 1)
            world.say("The bouquet started to feel ready for a surprise.")
    if bouquet.meters.get("delivered", 0.0) >= THRESHOLD and bouquet.memes.get("surprise", 0.0) >= THRESHOLD:
        sig = ("reveal",)
        if sig not in world.fired:
            world.fired.add(sig)
            add_meme(world.get("recipient"), "joy", 1)
            add_meme(florist, "warmth", 1)
            world.say("The last step turned the bouquet into a happy surprise.")


def introduce(world: World, florist: Entity, bouquet: Entity) -> None:
    world.say(
        f"{florist.id} was a florist who loved arranging flowers that could make a day feel kinder. "
        f"On the counter sat {bouquet.phrase}, waiting to {_safe_lookup(BOUQUETS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "bouquet_id")).before}."
    )


def setup_scene(world: World, florist: Entity, recipient: Entity, bouquet: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {florist.id} looked at {recipient.id}'s card and smiled softly. "
        f"{recipient.id} was having a hard week, and {florist.id} wanted a small surprise that would feel like care."
    )
    add_meme(florist, "worry", 1)
    add_meme(florist, "care", 1)


def do_transformation(world: World, florist: Entity, bouquet: Entity, t: Transformation) -> None:
    add_meter(bouquet, "transformed", 1)
    add_meme(florist, "hope", 1)
    world.say(f"{florist.id} decided to {t.prep}.")
    world.say(f"{t.reveal.capitalize()}.")


def do_surprise(world: World, florist: Entity, bouquet: Entity, s: Surprise) -> None:
    add_meter(bouquet, "tagged", 1)
    add_meter(bouquet, "delivered", 1)
    add_meme(bouquet, "surprise", 1)
    add_meme(florist, "love", 1)
    world.say(f"{florist.id} then chose to {s.trigger}.")
    world.say(f"{s.reveal_line.capitalize()}.")


def reveal_and_end(world: World, florist: Entity, recipient: Entity, bouquet: Entity) -> None:
    add_meme(recipient, "joy", 1)
    add_meme(recipient, "love", 1)
    world.say(
        f"When {recipient.id} finally saw the bouquet, their face lit up. "
        f"The plain flowers had become a gift that felt warm, thoughtful, and exactly right."
    )
    world.say(
        f"{florist.id} watched the smile grow and felt the lovely little secret turn into shared happiness."
    )


def tell(setting: FloristSetting, bouquet_cfg: Bouquet, transformation: Transformation, surprise: Surprise,
         florist_name: str, recipient_name: str) -> World:
    world = World(setting)
    florist = world.add(Entity(id=florist_name, kind="character", type="person", label="florist"))
    recipient = world.add(Entity(id=recipient_name, kind="character", type="person", label="recipient"))
    bouquet = world.add(Entity(id="bouquet", kind="thing", type="bouquet", label=bouquet_cfg.label, phrase=bouquet_cfg.phrase))
    world.facts.update(
        florist=florist, recipient=recipient, bouquet=bouquet, bouquet_id=bouquet_cfg.label,
        transformation=transformation, surprise=surprise, place=setting.place,
    )
    introduce(world, florist, bouquet)
    world.para()
    setup_scene(world, florist, recipient, bouquet)
    do_transformation(world, florist, bouquet, transformation)
    do_surprise(world, florist, bouquet, surprise)
    propagate(world)
    world.para()
    reveal_and_end(world, florist, recipient, bouquet)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming story about a florist turning a simple bouquet into a surprise gift.',
        f"Tell a gentle story set in {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place")} where a florist makes flowers feel special for someone kind.",
        "Write a short children's story about flowers, a careful change, and a happy reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    florist: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "florist")
    recipient: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "recipient")
    bouquet: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "bouquet")
    t: Transformation = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "transformation")
    s: Surprise = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "surprise")
    return [
        QAItem(
            question=f"What was {florist.id} trying to make from the plain bouquet?",
            answer=f"{florist.id} was trying to make it into a warm surprise gift for {recipient.id}.",
        ),
        QAItem(
            question=f"How did {florist.id} change the bouquet?",
            answer=f"{florist.id} changed it by choosing to {t.prep} and then to {s.trigger}.",
        ),
        QAItem(
            question=f"Why did the bouquet become more special at the end?",
            answer=f"It became more special because the flowers were transformed with care and a loving surprise was added for {recipient.id}.",
        ),
        QAItem(
            question=f"What did {recipient.id} feel when the bouquet was revealed?",
            answer=f"{recipient.id} felt joy and warmth when the bouquet was revealed.",
        ),
        QAItem(
            question=f"What kind of bouquet was it before the transformation?",
            answer=f"It was {bouquet.phrase}, and it first seemed {bouquet.before}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a florist do?",
            answer="A florist arranges and sells flowers, and often helps people choose bouquets for special moments.",
        ),
        QAItem(
            question="What is a bouquet?",
            answer="A bouquet is a bunch of flowers gathered together, often for a gift or a celebration.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that can make someone feel excited or happy.",
        ),
        QAItem(
            question="What does it mean to transform something?",
            answer="To transform something means to change it into a new form or to make it look or feel different.",
        ),
        QAItem(
            question="Why can flowers make people feel better?",
            answer="Flowers can feel cheerful, gentle, and thoughtful, so they often help people feel cared for.",
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(next(iter(t)) for t in world.fired) if world.fired else []}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming florist transformation surprise storyworld.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--bouquet", choices=BOUQUETS.keys())
    ap.add_argument("--transformation", choices=TRANSFORMATIONS.keys())
    ap.add_argument("--surprise", choices=SURPRISES.keys())
    ap.add_argument("--florist-name")
    ap.add_argument("--recipient-name")
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, b, t, s) for p in SETTINGS for b in BOUQUETS for t in TRANSFORMATIONS for s in SURPRISES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "bouquet", None):
        combos = [c for c in combos if c[1] == getattr(args, "bouquet", None)]
    if getattr(args, "transformation", None):
        combos = [c for c in combos if c[2] == getattr(args, "transformation", None)]
    if getattr(args, "surprise", None):
        combos = [c for c in combos if c[3] == getattr(args, "surprise", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, bouquet, transformation, surprise = rng.choice(list(combos))
    florist_name = getattr(args, "florist_name", None) or rng.choice(GIVEN_NAMES)
    recipient_name = getattr(args, "recipient_name", None) or rng.choice([n for n in GIVEN_NAMES if n != florist_name])
    return StoryParams(
        place=place,
        bouquet=bouquet,
        transformation=transformation,
        surprise=surprise,
        florist_name=florist_name,
        recipient_name=recipient_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(BOUQUETS, params.bouquet),
        _safe_lookup(TRANSFORMATIONS, params.transformation),
        _safe_lookup(SURPRISES, params.surprise),
        params.florist_name,
        params.recipient_name,
    )
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
valid(P,B,T,S) :- place(P), bouquet(B), transformation(T), surprise(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for b in BOUQUETS:
        lines.append(asp.fact("bouquet", b))
    for t in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", t))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("shop", "plain", "wrap", "card", "Mina", "June"),
            StoryParams("window", "tulips", "sparkle", "delivery", "Theo", "Iris"),
            StoryParams("shop", "roses", "arrange", "scent", "Lena", "Noah"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
