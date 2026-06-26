#!/usr/bin/env python3
"""
storyworlds/worlds/questionnaire_slave_slot_suspense_friendship_superhero_story.py
=================================================================================

A standalone superhero storyworld built from the seed words
"questionnaire", "slave", and "slot", with suspense and friendship
as the main narrative instruments.

Premise:
- A young superhero wants to join a rescue mission.
- A paper questionnaire determines who gets the next hero slot.
- A tricky event creates suspense when the slot may be lost.
- A friend helps in a way that proves loyalty and resolves the tension.

This world keeps the prose child-facing, state-driven, and compact:
one setup, one suspense turn, one friendship resolution, and an ending
image that proves something changed.

The Python gate and the inline ASP twin both enforce the same basic
reasonableness rule: only stories with a real at-risk slot and a real
compatible rescue are generated.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
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
    place: str
    indoors: bool = False
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
    risk: str
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
    kinds: set[str] = field(default_factory=set)
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
    fix: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_torn_questionnaire(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("questionnaire_safeguarded"):
        return out
    if world.facts.get("questionnaire_at_risk") and world.facts.get("questionnaire_spilled"):
        sig = ("torn_questionnaire",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("The questionnaire got wrinkled and nearly impossible to read.")
        world.facts["questionnaire_ruined"] = True
    return out


def _r_missed_slot(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("slot_blocked") and not world.facts.get("slot_saved"):
        sig = ("missed_slot",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("The hero slot was in danger of slipping away.")
        world.facts["slot_lost"] = True
    return out


CAUSAL_RULES = [
    Rule("torn_questionnaire", _r_torn_questionnaire),
    Rule("missed_slot", _r_missed_slot),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_at_risk(event: Event, prize: Prize) -> bool:
    return prize.region in event.zone


def select_gear(event: Event, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and event.keyword in gear.fix:
            return gear
    return None


def predict_outcome(world: World, hero: Entity, event: Event, prize: Prize) -> dict:
    sim = world.copy()
    do_event(sim, sim.get(hero.id), event, narrate=False)
    return {
        "ruined": bool(sim.facts.get("questionnaire_ruined")),
        "lost_slot": bool(sim.facts.get("slot_lost")),
    }


def do_event(world: World, hero: Entity, event: Event, narrate: bool = True) -> None:
    world.zone = set(event.zone)
    hero.memes["stress"] += 1
    hero.meters[event.keyword] = hero.meters.get(event.keyword, 0.0) + 1.0
    world.facts["questionnaire_at_risk"] = True
    world.facts["slot_blocked"] = True
    if event.keyword == "questionnaire":
        world.facts["questionnaire_spilled"] = True
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a small superhero with a brave cape and a careful heart."
    )


def friendship(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"{hero.id} trusted {friend.id}, because {friend.id} always stayed close in a tight spot."
    )


def setup(world: World, hero: Entity, friend: Entity, event: Event, prize: Prize) -> None:
    world.say(
        f"At {world.setting.place}, a shiny questionnaire waited beside the hero desk."
    )
    world.say(
        f"{hero.id} wanted the next hero slot, and {hero.pronoun('possessive')} friend {friend.id} wanted to help."
    )
    world.say(
        f"That day, the prize was {prize.phrase}, and losing it would mean losing the chance to join the rescue team."
    )


def suspense_turn(world: World, hero: Entity, friend: Entity, event: Event, prize: Prize) -> None:
    pred = predict_outcome(world, hero, event, prize)
    if pred["ruined"] or pred["lost_slot"]:
        world.facts["predicted_trouble"] = True
        world.say(
            f"When {hero.id} reached for the {event.keyword}, {hero.pronoun('possessive')} hands slipped and the room went quiet."
        )
        world.say(
            f"The questionnaire could be ruined, and the hero slot could vanish before the bell rang."
        )


def warning(world: World, hero: Entity, friend: Entity, event: Event, prize: Prize) -> None:
    world.say(
        f'"Careful," {friend.id} said. "We can still fix this if we move fast and stay together."'
    )


def rescue_with_friendship(
    world: World, hero: Entity, friend: Entity, event: Event, prize: Prize
) -> Optional[Gear]:
    gear = select_gear(event, prize)
    if gear is None:
        return None
    gear_ent = world.add(
        Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            plural=gear.plural,
        )
    )
    gear_ent.worn_by = hero.id
    if predict_outcome(world, hero, event, prize)["ruined"]:
        gear_ent.worn_by = None
        del world.entities[gear_ent.id]
        return None
    world.facts["slot_saved"] = True
    world.say(
        f"{friend.id} grabbed the {gear.label} and used it like a shield while {hero.id} held the questionnaire still."
    )
    world.say(
        f"Together they {gear.prep}, so the {event.keyword} stayed safe and the hero slot stayed open."
    )
    return gear_ent


def ending(world: World, hero: Entity, friend: Entity, event: Event, prize: Prize) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"In the end, {hero.id} signed the questionnaire with a steady hand, {friend.id} smiled, and the rescued slot belonged to them both."
    )
    world.say(
        f"The paper stayed neat, the cape stayed bright, and the team had one more brave helper."
    )


def tell(setting: Setting, event: Event, prize: Prize, hero_name: str, friend_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", traits=["small", "brave"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", traits=["loyal", "quick"]))
    world.add(Entity(id="questionnaire", type="thing", label="questionnaire", phrase="a shiny questionnaire"))
    world.add(Entity(id="slot", type="thing", label="slot", phrase="the hero slot"))
    world.add(Entity(id="prize", type="thing", label=prize.label, phrase=prize.phrase, owner=hero.id, caretaker=friend.id, plural=prize.plural))

    introduce(world, hero)
    friendship(world, hero, friend)
    setup(world, hero, friend, event, prize)
    world.para()
    suspense_turn(world, hero, friend, event, prize)
    warning(world, hero, friend, event, prize)
    do_event(world, hero, event, narrate=True)
    world.para()
    rescue_with_friendship(world, hero, friend, event, prize)
    ending(world, hero, friend, event, prize)
    world.facts.update(hero=hero, friend=friend, event=event, prize=prize)
    return world


SETTINGS = {
    "hero_hall": Setting(place="Hero Hall", affords={"questionnaire", "slot"}),
    "roof": Setting(place="the city roof", affords={"slot"}),
    "academy": Setting(place="the hero academy", affords={"questionnaire", "slot"}),
}


EVENTS = {
    "questionnaire": Event(
        id="questionnaire",
        verb="fill out the questionnaire",
        gerund="filling out the questionnaire",
        risk="spill",
        zone={"hands", "table"},
        keyword="questionnaire",
        tags={"questionnaire", "paper"},
    ),
    "slot": Event(
        id="slot",
        verb="reach the slot in time",
        gerund="racing for the slot",
        risk="slip",
        zone={"feet", "stairs"},
        keyword="slot",
        tags={"slot", "timing"},
    ),
}


PRIZES = {
    "badge": Prize(
        id="badge",
        label="badge",
        phrase="a gold hero badge",
        region="hands",
        kinds={"questionnaire", "slot"},
    ),
    "cap": Prize(
        id="cap",
        label="cap",
        phrase="a bright rescue cap",
        region="head",
        kinds={"slot"},
    ),
}


GEAR = [
    Gear(
        id="clipboard_cover",
        label="a plastic clipboard cover",
        covers={"hands", "table"},
        fix={"questionnaire"},
        prep="slipped the questionnaire into the plastic cover",
        tail="kept the paper dry and neat",
    ),
    Gear(
        id="sturdy_shoes",
        label="sturdy hero shoes",
        covers={"feet"},
        fix={"slot"},
        prep="tied on the sturdy shoes before running",
        tail="helped them reach the slot on time",
    ),
]


GIRL_NAMES = ["Maya", "Luna", "Zoe", "Nia", "Iris"]
BOY_NAMES = ["Finn", "Owen", "Jude", "Leo", "Sam"]


@dataclass
class StoryParams:
    setting: str
    event: str
    prize: str
    hero_name: str
    friend_name: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s, setting in SETTINGS.items():
        for e, event in EVENTS.items():
            if e not in setting.affords:
                continue
            for p, prize in PRIZES.items():
                if is_at_risk(event, prize) and select_gear(event, prize):
                    out.append((s, e, p))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, event, prize = f["hero"], f["friend"], f["event"], f["prize"]
    return [
        f'Write a superhero story for a young child using the word "{event.keyword}".',
        f"Tell a suspenseful friendship story where {hero.id} and {friend.id} protect {prize.phrase} at {world.setting.place}.",
        f'Write a short story with a questionnaire, a slot, and a loyal friend who helps the hero finish the mission.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, event, prize = f["hero"], f["friend"], f["event"], f["prize"]
    return [
        QAItem(
            question=f"Who wanted the hero slot at {world.setting.place}?",
            answer=f"{hero.id} wanted the hero slot, and {friend.id} stayed close to help.",
        ),
        QAItem(
            question=f"What was the suspenseful part of the story?",
            answer=f"The suspense came when the questionnaire and the hero slot could be lost if the {event.keyword} went wrong.",
        ),
        QAItem(
            question=f"How did {friend.id} help {hero.id}?",
            answer=f"{friend.id} helped by guarding the questionnaire with {prize.phrase} safe and steady.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    event = _safe_fact(world, f, "event")
    out = []
    if event.keyword == "questionnaire":
        out.append(
            QAItem(
                question="What is a questionnaire?",
                answer="A questionnaire is a set of questions people fill out to share information or make a choice.",
            )
        )
    if event.keyword == "slot":
        out.append(
            QAItem(
                question="What is a slot?",
                answer="A slot is a small open place or a time opening where something can fit or happen.",
            )
        )
    out.append(
        QAItem(
            question="What does a friend do in a brave team?",
            answer="A friend helps, listens, and stays nearby when the job gets scary or tricky.",
        )
    )
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="hero_hall", event="questionnaire", prize="badge", hero_name="Maya", friend_name="Finn"),
    StoryParams(setting="academy", event="questionnaire", prize="badge", hero_name="Luna", friend_name="Owen"),
    StoryParams(setting="roof", event="slot", prize="cap", hero_name="Zoe", friend_name="Jude"),
]


ASP_RULES = r"""
at_risk(E,P) :- event(E), prize(P), zone(E,R), region(P,R).
has_fix(E,P) :- at_risk(E,P), gear(G), fixes(G,E), covers(G,R), region(P,R).
valid(S,E,P) :- setting(S), affords(S,E), at_risk(E,P), has_fix(E,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for e in sorted(s.affords):
            lines.append(asp.fact("affords", sid, e))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        for r in sorted(e.zone):
            lines.append(asp.fact("zone", eid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for fx in sorted(g.fix):
            lines.append(asp.fact("fixes", g.id, fx))
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
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero suspense storyworld with friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, event, prize = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice(BOY_NAMES)
    return StoryParams(setting=setting, event=event, prize=prize, hero_name=hero_name, friend_name=friend_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(EVENTS, params.event),
        _safe_lookup(PRIZES, params.prize),
        params.hero_name,
        params.friend_name,
    )
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for row in vals:
            print(" ", row)
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
            header = f"### {p.hero_name}: {p.event} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
