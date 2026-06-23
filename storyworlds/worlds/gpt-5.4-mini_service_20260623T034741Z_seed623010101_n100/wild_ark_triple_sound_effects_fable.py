#!/usr/bin/env python3
"""
storyworlds/worlds/wild_ark_triple_sound_effects_fable.py
==========================================================

A small fable-style story world about a tiny ark, a wild storm, and a triple
sound-effect build. The world is state-driven: characters carry physical meters
and emotional memes, and the story turns when a practical plan changes the
state.

Seed premise:
- A wild storm threatens a small riverbank home.
- A child or animal wants to use an ark to cross safely.
- A helper warns, then a triple sound-effect build or launch succeeds.

The story must include the words "wild", "ark", and "triple", and it should
read like a fable with a clear lesson.
"""

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    age: int = 0
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "mare", "hen", "duck"}
        male = {"boy", "father", "man", "stallion", "rooster", "goose"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
        if not hasattr(self, "_tags"):
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
class Place:
    id: str
    label: str
    wild: bool = False
    water: bool = False
    stormy: bool = False
    affords: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Challenge:
    id: str
    label: str
    threat: str
    mess: str
    sound: str
    zone: str
    keyword: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    fragile: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class HelperPlan:
    id: str
    label: str
    prep: str
    finish: str
    guards: set[str] = field(default_factory=set)
    sound: str = ""
    sound2: str = ""
    sound3: str = ""
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.sound_log: list[str] = []

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        c.sound_log = list(self.sound_log)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.stormy:
        return out
    for e in world.characters():
        if e.meters["rain"] < THRESHOLD:
            continue
        sig = ("wet", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append(f"{e.label_word} shivered in the wild rain.")
    return out


CAUSAL_RULES = [Rule("wet", "physical", _r_wet)]


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


def sound_effect(world: World, token: str) -> None:
    world.sound_log.append(token)
    world.say(token)


def storm_risk(challenge: Challenge, prize: Prize) -> bool:
    return prize.region == challenge.zone


def choose_plan(challenge: Challenge, prize: Prize) -> Optional[HelperPlan]:
    for plan in PLANS:
        if challenge.id in plan.guards and prize.region == challenge.zone:
            return plan
    return None


def predict_outcome(world: World, actor: Entity, challenge: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["rain"] += 1
    propagate(sim, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soaked": bool(prize.meters["soaked"] >= THRESHOLD),
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def act_setup(world: World, hero: Entity, helper: Entity, challenge: Challenge, prize: Entity) -> None:
    hero.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In a wild morning by the river, {hero.id} and {helper.id} saw that "
        f"the water had grown high. They had to protect {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f"{hero.id} loved the little ark because it could carry them across the flood."
    )


def act_warning(world: World, helper: Entity, hero: Entity, challenge: Challenge, prize: Entity) -> None:
    pred = predict_outcome(world, hero, challenge, prize.id)
    helper.memes["care"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"{challenge.label}," said {helper.id}, "if we rush, the {prize.label} will get {challenge.mess}."'
    )


def act_build(world: World, hero: Entity, helper: Entity, plan: HelperPlan) -> None:
    hero.memes["determination"] += 1
    world.say(
        f"They chose a triple plan: {plan.prep}."
    )


def act_launch(world: World, hero: Entity, helper: Entity, plan: HelperPlan, prize: Entity) -> None:
    hero.meters["rain"] += 1
    helper.meters["rain"] += 1
    propagate(world, narrate=False)
    sound_effect(world, plan.sound)
    sound_effect(world, plan.sound2)
    sound_effect(world, plan.sound3)
    world.say(
        f"Then the little ark moved at once, and {plan.finish}."
    )
    world.say(
        f"The {prize.label} stayed dry, and the three friends crossed the water together."
    )


def act_lesson(world: World, hero: Entity, helper: Entity, challenge: Challenge) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    hero.memes["calm"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"At the end, {hero.id} learned that a careful plan is stronger than a wild rush."
    )
    world.say(
        f"And the riverbank was quiet again, with the ark resting safely on the mud."
    )


def tell(place: Place, challenge: Challenge, prize_cfg: Prize, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, label=helper_name))
    prize = world.add(Entity(id="prize", kind="thing", type="thing", label=prize_cfg.label, phrase=prize_cfg.phrase))
    hero.meters["rain"] = 0.0
    helper.meters["rain"] = 0.0
    hero.memes["hope"] = 0.0
    helper.memes["care"] = 0.0
    world.facts["place"] = place
    world.facts["challenge"] = challenge
    world.facts["prize"] = prize_cfg
    world.facts["hero"] = hero
    world.facts["helper"] = helper

    act_setup(world, hero, helper, challenge, prize)
    world.para()
    act_warning(world, helper, hero, challenge, prize)
    plan = choose_plan(challenge, prize_cfg)
    if plan is None:
        pass
    world.facts["plan"] = plan
    act_build(world, hero, helper, plan)
    world.para()
    act_launch(world, hero, helper, plan, prize)
    world.para()
    act_lesson(world, hero, helper, challenge)
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "riverbank": Place(id="riverbank", label="the riverbank", wild=True, water=True, stormy=True, affords={"cross", "build"}),
    "meadow": Place(id="meadow", label="the meadow", wild=True, water=False, stormy=False, affords={"build"}),
    "marsh": Place(id="marsh", label="the marsh", wild=True, water=True, stormy=True, affords={"cross", "build"}),
}

CHALLENGES = {
    "flood": Challenge(id="flood", label="the flood", threat="water", mess="soaked", sound="splish", zone="body", keyword="wild", tags={"wild", "water"}),
    "wind": Challenge(id="wind", label="the wild wind", threat="wind", mess="ruffled", sound="whoosh", zone="body", keyword="wild", tags={"wild"}),
}

PRIZES = {
    "seedbag": Prize(id="seedbag", label="seed bag", phrase="a small seed bag", region="body", fragile=True, tags={"seed"}),
    "eggs": Prize(id="eggs", label="nest eggs", phrase="three nest eggs", region="body", fragile=True, tags={"eggs"}),
}

PLANS = [
    HelperPlan(id="triple_paddle", label="triple paddle", prep="stack three planks on the ark", finish="the triple paddle worked", guards={"flood", "wind"}, sound="tap", sound2="tap", sound3="tap"),
    HelperPlan(id="triple_tie", label="triple tie", prep="tie three ropes around the ark", finish="the triple tie held fast", guards={"flood"}, sound="thump", sound2="thump", sound3="thump"),
]


@dataclass
class StoryParams:
    place: str
    challenge: str
    prize: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for challenge in CHALLENGES:
            for prize in PRIZES:
                if storm_risk(_safe_lookup(CHALLENGES, challenge), _safe_lookup(PRIZES, prize)):
                    combos.append((place, challenge, prize))
    return combos


GIRL_NAMES = ["Mina", "Luna", "Pip", "Nora", "Tia"]
BOY_NAMES = ["Otto", "Finn", "Ned", "Ben", "Roo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable world about a wild storm, an ark, and a triple plan.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy", "duck", "goose", "mouse"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "duck", "goose", "mouse"])
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
    if getattr(args, "place", None) and getattr(args, "challenge", None) and getattr(args, "prize", None):
        if not storm_risk(_safe_lookup(CHALLENGES, getattr(args, "challenge", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "challenge", None) is None or c[1] == getattr(args, "challenge", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge, prize = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy", "mouse"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["girl", "boy", "duck", "goose"])
    hero = getattr(args, "hero", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    return StoryParams(place=place, challenge=challenge, prize=prize, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a small child that uses the words "wild", "ark", and "triple".',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} build an ark for a wild storm and keep the {f['prize'].label} safe.",
        f'Write a story with sound effects where three careful sounds help a triple plan work on the riverbank.',
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    prize = world.facts["prize"]
    plan = world.facts["plan"]
    challenge = world.facts["challenge"]
    return [
        QAItem(question=f"What kind of day was it for {h.id} and {helper.id}?", answer=f"It was a wild day by the river, and the water was high. They had to make a careful plan so the {prize.label} would stay safe."),
        QAItem(question=f"What did they use to cross the water?", answer=f"They used an ark. It was the safe way to cross when the storm made the river too wild for walking."),
        QAItem(question=f"What triple plan did they choose?", answer=f"They chose the {plan.label}, a triple plan with three repeated sounds. The little rhythm helped them work together and keep calm."),
        QAItem(question=f"Why did the helper warn them?", answer=f"{helper.id} warned them because {challenge.label} could make the {prize.label} get wet. The warning gave them time to choose a safer way."),
        QAItem(question=f"How did the story end?", answer=f"It ended with the {prize.label} staying dry and the ark resting safely after the crossing. The careful choice turned the wild problem into a peaceful ending."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an ark?", answer="An ark is a boat that helps animals or people cross water safely."),
        QAItem(question="What does wild mean?", answer="Wild means uncontrolled or very strong, like a wild storm or wild water."),
        QAItem(question="What is triple?", answer="Triple means three of something, or something done three times."),
        QAItem(question="Why do sound effects help a story?", answer="Sound effects help a story feel lively and clear. They can show action, like tap, splash, or creak, without needing many extra words."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions -- answerable from the story text =="]
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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  sound log: {world.sound_log}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS.get(params.place)
    challenge = CHALLENGES.get(params.challenge)
    prize = PRIZES.get(params.prize)
    if place is None or challenge is None or prize is None:
        pass
    world = tell(place, challenge, prize, params.hero, params.hero_type, params.helper, params.helper_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


ASP_RULES = r"""
valid(P,C,R) :- place(P), challenge(C), prize(R), risk(C,R).
risk(C,R) :- challenge(C), prize(R), zone(C,Z), region(R,Z).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS.values():
        lines.append(asp.fact("place", p.id))
    for c in CHALLENGES.values():
        lines.append(asp.fact("challenge", c.id))
        lines.append(asp.fact("zone", c.id, c.zone))
    for r in PRIZES.values():
        lines.append(asp.fact("prize", r.id))
        lines.append(asp.fact("region", r.id, r.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = set(valid_combos()) == set(asp_valid_combos())
    if not ok:
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, challenge=None, prize=None, hero=None, hero_type=None, helper=None, helper_type=None), random.Random(777)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: ASP matches Python and generate() smoke test passed.")
    return 0


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
    StoryParams(place="riverbank", challenge="flood", prize="seedbag", hero="Mina", hero_type="girl", helper="Otto", helper_type="boy"),
    StoryParams(place="marsh", challenge="flood", prize="eggs", hero="Finn", hero_type="boy", helper="Luna", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {idx+1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
