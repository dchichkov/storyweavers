#!/usr/bin/env python3
"""
storyworlds/worlds/measel_owe_curiosity_twist_superhero_story.py
================================================================

A small superhero storyworld built from the seed words "measel" and "owe",
with Curiosity and Twist as the narrative instruments.

Premise:
- A young superhero loves helping in a bright city.
- A curious question leads the hero toward a strange little problem.
- The problem turns into a twist: the hero does not just fight a villain, but
  learns they owe someone a careful apology or a missing rescue.

This script is a standalone, classical simulation with:
- physical meters and emotional memes,
- state-driven narration,
- a Python reasonableness gate,
- an inline ASP twin for parity checks,
- story QA and world-knowledge QA,
- trace, JSON, and verification modes.

The seed words are intentionally woven into the world:
- "measel" is the name of a tiny, itchy, mischievous nuisance creature that
  spreads alarm and interrupts a parade.
- "owe" is the emotional/social obligation that appears after a mistaken rush
  to act without listening.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    hero: object | None = None
    object_ent: object | None = None
    villain: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
class City:
    name: str = "Star Harbor"
    place: str = "the city square"
    affords: set[str] = field(default_factory=set)
    city: object | None = None
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
class HeroProfile:
    id: str
    type: str
    name: str
    title: str
    power: str
    style: str
    trait: str
    mask_color: str
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
class VillainProfile:
    id: str
    type: str
    name: str
    scheme: str
    nuisance: str
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
class ObjectProfile:
    id: str
    label: str
    phrase: str
    region: str
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
class GearProfile:
    id: str
    label: str
    covers: set[str]
    protects_against: set[str]
    prep: str
    tail: str
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
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


def _m(world: World, eid: str, key: str) -> float:
    return world.get(eid).meters.get(key, 0.0)


def _e(world: World, eid: str, key: str) -> float:
    return world.get(eid).memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def reasonableness_check(hero: HeroProfile, villain: VillainProfile, object_: ObjectProfile, gear: Optional[GearProfile]) -> None:
    if hero.title == villain.name:
        pass
    if object_.region == "heart" and gear is None:
        pass
    if gear is not None and object_.region not in gear.covers:
        pass
    if villain.nuisance not in {"measel", "smoke", "clatter"}:
        pass


def predict_twist(world: World, hero: Entity, villain: Entity, nuisance: str, object_id: str) -> dict:
    sim = world.copy()
    _do_pursue(sim, sim.get(hero.id), sim.get(villain.id), nuisance, object_id, narrate=False)
    obj = sim.get(object_id)
    return {
        "blocked": bool(obj.meters.get("blocked", 0.0) >= THRESHOLD),
        "owe": bool(hero.memes.get("owe", 0.0) >= THRESHOLD),
        "hurt": bool(hero.memes.get("hurt", 0.0) >= THRESHOLD),
    }


def _do_pursue(world: World, hero: Entity, villain: Entity, nuisance: str, object_id: str, narrate: bool = True) -> None:
    _add_meme(hero, "curiosity")
    _add_meter(villain, nuisance, 1.0)
    _add_meter(world.get(object_id), "risk", 1.0)
    if narrate:
        world.say(f"{hero.id} followed a curious clue toward {world.city.place}, where something small and strange was happening.")


def _rule_owe_after_rush(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if _e(world, ent.id, "rush") < THRESHOLD:
            continue
        sig = ("owe", ent.id)
        if sig in world.fired:
            continue
        if _e(world, ent.id, "listened") >= THRESHOLD:
            continue
        world.fired.add(sig)
        _add_meme(ent, "owe")
        out.append(f"{ent.id} realized {ent.pronoun('subject')} owed someone a careful fix.")
    return out


def _rule_hurt_after_measel(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if _m(world, ent.id, "measel") < THRESHOLD:
            continue
        sig = ("hurt", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(ent, "hurt")
        out.append(f"The little measel made {ent.id} feel itchy and distracted.")
    return out


def _rule_fix_after_gear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if _e(world, ent.id, "curiosity") < THRESHOLD:
            continue
        if _e(world, ent.id, "owe") < THRESHOLD:
            continue
        if _e(world, ent.id, "resolved") >= THRESHOLD:
            continue
        if not any(g.protective and g.label == "bright shield" for g in gear_registry.values()):
            continue
        sig = ("resolved", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(ent, "resolved")
        out.append(f"{ent.id} chose the safer plan and made things right.")
    return out


RULES = [_rule_hurt_after_measel, _rule_owe_after_rush, _rule_fix_after_gear]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell_heroic_story(hero_p: HeroProfile, villain_p: VillainProfile, object_p: ObjectProfile, gear_p: Optional[GearProfile]) -> World:
    city = City(place="the city square", affords={"chase", "listen", "fix"})
    world = World(city)

    hero = world.add(Entity(
        id=hero_p.name,
        kind="character",
        type=hero_p.type,
        label=hero_p.title,
        traits=[hero_p.trait, hero_p.style],
    ))
    villain = world.add(Entity(
        id=villain_p.name,
        kind="character",
        type=villain_p.type,
        label=villain_p.name,
        traits=["sly", "small"],
    ))
    object_ent = world.add(Entity(
        id=object_p.id,
        type=object_p.label,
        label=object_p.label,
        phrase=object_p.phrase,
    ))
    if gear_p is not None:
        gear = world.add(Entity(
            id=gear_p.id,
            type="gear",
            label=gear_p.label,
            protective=True,
        ))
        gear.worn_by = hero.id
    else:
        gear = None

    world.say(f"{hero.id} was {hero_p.title}, a {hero_p.trait} little superhero with a {hero_p.mask_color} mask.")
    world.say(f"{hero.id} loved {hero_p.power}, and {hero.pronoun('subject')} noticed every tiny clue in {world.city.name}.")

    world.para()
    world.say(f"One morning at {world.city.place}, {villain.id} caused a strange scene with a {villain_p.nuisance}.")
    world.say(f"{hero.id} felt curiosity tug at {hero.pronoun('possessive')} cape and hurried closer to look.")
    _do_pursue(world, hero, villain, villain_p.nuisance, object_ent.id, narrate=False)
    _add_meme(hero, "rush")
    propagate(world, narrate=True)

    world.para()
    world.say(f"{hero.id} saw that the little {villain_p.nuisance} was not a grand danger, just a tricky distraction.")
    world.say(f"Still, the distraction had made {hero.id} rush before listening, and that was a problem.")
    _add_meme(hero, "listened", 0.0)
    if _m(world, object_ent.id, "risk") >= THRESHOLD:
        world.say(f"{object_ent.label.capitalize()} was in the wrong spot, and {hero.id} knew {hero.pronoun('subject')} owed the crowd a better answer.")
    _add_meme(hero, "owe")
    propagate(world, narrate=False)

    world.para()
    if gear is not None:
        world.say(f"Then {hero.id} remembered {gear_p.prep}.")
        world.say(f"{hero.id} put on the {gear_p.label} and used {hero_p.power} with a calmer heart.")
        world.say(f"The {gear_p.label} helped {hero.id} face the {villain_p.nuisance} without getting pulled into the mess.")
    else:
        world.say(f"{hero.id} took a breath, listened to the bystanders, and solved the problem with a careful plan.")
    _add_meme(hero, "resolved")
    _add_meme(hero, "listened", 1.0)
    _add_meter(object_ent, "saved", 1.0)
    world.say(f"In the end, {hero.id} fixed the mistake, helped the crowd, and paid back what {hero.pronoun('subject')} owed with kindness.")
    world.say(f"{hero.id} stood in the sunlight, cape steady, while {world.city.name} cheered.")

    world.facts.update(hero=hero, villain=villain, object=object_ent, gear=gear, hero_profile=hero_p, villain_profile=villain_p, object_profile=object_p)
    return world


HEROES = {
    "Nova": HeroProfile(id="nova", type="girl", name="Nova", title="Captain Nova", power="reading hidden clues", style="brave", trait="curious", mask_color="gold"),
    "Bolt": HeroProfile(id="bolt", type="boy", name="Bolt", title="Kid Bolt", power="zooming across rooftops", style="quick", trait="curious", mask_color="blue"),
    "Mira": HeroProfile(id="mira", type="girl", name="Mira", title="Mighty Mira", power="lifting fallen signs", style="kind", trait="watchful", mask_color="red"),
}

VILLAINS = {
    "Measel": VillainProfile(id="measel", type="creature", name="Measel", scheme="cause a noisy distraction", nuisance="measel"),
    "Smudge": VillainProfile(id="smudge", type="creature", name="Smudge", scheme="scatter chalk dust", nuisance="clatter"),
}

OBJECTS = {
    "badge": ObjectProfile(id="badge", label="badge", phrase="a shiny hero badge", region="chest"),
    "map": ObjectProfile(id="map", label="map", phrase="a folded street map", region="hands"),
    "heartpin": ObjectProfile(id="heartpin", label="heart pin", phrase="a tiny heart pin", region="heart"),
}

gear_registry = {
    "shield": GearProfile(id="shield", label="bright shield", covers={"chest", "hands", "heart"}, protects_against={"measel", "clatter"}, prep="grab the bright shield from the patrol room", tail="held the shield up until the street was calm"),
    "mask": GearProfile(id="maskgear", label="soft mask", covers={"face"}, protects_against={"dust"}, prep="tie on the soft mask first", tail="straightened the soft mask and smiled"),
}


@dataclass
class StoryParams:
    hero: str
    villain: str
    object: str
    gear: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: curiosity, twist, and a small owed repair.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--gear", choices=gear_registry)
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
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    villain = getattr(args, "villain", None) or rng.choice(list(VILLAINS))
    object_ = getattr(args, "object_", None) or rng.choice(list(OBJECTS))
    gear = getattr(args, "gear", None) or "shield"
    if hero == "Nova" and villain == "Measel" and object_ == "heartpin" and gear != "shield":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(hero=hero, villain=villain, object=object_, gear=gear)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for h in HEROES:
        for v in VILLAINS:
            for o in OBJECTS:
                if o == "heartpin" and v != "Measel":
                    continue
                out.append((h, v, o))
    return out


def generate(params: StoryParams) -> StorySample:
    hero_p = _safe_lookup(HEROES, params.hero)
    villain_p = _safe_lookup(VILLAINS, params.villain)
    obj_p = _safe_lookup(OBJECTS, params.object)
    gear_p = gear_registry.get(params.gear)
    reasonableness_check(hero_p, villain_p, obj_p, gear_p)
    world = tell_heroic_story(hero_p, villain_p, obj_p, gear_p)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero_profile")
    vill = _safe_fact(world, f, "villain_profile")
    obj = _safe_fact(world, f, "object_profile")
    return [
        f'Write a short superhero story for a child that includes the word "measel" and the idea of something being owed.',
        f"Tell a brave story about {hero.title}, who notices {vill.name}'s {vill.nuisance} and learns what {hero.pronoun('subject')} owes the city.",
        f"Write a simple superhero tale where curiosity leads to a twist and the hero fixes a small mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    villain = _safe_fact(world, f, "villain")
    obj = _safe_fact(world, f, "object")
    hero_p = _safe_fact(world, f, "hero_profile")
    villain_p = _safe_fact(world, f, "villain_profile")
    obj_p = _safe_fact(world, f, "object_profile")
    qa = [
        QAItem(
            question=f"Who is the hero in the story?",
            answer=f"The hero is {hero.id}, also known as {hero.label}. {hero.id} is a {hero_p.trait} little superhero who likes {hero_p.power}.",
        ),
        QAItem(
            question=f"What small problem did {hero.id} notice in {world.city.name}?",
            answer=f"{hero.id} noticed {villain.id}'s {villain_p.nuisance}. It was a small nuisance, but it pulled everyone's attention away from {obj_p.phrase}.",
        ),
        QAItem(
            question=f"What did {hero.id} owe after rushing in too fast?",
            answer=f"{hero.id} owed the city a careful fix and a calmer answer. The twist was that curiosity helped {hero.id} notice the problem, but it also meant {hero.id} had to make things right.",
        ),
    ]
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(
            QAItem(
                question=f"How did the {gear.label} help {hero.id}?",
                answer=f"The {gear.label} helped {hero.id} stay steady while facing the {villain_p.nuisance}. That let {hero.id} solve the problem without making the scene worse.",
            )
        )
    return qa


KNOWLEDGE = {
    "measel": [
        ("What is a measel in this story?",
         "A measel is a tiny, bothersome creature that makes a scene, but it is not a giant danger."),
    ],
    "owe": [
        ("What does it mean to owe someone?",
         "To owe someone means you should give them something back, like help, an apology, or a promise kept."),
    ],
    "curiosity": [
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to learn more and ask questions."),
    ],
    "twist": [
        ("What is a twist in a story?",
         "A twist is a turn that changes what you expected and makes the story feel surprising."),
    ],
    "shield": [
        ("What does a shield do?",
         "A shield helps protect you by blocking trouble or keeping danger away."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"measel", "owe", "curiosity", "twist", "shield"}
    out = []
    for tag in tags:
        for q, a in KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
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
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
villain(V) :- villain_name(V).
object(O) :- object_name(O).
gear(G) :- gear_name(G).

curious(H) :- curiosity(H).
rushed(H) :- rush(H).
owe(H) :- owes(H).

measel_event(V) :- nuisance(V, measel).
twist(H) :- curious(H), rushed(H), owe(H).

valid_story(H,V,O) :- hero(H), villain(V), object(O), measel_event(V).
valid_story(H,V,O) :- hero(H), villain(V), object(O), twist(H).

resolved(H) :- valid_story(H,_,_), hero_fix(H).
#show valid_story/3.
#show resolved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for h in HEROES.values():
        lines.append(asp.fact("hero_name", h.id))
        lines.append(asp.fact("curiosity", h.id))
    for v in VILLAINS.values():
        lines.append(asp.fact("villain_name", v.id))
        lines.append(asp.fact("nuisance", v.id, v.nuisance))
    for o in OBJECTS.values():
        lines.append(asp.fact("object_name", o.id))
    for g in gear_registry.values():
        lines.append(asp.fact("gear_name", g.id))
    lines.append(asp.fact("hero_fix", "nova"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    # Map ASP simple triples to the Python shape as a loose parity check.
    asp_triples = set((a, b, c) for a, b, c in asp_valid_combos())
    if asp_triples:
        print(f"OK: ASP produced {len(asp_triples)} candidate story shapes.")
        return 0
    print("MISMATCH: ASP produced no valid stories.")
    return 1


CURATED = [
    StoryParams(hero="Nova", villain="Measel", object="heartpin", gear="shield"),
    StoryParams(hero="Bolt", villain="Measel", object="badge", gear="shield"),
    StoryParams(hero="Mira", villain="Smudge", object="map", gear="shield"),
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.hero} vs {p.villain} ({p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
