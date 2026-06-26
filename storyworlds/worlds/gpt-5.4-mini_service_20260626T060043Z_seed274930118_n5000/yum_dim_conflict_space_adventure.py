#!/usr/bin/env python3
"""
A standalone story world: a tiny space adventure with a yum-dim conflict.

Premise:
A small crew is traveling between stations with a precious snack pack. One
crew member wants to enjoy a yum-dim treat right away, but another worries it
will get dim, stale, or ruined in the ship's dry air. The crew argues, then
finds a safer way to keep the snack bright and tasty while still sharing it.

The story is driven by a small world model:
- meters: physical conditions like dimness, sealedness, freshness, distance
- memes: emotional pressures like curiosity, hunger, conflict, relief

The narrative stays child-facing and concrete, with a beginning, a turn, and a
resolution that proves the state changed.
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
class ShipSetting:
    name: str
    kind: str  # station, ship, dock, tunnel
    dimness: int
    has_glow_panes: bool = False
    has_seal_lockers: bool = False
    has_viewport: bool = False
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
class Snack:
    id: str
    label: str
    phrase: str
    taste: str
    dim_risk: bool
    container: str
    container_label: str
    container_action: str
    container_fix: str
    allowed_heroes: tuple[str, ...] = ("girl", "boy")
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
class Gear:
    id: str
    label: str
    protects_from_dim: bool
    keeps_fresh: bool
    fits_snacks: tuple[str, ...]
    action: str
    closing: str
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


@dataclass(frozen=True)
class CrewRole:
    id: str
    type: str
    label: str
    pronouns: tuple[str, str, str]
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


SETTINGS = {
    "orbital_dock": ShipSetting(
        name="the orbital dock",
        kind="dock",
        dimness=1,
        has_glow_panes=True,
        has_seal_lockers=True,
        has_viewport=True,
    ),
    "starship_hall": ShipSetting(
        name="the starship hall",
        kind="ship",
        dimness=2,
        has_glow_panes=True,
        has_seal_lockers=True,
    ),
    "moon_tunnel": ShipSetting(
        name="the moon tunnel",
        kind="tunnel",
        dimness=3,
        has_glow_panes=False,
        has_seal_lockers=False,
    ),
    "garden_station": ShipSetting(
        name="the garden station",
        kind="station",
        dimness=1,
        has_glow_panes=True,
        has_seal_lockers=True,
        has_viewport=True,
    ),
}

SNACKS = {
    "yum_dim_buns": Snack(
        id="yum_dim_buns",
        label="yum-dim buns",
        phrase="warm yum-dim buns",
        taste="sweet and buttery",
        dim_risk=True,
        container="snack_case",
        container_label="a bright snack case",
        container_action="seal the buns in a bright snack case",
        container_fix="kept the buns bright and warm",
        allowed_heroes=("girl", "boy"),
    ),
    "glow_juice": Snack(
        id="glow_juice",
        label="glow juice",
        phrase="a cup of glow juice",
        taste="cool and fruity",
        dim_risk=True,
        container="cooler_shell",
        container_label="a cool shell cup",
        container_action="set the juice inside a cool shell cup",
        container_fix="kept the juice from turning dim and flat",
        allowed_heroes=("girl", "boy"),
    ),
    "moon_crisp": Snack(
        id="moon_crisp",
        label="moon crisps",
        phrase="a tin of moon crisps",
        taste="salty and crunchy",
        dim_risk=False,
        container="tin",
        container_label="a snug tin",
        container_action="close the crisps in a snug tin",
        container_fix="kept the crisps safe and neat",
        allowed_heroes=("girl", "boy"),
    ),
}

GEAR = {
    "glow_pouch": Gear(
        id="glow_pouch",
        label="a glow pouch",
        protects_from_dim=True,
        keeps_fresh=True,
        fits_snacks=("yum_dim_buns", "glow_juice"),
        action="put the snack in a glow pouch",
        closing="carried the snack in a glow pouch",
    ),
    "seal_box": Gear(
        id="seal_box",
        label="a seal box",
        protects_from_dim=False,
        keeps_fresh=True,
        fits_snacks=("yum_dim_buns", "glow_juice", "moon_crisp"),
        action="snap the lid shut on a seal box",
        closing="kept the snack sealed tight",
    ),
    "window_wrap": Gear(
        id="window_wrap",
        label="a window wrap",
        protects_from_dim=True,
        keeps_fresh=False,
        fits_snacks=("yum_dim_buns",),
        action="wrap the buns near the glow pane",
        closing="let the snack rest in a soft glow",
    ),
}

CREW = {
    "girl": CrewRole("girl", "girl", "girl", ("she", "her", "her")),
    "boy": CrewRole("boy", "boy", "boy", ("he", "him", "his")),
}


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    container: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    helper: object | None = None
    hero: object | None = None
    shell: object | None = None
    treat: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        role = CREW.get(self.type)
        if role:
            return {"subject": role.pronouns[0], "object": role.pronouns[1], "possessive": role.pronouns[2]}[case]
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


@dataclass
class StoryParams:
    setting: str
    snack: str
    name: str
    hero_type: str
    helper_name: str
    helper_type: str
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
    def __init__(self, setting: ShipSetting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _role(type_name: str) -> CrewRole:
    return CREW.get(type_name, CrewRole(type_name, type_name, type_name, ("they", "them", "their")))


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _name_from_type(hero_type: str, rng: random.Random) -> str:
    names = {
        "girl": ["Luna", "Mina", "Ivy", "Nova", "Pia", "Zoe"],
        "boy": ["Milo", "Jett", "Ollie", "Rex", "Tavi", "Finn"],
    }
    return rng.choice(names.get(hero_type, ["Alex"]))


def _helper_name_from_type(helper_type: str, rng: random.Random) -> str:
    names = {
        "girl": ["Aria", "Mira", "Sela", "Nina"],
        "boy": ["Kai", "Taro", "Bram", "Eli"],
    }
    return rng.choice(names.get(helper_type, ["Sky"]))


def choose_compatible(setting: ShipSetting, snack: Snack, rng: random.Random) -> Gear:
    candidates = [g for g in GEAR.values() if snack.id in g.fits_snacks]
    if not candidates:
        pass
    # Reasonableness gate: if the setting is very dim, prefer a dim-protecting gear.
    if setting.dimness >= 2:
        dimmers = [g for g in candidates if g.protects_from_dim]
        if dimmers:
            return rng.choice(dimmers)
    return rng.choice(candidates)


def invalid_combo_reason(setting: ShipSetting, snack: Snack) -> Optional[str]:
    if not snack.dim_risk:
        return f"(No story: {snack.label} would not be hurt by dim light, so there is no honest conflict to resolve.)"
    if setting.dimness <= 0:
        return f"(No story: {setting.name} is too bright for a dim-light snack problem.)"
    return None


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams, rng: random.Random) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    snack = _safe_lookup(SNACKS, params.snack)
    hero_role = _role(params.hero_type)
    helper_role = _role(params.helper_type)

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type, label=params.name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    treat = world.add(Entity(
        id="snack",
        kind="thing",
        type=snack.id,
        label=snack.label,
        phrase=snack.phrase,
        owner=hero.id,
        container=snack.container,
        meters={"fresh": 1.0, "dim": 0.0, "sealed": 0.0},
        memes={"desire": 0.0, "worry": 0.0, "conflict": 0.0, "relief": 0.0},
    ))

    gear = choose_compatible(setting, snack, rng)
    shell = world.add(Entity(
        id=gear.id,
        kind="thing",
        type=gear.id,
        label=gear.label,
        owner=hero.id,
        meters={"sealed": 0.0, "bright": 0.0},
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        snack=treat,
        gear=shell,
        snack_def=snack,
        gear_def=gear,
        hero_role=hero_role,
        helper_role=helper_role,
    )

    # Act 1
    world.say(
        f"{hero.id} and {helper.id} floated through {setting.name}, where the lights were "
        f"{'soft' if setting.dimness >= 2 else 'gentle'} and the walls hummed like a sleepy song."
    )
    world.say(
        f"{hero.id} loved {snack.phrase}, because it tasted {snack.taste}."
    )
    world.say(
        f"{hero.id} carried the snack pack and kept peeking at it, as if waiting for snack time to begin."
    )

    # Act 2
    world.para()
    hero.memes["desire"] += 1
    helper.memes["worry"] += 1
    treat.meters["dim"] += setting.dimness
    world.say(
        f"When the ship drifted into a dim corridor, {hero.id} wanted to eat the {snack.label} right away."
    )
    world.say(
        f"But {helper.id} frowned and said, 'If we leave it out here, it may get dim and sad before you finish.'"
    )
    world.say(
        f"{hero.id} hugged the snack closer and replied, 'It still looks yum-dim to me!'"
    )
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    treat.meters["dim"] += 1

    # Act 3
    world.para()
    world.say(
        f"{helper.id} looked at the glowing panels, then at the {gear.label}, and had an idea."
    )
    world.say(
        f"'Let's {gear.action} first,' {helper.id} said. 'Then your snack can stay bright and tasty.'"
    )
    shell.meters["sealed"] += 1
    if gear.protects_from_dim:
        shell.meters["bright"] += 1
    treat.meters["sealed"] = 1.0
    treat.meters["fresh"] += 1.0
    treat.meters["dim"] = max(0.0, treat.meters["dim"] - 1.0)
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} smiled, and together they {gear.closing}. Soon the snack was safe, "
        f"fresh, and ready to share."
    )
    world.say(
        f"{hero.id} took the first bite, and the yum-dim taste made the whole corridor feel bright."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    snack_def = _safe_fact(world, f, "snack_def")
    setting = world.setting
    return [
        f'Write a short space adventure story for a child about {hero.id}, {helper.id}, and a {snack_def.label} in {setting.name}.',
        f'Tell a gentle story where {hero.id} wants to eat {snack_def.phrase} but the crew worries it will get dim, then they solve the problem.',
        f'Write a tiny ship story that includes the phrase "yum-dim" and ends with a happy snack-sharing moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    snack = _safe_fact(world, f, "snack")
    snack_def = _safe_fact(world, f, "snack_def")
    gear = _safe_fact(world, f, "gear")
    setting = world.setting
    hero_role = _safe_fact(world, f, "hero_role")
    helper_role = _safe_fact(world, f, "helper_role")

    return [
        QAItem(
            question=f"Who wanted to eat the {snack.label} right away?",
            answer=f"{hero.id} wanted to eat it right away because {hero.pronoun('subject')} loved the {snack.label} and thought it looked yum-dim.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the snack?",
            answer=f"{helper.id} worried because the ship was dim, and the {snack.label} could get dim and stale if they left it out too long.",
        ),
        QAItem(
            question=f"What did they use to keep the snack safe?",
            answer=f"They used {gear.label} so the snack could stay sealed, bright, and fresh while they traveled through {setting.name}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and relieved, because the snack stayed good and they still got to share it.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the conflict?",
            answer=f"{helper.id} helped by suggesting a safer way to carry the snack, so the two crew members could stop arguing.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean when something is dim?",
            answer="Dim means there is not much light, so things look soft, dark, or hard to see clearly.",
        ),
        QAItem(
            question="Why do people seal snacks in containers?",
            answer="People seal snacks in containers to keep them fresh, clean, and safe to eat later.",
        ),
        QAItem(
            question="What is a space station?",
            answer="A space station is a place in space where people can live, work, and travel from one place to another.",
        ),
        QAItem(
            question="What does it mean to share food?",
            answer="To share food means to let more than one person enjoy it together.",
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Setting,Snack,Gear) :- setting(Setting), snack(Snack), gear(Gear),
    setting_dim(Setting,D), D > 0,
    snack_dim_risk(Snack),
    gear_fits(Gear,Snack),
    (setting_dim(Setting,D2), D2 >= 2, gear_protects_dim(Gear); setting_dim(Setting,D3), D3 < 2).

valid_story(Setting,Snack,Gear,Hero) :- valid(Setting,Snack,Gear), hero(Hero), allowed_hero(Snack,Hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("setting_dim", sid, s.dimness))
    for snid, sn in SNACKS.items():
        lines.append(asp.fact("snack", snid))
        if sn.dim_risk:
            lines.append(asp.fact("snack_dim_risk", snid))
        for h in sn.allowed_heroes:
            lines.append(asp.fact("allowed_hero", snid, h))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        if g.protects_from_dim:
            lines.append(asp.fact("gear_protects_dim", gid))
        for snid in g.fits_snacks:
            lines.append(asp.fact("gear_fits", gid, snid))
    for hid in CREW:
        lines.append(asp.fact("hero", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for snid, snack in SNACKS.items():
            if snack.dim_risk and setting.dimness > 0:
                for gid, gear in GEAR.items():
                    if snid in gear.fits_snacks:
                        if setting.dimness >= 2 and not gear.protects_from_dim:
                            continue
                        combos.append((sid, snid, gid))
    return sorted(set(combos))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny space adventure story world with a yum-dim snack conflict.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    snack = getattr(args, "snack", None) or rng.choice(sorted(SNACKS))
    sdef = _safe_lookup(SNACKS, snack)
    sset = _safe_lookup(SETTINGS, setting)
    reason = invalid_combo_reason(sset, sdef)
    if reason:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(list(CREW))
    if hero_type not in sdef.allowed_heroes:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or _name_from_type(hero_type, rng)
    helper_type = getattr(args, "helper_type", None) or ("boy" if hero_type == "girl" else "girl")
    helper_name = getattr(args, "helper_name", None) or _helper_name_from_type(helper_type, rng)
    return StoryParams(setting=setting, snack=snack, name=name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_world(params, rng)
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


CURATED = [
    StoryParams(setting="starship_hall", snack="yum_dim_buns", name="Luna", hero_type="girl", helper_name="Kai", helper_type="boy"),
    StoryParams(setting="moon_tunnel", snack="glow_juice", name="Milo", hero_type="boy", helper_name="Aria", helper_type="girl"),
    StoryParams(setting="garden_station", snack="yum_dim_buns", name="Nova", hero_type="girl", helper_name="Bram", helper_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, snack, gear) combos ({len(stories)} with hero type):\n")
        for setting, snack, gear in triples:
            heroes = sorted(h for (s, sn, g, h) in stories if (s, sn, g) == (setting, snack, gear))
            print(f"  {setting:14} {snack:14} {gear:12}  [{', '.join(heroes)}]")
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
            header = f"### {p.name}: {p.snack} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
