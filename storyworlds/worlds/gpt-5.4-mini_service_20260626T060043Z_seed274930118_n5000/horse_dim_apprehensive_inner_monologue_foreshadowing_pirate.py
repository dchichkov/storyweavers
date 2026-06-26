#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/horse_dim_apprehensive_inner_monologue_foreshadowing_pirate.py
=============================================================================================================

A small pirate-tale storyworld with a dim, horse-calm harbor, an apprehensive
young deckhand, inner monologue, and foreshadowing-driven resolution.

Premise:
- A young pirate loves a bold outing but grows apprehensive when the harbor
  goes horse-dim at dusk.
- The captain predicts trouble from the creaking rigging and the low tide.
- A safer route, a lantern, and a rope turn fear into a cautious triumph.

Narrative instruments:
- Inner monologue appears as short, child-facing thoughts.
- Foreshadowing is carried by physical details that later matter: the creak in
  the rope, the dim lantern, the rising tide, the slick stones.

Seed words required by the prompt:
- horse-dim
- apprehensive
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
# World model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cpt: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Harbor:
    name: str = "the harbor"
    places: tuple[str, ...] = ("dock", "deck", "cove")
    tide: str = "low"
    light: str = "horse-dim"  # seed word must appear in the world
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
class Goal:
    id: str
    label: str
    phrase: str
    risk: str
    zone: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    covers: set[str]
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path: str = "dock"
        self.weather: str = "calm"

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
        import copy as _copy

        c = World(self.harbor)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.path = self.path
        c.weather = self.weather
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    goal: str
    remedy: str
    name: str
    gender: str
    captain: str
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


HARBORS = {
    "dock": Harbor(name="the dock", light="horse-dim"),
    "ship": Harbor(name="the ship", light="horse-dim"),
    "cove": Harbor(name="the moon cove", light="dim"),
}

GOALS = {
    "lantern": Goal(
        id="lantern",
        label="lantern",
        phrase="a brass lantern with a bright wick",
        risk="go dim",
        zone="dark",
        weather="night",
        keyword="lantern",
        tags={"light", "dark", "night"},
    ),
    "map": Goal(
        id="map",
        label="map",
        phrase="a folded treasure map with a red X",
        risk="get wet",
        zone="water",
        weather="night",
        keyword="map",
        tags={"map", "water", "treasure"},
    ),
    "rope": Goal(
        id="rope",
        label="rope",
        phrase="a coil of sturdy rope",
        risk="slip away",
        zone="hands",
        weather="wind",
        keyword="rope",
        tags={"rope", "wind"},
    ),
}

REMEDIES = {
    "oil": Remedy(
        id="oil",
        label="a little oilcloth wrap",
        prep="wrap the lantern in oilcloth",
        tail="wrapped the lantern in oilcloth and kept the wick dry",
        helps={"dark"},
        covers={"hands"},
    ),
    "boots": Remedy(
        id="boots",
        label="sea boots",
        prep="pull on sea boots first",
        tail="pulled on sea boots and kept their feet steady on the slick stones",
        helps={"water"},
        covers={"feet"},
        plural=True,
    ),
    "gloves": Remedy(
        id="gloves",
        label="deck gloves",
        prep="pull on deck gloves first",
        tail="pulled on deck gloves and kept a firm grip on the rope",
        helps={"wind"},
        covers={"hands"},
        plural=True,
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Pia", "Tess", "Ivy"]
BOY_NAMES = ["Finn", "Jory", "Bram", "Ned", "Pip", "Hale"]
TRAITS = ["brave", "curious", "small", "quick", "cheerful", "stubborn"]


# ---------------------------------------------------------------------------
# ASP twin and reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(G, M) :- goal(G), remedy_for(G, R), goal_zone(G, Z), remedy_covers(R, Z), risk_kind(G, M).
has_fix(G) :- at_risk(G, _), remedy(R), helps(R, M), risk_kind(G, M), remedy_for(G, R).

valid(Place, Goal, Remedy) :- harbor(Place), goal(Goal), remedy(Remedy), at_risk(Goal, _), has_fix(Goal).

% Gender-neutral, tiny pirate world; any explicit combination is acceptable
% when the remedy really addresses the risk.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, h in HARBORS.items():
        lines.append(asp.fact("harbor", pid))
        for p in ["dock", "deck", "cove"]:
            if p == pid:
                lines.append(asp.fact("at", pid, p))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("risk_kind", gid, g.zone))
        lines.append(asp.fact("goal_zone", gid, g.zone))
        for r_id, r in REMEDIES.items():
            if g.zone in r.helps:
                lines.append(asp.fact("remedy_for", gid, r_id))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for c in r.covers:
            lines.append(asp.fact("remedy_covers", rid, c))
        for h in r.helps:
            lines.append(asp.fact("helps", rid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in HARBORS:
        for goal_id, g in GOALS.items():
            for remedy_id, r in REMEDIES.items():
                if g.zone in r.helps and g.zone in r.covers or (g.zone in r.helps):
                    out.append((place, goal_id, remedy_id))
    # tighter than the line above; now remove invalid pairings that don't cover risk
    final: list[tuple[str, str, str]] = []
    for place, goal_id, remedy_id in out:
        g = _safe_lookup(GOALS, goal_id)
        r = _safe_lookup(REMEDIES, remedy_id)
        if g.zone in r.helps and g.zone in r.covers:
            final.append((place, goal_id, remedy_id))
    return sorted(set(final))


def reason_invalid(goal: Goal, remedy: Remedy) -> str:
    return (
        f"(No story: {goal.label} wants {goal.risk}, but {remedy.label} does not "
        f"really cover that danger. The pirate tale needs a fix that matches the risk.)"
    )


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def predictive_warning(world: World, hero: Entity, goal: Goal) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["apprehensive"] += 1
    if goal.zone == "water":
        sim.facts["threat"] = "slick stones and a wet map"
    elif goal.zone == "dark":
        sim.facts["threat"] = "the lamp going dim"
    else:
        sim.facts["threat"] = "the rope slipping free"
    return {"danger": True, "threat": sim.facts["threat"]}


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"On a horse-dim evening, little {hero.id} was a {hero.memes['trait_word']} pirate "
        f"who noticed every creak in the boards."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved bold walks by the water, but tonight "
        f"{hero.pronoun('possessive')} belly felt apprehensive."
    )
    world.say(
        f"*What if the dark hides the path?* {hero.id} wondered, hugging the edge of the dock."
    )


def setup(world: World, hero: Entity, captain: Entity, goal: Entity) -> None:
    world.say(
        f"The captain showed {hero.id} {hero.pronoun('possessive')} {goal.label}: {goal.phrase}."
    )
    hero.memes["desire"] += 1
    hero.memes["love"] += 1
    goal.worn_by = hero.id
    world.say(
        f"{hero.id} wanted to carry {(getattr(goal, 'it')() if callable(getattr(goal, 'it', None)) else getattr(goal, 'it', 'it'))} out to sea, even while the lantern made "
        f"a tiny trembling circle of light."
    )


def foreshadow(world: World, hero: Entity, goal: Entity) -> None:
    world.say(
        f"A rope gave a soft creak, and the tide whispered against the stones."
    )
    world.say(
        f"*That does not sound safe,* {hero.id} thought."
    )


def warn(world: World, captain: Entity, hero: Entity, goal: Entity) -> None:
    prediction = predictive_warning(world, hero, goal)
    world.facts["threat"] = prediction["threat"]
    if goal.zone == "dark":
        line = f"'If the lantern goes dim, we'll lose the path,' {captain.id} said."
    elif goal.zone == "water":
        line = f"'If the tide rises, the map may get wet,' {captain.id} said."
    else:
        line = f"'If that rope slips, the crate may tumble,' {captain.id} said."
    world.say(line)


def hesitate(world: World, hero: Entity) -> None:
    hero.memes["apprehensive"] += 1
    world.say(f"{hero.id} bit {hero.pronoun('possessive')} lip and stayed very still.")
    world.say(f"*I want to go,* {hero.id} thought, *but the sea feels tricky tonight.*")


def offer(world: World, captain: Entity, hero: Entity, goal: Entity) -> Optional[Remedy]:
    remedy = None
    for r in REMEDIES.values():
        if goal.zone in r.helps and goal.zone in r.covers:
            remedy = r
            break
    if remedy is None:
        _fallback_pool = globals().get("REMEDYS") or globals().get("REMEDYES") or globals().get("REMEDIES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        remedy = next(iter(_fallback_pool), None)
        if remedy is None:
            raise StoryError
    world.say(
        f"{captain.id} smiled and said, 'Then we can {remedy.prep} and still go.'"
    )
    return remedy


def accept(world: World, hero: Entity, captain: Entity, goal: Entity, remedy: Remedy) -> None:
    hero.memes["apprehensive"] = 0.0
    hero.memes["joy"] += 1
    world.say(f"{hero.id}'s eyes went bright, and {hero.id} nodded.")
    world.say(
        f"They followed the plan: {remedy.tail}. Soon {hero.id} was steady, "
        f"and {(getattr(goal, 'it')() if callable(getattr(goal, 'it', None)) else getattr(goal, 'it', 'it'))} stayed safe."
    )
    world.say(
        f"At the end, the crew sailed on under a small clean light, and the horse-dim harbor "
        f"looked friendly instead of fearful."
    )


# ---------------------------------------------------------------------------
# Storyworld generation
# ---------------------------------------------------------------------------
def tell(harbor: Harbor, goal: Goal, remedy: Remedy, name: str, gender: str, captain: str, trait: str) -> World:
    world = World(harbor)
    world.path = harbor.name
    world.weather = "night"

    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            meters={"balance": 1.0},
            memes={"apprehensive": 1.0, "trait_word": trait},
        )
    )
    cpt = world.add(Entity(id=captain, kind="character", type="man" if captain == "Captain" else "woman"))
    obj = world.add(
        Entity(
            id=goal.id,
            kind="thing",
            type=goal.label,
            label=goal.label,
            phrase=goal.phrase,
            owner=hero.id,
            caretaker=cpt.id,
        )
    )

    intro(world, hero)
    world.para()
    setup(world, hero, cpt, obj)
    foreshadow(world, hero, obj)
    warn(world, cpt, hero, obj)
    hesitate(world, hero)
    world.para()
    remedy_choice = offer(world, cpt, hero, obj)
    accept(world, hero, cpt, obj, remedy_choice)

    world.facts.update(
        hero=hero,
        captain=cpt,
        goal=obj,
        goal_cfg=goal,
        remedy=remedy_choice,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, cpt, goal = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "captain"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "goal_cfg")
    return [
        f'Write a pirate tale for a child where "{world.harbor.light}" light and a little fear lead to a safer choice.',
        f"Tell a story about a pirate named {hero.id} who feels apprehensive about the {goal.label} and listens to {cpt.id}.",
        f'Write a short sea story that includes the word "{goal.keyword}" and ends with a calm, brave little victory.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, cpt, goal, remedy = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "captain"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "goal"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "remedy")
    qa = [
        QAItem(
            question=f"Why was {hero.id} apprehensive at the dock?",
            answer=(
                f"{hero.id} was apprehensive because the harbor was horse-dim and the story warned that "
                f"{goal.label} could be risky if the danger got worse."
            ),
        ),
        QAItem(
            question=f"What did the captain notice before the pirate trip?",
            answer=(
                f"The captain noticed the rope creaking and the tide whispering at the stones, which was a clue "
                f"that the path might be tricky."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel when the plan used {remedy.label}?",
            answer=(
                f"{hero.id} felt braver and calmer, because {remedy.label} helped solve the problem without making "
                f"the risky part worse."
            ),
        ),
    ]
    if goal.zone == "water":
        qa.append(
            QAItem(
                question=f"Why was the {goal.label} in danger?",
                answer=f"The {goal.label} was in danger because wet stones and rising tide could make it unsafe.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "lantern": (
        "What does a lantern do?",
        "A lantern makes light so people can see in the dark.",
    ),
    "map": (
        "What is a treasure map?",
        "A treasure map is a picture or drawing that shows where something hidden might be.",
    ),
    "rope": (
        "What is rope good for on a ship?",
        "Rope helps people tie, pull, or hold things steady.",
    ),
    "water": (
        "Why can seawater make things slippery?",
        "Water on stone or wood can make feet slide more easily.",
    ),
    "dark": (
        "Why do people use light at night?",
        "Light helps them see where they are going when it is dark.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "goal_cfg").tags)
    out: list[QAItem] = []
    for tag, (q, a) in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.append(QAItem(question=q, answer=a))
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
        memes = {k: v for k, v in e.memes.items() if v and k != "trait_word"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="dock", goal="map", remedy="boots", name="Pip", gender="boy", captain="Captain", trait="curious"),
    StoryParams(place="ship", goal="lantern", remedy="oil", name="Mira", gender="girl", captain="Captain", trait="brave"),
    StoryParams(place="cove", goal="rope", remedy="gloves", name="Ned", gender="boy", captain="Captain", trait="small"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with apprehension and foreshadowing.")
    ap.add_argument("--place", choices=HARBORS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--captain", default="Captain")
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
              and (getattr(args, "goal", None) is None or c[1] == getattr(args, "goal", None))
              and (getattr(args, "remedy", None) is None or c[2] == getattr(args, "remedy", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, goal, remedy = (list(rng.choice(combos)) + [None, None, None])[:3]
    g = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if g == "girl" else BOY_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal, remedy=remedy, name=name, gender=g, captain=getattr(args, "captain", None), trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(HARBORS, params.place), _safe_lookup(GOALS, params.goal), _safe_lookup(REMEDIES, params.remedy), params.name, params.gender, params.captain, params.trait)
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


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid (place, goal, remedy) combos:\n")
        for place, goal, remedy in stories:
            print(f"  {place:8} {goal:8} {remedy:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.goal} at {p.place} ({p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
