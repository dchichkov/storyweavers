#!/usr/bin/env python3
"""
storyworlds/worlds/inlet_shuffle_sound_effects_nursery_rhyme.py
===============================================================

A small nursery-rhyme storyworld about a windy inlet, a careful shuffle,
and a few sound effects that turn worry into play.

Seed tale:
---
A little child comes to a quiet inlet where the pebbles click and the reeds
whisper. The child wants to make a loud shuffle across the shore, but the
little boat nearby is sleeping, and the gulls are skittish. A grown-up suggests
a gentler way: shuffle softly, listen to the water's hush, and answer the
sounds like a rhyme. The child tries it, the inlet becomes a singing place,
and the boat rocks happily instead of startling.
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

RHYME_TEMPLATES = [
    "tip-tap",
    "shoo-shoo",
    "clink-clink",
    "swish-swish",
    "hush-hush",
]

SOUND_EFFECTS = {
    "pebbles": "clink-clink",
    "water": "shoo-shoo",
    "reeds": "swish-swish",
    "boat": "hush-hush",
    "steps": "tip-tap",
}

PLACES = {
    "inlet": {"name": "the inlet", "watery": True, "affords": {"shuffle", "listen"}},
    "shore": {"name": "the shore of the inlet", "watery": True, "affords": {"shuffle", "listen"}},
    "dock": {"name": "the little dock", "watery": True, "affords": {"shuffle", "listen"}},
    "bank": {"name": "the grassy bank", "watery": False, "affords": {"shuffle", "listen"}},
}

CHARACTER_NAMES = ["Mina", "Toby", "Lila", "Pip", "Nora", "Sami", "Ivy", "Jude"]
GROWNUP_NAMES = ["Mama", "Papa", "Auntie", "Uncle", "Grandma", "Grandpa"]
MOODS = ["curious", "gentle", "bright", "lively", "cheery"]



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    boat: object | None = None
    grownup: object | None = None
    hero: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
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
    key: str
    name: str
    watery: bool
    affords: set[str] = field(default_factory=set)
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
class Action:
    key: str
    verb: str
    gerund: str
    rush: str
    effect: str
    sound: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Prize:
    key: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
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
class Gear:
    key: str
    label: str
    phrase: str
    covers: set[str]
    softens: set[str]
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: callable
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


THRESHOLD = 1.0


def _r_shuffle_makes_sound(world: World) -> list[str]:
    out = []
    actor = world.get(world.facts["hero"].id)
    if actor.meters["shuffle"] < THRESHOLD:
        return out
    sig = ("sound", actor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["sound_made"] = True
    out.append(f"{SOUND_EFFECTS['steps']}, went the little steps.")
    return out


def _r_startle_boat(world: World) -> list[str]:
    out = []
    boat = world.entities.get("boat")
    actor = world.get(world.facts["hero"].id)
    if not boat:
        return out
    if actor.meters["loud"] < THRESHOLD:
        return out
    sig = ("startle", boat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boat.memes["worry"] = 1
    out.append("The boat gave a tiny wobble-wobble.")
    return out


def _r_gentle_fix(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"].id)
    grownup = world.get(world.facts["grownup"].id)
    if hero.meters["listen"] < THRESHOLD:
        return out
    sig = ("fix", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["calm"] += 1
    grownup.memes["delight"] += 1
    boat = world.entities.get("boat")
    if boat:
        boat.memes["worry"] = 0
    out.append(f"{SOUND_EFFECTS['water']}, said the water, and the worry washed away.")
    return out


CAUSAL_RULES = [
    Rule("shuffle_sound", _r_shuffle_makes_sound),
    Rule("startle_boat", _r_startle_boat),
    Rule("gentle_fix", _r_gentle_fix),
]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


def build_place(key: str) -> Place:
    p = _safe_lookup(PLACES, key)
    return Place(key=key, name=p["name"], watery=p["watery"], affords=set(p["affords"]))


ACTIONS = {
    "shuffle": Action(
        key="shuffle",
        verb="shuffle along the shore",
        gerund="shuffling along",
        rush="stomp too hard",
        effect="made a busy little sound",
        sound=SOUND_EFFECTS["steps"],
        zone={"feet"},
        tags={"sound", "movement", "shore"},
    ),
    "listen": Action(
        key="listen",
        verb="listen to the inlet",
        gerund="listening closely",
        rush="cover both ears",
        effect="made the hush easy to hear",
        sound=SOUND_EFFECTS["water"],
        zone=set(),
        tags={"sound", "quiet", "water"},
    ),
}

PRIZES = {
    "shell": Prize(
        key="shell",
        label="shell",
        phrase="a smooth little shell",
        region="hand",
    ),
    "boat": Prize(
        key="boat",
        label="boat",
        phrase="a tiny toy boat",
        region="water",
    ),
    "ribbon": Prize(
        key="ribbon",
        label="ribbon",
        phrase="a bright ribbon",
        region="hand",
    ),
}

GEAR = {
    "softshoes": Gear(
        key="softshoes",
        label="soft shoes",
        phrase="soft shoes that hush the steps",
        covers={"feet"},
        softens={"shuffle"},
    ),
    "hands": Gear(
        key="hands",
        label="gentle hands",
        phrase="gentle hands for careful play",
        covers={"hand"},
        softens={"listen"},
    ),
}


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    grownup: str
    mood: str
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


def reasonableness_gate(place: str, action: str, prize: str) -> bool:
    if action == "shuffle" and prize == "boat":
        return True
    if action == "shuffle" and prize == "shell":
        return True
    if action == "listen" and prize in {"boat", "shell", "ribbon"}:
        return True
    return False


def explain_rejection(place: str, action: str, prize: str) -> str:
    return (
        f"(No story: at {_safe_lookup(PLACES, place)['name']}, the action '{action}' and prize '{prize}' "
        f"do not make a gentle nursery-rhyme problem and fix.)"
    )


def select_gear(action: str) -> Optional[Gear]:
    if action == "shuffle":
        return GEAR["softshoes"]
    if action == "listen":
        return GEAR["hands"]
    return None


def predict(world: World, hero: Entity, action: Action) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters[action.key] += 1
    if action.key == "shuffle":
        sim.get(hero.id).meters["loud"] += 1
    propagate(sim)
    boat = sim.entities.get("boat")
    return {"boat_worried": bool(boat and boat.memes.get("worry", 0) >= THRESHOLD)}


def tell(place: Place, action: Action, prize: Prize, name: str, grownup_name: str, mood: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type="child"))
    grownup = world.add(Entity(id=grownup_name, kind="character", type="adult"))
    boat = world.add(Entity(id="boat", type="boat", label="little boat"))
    prize_ent = world.add(Entity(id=prize.key, type=prize.key, label=prize.label, phrase=prize.phrase, owner=name))

    world.facts.update(hero=hero, grownup=grownup, boat=boat, prize=prize_ent, action=action, mood=mood)

    world.say(f"{name} came to {place.name}, where the reeds went {SOUND_EFFECTS['reeds']}.")
    world.say(f"{name} was {mood}, and the little boat by the water was resting so still.")
    world.say(f"{name} loved {action.gerund}, and the inlet answered with {action.sound}.")
    world.say(f"Near the water sat {prize.phrase}, bright as a wink.")

    world.para()
    world.say(f"Then {name} wanted to {action.verb}, but {grownup_name} watched the boat and listened hard.")
    if action.key == "shuffle":
        world.say(f'"Do not {action.rush}," said {grownup_name}, "or the boat may wobble."')
        hero.meters["shuffle"] += 1
        hero.meters["loud"] += 1
        hero.memes["want"] += 1
        propagate(world)
    else:
        world.say(f'"Be gentle," said {grownup_name}, "and let the inlet sing softly."')
        hero.meters["listen"] += 1
        hero.memes["want"] += 1
        propagate(world)

    world.para()
    gear = select_gear(action.key)
    if gear:
        world.say(f"{grownup_name} brought out {gear.phrase}.")
        if action.key == "shuffle":
            hero.meters["shuffle"] += 1
            hero.meters["loud"] = 0
        else:
            hero.meters["listen"] += 1
        hero.memes["calm"] += 1
        grownup.memes["delight"] += 1
        world.say(f"{name} tried again, and this time the sound came out tiny and neat.")
        world.say(f"{SOUND_EFFECTS['pebbles']}, went the pebbles. {SOUND_EFFECTS['water']}, went the tide.")
        world.say(f"The boat stayed happy and still, and {name} kept the rhythm like a nursery rhyme.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a nursery-rhyme style story about {hero.id} at {world.place.name} with sound effects like "{SOUND_EFFECTS["steps"]}" and "{SOUND_EFFECTS["water"]}".',
        f'Tell a tiny story where a child named {hero.id} wants to shuffle at an inlet, but a grown-up suggests a gentler rhythm.',
        f'Write a gentle tale about a quiet inlet, a small boat, and a child learning to make careful sounds.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    grownup = _safe_fact(world, f, "grownup")
    action = _safe_fact(world, f, "action")
    boat = _safe_fact(world, f, "boat")
    prize = _safe_fact(world, f, "prize")
    qa = [
        QAItem(
            question=f"Where did {hero.id} go in the story?",
            answer=f"{hero.id} went to {world.place.name}, where the water and reeds made soft sounds.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the inlet?",
            answer=f"{hero.id} wanted to {action.verb}, which made a little sound that could startle the boat.",
        ),
        QAItem(
            question=f"Who helped {hero.id} keep the play gentle?",
            answer=f"{grownup.id} helped {hero.id} by choosing a softer way to play and listen.",
        ),
        QAItem(
            question=f"What small thing stayed safe and happy at the end?",
            answer=f"The little boat stayed safe and happy, and {prize.label} still looked bright near the shore.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an inlet?", answer="An inlet is a small arm of water that reaches into the land."),
        QAItem(question="What does shuffle mean?", answer="To shuffle means to move your feet with small, sliding steps."),
        QAItem(question="Why do sound effects help in stories?", answer="Sound effects help readers imagine what the place and the action feel like."),
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pk, p in PLACES.items():
        lines.append(asp.fact("place", pk))
        if p["watery"]:
            lines.append(asp.fact("watery", pk))
        for a in sorted(p["affords"]):
            lines.append(asp.fact("affords", pk, a))
    for ak, a in ACTIONS.items():
        lines.append(asp.fact("action", ak))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", ak, z))
    for pk, pr in PRIZES.items():
        lines.append(asp.fact("prize", pk))
        lines.append(asp.fact("worn_on", pk, pr.region))
    for gk, g in GEAR.items():
        lines.append(asp.fact("gear", gk))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gk, c))
        for s in sorted(g.softens):
            lines.append(asp.fact("softens", gk, s))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A,P) :- action(A), prize(P), zone(A,R), worn_on(P,R).
has_fix(A,P) :- at_risk(A,P), gear(G), softens(G,A), covers(G,R), worn_on(P,R).
valid(P,A,Pr) :- place(P), action(A), prize(Pr), affords(P,A), (A = listen; at_risk(A,Pr)), has_fix(A,Pr).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pk, p in PLACES.items():
        for ak in ACTIONS:
            for pr in PRIZES:
                if p["watery"] and reasonableness_gate(pk, ak, pr):
                    combos.append((pk, ak, pr))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        asp_set = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python-only:", sorted(py - asp_set))
    print("asp-only:", sorted(asp_set - py))
    return 1


CURATED = [
    StoryParams(place="inlet", action="shuffle", prize="boat", name="Mina", grownup="Mama", mood="curious"),
    StoryParams(place="shore", action="shuffle", prize="shell", name="Toby", grownup="Papa", mood="lively"),
    StoryParams(place="dock", action="listen", prize="ribbon", name="Lila", grownup="Auntie", mood="gentle"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld of an inlet, a shuffle, and sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--grownup", choices=GROWNUP_NAMES)
    ap.add_argument("--mood", choices=MOODS)
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
    combos = [
        (p, a, pr)
        for p, a, pr in valid_combos()
        if (getattr(args, "place", None) is None or getattr(args, "place", None) == p)
        and (getattr(args, "action", None) is None or getattr(args, "action", None) == a)
        and (getattr(args, "prize", None) is None or getattr(args, "prize", None) == pr)
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "action", None) and getattr(args, "prize", None) and not reasonableness_gate(getattr(args, "place", None), getattr(args, "action", None), getattr(args, "prize", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        action=action,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(CHARACTER_NAMES),
        grownup=getattr(args, "grownup", None) or rng.choice(GROWNUP_NAMES),
        mood=getattr(args, "mood", None) or rng.choice(MOODS),
    )


def generate(params: StoryParams) -> StorySample:
    place = build_place(params.place)
    action = _safe_lookup(ACTIONS, params.action)
    prize = _safe_lookup(PRIZES, params.prize)
    world = tell(place, action, prize, params.name, params.grownup, params.mood)
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
        print(f"{len(valid_combos())} compatible combos")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
