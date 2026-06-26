#!/usr/bin/env python3
"""
storyworlds/worlds/sorrow_slant_happy_ending_space_adventure.py
===============================================================

A small, self-contained story world for a Space Adventure style tale with
sorrow, slant, and a happy ending.

The seed image:
- A child astronaut is excited to help on a tiny space mission.
- A slanted ramp or slanted dock makes a helpful object slide away.
- The child feels sorrow when the mission seems to go wrong.
- A careful helper uses the right gear and a patient method.
- The story ends with a bright, happy image of the repaired mission.

This world keeps the action concrete and state-driven:
- physical meters: glide, drift, tilt, scuff, charge, crack, repair, secure
- emotional memes: joy, worry, sorrow, pride, calm, relief, love, wonder

The prose is authored from the simulated world, not a frozen template.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tilt": 0.0, "glide": 0.0, "drift": 0.0, "scuff": 0.0, "charge": 0.0, "repair": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "sorrow": 0.0, "pride": 0.0, "calm": 0.0, "relief": 0.0, "love": 0.0, "wonder": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pilot"}
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
    place: str = "the spaceport"
    indoors: bool = True
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
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    result: str
    slant: str
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


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.mission: Optional[Mission] = None
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

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.mission = self.mission
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


SETTINGS = {
    "spaceport": Setting(place="the spaceport", indoors=True, affords={"dock"}),
    "hangar": Setting(place="the hangar", indoors=True, affords={"dock", "repair"}),
    "moonbase": Setting(place="the moonbase", indoors=True, affords={"dock", "repair"}),
}

MISSIONS = {
    "dock": Mission(
        id="dock",
        verb="dock the little shuttle",
        gerund="docking the little shuttle",
        rush="rush down the ramp",
        risk="the shuttle could slide off the slant",
        result="the shuttle would settle safely",
        slant="slanted",
        zone={"floor"},
        keyword="slant",
        tags={"space", "slant"},
    ),
    "repair": Mission(
        id="repair",
        verb="repair the signal lamp",
        gerund="repairing the signal lamp",
        rush="reach for the loose panel",
        risk="the panel could crack and spill tiny parts",
        result="the lamp would shine again",
        slant="crooked",
        zone={"table"},
        keyword="sorrow",
        tags={"space", "repair"},
    ),
}

GEAR = [
    Gear(
        id="magboots",
        label="magnetic boots",
        covers={"floor"},
        guards={"glide"},
        prep="put on magnetic boots first",
        tail="tied on the magnetic boots",
    ),
    Gear(
        id="strap",
        label="a safety strap",
        covers={"floor", "table"},
        guards={"glide", "drift"},
        prep="clip on a safety strap first",
        tail="clicked the safety strap shut",
    ),
    Gear(
        id="gloves",
        label="soft repair gloves",
        covers={"table"},
        guards={"scuff"},
        prep="wear soft repair gloves first",
        tail="pulled on the soft repair gloves",
    ),
]

PRIZES = {
    "lantern": Prize(id="lantern", label="signal lamp", phrase="a bright signal lamp", region="table"),
    "shuttle": Prize(id="shuttle", label="shuttle", phrase="a tiny shuttle", region="floor"),
}

NAMES = ["Ari", "Mina", "Leo", "Noa", "Iris", "Kai"]
TRAITS = ["brave", "gentle", "curious", "cheerful", "careful"]


def _worn(actor: Entity, item: Entity) -> bool:
    return item.worn_by == actor.id


def prize_at_risk(mission: Mission, prize: Prize) -> bool:
    return prize.region in mission.zone


def select_gear(mission: Mission, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers:
            if mission.id == "dock" and "glide" in gear.guards:
                return gear
            if mission.id == "repair" and ("scuff" in gear.guards or "drift" in gear.guards):
                return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            mission = _safe_lookup(MISSIONS, mid)
            for pid, prize in PRIZES.items():
                if prize_at_risk(mission, prize) and select_gear(mission, prize):
                    out.append((place, mid, pid))
    return out


def _r_misstep(world: World) -> list[str]:
    out = []
    mission = world.mission
    if mission is None:
        return out
    for actor in world.characters():
        if actor.meters["glide"] < THRESHOLD and actor.meters["scuff"] < THRESHOLD:
            continue
        if actor.meters["glide"] >= THRESHOLD:
            actor.memes["worry"] += 1
        if actor.meters["scuff"] >= THRESHOLD:
            actor.memes["worry"] += 1
        if actor.memes["sorrow"] >= THRESHOLD and ("sorrow", actor.id) not in world.fired:
            world.fired.add(("sorrow", actor.id))
            out.append(f"{actor.id} felt sorrow when the plan started to wobble.")
    return out


def _r_repair(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters["repair"] < THRESHOLD:
            continue
        if item.id in world.fired:
            continue
        world.fired.add((item.id, "repair"))
        item.meters["charge"] += 1
        out.append(f"The little machine began to glow again.")
    return out


ASP_RULES = r"""
prize_at_risk(M, P) :- mission(M), zone(M, R), prize(P), region(P, R).
compatible(G, M, P) :- gear(G), prize_at_risk(M, P), cover(G, R), region(P, R), guard(G, X), needs(M, X).
valid(Place, M, P) :- affords(Place, M), prize_at_risk(M, P), compatible(_, M, P).
"""


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    for rule in (_r_misstep, _r_repair):
        produced.extend(rule(world))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, mission: Mission, prize_id: str) -> dict:
    sim = world.copy()
    _do_mission(sim, sim.get(actor.id), mission, narrate=False)
    prize = sim.get(prize_id)
    return {"risk": prize.meters["scuff"] >= THRESHOLD, "sorrow": sim.get(actor.id).memes["sorrow"]}


def _do_mission(world: World, actor: Entity, mission: Mission, narrate: bool = True) -> None:
    world.mission = mission
    if mission.id == "dock":
        actor.meters["glide"] += 1
    else:
        actor.meters["scuff"] += 1
    actor.memes["sorrow"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} astronaut who loved looking at the stars.")


def mission_love(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["wonder"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {mission.gerund}, because space felt big and kind.")


def setup_prize(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} kept {hero.pronoun('possessive')} {prize.label} ready for the mission.")


def arrive(world: World, hero: Entity, helper: Entity) -> None:
    world.say(f"One day, {hero.id} and {helper.pronoun('possessive')} helper went to {world.setting.place}.")


def worry(world: World, hero: Entity, mission: Mission, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} wanted to {mission.verb}, but {mission.risk}.")


def sorrow_beat(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["sorrow"] += 1
    world.say(f"{hero.id} felt sorrow and looked down at the {prize.label}.")


def offer_fix(world: World, helper: Entity, hero: Entity, mission: Mission, prize: Entity) -> Optional[Gear]:
    gear = select_gear(mission, prize)
    if gear is None:
        return None
    item = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), owner=hero.id, caretaker=helper.id))
    item.worn_by = hero.id
    pred = predict(world, hero, mission, prize.id)
    if pred["risk"]:
        item.worn_by = None
        del world.entities[item.id]
        return None
    world.say(f"{helper.id} smiled and said, \"Let's {gear.prep} so we can still play safely.\"")
    return gear


def accept(world: World, hero: Entity, helper: Entity, mission: Mission, prize: Entity, gear: Gear) -> None:
    hero.memes["sorrow"] = 0.0
    hero.memes["joy"] += 2
    hero.memes["relief"] += 1
    world.say(f"{hero.id} nodded, and {hero.pronoun()} and {helper.pronoun('subject')} {gear.tail}.")
    if mission.id == "dock":
        world.say(f"Then the shuttle rolled along the slant and settled neatly in place.")
    else:
        world.say(f"Then the lamp was fixed, and its little beam shone warm and bright again.")
    world.say(f"At the end, {hero.id} was smiling, and the spaceport looked safe and sparkling.")


def tell(setting: Setting, mission: Mission, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str = "captain") -> World:
    world = World(setting)
    world.mission = mission
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=parent_type))
    prize = world.add(Entity(id=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, region=prize_cfg.region))
    intro(world, hero)
    mission_love(world, hero, mission)
    setup_prize(world, hero, prize)
    world.para()
    arrive(world, hero, helper)
    worry(world, hero, mission, prize)
    sorrow_beat(world, hero, prize)
    gear = offer_fix(world, helper, hero, mission, prize)
    if gear:
        accept(world, hero, helper, mission, prize, gear)
    world.facts.update(hero=hero, helper=helper, prize=prize, mission=mission, setting=setting, gear=gear, resolved=gear is not None)
    return world


@dataclass
class StoryParams:
    place: str
    mission: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mission, prize = f["hero"], f["mission"], f["prize"]
    return [
        f'Write a short Space Adventure story for a young child about {hero.id} and a {mission.keyword} problem.',
        f'Tell a gentle story where {hero.id} wants to {mission.verb} but {mission.risk}, and a helper finds a safe fix.',
        f'Write a happy-ending space story that includes the word "{mission.keyword}" and ends with a bright scene.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, mission = f["hero"], f["helper"], f["prize"], f["mission"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {mission.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel sorrow?",
            answer=f"{hero.id} felt sorrow because {mission.risk}.",
        ),
        QAItem(
            question=f"How did the helper solve the problem?",
            answer=f"{helper.id} used {f['gear'].label} so {hero.id} could keep going safely.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What happened at the happy ending?",
            answer=f"{hero.id} and {helper.id} finished the mission, and {prize.label} was safe and the space scene ended bright and calm.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    mission = _safe_fact(world, world.facts, "mission")
    if mission.id == "dock":
        return [QAItem(question="What does it mean to dock a shuttle?", answer="Docking means bringing a spaceship or shuttle safely into place so it can stop and stay put.")]
    return [QAItem(question="What is a signal lamp for?", answer="A signal lamp makes a bright light so others can see you and know where you are.")]


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
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="spaceport", mission="dock", prize="shuttle", name="Ari", gender="girl", parent="captain", trait="brave"),
    StoryParams(place="moonbase", mission="repair", prize="lantern", name="Kai", gender="boy", parent="captain", trait="gentle"),
]


def explain_rejection(mission: Mission, prize: Prize) -> str:
    return f"(No story: {mission.verb} does not reasonably threaten the {prize.label} in this world.)"


def valid_gender(prize_id: str, gender: str) -> bool:
    return gender in _safe_lookup(PRIZES, prize_id).genders


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world with sorrow, slant, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    combos = []
    for place, mission_id, prize_id in valid_combos():
        if getattr(args, "place", None) is not None and place != getattr(args, "place", None):
            continue
        if getattr(args, "mission", None) is not None and mission_id != getattr(args, "mission", None):
            continue
        if getattr(args, "prize", None) is not None and prize_id != getattr(args, "prize", None):
            continue
        if getattr(args, "gender", None) is not None and not valid_gender(prize_id, getattr(args, "gender", None)):
            continue
        combos.append((place, mission_id, prize_id))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, prize=prize, name=name, gender=gender, parent=getattr(args, "parent", None) or "captain", trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MISSIONS, params.mission), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.indoors:
            lines.append(asp.fact("indoors", pid))
        for mid in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, mid))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("needs", mid, "glide" if mid == "dock" else "drift"))
        for r in sorted(mission.zone):
            lines.append(asp.fact("zone", mid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, prize.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("cover", gear.id, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guard", gear.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
