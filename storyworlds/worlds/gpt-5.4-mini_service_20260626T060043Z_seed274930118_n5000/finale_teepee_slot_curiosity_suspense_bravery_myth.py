#!/usr/bin/env python3
"""
A small myth-like story world about a curious child, a teepee, and a
careful finale.

The premise:
- A child is drawn to a teepee during a festival finale.
- There is a narrow slot in the hide flap.
- Curiosity tempts the child to peek early.
- Suspense rises because the finale should not be spoiled.
- Bravery turns the choice from sneaking to asking.

The simulation keeps physical meters and emotional memes, then narrates the
causal turn and resolution as a short complete story.
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
# Entities and world state
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
    traits: list[str] = field(default_factory=list)

    labels: object | None = None
    elder: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
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
    name: str
    indoor: bool = False
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
class TaleNeedle:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    threshold: float = 1.0
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
class Relic:
    label: str
    phrase: str
    type: str
    slot: str
    plural: bool = False
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
class Cover:
    id: str
    label: str
    protects: set[str]
    guards: set[str]
    offer: str
    ending: str
    plural: bool = False
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.slot_seen: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "teepee_ring": Place(name="the teepee ring", indoor=False, affords={"watch", "peek", "speak"}),
    "ridge": Place(name="the hill ridge", indoor=False, affords={"watch"}),
    "campfire_circle": Place(name="the campfire circle", indoor=False, affords={"watch", "speak"}),
}

NEEDLES = {
    "curiosity": TaleNeedle(
        id="curiosity",
        verb="peek into the teepee slot",
        gerund="peeking into the teepee slot",
        rush="slip closer to the flap",
        risk="might spoil the finale",
        tags={"teepee", "slot", "curiosity"},
    ),
    "suspense": TaleNeedle(
        id="suspense",
        verb="wait for the finale",
        gerund="waiting through the suspense",
        rush="lean in and ask too soon",
        risk="might break the hush",
        tags={"finale", "suspense"},
    ),
    "bravery": TaleNeedle(
        id="bravery",
        verb="speak before the elders",
        gerund="speaking with bravery",
        rush="hide and listen in secret",
        risk="might miss the true welcome",
        tags={"bravery", "myth"},
    ),
}

RELICS = {
    "drum": Relic(label="drum", phrase="a painted drum", type="drum", slot="inside", plural=False),
    "torch": Relic(label="torch", phrase="a bright torch", type="torch", slot="outside", plural=False),
    "cloak": Relic(label="cloak", phrase="a woven cloak", type="cloak", slot="body", plural=False),
}

COVERS = [
    Cover(
        id="blanket",
        label="a story blanket",
        protects={"eyes", "feet"},
        guards={"curiosity"},
        offer="give the child a story blanket and ask them to sit beside the elders",
        ending="sat beside the fire with the story blanket around their shoulders",
    ),
    Cover(
        id="drumcover",
        label="a drum cover",
        protects={"inside"},
        guards={"suspense"},
        offer="cover the drum and tell the child to wait for the finale",
        ending="waited with the drum covered until the singing began",
    ),
    Cover(
        id="cloakwrap",
        label="a wind cloak",
        protects={"body"},
        guards={"bravery"},
        offer="wrap the child in a wind cloak and invite them to speak openly",
        ending="stood taller in the wind cloak and spoke with a steady voice",
        plural=False,
    ),
]

GIRL_NAMES = ["Mira", "Nara", "Tala", "Suri", "Ila"]
BOY_NAMES = ["Kiran", "Aro", "Batu", "Ravi", "Tovi"]
TRAITS = ["curious", "gentle", "bold", "quiet", "bright"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    need: str
    relic: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasoning helpers
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


def risk_reason(need: TaleNeedle, relic: Relic) -> bool:
    if need.id == "curiosity":
        return relic.slot in {"inside", "body"}
    if need.id == "suspense":
        return relic.slot == "inside"
    if need.id == "bravery":
        return relic.slot in {"inside", "body"}
    return False


def choose_cover(need: TaleNeedle, relic: Relic) -> Optional[Cover]:
    for cover in COVERS:
        if need.id in cover.guards and relic.slot in cover.protects:
            return cover
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for need_id in place.affords:
            need = _safe_lookup(NEEDLES, need_id)
            for relic_id, relic in RELICS.items():
                if risk_reason(need, relic) and choose_cover(need, relic):
                    out.append((place_id, need_id, relic_id))
    return out


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def _make_char(name: str, gender: str, trait: str) -> Entity:
    return Entity(
        id=name,
        kind="character",
        type="girl" if gender == "girl" else "boy",
        traits=["young", trait],
        meters={"steady": 0.0},
        memes={"curiosity": 0.0, "suspense": 0.0, "bravery": 0.0, "joy": 0.0, "fear": 0.0},
    )


def _make_elder(name: str, elder_type: str) -> Entity:
    return Entity(
        id=name,
        kind="character",
        type=elder_type,
        labels=name if False else "",
        traits=["old", "wise"],
        meters={"steady": 0.0},
        memes={"patience": 0.0, "trust": 0.0},
    )


def _tell_intro(world: World, hero: Entity, elder: Entity, relic: Entity, need: TaleNeedle) -> None:
    world.say(
        f"At {world.place.name}, {hero.id} was a {hero.traits[-1]} little {hero.type} "
        f"who loved old stories and bright firelight."
    )
    world.say(
        f"Near the great teepee, the elders kept {relic.phrase} ready for the finale, "
        f"and the hide flap had a narrow slot that tempted {hero.pronoun()}."
    )
    hero.memes[need.id] += 1
    hero.memes["curiosity"] += 1


def _build_suspense(world: World, hero: Entity, need: TaleNeedle, relic: Entity) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"The hush before the finale made {hero.id}'s chest feel tight, because "
        f"{hero.pronoun('possessive')} heart kept asking what the teepee was hiding."
    )
    world.say(
        f"{hero.id} wanted to {need.verb}, but the slot seemed like a secret that was "
        f"meant to be honored, not stolen."
    )


def _warn(world: World, elder: Entity, hero: Entity, need: TaleNeedle, relic: Entity) -> None:
    world.say(
        f"{elder.id} lifted a hand and said, \"Little one, a borrowed secret can spoil the "
        f"finale.\""
    )
    hero.memes["fear"] += 1
    hero.memes["suspense"] += 1


def _turn(world: World, hero: Entity, elder: Entity, need: TaleNeedle) -> None:
    hero.memes["bravery"] += 1
    hero.meters["steady"] += 1
    world.say(
        f"{hero.id} took one brave breath and did not slip closer at once."
    )
    world.say(
        f"Instead, {hero.pronoun()} stepped back from the slot and chose to wait for the "
        f"right moment."
    )


def _offer_cover(world: World, elder: Entity, hero: Entity, need: TaleNeedle, relic: Entity) -> Optional[Cover]:
    cover = choose_cover(need, relic)
    if cover is None:
        return None
    world.say(
        f"{elder.id} smiled and offered {cover.label}: {cover.offer}."
    )
    return cover


def _accept(world: World, hero: Entity, elder: Entity, cover: Cover, relic: Entity, need: TaleNeedle) -> None:
    hero.memes["joy"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    hero.memes["suspense"] = 0.0
    world.say(
        f"{hero.id} accepted the gift of patience, and soon {cover.ending}."
    )
    world.say(
        f"When the finale finally came, the teepee door opened, the {relic.label} sounded, "
        f"and {hero.id} saw that the waiting had been worth it."
    )
    world.say(
        f"{hero.id} stood tall beside {elder.id}, with curiosity calmed, suspense resolved, "
        f"and bravery shining like firelight."
    )


def tell(place: Place, need: TaleNeedle, relic_cfg: Relic, name: str, gender: str,
         elder_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(_make_char(name, gender, trait))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        traits=["old", "wise"],
        meters={"steady": 0.0},
        memes={"patience": 1.0, "trust": 1.0},
    ))
    relic = world.add(Entity(
        id="relic",
        kind="thing",
        type=relic_cfg.type,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        plural=relic_cfg.plural,
    ))

    _tell_intro(world, hero, elder, relic, need)
    world.para()
    _build_suspense(world, hero, need, relic)
    _warn(world, elder, hero, need, relic)
    _turn(world, hero, elder, need)
    world.para()
    cover = _offer_cover(world, elder, hero, need, relic)
    if cover is not None:
        _accept(world, hero, elder, cover, relic, need)

    world.facts.update(
        hero=hero,
        elder=elder,
        relic=relic,
        need=need,
        cover=cover,
        place=place,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    need = _safe_fact(world, f, "need")
    return [
        f'Write a myth-like story for a young child about "{need.id}", a teepee, and a finale.',
        f"Tell a gentle legend where {hero.id} wants to {need.verb} but learns to wait, ask, and be brave.",
        f"Write a short story that includes the words finale, teepee, and slot, and ends in a calm victory.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    need = _safe_fact(world, f, "need")
    relic = _safe_fact(world, f, "relic")
    cover = _safe_fact(world, f, "cover")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a young {hero.type} with a curious heart, and {elder.id}, the wise elder beside the teepee.",
        ),
        QAItem(
            question=f"What made {hero.id} want to move closer to the teepee?",
            answer=f"{hero.id} wanted to {need.verb} because the slot looked like a secret and the finale felt important.",
        ),
        QAItem(
            question=f"What was waiting for the finale?",
            answer=f"A {relic.label} was waiting for the finale, and the elders kept it ready for the right moment.",
        ),
    ]
    if cover is not None:
        qa.append(
            QAItem(
                question=f"How did the elder help {hero.id} stay brave?",
                answer=f"The elder offered {cover.label} and asked {hero.id} to wait for the proper moment, so bravery could become patience instead of sneaking.",
            )
        )
        qa.append(
            QAItem(
                question=f"What changed at the end of the story?",
                answer=f"At the end, {hero.id} was no longer tugged by suspense; {hero.id} waited peacefully until the finale arrived and the teepee opened.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "teepee": [
        QAItem(
            question="What is a teepee?",
            answer="A teepee is a cone-shaped shelter made with poles and coverings. People can sit inside it, and it often feels special in stories.",
        )
    ],
    "slot": [
        QAItem(
            question="What is a slot?",
            answer="A slot is a narrow opening or gap. People can look through a slot, but they should not always use it without permission.",
        )
    ],
    "finale": [
        QAItem(
            question="What is a finale?",
            answer="A finale is the last part of a performance or celebration. It is the ending that people wait for.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more, look closer, or ask questions.",
        )
    ],
    "suspense": [
        QAItem(
            question="What is suspense?",
            answer="Suspense is the tense feeling you get when you are waiting to find out what will happen next.",
        )
    ],
    "bravery": [
        QAItem(
            question="What is bravery?",
            answer="Bravery is the choice to do the right thing even when you feel nervous or unsure.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["need"].tags)
    tags.add("teepee")
    tags.add("slot")
    tags.add("finale")
    out: list[QAItem] = []
    for tag in ["teepee", "slot", "finale", "curiosity", "suspense", "bravery"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A need is reasonable for a relic when the relic's slot makes the temptation real.
at_risk(N, R) :- need(N), relic(R), risk_pair(N, R).

% A cover is a compatible resolution only when it guards the need and reaches
% the slot type at risk.
fix(C, N, R) :- cover(C), at_risk(N, R), guards(C, N), protects(C, S), relic_slot(R, S).

valid(P, N, R) :- place(P), affords(P, N), at_risk(N, R), fix(_, N, R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for n in sorted(p.affords):
            lines.append(asp.fact("affords", pid, n))
    for nid, n in NEEDLES.items():
        lines.append(asp.fact("need", nid))
        for t in sorted(n.tags):
            lines.append(asp.fact("tag", nid, t))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_slot", rid, r.slot))
    for c in COVERS:
        lines.append(asp.fact("cover", c.id))
        for n in sorted(c.guards):
            lines.append(asp.fact("guards", c.id, n))
        for s in sorted(c.protects):
            lines.append(asp.fact("protects", c.id, s))
    for nid, need in NEEDLES.items():
        for rid, relic in RELICS.items():
            if risk_reason(need, relic):
                lines.append(asp.fact("risk_pair", nid, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Params / generation / CLI
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    need: str
    relic: str
    name: str
    gender: str
    elder: str
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


CURATED = [
    StoryParams(place="teepee_ring", need="curiosity", relic="drum", name="Mira", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(place="teepee_ring", need="suspense", relic="drum", name="Kiran", gender="boy", elder="grandfather", trait="gentle"),
    StoryParams(place="campfire_circle", need="bravery", relic="cloak", name="Tala", gender="girl", elder="aunt", trait="bold"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like story world of a teepee finale, a slot, and brave patience.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDLES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "need", None) and getattr(args, "relic", None):
        need = _safe_lookup(NEEDLES, getattr(args, "need", None))
        relic = _safe_lookup(RELICS, getattr(args, "relic", None))
        if not (risk_reason(need, relic) and choose_cover(need, relic)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "need", None) is None or c[1] == getattr(args, "need", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, need, relic = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, need=need, relic=relic, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(NEEDLES, params.need), _safe_lookup(RELICS, params.relic),
                 params.name, params.gender, params.elder, params.trait)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(set(asp.atoms(models, 'valid')))} valid combos")
        for row in sorted(set(asp.atoms(models, "valid"))):
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.need} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
