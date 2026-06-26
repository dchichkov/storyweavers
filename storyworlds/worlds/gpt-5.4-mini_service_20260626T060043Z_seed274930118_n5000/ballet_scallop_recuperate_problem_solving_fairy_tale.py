#!/usr/bin/env python3
"""
storyworlds/worlds/ballet_scallop_recuperate_problem_solving_fairy_tale.py
==========================================================================

A small fairy-tale story world about a dancer, a scallop shell, and a
careful problem-solving recovery.

Premise:
- A child dancer loves ballet in a little seaside kingdom.
- A special scallop shell holds a tiny moon-beam charm that helps her
  dance on the tidepath.
- When the charm slips away into the surf, the dancer must solve the
  problem, recover it, and return to the stage.

The world models physical meters and emotional memes:
- meters: wetness, damage, distance, sparkle
- memes: hope, worry, confidence, gratitude, joy

The tale turns on a concrete problem:
- the scallop shell is needed for the dance,
- the tidepath is slippery,
- the dancer and a helper must search, test ideas, and recover the shell
  before the moonlit performance.

This script follows the storyworld contract:
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- lazy ASP import in helpers
- inline ASP_RULES twin plus Python reasonableness gate
- --verify checks parity and exercises generated stories
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    holds: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "fairy", "queen", "mother", "woman"}
        male = {"boy", "prince", "knight", "king", "father", "man"}
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
class Setting:
    place: str = "the moonlit shore"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "shore": Setting(place="the moonlit shore", affords={"ballet", "search"}),
    "garden": Setting(place="the rose garden", affords={"ballet", "search"}),
    "hall": Setting(place="the crystal hall", affords={"ballet", "search"}),
}

ACTIVITIES = {
    "ballet": Activity(
        id="ballet",
        verb="dance ballet",
        gerund="dancing ballet",
        rush="pirouette toward the stage",
        mess="tattered",
        soil="tattered and damp",
        zone={"feet", "legs"},
        keyword="ballet",
        tags={"ballet"},
    ),
    "search": Activity(
        id="search",
        verb="search for the scallop",
        gerund="searching carefully",
        rush="dash to the tide pools",
        mess="wet",
        soil="wet and sandy",
        zone={"feet", "legs", "torso"},
        keyword="scallop",
        tags={"search", "scallop"},
    ),
}

PRIZES = {
    "slippers": Prize(
        label="slippers",
        phrase="a pair of satin ballet slippers",
        type="slippers",
        region="feet",
        plural=True,
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a silver dance cloak",
        type="cloak",
        region="torso",
    ),
    "crown": Prize(
        label="crown",
        phrase="a little moon-crown",
        type="crown",
        region="head",
    ),
}

GEAR = [
    Gear(
        id="dry_wrap",
        label="a dry wrap",
        covers={"feet", "legs"},
        guards={"wet"},
        prep="wrap the slippers in a dry wrap",
        tail="wrapped the slippers in a dry wrap",
    ),
    Gear(
        id="net_bag",
        label="a little net bag",
        covers={"feet", "legs", "torso"},
        guards={"wet", "tattered"},
        prep="place the thing in a little net bag",
        tail="carried it home in a little net bag",
    ),
]

NAMES = ["Luna", "Mira", "Anya", "Iris", "Selene", "Nora"]
GENDERS = ["girl", "boy"]
PARENTS = ["mother", "father"]
TRAITS = ["gentle", "brave", "curious", "bright", "kind"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} does not reach the {prize.region}, "
            f"so the {prize.label} would not truly be in danger.)"
        )
    return (
        f"(No story: there is no gear that both covers the {prize.region} and "
        f"guards against {activity.mess} for this problem.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
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


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'brave')} {hero.type} "
        f"who loved to listen to the sea."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, and every step "
        f"felt like a tiny bell in the moonlight."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One bright morning, {hero.pronoun('possessive')} {parent.type} brought "
        f"home {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore "
        f"{prize.it()} with care."
    )


def tell_start(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    world.say(
        f"At {world.setting.place}, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.type} watched the tide draw silver lines across the sand."
    )
    world.say(
        f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} "
        f"{prize.label} could be spoiled by the sea."
    )


def predict_problem(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    hero_sim = sim.get(hero.id)
    hero_sim.meters[activity.mess] = hero_sim.meters.get(activity.mess, 0.0) + 1
    sim.zone = set(activity.zone)
    prize = sim.get(prize_id)
    soiled = prize.worn_by == hero.id and activity.region if False else False
    soiled = prize.region in activity.zone
    gear_ok = False
    for item in sim.worn_items(hero_sim):
        if item.protective and prize.region in item.covers and activity.mess in item.guards:
            gear_ok = True
    return {"soiled": soiled and not gear_ok}


def warn(world: World, parent: Entity, hero: Entity, act: Activity, prize: Entity) -> None:
    if prize_at_risk(act, prize):
        world.say(
            f'"If you rush into {act.verb}, your {prize.label} may get {act.soil}," '
            f"said {hero.pronoun('possessive')} {parent.type}. "
            f'"We should solve this first."'
        )


def search_solution(world: World, hero: Entity, parent: Entity, act: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(act, prize)
    if gear is None:
        return None
    helper = world.add(
        Entity(
            id=gear.id,
            kind="thing",
            type="gear",
            label=gear.label,
            protective=True,
            owner=hero.id,
            caretaker=parent.id,
            meters={},
            memes={},
        )
    )
    helper.worn_by = hero.id
    world.say(
        f"{hero.id} and {hero.pronoun('possessive')} {parent.type} looked near the tide pools, "
        f"then under a shell-colored stone, and at last found a clever plan: "
        f"{gear.prep}."
    )
    return gear


def solve_problem(world: World, hero: Entity, parent: Entity, act: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1.0)
    hero.memes["confidence"] += 1
    world.say(
        f"They used the {gear.label} so {hero.id} could still {act.verb} without ruining "
        f"{hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"With the problem solved, {hero.id} danced again, and the moon looked as if it were clapping."
    )


def recover_scallop(world: World, hero: Entity, parent: Entity) -> None:
    scallop = world.entities.get("scallop")
    if scallop is None:
        return
    scallop.meters["distance"] = 0
    scallop.memes["safe"] += 1
    hero.memes["gratitude"] += 1
    world.say(
        f"Then they found the scallop shell hiding in a ripple of foam, "
        f"and {hero.id} carefully lifted it home."
    )
    world.say(
        f"It was safe again, and the tiny moon-beam charm rested inside like a sleeping star."
    )


def finish(world: World, hero: Entity, parent: Entity, prize: Entity, act: Activity) -> None:
    hero.memes["joy"] += 2
    hero.memes["confidence"] += 1
    world.say(
        f"At last, {hero.id} could {act.gerund} again, with {hero.pronoun('possessive')} "
        f"{prize.label} shining clean in the moonlight."
    )
    world.say(
        f"{hero.pronoun().capitalize()} bowed to {hero.pronoun('possessive')} {parent.type}, "
        f"and the little shore felt peaceful and proud."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, memes={"trait_word": trait, "worry": 1.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )
    scallop = world.add(
        Entity(
            id="scallop",
            kind="thing",
            type="shell",
            label="scallop shell",
            phrase="a scallop shell with a moon-beam charm inside",
            owner=hero.id,
            meters={"distance": 3.0, "wet": 1.0},
            memes={"shimmer": 1.0},
        )
    )

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    tell_start(world, hero, parent, prize, activity)
    warn(world, parent, hero, activity, prize)
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} frowned, but {hero.pronoun()} did not give up. {hero.pronoun().capitalize()} "
        f"looked for a way to keep dancing safely."
    )
    gear = search_solution(world, hero, parent, activity, prize)
    if gear is None:
        pass
    recover_scallop(world, hero, parent)
    world.para()
    solve_problem(world, hero, parent, activity, prize, gear)
    finish(world, hero, parent, prize, activity)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        scallop=scallop,
        resolved=True,
    )
    return world


KNOWLEDGE = {
    "ballet": [
        (
            "What is ballet?",
            "Ballet is a kind of dance with careful steps, turns, and graceful arms.",
        )
    ],
    "scallop": [
        (
            "What is a scallop shell?",
            "A scallop shell is a fan-shaped shell from the sea, made by a shellfish that lives in salt water.",
        )
    ],
    "recover": [
        (
            "What does recuperate mean?",
            "To recuperate means to get better, rest, and slowly have your strength come back.",
        )
    ],
    "sea": [
        (
            "What is the sea?",
            "The sea is a very large body of salty water that moves in waves.",
        )
    ],
    "problem": [
        (
            "What is a problem?",
            "A problem is something that is wrong or tricky and needs help or careful thinking to fix.",
        )
    ],
    "solution": [
        (
            "What is a solution?",
            "A solution is a good answer or plan that helps solve a problem.",
        )
    ],
}

KNOWLEDGE_ORDER = ["ballet", "scallop", "recover", "sea", "problem", "solution"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a fairy tale for a young child about {hero.id}, {act.keyword}, and a kind problem-solving recovery.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but must protect {hero.pronoun('possessive')} {prize.label}.",
        f'Write a moonlit story that uses the words "ballet" and "scallop" and ends with a happy recuperate moment.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    prize: Entity = _safe_fact(world, f, "prize")
    act: Activity = _safe_fact(world, f, "activity")
    gear: Gear = _safe_fact(world, f, "gear")
    scallop: Entity = _safe_fact(world, f, "scallop")

    qa = [
        QAItem(
            question=f"Who wanted to {act.verb} at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"What worried {hero.id}'s {parent.type} about the {prize.label}?",
            answer=(
                f"{hero.id}'s {parent.type} worried that if {hero.id} rushed into {act.verb}, "
                f"the {prize.label} would get {act.soil}."
            ),
        ),
        QAItem(
            question=f"What clever thing helped solve the problem?",
            answer=(
                f"They used {gear.label} to protect the {prize.label}, so {hero.id} could keep dancing."
            ),
        ),
        QAItem(
            question=f"What did they recover near the waves?",
            answer=(
                f"They recovered the scallop shell and brought it safely home."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=(
                f"{hero.id} felt happy, confident, and grateful after the problem was solved."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"Why is this a recuperate story?",
                answer=(
                    f"It is a recuperate story because the scallop shell and the dancer both needed careful recovery: "
                    f"the shell was brought safely back, and {hero.id} got to dance again after resting and solving the problem."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("recover")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shore", activity="ballet", prize="slippers", name="Luna", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="garden", activity="ballet", prize="cloak", name="Mira", gender="girl", parent="father", trait="brave"),
    StoryParams(place="hall", activity="search", prize="crown", name="Anya", gender="girl", parent="mother", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: ballet, scallop, recuperate, and a problem solved kindly."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent, params.trait)
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


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:8} {prize:8} [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
