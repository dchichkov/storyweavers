#!/usr/bin/env python3
"""
storyworlds/worlds/universe_velcro_yoke_teamwork_kindness_flashback_space.py
=============================================================================

A small space-adventure story world about a crew, a drifting tool, and a
careful fix. The world is centered on teamwork, kindness, and a brief flashback
that explains why the hero trusts the gear.

Premise:
- A young spacer wants to guide a little shuttle through a bright corner of the
  universe.
- The control yoke is loose, and a velcro strap is needed to keep it steady.
- The crew must work together kindly, because the fix only works if everyone
  helps and nobody rushes.

World model:
- Entities have physical meters and emotional memes.
- The story is driven by state changes: drift, grip, memory, relief, and trust.
- A flashback is used to explain why the velcro matters and why the hero can
  believe in the team.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager results import
- lazy asp import inside ASP helpers only
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    paired_with: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    location: str = ""
    gear_ent: object | None = None
    hero: object | None = None
    leader: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    place: str
    style: str
    afford: set[str] = field(default_factory=set)
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
class Mission:
    id: str
    verb: str
    gerund: str
    danger: str
    reveal: str
    kind: str
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
    location: str
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
class Gear:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    protects: set[str]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("drift", 0.0) < THRESHOLD:
            continue
        sig = ("drift", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"The cabin trembled, and {actor.id} felt the ship slide off center.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("teamwork_call", 0.0) < THRESHOLD:
            continue
        sig = ("teamwork", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trust"] = actor.memes.get("trust", 0.0) + 1
        out.append(f"The crew leaned in together, each one taking a careful job.")
    return out


CAUSAL_RULES = [_r_drift, _r_teamwork]


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            sents = rule(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)
            if len(world.fired) != before:
                changed = True


def predict_fix(world: World, hero: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    perform_mission(sim, hero.id, mission, prize_id, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "safe": prize.meters.get("loose", 0.0) < THRESHOLD,
        "calm": sim.get(hero.id).memes.get("calm", 0.0),
    }


def perform_mission(world: World, hero_id: str, mission: Mission, prize_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    prize = world.get(prize_id)
    gear = next((e for e in world.entities.values() if e.protective and e.worn_by == hero.id), None)
    if gear and prize.location in gear.protects:
        prize.meters["loose"] = 0.0
    else:
        prize.meters["loose"] = prize.meters.get("loose", 0.0) + 1
    hero.meters["focus"] = hero.meters.get("focus", 0.0) + 1
    hero.meters["mission"] = hero.meters.get("mission", 0.0) + 1
    hero.memes["teamwork_call"] = hero.memes.get("teamwork_call", 0.0) + 1
    propagate(world)
    if narrate:
        world.say(f"{hero.id} reached for the yoke and guided the little craft through the bright spill of the universe.")


def introduction(world: World, hero: Entity, mission: Mission, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a young spacer who loved to {mission.verb} above the glowing universe."
    )
    world.say(
        f"{hero.pronoun().capitalize()} kept {hero.pronoun('possessive')} {prize.label} close, because the {mission.kind} would shake if it went loose."
    )


def flashback(world: World, hero: Entity, gear: Gear) -> None:
    hero.memes["memory"] = hero.memes.get("memory", 0.0) + 1
    world.say(
        f"{hero.id} remembered a previous flight, when a small hook had slipped and the yoke had wobbled under {hero.pronoun('possessive')} hands."
    )
    world.say(
        f"That was when the kind mechanic showed {hero.pronoun('object')} the {gear.label}, saying it could hold tight without hurting anything."
    )


def warning(world: World, leader: Entity, hero: Entity, prize: Entity, mission: Mission) -> None:
    pred = predict_fix(world, hero, mission, prize.id)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f'"If the {mission.kind} slips, your {prize.label} will jolt loose," {leader.id} said gently.'
    )
    if not pred["safe"]:
        world.say(f'"We need a better grip than hope," {leader.id} added, but {hero.id} nodded instead of rushing.')
    else:
        world.say(f'"We can keep it safe," {leader.id} said, and the whole crew listened.')


def kindness_and_fix(world: World, leader: Entity, hero: Entity, gear: Gear, prize: Entity, mission: Mission) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["teamwork_call"] = hero.memes.get("teamwork_call", 0.0) + 1
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        phrase=gear.phrase,
        owner=hero.id,
        protective=True,
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id
    world.say(
        f"{leader.id} smiled and helped {hero.id} wrap the {gear.label} around the yoke."
    )
    world.say(
        f'"Let us do it together," {leader.id} said kindly, and {hero.id} felt brave enough to try again.'
    )
    world.say(
        f"The {gear.label} held the {prize.label} steady, and the yoke stopped slipping."
    )


def resolution(world: World, hero: Entity, prize: Entity, mission: Mission) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    prize.meters["loose"] = 0.0
    world.say(
        f"Together, the crew finished the {mission.gerund}, and the little craft drifted safely through the starry dark."
    )
    world.say(
        f"At the end, {hero.id} was laughing softly with {prize.label} snug on the yoke, while the universe shimmered outside the window."
    )


def tell(setting: Setting, mission: Mission, prize_cfg: Prize, hero_name: str, hero_type: str, leader_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    leader = world.add(Entity(id="Captain", kind="character", type=leader_type, label="captain"))
    prize = world.add(Entity(
        id="yoke",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        location=prize_cfg.location,
        plural=prize_cfg.plural,
    ))
    gear = GEAR["velcro_band"]

    introduction(world, hero, mission, prize)
    world.para()
    warning(world, leader, hero, prize, mission)
    flashback(world, hero, gear)
    kindness_and_fix(world, leader, hero, gear, prize, mission)
    world.para()
    perform_mission(world, hero.id, mission, prize.id)
    resolution(world, hero, prize, mission)

    world.facts.update(hero=hero, leader=leader, prize=prize, mission=mission, gear=gear)
    return world


SETTINGS = {
    "orbital_hub": Setting(place="the orbital hub", style="space adventure", afford={"guide"}),
    "starbridge": Setting(place="the starbridge", style="space adventure", afford={"guide"}),
    "moon_garden": Setting(place="the moon garden", style="space adventure", afford={"guide"}),
}

MISSIONS = {
    "guide": Mission(
        id="guide",
        verb="guide the shuttle",
        gerund="guiding the shuttle",
        danger="the yoke could slip",
        reveal="the velcro would hold the grip steady",
        kind="yoke",
        keyword="universe",
        tags={"universe", "yoke"},
    )
}

PRIZES = {
    "yoke": Prize(
        label="yoke",
        phrase="a small control yoke",
        type="yoke",
        location="hands",
        plural=False,
    )
}

GEAR = {
    "velcro_band": Gear(
        id="velcro_band",
        label="velcro strap",
        phrase="a soft velcro strap",
        prep="wrap the velcro strap around the yoke",
        tail="fastened the strap with a neat rip",
        protects={"hands"},
        plural=False,
    )
}

HERO_NAMES = ["Nova", "Milo", "Iris", "Kade", "Luna", "Orin"]
HERO_TYPES = ["girl", "boy"]
LEADER_TYPES = ["captain", "pilot"]
TRAITS = ["brave", "careful", "curious", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mission in MISSIONS:
            for prize in PRIZES:
                combos.append((place, mission, prize))
    return combos


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    name: str
    hero_type: str
    leader_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mission = _safe_fact(world, f, "mission")
    return [
        f"Write a gentle space-adventure story about {hero.id} in the universe, where teamwork and kindness help fix a wobbly yoke.",
        f"Tell a short story in which a velcro strap saves the day when a small {mission.kind} slips during a shuttle flight.",
        f"Write a kid-friendly story that includes a flashback, a velcro strap, and a happy teamwork ending in space.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    leader = _safe_fact(world, f, "leader")
    prize = _safe_fact(world, f, "prize")
    mission = _safe_fact(world, f, "mission")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a young spacer who needed to guide the shuttle safely through the universe.",
        ),
        QAItem(
            question=f"Why did the captain worry about the {prize.label}?",
            answer=f"The captain worried because if the {mission.kind} slipped, the {prize.label} could jolt loose during the flight.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback helped {hero.id} remember that a kind mechanic had once shown how the {gear.label} could hold the yoke steady.",
        ),
        QAItem(
            question=f"How did teamwork help in the end?",
            answer=f"Teamwork helped because the captain and {hero.id} wrapped the {gear.label} around the yoke together, and that kept everything steady.",
        ),
        QAItem(
            question=f"How did kindness show up in the story?",
            answer=f"Kindness showed up when the captain spoke gently, helped with the fix, and encouraged {hero.id} to try again without fear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the universe?",
            answer="The universe is everything in space: stars, planets, moons, and all the dark room between them.",
        ),
        QAItem(
            question="What is velcro for?",
            answer="Velcro is a fastener that sticks closed with tiny hooked threads, so it can hold things together and still be easy to open.",
        ),
        QAItem(
            question="What is a yoke?",
            answer="A yoke is a control bar or handle that helps someone steer a craft or machine.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and share the job so they can do something better together.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring with someone else.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short memory scene that shows something that happened before the main story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orbital_hub", mission="guide", prize="yoke", name="Nova", hero_type="girl", leader_type="captain", trait="careful"),
    StoryParams(place="starbridge", mission="guide", prize="yoke", name="Milo", hero_type="boy", leader_type="pilot", trait="brave"),
    StoryParams(place="moon_garden", mission="guide", prize="yoke", name="Iris", hero_type="girl", leader_type="captain", trait="gentle"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("style", sid, s.style))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("keyword", mid, m.keyword))
        lines.append(asp.fact("kind", mid, m.kind))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("location", pid, p.location))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for r in sorted(g.protects):
            lines.append(asp.fact("protects_region", gid, r))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, M, P) :- setting(S), mission(M), prize(P), affords(S, M), location(P, hands), kind(M, yoke), gear(G), protects_region(G, hands).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(a - b))
    print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about universe, velcro, yoke, teamwork, kindness, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--leader-type", choices=LEADER_TYPES)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission, prize = rng.choice(list(combos))
    return StoryParams(
        place=place,
        mission=mission,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        hero_type=getattr(args, "hero_type", None) or rng.choice(HERO_TYPES),
        leader_type=getattr(args, "leader_type", None) or rng.choice(LEADER_TYPES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    world.facts["params"] = params
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    leader = world.add(Entity(id="Captain", kind="character", type=params.leader_type, label="captain"))
    prize = world.add(Entity(id="yoke", type="yoke", label="yoke", phrase="a small control yoke", owner=hero.id, location="hands"))
    mission = _safe_lookup(MISSIONS, params.mission)
    gear = GEAR["velcro_band"]

    tell(world, mission, Prize(prize.label, prize.phrase, prize.type, prize.location, prize.plural), hero.id, hero.type, leader.type)

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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print("  ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
