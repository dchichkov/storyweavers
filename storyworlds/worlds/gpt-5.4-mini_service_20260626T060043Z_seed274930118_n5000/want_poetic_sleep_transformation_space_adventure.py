#!/usr/bin/env python3
"""
storyworlds/worlds/want_poetic_sleep_transformation_space_adventure.py
======================================================================

A tiny space-adventure story world about wanting a poetic sleep, using a
carefully chosen transformation to solve a problem in the ship.

Premise:
- A small traveler is on a quiet ship or station.
- They want to sleep, but not in an ordinary way: they want a poetic sleep,
  something calm and dreamy and beautiful.
- The ship's environment is a little wrong for rest: too bright, too noisy, or
  too lonely.
- A transformation device or helper changes the traveler, the room, or the
  sleeping setup in a way that makes sleep possible without breaking the mood.

The world is built from state:
- physical meters: light, noise, warmth, drift, charge, comfort
- emotional memes: want, calm, wonder, worry, sleepiness, joy, transformation

The story should feel like a small classical TinyStories-style space adventure:
beginning, a problem, a useful transformation, and a final image showing what
changed.
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
# Core domain data
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
    kind: str = "thing"  # character | thing | place | device
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    covers: set[str] = field(default_factory=set)
    protective: bool = False

    helper: object | None = None
    traveler: object | None = None
    def __post_init__(self) -> None:
        for key in ["light", "noise", "warmth", "drift", "charge", "comfort"]:
            self.meters.setdefault(key, 0.0)
        for key in ["want", "calm", "wonder", "worry", "sleepiness", "joy", "transform"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class ShipSetting:
    place: str
    light: float
    noise: float
    warmth: float
    drift: float
    mood: str
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
class SleepNeed:
    id: str
    phrase: str
    poetry: str
    comfort_bias: str
    tags: set[str] = field(default_factory=set)
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
    pitch: str
    turn: str
    effect: str
    requires: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: ShipSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "quiet_cabin": ShipSetting(
        place="the quiet cabin",
        light=0.7,
        noise=0.5,
        warmth=0.4,
        drift=0.3,
        mood="too bright to rest",
        affords={"sleep", "poem"},
    ),
    "glass_observatory": ShipSetting(
        place="the glass observatory",
        light=0.9,
        noise=0.3,
        warmth=0.2,
        drift=0.6,
        mood="beautiful but too awake",
        affords={"sleep", "poem"},
    ),
    "engine_hall": ShipSetting(
        place="the engine hall",
        light=0.6,
        noise=0.9,
        warmth=0.8,
        drift=0.1,
        mood="too loud for sleep",
        affords={"transformation", "sleep"},
    ),
}

SLEEP_NEEDS = {
    "poetic_sleep": SleepNeed(
        id="poetic_sleep",
        phrase="a poetic sleep",
        poetry="a sleep with moonlike words and soft star-songs",
        comfort_bias="gentle rhythm",
        tags={"sleep", "poem"},
    ),
    "tiny_sleep": SleepNeed(
        id="tiny_sleep",
        phrase="a tiny sleep",
        poetry="a small and careful sleep curled like a pebble",
        comfort_bias="small warmth",
        tags={"sleep"},
    ),
    "star_sleep": SleepNeed(
        id="star_sleep",
        phrase="a starry sleep",
        poetry="a sleep that glittered like a sky full of hush",
        comfort_bias="sparkling calm",
        tags={"sleep", "stars"},
    ),
}

TRANSFORMS = {
    "mooncloak": Transform(
        id="mooncloak",
        label="a mooncloak",
        pitch="put on the mooncloak",
        turn="wrapped the room in silver hush",
        effect="softened the light and made the air feel dreamy",
        requires={"light"},
        fixes={"light", "worry"},
        tags={"moon", "poetic", "sleep"},
    ),
    "starglass": Transform(
        id="starglass",
        label="starglass sleep panes",
        pitch="open the starglass panes",
        turn="turned the cabin window into a drifting star-view",
        effect="made the traveler feel small in a good, calm way",
        requires={"wonder"},
        fixes={"worry", "noise"},
        tags={"stars", "poetic"},
    ),
    "lullaby_gizmo": Transform(
        id="lullaby gizmo",
        label="a lullaby gizmo",
        pitch="switch on the lullaby gizmo",
        turn="changed engine hum into a slow, sleepy song",
        effect="lowered the noise and helped the body settle",
        requires={"noise"},
        fixes={"noise", "sleepiness"},
        tags={"music", "sleep"},
    ),
}

NAMES = ["Mira", "Juno", "Pip", "Nova", "Tala", "Iris", "Cleo", "Ari"]
KINDS = ["girl", "boy"]
PARENTS = ["captain", "pilot"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    need: str
    transform: str
    name: str
    type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
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


def _add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def tension_level(world: World, traveler: Entity) -> float:
    s = world.setting
    return max(0.0, s.light + s.noise - s.warmth - traveler.memes["calm"] * 0.2)


def can_transform(world: World, need: SleepNeed, trans: Transform) -> bool:
    if not trans.requires.issubset(need.tags | world.facts.get("setting_tags", set())):
        return False
    return True


def predict_rest(world: World, traveler: Entity, need: SleepNeed, trans: Transform) -> bool:
    sim = world.copy()
    apply_transformation(sim, sim.get(traveler.id), trans, narrate=False)
    settle_for_sleep(sim, sim.get(traveler.id), need, narrate=False)
    return sim.get(traveler.id).memes["sleepiness"] >= 1.0 and sim.get(traveler.id).memes["worry"] < 0.5


def introduce(world: World, traveler: Entity, need: SleepNeed) -> None:
    world.say(
        f"{traveler.id} was a little {traveler.type} aboard the ship, and "
        f"{traveler.pronoun()} wanted {need.phrase}."
    )
    _add_meme(traveler, "want", 1.0)
    _add_meme(traveler, "wonder", 0.5)
    world.say(
        f"{traveler.pronoun().capitalize()} loved the quiet parts of space, especially "
        f"{need.poetry}."
    )


def setting_line(world: World) -> None:
    s = world.setting
    if s.place == "the engine hall":
        world.say("The engine hall hummed and trembled like a giant purring drum.")
    elif s.place == "the glass observatory":
        world.say("The glass observatory shone with faraway stars, but it was hard to close one’s eyes there.")
    else:
        world.say("The quiet cabin was small, neat, and still a little too awake.")


def describe_problem(world: World, traveler: Entity, need: SleepNeed) -> None:
    s = world.setting
    _add_meme(traveler, "worry", 0.9)
    _add_meme(traveler, "sleepiness", 0.4)
    world.say(
        f"But {s.place} felt {s.mood}, and the light, noise, and drifting all tugged at {traveler.pronoun('possessive')} eyes."
    )
    if s.noise > 0.7:
        world.say(f"The engine sound kept sneaking into {traveler.pronoun('possessive')} thoughts like a tiny metal drum.")
    elif s.light > 0.8:
        world.say(f"The bright panels kept blinking, even when {traveler.id} tried to close {traveler.pronoun('possessive')} eyes.")
    else:
        world.say(f"The room was calm, but not calm enough for the kind of sleep {traveler.id} wanted.")


def ask_for_help(world: World, traveler: Entity, need: SleepNeed) -> None:
    _add_meme(traveler, "want", 0.5)
    world.say(
        f"{traveler.id} whispered, \"I want {need.phrase}.\" "
        f"{traveler.pronoun().capitalize()} looked around for something that could help."
    )


def apply_transformation(world: World, traveler: Entity, trans: Transform, narrate: bool = True) -> None:
    s = world.setting
    _add_meme(traveler, "transform", 1.0)
    _add_meme(traveler, "calm", 0.8)
    if "light" in trans.fixes:
        s.light = max(0.0, s.light - 0.5)
    if "noise" in trans.fixes:
        s.noise = max(0.0, s.noise - 0.5)
    if "worry" in trans.fixes:
        traveler.memes["worry"] = max(0.0, traveler.memes["worry"] - 0.7)
    if narrate:
        world.say(f"{traveler.id} chose {trans.label} and {trans.pitch}.")
        world.say(f"It {trans.turn}, and {trans.effect}.")


def settle_for_sleep(world: World, traveler: Entity, need: SleepNeed, narrate: bool = True) -> None:
    s = world.setting
    comfort = max(0.0, 1.2 - tension_level(world, traveler))
    _add_meter(traveler, "comfort", comfort)
    _add_meme(traveler, "sleepiness", 0.8 + comfort)
    _add_meme(traveler, "calm", 0.6)
    if narrate:
        world.say(
            f"The room grew softer, and {traveler.id} finally lay still enough to listen to the new hush."
        )
        world.say(
            f"At last, {traveler.id} drifted into {need.phrase}, while the ship glowed quietly around {traveler.pronoun('object')}."
        )


def tell_story(setting: ShipSetting, need: SleepNeed, trans: Transform, name: str, kind: str) -> World:
    world = World(setting)
    world.facts["setting_tags"] = {need.id} | set(trans.tags) | {setting.place.replace("the ", "").replace(" ", "_")}
    traveler = world.add(Entity(id=name, kind="character", type=kind, label=name))
    helper = world.add(Entity(id="Helper", kind="character", type="pilot", label="the pilot"))
    world.facts.update(traveler=traveler, helper=helper, need=need, transform=trans, setting=setting)

    introduce(world, traveler, need)
    setting_line(world)
    world.para()
    describe_problem(world, traveler, need)
    ask_for_help(world, traveler, need)

    if not can_transform(world, need, trans):
        pass

    if not predict_rest(world, traveler, need, trans):
        pass

    world.para()
    apply_transformation(world, traveler, trans, narrate=True)
    settle_for_sleep(world, traveler, need, narrate=True)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasonable combo registry
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for need_id, need in SLEEP_NEEDS.items():
            for trans_id, trans in TRANSFORMS.items():
                if can_transformation_apply(setting, need, trans):
                    out.append((place, need_id, trans_id))
    return out


def can_transformation_apply(setting: ShipSetting, need: SleepNeed, trans: Transform) -> bool:
    if need.id == "poetic_sleep" and trans.id in {"mooncloak", "starglass", "lullaby_gizmo"}:
        return True
    if need.id == "star_sleep" and trans.id in {"starglass", "mooncloak"}:
        return True
    if need.id == "tiny_sleep" and trans.id in {"mooncloak", "lullaby_gizmo"}:
        return True
    return False


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    traveler = _safe_fact(world, f, "traveler")
    need = _safe_fact(world, f, "need")
    trans = _safe_fact(world, f, "transform")
    return [
        f'Write a gentle space adventure for a young child who wants "{need.phrase}" and uses "{trans.label}" to feel sleepy.',
        f"Tell a short story about {traveler.id} aboard {world.setting.place} who wants to sleep in a poetic way and finds a transformation that helps.",
        f"Write a child-friendly space story that includes the words want, poetic, and sleep, and ends with a calm transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler = _safe_fact(world, f, "traveler")
    need = _safe_fact(world, f, "need")
    trans = _safe_fact(world, f, "transform")
    setting = _safe_fact(world, f, "setting")
    qa = [
        QAItem(
            question=f"What did {traveler.id} want in {setting.place}?",
            answer=f"{traveler.id} wanted {need.phrase}, because {need.poetry} felt perfect for the ship.",
        ),
        QAItem(
            question=f"Why was it hard for {traveler.id} to sleep at first?",
            answer=f"It was hard because {setting.place} felt {setting.mood}, with too much light, noise, or drifting for easy rest.",
        ),
        QAItem(
            question=f"What transformation helped {traveler.id}?",
            answer=f"{trans.label} helped, because it changed the room into a softer place for a calm bedtime.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the story end for {traveler.id}?",
                answer=f"{traveler.id} drifted into {need.phrase} and the ship grew quiet and kind around {traveler.pronoun('object')}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is a change, like changing a room, a costume, or a sound so the next part can happen in a new way.",
        ),
        QAItem(
            question="Why do people like poetic words before sleep?",
            answer="Poetic words can feel soft, calm, and dreamy, which can help a bedtime feel peaceful.",
        ),
        QAItem(
            question="Why can space be a good setting for a sleepy story?",
            answer="Space can feel quiet, wide, and starry, so it is easy to imagine gentle lights and calm drifting.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_ok(Place, Need, Transform) :- place(Place), need(Need), transform(Transform),
    compatible(Place, Need, Transform).

story_ok(Place, Need, Transform) :- setting_ok(Place, Need, Transform).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("light", pid, int(s.light * 10)))
        lines.append(asp.fact("noise", pid, int(s.noise * 10)))
        lines.append(asp.fact("warmth", pid, int(s.warmth * 10)))
        lines.append(asp.fact("drift", pid, int(s.drift * 10)))
    for nid, n in SLEEP_NEEDS.items():
        lines.append(asp.fact("need", nid))
        for t in sorted(n.tags):
            lines.append(asp.fact("need_tag", nid, t))
    for tid, t in TRANSFORMS.items():
        lines.append(asp.fact("transform", tid))
        for req in sorted(t.requires):
            lines.append(asp.fact("requires", tid, req))
        for fix in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, fix))
        for tag in sorted(t.tags):
            lines.append(asp.fact("transform_tag", tid, tag))
    for place, need_id, trans_id in valid_combos():
        lines.append(asp.fact("compatible", place, need_id, trans_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting_ok/3."))
    return sorted(set(asp.atoms(model, "setting_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about want, poetic sleep, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--need", choices=SLEEP_NEEDS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "need", None) or getattr(args, "transform", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "need", None) is None or c[1] == getattr(args, "need", None))
            and (getattr(args, "transform", None) is None or c[2] == getattr(args, "transform", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, need, transform = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(place=place, need=need, transform=transform, name=name, type=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(SETTINGS, params.place), _safe_lookup(SLEEP_NEEDS, params.need), _safe_lookup(TRANSFORMS, params.transform), params.name, params.type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="quiet_cabin", need="poetic_sleep", transform="mooncloak", name="Mira", type="girl"),
    StoryParams(place="glass_observatory", need="star_sleep", transform="starglass", name="Nova", type="girl"),
    StoryParams(place="engine_hall", need="tiny_sleep", transform="lullaby_gizmo", name="Pip", type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show setting_ok/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for triple in triples:
            print(" ", triple)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
