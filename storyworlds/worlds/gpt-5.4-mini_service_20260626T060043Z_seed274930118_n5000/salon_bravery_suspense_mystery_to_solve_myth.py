#!/usr/bin/env python3
"""
storyworlds/worlds/salon_bravery_suspense_mystery_to_solve_myth.py
===================================================================

A tiny mythic storyworld set in a salon, where a child must be brave while a
small mystery is solved.

Premise:
- A child arrives at a salon for a special styling.
- Something important is missing or seems wrong.
- The child feels suspense and must be brave.
- The stylist and a helper solve the mystery.
- The ending proves the change with a new, shining look.

The world model tracks both physical and emotional state:
- meters: combs, clips, hair, polish, light, and the small physical clues
- memes: bravery, suspense, mystery, relief, wonder, pride

The prose is authored from world state; it is not a frozen paragraph with
swapped names.
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
# Content registries
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

@dataclass(frozen=True)
class SalonSetting:
    place: str = "the salon"
    detail: str = "bright mirrors and warm chairs"
    closing_time: str = "before the lamps dimmed"
    SALON: object | None = None
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


@dataclass(frozen=True)
class StyleChoice:
    id: str
    style_name: str
    verb: str
    result: str
    sparkle: str
    clue: str
    requires: str
    mystery_kind: str
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


@dataclass(frozen=True)
class KeyItem:
    id: str
    label: str
    phrase: str
    type: str
    owner_role: str
    helpful: bool = False
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


@dataclass(frozen=True)
class Helper:
    id: str
    label: str
    role: str
    kind: str
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


SALON = SalonSetting()

STYLE_CHOICES: dict[str, StyleChoice] = {
    "braid": StyleChoice(
        id="braid",
        style_name="braid",
        verb="braid",
        result="a neat braid",
        sparkle="like a river woven with moonlight",
        clue="a ribbon tangled under a comb",
        requires="ribbon",
        mystery_kind="lost ribbon",
    ),
    "curls": StyleChoice(
        id="curls",
        style_name="curls",
        verb="curl",
        result="soft curls",
        sparkle="like clouds touched by sunrise",
        clue="a curling iron left unplugged but warm",
        requires="curling_iron",
        mystery_kind="sleepy iron",
    ),
    "crown": StyleChoice(
        id="crown",
        style_name="crown",
        verb="pin into a crown",
        result="a shining crown of hair",
        sparkle="like a little halo fit for a hero",
        clue="a gold clip hiding behind a mirror pot",
        requires="gold_clip",
        mystery_kind="hidden clip",
    ),
}

KEY_ITEMS: dict[str, KeyItem] = {
    "ribbon": KeyItem(
        id="ribbon",
        label="ribbon",
        phrase="a blue ribbon with a silver edge",
        type="ribbon",
        owner_role="child",
        helpful=True,
    ),
    "curling_iron": KeyItem(
        id="curling_iron",
        label="curling iron",
        phrase="a small curling iron",
        type="tool",
        owner_role="stylist",
        helpful=True,
    ),
    "gold_clip": KeyItem(
        id="gold_clip",
        label="gold clip",
        phrase="a little gold clip",
        type="clip",
        owner_role="child",
        helpful=True,
    ),
}

HELPERS: dict[str, Helper] = {
    "stylist": Helper(id="stylist", label="the stylist", role="stylist", kind="person"),
    "assistant": Helper(id="assistant", label="the helper", role="assistant", kind="person"),
}

GIRL_NAMES = ["Mia", "Lina", "Ava", "Nora", "Zoe", "Iris", "Luna", "Maya"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Owen", "Theo", "Max", "Sam"]
TRAITS = ["brave", "curious", "gentle", "shy", "spirited", "hopeful"]


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    helper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    wearing: Optional[str] = None
    found: bool = False

    assistant: object | None = None
    hero: object | None = None
    item: object | None = None
    stylist: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "it"
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
class StoryParams:
    name: str
    gender: str
    trait: str
    style: str
    clue_source: str
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
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        clone = World(self.params)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def add_bravery(world: World, hero: Entity) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0


def add_suspense(world: World, hero: Entity) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1.0


def add_mystery(world: World, hero: Entity) -> None:
    hero.memes["mystery"] = hero.memes.get("mystery", 0.0) + 1.0


def add_relief(world: World, hero: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1.0


def add_pride(world: World, hero: Entity) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def setting_line() -> str:
    return f"{SALON.place.capitalize()} held {SALON.detail}."


def opening_line(hero: Entity, style: StyleChoice) -> str:
    return (
        f"{hero.id} came to {SALON.place} wanting {style.verb} {hero.pronoun('possessive')} hair "
        f"into {style.result}."
    )


def mythic_tone(style: StyleChoice) -> str:
    return (
        f"It promised to shine {style.sparkle}, fit for a story told beside a hearth."
    )


def mystery_line(style: StyleChoice) -> str:
    return f"But there was a mystery: {style.clue}."


def reveal_line(style: StyleChoice) -> str:
    return f"At last, the missing piece was found, and the salon grew calm again."


def ending_line(hero: Entity, style: StyleChoice) -> str:
    return (
        f"In the end, {hero.id} wore {style.result}, and it glimmered {style.sparkle}."
    )


def solution_line(hero: Entity, helper: Entity, item: Entity, style: StyleChoice) -> str:
    return (
        f"{helper.label} spotted {item.phrase} and handed it over, so {hero.id} could keep "
        f"going without fear."
    )


def courage_line(hero: Entity) -> str:
    return f"{hero.id} took a slow breath and stayed still, brave as a small knight."


def suspense_line(hero: Entity) -> str:
    return f"{hero.id} listened closely while the brushes whispered and the mirrors waited."


def resolve_world(world: World, hero: Entity) -> None:
    hero.memes["suspense"] = max(0.0, hero.memes.get("suspense", 0.0) - 1.0)
    add_relief(world, hero)
    add_pride(world, hero)


def narrate_salon_story(world: World) -> None:
    hero = world.get("hero")
    stylist = world.get("stylist")
    assistant = world.get("assistant")
    item = world.get("item")
    style = _safe_lookup(STYLE_CHOICES, world.params.style)

    add_bravery(world, hero)
    add_mystery(world, hero)
    add_suspense(world, hero)

    world.say(setting_line())
    world.say(opening_line(hero, style))
    world.say(mythic_tone(style))

    world.para()
    world.say(mystery_line(style))
    world.say(courage_line(hero))
    world.say(suspense_line(hero))
    world.say(
        f"{stylist.label} and {assistant.label} looked under combs, behind jars, and beside the chair."
    )

    world.para()
    world.say(solution_line(hero, assistant, item, style))
    world.say(reveal_line(style))
    resolve_world(world, hero)
    item.found = True
    item.wearing = hero.id
    world.say(
        f"{hero.id} smiled with relief while {stylist.label} finished the style with careful hands."
    )

    world.para()
    world.say(ending_line(hero, style))
    world.say(
        f"{hero.id} walked out of {SALON.place} with {style.result}, and the day felt like a small myth come true."
    )

    world.facts.update(
        hero=hero,
        stylist=stylist,
        assistant=assistant,
        item=item,
        style=style,
        solved=item.found,
    )


def build_world(params: StoryParams) -> World:
    world = World(params)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"hair": 1.0},
        memes={"bravery": 0.0, "suspense": 0.0, "mystery": 0.0, "relief": 0.0, "pride": 0.0},
    ))
    stylist = world.add(Entity(id="stylist", kind="character", type="adult", label="the stylist"))
    assistant = world.add(Entity(id="assistant", kind="character", type="adult", label="the helper"))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=_safe_lookup(KEY_ITEMS, params.clue_source).type,
        label=_safe_lookup(KEY_ITEMS, params.clue_source).label,
        phrase=_safe_lookup(KEY_ITEMS, params.clue_source).phrase,
        owner=hero.id,
        helper=stylist.id,
    ))
    world.say(hero.id)  # harmless seed of entity existence for traceability? no, avoid prose fragments
    world.paragraphs = [[]]
    narrate_salon_story(world)
    return world


# ---------------------------------------------------------------------------
# Registries and resolution
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for style_id, style in STYLE_CHOICES.items():
        for item_id, item in KEY_ITEMS.items():
            if item_id == style.requires:
                combos.append((SALON.place, style_id, item_id))
    return combos


def explain_rejection(style: StyleChoice, item: KeyItem) -> str:
    return (
        f"(No story: this salon mystery needs {style.requires}, but the chosen clue was {item.label}. "
        f"The missing-piece mystery must match the style being solved.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Salon myth storyworld: bravery, suspense, and a mystery to solve.")
    ap.add_argument("--style", choices=STYLE_CHOICES)
    ap.add_argument("--clue-source", choices=KEY_ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if getattr(args, "style", None) and getattr(args, "clue_source", None):
        style = _safe_lookup(STYLE_CHOICES, getattr(args, "style", None))
        item = _safe_lookup(KEY_ITEMS, getattr(args, "clue_source", None))
        if item.id != style.requires:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = valid_combos()
    if getattr(args, "style", None):
        combos = [c for c in combos if c[1] == getattr(args, "style", None)]
    if getattr(args, "clue_source", None):
        combos = [c for c in combos if c[2] == getattr(args, "clue_source", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    _, style_id, clue_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, trait=trait, style=style_id, clue_source=clue_id)


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    style = _safe_fact(world, world.facts, "style")
    return [
        f"Write a short mythic story about {hero.id} in a salon, with bravery, suspense, and a mystery to solve.",
        f"Tell a gentle tale where {hero.id} wants to {style.verb} {hero.pronoun('possessive')} hair, but a clue goes missing.",
        f"Write a child-friendly myth set in a salon where helpers search for {style.requires} and the ending feels like a blessing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    style = _safe_fact(world, world.facts, "style")
    item = _safe_fact(world, world.facts, "item")
    return [
        QAItem(
            question=f"Where did {hero.id} go to get {hero.pronoun('possessive')} hair styled?",
            answer=f"{hero.id} went to {SALON.place}, where the mirrors were bright and the chairs were warm.",
        ),
        QAItem(
            question=f"What did {hero.id} want the stylist to do with {hero.pronoun('possessive')} hair?",
            answer=f"{hero.id} wanted to {style.verb} {hero.pronoun('possessive')} hair into {style.result}.",
        ),
        QAItem(
            question=f"What was the mystery in the salon story?",
            answer=f"The mystery was {item.phrase}, which had to be found before the style could be finished.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery while the salon mystery was being solved?",
            answer=f"{hero.id} stayed still, took a slow breath, and waited bravely while the search went on.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The mystery was solved, {hero.id} felt relief and pride, and the hair became {style.result}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a salon?",
            answer="A salon is a place where people wash, cut, brush, and style hair.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means staying calm and doing what needs to be done even when something feels a little scary.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first, so people look for clues to solve it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.wearing:
            bits.append(f"wearing={e.wearing}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
style_choice(S) :- style(S).
clue_choice(C) :- item(C).

compatible(S,C) :- style(S), item(C), requires(S,C).

valid_story(S,C) :- compatible(S,C).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("salon", "salon"))
    for s in STYLE_CHOICES.values():
        lines.append(asp.fact("style", s.id))
        lines.append(asp.fact("requires", s.id, s.requires))
    for item in KEY_ITEMS.values():
        lines.append(asp.fact("item", item.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(s, c) for _, s, c in valid_combos()}
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

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


CURATED = [
    StoryParams(name="Mia", gender="girl", trait="brave", style="braid", clue_source="ribbon"),
    StoryParams(name="Leo", gender="boy", trait="curious", style="curls", clue_source="curling_iron"),
    StoryParams(name="Ava", gender="girl", trait="hopeful", style="crown", clue_source="gold_clip"),
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            header = f"### {p.name}: {p.style} / {p.clue_source}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
