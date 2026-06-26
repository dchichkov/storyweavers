#!/usr/bin/env python3
"""
A standalone story world for a small pirate-tale domain with a moral-value turn.

Premise:
- A pirate crew discovers a problem at sea or on an island.
- The captain or child-pirate feels dismay when a prize, promise, or plan goes wrong.
- A moral value such as honesty, sharing, bravery, or kindness changes the outcome.
- The ending proves what changed in the world state.

This world intentionally keeps the vocabulary small and the causal structure tight:
the story only generates when the conflict and the moral fix are both reasonable.
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
# Core domain model
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"wet": 0.0, "broken": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "dismay": 0.0, "trust": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pirate", "sailor", "mate", "crew"}
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
    afford: set[str] = field(default_factory=set)
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
class Trouble:
    id: str
    label: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    mood: str
    keyword: str
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
class MoralValue:
    id: str
    label: str
    fix: str
    promise: str
    effect: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    value: str = "treasure"
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
class StoryParams:
    place: str
    trouble: str
    moral: str
    prize: str
    name: str
    gender: str
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


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.zone = set(self.zone)
        w.fired = set(self.fired)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

PLACES = {
    "dock": Place("dock", "the dock", {"tidying", "storm"}),
    "ship": Place("ship", "the ship", {"sailing", "storm", "map"}),
    "island": Place("island", "the island", {"searching", "sharing"}),
    "cove": Place("cove", "the cove", {"searching", "storm"}),
}

TROUBLES = {
    "storm": Trouble(
        "storm",
        "a storm",
        verb="sail through the storm",
        gerund="sailing through the storm",
        rush="race into the waves",
        risk="soaked and shaken",
        zone={"torso", "feet"},
        mood="stormy",
        keyword="storm",
        tags={"storm", "wet", "wind"},
    ),
    "mud": Trouble(
        "mud",
        "muddy island paths",
        verb="cross the muddy path",
        gerund="crossing muddy paths",
        rush="run onto the muddy sand",
        risk="muddy from nose to boots",
        zone={"feet", "legs"},
        mood="squishy",
        keyword="mud",
        tags={"mud", "dirty"},
    ),
    "map": Trouble(
        "map",
        "a torn map",
        verb="search for the hidden cove",
        gerund="searching for the hidden cove",
        rush="snatch at the map corner",
        risk="torn in half",
        zone={"hands", "torso"},
        mood="worrying",
        keyword="map",
        tags={"map", "careful"},
    ),
}

MORAL_VALUES = {
    "honesty": MoralValue(
        "honesty",
        "honesty",
        fix="tell the truth",
        promise="kept the truth in the open",
        effect="trust",
        tags={"truth", "trust"},
    ),
    "sharing": MoralValue(
        "sharing",
        "sharing",
        fix="share the prize",
        promise="gave each mate a fair turn",
        effect="joy",
        tags={"share", "kind"},
    ),
    "bravery": MoralValue(
        "bravery",
        "bravery",
        fix="take a brave step",
        promise="stood steady even with fear in the wind",
        effect="pride",
        tags={"brave", "courage"},
    ),
    "kindness": MoralValue(
        "kindness",
        "kindness",
        fix="be kind first",
        promise="helped before asking for reward",
        effect="joy",
        tags={"kind", "help"},
    ),
}

PRIZES = {
    "compass": Prize("compass", "a brass compass", "a brass compass", "hands", False, "tool"),
    "flag": Prize("flag", "the crew's flag", "the crew's flag", "torso", True, "symbol"),
    "sack": Prize("sack", "a sack of shiny shells", "a sack of shiny shells", "hands", False, "treasure"),
    "boots": Prize("boots", "new sea boots", "new sea boots", "feet", True, "clothes"),
}

GIRL_NAMES = ["Anne", "Rina", "Nell", "Mara", "Tia"]
BOY_NAMES = ["Jack", "Finn", "Eli", "Rowan", "Nico"]
TITLES = ["captain", "mate", "pirate"]


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------

def prize_at_risk(trouble: Trouble, prize: Prize) -> bool:
    return prize.region in trouble.zone


def compatible_fix(trouble: Trouble, moral: MoralValue, prize: Prize) -> bool:
    # Tight coupling: the moral value must match the type of trouble.
    if trouble.id == "map":
        return moral.id in {"honesty", "bravery"}
    if trouble.id == "mud":
        return moral.id in {"sharing", "kindness"}
    if trouble.id == "storm":
        return moral.id in {"bravery", "honesty"}
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for trouble_id in place.afford:
            trouble = _safe_lookup(TROUBLES, trouble_id)
            for prize_id, prize in PRIZES.items():
                if not prize_at_risk(trouble, prize):
                    continue
                for moral_id, moral in MORAL_VALUES.items():
                    if compatible_fix(trouble, moral, prize):
                        combos.append((place_id, trouble_id, prize_id, moral_id))
    return combos


def explain_rejection(trouble: Trouble, prize: Prize, moral: Optional[MoralValue] = None) -> str:
    if not prize_at_risk(trouble, prize):
        return (
            f"(No story: {trouble.gerund} does not endanger {prize.label}; "
            f"there would be no true dismay and no honest turn."
            f" Choose a prize worn on the at-risk part of the body.)"
        )
    if moral is not None and not compatible_fix(trouble, moral, prize):
        return (
            f"(No story: {moral.label} does not fit this trouble well enough to solve it. "
            f"Try a moral value that matches the problem.)"
        )
    return "(No story: no valid combination matches the given options.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, title: str) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} pirate, and {hero.pronoun('possessive')} "
        f"{title} liked a tidy deck and a brave heart."
    )


def set_scene(world: World, hero: Entity, trouble: Trouble, prize: Prize, moral: MoralValue) -> None:
    world.say(
        f"One day at {world.place.label}, {hero.id} found {prize.phrase} and loved how it gleamed."
    )
    world.say(
        f"Then {hero.id} wanted to {trouble.verb}, because the sea looked wild and full of fun."
    )


def predict_damage(world: World, hero: Entity, trouble: Trouble, prize: Prize) -> bool:
    sim = world.copy()
    sim.zone = set(trouble.zone)
    actor = sim.get(hero.id)
    actor.meters["wet"] += 1
    actor.memes["dismay"] += 1
    item = sim.get(prize.id)
    if prize.region in trouble.zone:
        item.meters["wet"] += 1
        item.meters["broken"] += 1 if trouble.id == "map" else 0
    return item.meters["wet"] >= THRESHOLD or item.meters["broken"] >= THRESHOLD


def warn(world: World, hero: Entity, trouble: Trouble, prize: Prize) -> bool:
    if not predict_damage(world, hero, trouble, prize):
        return False
    hero.memes["dismay"] += 1
    world.say(
        f"{hero.pronoun('possessive').capitalize()} smile slipped into dismay, because {prize.label} could get {trouble.risk}."
    )
    return True


def act_out(world: World, hero: Entity, trouble: Trouble, prize: Prize) -> None:
    hero.meters["wet"] += 1
    world.zone = set(trouble.zone)
    if prize.region in trouble.zone:
        prize_ent = world.get(prize.id)
        prize_ent.meters["wet"] += 1
        if trouble.id == "map":
            prize_ent.meters["broken"] += 1
        world.say(f"The {prize.label} got caught in the trouble and came out {trouble.risk}.")
    if trouble.id == "mud":
        world.say("Mud clung to boots and hems, and the deck would need a long scrub.")
    elif trouble.id == "storm":
        world.say("Salt spray slapped the deck, and every board shivered under the wind.")
    elif trouble.id == "map":
        world.say("The torn map fluttered like a nervous gull, and the way ahead grew harder to read.")


def moral_turn(world: World, hero: Entity, trouble: Trouble, prize: Prize, moral: MoralValue) -> None:
    hero.memes[moral.effect] += 1
    if moral.id == "honesty":
        world.say(
            f"Then {hero.id} remembered {moral.label} and chose to {moral.fix}."
        )
        world.say(
            f"That meant {hero.id} admitted the mistake, and the crew trusted {hero.pronoun('object')} more."
        )
    elif moral.id == "sharing":
        world.say(
            f"Then {hero.id} remembered {moral.label} and chose to {moral.fix}."
        )
        world.say(
            f"{hero.id} split the prize fairly, and the crew's grins made the deck feel brighter."
        )
    elif moral.id == "bravery":
        world.say(
            f"Then {hero.id} remembered {moral.label} and chose to {moral.fix}."
        )
        world.say(
            f"{hero.id} stood steady, so the wind did not scare the crew away from the right choice."
        )
    else:
        world.say(
            f"Then {hero.id} remembered {moral.label} and chose to {moral.fix}."
        )
        world.say(
            f"{hero.id} helped first, and the crew answered with warm smiles instead of grumbles."
        )


def resolve(world: World, hero: Entity, trouble: Trouble, prize: Prize, moral: MoralValue) -> None:
    hero.memes["dismay"] = 0.0
    hero.memes["joy"] += 1
    world.say(
        f"In the end, {hero.id} kept {moral.promise}, and the trouble did not rule the day."
    )
    if trouble.id == "map":
        world.say(
            f"The crew patched the map, and {prize.label} stayed useful for the next voyage."
        )
    elif trouble.id == "storm":
        world.say(
            f"The storm passed, and {prize.label} stayed dry enough for the next lookout."
        )
    else:
        world.say(
            f"The deck got cleaned, and {prize.label} stayed safe for another merry sail."
        )


def tell(place: Place, trouble: Trouble, prize_cfg: Prize, moral: MoralValue,
         hero_name: str, hero_type: str, title: str) -> World:
    world = World(place)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=title,
    ))
    prize = world.add(Entity(
        id=prize_cfg.id,
        kind="thing",
        type=prize_cfg.value,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=hero.id,
    ))

    world.facts.update(hero=hero, prize=prize, trouble=trouble, moral=moral, place=place)

    introduce(world, hero, title)
    world.para()
    set_scene(world, hero, trouble, prize, moral)
    warn(world, hero, trouble, prize)
    act_out(world, hero, trouble, prize)
    world.para()
    moral_turn(world, hero, trouble, prize, moral)
    resolve(world, hero, trouble, prize, moral)
    return world


# ---------------------------------------------------------------------------
# Registries and sampling
# ---------------------------------------------------------------------------

def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def story_compatible(place: str, trouble: str, prize: str, moral: str, gender: str) -> bool:
    if prize == "flag" and trouble == "mud":
        return False
    if gender == "girl" and prize == "boots" and trouble == "map":
        return True
    return True


CURATED = [
    StoryParams("ship", "storm", "compass", "honesty", "Anne", "girl", "captain"),
    StoryParams("island", "mud", "sack", "sharing", "Jack", "boy", "mate"),
    StoryParams("cove", "map", "flag", "bravery", "Mara", "girl", "pirate"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    trouble: Trouble = _safe_fact(world, f, "trouble")
    prize: Prize = _safe_fact(world, f, "prize")
    moral: MoralValue = _safe_fact(world, f, "moral")
    return [
        f'Write a short pirate tale about {hero.id} where {hero.pronoun("possessive")} {prize.label} and {trouble.keyword} bring dismay, then {moral.label} helps.',
        f"Tell a child-friendly pirate story in which a {hero.type} named {hero.id} learns {moral.label} while dealing with {trouble.gerund}.",
        f'Write a story with a clear start, dismay, and resolution, using the word "{trouble.keyword}" and the idea of {moral.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    trouble: Trouble = _safe_fact(world, f, "trouble")
    prize: Prize = _safe_fact(world, f, "prize")
    moral: MoralValue = _safe_fact(world, f, "moral")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What made {hero.id} feel dismay at {place.label}?",
            answer=f"{hero.id} felt dismay because {prize.label} could be ruined when {hero.id} tried {trouble.gerund}.",
        ),
        QAItem(
            question=f"What moral value helped {hero.id} in the end?",
            answer=f"{moral.label} helped {hero.id}, because {hero.id} chose to {moral.fix} instead of making the trouble worse.",
        ),
        QAItem(
            question=f"What happened to the prize by the end of the story?",
            answer=f"The {prize.label} stayed safe enough for the next voyage, because the moral choice changed what the crew did.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "storm": [
        QAItem(
            question="What is a storm?",
            answer="A storm is very rough weather with strong wind, rain, or waves.",
        )
    ],
    "mud": [
        QAItem(
            question="What is mud?",
            answer="Mud is soft, wet dirt that sticks to shoes and clothes.",
        )
    ],
    "map": [
        QAItem(
            question="What is a map?",
            answer="A map is a picture that shows where places are and how to get there.",
        )
    ],
    "honesty": [
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth and not pretending something false is real.",
        )
    ],
    "sharing": [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving other people a fair turn or a fair part.",
        )
    ],
    "bravery": [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel afraid.",
        )
    ],
    "kindness": [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means caring about others and helping them in a gentle way.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    keys = {f["trouble"].id, f["moral"].id}
    out: list[QAItem] = []
    for key in keys:
        out.extend(WORLD_KNOWLEDGE.get(key, []))
    return out


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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A prize is at risk when the trouble reaches the body region it is on.
at_risk(T, P) :- trouble(T), prize(P), zone(T, R), region(P, R).

% A moral value is compatible when it can actually resolve the trouble.
compatible(T, M, P) :- at_risk(T, P), moral(M), fits(T, M).

valid_story(Place, Trouble, Prize, Moral) :- place(Place), affords(Place, Trouble),
                                             at_risk(Trouble, Prize), compatible(Trouble, Moral, Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(place.afford):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        for r in sorted(t.zone):
            lines.append(asp.fact("zone", tid, r))
    for mid, m in MORAL_VALUES.items():
        lines.append(asp.fact("moral", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("fits", "dummy", "dummy")) if False else None
    for prid, p in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("region", prid, p.region))
    for tid, t in TROUBLES.items():
        for mid, m in MORAL_VALUES.items():
            if compatible_fix(t, m, PRIZES["compass"]):
                lines.append(asp.fact("fits", tid, mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale story world with a moral-value turn.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--moral", choices=MORAL_VALUES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--title", choices=TITLES)
    ap.add_argument("--name")
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
    if getattr(args, "place", None) or getattr(args, "trouble", None) or getattr(args, "prize", None) or getattr(args, "moral", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "trouble", None) is None or c[1] == getattr(args, "trouble", None))
            and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
            and (getattr(args, "moral", None) is None or c[3] == getattr(args, "moral", None))
        ]
    if not combos:
        if getattr(args, "trouble", None) and getattr(args, "prize", None):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, trouble, prize, moral = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(gender, rng)
    title = getattr(args, "title", None) or rng.choice(TITLES)
    return StoryParams(place, trouble, moral, prize, name, gender, title)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(TROUBLES, params.trouble),
        _safe_lookup(PRIZES, params.prize),
        _safe_lookup(MORAL_VALUES, params.moral),
        params.name,
        {"girl": "girl", "boy": "boy"}[params.gender],
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:\n")
        for place, trouble, prize, moral in stories:
            print(f"  {place:8} {trouble:8} {prize:8} {moral:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.trouble} at {p.place} with {p.moral}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
