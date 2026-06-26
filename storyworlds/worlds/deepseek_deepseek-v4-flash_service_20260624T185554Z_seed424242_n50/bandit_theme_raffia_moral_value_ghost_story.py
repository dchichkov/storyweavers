#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/bandit_theme_raffia_moral_value_ghost_story.py
============================================================================================================================

A standalone story world sketch for "The Bandit & the Raffia Basket" – a ghost story
with a moral value. The domain models a bandit tempted to steal a raffia basket and the
ghost of its former owner who teaches him a lesson.

Causal state updates:
---
    do activity (steal)        -> basket.stolen = 1
                                 bandit.greed += 1
                                 ghost.anger += 1
    ghost appears (if stolen)  -> bandit.fear += 1
                                 ghost.presence += 1
    ghost warns                -> bandit.defiance += 1  (if ignored)
    bandit returns basket      -> basket.stolen = 0
                                 bandit.remorse += 1
                                 ghost.anger -= 1
                                 ghost.compassion += 1
                                 bandit.moral_learned += 1
    bandit learns moral        -> bandit.greed → 0
                                 ghost.presence → 0
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MORAL_THEMES = {"honesty", "kindness", "sharing", "gratitude"}


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
    kind: str = "thing"        # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None    # not used here
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    # meters (physical / factual) and memes (emotional / moral)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    bandit: object | None = None
    basket: object | None = None
    ghost: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"ghost_of_mother", "ghost_of_grandmother"}
        male = {"bandit", "ghost_of_father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
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
    place: str = "the village market"
    indoor: bool = False
    affords: set[str] = field(default_factory=lambda: {"steal", "return"})
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
class Activity:
    id: str
    verb: str          # after "wanted to ..."
    gerund: str        # after "loved ... and ..."
    rush: str          # after "tried to ..."
    mess: str          # moral stain key
    soil: str          # how the prize gets ruined (moral)
    zone: set[str]     # not physically meaningful here; kept for structure
    weather: str = "foggy"
    keyword: str = ""
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
class Basket:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"bandit"})
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
class MoralLesson:
    """The ghost's intervention – the 'gear' that protects the basket from being stolen."""
    id: str
    label: str
    covers: set[str]          # not used physically
    guards: set[str]          # the moral stain it neutralises
    prep: str                 # ghost's offer
    tail: str                 # resolution action
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_stain(world: World) -> list[str]:
    """Stealing stains the basket and angers the ghost."""
    out: list[str] = []
    for basket in list(world.entities.values()):
        if basket.meters["stolen"] >= THRESHOLD:
            continue
        # If the bandit's greed crossed threshold, the basket is stolen.
        bandit = world.get("Bandit")
        if bandit and bandit.memes["greed"] >= THRESHOLD and basket.type == "basket":
            sig = ("steal", basket.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            basket.meters["stolen"] = 1.0
            bandit.memes["greed"] += 1
            ghost = world.get("Ghost")
            if ghost:
                ghost.memes["anger"] += 1
            out.append(f"The raffia basket was stolen, and a cold wind blew through the market.")
    return out


def _r_appear(world: World) -> list[str]:
    """If basket stolen and ghost not yet appeared, ghost manifests."""
    out: list[str] = []
    ghost = world.get("Ghost")
    if not ghost or ghost.memes["presence"] >= THRESHOLD:
        return out
    for basket in list(world.entities.values()):
        if basket.meters["stolen"] >= THRESHOLD:
            sig = ("appear",)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ghost.memes["presence"] = 1.0
            bandit = world.get("Bandit")
            if bandit:
                bandit.memes["fear"] += 1
            out.append("A shimmering figure appeared – the ghost of the person who once owned the basket.")
    return out


def _r_warning(world: World) -> list[str]:
    """If ghost is present and bandit has not yet listened, ghost warns."""
    out: list[str] = []
    ghost = world.get("Ghost")
    bandit = world.get("Bandit")
    if not ghost or not bandit:
        return out
    if ghost.memes["presence"] >= THRESHOLD and ghost.memes["anger"] >= THRESHOLD:
        sig = ("warn", bandit.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        bandit.memes["defiance"] += 1
        out.append('"That basket is not yours to take," whispered the ghost. "Return it, and learn to be honest."')
    return out


def _r_remorse(world: World) -> list[str]:
    """If bandit has high defiance and the ghost's compassion is low, the bandit may feel remorse."""
    out: list[str] = []
    bandit = world.get("Bandit")
    ghost = world.get("Ghost")
    if not bandit or not ghost:
        return out
    if bandit.memes["defiance"] >= THRESHOLD and ghost.memes["compassion"] < THRESHOLD:
        sig = ("remorse", bandit.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        bandit.memes["remorse"] += 1
        ghost.memes["anger"] -= 1
        ghost.memes["compassion"] += 1
        out.append("The bandit lowered his eyes. He felt a strange warmth – the ghost was not angry, only sad.")
    return out


def _r_moral_lesson(world: World) -> list[str]:
    """If remorse is high, the bandit learns the moral value and returns the basket."""
    out: list[str] = []
    bandit = world.get("Bandit")
    ghost = world.get("Ghost")
    if not bandit or not ghost:
        return out
    if bandit.memes["remorse"] >= THRESHOLD and ghost.memes["compassion"] >= THRESHOLD:
        sig = ("lesson", bandit.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        # The moral theme is stored in world.facts
        theme = world.facts.get("moral_theme", "honesty")
        bandit.memes["greed"] = 0.0
        bandit.memes["moral_learned"] = 1.0
        ghost.memes["presence"] = 0.0
        # Return the basket
        basket = world.get("Basket")
        if basket:
            basket.meters["stolen"] = 0.0
        out.append(f"The ghost smiled. 'Now you understand the value of {theme}.' "
                   "The bandit gently placed the raffia basket back where it belonged.")
    return out


CAUSAL_RULES = [
    Rule(name="stain", tag="physical", apply=_r_stain),
    Rule(name="appear", tag="ghostly", apply=_r_appear),
    Rule(name="warning", tag="ghostly", apply=_r_warning),
    Rule(name="remorse", tag="moral", apply=_r_remorse),
    Rule(name="moral_lesson", tag="moral", apply=_r_moral_lesson),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__skip__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def basket_can_be_stolen(basket: Basket) -> bool:
    """All raffia baskets can be stolen."""
    return True


def moral_lesson_exists(activity: Activity, moral_theme: str) -> bool:
    """Every moral theme has a lesson (the ghost)."""
    return moral_theme in MORAL_THEMES


# ---------------------------------------------------------------------------
# Prediction (not used in this world, but kept for consistency)
# ---------------------------------------------------------------------------
def predict_outcome(world: World, bandit: Entity, basket_id: str) -> dict:
    sim = world.copy()
    bandit_sim = sim.get(bandit.id)
    if bandit_sim:
        bandit_sim.memes["greed"] += 1
    propagate(sim, narrate=False)
    basket = sim.entities.get(basket_id)
    return {
        "stolen": bool(basket and basket.meters["stolen"] >= THRESHOLD),
        "ghost_angry": sim.get("Ghost").memes["anger"] if sim.get("Ghost") else 0,
    }


# ---------------------------------------------------------------------------
# Narrative verbs
# ---------------------------------------------------------------------------
def introduce(world: World, bandit: Entity, moral_theme: str) -> None:
    world.say(f"Once, in a foggy village, there lived a {bandit.type} named {bandit.id}.")
    world.say(f"He had a rough life and often thought of taking things that were not his.")
    world.facts["moral_theme"] = moral_theme


def describe_raffia(world: World, basket: Entity) -> None:
    world.say(f"In the market, a beautiful raffia {basket.label} sat on a stall.")
    world.say(f"It was woven with golden fibers, and everyone said it belonged to an old woman who had passed away.")


def bandit_wants(world: World, bandit: Entity, activity: Activity) -> None:
    bandit.memes["greed"] += 0.5
    world.say(f"{bandit.id} wanted to {activity.verb} – his fingers itched for the raffia basket.")


def bandit_steals(world: World, bandit: Entity, activity: Activity) -> None:
    bandit.memes["greed"] += 1
    propagate(world)
    world.say(f"When no one was looking, he grabbed the basket and hid it under his coat.")


def ghost_appears_and_warns(world: World, ghost: Entity) -> None:
    propagate(world)


def bandit_defies(world: World, bandit: Entity) -> None:
    bandit.memes["defiance"] += 1
    world.say(f"But {bandit.id} shook his head. 'It's mine now,' he muttered.")


def ghost_pleads(world: World, ghost: Entity) -> None:
    propagate(world)


def bandit_relents(world: World, bandit: Entity, basket: Entity) -> None:
    propagate(world)


def resolution(world: World, bandit: Entity, basket: Entity, ghost: Entity, moral_theme: str) -> None:
    world.say(f"{bandit.id} returned the raffia basket to the market. The ghost faded away, and the fog lifted.")
    world.say(f"From that day, {bandit.id} never stole again, for he had learned the value of {moral_theme}.")


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, basket_cfg: Basket,
         bandit_name: str = "Kael", bandit_type: str = "bandit",
         ghost_type: str = "ghost_of_mother", moral_theme: str = "honesty") -> World:
    world = World(setting)
    world.weather = "foggy"

    bandit = world.add(Entity(
        id=bandit_name, kind="character", type=bandit_type,
        traits=["greedy", "stubborn", "poor"],
    ))
    ghost = world.add(Entity(
        id="Ghost", kind="character", type=ghost_type,
        traits=["sad", "wise", "patient"],
    ))
    basket = world.add(Entity(
        id="Basket", kind="thing", type="basket", label=basket_cfg.label,
        phrase=basket_cfg.phrase, owner=None, caretaker=None,
        region="hands", plural=basket_cfg.plural,
    ))

    world.facts["moral_theme"] = moral_theme
    world.facts["basket"] = basket
    world.facts["bandit"] = bandit
    world.facts["ghost"] = ghost

    # Act 1: setup
    introduce(world, bandit, moral_theme)
    describe_raffia(world, basket)
    bandit_wants(world, bandit, activity)

    # Act 2: conflict
    world.para()
    bandit_steals(world, bandit, activity)
    ghost_appears_and_warns(world, ghost)
    bandit_defies(world, bandit)
    ghost_pleads(world, ghost)

    # Act 3: resolution
    world.para()
    bandit_relents(world, bandit, basket)
    resolution(world, bandit, basket, ghost, moral_theme)

    world.facts["resolved"] = (bandit.memes["moral_learned"] >= THRESHOLD)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "market": Setting(place="the village market", affords={"steal", "return"}),
    "temple": Setting(place="the old temple", affords={"steal", "return"}),
}

ACTIVITIES = {
    "steal": Activity(
        id="steal",
        verb="steal the raffia basket",
        gerund="stealing raffia baskets",
        rush="grab the basket and run",
        mess="stolen",
        soil="stolen and cursed",
        zone={"hands"},
        keyword="steal",
        tags={"stealing", "basket"},
    ),
}

BASKETS = {
    "basket": Basket(
        label="basket",
        phrase="a golden raffia basket",
        type="basket",
    ),
    "hat": Basket(
        label="hat",
        phrase="a wide raffia hat with a blue ribbon",
        type="basket",  # still a raffia item
        region="head",
    ),
}

BANDIT_NAMES = ["Kael", "Dorn", "Vex", "Rynn", "Grim"]
GHOST_TYPES = ["ghost_of_mother", "ghost_of_father", "ghost_of_grandmother"]
MORAL_THEMES_LIST = list(MORAL_THEMES)


def valid_combos() -> list[tuple[str, str, str]]:
    """(setting_id, activity_id, basket_id) triples that are valid."""
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting.affords:
            for bid in BASKETS:
                if basket_can_be_stolen(_safe_lookup(BASKETS, bid)):
                    combos.append((sid, aid, bid))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    basket: str
    bandit_name: str
    bandit_type: str
    ghost_type: str
    moral_theme: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "raffia": [("What is raffia?",
                "Raffia is a natural fiber made from palm leaves. People weave it into baskets, hats, and mats.")],
    "ghost": [("What is a ghost?",
               "In stories, a ghost is the spirit of a person who has died, sometimes appearing to teach a lesson.")],
    "honesty": [("What does honesty mean?",
                 "Honesty means telling the truth and not taking things that belong to others.")],
    "stealing": [("Why is stealing wrong?",
                  "Stealing hurts other people. It takes away something that is not yours, and it can make you feel guilty.")],
}
KNOWLEDGE_ORDER = ["raffia", "ghost", "honesty", "stealing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bandit, ghost = f["bandit"], f["ghost"]
    moral = f.get("moral_theme", "honesty")
    return [
        f'Write a short ghost story for a child about a bandit who learns the value of {moral}.',
        f'Tell a gentle story where a bandit named {bandit.id} encounters a ghost and makes a moral choice.',
        f'Create a simple story that uses the word "raffia" and ends with the bandit returning what was stolen.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bandit = _safe_fact(world, f, "bandit")
    ghost = _safe_fact(world, f, "ghost")
    moral = f.get("moral_theme", "honesty")
    basket = _safe_fact(world, f, "basket")
    resolved = f.get("resolved", False)
    qa = [
        QAItem(
            question=f"What did the bandit {bandit.id} try to steal?",
            answer=f"He tried to steal a raffia {basket.label} from the market."
        ),
        QAItem(
            question=f"Who appeared to warn the bandit?",
            answer=f"A ghost – the spirit of the person who once owned the raffia basket."
        ),
        QAItem(
            question=f"What moral did the bandit learn at the end?",
            answer=f"He learned the value of {moral}. He returned the basket and promised to be honest."
        ),
    ]
    if resolved:
        qa.append(QAItem(
            question=f"How did the ghost feel after the bandit returned the basket?",
            answer=f"The ghost felt peaceful and smiled. The fog lifted, and the ghost faded away."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="market", activity="steal", basket="basket",
        bandit_name="Kael", bandit_type="bandit", ghost_type="ghost_of_mother",
        moral_theme="honesty",
    ),
    StoryParams(
        setting="temple", activity="steal", basket="hat",
        bandit_name="Vex", bandit_type="bandit", ghost_type="ghost_of_father",
        moral_theme="kindness",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A basket can be stolen if it exists.
can_steal(B) :- basket(B).
% A moral lesson exists if the theme is valid.
has_moral_lesson(M) :- moral_theme(M).
% A story is valid if the setting affords the activity and a lesson exists.
valid(Setting, Activity, Basket, Moral) :-
    affords(Setting, Activity),
    basket(Basket),
    moral_theme(Moral),
    can_steal(Basket),
    has_moral_lesson(Moral).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for a in sorted(_safe_lookup(SETTINGS, sid).affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for bid in BASKETS:
        lines.append(asp.fact("basket", bid))
    for m in MORAL_THEMES_LIST:
        lines.append(asp.fact("moral_theme", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_combos = set(valid_combos())
    # ASP combos are 4‑tuples (setting, activity, basket, moral); we ignore moral for size
    asp_combos = set((s, a, b) for s, a, b, _ in asp_valid())
    if asp_combos == python_combos:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_combos)} combos).")
        return 0
    print("MISMATCH:")
    if asp_combos - python_combos:
        print("  only in clingo:", sorted(asp_combos - python_combos))
    if python_combos - asp_combos:
        print("  only in python:", sorted(python_combos - asp_combos))
    return 1


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story: a bandit, a raffia basket, a moral.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--basket", choices=BASKETS)
    ap.add_argument("--bandit-name")
    ap.add_argument("--bandit-type", default="bandit")
    ap.add_argument("--ghost-type", choices=GHOST_TYPES)
    ap.add_argument("--moral-theme", choices=MORAL_THEMES_LIST)
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
    if getattr(args, "setting", None) or getattr(args, "activity", None) or getattr(args, "basket", None):
        filtered = [c for c in combos
                    if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
                    and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
                    and (getattr(args, "basket", None) is None or c[2] == getattr(args, "basket", None))]
        if not filtered:
            return _fallback_storyparams(args, rng, StoryParams, globals())
        combos = filtered
    setting, activity, basket = rng.choice(list(combos))
    bandit_name = getattr(args, "bandit_name", None) or rng.choice(BANDIT_NAMES)
    ghost_type = getattr(args, "ghost_type", None) or rng.choice(GHOST_TYPES)
    moral_theme = getattr(args, "moral_theme", None) or rng.choice(MORAL_THEMES_LIST)
    return StoryParams(
        setting=setting,
        activity=activity,
        basket=basket,
        bandit_name=bandit_name,
        bandit_type="bandit",
        ghost_type=ghost_type,
        moral_theme=moral_theme,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(BASKETS, params.basket),
        params.bandit_name,
        params.bandit_type,
        params.ghost_type,
        params.moral_theme,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        combos = asp_valid()
        print(f"{len(combos)} valid stories (setting, activity, basket, moral_theme):")
        for s, a, b, m in combos:
            print(f"  {s:9} {a:8} {b:8} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.bandit_name}: {p.moral_theme} (basket: {p.basket})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
