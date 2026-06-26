#!/usr/bin/env python3
"""
storyworlds/worlds/soap_dogie_tweak_loading_dock_humor_pirate.py
=================================================================

A small pirate-tale storyworld set at a loading dock.

Premise:
- A cheerful little pirate crew works beside a loading dock.
- A dogie (a small dog) gets curious about the soap used to scrub the deck.
- A tiny tweak in the crew's plan turns a slippery problem into a funny, safe
  little rescue.

This world keeps the action concrete and state-driven:
- meters track physical conditions like wetness, slipperiness, cargo stability,
  and cleanliness
- memes track feelings like worry, amusement, pride, and relief

The generated stories stay close to a pirate tale tone while remaining
child-facing and humorous.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

CREW_NAMES = [
    "Mira",
    "Nell",
    "Pip",
    "Jory",
    "Tessa",
    "Bo",
    "Ada",
    "Kite",
]

DOGIE_NAMES = [
    "Dogie",
    "Muffin",
    "Skipper",
    "Pebble",
    "Buttons",
]

TREASURE_NAMES = [
    "a crate of oranges",
    "a barrel of biscuits",
    "a bundle of rope",
    "a sack of shiny shells",
]

HUMOR_BEATS = [
    "it made even the grumpiest gull sound like it was chuckling",
    "it looked so silly that the dockhands snorted with laughter",
    "it was the kind of joke that made a tiny dog wag twice as fast",
    "it turned the whole dock into a giggly scramble",
]


# ---------------------------------------------------------------------------
# Entities
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    dogie: object | None = None
    ent: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "pirate-girl", "captainess", "mother"}
        male = {"boy", "man", "pirate-boy", "captain", "father"}
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
    place: str = "the loading dock"
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
        return any(item.protective and region in getattr(item, "covers", set())
                   for item in self.worn_items(actor))

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "dock": Setting(place="the loading dock", affords={"soap_scrub", "rope_tug"}),
}

ACTIVITIES = {
    "soap_scrub": Activity(
        id="soap_scrub",
        verb="scrub the deck",
        gerund="scrubbing the deck",
        rush="dash through the suds",
        mess="slippery",
        soil="all slick and foamy",
        zone={"floor"},
        keyword="soap",
        tags={"soap", "humor", "dock"},
    ),
    "rope_tug": Activity(
        id="rope_tug",
        verb="tug the rope",
        gerund="tugging the rope",
        rush="pull the rope too hard",
        mess="jolted",
        soil="out of line",
        zone={"floor", "hands"},
        keyword="tweak",
        tags={"rope", "tweak", "humor", "dock"},
    ),
}

PRIZES = {
    "crate": Prize(
        label="crate",
        phrase="a crate of apples",
        type="crate",
        region="floor",
    ),
    "lantern": Prize(
        label="lantern",
        phrase="a brass lantern",
        type="lantern",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="grip_shoes",
        label="grippy dock shoes",
        covers={"floor"},
        guards={"slippery"},
        prep="put on grippy dock shoes first",
        tail="went back for the grippy dock shoes",
    ),
    Gear(
        id="apron",
        label="an oilcloth apron",
        covers={"hands", "floor"},
        guards={"slippery", "jolted"},
        prep="pull on an oilcloth apron",
        tail="pulled on the oilcloth apron",
    ),
    Gear(
        id="cloth",
        label="a dry cleaning cloth",
        covers={"hands"},
        guards={"jolted"},
        prep="keep a dry cleaning cloth ready",
        tail="kept the dry cleaning cloth ready",
    ),
]

NAMES = CREW_NAMES
DOGIE_NAMES = DOGIE_NAMES
TRAITS = ["cheery", "spry", "curious", "mischievous"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or prize.region == "floor"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Reasoner gate helpers
# ---------------------------------------------------------------------------

def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly threaten {prize.label}, "
        f"so the captain would have no real reason to warn anyone.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
fix(G, A, P) :- prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), fix(_, A, P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["mischief"] = actor.memes.get("mischief", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} went to {activity.gerund}.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": prize.meters.get("slippery", 0.0) >= THRESHOLD,
        "humor": actor.memes.get("amusement", 0.0),
    }


def introduce(world: World, hero: Entity, dogie: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.type} pirate with a bright grin, and {dogie.id} was a tiny dogie "
        f"who trotted everywhere as if the deck belonged to {dogie.pronoun('object')}."
    )


def dock_scene(world: World) -> None:
    world.say(
        "The loading dock smelled like salt, rope, and old sea air. "
        "Crates sat in neat stacks, and the gulls sounded like they were telling jokes."
    )


def love_dock_work(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved working at {world.setting.place} because "
        f"{activity.keyword} and rope always made the day feel lively."
    )


def warn_about_soap(world: World, captain: Entity, hero: Entity, prize: Entity) -> None:
    if world.facts.get("soapy_floor", False):
        world.say(
            f'"Careful," {captain.id} said. "That soap can make the boards slick, and '
            f'{prize.label} could slide right into a foolish little tumble."'
        )


def dogie_mischief(world: World, dogie: Entity) -> None:
    dogie.memes["curiosity"] = dogie.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{dogie.id} nosed at the soap, sneezed at the bubbles, and then skidded three tiny steps. "
        f"It was so funny that the crew laughed before they could even stop themselves."
    )
    world.facts["soapy_floor"] = True


def tweak_plan(world: World, captain: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f"{hero.id} thought a moment, then made a tiny tweak to the plan: "
        f"keep the soap on one side and the cargo on the other."
    )
    world.say(
        f"{captain.id} nodded, because a small tweak could save a big splash of trouble."
    )


def offer_gear(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    ent = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        protective=True,
    ))
    ent.worn_by = hero.id
    ent.covers = set(gear.covers)  # type: ignore[attr-defined]
    world.say(
        f'{captain.id} grinned and said, "How about we {gear.prep} and then work with the soap?"'
    )
    return gear


def resolve(world: World, hero: Entity, dogie: Entity, prize: Entity, gear: Gear) -> None:
    hero.memes["amusement"] = hero.memes.get("amusement", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id} laughed so hard that {hero.pronoun('possessive')} hat nearly tipped off. "
        f'{hero.pronoun().capitalize()} picked up {dogie.id}, gave {dogie.pronoun("object")} a gentle pat, and said, '
        f'"You are the silliest mate on the dock."'
    )
    world.say(
        f"Then they {gear.tail}, finished the work, and {prize.label} stayed safe and steady. "
        f"The loading dock ended in giggles, clean boards, and one very proud little pirate crew."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, dogie_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate", label="little pirate"))
    dogie = world.add(Entity(id=dogie_name, kind="character", type="dog", label="dogie"))
    captain = world.add(Entity(id="Captain", kind="character", type="captain", label="captain"))
    prize = world.add(Entity(
        id="Prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=captain.id,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero, dogie)
    dock_scene(world)
    love_dock_work(world, hero, activity)
    world.say(
        f"{hero.id} had a joke ready about {trait} pirates and a mop that looked like a sea monster, "
        f"which made the whole crew laugh."
    )

    world.para()
    world.say(
        f"One morning at {world.setting.place}, {hero.id} started {activity.gerund} while {prize.label} sat nearby."
    )
    _do_activity(world, hero, activity, narrate=False)
    if activity.keyword == "soap":
        world.facts["soapy_floor"] = True
        world.say(
            f"The soap made the planks shine, and the floor got slippery in a way that was funny "
            f"right up until someone nearly slid."
        )
    else:
        world.say(
            f"The rope tug sent a sharp little jolt through the deck, and everybody blinked, then laughed."
        )
    warn_about_soap(world, captain, hero, prize)
    dogie_mischief(world, dogie)

    world.para()
    tweak_plan(world, captain, hero, activity)
    gear = offer_gear(world, captain, hero, activity, prize)
    if gear:
        resolve(world, hero, dogie, prize, gear)

    world.facts.update(
        hero=hero,
        dogie=dogie,
        captain=captain,
        prize=prize,
        activity=activity,
        gear=gear,
        trait=trait,
        resolved=gear is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short pirate tale for a young child set at a loading dock about {hero.id}, soap, and a dogie.',
        f"Tell a humorous story where {hero.id} must handle {act.keyword} at the loading dock without letting {prize.label} get into trouble.",
        f'Write a gentle pirate story that includes the words "soap", "dogie", and "tweak".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    dogie = _safe_fact(world, f, "dogie")
    captain = _safe_fact(world, f, "captain")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    trait = _safe_fact(world, f, "trait")

    return [
        QAItem(
            question=f"Who were the main characters in the story?",
            answer=(
                f"The story was about {hero.id}, {dogie.id}, and {captain.id}. "
                f"{hero.id} was the pirate who worked at the loading dock, and {dogie.id} made the funny trouble."
            ),
        ),
        QAItem(
            question=f"What made the loading dock slippery?",
            answer=(
                f"The soap made the dock slippery. That was funny at first, but it also meant the crew had to be careful."
            ),
        ),
        QAItem(
            question=f"What tiny tweak did the pirate make?",
            answer=(
                f"{hero.id} made a tiny tweak to the plan by keeping the soap on one side and the cargo on the other."
            ),
        ),
        QAItem(
            question=f"Why did the captain worry about the prize?",
            answer=(
                f"The captain worried because the slippery floor could send {prize.label} into a silly mess at the loading dock."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {dogie.id}?",
            answer=(
                f"They ended up laughing together, and {hero.id} felt proud because the work got done safely "
                f"while {dogie.id} stayed a funny little helper."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "soap": [
        QAItem(
            question="What is soap used for?",
            answer="Soap is used to wash dirt and grease away so hands, dishes, or floors can get clean.",
        )
    ],
    "dogie": [
        QAItem(
            question="What is a dogie?",
            answer="A dogie is a small dog or a little dog-like animal, and it often likes to sniff and follow people around.",
        )
    ],
    "tweak": [
        QAItem(
            question="What does a tweak mean?",
            answer="A tweak is a small change or adjustment that can make a plan work better.",
        )
    ],
    "dock": [
        QAItem(
            question="What is a loading dock?",
            answer="A loading dock is a place where people load and unload boxes, crates, and other cargo from ships or trucks.",
        )
    ],
    "humor": [
        QAItem(
            question="What makes a story funny?",
            answer="A story can be funny when something surprising, silly, or a little bit clumsy happens, and everyone can laugh kindly.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags:
            out.extend(items)
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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    dogie: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CREW_NAMES)
    dogie = getattr(args, "dogie", None) or rng.choice(DOGIE_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, dogie=dogie, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.dogie,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Trace / emit / CLI
# ---------------------------------------------------------------------------

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
            bits.append(f"protective={True}")
            bits.append(f"covers={sorted(getattr(e, 'covers', set()))}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate loading-dock storyworld with soap, a dogie, and a tiny tweak."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--dogie")
    ap.add_argument("--trait")
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
    StoryParams(place="dock", activity="soap_scrud" if False else "soap_scratch" if False else "soap_srub" if False else "soap_scrub", prize="crate", name="Mira", dogie="Dogie", trait="cheery"),
]

# Fix curated with valid value explicitly.
CURATED = [
    StoryParams(place="dock", activity="soap_scratch" if False else "soap_scrub", prize="crate", name="Mira", dogie="Dogie", trait="cheery"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
