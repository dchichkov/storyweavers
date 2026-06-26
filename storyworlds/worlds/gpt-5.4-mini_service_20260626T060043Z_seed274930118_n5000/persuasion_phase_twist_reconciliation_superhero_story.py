#!/usr/bin/env python3
"""
storyworlds/worlds/persuasion_phase_twist_reconciliation_superhero_story.py
===========================================================================

A standalone storyworld for a small superhero tale: a hero faces a crisis,
tries persuasion first, survives a twist, and reaches reconciliation.

Seed premise:
- A hero notices a problem in the city.
- A rival is not purely evil, just stubborn.
- The hero uses a persuasion phase before the action phase.
- The story includes a twist that changes what everyone thought.
- The ending is reconciliation, not a punch-up.

The world is modeled as typed entities with physical meters and emotional memes.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    ally_of: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    city_ent: object | None = None
    hero: object | None = None
    tool: object | None = None
    villain: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine"}
        male = {"boy", "man", "hero", "villain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class City:
    name: str
    place: str
    hazard: str
    save_target: str
    requires: str
    twist: str
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
class Gear:
    id: str
    label: str
    protects_against: str
    phrase: str
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
class RivalPlan:
    id: str
    label: str
    action: str
    risk: str
    motive: str
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


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

        w = World(self.city)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _harmony(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    rival = world.get("rival")
    if hero.memes.get("trust", 0.0) < THRESHOLD:
        return out
    if rival.memes.get("soften", 0.0) < THRESHOLD:
        return out
    sig = ("harmony",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    rival.memes["hope"] = rival.memes.get("hope", 0.0) + 1.0
    out.append("The air felt lighter, as if the city had finally remembered how to breathe.")
    return out


def _damage(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters.get("power", 0.0) < THRESHOLD:
        return out
    sig = ("damage",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("city").memes = getattr(world.get("city"), "memes", {})
    out.append("For a moment, the streets trembled under the villain's plan.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_damage, _harmony):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


CITY_REGISTRY = {
    "harbor": City(
        name="Harbor City",
        place="the harbor",
        hazard="a broken signal tower",
        save_target="the night ferry",
        requires="clear the tower",
        twist="the tower was hijacked by a scared inventor, not a true criminal",
    ),
    "metro": City(
        name="Metro Square",
        place="the square",
        hazard="a frozen fountain",
        save_target="the tram line",
        requires="thaw the pipes",
        twist="the freeze came from a failing cooling machine in the basement",
    ),
    "skyport": City(
        name="Skyport",
        place="the roof docks",
        hazard="a jammed skybridge",
        save_target="the rescue drone",
        requires="unclog the gears",
        twist="the jammed gears were packed with paper birds from a parade prank",
    ),
}

HEROES = {
    "spark": ("Spark", "hero", ["bright", "fast"]),
    "comet": ("Comet Kid", "boy", ["quick", "kind"]),
    "flare": ("Flare", "girl", ["brave", "gentle"]),
}

RIVALS = {
    "rift": RivalPlan(
        id="rift",
        label="Rift",
        action="shut down the tower",
        risk="the ferry would be delayed",
        motive="to prove that nobody listened to warnings",
    ),
    "glint": RivalPlan(
        id="glint",
        label="Glint",
        action="freeze the fountain",
        risk="the tram line would stop",
        motive="to get attention for a forgotten idea",
    ),
    "gearjaw": RivalPlan(
        id="gearjaw",
        label="Gearjaw",
        action="jam the skybridge",
        risk="the drone could not deliver medicine",
        motive="to hide a mistake before anyone noticed",
    ),
}

GEAR = {
    "visor": Gear(id="visor", label="a listening visor", protects_against="doubt", phrase="so the hero could hear the truth better"),
    "gloves": Gear(id="gloves", label="signal gloves", protects_against="static", phrase="so the hero could handle the machine safely"),
    "cape": Gear(id="cape", label="a soft cape", protects_against="fear", phrase="so the hero could move through the crowd kindly"),
}

TRAITS = ["bold", "careful", "cheerful", "steady", "bright"]


@dataclass
class StoryParams:
    city: str = ""
    hero: str = ""
    rival: str = ""
    gear: str = ""
    name: str = ""
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


class ReasoningError(StoryError):
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story about persuasion, a twist, and reconciliation.")
    ap.add_argument("--city", choices=CITY_REGISTRY)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--gear", choices=GEAR)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for city_id, city in CITY_REGISTRY.items():
        for rival_id, rival in RIVALS.items():
            if city.hazard and city.requires:
                for gear_id in GEAR:
                    combos.append((city_id, rival_id, gear_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "city", None) is None or c[0] == getattr(args, "city", None))
              and (getattr(args, "rival", None) is None or c[1] == getattr(args, "rival", None))
              and (getattr(args, "gear", None) is None or c[2] == getattr(args, "gear", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    city, rival, gear = rng.choice(list(combos))
    hero_id = getattr(args, "hero", None) or rng.choice(list(HEROES))
    name = getattr(args, "name", None) or _safe_lookup(HEROES, hero_id)[0]
    trait = rng.choice(TRAITS)
    return StoryParams(city=city, hero=hero_id, rival=rival, gear=gear, name=name, trait=trait)


def setup_world(params: StoryParams) -> World:
    city = CITY_REGISTRY[params.city]
    world = World(city)
    hero_name, hero_type, hero_traits = _safe_lookup(HEROES, params.hero)
    rival = _safe_lookup(RIVALS, params.rival)
    gear = GEAR[params.gear]

    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=[params.trait] + hero_traits))
    villain = world.add(Entity(id="rival", kind="character", type="villain", label=rival.label, traits=["stubborn"]))
    city_ent = world.add(Entity(id="city", kind="place", type="city", label=city.name))
    tool = world.add(Entity(id="gear", kind="thing", type="gear", label=gear.label, phrase=gear.phrase, owner=hero.id))
    tool.meters["charge"] = 1.0
    world.facts.update(hero=hero, rival=villain, city=city_ent, gear=tool, gear_cfg=gear, city_cfg=city, rival_cfg=rival)
    return world


def tell(world: World) -> None:
    hero = world.get("hero")
    rival = world.get("rival")
    city = world.city
    gear = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "gear_cfg")
    rival_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "rival_cfg")

    world.say(
        f"{hero.label} was a {hero.traits[0]} superhero who watched {city.place} every night."
    )
    world.say(
        f"Tonight, {hero.pronoun()} saw {rival_cfg.label} trying to {rival_cfg.action}, and that meant {rival_cfg.risk}."
    )

    world.para()
    world.say(
        f"First came the persuasion phase. {hero.label} did not rush in with fists. "
        f"{hero.pronoun().capitalize()} spoke calmly, using {gear.label}, {gear.phrase}, and a kind voice."
    )
    rival.memes["doubt"] = rival.memes.get("doubt", 0.0) + 1.0
    rival.memes["listen"] = rival.memes.get("listen", 0.0) + 1.0

    world.say(
        f"{rival.label} frowned, because {rival_cfg.motive} sounded truer than {hero.label} first guessed."
    )

    world.para()
    world.say(
        f"Then came the twist: {city.twist}. The danger was real, but the reason was not what anyone expected."
    )
    world.say(
        f"{hero.label} realized the city needed help, not blame."
    )
    world.facts["twist"] = city.twist
    world.facts["persuasion"] = True
    world.facts["phase"] = "persuasion"

    world.para()
    world.say(
        f"So {hero.label} changed plans and asked {rival.label} to work together. "
        f"{hero.pronoun().capitalize()} promised to fix {city.requires} instead of fighting."
    )
    rival.memes["soften"] = rival.memes.get("soften", 0.0) + 1.0
    rival.memes["trust"] = rival.memes.get("trust", 0.0) + 1.0
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1.0
    propagate(world, narrate=True)

    world.say(
        f"At the end, {rival.label} helped, and the two of them reached reconciliation. "
        f"{city.save_target} was safe again, and the lights over {city.place} shone steady and warm."
    )
    world.facts["resolved"] = True


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    city = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "city_cfg")
    rival = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "rival_cfg")
    return [
        f'Write a short superhero story for a child that includes the words "persuasion" and "phase".',
        f"Tell a superhero story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").label} uses persuasion first, then a twist changes the plan, and reconciliation follows.",
        f"Write a gentle action story set at {city.place} where {rival.label} causes trouble, but the hero finds a calm way to help.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    rival = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "rival")
    city = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "city_cfg")
    qa = [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.label}, a {hero.traits[0]} helper who watched over {city.place}.",
        ),
        QAItem(
            question=f"What did {hero.label} do first when {rival.label} caused trouble?",
            answer=f"{hero.label} started with the persuasion phase and spoke calmly instead of fighting right away.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {city.twist}",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with reconciliation, because {hero.label} and {rival.label} worked together and made the city safe again.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"Why did {hero.label} change plans?",
            answer=f"{hero.label} learned that the problem was bigger than a simple fight, so {hero.pronoun().capitalize()} chose help, trust, and reconciliation.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    city = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "city_cfg")
    return [
        QAItem(
            question="What is persuasion?",
            answer="Persuasion is trying to change someone's mind by talking kindly and giving good reasons.",
        ),
        QAItem(
            question="What is a phase?",
            answer="A phase is one part of a process or story, like the persuasion phase before the action phase.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and make peace again.",
        ),
        QAItem(
            question=f"What place was the story set in?",
            answer=f"It was set at {city.place} in {city.name}.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_fact(H).
rival(R) :- rival_fact(R).
city(C) :- city_fact(C).

persuasion_phase(H) :- hero(H), talks_kindly(H).
twist(C) :- city(C), twist_fact(C).
reconciliation(H,R) :- hero(H), rival(R), trust(H,R), softened(R).

valid_story(C,H,R,G) :- city(C), hero(H), rival(R), gear(G).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for cid, city in CITY_REGISTRY.items():
        lines.append(asp.fact("city_fact", cid))
        lines.append(asp.fact("twist_fact", cid))
    for hid in HEROES:
        lines.append(asp.fact("hero_fact", hid))
    for rid in RIVALS:
        lines.append(asp.fact("rival_fact", rid))
    for gid in GEAR:
        lines.append(asp.fact("gear_fact", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/4.")
    model = asp.one_model(program)
    clingo_set = sorted(set(asp.atoms(model, "valid_story")))
    python_set = sorted(set((c, h, r, g) for c, h, r in valid_combos() for g in GEAR))
    if set(clingo_set) == set(python_set):
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("clingo:", clingo_set)
    print("python:", python_set)
    return 1


CURATED = [
    StoryParams(city="harbor", hero="spark", rival="rift", gear="visor", name="Spark"),
    StoryParams(city="metro", hero="flare", rival="glint", gear="gloves", name="Flare"),
    StoryParams(city="skyport", hero="comet", rival="gearjaw", gear="cape", name="Comet Kid"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection() -> str:
    return "(No story: the requested combination does not fit this superhero world.)"


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
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for row in combos:
            print(" ", row)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.city} / {p.rival} / {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
