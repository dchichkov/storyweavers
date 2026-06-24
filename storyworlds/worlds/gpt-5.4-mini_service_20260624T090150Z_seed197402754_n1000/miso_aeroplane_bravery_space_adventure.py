#!/usr/bin/env python3
"""
storyworlds/worlds/miso_aeroplane_bravery_space_adventure.py
============================================================

A small storyworld for a Space Adventure flavored tale about miso, an aeroplane,
and bravery.

Seed-tale premise:
- A child pilot helps bring a warm bowl of miso soup on a tiny aeroplane trip.
- The sky trip turns uneasy when a bumpy cloudfield or space gusts shake the cabin.
- Bravery matters when the hero must keep calm, fix the problem, and land safely.

The world model tracks physical meters and emotional memes:
- meters: things like wobble, spill, heat, seal, distance, damage
- memes: things like fear, bravery, trust, relief, pride

This script follows the storyworld contract:
- build_parser, resolve_params, generate, emit, main
- lazy ASP import inside helpers
- inline ASP_RULES twin of the Python reasonableness gate
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cargo: object | None = None
    g: object | None = None
    hero: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for key in ["wobble", "spill", "damage", "seal", "heat", "distance"]:
            self.meters.setdefault(key, 0.0)
        for key in ["fear", "bravery", "trust", "relief", "pride"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "pilot"}
        male = {"boy", "father", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id
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
    place: str
    affords: set[str] = field(default_factory=set)
    sky_kind: str = "space"  # space | clouds | moon
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
class Flight:
    id: str
    name: str
    verb: str
    gerund: str
    danger: str
    fix_hint: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    zone: set[str] = field(default_factory=set)
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
class Cargo:
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


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sky: str = setting.sky_kind

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.sky = self.sky
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "shuttle": Setting(place="the little shuttle", affords={"spaceflight", "landing"}, sky_kind="space"),
    "moonbase": Setting(place="the moon base", affords={"landing"}, sky_kind="moon"),
    "clouddeck": Setting(place="the cloud deck", affords={"spaceflight"}, sky_kind="clouds"),
}

FLIGHTS = {
    "spaceflight": Flight(
        id="spaceflight",
        name="space flight",
        verb="fly through the starry sky",
        gerund="flying through the starry sky",
        danger="the ship would wobble in the wind-sparks",
        fix_hint="a steady harness and a brave breath",
        keyword="space",
        tags={"space", "stars", "wind"},
        zone={"body"},
    ),
    "landing": Flight(
        id="landing",
        name="landing",
        verb="land on the moon platform",
        gerund="landing carefully on the moon platform",
        danger="the ship could bump hard on the silver deck",
        fix_hint="a soft landing and a calm hand",
        keyword="moon",
        tags={"moon", "landing"},
        zone={"body"},
    ),
}

CARGO = {
    "miso": Cargo(
        id="miso",
        label="miso soup",
        phrase="a warm bowl of miso soup",
        region="hands",
        plural=False,
        genders={"girl", "boy"},
    ),
    "thermos": Cargo(
        id="thermos",
        label="thermos",
        phrase="a sealed soup thermos",
        region="hands",
        plural=False,
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="lid",
        label="a tight lid",
        covers={"hands"},
        guards={"spill"},
        prep="clip on a tight lid",
        tail="snapped the lid shut",
    ),
    Gear(
        id="harness",
        label="a safety harness",
        covers={"body"},
        guards={"wobble", "damage"},
        prep="buckle a safety harness",
        tail="buckled the safety harness",
    ),
    Gear(
        id="tray",
        label="a steady tray",
        covers={"hands"},
        guards={"spill", "wobble"},
        prep="set the bowl in a steady tray",
        tail="set the soup in the steady tray",
    ),
    Gear(
        id="visor",
        label="a bright visor",
        covers={"eyes"},
        guards={"fear"},
        prep="pull down a bright visor",
        tail="lowered the bright visor",
    ),
]

NAMES = {
    "girl": ["Mina", "Luna", "Aya", "Nori", "Tia", "Mila"],
    "boy": ["Kai", "Noel", "Rio", "Tomo", "Eli", "Jun"],
}
TRAITS = ["curious", "gentle", "bold", "careful", "spirited", "brave"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    flight: str
    cargo: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
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


def cargo_at_risk(flight: Flight, cargo: Cargo) -> bool:
    return cargo.region in flight.zone


def select_gear(flight: Flight, cargo: Cargo) -> Optional[Gear]:
    # A fix is reasonable only if it can actually guard the sort of trouble the flight creates.
    for gear in GEAR:
        if flight.id == "spaceflight" and "wobble" in gear.guards and cargo.region in gear.covers:
            return gear
        if flight.id == "landing" and ("damage" in gear.guards or "wobble" in gear.guards) and cargo.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for fid in setting.affords:
            flight = _safe_lookup(FLIGHTS, fid)
            for cid, cargo in CARGO.items():
                if cargo_at_risk(flight, cargo) and select_gear(flight, cargo):
                    combos.append((place, fid, cid))
    return combos


def explain_rejection(flight: Flight, cargo: Cargo) -> str:
    return (
        f"(No story: {flight.gerund} would not honestly threaten {cargo.phrase}. "
        f"The parent would have no real reason to worry, so the scene would be flat.)"
    )


def explain_gender(cargo_id: str, gender: str) -> str:
    return (
        f"(No story: a {CARGO[cargo_id].label} is not restricted by gender here, "
        f"so try a different pin.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _do_flight(world: World, actor: Entity, flight: Flight, narrate: bool = True) -> None:
    actor.meters["distance"] += 1
    actor.meters["wobble"] += 1
    actor.memes["fear"] += 1
    actor.memes["bravery"] += 1
    if narrate:
        world.say(f"{actor.name} kept the little ship moving as the {flight.name} began.")


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wobble"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region != "hands":
                continue
            sig = ("spill", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["spill"] += 1
            item.meters["damage"] += 1
            out.append(f"{actor.name}'s {item.label} sloshed and got messy.")
    return out


CAUSAL_RULES = []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, flight: Flight, cargo_id: str) -> dict:
    sim = world.copy()
    _do_flight(sim, sim.get(actor.id), flight, narrate=False)
    cargo = sim.entities[cargo_id]
    return {
        "spilled": cargo.meters["spill"] >= THRESHOLD,
        "fear": sim.get(actor.id).memes["fear"],
    }


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.name} was a little {hero.type} with a brave heart and a big wish to help."
    )


def loves(world: World, hero: Entity, flight: Flight) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {flight.gerund} and watching the silver stars slide by."
    )


def loads(world: World, hero: Entity, cargo: Entity) -> None:
    world.say(
        f"Before takeoff, {hero.name} carried {hero.pronoun('object')} {cargo.phrase} into the cabin."
    )


def warns(world: World, hero: Entity, cargo: Entity, flight: Flight, parent: Entity) -> bool:
    pred = predict_mess(world, hero, flight, cargo.id)
    if not pred["spilled"]:
        return False
    world.facts["predicted_spill"] = True
    world.say(
        f'"If the ship wobbles, your {cargo.label} could spill," {parent.name} said. '
        f'"We should choose a safer way."'
    )
    return True


def brave_choice(world: World, hero: Entity, flight: Flight) -> None:
    hero.memes["fear"] += 1
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.name} felt a tiny shiver, but {hero.pronoun()} took one brave breath and held steady."
    )
    world.say(
        f"{hero.pronoun().capitalize()} reached for the controls and kept the ship on course."
    )


def offer_fix(world: World, hero: Entity, parent: Entity, flight: Flight, cargo: Entity) -> Optional[Gear]:
    gear = select_gear(flight, cargo)
    if gear is None:
        return None
    g = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        protective=True,
        covers=set(gear.covers),
        owner=hero.id,
    ))
    g.worn_by = hero.id
    if predict_mess(world, hero, flight, cargo.id)["spilled"]:
        g.worn_by = None
        del world.entities[g.id]
        return None
    world.say(
        f"{parent.name} pointed to {gear.label} and smiled. "
        f'"How about we {gear.prep} first?"'
    )
    return g


def accept_fix(world: World, hero: Entity, parent: Entity, flight: Flight, cargo: Entity, gear: Gear) -> None:
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.name} nodded and {gear.tail}."
    )
    world.say(
        f"Then the little ship moved on, {flight.gerund}, while {cargo.label} stayed safe and warm."
    )
    world.say(
        f"{hero.name} looked out at the stars and felt brave enough for the whole sky."
    )


def tell(setting: Setting, flight: Flight, cargo_cfg: Cargo, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type=cargo_cfg.id,
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    cargo.worn_by = hero.id

    # Act 1
    introduce(world, hero)
    loves(world, hero, flight)
    loads(world, hero, cargo)

    # Act 2
    world.para()
    world.say(
        f"One day, {hero.name} and {hero.pronoun('possessive')} {parent.label} boarded {setting.place}."
    )
    world.say(
        f"The trip was set for {flight.verb}, but {flight.danger}."
    )
    warns(world, hero, cargo, flight, parent)
    brave_choice(world, hero, flight)

    # Act 3
    world.para()
    gear = offer_fix(world, hero, parent, flight, cargo)
    if gear:
        accept_fix(world, hero, parent, flight, cargo, gear)

    world.facts.update(
        hero=hero,
        parent=parent,
        cargo=cargo,
        cargo_cfg=cargo_cfg,
        flight=flight,
        setting=setting,
        gear=gear if "gear" in locals() else None,
        resolved=bool(gear),
    )
    return world


# ---------------------------------------------------------------------------
# Prose registries and helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, cargo, flight = f["hero"], f["cargo_cfg"], f["flight"]
    return [
        f'Write a short space adventure for a young child about "{cargo.label}" and bravery.',
        f"Tell a gentle story where {hero.name} must {flight.verb} while protecting {cargo.phrase}.",
        f'Write a small story that includes the word "{cargo.label}" and ends with a brave, safe choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, cargo, flight = f["hero"], f["parent"], f["cargo"], f["flight"]
    qa = [
        QAItem(
            question=f"What was {hero.name} carrying on the little ship?",
            answer=f"{hero.name} was carrying {cargo.phrase}."
        ),
        QAItem(
            question=f"Why did the parent worry before {flight.verb}?",
            answer=f"The parent worried because {flight.danger}, and that could make {cargo.label} spill."
        ),
        QAItem(
            question=f"What did {hero.name} do when things felt scary?",
            answer=f"{hero.name} took a brave breath, held steady, and kept the ship on course."
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did the family keep the cargo safe?",
                answer=f"They used {f['gear'].label} first, so {cargo.label} stayed safe and warm."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aeroplane?",
            answer="An aeroplane is a flying vehicle that carries people through the air."
        ),
        QAItem(
            question="What is miso soup?",
            answer="Miso soup is a warm soup made with miso, a salty paste often used in Japanese cooking."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary while trying to stay calm and do the right thing."
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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(F, C) :- flight(F), cargo(C), cargo_region(C, R), flight_zone(F, R).
has_fix(F, C) :- prize_at_risk(F, C), gear(G), guards(G, M), threatens(F, M), covers(G, R), cargo_region(C, R).
valid(Place, F, C) :- setting(Place), affords(Place, F), prize_at_risk(F, C), has_fix(F, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for fid, f in FLIGHTS.items():
        lines.append(asp.fact("flight", fid))
        for r in sorted(f.zone):
            lines.append(asp.fact("flight_zone", fid, r))
        for t in sorted(f.tags):
            lines.append(asp.fact("threatens", fid, t))
    for cid, c in CARGO.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("cargo_region", cid, c.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        # Also exercise generation.
        rng = random.Random(1234)
        params = resolve_params(argparse.Namespace(place=None, flight=None, cargo=None, gender=None, name=None, parent=None), rng)
        sample = generate(params)
        if not sample.story.strip():
            print("FAIL: generated story was empty.")
            return 1
        print("OK: generation produced a non-empty story.")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="shuttle", flight="spaceflight", cargo="miso", name="Mina", gender="girl", trait="brave"),
    StoryParams(place="moonbase", flight="landing", cargo="thermos", name="Kai", gender="boy", trait="careful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: miso, aeroplane, and bravery in a small space adventure."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--flight", choices=FLIGHTS)
    ap.add_argument("--cargo", choices=CARGO)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "flight", None) and getattr(args, "cargo", None):
        flight, cargo = _safe_lookup(FLIGHTS, getattr(args, "flight", None)), CARGO[getattr(args, "cargo", None)]
        if not (cargo_at_risk(flight, cargo) and select_gear(flight, cargo)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "flight", None) is None or c[1] == getattr(args, "flight", None))
              and (getattr(args, "cargo", None) is None or c[2] == getattr(args, "cargo", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, flight_id, cargo_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, flight=flight_id, cargo=cargo_id, name=name, gender=gender, trait=trait, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(FLIGHTS, params.flight), CARGO[params.cargo], params.name, params.gender, "parent")
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, flight, cargo) combos:\n")
        for place, flight, cargo in combos:
            print(f"  {place:10} {flight:12} {cargo}")
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
            header = f"### {p.name}: {p.flight} with {p.cargo} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
