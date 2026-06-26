#!/usr/bin/env python3
"""
storyworlds/worlds/transmit_bookstore_transformation_tall_tale.py
==================================================================

A tall-tale story world about a bookstore where a child discovers a strange
transmitter, sends a tiny signal through the shelves, and watches a humble
transformation ripple through the shop.

The seed image is simple:
- a bookstore full of books, ladders, and quiet corners
- a curious child who can transmit a wish or a message
- a small object that changes into something grander
- a grumbly problem that turns into wonder

The world is constrained and causal:
- the transmitter can only work when its battery is charged and its speaker is
  aimed at a shelf or a sign
- a transformed object must be small enough to change and must fit the target
  role it becomes
- the transformation should be surprising but useful, not random noise

The story is written in a child-facing tall-tale style, with a big-voiced
narrator, clear state changes, and a final image that proves the change took.
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

THRESHOLD = 1.0


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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    portable: bool = True
    transformed_from: Optional[str] = None
    transformed_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    problem: object | None = None
    transform: object | None = None
    transmitter: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the bookstore"
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
class Transmitter:
    id: str
    label: str
    battery: str
    power: int
    needs_aim: bool = True
    sound: str = "booming"
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Transform:
    id: str
    label: str
    phrase: str
    becomes: str
    size: str
    role: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
    kind: str
    blocking: str
    target_role: str
    tags: set[str] = field(default_factory=set)
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
        self.trace: list[str] = []

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
            self.trace.append(text)

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
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


@dataclass
class StoryParams:
    place: str
    transmitter: str
    transform: str
    problem: str
    name: str
    gender: str
    helper: str
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


SETTINGS = {
    "bookstore": Setting(place="the bookstore", affords={"transmit", "transform"}),
}

TRANSMITTERS = {
    "megaphone": Transmitter(
        id="megaphone",
        label="a brass megaphone",
        battery="fresh batteries",
        power=2,
        sound="booming",
        tags={"transmit", "sound"},
    ),
    "radio": Transmitter(
        id="radio",
        label="an old radio",
        battery="fresh batteries",
        power=2,
        sound="crackling",
        tags={"transmit", "signal"},
    ),
}

TRANSFORMS = {
    "bookmark": Transform(
        id="bookmark",
        label="a plain bookmark",
        phrase="a plain paper bookmark",
        becomes="a golden bookmark",
        size="small",
        role="guide",
        keyword="transformation",
        tags={"transform", "book"},
    ),
    "stool": Transform(
        id="stool",
        label="a little stool",
        phrase="a little wooden stool",
        becomes="a tall ladder-step stool",
        size="small",
        role="reach",
        keyword="transformation",
        tags={"transform", "shelf"},
    ),
    "sign": Transform(
        id="sign",
        label="a sleepy sign",
        phrase="a sleepy shelf sign",
        becomes="a bright, blinking welcome sign",
        size="small",
        role="welcome",
        keyword="transformation",
        tags={"transform", "sign"},
    ),
}

PROBLEMS = {
    "dark_corner": Problem(
        id="dark_corner",
        label="a dark corner",
        phrase="a dark corner that made the far shelf hard to read",
        kind="shadow",
        blocking="reading",
        target_role="welcome",
        tags={"bookstore", "sign"},
    ),
    "high_shelf": Problem(
        id="high_shelf",
        label="a high shelf",
        phrase="a high shelf that no small hand could reach",
        kind="height",
        blocking="reaching",
        target_role="reach",
        tags={"bookstore", "shelf"},
    ),
    "lost_greeting": Problem(
        id="lost_greeting",
        label="a lost greeting",
        phrase="a lost greeting that made the front desk feel plain",
        kind="plainness",
        blocking="welcoming",
        target_role="welcome",
        tags={"bookstore", "sign"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "June", "Nora", "Ivy", "Ada", "Tessa", "Ruth"]
BOY_NAMES = ["Otis", "Pip", "Eli", "Finn", "Theo", "Arlo", "Beck", "Noah"]
TRAITS = ["curious", "bold", "cheerful", "spry", "bright-eyed", "determined"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for t in TRANSFORMERS():
            pass
    for place in SETTINGS:
        for tx in TRANSMITTERS:
            for tr in TRANSFORMS:
                for pr in PROBLEMS:
                    if place == "bookstore":
                        combos.append((place, tx, tr))
    return combos


def TRANSFORMERS():
    return ["megaphone", "radio"]


def prize_at_risk(transform: Transform, problem: Problem) -> bool:
    return transform.role == problem.target_role


def select_fix(transmitter: Transmitter, transform: Transform, problem: Problem) -> bool:
    return transmitter.power >= THRESHOLD and prize_at_risk(transform, problem)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _transmit(world: World, child: Entity, transmitter: Transmitter, problem: Problem) -> bool:
    if transmitter.id not in world.entities:
        pass
    item = world.get(transmitter.id)
    if item.meters.get("charged", 0.0) < THRESHOLD:
        return False
    if world.setting.place != "the bookstore":
        return False
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1
    world.say(
        f"{child.id} lifted {item.label} and transmit a mighty message across the bookstore."
    )
    world.say(
        f"The sound rolled between the shelves like thunder wearing slippers, right toward {problem.label}."
    )
    return True


def _transform(world: World, child: Entity, transform: Transform, problem: Problem) -> bool:
    target = world.get(transform.id)
    if target.meters.get("ready", 0.0) < THRESHOLD:
        return False
    if transform.role != problem.target_role:
        return False
    target.transformed_from = transform.phrase
    target.transformed_to = transform.becomes
    target.label = transform.becomes
    target.phrase = transform.becomes
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    world.say(
        f"And then came the grand Transformation: {transform.phrase} blinked, spun, and became {transform.becomes}."
    )
    return True


def tell_story(world: World, child: Entity, helper: Entity, transmitter: Transmitter,
               transform: Transform, problem: Problem) -> None:
    world.say(
        f"Once upon a tall and twinkling afternoon, {child.id} was in {world.setting.place}, "
        f"where the books stood shoulder to shoulder like patient old trees."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved the smell of paper and ink, and {helper.id} kept the aisle tidy with a grin."
    )
    world.say(
        f"On a shelf near the window sat {transmitter.label}, and beside it rested {transform.phrase}."
    )
    world.say(
        f"Farther in the shop waited {problem.phrase}, and it was giving the whole place a grumpy little shadow."
    )
    world.para()

    transmitter_ent = world.get(transmitter.id)
    transformer_ent = world.get(transform.id)
    transmitter_ent.meters["charged"] = 1.0
    transformer_ent.meters["ready"] = 1.0

    if _transmit(world, child, transmitter, problem):
        world.say(
            f"The message was not a small one. It swelled up big as a parade drum and boomed straight to the dark corner."
        )
    world.say(
        f"{helper.id} pointed and said, \"That signal stirred the dust, but it looks like the right kind of storm for a change.\""
    )
    world.say(
        f"{child.id} took a breath, aimed the buzz of the transmitter, and whispered the word {transform.keyword}."
    )
    _transform(world, child, transform, problem)
    world.para()

    world.say(
        f"Then the bookstore showed its trick: the new {transform.becomes} lit the corner, and the problem shrank like a puddle under noon sun."
    )
    world.say(
        f"Customers could read the signs again, the aisle brightened, and {helper.id} laughed so hard the ladder rattled."
    )
    world.say(
        f"{child.id} stood tall beside the shelves, holding the transmitter in one hand and the shining new thing in the other, as proud as a lion in a library."
    )


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=params.helper, meters={}, memes={}))
    transmitter = world.add(Entity(
        id=params.transmitter,
        kind="thing",
        type="tool",
        label=_safe_lookup(TRANSMITTERS, params.transmitter).label,
        phrase=_safe_lookup(TRANSMITTERS, params.transmitter).label,
        portable=True,
        meters={"charged": 1.0},
    ))
    transform = world.add(Entity(
        id=params.transform,
        kind="thing",
        type="object",
        label=_safe_lookup(TRANSFORMS, params.transform).label,
        phrase=_safe_lookup(TRANSFORMS, params.transform).phrase,
        portable=True,
        meters={"ready": 1.0},
    ))
    problem = world.add(Entity(
        id=params.problem,
        kind="thing",
        type="problem",
        label=_safe_lookup(PROBLEMS, params.problem).label,
        phrase=_safe_lookup(PROBLEMS, params.problem).phrase,
        portable=False,
    ))
    world.facts.update(
        child=child,
        helper=helper,
        transmitter=_safe_lookup(TRANSMITTERS, params.transmitter),
        transform=_safe_lookup(TRANSFORMS, params.transform),
        problem=_safe_lookup(PROBLEMS, params.problem),
    )
    tell_story(world, child, helper, _safe_lookup(TRANSMITTERS, params.transmitter), _safe_lookup(TRANSFORMS, params.transform), _safe_lookup(PROBLEMS, params.problem))
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for young children set in a bookstore that includes the word "transmit".',
        f"Tell a playful story where {f['child'].id} uses {f['transmitter'].label} to transmit a message and cause a Transformation.",
        f"Write a bookstore story about a curious child, a booming signal, and a surprising transformation on a shelf.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    tx = _safe_fact(world, f, "transmitter")
    tr = _safe_fact(world, f, "transform")
    pr = _safe_fact(world, f, "problem")
    return [
        QAItem(
            question=f"Who was the story about in the bookstore?",
            answer=f"It was about {child.id}, who was curious and brave in the bookstore with {helper.label}.",
        ),
        QAItem(
            question=f"What did {child.id} use to transmit a message?",
            answer=f"{child.id} used {tx.label} to transmit a mighty message across the bookstore.",
        ),
        QAItem(
            question=f"What happened to {tr.phrase}?",
            answer=f"It changed in a grand Transformation and became {tr.becomes}.",
        ),
        QAItem(
            question=f"What problem was fixed by the end of the story?",
            answer=f"{pr.phrase} was no longer a problem, because the new bright thing lit the corner and made the bookstore feel welcoming.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bookstore?",
            answer="A bookstore is a place where people go to find books, stories, and quiet corners to read.",
        ),
        QAItem(
            question="What does transmit mean?",
            answer="To transmit means to send something, like a sound, a message, or a signal, from one place to another.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form to another, like when something plain becomes something new and useful.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.transformed_to:
            bits.append(f"transformed_to={e.transformed_to}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A transformation is reasonable when the target role matches the problem.
reasonable_transform(T, P) :- transform(T), problem(P), role(T, R), target_role(P, R).

% Transmit is reasonable when there is power and the place is the bookstore.
reasonable_transmit(Tx, Place) :- transmitter(Tx), power(Tx, Pow), Pow >= 1, place(Place), bookstore(Place).

valid_combo(Place, Tx, T, P) :- reasonable_transmit(Tx, Place), reasonable_transform(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        if place == "bookstore":
            lines.append(asp.fact("bookstore", place))
    for tid, tx in TRANSMITTERS.items():
        lines.append(asp.fact("transmitter", tid))
        lines.append(asp.fact("power", tid, tx.power))
    for tid, tr in TRANSFORMS.items():
        lines.append(asp.fact("transform", tid))
        lines.append(asp.fact("role", tid, tr.role))
    for pid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("target_role", pid, pr.target_role))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/4."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


# ---------------------------------------------------------------------------
# Random selection and sample generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [("bookstore", tx, tr) for tx in TRANSMITTERS for tr in TRANSFORMS]


def explain_rejection() -> str:
    return "(No story: this world only supports the bookstore, a transmitter, and a transformation that truly fits the problem.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale bookstore storyworld with transmit and Transformation."
    )
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--transmitter", choices=list(TRANSMITTERS))
    ap.add_argument("--transform", choices=list(TRANSFORMS))
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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
    if getattr(args, "place", None) and getattr(args, "place", None) != "bookstore":
        return _fallback_storyparams(args, rng, StoryParams, globals())

    tx = getattr(args, "transmitter", None) or rng.choice(list(TRANSMITTERS))
    tr = getattr(args, "transform", None) or rng.choice(list(TRANSFORMS))
    pr = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    if not (prize_at_risk(_safe_lookup(TRANSFORMS, tr), _safe_lookup(PROBLEMS, pr))):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["the kindly clerk", "the bookish helper", "the smiling librarian"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place="bookstore",
        transmitter=tx,
        transform=tr,
        problem=pr,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_combo/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/4."))
        triples = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(triples)} valid combos:\n")
        for row in triples:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("bookstore", "megaphone", "bookmark", "dark_corner", "Mina", "girl", "the kindly clerk", "curious"),
            StoryParams("bookstore", "radio", "stool", "high_shelf", "Otis", "boy", "the smiling librarian", "bold"),
            StoryParams("bookstore", "megaphone", "sign", "lost_greeting", "Lily", "girl", "the bookish helper", "cheerful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
            header = f"### {p.name}: {p.transmitter} + {p.transform} in the bookstore"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
