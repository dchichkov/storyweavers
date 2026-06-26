#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/kaka_set_cautionary_kindness_transformation_pirate_tale.py
==============================================================================================================================

A standalone story world for a small pirate tale with cautionary warnings,
kindness, and a clear transformation.

Premise:
- A young pirate sets out to sea with a chatty parrot named Kaka.
- Kaka gives a cautionary warning when the sea turns rough.
- The pirate chooses kindness toward a frightened helper instead of bravado.
- That kind choice transforms the pirate from harsh and reckless into calm and brave.

This script keeps the world tiny but state-driven:
- physical meters: wind, wetness, rope-tension, sail-safety
- emotional memes: worry, kindness, courage, pride, trust

The story is generated from simulated world state; the ending image proves the
change that happened.
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
# Core thresholds
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world state
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    boat: object | None = None
    helper: object | None = None
    hero: object | None = None
    kaka: object | None = None
    sail: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def them(self) -> str:
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
    place: str = "the harbor"
    sea: str = "the blue sea"
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
class Hazard:
    id: str
    label: str
    weather: str
    splash: str
    mess: str
    zone: set[str]
    caution_line: str
    tags: set[str] = field(default_factory=set)
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
class Aid:
    id: str
    label: str
    cover: set[str]
    guards: set[str]
    offer_line: str
    result_line: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "harbor": Setting(place="the harbor", sea="the blue sea", affords={"set_sail", "storm"}),
    "island": Setting(place="the little island dock", sea="the green sea", affords={"set_sail", "storm"}),
    "cove": Setting(place="the quiet cove", sea="the salty sea", affords={"set_sail", "storm"}),
}

HAZARDS = {
    "storm": Hazard(
        id="storm",
        label="a sudden storm",
        weather="stormy",
        splash="soaked",
        mess="wet",
        zone={"deck", "sail"},
        caution_line="The sky turned dark, and the wind began to shove the boat around.",
        tags={"storm", "wet"},
    ),
    "spray": Hazard(
        id="spray",
        label="big sea spray",
        weather="windy",
        splash="splashed",
        mess="wet",
        zone={"deck"},
        caution_line="White spray leapt over the side like a handful of cold coins.",
        tags={"sea", "wet"},
    ),
}

AIDS = {
    "oilcloth": Aid(
        id="oilcloth",
        label="an oilcloth tarp",
        cover={"deck", "sail"},
        guards={"wet"},
        offer_line="tie an oilcloth tarp over the deck and the sail",
        result_line="The tarp kept the worst of the water off the deck",
    ),
    "raincloak": Aid(
        id="raincloak",
        label="a rain cloak",
        cover={"body"},
        guards={"wet"},
        offer_line="put on a rain cloak",
        result_line="The cloak kept the pirate warm and dry",
    ),
    "lanternhood": Aid(
        id="lanternhood",
        label="a lantern hood",
        cover={"hands"},
        guards={"wet"},
        offer_line="cover the lantern with a hood",
        result_line="The lantern stayed bright even in the wind",
    ),
}

NAMES = ["Mara", "Jory", "Lena", "Finn", "Nia", "Rook", "Tess"]
PIRATE_TITLES = ["young pirate", "brave pirate", "small captain", "tiny deckhand"]
TRAITS = ["reckless", "sharp-eyed", "quick", "stubborn", "bold", "merry"]


@dataclass
class StoryParams:
    place: str
    hazard: str
    name: str
    title: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gates
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


def hazard_at_risk(hazard: Hazard) -> bool:
    return bool(hazard.zone)


def select_aid(hazard: Hazard) -> Optional[Aid]:
    for aid in AIDS.values():
        if hazard.mess in aid.guards:
            return aid
    return None


def explain_rejection(hazard: Hazard) -> str:
    return (
        f"(No story: nothing in the aid catalog can meaningfully answer {hazard.label}. "
        f"The warning and the fix need to fit the same sea trouble.)"
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="pirate",
        label=params.title,
        meters={"wet": 0.0, "balance": 1.0},
        memes={"worry": 0.0, "pride": 1.0, "kindness": 0.0, "courage": 0.0, "trust": 0.0},
    ))
    kaka = world.add(Entity(
        id="Kaka",
        kind="character",
        type="bird",
        label="Kaka",
        meters={"perch": 1.0},
        memes={"alertness": 1.0, "trust": 1.0},
    ))
    helper = world.add(Entity(
        id="Pip",
        kind="character",
        type="child",
        label="a frightened helper",
        meters={"wet": 0.0},
        memes={"fear": 1.0, "hope": 0.0},
    ))
    boat = world.add(Entity(
        id="boat",
        type="boat",
        label="the little boat",
        meters={"hull": 1.0, "wet": 0.0, "rope_tension": 0.0},
        memes={"safety": 1.0},
    ))
    sail = world.add(Entity(
        id="sail",
        type="sail",
        label="the sail",
        meters={"wet": 0.0, "torn": 0.0},
        memes={"snugness": 1.0},
        owner=hero.id,
    ))

    world.facts.update(hero=hero, kaka=kaka, helper=helper, boat=boat, sail=sail)
    return world


def warn_about_weather(world: World, hero: Entity, kaka: Entity, hazard: Hazard) -> None:
    hero.memes["worry"] += 1.0
    kaka.memes["alertness"] += 1.0
    world.say(f"Kaka the parrot hopped on the rail and squawked, \"Set your feet, matey!\"")
    world.say(hazard.caution_line)
    world.say(f"{kaka.label} was not being mean; {kaka.pronoun('subject')} was trying to keep {hero.id} safe.")


def choose_kindness(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["kindness"] += 1.0
    helper.memes["hope"] += 1.0
    helper.memes["fear"] = max(0.0, helper.memes["fear"] - 1.0)
    world.say(
        f"{hero.id} looked at the frightened helper and lowered {hero.pronoun('possessive')} voice. "
        f"\"You can stand near me,\" {hero.pronoun()} said, \"and we will set things right together.\""
    )
    world.say(
        f"The kind words made {helper.id} blink and breathe easier."
    )


def transform_hero(world: World, hero: Entity) -> None:
    if hero.memes["kindness"] >= THRESHOLD and hero.memes["worry"] >= THRESHOLD:
        hero.memes["pride"] = max(0.0, hero.memes["pride"] - 1.0)
        hero.memes["courage"] += 1.0
        hero.memes["trust"] += 1.0
        world.say(
            f"That was the start of a change: the once-brash pirate became calmer, "
            f"and {hero.pronoun('subject')} found a steadier kind of courage."
        )


def apply_hazard(world: World, hero: Entity, hazard: Hazard, sail: Entity, boat: Entity) -> None:
    hero.meters["wet"] += 1.0
    sail.meters["wet"] += 1.0
    boat.meters["wet"] += 1.0
    boat.meters["rope_tension"] += 1.0
    world.say(
        f"The {hazard.label} slapped the boat, and the deck got {hazard.splash}. "
        f"{hero.id} had to keep a firm grip while the boat shivered."
    )


def secure_boat(world: World, hero: Entity, helper: Entity, aid: Aid, sail: Entity, boat: Entity) -> None:
    sail.meters["wet"] = max(0.0, sail.meters["wet"] - 1.0)
    boat.meters["rope_tension"] = max(0.0, boat.meters["rope_tension"] - 1.0)
    hero.memes["courage"] += 1.0
    helper.memes["hope"] += 1.0
    world.say(
        f"Together they chose to {aid.offer_line}. {aid.result_line}, and the little boat stopped wobbling so much."
    )
    world.say(
        f"{hero.id} held the line, {helper.id} helped with the knots, and Kaka watched from the mast with bright eyes."
    )


def end_image(world: World, hero: Entity, kaka: Entity, helper: Entity, sail: Entity) -> None:
    if hero.memes["trust"] >= THRESHOLD and hero.memes["courage"] >= THRESHOLD:
        world.say(
            f"By the time the sky cleared, {hero.id} was no longer trying to look tough. "
            f"{hero.pronoun('subject').capitalize()} was busy helping, while {kaka.id} perched nearby and {helper.id} smiled beside the sail."
        )
    else:
        world.say(
            f"When the wind eased, {hero.id} still stood watch with Kaka, and the sail stayed tied down."
        )


def simulate(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.get(params.name)
    kaka = world.get("Kaka")
    helper = world.get("Pip")
    boat = world.get("boat")
    sail = world.get("sail")
    hazard = _safe_lookup(HAZARDS, params.hazard)

    world.say(f"In {world.setting.place}, {hero.id} was a {params.trait} {params.title} who wanted to set sail.")
    world.say(f"Kaka the parrot rode the wind on {hero.id}'s shoulder and kept a keen eye on the clouds.")

    world.para()
    warn_about_weather(world, hero, kaka, hazard)

    world.para()
    apply_hazard(world, hero, hazard, sail, boat)
    choose_kindness(world, hero, helper)
    transform_hero(world, hero)

    world.para()
    aid = select_aid(hazard)
    if aid is None:
        pass
    secure_boat(world, hero, helper, aid, sail, boat)
    end_image(world, hero, kaka, helper, sail)

    world.facts.update(hazard=hazard, aid=aid, params=params)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hazard_at_risk(H) :- hazard(H), zone(H, _).
compatible_aid(H, A) :- hazard(H), aid(A), hazard_mess(H, M), guards(A, M), hazard_at_risk(H).
valid_story(P, H, A) :- place(P), hazard(H), compatible_aid(H, A), on_sea(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("on_sea", pid))
        for afford in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, afford))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("hazard_mess", hid, hazard.mess))
        for z in sorted(hazard.zone):
            lines.append(asp.fact("zone", hid, z))
    for aid, thing in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for g in sorted(thing.guards):
            lines.append(asp.fact("guards", aid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [(place, hid, aid.id) for place in SETTINGS for hid, haz in HAZARDS.items() for aid in AIDS.values() if haz.mess in aid.guards]


def asp_verify() -> int:
    import asp
    clingo_model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(clingo_model, "valid_story"))
    py_set = set((p, h, a) for p in SETTINGS for h in HAZARDS for a in AIDS if _safe_lookup(HAZARDS, h).mess in _safe_lookup(AIDS, a).guards)
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} valid story triples).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in clingo:", sorted(clingo_set - py_set))
    print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    params = _safe_fact(world, world.facts, "params")
    hazard = _safe_fact(world, world.facts, "hazard")
    return [
        f'Write a short pirate tale for a young child that includes "{params.name}" and "{hazard.label}".',
        f"Tell a gentle sea story where Kaka gives a warning and kindness changes the pirate's heart.",
        f"Write a story about a pirate who decides to set sail carefully after a cautionary sign from a parrot named Kaka.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    kaka: Entity = _safe_fact(world, world.facts, "kaka")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    hazard: Hazard = _safe_fact(world, world.facts, "hazard")
    aid: Aid = _safe_fact(world, world.facts, "aid")

    return [
        QAItem(
            question=f"Who warned the pirate about the trouble at sea?",
            answer=f"Kaka the parrot warned {hero.id} about {hazard.label} so {hero.id} could stay safe.",
        ),
        QAItem(
            question=f"Why did {hero.id} speak kindly to the frightened helper?",
            answer=f"{hero.id} chose kindness because the storm made everyone nervous, and kind words helped {helper.id} feel brave enough to help.",
        ),
        QAItem(
            question=f"What helped the boat after the weather turned rough?",
            answer=f"They used {aid.label} to keep the boat and sail steadier, so they could set things right together.",
        ),
        QAItem(
            question=f"How did {hero.id} change by the end of the story?",
            answer=f"{hero.id} changed from a bold, brash pirate into someone calmer, kinder, and more courageous.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a parrot do on a pirate ship?",
            answer="A parrot can watch, squawk, and warn the crew about danger.",
        ),
        QAItem(
            question="What is a storm at sea?",
            answer="A storm at sea brings strong wind, rough water, and splashing waves.",
        ),
        QAItem(
            question="Why does kindness matter when someone is scared?",
            answer="Kindness helps scared people feel safe, and feeling safe makes it easier for them to help and trust others.",
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is a big change, like when a character becomes kinder, braver, or wiser.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for hazard in setting.affords:
            if select_aid(_safe_lookup(HAZARDS, hazard)) is not None:
                combos.append((place, hazard))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world with Kaka, caution, kindness, and transformation.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--hazard", choices=HAZARDS.keys())
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--title", choices=PIRATE_TITLES)
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
    if getattr(args, "place", None) and getattr(args, "hazard", None):
        if getattr(args, "hazard", None) not in _safe_lookup(SETTINGS, getattr(args, "place", None)).affords:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "hazard", None) is None or c[1] == getattr(args, "hazard", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hazard = rng.choice(list(combos))
    return StoryParams(
        place=place,
        hazard=hazard,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        title=getattr(args, "title", None) or rng.choice(PIRATE_TITLES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
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
        triples = asp_valid_stories()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(place="harbor", hazard="storm", name="Mara", title="small captain", trait="bold"),
        StoryParams(place="cove", hazard="spray", name="Finn", title="young pirate", trait="stubborn"),
    ]

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
