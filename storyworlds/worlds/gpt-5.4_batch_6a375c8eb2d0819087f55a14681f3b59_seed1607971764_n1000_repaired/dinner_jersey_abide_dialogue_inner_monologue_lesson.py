#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dinner_jersey_abide_dialogue_inner_monologue_lesson.py
=================================================================================

A standalone story world for a gentle child-sized whodunit: before dinner, a
child's team jersey goes missing. The loss looks mysterious, but the world model
knows whether the jersey was moved to protect it from a messy meal or tidied
away by a helpful grown-up. The child first worries, then investigates, then
learns a lesson about asking before blaming.

Run it
------
    python storyworlds/worlds/gpt-5.4/dinner_jersey_abide_dialogue_inner_monologue_lesson.py
    python storyworlds/worlds/gpt-5.4/dinner_jersey_abide_dialogue_inner_monologue_lesson.py --meal stew --mover grandma --place coat_hook
    python storyworlds/worlds/gpt-5.4/dinner_jersey_abide_dialogue_inner_monologue_lesson.py --place freezer
    python storyworlds/worlds/gpt-5.4/dinner_jersey_abide_dialogue_inner_monologue_lesson.py --all
    python storyworlds/worlds/gpt-5.4/dinner_jersey_abide_dialogue_inner_monologue_lesson.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dinner_jersey_abide_dialogue_inner_monologue_lesson.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Meal:
    id: str
    label: str
    aroma: str
    mess: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class JerseyKind:
    id: str
    phrase: str
    color: str
    team: str
    number: int
    clue: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Mover:
    id: str
    label: str
    type: str
    motive: str
    style: str
    reachable: set[str] = field(default_factory=set)
    washable: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    suits: set[str] = field(default_factory=set)
    clue: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_danger(world: World) -> list[str]:
    jersey = world.get("jersey")
    if jersey.attrs.get("location") != "chair":
        return []
    if world.facts.get("meal_risk", 0.0) < THRESHOLD:
        return []
    sig = ("danger", "jersey")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    jersey.meters["at_risk"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    world.facts["risk_reason"] = "splash"
    return []


def _r_move(world: World) -> list[str]:
    jersey = world.get("jersey")
    mover = world.get("mover")
    if jersey.meters["at_risk"] < THRESHOLD:
        return []
    if mover.meters["noticed_risk"] < THRESHOLD:
        return []
    sig = ("move", mover.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target_place = world.facts["place"]
    jersey.attrs["location"] = target_place.id
    jersey.meters["moved"] += 1
    jersey.meters["safe"] += 1
    mover.memes["helpfulness"] += 1
    world.facts["found_place"] = target_place.id
    world.facts["clue_text"] = target_place.clue
    return []


def _r_damp(world: World) -> list[str]:
    jersey = world.get("jersey")
    mover = world.get("mover")
    place = world.facts["place"]
    if mover.attrs.get("motive") != "wash":
        return []
    if jersey.attrs.get("location") != place.id:
        return []
    sig = ("damp", jersey.attrs.get("location"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    jersey.meters["damp"] += 1
    jersey.attrs["smell"] = "soap"
    return []


CAUSAL_RULES = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="move", tag="physical", apply=_r_move),
    Rule(name="damp", tag="physical", apply=_r_damp),
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
            elif rule.name in {name for name, *_ in world.fired}:
                changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def meal_puts_jersey_at_risk(meal: Meal) -> bool:
    return meal.risky


def place_fits_motive(place: Place, mover: Mover) -> bool:
    return mover.motive in place.suits


def reachable_place(place: Place, mover: Mover) -> bool:
    return place.id in mover.reachable


def valid_combo(meal: Meal, mover: Mover, place: Place) -> bool:
    return meal_puts_jersey_at_risk(meal) and place_fits_motive(place, mover) and reachable_place(place, mover)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for meal_id, meal in MEALS.items():
        for mover_id, mover in MOVERS.items():
            for place_id, place in PLACES.items():
                if valid_combo(meal, mover, place):
                    combos.append((meal_id, mover_id, place_id))
    return combos


def explain_rejection(meal: Meal, mover: Mover, place: Place) -> str:
    if not meal.risky:
        return (
            f"(No story: {meal.label} is not messy enough to threaten a jersey at dinner, "
            f"so nobody has a real reason to move it.)"
        )
    if not reachable_place(place, mover):
        return (
            f"(No story: {mover.label} would not reasonably put the jersey in {place.phrase}. "
            f"Pick a place {mover.pronoun('subject') if isinstance(mover, Entity) else 'they'} can reach in this little world.)"
        )
    return (
        f"(No story: {place.phrase} does not match {mover.label}'s motive to {mover.motive} the jersey. "
        f"The hiding place has to fit why it was moved.)"
    )


def predicted_move(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    jersey = sim.get("jersey")
    return {
        "moved": jersey.meters["moved"] >= THRESHOLD,
        "location": jersey.attrs.get("location", ""),
        "damp": jersey.meters["damp"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, meal: Meal, jersey_cfg: JerseyKind) -> None:
    jersey = world.get("jersey")
    hero.memes["pride"] += 1
    world.say(
        f"On game night, {hero.id} came to the table wearing {jersey_cfg.phrase} from the {jersey_cfg.team}, "
        f"number {jersey_cfg.number} bright on the back."
    )
    world.say(
        f"The whole house smelled like {meal.aroma}, because {helper.label_word} was setting out dinner."
    )
    world.say(
        f'"Please hang that jersey away from the bowls and abide by the supper rule," '
        f'{helper.label_word} said. "We do not eat in our game clothes."'
    )


def hero_decides(world: World, hero: Entity, jersey_cfg: JerseyKind) -> None:
    world.say(
        f'{hero.id} touched the {jersey_cfg.color} sleeve and thought, '
        f'"I only want to wear it a little longer. Nothing bad will happen."'
    )
    hero.memes["defiance"] += 1
    world.get("jersey").attrs["location"] = "chair"
    world.get("jersey").m
