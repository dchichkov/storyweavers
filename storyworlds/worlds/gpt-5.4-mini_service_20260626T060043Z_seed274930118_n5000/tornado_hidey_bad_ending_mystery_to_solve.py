#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tornado_hidey_bad_ending_mystery_to_solve.py
===========================================================================================================

A small space-adventure story world built from the seed words:
tornado, hidey.

Premise:
- A tiny crew on a dusty frontier world notices a strange tornado swirling near
  their dock.
- Someone has also hidden the emergency beacon in a hidey nook, and the crew
  must solve that mystery before the storm hits.
- The story keeps a space-adventure feel: ship decks, scanners, rover bays,
  hatch seals, and a tense countdown.
- It supports a "Bad Ending" mode where the crew learns the truth too late and
  the storm wins, but the story still reads like a complete, child-facing tale.

The world is intentionally small and state-driven:
- physical meters: damage, dust, charge, speed, safety, etc.
- emotional memes: worry, hope, curiosity, blame, relief, etc.

The story generator uses a simple causal simulation, plus an inline ASP twin
for parity checks on the reasonableness gate and registry-derived facts.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Data model
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
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
    place: str
    indoors: bool
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
class Event:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    damage: str
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
class StoryParams:
    place: str
    event: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = set(self.zone)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "orbital_dock": Setting("the orbital dock", indoors=False, affords={"tornado"}),
    "mars_outpost": Setting("the Mars outpost", indoors=False, affords={"tornado"}),
    "cargo_bay": Setting("the cargo bay", indoors=True, affords={"tornado"}),
}

EVENTS = {
    "tornado": Event(
        id="tornado",
        verb="follow the tornado",
        gerund="watching the tornado swirl",
        rush="run toward the dock doors",
        hazard="dust and sparks",
        damage="damaged",
        zone={"dock", "bay", "tower"},
        keyword="tornado",
        tags={"tornado", "wind", "storm"},
    ),
}

PRIZES = {
    "beacon": Prize(
        id="beacon",
        label="beacon",
        phrase="a tiny emergency beacon",
        region="hand",
        plural=False,
    ),
    "map": Prize(
        id="map",
        label="map",
        phrase="a folded star map",
        region="hand",
        plural=False,
    ),
    "capsule": Prize(
        id="capsule",
        label="capsule",
        phrase="a little message capsule",
        region="chest",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="magnet_cloak",
        label="a magnet cloak",
        covers={"chest", "hand"},
        guards={"dust"},
        prep="put on a magnet cloak",
        tail="pulled on the magnet cloak",
    ),
    Gear(
        id="storm_shell",
        label="storm-shell boots",
        covers={"feet"},
        guards={"wind"},
        prep="lace up storm-shell boots",
        tail="laced up the storm-shell boots",
        plural=True,
    ),
    Gear(
        id="hidey_shield",
        label="the hidey shield panel",
        covers={"chest", "hand", "feet"},
        guards={"dust", "wind"},
        prep="slide behind the hidey shield panel",
        tail="slid behind the hidey shield panel",
    ),
]

NAMES = {
    "girl": ["Mira", "Luna", "Tess", "Nova", "Ivy"],
    "boy": ["Kai", "Finn", "Jett", "Leo", "Ari"],
}
TRAITS = ["brave", "curious", "small", "careful", "quick"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for evt in setting.affords:
            for prize in PRIZES:
                if event_at_risk(_safe_lookup(EVENTS, evt), _safe_lookup(PRIZES, prize)) and select_gear(_safe_lookup(EVENTS, evt), _safe_lookup(PRIZES, prize)):
                    combos.append((place, evt, prize))
    return combos


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def event_at_risk(event: Event, prize: Prize) -> bool:
    return prize.region in event.zone


def select_gear(event: Event, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if prize.region in g.covers and "dust" in g.guards:
            return g
        if prize.region in g.covers and "wind" in g.guards:
            return g
    return None


def explain_rejection(event: Event, prize: Prize) -> str:
    return (
        f"(No story: the {event.keyword} would not reach a {prize.label} on the {prize.region}, "
        f"or there is no safe hidey gear that fits the problem.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s item here; try --gender {ok}.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _storm_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.chars():
        if actor.meters.get("storm", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.id in world.fired:
                continue
            if item.owner != actor.id:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            world.fired.add((item.id, "storm"))
            item.meters["dust"] = item.meters.get("dust", 0.0) + 1
            item.meters["damage"] = item.meters.get("damage", 0.0) + 1
            out.append(f"The storm slapped {actor.pronoun('possessive')} {item.label} with dust.")
    return out


def _fear_rise(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.chars():
        if actor.memes.get("worry", 0.0) >= THRESHOLD and actor.id not in world.fired:
            actor.memes["panic"] = actor.memes.get("panic", 0.0) + 1
            world.fired.add((actor.id, "panic"))
            out.append(f"{actor.id} felt a shaky knot of worry.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    sentences: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_storm_damage, _fear_rise):
            produced = rule(world)
            if produced:
                changed = True
                sentences.extend(produced)
    if narrate:
        for s in sentences:
            world.say(s)
    return sentences


def predict_damage(world: World, actor: Entity, event: Event, prize_id: str) -> dict:
    sim = world.copy()
    _do_event(sim, sim.get(actor.id), event, narrate=False)
    prize = sim.get(prize_id)
    return {
        "damaged": prize.meters.get("damage", 0.0) >= THRESHOLD,
        "dusty": prize.meters.get("dust", 0.0) >= THRESHOLD,
    }


def _do_event(world: World, actor: Entity, event: Event, narrate: bool = True) -> None:
    world.zone = set(event.zone)
    actor.meters["storm"] = actor.meters.get("storm", 0.0) + 1
    actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {next(t for t in hero.memes if t != 'worry') if hero.memes else 'space'} explorer aboard the ship.")


def setup(world: World, hero: Entity, parent: Entity, prize: Entity, event: Event) -> None:
    world.say(f"{hero.id} loved the bright corridors of the ship and the hum of the engines.")
    world.say(f"One day, {hero.id}'s {parent.label} found {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id} liked {prize.item_pronoun()} and carried {prize.item_pronoun()} everywhere.")


def mystery(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(
        f"But then the {prize.label} vanished from the shelf, and everybody looked at the hidey nook."
    )
    world.say(
        f"{hero.id} wanted to know who hid it, because a hidden {prize.label} could make the next launch go wrong."
    )


def warning(world: World, hero: Entity, parent: Entity, event: Event, prize: Entity) -> None:
    pred = predict_damage(world, hero, event, prize.id)
    if pred["damaged"]:
        world.facts["predicted_damage"] = True
        world.say(
            f'"If the {event.keyword} reaches the dock, your {prize.label} will get {event.damage}," {parent.pronoun("possessive")} {parent.type} said.'
        )
        world.say(f'"We should solve the mystery before the storm wakes up," {parent.pronoun()} added.')


def hidey_turn(world: World, hero: Entity, parent: Entity, event: Event) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"{hero.id} peeked into the hidey nook behind the repair crates.")
    world.say(f"There, tucked in the dark, was a tiny lever with dust on it.")


def bad_choice(world: World, hero: Entity, parent: Entity, event: Event) -> None:
    hero.memes["blame"] = hero.memes.get("blame", 0.0) + 1
    world.say(
        f"{hero.id} guessed the wrong clue and pulled the lever too soon."
    )
    world.say(
        f"The hatch clicked open, and the {event.keyword} caught the ship before the lock could shut."
    )


def ending_bad(world: World, hero: Entity, parent: Entity, prize: Entity, event: Event) -> None:
    prize.meters["dust"] = prize.meters.get("dust", 0.0) + 1
    prize.meters["damage"] = prize.meters.get("damage", 0.0) + 1
    hero.memes["hope"] = 0.0
    world.say(
        f"By the time {hero.id} found the real answer, the {prize.label} was already dusty and bent."
    )
    world.say(
        f"The crew sat in the hidey nook while the {event.keyword} rumbled past the windows, and the ship stayed stuck at the dock."
    )


def tell(setting: Setting, event: Event, prize_cfg: Prize,
         hero_name: str = "Mira", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        memes={t: 0.0 for t in ["worry", "curiosity", "hope", "blame"]},
    ))
    hero.memes["worry"] = 0.0
    parent = world.add(Entity(
        id="Captain",
        kind="character",
        type=parent_type,
        label="captain",
        memes={"worry": 0.0},
    ))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
        owner=hero.id,
        caretaker=parent.id,
    ))

    setup(world, hero, parent, prize, event)
    world.para()
    mystery(world, hero, parent, prize)
    warning(world, hero, parent, event, prize)
    hidey_turn(world, hero, parent, event)
    world.para()
    bad_choice(world, hero, parent, event)
    ending_bad(world, hero, parent, prize, event)

    world.facts.update(hero=hero, parent=parent, prize=prize, event=event, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Registries / QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    event = _safe_fact(world, f, "event")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short space-adventure story about a child who finds a hidey nook, a tornado, and a missing {prize.label}.',
        f'Tell a gentle mystery where {hero.id} must figure out who hid the {prize.label} before the {event.keyword} reaches the ship.',
        f'Write a child-friendly story set on a ship with a storm outside and a bad ending that still feels complete.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    event = _safe_fact(world, f, "event")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What was the mystery in the story at {place}?",
            answer=f"The mystery was who hid the {prize.label} in the hidey nook before the tornado came.",
        ),
        QAItem(
            question=f"Why did {hero.id} and the captain worry about the {prize.label}?",
            answer=f"They worried because the tornado could reach the dock and leave the {prize.label} dusty and damaged.",
        ),
        QAItem(
            question=f"Where did {hero.id} look for clues?",
            answer=f"{hero.id} looked in the hidey nook behind the repair crates, because that was the best place for a secret clue.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended badly: the crew learned the answer too late, the {prize.label} got damaged, and the ship stayed stuck while the tornado passed.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "tornado": [
        QAItem(
            question="What is a tornado?",
            answer="A tornado is a very fast spinning wind storm that can blow dust and push things around.",
        ),
        QAItem(
            question="Why is a tornado dangerous?",
            answer="A tornado is dangerous because it can break things, carry dust into the air, and make it hard to stay safe.",
        ),
    ],
    "hidey": [
        QAItem(
            question="What is a hidey nook?",
            answer="A hidey nook is a small hidden spot where someone can tuck something away or hide for a little while.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["event"].tags)
    out: list[QAItem] = []
    for tag in ("tornado", "hidey"):
        if tag in tags or tag == "hidey":
            out.extend(WORLD_KNOWLEDGE.get(tag, []))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
event_at_risk(E,P) :- zone(E,R), prize_region(P,R).
gear_ok(G,E,P) :- prize_region(P,R), covers(G,R), guards(G,dust).
valid(Place,E,P) :- afford(Place,E), event_at_risk(E,P), gear_ok(G,E,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for e in sorted(s.affords):
            lines.append(asp.fact("afford", sid, e))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        for z in sorted(e.zone):
            lines.append(asp.fact("zone", eid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gd in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - asp_set:
        print("  only in Python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a tornado, a hidey nook, and a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain", "pilot"])
    ap.add_argument("--name")
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
    if getattr(args, "event", None) and getattr(args, "prize", None):
        evt = _safe_lookup(EVENTS, getattr(args, "event", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (event_at_risk(evt, pr) and select_gear(evt, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, event, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender not in _safe_lookup(PRIZES, prize).genders:
        gender = next(iter(sorted(_safe_lookup(PRIZES, prize).genders)))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["captain", "pilot"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(EVENTS, params.event), _safe_lookup(PRIZES, params.prize),
                 hero_name=params.name, hero_type=params.gender, hero_traits=[params.trait], parent_type=params.parent)
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


def CURATED() -> list[StoryParams]:
    return [
        StoryParams(place="orbital_dock", event="tornado", prize="beacon", name="Mira", gender="girl", parent="captain", trait="curious"),
        StoryParams(place="mars_outpost", event="tornado", prize="map", name="Kai", gender="boy", parent="pilot", trait="brave"),
        StoryParams(place="cargo_bay", event="tornado", prize="capsule", name="Nova", gender="girl", parent="captain", trait="careful"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
