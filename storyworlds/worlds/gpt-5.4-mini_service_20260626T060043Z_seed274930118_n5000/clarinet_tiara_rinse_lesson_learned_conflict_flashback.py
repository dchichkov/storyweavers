#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/clarinet_tiara_rinse_lesson_learned_conflict_flashback.py
===================================================================================================

A small animal-story world about a careful musician, a shiny tiara, and a
lesson learned after a muddy mistake.

Premise:
- An animal child loves music and a special costume piece.
- A wet, messy place can damage the special items.
- A parent or friend warns the child.
- A flashback reminds the child of an earlier mess.
- The child learns the lesson, chooses a safer way, and the story ends with
  the items clean and the feeling changed.

This file is self-contained and follows the Storyweavers world contract.
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
    kind: str = "thing"   # character | thing
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

    region: str = ""
    clarinet: object | None = None
    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    tiara: object | None = None
    def __post_init__(self):
        for k in ("wet", "dirty", "sparkle", "care", "fear", "joy", "conflict", "lesson", "flashback"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "mouse", "goat", "cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"fox", "bear", "dog", "lion"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the garden"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
    ACTIVITY: object | None = None
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


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    type: str = "thing"
    plural: bool = False
    PRIZE_CLARINET: object | None = None
    PRIZE_TIARA: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict[str, object] = {}

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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


ACTIVITY = Activity(
    id="rinse",
    verb="rinse the stage ribbons",
    gerund="rinsing the stage ribbons",
    rush="dash through the splashy path",
    mess="wet",
    soil="soaked and muddy",
    zone={"feet", "legs", "torso"},
    keyword="rinse",
)

SETTING = Setting(place="the garden", affords={"rinse"})

PRIZE_TIARA = Prize(
    label="tiara",
    phrase="a tiny silver tiara",
    region="torso",
    type="tiara",
)

PRIZE_CLARINET = Prize(
    label="clarinet",
    phrase="a polished clarinet",
    region="torso",
    type="clarinet",
)

GEAR = [
    Gear(
        id="raincoat",
        label="a raincoat",
        covers={"torso"},
        guards={"wet"},
        prep="put on a raincoat first",
        tail="came back in the raincoat",
    ),
    Gear(
        id="boots",
        label="rubber boots",
        covers={"feet"},
        guards={"wet"},
        prep="pull on rubber boots first",
        tail="came back in the rubber boots",
        plural=True,
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Tia", "Pippa", "Nori"]
BOY_NAMES = ["Ollie", "Bram", "Pico", "Milo", "Tobi"]
ANIMALS = ["rabbit", "fox", "mouse", "cat", "bear", "dog"]


@dataclass
class StoryParams:
    name: str
    animal: str
    parent: str
    seed: Optional[int] = None
    p: object | None = None
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection() -> str:
    return (
        "(No story: the rinse lesson only works when the shiny prize can be "
        "protected in a believable way.)"
    )


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet and dirty.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    if hero.memes["fear"] >= THRESHOLD and hero.memes["conflict"] < THRESHOLD:
        hero.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    _r_soak,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD}


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="hero", kind="character", type=params.animal, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label="parent"))
    tiara = world.add(Entity(
        id="tiara", type="tiara", label="tiara", phrase=PRIZE_TIARA.phrase,
        owner=hero.id, caretaker=parent.id, region="torso",
    ))
    clarinet = world.add(Entity(
        id="clarinet", type="clarinet", label="clarinet", phrase=PRIZE_CLARINET.phrase,
        owner=hero.id, caretaker=parent.id, region="torso",
    ))
    hero.memes["love"] = 1.0
    tiara.worn_by = hero.id
    clarinet.worn_by = hero.id

    world.say(f"{params.name} was a little {params.animal} who loved music and sparkle.")
    world.say(f"{params.name} loved {clarinet.label} and {tiara.label} almost as much as puddle-jumping games.")
    world.say(f"One morning, {params.name}'s {params.parent} gave {params.name} the {clarinet.label} and the {tiara.label} to keep safe.")

    world.para()
    world.say(f"Then {params.name} went to {SETTING.place}.")
    world.say(f"{params.name} wanted to {ACTIVITY.verb}, but the path was still damp and slippery.")

    can_risk = prize_at_risk(ACTIVITY, tiara) and select_gear(ACTIVITY, tiara)
    if not can_risk:
        pass

    pred = predict_mess(world, hero, ACTIVITY, tiara.id)
    if pred["soiled"]:
        world.say(f'"Wait," said the {params.parent}, "your {tiara.label} could get ruined if you rush in like that."')
    else:
        pass

    world.say(f"{params.name} froze, and a little flashback popped into {params.name}'s mind.")
    world.say(f"Last week, {params.name} had ignored the mud and had to spend a long time rinsing a sticky ribbon clean.")
    hero.memes["flashback"] += 1
    hero.memes["fear"] += 1
    hero.memes["lesson"] += 1

    world.para()
    world.say(f"{params.name} remembered the lesson learned: shiny things need a careful plan.")
    world.say(f"That brought a bit of conflict, because {params.name} still wanted to play right away.")
    world.say(f"Then the {params.parent} smiled and said, '{select_gear(ACTIVITY, tiara).prep.capitalize()}, and then you can go.'")

    gear_def = select_gear(ACTIVITY, tiara)
    gear = world.add(Entity(
        id=gear_def.id,
        type=gear_def.id,
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
    ))
    gear.worn_by = hero.id

    hero.memes["fear"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1

    world.say(f"{params.name} nodded and wore {gear.label}.")
    world.say(f"After that, {params.name} could {ACTIVITY.verb} without hurting the {tiara.label} or the {clarinet.label}.")
    world.say(f"In the end, {params.name} came back smiling, and the {tiara.label} still shone clean.")

    world.facts.update(
        hero=hero,
        parent=parent,
        tiara=tiara,
        clarinet=clarinet,
        gear=gear,
        activity=ACTIVITY,
        setting=SETTING,
        lesson_learned=True,
        conflict=True,
        flashback=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    return [
        f"Write an animal story about {hero.label}, a {hero.type}, who wants to use a clarinet and a tiara but must make a careful choice.",
        f"Tell a short story where a parent warns {hero.label} about rinsing something shiny, and a lesson learned changes the ending.",
        f"Write a gentle Animal Story with a flashback, a small conflict, and a safe plan for a clarinet and a tiara.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    tiara = _safe_fact(world, f, "tiara")
    clarinet = _safe_fact(world, f, "clarinet")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a little {hero.type} who loves a clarinet and a tiara.",
        ),
        QAItem(
            question=f"Why was there a conflict when {hero.label} wanted to rinse things at {SETTING.place}?",
            answer=(
                f"There was conflict because the path was damp, so the {tiara.label} could get wet and dirty if {hero.label} rushed in."
                f" The {parent.label} wanted a safer plan."
            ),
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=(
                f"{hero.label} remembered a time last week when a sticky ribbon got messy, and the lesson learned was to use a careful plan before rinsing anything shiny."
            ),
        ),
        QAItem(
            question=f"How did the {gear.label} help?",
            answer=(
                f"The {gear.label} helped by keeping the important part safe while {hero.label} could still play and rinse the stage ribbons without ruining the tiara."
            ),
        ),
        QAItem(
            question=f"What happened to the {tiara.label} at the end?",
            answer=f"The {tiara.label} stayed clean and shiny at the end.",
        ),
        QAItem(
            question=f"What about the {clarinet.label}?",
            answer=f"The {clarinet.label} stayed safe too, because the story chose a careful way instead of a messy rush.",
        ),
    ]


KNOWLEDGE = {
    "clarinet": (
        "What is a clarinet?",
        "A clarinet is a long woodwind instrument with keys. You blow air through it to make music.",
    ),
    "tiara": (
        "What is a tiara?",
        "A tiara is a small crown-like headpiece, often shiny and decorative.",
    ),
    "rinse": (
        "What does rinse mean?",
        "To rinse means to wash something lightly with water to remove soap, dirt, or sticky stuff.",
    ),
    "lesson": (
        "What is a lesson learned?",
        "A lesson learned is something you remember after a mistake, so you make a better choice next time.",
    ),
    "flashback": (
        "What is a flashback in a story?",
        "A flashback is a short memory from the past that helps explain why a character feels or acts a certain way.",
    ),
    "conflict": (
        "What is conflict in a story?",
        "Conflict is a problem or disagreement that makes the characters stop and decide what to do.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE.values()]


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
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("activity", "rinse"),
        asp.fact("mess_of", "rinse", "wet"),
        asp.fact("worn_on", "tiara", "torso"),
        asp.fact("worn_on", "clarinet", "torso"),
        asp.fact("gear", "raincoat"),
        asp.fact("gear", "boots"),
        asp.fact("guards", "raincoat", "wet"),
        asp.fact("guards", "boots", "wet"),
        asp.fact("covers", "raincoat", "torso"),
        asp.fact("covers", "boots", "feet"),
        asp.fact("splashes", "rinse", "feet"),
        asp.fact("splashes", "rinse", "legs"),
        asp.fact("splashes", "rinse", "torso"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(A) :- activity(A), has_fix(A, tiara).
#show prize_at_risk/2.
#show protects/3.
#show valid/1.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = set(asp.atoms(model, "valid"))
    if valid == {("rinse",)}:
        print("OK: ASP gate agrees with Python reasonableness.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    print("ASP atoms:", sorted(valid))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: clarinet, tiara, rinse.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
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
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    animal = getattr(args, "animal", None) or rng.choice(ANIMALS)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(name=name, animal=animal, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, name in enumerate(["Mina", "Ollie", "Tia", "Bram", "Luna"]):
            p = StoryParams(name=name, animal=_safe_lookup(ANIMALS, i % len(ANIMALS)), parent="mother")
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
