#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tote_uniform_teamwork_adventure.py
===============================================================================================================

A small Adventure-style story world about a child, a tote, a uniform, and a
teamwork-based fix.

Premise seed:
- tote
- uniform
- teamwork
- adventure

The simulated world follows a simple causal shape:
1) A child is excited for a little adventure with a team.
2) The child wants to hurry off with a useful tote, but a neat uniform must
   stay clean and ready.
3) A messy or risky route threatens the uniform.
4) The team works together with the tote to carry the right gear, keeping the
   uniform safe and ending the outing on a cheerful note.

This script is standalone and follows the Storyweavers storyworld contract.
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
RISK_KINDS = {"dust", "mud", "paint", "water"}



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
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    held: object | None = None
    hero: object | None = None
    teammate: object | None = None
    tote: object | None = None
    uniform: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "dirty": 0.0, "tired": 0.0, "ready": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "teamwork": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Route:
    id: str
    label: str
    risky_mess: str
    zone: set[str]
    clue: str
    keyword: str
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
class Supply:
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
class HelperItem:
    id: str
    label: str
    phrase: str
    covers: set[str]
    guards: set[str]
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
class Team:
    name: str
    member_count: int
    vibe: str
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
    def __init__(self, route: Route) -> None:
        self.route = route
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set(route.zone)
        self.route_risk: str = route.risky_mess

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
        clone = World(self.route)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.route_risk = self.route_risk
        return clone


@dataclass
class StoryParams:
    route: str
    supply: str
    hero_name: str
    hero_type: str
    teammate_name: str
    teammate_type: str
    team_name: str
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


ROUTES = {
    "trail": Route(
        id="trail",
        label="the trail",
        risky_mess="mud",
        zone={"feet", "legs"},
        clue="The trail had a soft, muddy patch after the rain.",
        keyword="trail",
    ),
    "yard": Route(
        id="yard",
        label="the yard",
        risky_mess="dust",
        zone={"legs", "torso"},
        clue="The yard had a dusty path beside the garden fence.",
        keyword="yard",
    ),
    "workshop": Route(
        id="workshop",
        label="the workshop",
        risky_mess="paint",
        zone={"torso"},
        clue="The workshop smelled like paint and bright things were drying on tables.",
        keyword="workshop",
    ),
    "dock": Route(
        id="dock",
        label="the dock",
        risky_mess="water",
        zone={"feet", "legs"},
        clue="The dock was slick with water from the waves.",
        keyword="dock",
    ),
}

SUPPLIES = {
    "uniform": Supply(
        id="uniform",
        label="uniform",
        phrase="a crisp adventure uniform",
        region="torso",
    ),
    "tote": Supply(
        id="tote",
        label="tote",
        phrase="a sturdy tote bag with a wide strap",
        region="hand",
    ),
}

HELPERS = {
    "tote": HelperItem(
        id="tote_bag",
        label="tote bag",
        phrase="the tote bag",
        covers={"hand"},
        guards={"mud", "dust", "paint", "water"},
        plural=False,
    ),
    "apron": HelperItem(
        id="apron",
        label="apron",
        phrase="an apron",
        covers={"torso"},
        guards={"paint"},
        plural=False,
    ),
    "rain_cloak": HelperItem(
        id="rain_cloak",
        label="rain cloak",
        phrase="a rain cloak",
        covers={"torso"},
        guards={"water"},
        plural=False,
    ),
    "boots": HelperItem(
        id="boots",
        label="boots",
        phrase="sturdy boots",
        covers={"feet"},
        guards={"mud", "water"},
        plural=True,
    ),
}

TEAMS = {
    "scouts": Team(name="scouts", member_count=4, vibe="careful"),
    "crew": Team(name="crew", member_count=3, vibe="helpful"),
    "explorers": Team(name="explorers", member_count=5, vibe="brave"),
}

HERO_NAMES = ["Mia", "Noah", "Ava", "Leo", "Zoe", "Finn", "Lily", "Max"]
TEAMMATE_NAMES = ["June", "Eli", "Ruby", "Owen", "Ivy", "Theo", "Nina", "Sam"]
HERO_TYPES = ["girl", "boy"]
TEAMMATE_TYPES = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for route_id, route in ROUTES.items():
        for supply_id, supply in SUPPLIES.items():
            if supply.region == "torso" and route.risky_mess in {"mud", "dust", "paint", "water"}:
                combos.append((route_id, supply_id))
            elif supply.region == "hand":
                combos.append((route_id, supply_id))
    return combos


def choose_helper(route: Route, supply: Supply) -> Optional[HelperItem]:
    for helper in HELPERS.values():
        if supply.region in helper.covers and route.risky_mess in helper.guards:
            return helper
    return None


def predict_mess(world: World, hero: Entity, route: Route, supply: Entity) -> dict:
    sim = world.copy()
    _do_adventure(sim, sim.get(hero.id), route, narrate=False)
    s = sim.entities[supply.id]
    return {
        "dirty": s.meters["dirty"] >= THRESHOLD,
        "teamwork": sum(e.memes["teamwork"] for e in sim.characters()),
    }


def _do_adventure(world: World, hero: Entity, route: Route, narrate: bool = True) -> None:
    world.zone = set(route.zone)
    hero.meters["mess"] += 1
    hero.memes["joy"] += 1
    for ent in list(world.entities.values()):
        if ent.worn_by == hero.id and ent.protective:
            continue
        if ent.id == "uniform" and ent.worn_by == hero.id:
            if route.risky_mess == "mud" and "feet" in route.zone:
                ent.meters["dirty"] += 1
                ent.meters["mess"] += 1
            elif route.risky_mess == "dust":
                ent.meters["dirty"] += 1
                ent.meters["mess"] += 1
            elif route.risky_mess == "paint":
                ent.meters["dirty"] += 1
                ent.meters["mess"] += 1
            elif route.risky_mess == "water":
                ent.meters["dirty"] += 1
                ent.meters["mess"] += 1


def introduce(world: World, hero: Entity, team: Team) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who loved a good adventure with the {team.name}."
    )


def setup(world: World, hero: Entity, teammate: Entity, supply: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} carried {hero.pronoun('possessive')} {supply.label} and kept "
        f"{supply.phrase} ready for the day."
    )
    world.say(
        f"{teammate.id} liked how tidy {hero.id} looked in {hero.pronoun('possessive')} uniform."
    )


def wish_to_go(world: World, hero: Entity, route: Route) -> None:
    world.say(
        f"One day, {hero.id} and the team went to {route.label}."
    )
    world.say(route.clue)
    hero.memes["worry"] += 0.5
    world.say(
        f"{hero.id} wanted to hurry ahead, because the {route.keyword} path looked exciting."
    )


def warn(world: World, hero: Entity, supply: Entity, route: Route) -> bool:
    pred = predict_mess(world, hero, route, supply)
    if not pred["dirty"]:
        return False
    world.facts["predicted_dirty"] = True
    world.say(
        f'"Your {supply.label} could get {route.risky_mess}," {hero.pronoun("possessive")} teammate said. '
        f'"Let\'s keep the uniform safe."'
    )
    return True


def team_gathers(world: World, hero: Entity, teammate: Entity) -> None:
    hero.memes["worry"] += 0.5
    teammate.memes["teamwork"] += 1
    world.say(
        f"{hero.id} slowed down, and {teammate.id} walked beside {hero.pronoun('object')} instead of racing ahead."
    )


def offer_fix(world: World, hero: Entity, teammate: Entity, route: Route, supply: Entity) -> Optional[HelperItem]:
    helper = choose_helper(route, supply)
    if helper is None:
        return None
    if helper.id == "tote":
        held = world.add(Entity(
            id="tote_bag",
            kind="thing",
            type="tote",
            label="tote bag",
            phrase="the tote bag",
            owner=hero.id,
            caretaker=teammate.id,
            protective=True,
            covers=set(helper.covers),
        ))
    else:
        held = world.add(Entity(
            id=helper.id,
            kind="thing",
            type=helper.id,
            label=helper.label,
            phrase=helper.phrase,
            owner=hero.id,
            caretaker=teammate.id,
            protective=True,
            covers=set(helper.covers),
        ))
    held.worn_by = None
    held.carried_by = hero.id
    if predict_mess(world, hero, route, supply)["dirty"]:
        del world.entities[held.id]
        return None
    world.say(
        f"{teammate.id} pointed at {held.label} and smiled. "
        f'"Let\'s use {held.phrase} to carry the wet gear and keep your uniform clean."'
    )
    return helper


def accept(world: World, hero: Entity, teammate: Entity, route: Route, supply: Entity, helper: HelperItem) -> None:
    hero.memes["joy"] += 1
    hero.memes["teamwork"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} nodded, and {teammate.id} gave {hero.pronoun('object')} a quick thumbs-up."
    )
    world.say(
        f"Together they packed the needed things in the {helper.label}, and the {route.label} adventure could begin."
    )
    world.say(
        f"By the end, {hero.id}'s uniform stayed neat, and {hero.id} felt proud of helping the team."
    )


def tell(route: Route, supply: Supply, hero_name: str, hero_type: str,
         teammate_name: str, teammate_type: str, team_name: str) -> World:
    world = World(route)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=f"little {hero_type} {hero_name}",
        worn_by=None,
    ))
    teammate = world.add(Entity(
        id=teammate_name,
        kind="character",
        type=teammate_type,
        label=teammate_name,
        phrase=f"friendly teammate {teammate_name}",
    ))
    team = _safe_lookup(TEAMS, team_name)
    uniform = world.add(Entity(
        id="uniform",
        kind="thing",
        type="uniform",
        label="uniform",
        phrase="a crisp adventure uniform",
        owner=hero.id,
        caretaker=teammate.id,
        worn_by=hero.id,
    ))
    if supply.id == "tote":
        tote = world.add(Entity(
            id="tote",
            kind="thing",
            type="tote",
            label="tote",
            phrase="a sturdy tote bag with a wide strap",
            owner=hero.id,
            caretaker=teammate.id,
            carried_by=hero.id,
        ))
    else:
        tote = world.add(Entity(
            id="tote",
            kind="thing",
            type="tote",
            label="tote",
            phrase="a sturdy tote bag with a wide strap",
            owner=hero.id,
            caretaker=teammate.id,
            carried_by=hero.id,
        ))

    world.say(f"{hero.id} and {teammate.id} were part of the {team.name}, and they worked well together.")
    introduce(world, hero, team)
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} uniform for the adventure.")
    setup(world, hero, teammate, tote)

    world.para()
    wish_to_go(world, hero, route)
    warn(world, hero, uniform, route)
    team_gathers(world, hero, teammate)

    world.para()
    helper = offer_fix(world, hero, teammate, route, uniform)
    if helper is not None:
        accept(world, hero, teammate, route, uniform, helper)

    world.facts.update(
        hero=hero,
        teammate=teammate,
        team=team,
        route=route,
        supply=uniform,
        tote=tote,
        helper=helper,
        resolved=helper is not None,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    route = _safe_fact(world, f, "route")
    return [
        f'Write a short Adventure story about {hero.id}, a {hero.type}, the {route.label}, and a helpful tote.',
        f"Tell a teamwork story where {hero.id} keeps a uniform safe while exploring {route.label}.",
        f'Write a child-friendly adventure that includes a tote, a uniform, and friends working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    teammate = _safe_fact(world, f, "teammate")
    route = _safe_fact(world, f, "route")
    uniform = _safe_fact(world, f, "supply")
    helper = _safe_fact(world, f, "helper")
    qa = [
        QAItem(
            question=f"Who went on the adventure at {route.label}?",
            answer=f"{hero.id} went with {teammate.id}, and they were part of the {f['team'].name}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to keep safe during the trip?",
            answer=f"{hero.id} wanted to keep the {uniform.label} clean and neat.",
        ),
        QAItem(
            question=f"Why did the team slow down when they reached {route.label}?",
            answer=f"They slowed down because the path could make the {uniform.label} get {route.risky_mess}.",
        ),
    ]
    if f.get("helper"):
        qa.append(QAItem(
            question=f"How did the {helper.label} help the team?",
            answer=(
                f"The {helper.label} carried the needed gear, so {hero.id} and {teammate.id} could work together "
                f"and keep the {uniform.label} safe."
            ),
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=(
                f"{hero.id} felt proud and happy because the team solved the problem together and the "
                f"{uniform.label} stayed neat."
            ),
        ))
    return qa


KNOWLEDGE = {
    "tote": [
        (
            "What is a tote bag?",
            "A tote bag is a bag with open handles that people use to carry things from place to place.",
        )
    ],
    "uniform": [
        (
            "What is a uniform?",
            "A uniform is a special set of clothes that helps show you belong to a group or team.",
        )
    ],
    "teamwork": [
        (
            "What does teamwork mean?",
            "Teamwork means people work together and help one another to finish a job or solve a problem.",
        )
    ],
    "mud": [
        (
            "What is mud?",
            "Mud is wet dirt that can stick to shoes and clothes.",
        )
    ],
    "dust": [
        (
            "What is dust?",
            "Dust is made of tiny bits of dry dirt that can settle on things and make them look gray.",
        )
    ],
    "paint": [
        (
            "Why can paint be messy?",
            "Paint can drip and smear, so it can easily get on clothes and hands.",
        )
    ],
    "water": [
        (
            "Why do people wear dry clothes on a wet day?",
            "People wear dry clothes so they can stay warm and comfortable when water is splashing around.",
        )
    ],
}

KNOWLEDGE_ORDER = ["teamwork", "tote", "uniform", "mud", "dust", "paint", "water"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = {"teamwork", "tote", "uniform", f["route"].risky_mess}
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"covers={sorted(e.covers)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
route_risky(R, M) :- route(R), risky(R, M).
supply_on_body(S, torso) :- supply(S), uniform(S).
supply_on_body(S, hand) :- supply(S), tote(S).

risk_hits_supply(R, S) :- route_risky(R, M), supply_on_body(S, torso), mess(R, M).
risk_hits_supply(R, S) :- route_risky(R, M), supply_on_body(S, hand), mess(R, M).

helper_fixes(H, R, S) :- helper(H), route_risky(R, M), guards(H, M), supply_on_body(S, Rgn), covers(H, Rgn), risk_hits_supply(R, S).
valid_story(R, S) :- route(R), supply(S), risk_hits_supply(R, S), helper_fixes(_, R, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("risky", rid, route.risky_mess))
        for region in sorted(route.zone):
            lines.append(asp.fact("zone", rid, region))
    for sid, supply in SUPPLIES.items():
        lines.append(asp.fact("supply", sid))
        if supply.id == "uniform":
            lines.append(asp.fact("uniform", sid))
        if supply.id == "tote":
            lines.append(asp.fact("tote", sid))
        lines.append(asp.fact("supply_region", sid, supply.region))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for g in sorted(helper.guards):
            lines.append(asp.fact("guards", hid, g))
        for c in sorted(helper.covers):
            lines.append(asp.fact("covers", hid, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/2."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(route="trail", supply="uniform", hero_name="Mia", hero_type="girl", teammate_name="June", teammate_type="girl", team_name="scouts"),
    StoryParams(route="workshop", supply="uniform", hero_name="Leo", hero_type="boy", teammate_name="Eli", teammate_type="boy", team_name="crew"),
    StoryParams(route="dock", supply="uniform", hero_name="Ava", hero_type="girl", teammate_name="Nina", teammate_type="girl", team_name="explorers"),
    StoryParams(route="yard", supply="tote", hero_name="Max", hero_type="boy", teammate_name="Ruby", teammate_type="girl", team_name="crew"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world about tote, uniform, and teamwork.")
    ap.add_argument("--route", choices=ROUTES.keys())
    ap.add_argument("--supply", choices=SUPPLIES.keys())
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--teammate-name")
    ap.add_argument("--teammate-type", choices=TEAMMATE_TYPES)
    ap.add_argument("--team-name", choices=TEAMS.keys())
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
    route_id = getattr(args, "route", None) or rng.choice(list(ROUTES.keys()))
    supply_id = getattr(args, "supply", None) or "uniform"
    if route_id not in ROUTES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if supply_id not in SUPPLIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        route=route_id,
        supply=supply_id,
        hero_name=getattr(args, "hero_name", None) or rng.choice(HERO_NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(HERO_TYPES),
        teammate_name=getattr(args, "teammate_name", None) or rng.choice(TEAMMATE_NAMES),
        teammate_type=getattr(args, "teammate_type", None) or rng.choice(TEAMMATE_TYPES),
        team_name=getattr(args, "team_name", None) or rng.choice(list(TEAMS.keys())),
    )


def generate(params: StoryParams) -> StorySample:
    route = _safe_lookup(ROUTES, params.route)
    supply = _safe_lookup(SUPPLIES, params.supply)
    world = tell(route, supply, params.hero_name, params.hero_type, params.teammate_name, params.teammate_type, params.team_name)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for route, supply in stories:
            print(f"  {route:10} {supply}")
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
            header = f"### {p.hero_name}: {p.route} with {p.supply}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
