#!/usr/bin/env python3
"""
storyworlds/worlds/drench_cautionary_kindness_transformation_tall_tale.py
========================================================================

A small tall-tale storyworld about a warning, a drenched mistake, a kind fix,
and a surprising transformation.

Premise:
- A child or villager is warned not to go near a place where a giant fountain,
  storm barrel, or cloud-sprayer will drench them.
- They ignore the caution, get drenched, and a treasured item becomes heavy,
  soggy, or ruined.
- A kind helper offers a clever dry-off, and the helper's kindness leads to a
  transformation: the drenched mess becomes something new and useful.

The world stays tiny and classical:
- physical meters: wetness, heaviness, splashedness, dryness, shine
- emotional memes: worry, embarrassment, kindness, gratitude, wonder

The prose is authored from simulated state, not from a frozen template.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    helper: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id

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
class Location:
    place: str = "the riverbank"
    indoors: bool = False
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
class Device:
    id: str
    label: str
    verb: str
    warning: str
    mess: str
    zone: set[str]
    transformation: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    transforms_to: str = ""
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
class StoryParams:
    place: str = ""
    device: str = ""
    treasure: str = ""
    name: str = ""
    gender: str = ""
    helper: str = ""
    trait: str = ""
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


class World:
    def __init__(self, location: Location):
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.device_zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


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


def _r_drench(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("drench", 0.0) < THRESHOLD:
            continue
        sig = ("drench", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["wet"] = actor.meters.get("wet", 0.0) + 1
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.name_or_label()} was drenched from head to toe.")
    return out


def _r_soak_treasure(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("drench", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            item.meters["heavy"] = item.meters.get("heavy", 0.0) + 1
            out.append(f"That made {item.name_or_label()} heavy and soggy.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.facts.get("helper")
    hero = world.facts.get("hero")
    treasure = world.facts.get("treasure")
    if not helper or not hero or not treasure:
        return out
    if hero.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("kindness", helper.id, hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["gratitude"] = hero.memes.get("gratitude", 0.0) + 1
    treasure.meters["wet"] = max(0.0, treasure.meters.get("wet", 0.0) - 1)
    treasure.meters["shine"] = treasure.meters.get("shine", 0.0) + 1
    out.append(f"{helper.name_or_label()} offered a kind hand and a warm towel.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    treasure = world.facts.get("treasure")
    if not hero or not treasure:
        return out
    if treasure.meters.get("shine", 0.0) < THRESHOLD:
        return out
    sig = ("transform", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    treasure.meters["transformed"] = 1
    out.append(f"By sunset, the soggy thing had become something new.")
    return out


RULES = [
    Rule("drench", _r_drench),
    Rule("soak_treasure", _r_soak_treasure),
    Rule("kindness", _r_kindness),
    Rule("transformation", _r_transformation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def place_detail(location: Location, device: Device) -> str:
    if location.indoors:
        return f"Inside {location.place}, the air hummed like a held note."
    if device.id == "cloudsprayer":
        return f"Above {location.place}, one great cloud-sprayer rattled and hissed."
    return f"{location.place.capitalize()} stretched wide and bright under the sky."


def hero_intro(hero: Entity) -> str:
    return f"{hero.name_or_label()} was a little {next((t for t in hero.tags if t != 'little'), 'brave')} {hero.type} with quick feet and a bigger-than-life heart."


def tell_story(world: World) -> World:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")
    treasure = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "treasure")
    device = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "device")

    world.say(hero_intro(hero))
    world.say(f"{hero.pronoun('subject').capitalize()} loved {device.verb}, but {device.warning}.")
    world.say(f"That was why {helper.name_or_label()} kept saying, “Don't go closer than the old fence, or you'll get drenched.”")
    world.para()
    world.say(place_detail(world.location, device))
    world.say(f"Still, {hero.name_or_label()} wanted to see the {device.label} up close.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.meters["drench"] = hero.meters.get("drench", 0.0) + 1
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{hero.name_or_label()} looked down at {treasure.name_or_label()} and saw it was ruined.")
    world.say(f"Then {helper.name_or_label()} smiled, wrapped {(getattr(treasure, 'it')() if callable(getattr(treasure, 'it', None)) else getattr(treasure, 'it', 'it'))} in a towel, and said, “Let's turn this into something better.”")
    propagate(world, narrate=True)
    world.say(f"Together they {device.transformation}, and that made the day feel taller than a circus tent.")
    return world


LOCATION_REGISTRY = {
    "riverbank": Location(place="the riverbank", indoors=False, affords={"spray", "drench"}),
    "cliffgarden": Location(place="the cliff garden", indoors=False, affords={"spray", "drench"}),
    "harbor": Location(place="the harbor", indoors=False, affords={"drench"}),
    "workshop": Location(place="the workshop", indoors=True, affords={"spray"}),
}

DEVICE_REGISTRY = {
    "cloudsprayer": Device(
        id="cloudsprayer",
        label="cloud-sprayer",
        verb="listen to its huffing and puffing",
        warning="one burst could drench a traveler in a blink",
        mess="drench",
        zone={"head", "torso"},
        transformation="bent the bent tin into a wind bell",
        tags={"drench", "cloud", "weather"},
    ),
    "rivercannon": Device(
        id="rivercannon",
        label="river cannon",
        verb="watch the water cannon",
        warning="its splash could drench anyone standing too close",
        mess="drench",
        zone={"head", "torso", "legs"},
        transformation="shaped the broken bucket into a tiny boat",
        tags={"drench", "water"},
    ),
    "rainbarrel": Device(
        id="rainbarrel",
        label="rain barrel",
        verb="study the old rain barrel",
        warning="its overflow could drench boots and hems alike",
        mess="drench",
        zone={"legs", "torso"},
        transformation="turned the wet cloth into a bright kite tail",
        tags={"drench", "rain"},
    ),
}

TREASURE_REGISTRY = {
    "hat": Treasure(id="hat", label="hat", phrase="a fine straw hat", region="head", transforms_to="wind bell"),
    "shawl": Treasure(id="shawl", label="shawl", phrase="a red wool shawl", region="torso", transforms_to="kite tail"),
    "apron": Treasure(id="apron", label="apron", phrase="a patchwork apron", region="torso", transforms_to="boat sail"),
}

HELPERS = {
    "grandma": ("grandma", "woman"),
    "uncle": ("uncle", "man"),
    "neighbor": ("neighbor", "person"),
}

GIRL_NAMES = ["Mabel", "Nell", "Ruby", "Ivy", "Luna", "Hazel"]
BOY_NAMES = ["Otis", "Benny", "Hank", "Earl", "Jude", "Milo"]
TRAITS = ["curious", "stubborn", "cheerful", "daring", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, loc in LOCATION_REGISTRY.items():
        for device in loc.affords:
            for treasure in TREASURE_REGISTRY:
                combos.append((place, device, treasure))
    return combos


def select_helper(gender: str) -> tuple[str, str]:
    return random.choice(list(HELPERS.values()))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: caution, drench, kindness, and transformation.")
    ap.add_argument("--place", choices=LOCATION_REGISTRY)
    ap.add_argument("--device", choices=DEVICE_REGISTRY)
    ap.add_argument("--treasure", choices=TREASURE_REGISTRY)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=list(HELPERS))
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "device", None) is None or c[1] == getattr(args, "device", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, device, treasure = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, device=device, treasure=treasure, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    loc = _safe_lookup(LOCATION_REGISTRY, params.place)
    device = _safe_lookup(DEVICE_REGISTRY, params.device)
    treasure_cfg = _safe_lookup(TREASURE_REGISTRY, params.treasure)
    helper_id, helper_type = _safe_lookup(HELPERS, params.helper)

    world = World(loc)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, tags={"little", params.trait}))
    helper = world.add(Entity(id=helper_id, kind="character", type=helper_type, tags={"kind"}))
    treasure = world.add(Entity(
        id=treasure_cfg.id,
        type="thing",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        plural=treasure_cfg.plural,
    ))
    treasure.worn_by = hero.id

    world.facts.update(hero=hero, helper=helper, treasure=treasure, device=device)
    world = tell_story(world)

    prompts = [
        f"Write a short tall tale for a child who gets drenched and then helped kindly.",
        f"Tell a simple story where {hero.name_or_label()} ignores a warning near {device.label}.",
        f"Make a gentle story about kindness turning a ruined {treasure.label} into something new.",
    ]

    story_qa = [
        QAItem(
            question=f"Who got drenched near the {device.label}?",
            answer=f"{hero.name_or_label()} got drenched after ignoring the warning near the {device.label}.",
        ),
        QAItem(
            question=f"What happened to {treasure.name_or_label()} when {hero.name_or_label()} got too close?",
            answer=f"{treasure.name_or_label()} became heavy and soggy, because the drench soaked it too.",
        ),
        QAItem(
            question=f"How did {helper.name_or_label()} help at the end?",
            answer=f"{helper.name_or_label()} helped kindly with a towel and a new idea, and that led to a transformation.",
        ),
        QAItem(
            question=f"What did the ruined thing become?",
            answer=f"It became something useful again through a cheerful transformation.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does drench mean?",
            answer="To drench something is to soak it with a lot of water so it becomes very wet.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something gentle and helpful for someone else.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a different kind of thing or a new form.",
        ),
    ]

    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({a for a, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% This world is tiny: a device can drench a hero, a drenched hero can soak a
% treasure, kindness can mend the mood, and a transformation can follow.

hero(H) :- hero_id(H).
helper(K) :- helper_id(K).
treasure(T) :- treasure_id(T).
device(D) :- device_id(D).

drenched(H) :- hero(H), too_close(H, D), device(D), drench_device(D).
soaks(T) :- drenched(H), treasure(T), worn_by(T, H).

kind_move(K, H) :- helper(K), hero(H), drenched(H).
transformed(T) :- soaks(T), kind_move(_, _).

#show drenched/1.
#show soaks/1.
#show transformed/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in LOCATION_REGISTRY:
        lines.append(asp.fact("location", place))
    for did in DEVICE_REGISTRY:
        lines.append(asp.fact("device_id", did))
        if "drench" in _safe_lookup(DEVICE_REGISTRY, did).tags:
            lines.append(asp.fact("drench_device", did))
    for tid in TREASURE_REGISTRY:
        lines.append(asp.fact("treasure_id", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper_id", hid))
    return "\n".join(lines)


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    if model is None:
        print("No ASP model found.")
        return 1
    print("OK: ASP program grounded successfully.")
    return 0


def build_random_story(params: StoryParams) -> StorySample:
    return generate(params)


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
    StoryParams(place="riverbank", device="cloudsprayer", treasure="hat", name="Mabel", gender="girl", helper="grandma", trait="curious"),
    StoryParams(place="cliffgarden", device="rivercannon", treasure="shawl", name="Otis", gender="boy", helper="uncle", trait="daring"),
    StoryParams(place="harbor", device="rainbarrel", treasure="apron", name="Ruby", gender="girl", helper="neighbor", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "show_asp", None):
        print(asp_program())
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
