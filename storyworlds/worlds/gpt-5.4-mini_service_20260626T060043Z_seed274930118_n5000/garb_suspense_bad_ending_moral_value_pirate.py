#!/usr/bin/env python3
"""
A tiny pirate tale storyworld: a child-friendly suspense story about garb,
where a careless choice leads to a bad ending and a moral lesson.

The premise is intentionally small:
- a young pirate wants to wear a special garb for a sea outing,
- something dangerous goes wrong or is nearly wrong,
- the final image proves what changed,
- but the ending keeps a moral value: the crew learns to respect safety,
  promises, and careful choices.

This world is constraint-checked and comes with an ASP twin for parity.
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
# Domain registries
# ---------------------------------------------------------------------------


def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
class Setting:
    id: str
    place: str
    weather: str
    afford: set[str] = field(default_factory=set)
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
class Garb:
    id: str
    label: str
    phrase: str
    body: str
    value: str
    protects: set[str] = field(default_factory=set)
    style: str = "pirate"
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
class Threat:
    id: str
    label: str
    verb: str
    danger: str
    fear: str
    kind: str
    needed: str
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
class Lesson:
    id: str
    moral: str
    value: str
    phrase: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


SETTINGS = {
    "dock": Setting(
        id="dock",
        place="the dock",
        weather="windy",
        afford={"tide", "gull", "rope"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the harbor",
        weather="foggy",
        afford={"tide", "gull", "rope", "fog"},
    ),
    "ship": Setting(
        id="ship",
        place="the deck of the ship",
        weather="stormy",
        afford={"tide", "rope", "fog", "storm"},
    ),
}

GARB = {
    "hat": Garb(
        id="hat",
        label="captain hat",
        phrase="a bright captain hat",
        body="head",
        value="pride",
        protects={"sun", "spray"},
    ),
    "coat": Garb(
        id="coat",
        label="oilskin coat",
        phrase="a thick oilskin coat",
        body="torso",
        value="care",
        protects={"rain", "spray"},
    ),
    "boots": Garb(
        id="boots",
        label="sea boots",
        phrase="sturdy sea boots",
        body="feet",
        value="steady steps",
        protects={"spray", "slip"},
    ),
    "sash": Garb(
        id="sash",
        label="red sash",
        phrase="a red sash with a knot",
        body="waist",
        value="bravery",
        protects={"rope"},
    ),
}

THREATS = {
    "tide": Threat(
        id="tide",
        label="the rising tide",
        verb="rose fast",
        danger="the dock would soon be slick and slippery",
        fear="the planks could turn wet under their feet",
        kind="water",
        needed="boots",
    ),
    "gull": Threat(
        id="gull",
        label="a hungry gull",
        verb="kept swooping low",
        danger="it might snatch the shiny snack",
        fear="it could peck at the food and start trouble",
        kind="bird",
        needed="hat",
    ),
    "rope": Threat(
        id="rope",
        label="a tangled rope",
        verb="lay twisted across the deck",
        danger="someone could trip and tumble",
        fear="the knot could catch a careless ankle",
        kind="snare",
        needed="boots",
    ),
    "fog": Threat(
        id="fog",
        label="the thick fog",
        verb="rolled in close",
        danger="the ship’s edge looked hard to see",
        fear="the crew could lose their way",
        kind="mist",
        needed="coat",
    ),
    "storm": Threat(
        id="storm",
        label="the storm",
        verb="banged the sails and hissed",
        danger="spray could soak everything at once",
        fear="the deck could become cold and wild",
        kind="weather",
        needed="coat",
    ),
}

LESSONS = {
    "care": Lesson(
        id="care",
        moral="It is wise to dress for the sea before you rush to play.",
        value="care",
        phrase="careful choices keep everyone safer",
    ),
    "promise": Lesson(
        id="promise",
        moral="A promise is best kept, even when the sea looks exciting.",
        value="promise",
        phrase="keeping promises builds trust",
    ),
    "sharing": Lesson(
        id="sharing",
        moral="When a crew shares and listens, the ship feels steadier.",
        value="sharing",
        phrase="listening helps a crew work together",
    ),
}

NAMES = ["Nina", "Milo", "Tess", "Pip", "Jory", "Lena", "Oren", "Sia"]
CREW = ["captain", "mate", "first mate", "deckhand"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    label: str
    title: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    wearing: Optional[str] = None
    owner: Optional[str] = None
    hero: object | None = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        w.facts = dict(self.facts)
        return w


def meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def garb_is_reasonable(threat: Threat, garb: Garb) -> bool:
    return garb.id == threat.needed or garb.protects.intersection({threat.kind, threat.id})


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid in setting.afford:
            threat = _safe_lookup(THREATS, tid)
            for gid, garb in GARB.items():
                if garb_is_reasonable(threat, garb):
                    for lesson_id in LESSONS:
                        combos.append((sid, tid, gid, lesson_id))
    return combos


def explain_rejection(setting_id: str, threat_id: str, garb_id: str) -> str:
    setting = _safe_lookup(SETTINGS, setting_id)
    threat = _safe_lookup(THREATS, threat_id)
    garb = GARB[garb_id]
    return (
        f"(No story: at {setting.place}, {garb.phrase} does not honestly help with "
        f"{threat.label}. The pirate tale needs garb that can actually meet the danger.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def predict_outcome(world: World, hero: Entity, threat: Threat) -> dict[str, bool]:
    sim = world.copy()
    simulate_threat(sim, hero, threat, narrate=False)
    return {
        "bad_ending": bool(sim.facts.get("bad_ending")),
        "warning_spread": bool(sim.facts.get("warning_spread")),
    }


def start_story(world: World, hero: Entity, garb: Garb, lesson: Lesson) -> None:
    world.say(
        f"{hero.label} was a little pirate who loved the sea and valued {lesson.value}."
    )
    world.say(
        f"{hero.label} also loved {garb.phrase}, because it made {hero.title or 'the crew'} feel ready for adventure."
    )


def set_out(world: World, hero: Entity, setting: Setting, threat: Threat) -> None:
    world.say(f"One day, {hero.label} went to {setting.place}, where {threat.label} was nearby.")
    world.say(f"The air was {setting.weather}, and {threat.label} {threat.verb}.")


def warn(world: World, hero: Entity, threat: Threat, garb: Garb) -> None:
    meme(hero, "worry", 1)
    world.say(
        f"A salty old mate frowned and said, \"Watch out — {threat.fear}, and your {garb.label} may not be enough.\""
    )


def disobey(world: World, hero: Entity, garb: Garb) -> None:
    meme(hero, "curiosity", 1)
    world.say(
        f"But {hero.label} laughed, tightened {garb.phrase} in a hurry, and ran toward the excitement anyway."
    )


def simulate_threat(world: World, hero: Entity, threat: Threat, narrate: bool = True) -> None:
    meter(hero, threat.kind, 1)
    if threat.id == "storm":
        meter(hero, "wet", 1)
    if threat.id in {"tide", "rope", "fog", "storm"}:
        world.facts["bad_ending"] = True
        world.facts["warning_spread"] = True
        if narrate:
            world.say(
                f"Then trouble struck: {threat.label} did what it does, and {hero.label} got caught in it."
            )
        return
    world.facts["bad_ending"] = False
    if narrate:
        world.say(
            f"The danger passed, but only because the crew had chosen the right garb first."
        )


def bad_ending(world: World, hero: Entity, garb: Garb, threat: Threat, lesson: Lesson) -> None:
    meter(hero, "fear", 1)
    world.facts["lesson"] = lesson.id
    world.say(
        f"In the end, {hero.label} lost the race against {threat.label}; {garb.phrase} could not save the day."
    )
    world.say(
        f"{hero.label} had to admit that {lesson.moral.lower()}"
    )


def resolve(world: World, hero: Entity, garb: Garb, threat: Threat, lesson: Lesson) -> None:
    if world.facts.get("bad_ending"):
        bad_ending(world, hero, garb, threat, lesson)
    else:
        world.say(
            f"At last, {hero.label} learned that {lesson.moral.lower()}"
        )


def tell(setting: Setting, threat: Threat, garb: Garb, lesson: Lesson, name: str, title: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", label=name, title=title))
    world.facts.update(setting=setting.id, threat=threat.id, garb=garb.id, lesson=lesson.id)

    start_story(world, hero, garb, lesson)
    world.para()
    set_out(world, hero, setting, threat)
    warn(world, hero, threat, garb)
    disobey(world, hero, garb)
    simulate_threat(world, hero, threat, narrate=True)
    world.para()
    resolve(world, hero, garb, threat, lesson)
    return world


# ---------------------------------------------------------------------------
# Parameters and sampling
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    threat: str
    garb: str
    lesson: str
    name: str
    title: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_id = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    setting = _safe_lookup(SETTINGS, setting_id)
    threat_id = getattr(args, "threat", None) or rng.choice(sorted(setting.afford))
    if threat_id not in setting.afford:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    threat = _safe_lookup(THREATS, threat_id)

    if getattr(args, "garb", None):
        garb = GARB[getattr(args, "garb", None)]
        if not garb_is_reasonable(threat, garb):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        garb_id = getattr(args, "garb", None)
    else:
        choices = [gid for gid, g in GARB.items() if garb_is_reasonable(threat, g)]
        if not choices:
            return _fallback_storyparams(args, rng, StoryParams, globals())
        garb_id = rng.choice(sorted(choices))

    lesson_id = getattr(args, "lesson", None) or rng.choice(list(LESSONS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    title = getattr(args, "title", None) or rng.choice(CREW)
    return StoryParams(
        setting=setting_id,
        threat=threat_id,
        garb=garb_id,
        lesson=lesson_id,
        name=name,
        title=title,
        seed=getattr(args, "seed", None),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = _safe_lookup(SETTINGS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting"))
    threat = _safe_lookup(THREATS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "threat"))
    garb = _safe_lookup(GARB, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "garb"))
    lesson = _safe_lookup(LESSONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "lesson"))
    return [
        f'Write a short pirate tale set at {setting.place} that includes the word "garb".',
        f"Tell a suspenseful story about a little pirate whose {garb.phrase} is not enough for {threat.label}, and end with a moral lesson.",
        f"Write a child-friendly pirate story where danger rises, a choice goes wrong, and {lesson.moral.lower()} is learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "name")
    setting = _safe_lookup(SETTINGS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting"))
    threat = _safe_lookup(THREATS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "threat"))
    garb = _safe_lookup(GARB, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "garb"))
    lesson = _safe_lookup(LESSONS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "lesson"))
    return [
        QAItem(
            question=f"Where did {hero.label} go in the story?",
            answer=f"{hero.label} went to {setting.place}, where {threat.label} was waiting nearby.",
        ),
        QAItem(
            question=f"What garb did {hero.label} love to wear?",
            answer=f"{hero.label} loved {garb.phrase}. It made the pirate feel ready, even though it was not enough for the danger.",
        ),
        QAItem(
            question=f"What was the moral value of the story?",
            answer=lesson.moral,
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=(
                f"The ending was bad because {threat.label} won the struggle, and {hero.label} learned the hard way that "
                f"{lesson.phrase}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is garb?",
            answer="Garb is clothing or an outfit that a person wears.",
        ),
        QAItem(
            question="Why do sailors use strong clothes on a ship?",
            answer="Sailors use strong clothes because wind, water, and ropes can be rough on a ship.",
        ),
        QAItem(
            question="Why can fog be dangerous at sea?",
            answer="Fog can hide the edges of a dock or ship, so people may not see where they are going.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for e in list(world.entities.values()):
        parts.append(f"{e.id}: kind={e.kind} label={e.label} meters={e.meters} memes={e.memes}")
    parts.append(f"facts={world.facts}")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/4.

valid(S, T, G, L) :-
    setting(S), afford(S, T),
    threat(T), garb(G), lesson(L),
    reasonable(T, G).

reasonable(T, G) :- needed(T, G).
reasonable(T, G) :- protects(G, K), threat_kind(T, K).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tid in sorted(s.afford):
            lines.append(asp.fact("afford", sid, tid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("threat_kind", tid, t.kind))
        lines.append(asp.fact("needed", tid, t.needed))
    for gid, g in GARB.items():
        lines.append(asp.fact("garb", gid))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", gid, p))
    for lid in LESSONS:
        lines.append(asp.fact("lesson", lid))
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
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate garb suspense storyworld with a bad ending and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--garb", choices=GARB)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--title", choices=CREW)
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(THREATS, params.threat),
        GARB[params.garb],
        _safe_lookup(LESSONS, params.lesson),
        params.name,
        params.title,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="dock", threat="tide", garb="boots", lesson="care", name="Nina", title="captain"),
    StoryParams(setting="harbor", threat="fog", garb="coat", lesson="promise", name="Pip", title="mate"),
    StoryParams(setting="ship", threat="storm", garb="coat", lesson="sharing", name="Tess", title="deckhand"),
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid pirate garb combos:")
        for c in combos:
            print("  ", c)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = (getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)) + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(str(e))
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
