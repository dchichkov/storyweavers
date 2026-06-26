#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0


def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    glows: object | None = None
    captain: object | None = None
    ship: object | None = None
    squint: object | None = None
    storm: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "boy", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male or "pirate" in self.type:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "mentor": "captain"}.get(self.type, self.type)
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
    place: str = "open sea"
    indoor: bool = False
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
    mess: str
    zone: set[str]
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
class ShipType:
    id: str
    label: str
    sea_worthiness: float
    risk_factor: float
    desc: str
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
class StormLevel:
    id: str
    label: str
    intensity: float
    noise: str
    splash_factor: float
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
class Treasure:
    id: str
    label: str
    phrase: str
    region: str
    glows: bool = False
    description: str = ""
    tre_id: object | None = None
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
        self.zone: set[str] = set()
        self.weather: str = "stormy"
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for ship in list(world.entities.values()):
        if ship.type != "ship":
            continue
        integrity = ship.meters.get("integrity", 1.0)
        hazard = world.facts.get("storm_intensity", 1.0)
        reckless = world.facts.get("recklessness", 0.0)
        if hazard == 0 or reckless == 0:
            continue
        damage = min(0.5, hazard * reckless * 0.1)
        if ship.meters["integrity"] - damage >= 0:
            ship.meters["integrity"] -= damage
            sig = ("damage", ship.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append(
                    f"The {ship.label} groaned under the strain and was now taking on water!"
                )
    return out

def _r_lesson(world: World) -> list[str]:
    for actor in world.characters():
        if actor.type != "pirate" or "Squint" not in actor.id:
            continue
        if actor.memes.get("lesson_learned", 0.0) >= THRESHOLD:
            sig = ("lesson", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                world.facts["transformation"] = True
                actor.memes["recklessness"] = max(0.0, actor.memes["recklessness"] - 1.2)
                actor.memes["responsibility"] = min(1.0, actor.memes["responsibility"] + 0.8)
                return [
                    "Squint’s eyes widened and his shoulders dropped. "
                    "'Aye captain,' he mumbled, 'I see now.'"
                ]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="lesson", tag="social", apply=_r_lesson),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def set_sail(world: World, actor: Entity) -> None:
    actor.memes["recklessness"] = min(1.0, actor.memes["recklessness"] + 0.6)
    actor.memes["determination"] = min(1.0, actor.memes["determination"] + 0.4)
    world.say(
        f"{actor.id.capitalize()} hoisted the colors and called for fair winds. "
        "The deed was begun."
    )

def storm_approach(world: World, actor: Entity, storm: Entity) -> None:
    world.facts["storm_intensity"] = storm.meters.get("intensity", 0.0)
    world.facts["recklessness"] = actor.memes.get("recklessness", 0.0)
    where = world.setting.place.replace("open ", "")
    world.say(
        f"{actor.pronoun().capitalize()} looked toward the horizon where a "
        f"{storm.label} swirled dark and {storm.phrase}. "
        "The {where} would soon be swallowed by foam!"
    )

def warn_captain(world: World, captain: Entity, squint: Entity, ship: Entity) -> None:
    risk = max(0.0, 1.0 - ship.meters.get("sea_worthiness", 0.5))
    ship_risk = risk * (world.facts.get("storm_intensity", 0.0) + 0.3)
    world.facts["predicted_damage"] = min(1.0, ship_risk)
    world.say(
        f'"{captain.id} yelled over the wind, "That {ship.label} canna take more! '
        f'Safer harbour first, then treasure!"'
    )

def defy_captain(world: World, squint: Entity, ship: Entity, captain: Entity) -> None:
    squint.memes["recklessness"] += 0.8
    world.say(
        f'{squint.id} just grinned, teeth flashing. "Short cut it is, then!" '
        f'He leapt to the tiller full bore. The {ship.label} lurched wildly.'
    )

def storm_hit(world: World, ship: Entity, squint: Entity, storm: Entity) -> None:
    world.facts["storm_intensity"] = storm.meters.get("intensity", 0.0)
    world.facts["recklessness"] = squint.memes.get("recklessness", 0.0)
    damage = min(0.6, world.facts["storm_intensity"] * world.facts["recklessness"])
    ship.meters["integrity"] -= damage
    world.say(
        f"The {storm.label} struck with a spectacular crack! "
        f"The {ship.label} screamed as planks pried apart."
    )
    world.say(
        "Seawater rushed in — belly deep. Sperrit! They were going down!"
    )

def realize_lesson(world: World, squint: Entity, storm: Entity) -> None:
    squint.memes["lesson_learned"] += 1.0
    danger = storm.meters.get("intensity", 0.0)
    squint.memes["worry"] = min(1.0, danger * 0.7 + 0.2)
    world.say(
        f"{squint.id.strip()} face went pale. Had his folly cost them all dearly?"
    )

def compromise_secure(world: World, squint: Entity, captain: Entity, ship: Entity) -> None:
    squint.memes["responsibility"] = min(1.0, squint.memes["responsibility"] + 0.5)
    ship.meters["integrity"] = min(0.9, ship.meters.get("integrity", 0.5) + 0.3)
    world.say(
        f"Clutching the helm steady, {squint.id} cried, 'We punch through! "
        "For every hand — bales and prayers!'"
    )
    world.say(
        f"{captain.id} roared orders while {squint.id} lashed down the foresail "
        f"before the wind could rip it free."
    )

def reach_treasure(world: World, squint: Entity, treasure: Entity, ship: Entity) -> None:
    treasure_worth = 1.0 if treasure.glows else 0.5
    squint.memes["pride"] = min(1.0, squint.memes["pride"] + treasure_worth * 0.6)
    world.facts["treasure_secured"] = True
    world.say(
        f"The {treasure.label} glistened under the lightning-strike sky — "
        f"glorious, {treasure.phrase}."
    )
    world.say(
        f"{squint.id} dropped to his knees sobbing with joy. "
        "'We made it... and I changed!'"
    )

def tell(setting: Setting, ship_type: ShipType, storm_level: StormLevel,
         treasure_cfg: Treasure, squint_name: str = "Squint") -> World:
    world = World(setting)
    world.weather = "stormy"

    captain = world.add(Entity(
        id="Captain Ironhook",
        kind="character",
        type="mentor",
        label="the grizzled first mate",
        phrase="Captain Ironhook’s boots left deep prints in the wet deck",
        traits=["wise"],
    ))
    squint = world.add(Entity(
        id=squint_name,
        kind="character",
        type="boy",
        label="a reckless deckhand",
        phrase="a lanky boy with a mop of copper curls",
        traits=["lively", "curious"],
        owner="crew",
        caretaker="captain",
    ))
    ship = world.add(Entity(
        id="ship",
        kind="thing",
        type="ship",
        label=ship_type.label,
        phrase=ship_type.desc,
        meters={"integrity": ship_type.sea_worthiness, "safety": 0.8},
        traits=[ship_type.id],
    ))
    storm = world.add(Entity(
        id="storm",
        kind="thing",
        type="storm",
        label=storm_level.label,
        phrase=storm_level.noise,
        meters={"intensity": storm_level.intensity, "noise": 0.9},
        traits=[storm_level.id],
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure_cfg.type,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        glows=treasure_cfg.glows,
        region="hold",
        plural=treasure_cfg.id == "gold_coins",
    ))

    world.facts.update(treasure_cfg=treasure_cfg, storm_level=storm_level.id,
                       ship_type=ship_type.id, captain=captain, squint=squint)

    world.say(
        f"In the pirate cove of Tortuga’s Pocket, atop a squat hull "
        f"called the {ship.label}, young {squint.id} rubbed his hands, "
        "eyes wide with dreams of glory."
    )
    introduce_crew(world, captain, squint)
    world.para()

    world.say(
        "Legend spoke of a hidden cove east of Devil’s Teeth Island — "
        "where a treasure gleamed spectacular amidst tides that sang "
        "deep songs of gold."
    )
    set_sail(world, squint)
    storm_approach(world, squint, storm)
    world.para()

    warn_captain(world, captain, squint, ship)
    defy_captain(world, squint, ship, captain)
    storm_hit(world, ship, squint, storm)
    world.para()

    realize_lesson(world, squint, storm)
    compromise_secure(world, squint, captain, ship)
    world.para()

    reach_treasure(world, squint, treasure, ship)

    world.facts.update(
        transformation=squint.memes["responsibility"] >= THRESHOLD,
        lesson_learned=squint.memes["lesson_learned"] >= THRESHOLD,
        treasure_secured=True,
        integrity_left=max(0.0, ship.meters["integrity"])
    )
    return world

def introduce_crew(world: World, captain: Entity, squint: Entity) -> None:
    world.say(
        f"The {captain.label} stood like a carved oak beside "
        f"{squint.id}, whose small frame trembled with unsated hunger for chance."
    )
    world.say(
        "The boy loved storms and the glisten of gold — "
        "two things most pirates feared."
    )

SETTINGS = {
    "open_waters": Setting(place="open sea", indoor=False, affords={"sail"}),
    "devils_teeth": Setting(place="Devil’s Teeth shoals", indoor=False, affords={"treasure"}),
}

SHIP_TYPES = {
    "squat": ShipType(
        id="squat",
        label="Squat Hull",
        sea_worthiness=0.35,
        risk_factor=1.2,
        desc="a tiny, low-hulled coasting boat with sails patched in bright calico",
    ),
    "sturdy": ShipType(
        id="sturdy",
        label="Iron Wake",
        sea_worthiness=0.85,
        risk_factor=0.5,
        desc="a broad-beamed cargo cog with thick oak strakes",
    ),
    "long": ShipType(
        id="long",
        label="Swift Dart",
        sea_worthiness=0.70,
        risk_factor=0.8,
        desc="a graceful fluit whose lines cut through water like a needle",
    ),
}

STORM_LEVELS = {
    "spectacular": StormLevel(
        id="spectacular",
        label="Spectacular Squall",
        intensity=0.9,
        noise="a colossal roar that rattled fillings in the jaw",
        splash_factor=1.3,
    ),
    "fierce": StormLevel(
        id="fierce",
        label="Fierce Gale",
        intensity=0.65,
        noise="howling winds that whistled through the rigging like death itself",
        splash_factor=0.9,
    ),
}

TREASURES = {
    "glistening_chest": Treasure(
        id="glistening_chest",
        label="golden chest",
        phrase="sun-bright chest dug up from Davy Jones’ own locker",
        region="cabin",
        glows=True,
        description="glistened under each lightning flicker",
    ),
    "treasure_coins": Treasure(
        id="gold_coins",
        label="gold coins",
        phrase="mountains of newly-minted doubloons fleeted with fish scales",
        region="hold",
        glows=True,
        description="glistened like captured sunlight",
    ),
    "jewelled_crown": Treasure(
        id="crown_of_morgause",
        label="crowned jewel",
        phrase="ruby-encrusted crown weighing more than a child",
        region="deck",
        glows=False,
    ),
}

def valid_combos() -> list[tuple]:
    combos = []
    for storm_id, storm in STORM_LEVELS.items():
        for ship_id, ship in SHIP_TYPES.items():
            for tid, treasure in TREASURES.items():
                combos.append((storm_id, ship_id, tid))
    return combos

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    storm_id = f.get("storm_level", "none")
    ship_id = f.get("ship_type", "none")
    tre_id = f.get("treasure_cfg", Treasure("", "", "", "")).id
    seed = f.get("seed", 424242)
    return [
        f'Tell a swashbuckling pirate tale for youngsters featuring the words '
        f'"spectacular", "squat", and "glisten". Create one story under two-hundred words.',
        f'Write a short pirate’s coming-of-age story (about 200 words) for '
        f'3–5-year-olds using the word "spectacular" to describe a storm. '
        'End with the young pirate learning a lesson.',
        f'A tiny "{ship_id}" boat pursues a {tre_id} that glistens in the light '
        f'of a {storm_id} storm. Show the lesson learned when the reckless boy '
        f'transforms into a steady sailor.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "squint")
    captain = _safe_fact(world, f, "captain")
    ship = world.get("ship")
    storm = world.get("storm")
    treasure = _safe_fact(world, f, "treasure_cfg")
    pw = captain.label_word
    hero_pronouns = (
        hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    )
    storm_desc = storm.phrase if storm else "a fierce storm"
    qa: list[QAItem] = [
        QAItem(
            question="Who went looking for treasure through a spectacular storm?",
            answer=f"It was {hero.id}, a lively boy on the {ship.label} "
                   f"sailed by {captain.id}, in search of the {treasure.phrase}.",
        ),
        QAItem(
            question="What kind of ship was the Squat Hull?",
            answer=f"The {ship.label} was a {ship.traits[0]} vessel with "
                   "patched calico sails, perfect for coasting but poor in squalls.",
        ),
        QAItem(
            question="Why did Captain Ironhook warn Squint before the storm?",
            answer=f"Because the Squat Hull could not handle {storm_desc}; "
                   "waves would overwhelm its low hull.",
        ),
    ]
    if f.get("transformation"):
        qa.append(QAItem(
            question=(
                f"How did {hero.id} change after the storm hit the {ship.label}?"
            ),
            answer=(
                f"Though his recklessness put them all in peril, once the "
                f"{ship.label} began to sink {hero.id} took responsibility, "
                f"helped secure the sails, and finally reached the treasure "
                f"not as a heedless pirate but as a future captain."
            ),
        ))
    if f.get("treasure_secured"):
        qa.append(QAItem(
            question="What glistened under the lightning that guided Squint?",
            answer=(
                f"A {treasure.phrase} lay hidden in a cove, "
                f"its gold and jewels {treasure.description}."
            ),
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    qa: list[QAItem] = []
    if any("spectacular" in word for word in world.facts.get("prompts", [])):
        qa.append(QAItem(
            question="What does spectacular mean?",
            answer="Spectacular means very impressive or exciting — like a "
                   "huge crashing wave or a sky lit by an emerald rainbow!",
        ))
    if any("glisten" in word for word in world.facts.get("prompts", [])):
        qa.append(QAItem(
            question="When do things glisten?",
            answer="Things glisten when they sparkle like wet metal or polished gold "
                   "under sunlight or lightning.",
        ))
    if any("squat" in word for word in world.facts.get("prompts", [])):
        qa.append(QAItem(
            question="What is a squat vessel?",
            answer="A squat vessel is a boat with a low, broad hull built for calm "
                   "waters rather than big waves.",
        ))
    qa.extend([
        QAItem(
            question="Why do pirates love treasure?",
            answer="Sea dogs treasure gold, jewels and shiny things because they "
                   "can trade them for food, rum, and a ship to sail again.",
        ),
        QAItem(
            question="What does it mean to learn a lesson at sea?",
            answer="Learning at sea means facing danger and coming out wiser, "
                   "so next time you choose more carefully.",
        ),
    ])
    return qa[:3]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    lines.append("\n== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}\nA: {item.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world state ---"]
    for e in list(world.entities.values()):
        meters = {k: f"{v:.2f}" for k, v in e.meters.items() if v}
        memes = {k: f"{v:.2f}" for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:15} ({e.type:7}) {' | '.join(bits)}")
    lines.append(f"  fired: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

ASP_RULES = r"""
% Valid pirate stories: ship, storm, treasure exist and end with transformation
ship(S) :- ship_type(S), sea_worthiness(S, SW), SW >= 0.0.
storm(T) :- storm_level(T), intensity(T, I), I > 0.0.
treasure(Tr) :- treasure(Tr), phrase(Tr,P), P="glistening…"|P="golden…".
valid_story(S, T, Tr) :- ship(S), storm(T), treasure(Tr).
transformed :- character(C), type(C,"boy"), memes(C,"responsibility",R), R >= 1.0.
has_lesson :- character(C), memes(C,"lesson_learned", L), L >= 1.0.
:- valid_story(S,T,Tr), not transformed.
:- valid_story(S,T,Tr), not has_lesson.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SHIP_TYPES.values():
        lines.append(asp.fact("ship_type", s.id))
        lines.append(asp.fact("sea_worthiness", s.id, s.sea_worthiness))
    for t in STORM_LEVELS.values():
        lines.append(asp.fact("storm_level", t.id))
        lines.append(asp.fact("intensity", t.id, t.intensity))
    for tr in TREASURES.values():
        lines.append(asp.fact("treasure", tr.id))
        if tr.glows:
            lines.append(asp.fact("glistening", tr.id))
    return "\n".join(lines)

def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    clingo_set = set(asp.asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only clingo: ", sorted(clingo_set - python_set))
    print("  only python:", sorted(python_set - clingo_set))
    return 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Squint chases glistening treasure aboard a squat ship through a spectacular storm!")
    ap.add_argument("--storm", choices=STORM_LEVELS, help="storm level id")
    ap.add_argument("--ship", choices=SHIP_TYPES, help="ship type id")
    ap.add_argument("--treasure", choices=TREASURES, help="treasure id")
    ap.add_argument("--name", default="Squint", help="young pirate’s name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="pre-curated set")
    ap.add_argument("--trace", action="store_true", help="show world state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list clingo valid stories")
    ap.add_argument("--verify", action="store_true", help="check ASP parity")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap

@dataclass
class StoryParams:
    storm: str
    ship: str
    treasure: str
    name: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "storm", None) and getattr(args, "ship", None):
        storm_ok = float(_safe_lookup(STORM_LEVELS, getattr(args, "storm", None)).intensity) * 0.5 <= float(_safe_lookup(SHIP_TYPES, getattr(args, "ship", None)).sea_worthiness)
        if not storm_ok:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "storm", None) is None or c[0] == getattr(args, "storm", None))
              and (getattr(args, "ship", None) is None or c[1] == getattr(args, "ship", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    storm_id, ship_id, treasure_id = rng.choice(list(combos))
    return StoryParams(
        storm=storm_id,
        ship=ship_id,
        treasure=treasure_id,
        name=getattr(args, "name", None) if getattr(args, "name", None) else rng.choice(["Squint", "Pip", "Snag", "Tuck"]),
        seed=getattr(args, "seed", None) if getattr(args, "seed", None) else rng.randrange(2**31),
    )

def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS["open_waters"]
    world = tell(setting, _safe_lookup(SHIP_TYPES, params.ship), _safe_lookup(STORM_LEVELS, params.storm),
                 _safe_lookup(TREASURES, params.treasure), params.name)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )
    sample.prompts.append(
        f'Write a Pirate Tale for kids (under 220 words) using the words '
        f'"{params.ship}", "{params.storm}", and "{params.treasure}". '
        'End with the word "changed" to show transformation.'
    )
    return sample

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))

CURATED = [
    StoryParams(storm="spectacular", ship="squat", treasure="glistening_chest", name="Squint"),
    StoryParams(storm="fierce", ship="sturdy", treasure="treasure_coins", name="Pip"),
    StoryParams(storm="spectacular", ship="long", treasure="jewelled_crown", name="Snag"),
]

def main() -> None:
    args = build_parser().parse_args()
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = valid_combos()
        print(f"{len(pairs)} valid (storm, ship, treasure) combos:\n")
        for storm, ship, tid in pairs:
            print(f"  {storm:12}   {ship:8}   {tid}")
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
                story_text = sample.story
                if story_text in seen:
                    continue
                seen.add(story_text)
                samples.append(sample)
            except StoryError as err:
                print(err, file=sys.stderr)
                continue

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.ship} vs {p.storm} for {p.treasure} ({p.seed})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
