#!/usr/bin/env python3
"""
storyworlds/worlds/contain_grizzly_surprise_mystery_to_solve_superhero.py
=========================================================================

A small superhero story world with a surprise mystery to solve.

Seed premise:
- A young hero tries to contain a grizzly situation.
- A surprise reveals the real problem.
- The hero solves the mystery and keeps everyone safe.

This script models a tiny classical domain with physical meters and emotional
memes, plus an inline ASP twin for the reasonableness gate.
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
# Small world model
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
    protective: bool = False
    contains: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    region: object | None = None
    gear: object | None = None
    hero: object | None = None
    prize: object | None = None
    sidekick: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "danger": 0.0, "noise": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "curiosity": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
class Setting:
    place: str
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    hazard: str
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
    shields: set[str]
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.facts: dict = {}
        self.surprise: str = ""

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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "city": Setting(place="the city rooftop", affords={"contain", "mystery"}),
    "museum": Setting(place="the museum hall", affords={"contain", "mystery"}),
    "harbor": Setting(place="the harbor", affords={"contain", "mystery"}),
}

CHALLENGES = {
    "contain": Challenge(
        id="contain",
        verb="contain the danger",
        gerund="containing the danger",
        rush="rush to hold it back",
        mess="rumble",
        hazard="the grizzly surprise",
        zone={"torso", "arms"},
        keyword="contain",
        tags={"contain", "hero"},
    ),
    "grizzly": Challenge(
        id="grizzly",
        verb="face the grizzly mystery",
        gerund="facing the grizzly mystery",
        rush="dash toward the growling shape",
        mess="rumble",
        hazard="the grizzly surprise",
        zone={"arms", "legs"},
        keyword="grizzly",
        tags={"grizzly", "mystery"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", region="torso"),
    "boots": Prize(label="boots", phrase="shiny rescue boots", region="feet", plural=True),
    "mask": Prize(label="mask", phrase="a silver mask", region="face"),
}

GEAR = [
    Gear(
        id="shield",
        label="a shield belt",
        covers={"torso", "arms"},
        shields={"rumble"},
        prep="put on the shield belt",
        tail="fastened the shield belt",
    ),
    Gear(
        id="gloves",
        label="power gloves",
        covers={"arms"},
        shields={"rumble"},
        prep="wear power gloves first",
        tail="pulled on the power gloves",
        plural=True,
    ),
    Gear(
        id="visor",
        label="a clear visor",
        covers={"face"},
        shields={"rumble"},
        prep="slip on a clear visor",
        tail="slipped on the clear visor",
    ),
]

HERO_NAMES = ["Nova", "Blaze", "Milo", "Zara", "Iris", "Theo"]
SIDEKICK_NAMES = ["Pip", "Bea", "Jax", "Tess"]
TRAITS = ["brave", "quick", "curious", "kind", "smart"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    name: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
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


def reasonableness_gate(challenge: Challenge, prize: Prize) -> bool:
    return prize.region in challenge.zone


def select_gear(challenge: Challenge, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and challenge.mess in gear.shields:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for cid in s.affords:
            ch = _safe_lookup(CHALLENGES, cid)
            for pid, pr in PRIZES.items():
                if reasonableness_gate(ch, pr) and select_gear(ch, pr):
                    out.append((place, cid, pid))
    return out


def hero_intro(hero: Entity) -> str:
    return f"{hero.id} was a {hero.memes.get('trait', 'brave')} superhero who listened for trouble."


def setting_line(world: World, challenge: Challenge) -> str:
    return f"{world.setting.place.capitalize()} was busy and bright, but {challenge.hazard} was hiding nearby."


def run_prediction(world: World, hero: Entity, challenge: Challenge, prize_id: str) -> dict:
    prize = world.get(prize_id)
    if challenge.mess and prize.region in challenge.zone:
        return {"soiled": True, "fear": 1.0}
    return {"soiled": False, "fear": 0.0}


def do_challenge(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.meters["danger"] += 1
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} wanted to {challenge.verb}, and {hero.pronoun('possessive')} heart thumped with curiosity.")


def warn(world: World, hero: Entity, sidekick: Entity, challenge: Challenge, prize: Entity) -> bool:
    pred = run_prediction(world, hero, challenge, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = challenge.hazard
    world.say(
        f'"If you go now, your {prize.label} could get caught in the grizzly mess," '
        f"{sidekick.id} warned. "
        f'"We should solve the mystery first."'
    )
    return True


def surprise_reveal(world: World, hero: Entity, sidekick: Entity, challenge: Challenge) -> None:
    world.surprise = "A toy bear had rolled into a vent and jammed the noise machine."
    world.say(
        f"Then came a surprise: a tiny toy bear had rolled into a vent and jammed the noise machine. "
        f"That was the real mystery to solve."
    )
    hero.memes["fear"] += 1


def solve_mystery(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"{hero.id} and {sidekick.id} followed the sound, opened the vent, and gently lifted out the toy bear."
    )
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    sidekick.memes["joy"] += 1


def offer_gear(world: World, hero: Entity, sidekick: Entity, challenge: Challenge, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(challenge, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        phrase=gear_def.label,
        protective=True,
        owner=hero.id,
    ))
    gear.worn_by = hero.id
    world.say(
        f"{sidekick.id} smiled and said, 'How about we {gear_def.prep} and then try again?'"
    )
    return gear


def accept(world: World, hero: Entity, sidekick: Entity, challenge: Challenge, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    world.say(
        f"{hero.id} nodded, and together they {gear_def.tail}. "
        f"After that, {hero.id} could {challenge.gerund}, and {prize.label} stayed safe."
    )


def tell(setting: Setting, challenge: Challenge, prize_cfg: Prize, hero_name: str, sidekick_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name in {"Theo", "Milo", "Blaze", "Jax"} else "girl"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="boy" if sidekick_name in {"Jax"} else "girl"))
    prize = world.add(Entity(id="prize", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, region=prize_cfg.region, plural=prize_cfg.plural))
    hero.memes["trait"] = trait

    world.say(f"{hero.id} was a {trait} superhero, and {sidekick.id} was {hero.id}'s loyal sidekick.")
    world.say(f"{hero.id} loved {challenge.gerund}, especially when the day felt big enough for a mission.")
    world.say(f"One day, {hero.id} wore {prize.phrase} and went to {world.setting.place}.")

    world.para()
    world.say(setting_line(world, challenge))
    do_challenge(world, hero, challenge)
    warn(world, hero, sidekick, challenge, prize)
    surprise_reveal(world, hero, sidekick, challenge)
    solve_mystery(world, hero, sidekick)

    world.para()
    gear_def = offer_gear(world, hero, sidekick, challenge, prize)
    if gear_def:
        accept(world, hero, sidekick, challenge, prize, gear_def)

    world.facts.update(hero=hero, sidekick=sidekick, prize=prize, challenge=challenge, gear=gear_def, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a superhero story for a young child about "{ch.keyword}" and a surprise mystery to solve.',
        f"Tell a short story where {hero.id} must contain the grizzly mess while keeping {prize.phrase} safe.",
        f"Write a brave and gentle adventure in which a sidekick helps solve a mystery and then the hero can {ch.verb}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    prize = _safe_fact(world, f, "prize")
    ch = _safe_fact(world, f, "challenge")
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, and {sidekick.id} helped {hero.id} through the mystery.",
        ),
        QAItem(
            question=f"What surprise did {the_hero(hero)} find in the story?",
            answer="They found that a toy bear had jammed the noise machine, which was the real mystery to solve.",
        ),
        QAItem(
            question=f"What did {hero.id} need to keep safe while solving the problem?",
            answer=f"{hero.id} needed to keep {f['prize'].phrase} safe while dealing with the grizzly mess.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did the gear help {hero.id} after the mystery was solved?",
            answer=f"The gear helped because {hero.id} could {ch.gerund} without ruining {prize.label}.",
        ))
    return qa


def the_hero(hero: Entity) -> str:
    return hero.id


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a superhero?",
        answer="A superhero is a brave helper who uses special skills or gear to keep people safe.",
    ),
    QAItem(
        question="What does it mean to solve a mystery?",
        answer="To solve a mystery means to figure out what caused the strange problem.",
    ),
    QAItem(
        question="What does contain mean?",
        answer="To contain something means to keep it under control so it does not spread or cause more trouble.",
    ),
    QAItem(
        question="What is a grizzly?",
        answer="A grizzly is a large kind of bear, and people can also use the word to mean something rough or scary.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(C,P) :- zone(C,R), prize_region(P,R).
gear_fixes(G,C,P) :- gear(G), prize_at_risk(C,P), covers(G,R), prize_region(P,R), shields(G,M), challenge_mess(C,M).
valid(Place,C,P) :- affords(Place,C), prize_at_risk(C,P), gear_fixes(_,C,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", pid, c))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("challenge_mess", cid, c.mess))
        for r in sorted(c.zone):
            lines.append(asp.fact("zone", cid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.shields):
            lines.append(asp.fact("shields", g.id, m))
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
    print("MISMATCH between clingo and python:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with a contain/grizzly mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if getattr(args, "challenge", None) and getattr(args, "prize", None):
        ch = _safe_lookup(CHALLENGES, getattr(args, "challenge", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not reasonableness_gate(ch, pr) or not select_gear(ch, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, prize=prize, name=name, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(CHALLENGES, params.challenge), _safe_lookup(PRIZES, params.prize), params.name, params.sidekick, params.trait)
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


CURATED = [
    StoryParams(place="city", challenge="contain", prize="cape", name="Nova", sidekick="Pip", trait="brave"),
    StoryParams(place="museum", challenge="grizzly", prize="boots", name="Zara", sidekick="Bea", trait="curious"),
    StoryParams(place="harbor", challenge="contain", prize="mask", name="Theo", sidekick="Jax", trait="smart"),
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
        triples = asp_valid_combos()
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
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
            header = f"### {p.name}: {p.challenge} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
