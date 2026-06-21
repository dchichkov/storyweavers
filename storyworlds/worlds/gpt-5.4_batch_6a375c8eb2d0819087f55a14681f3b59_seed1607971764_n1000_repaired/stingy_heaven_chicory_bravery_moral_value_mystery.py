#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stingy_heaven_chicory_bravery_moral_value_mystery.py
================================================================================

A standalone story world for a tall-tale flavored mystery about a brave child,
a stingy grown-up, and a trail of heaven-blue chicory that reveals hidden water.

The world model is simple and classical:

- a frontier town is thirsty because water has been secretly diverted;
- a stingy keeper refuses to share;
- chicory grows where hidden water runs, so an odd bloom becomes a clue;
- a brave child follows the clue with the right gear through a real obstacle;
- the secret is uncovered, the moral turn happens, and the water is shared.

The story always aims at a complete child-facing arc:
premise -> mystery -> brave investigation -> revelation -> moral resolution.

Run it
------
    python storyworlds/worlds/gpt-5.4/stingy_heaven_chicory_bravery_moral_value_mystery.py
    python storyworlds/worlds/gpt-5.4/stingy_heaven_chicory_bravery_moral_value_mystery.py --all
    python storyworlds/worlds/gpt-5.4/stingy_heaven_chicory_bravery_moral_value_mystery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/stingy_heaven_chicory_bravery_moral_value_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/stingy_heaven_chicory_bravery_moral_value_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "grandmother"}
        male = {"boy", "man", "father", "uncle", "grandfather", "miller"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        special = {
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }
        return special.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    town: str
    boast: str
    horizon: str
    helper_title: str
    helper_type: str
    affords_secrets: set[str] = field(default_factory=set)
    affords_obstacles: set[str] = field(default_factory=set)
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
class Keeper:
    id: str
    label: str
    type: str
    hoard_text: str
    lesson_text: str
    secret_ids: set[str] = field(default_factory=set)
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
class Secret:
    id: str
    label: str
    place_text: str
    cause_text: str
    reveal_text: str
    fix_text: str
    clue_ids: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    sight_text: str
    reason_text: str
    find_text: str
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
class Obstacle:
    id: str
    label: str
    risk_text: str
    crossing_text: str
    gear_ids: set[str] = field(default_factory=set)
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
class Gear:
    id: str
    label: str
    phrase: str
    use_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_dry_town(world: World) -> list[str]:
    town = world.get("town")
    waterworks = world.get("waterworks")
    hero = world.get("hero")
    if waterworks.meters["diverted"] < THRESHOLD:
        return []
    sig = ("dry_town",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    town.meters["thirst"] += 1
    hero.memes["concern"] += 1
    return []


def _r_chicory_signal(world: World) -> list[str]:
    clue = world.get("clue")
    waterworks = world.get("waterworks")
    if waterworks.meters["hidden_water"] < THRESHOLD:
        return []
    if clue.meters["seen"] < THRESHOLD:
        return []
    sig = ("chicory_signal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["evidence"] += 1
    world.get("hero").memes["curiosity"] += 1
    return []


def _r_reveal_secret(world: World) -> list[str]:
    hero = world.get("hero")
    secret = world.get("secret")
    obstacle = world.get("obstacle")
    gear = world.get("gear")
    clue = world.get("clue")
    if hero.memes["at_secret"] < THRESHOLD:
        return []
    if gear.attrs.get("fits") != obstacle.id:
        return []
    if clue.meters["evidence"] < THRESHOLD:
        return []
    sig = ("reveal_secret",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    secret.meters["hidden"] = 0.0
    secret.meters["found"] += 1
    world.get("keeper").memes["shame"] += 1
    return []


def _r_restore_flow(world: World) -> list[str]:
    keeper = world.get("keeper")
    secret = world.get("secret")
    waterworks = world.get("waterworks")
    town = world.get("town")
    if secret.meters["found"] < THRESHOLD or keeper.memes["shame"] < THRESHOLD:
        return []
    sig = ("restore_flow",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    keeper.memes["generosity"] += 1
    keeper.memes["greed"] = 0.0
    waterworks.meters["diverted"] = 0.0
    waterworks.meters["flow"] += 1
    town.meters["thirst"] = 0.0
    world.get("hero").memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="dry_town", tag="physical", apply=_r_dry_town),
    Rule(name="chicory_signal", tag="mystery", apply=_r_chicory_signal),
    Rule(name="reveal_secret", tag="mystery", apply=_r_reveal_secret),
    Rule(name="restore_flow", tag="moral", apply=_r_restore_flow),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired) and ("_seen_" + rule.name) not in world.facts:
                world.facts["_seen_" + rule.name] = True
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def clue_matches(secret: Secret, clue: Clue) -> bool:
    return clue.id in secret.clue_ids


def gear_matches(obstacle: Obstacle, gear: Gear) -> bool:
    return gear.id in obstacle.gear_ids


def keeper_matches(keeper: Keeper, secret: Secret) -> bool:
    return secret.id in keeper.secret_ids


def place_supports(place: Place, secret: Secret, obstacle: Obstacle) -> bool:
    return secret.id in place.affords_secrets and obstacle.id in place.affords_obstacles


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for keeper_id, keeper in KEEPERS.items():
            for secret_id, secret in SECRETS.items():
                if not keeper_matches(keeper, secret):
                    continue
                for clue_id, clue in CLUES.items():
                    if not clue_matches(secret, clue):
                        continue
                    for obstacle_id, obstacle in OBSTACLES.items():
                        if not place_supports(place, secret, obstacle):
                            continue
                        for gear_id, gear in GEARS.items():
                            if gear_matches(obstacle, gear):
                                combos.append((place_id, keeper_id, secret_id, clue_id, obstacle_id, gear_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.place not in PLACES or params.keeper not in KEEPERS or params.secret not in SECRETS:
        return "invalid"
    if params.clue not in CLUES or params.obstacle not in OBSTACLES or params.gear not in GEARS:
        return "invalid"
    place = PLACES[params.place]
    keeper = KEEPERS[params.keeper]
    secret = SECRETS[params.secret]
    clue = CLUES[params.clue]
    obstacle = OBSTACLES[params.obstacle]
    gear = GEARS[params.gear]
    if keeper_matches(keeper, secret) and clue_matches(secret, clue) and place_supports(place, secret, obstacle) and gear_matches(obstacle, gear):
        return "solved"
    return "invalid"


def explain_rejection(place: Optional[str], keeper: Optional[str], secret: Optional[str],
                      clue: Optional[str], obstacle: Optional[str], gear: Optional[str]) -> str:
    if keeper and secret and keeper in KEEPERS and secret in SECRETS:
        if not keeper_matches(KEEPERS[keeper], SECRETS[secret]):
            return (f"(No story: {KEEPERS[keeper].label} does not fit the secret "
                    f'"{SECRETS[secret].label}". Pick a keeper whose property could '
                    f"hide that waterworks trick.)")
    if secret and clue and secret in SECRETS and clue in CLUES:
        if not clue_matches(SECRETS[secret], CLUES[clue]):
            return (f"(No story: {CLUES[clue].label} would not honestly point to "
                    f'"{SECRETS[secret].label}". The mystery clue must fit the secret.)')
    if obstacle and gear and obstacle in OBSTACLES and gear in GEARS:
        if not gear_matches(OBSTACLES[obstacle], GEARS[gear]):
            return (f"(No story: {GEARS[gear].label} is the wrong tool for "
                    f'{OBSTACLES[obstacle].label}. The brave move needs the right gear.)')
    if place and secret and obstacle and place in PLACES and secret in SECRETS and obstacle in OBSTACLES:
        if not place_supports(PLACES[place], SECRETS[secret], OBSTACLES[obstacle]):
            return (f"(No story: {PLACES[place].town} does not suit that secret and "
                    f"obstacle together. Pick a landscape that can honestly hold both.)")
    return "(No valid combination matches the given options.)"


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, place: Place, hero: Entity, helper: Entity) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"In {place.town}, the wind was so broad it could have hung ten shirts on the same clothesline, "
        f"and the sky looked near enough to pat with a broom. Folks said the horizon there leaned down from heaven "
        f"just to hear children laugh."
    )
    world.say(
        f"{hero.id} was the sort of {hero.type} who would walk toward a puzzle instead of around it, "
        f"and {helper.label} always said that was half bravery and half good sense."
    )


def set_problem(world: World, place: Place, keeper_cfg: Keeper, hero: Entity, keeper: Entity) -> None:
    keeper.memes["greed"] += 1
    world.get("waterworks").meters["diverted"] += 1
    world.get("waterworks").meters["hidden_water"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That summer the town pump coughed more dust than water, while {keeper_cfg.label} kept a private patch of green "
        f"growing fat and glossy behind a fence. {keeper_cfg.hoard_text}"
    )
    world.say(
        f'"Water is short," {keeper.id} said, hugging the dipper to {keeper.pronoun("possessive")} vest. '
        f'"A person ought to mind {keeper.pronoun("possessive")} own bucket."'
    )
    world.facts["keeper_refusal"] = True
    hero.memes["justice"] += 1


def notice_clue(world: World, clue_cfg: Clue, hero: Entity) -> None:
    clue = world.get("clue")
    clue.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But on the cracked lane beyond the pump, {hero.id} saw {clue_cfg.sight_text}. "
        f"The blossoms were blue as a little scrap of heaven dropped on the dirt."
    )
    world.say(
        f"{hero.id} crouched low and whispered, "
        f'"That chicory is telling on somebody."'
    )


def reason_about_clue(world: World, clue_cfg: Clue, helper: Entity, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'{helper.label} shaded {helper.pronoun("possessive")} eyes and nodded. '
        f'"{clue_cfg.reason_text}"'
    )
    world.say(
        f"That made the blue flowers into more than pretty weeds. It made them a mystery to solve."
    )


def choose_bravery(world: World, obstacle_cfg: Obstacle, gear_cfg: Gear, hero: Entity, helper: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"The trail of chicory pointed straight toward {obstacle_cfg.label}, and everybody in town knew about {obstacle_cfg.risk_text}."
    )
    world.say(
        f'{helper.label} offered {gear_cfg.phrase}. "{gear_cfg.use_text}," {helper.pronoun()} said.'
    )
    hero.memes["courage"] += 1
    world.facts["brave_choice"] = True
    world.say(
        f"{hero.id} swallowed once, set {hero.pronoun('possessive')} shoulders, and chose to go on anyway."
    )


def cross_obstacle(world: World, obstacle_cfg: Obstacle, gear_cfg: Gear, hero: Entity) -> None:
    gear = world.get("gear")
    gear.attrs["fits"] = obstacle_cfg.id
    hero.memes["at_secret"] += 1
    world.say(
        f"With {gear_cfg.label}, {hero.id} {obstacle_cfg.crossing_text}. "
        f"The brave part was not pretending the place was safe. The brave part was going carefully because it was not."
    )


def reveal_secret(world: World, secret_cfg: Secret, clue_cfg: Clue, hero: Entity, keeper: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"At the far side, {hero.id} found {clue_cfg.find_text}, and there lay {secret_cfg.place_text}."
    )
    world.say(
        f"{secret_cfg.reveal_text} {secret_cfg.cause_text}"
    )
    keeper.memes["shame"] += 1
    propagate(world, narrate=False)
    world.facts["evidence_found"] = True


def moral_turn(world: World, keeper_cfg: Keeper, secret_cfg: Secret, keeper: Entity, helper: Entity, hero: Entity) -> None:
    world.say(
        f'{hero.id} ran back with {helper.label}, and together they stood before {keeper.id}. '
        f'"We found the truth," {hero.pronoun()} said.'
    )
    world.say(
        f"{keeper.id} looked from the hidden waterworks to the dry pump and then down at {keeper.pronoun('possessive')} own boots. "
        f"{keeper_cfg.lesson_text}"
    )
    propagate(world, narrate=False)
    world.say(
        f"{keeper.id} went to {secret_cfg.label} and {secret_cfg.fix_text}. Water answered at once with a happy rush."
    )
    world.facts["confessed"] = True


def ending(world: World, place: Place, keeper: Entity, hero: Entity, helper: Entity) -> None:
    town = world.get("town")
    town.meters["water"] += 1
    hero.memes["joy"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"By suppertime the pump was singing again, children were splashing their hands, and even the trough for the mules brimmed to the edge."
    )
    world.say(
        f"{keeper.id} was not stingy anymore. {keeper.pronoun().capitalize()} filled cups for the line of neighbors and even brewed a nutty chicory drink for the grown-ups while the blue blossoms nodded beside the lane."
    )
    world.say(
        f"In {place.town}, folks told the tale for years: if you follow a true clue with a brave heart and a fair mind, even a mean secret will open and share."
    )


def tell(place: Place, keeper_cfg: Keeper, secret_cfg: Secret, clue_cfg: Clue,
         obstacle_cfg: Obstacle, gear_cfg: Gear,
         hero_name: str = "June", hero_type: str = "girl",
         helper_name: str = "Grandma Wren") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=place.helper_type, role="helper", label=helper_name))
    keeper = world.add(Entity(id=keeper_cfg.label, kind="character", type=keeper_cfg.type, role="keeper", label=keeper_cfg.label))
    town = world.add(Entity(id="town", kind="thing", type="town", label=place.town))
    waterworks = world.add(Entity(id="waterworks", kind="thing", type="waterworks", label=secret_cfg.label))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=clue_cfg.label))
    secret = world.add(Entity(id="secret", kind="thing", type="secret", label=secret_cfg.label))
    obstacle = world.add(Entity(id="obstacle", kind="thing", type="obstacle", label=obstacle_cfg.label))
    gear = world.add(Entity(id="gear", kind="thing", type="gear", label=gear_cfg.label))

    secret.meters["hidden"] = 1.0
    waterworks.meters["flow"] = 0.0
    waterworks.meters["diverted"] = 0.0
    waterworks.meters["hidden_water"] = 0.0
    clue.meters["seen"] = 0.0
    clue.meters["evidence"] = 0.0
    hero.memes["curiosity"] = 0.0
    hero.memes["courage"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["justice"] = 0.0
    hero.memes["at_secret"] = 0.0
    keeper.memes["greed"] = 0.0
    keeper.memes["shame"] = 0.0
    keeper.memes["generosity"] = 0.0
    town.meters["thirst"] = 0.0
    town.meters["water"] = 0.0
    gear.attrs["fits"] = ""
    world.facts["outcome"] = "solved"

    introduce(world, place, hero, helper)
    set_problem(world, place, keeper_cfg, hero, keeper)
    world.para()
    notice_clue(world, clue_cfg, hero)
    reason_about_clue(world, clue_cfg, helper, hero)
    world.para()
    choose_bravery(world, obstacle_cfg, gear_cfg, hero, helper)
    cross_obstacle(world, obstacle_cfg, gear_cfg, hero)
    reveal_secret(world, secret_cfg, clue_cfg, hero, keeper)
    world.para()
    moral_turn(world, keeper_cfg, secret_cfg, keeper, helper, hero)
    ending(world, place, keeper, hero, helper)

    world.facts.update(
        place=place,
        keeper_cfg=keeper_cfg,
        secret_cfg=secret_cfg,
        clue_cfg=clue_cfg,
        obstacle_cfg=obstacle_cfg,
        gear_cfg=gear_cfg,
        hero=hero,
        helper=helper,
        keeper=keeper,
        town=town,
        secret=secret,
        clue=clue,
        obstacle=obstacle,
        gear=gear,
        solved=secret.meters["found"] >= THRESHOLD,
        shared=keeper.memes["generosity"] >= THRESHOLD,
        thirsty=town.meters["thirst"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PLACES = {
    "prairie": Place(
        id="prairie",
        town="Dusty Flats",
        boast="where the wheat grew so high it combed the moon",
        horizon="a flat silver rim",
        helper_title="Grandma",
        helper_type="grandmother",
        affords_secrets={"windmill_valve", "sluice_gate"},
        affords_obstacles={"muddy_ditch", "creaky_bridge"},
        tags={"prairie", "water"},
    ),
    "canyon": Place(
        id="canyon",
        town="Red Bluff",
        boast="where echoes were said to wear boots",
        horizon="a red stone rim",
        helper_title="Grandpa",
        helper_type="grandfather",
        affords_secrets={"stone_lid", "sluice_gate"},
        affords_obstacles={"steep_bank", "creaky_bridge"},
        tags={"canyon", "water"},
    ),
    "riverbend": Place(
        id="riverbend",
        town="Willow Bend",
        boast="where catfish were rumored to wink at wagon wheels",
        horizon="a shining bend of river light",
        helper_title="Aunt",
        helper_type="aunt",
        affords_secrets={"windmill_valve", "stone_lid"},
        affords_obstacles={"muddy_ditch", "dark_culvert"},
        tags={"river", "water"},
    ),
}

KEEPERS = {
    "miller": Keeper(
        id="miller",
        label="Mr. Grindle the Miller",
        type="miller",
        hoard_text="His mill pond stayed full as a silver platter, and he counted each drop as if it were a coin.",
        lesson_text="For the first time, his face looked smaller than his fence. He understood that keeping water from thirsty neighbors was meaner than any dry spell.",
        secret_ids={"windmill_valve"},
        tags={"stingy", "mill", "sharing"},
    ),
    "orcharder": Keeper(
        id="orcharder",
        label="Aunt Brindle the Orchard Keeper",
        type="woman",
        hoard_text="Her peach trees drank deep behind locked boards, though the town pump wheezed like an old harmonica.",
        lesson_text="Her shoulders drooped. Sweet fruit, she suddenly saw, tasted poor when everyone else was thirsty.",
        secret_ids={"sluice_gate"},
        tags={"stingy", "orchard", "sharing"},
    ),
    "storekeeper": Keeper(
        id="storekeeper",
        label="Mrs. Pennycuff the Storekeeper",
        type="woman",
        hoard_text="The barrels behind her store stayed cool and wet, and she sold even a sip as if it were treasure.",
        lesson_text="She heard the children licking dry lips and felt ashamed clear down to her apron hem. Fairness mattered more than profit.",
        secret_ids={"stone_lid"},
        tags={"stingy", "store", "sharing"},
    ),
}

SECRETS = {
    "windmill_valve": Secret(
        id="windmill_valve",
        label="the old windmill valve",
        place_text="a crooked iron valve hidden under the windmill floorboards",
        cause_text="Someone had turned it so the underground spring fed a private tank instead of the town pump.",
        reveal_text="A thin ribbon of wet earth gleamed in the shade.",
        fix_text="swung the valve back toward town",
        clue_ids={"chicory_crown", "chicory_line"},
        tags={"spring", "valve", "mystery"},
    ),
    "sluice_gate": Secret(
        id="sluice_gate",
        label="the creek sluice gate",
        place_text="a timber gate tucked under willow roots",
        cause_text="Its boards had been set to send the creek toward one fenced patch while the public channel went thirsty.",
        reveal_text="Water whispered behind the roots like a secret trying to get out.",
        fix_text="lifted the sluice and let the water choose the public channel again",
        clue_ids={"chicory_line"},
        tags={"creek", "gate", "mystery"},
    ),
    "stone_lid": Secret(
        id="stone_lid",
        label="the buried spring lid",
        place_text="a round stone lid hidden under thorny brush",
        cause_text="The spring below had been capped, and the water crept sideways into private barrels instead of rising where everyone could draw it.",
        reveal_text="The ground there breathed cool against the heat.",
        fix_text="rolled the lid aside and broke the selfish little trick",
        clue_ids={"chicory_ring"},
        tags={"spring", "stone", "mystery"},
    ),
}

CLUES = {
    "chicory_line": Clue(
        id="chicory_line",
        label="a line of chicory",
        sight_text="a neat blue line of chicory running across dirt too dry for polite weeds",
        reason_text="Chicory does not waste itself in dead ground. If it is blooming there, hidden water is walking underfoot.",
        find_text="where the chicory line ended in a patch of damp roots",
        tags={"chicory", "clue", "water"},
    ),
    "chicory_ring": Clue(
        id="chicory_ring",
        label="a ring of chicory",
        sight_text="a ring of chicory blooming in a perfect circle in the hardpan",
        reason_text="Flowers do not stand in a round ring for no reason. Something cool and wet is sleeping in the middle.",
        find_text="where the chicory ring hugged a low hump in the earth",
        tags={"chicory", "clue", "water"},
    ),
    "chicory_crown": Clue(
        id="chicory_crown",
        label="a crown of chicory",
        sight_text="a crown of chicory nodding around a forgotten windmill",
        reason_text="Those heaven-blue blossoms are drinking from somewhere. Follow what they are praising, and you will find the spring.",
        find_text="where the chicory crown leaned against loose boards",
        tags={"chicory", "clue", "water"},
    ),
}

OBSTACLES = {
    "dark_culvert": Obstacle(
        id="dark_culvert",
        label="the dark culvert",
        risk_text="the dark culvert where sounds got big and shadows got bigger",
        crossing_text="ducked through the dark culvert, step by steady step",
        gear_ids={"lantern"},
        tags={"dark", "bravery"},
    ),
    "steep_bank": Obstacle(
        id="steep_bank",
        label="the steep bank",
        risk_text="the steep bank where loose pebbles slid like marbles",
        crossing_text="lowered down the steep bank carefully and climbed the far side without slipping",
        gear_ids={"rope"},
        tags={"height", "bravery"},
    ),
    "muddy_ditch": Obstacle(
        id="muddy_ditch",
        label="the muddy ditch",
        risk_text="the muddy ditch that could steal a shoe and a whole afternoon",
        crossing_text="splashed through the muddy ditch without losing footing or nerve",
        gear_ids={"boots"},
        tags={"mud", "bravery"},
    ),
    "creaky_bridge": Obstacle(
        id="creaky_bridge",
        label="the creaky bridge",
        risk_text="the creaky bridge that grumbled at every board",
        crossing_text="crossed the creaky bridge one honest plank at a time",
        gear_ids={"rope"},
        tags={"bridge", "bravery"},
    ),
}

GEARS = {
    "lantern": Gear(
        id="lantern",
        label="a lantern",
        phrase="a lantern with a chimney bright as a firefly jar",
        use_text="Light first, feet second",
        tags={"lantern", "light"},
    ),
    "rope": Gear(
        id="rope",
        label="a coil of rope",
        phrase="a coil of rope thick as a sleepy snake",
        use_text="Tie courage to care, and then climb",
        tags={"rope", "tool"},
    ),
    "boots": Gear(
        id="boots",
        label="high boots",
        phrase="high boots that had seen enough mud to write their own book",
        use_text="Keep your footing and the rest of you can stay brave",
        tags={"boots", "tool"},
    ),
}

GIRL_NAMES = ["June", "Mabel", "Nell", "Sadie", "Pearl", "Dottie", "Elsie", "Hattie"]
BOY_NAMES = ["Beau", "Eli", "Wade", "Jasper", "Otis", "Rudy", "Cal", "Tuck"]
HELPER_NAMES = {
    "grandmother": ["Grandma Wren", "Grandma May", "Grandma Clover"],
    "grandfather": ["Grandpa Reed", "Grandpa Flint", "Grandpa Clay"],
    "aunt": ["Aunt Lark", "Aunt Tilda", "Aunt Rue"],
}
TRAITS = ["curious", "steady", "kind", "sharp-eyed", "plucky", "patient"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    keeper: str
    secret: str
    clue: str
    obstacle: str
    gear: str
    hero_name: str
    hero_gender: str
    helper_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "chicory": [
        (
            "What is chicory?",
            "Chicory is a plant with blue flowers that often grows by roads and fields. Its roots can also be roasted to make a drink.",
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes up from the ground. It can feed a creek, a pump, or a pond.",
        )
    ],
    "sharing": [
        (
            "Why is sharing water important?",
            "Water is something everyone needs. Keeping it only for yourself when others are thirsty is unfair and unkind.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel scared. It does not mean being careless.",
        )
    ],
    "mystery": [
        (
            "What is a mystery to solve?",
            "A mystery to solve is a question with hidden facts. You look for clues and think carefully until the answer makes sense.",
        )
    ],
    "lantern": [
        (
            "Why does a lantern help in a dark place?",
            "A lantern makes light so you can see where you are stepping. Seeing clearly helps people stay safer.",
        )
    ],
    "rope": [
        (
            "Why is a rope useful on a steep place?",
            "A rope helps you hold on and lower yourself carefully. It gives you more control so you do not slip as easily.",
        )
    ],
    "boots": [
        (
            "Why are boots good in mud?",
            "Boots protect your feet and help keep your footing. They make it easier to walk through wet, sticky ground.",
        )
    ],
}

KNOWLEDGE_ORDER = ["chicory", "spring", "sharing", "bravery", "mystery", "lantern", "rope", "boots"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    keeper_cfg = f["keeper_cfg"]
    clue_cfg = f["clue_cfg"]
    return [
        f'Write a tall-tale style story for a 3-to-5-year-old about a brave child in {place.town} who solves a water mystery. Include the words "stingy", "heaven", and "chicory".',
        f"Tell a frontier-flavored story where {hero.id} notices {clue_cfg.label}, uncovers why a stingy keeper is hiding water, and helps the town share fairly.",
        f'Write a simple mystery story with bravery and moral value, where heaven-blue chicory becomes the clue that leads to the truth.',
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    keeper = f["keeper"]
    clue_cfg = f["clue_cfg"]
    secret_cfg = f["secret_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    gear_cfg = f["gear_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a brave {hero.type}, and {helper.label}, who helped {hero.pronoun('object')} think about the clues. It is also about {keeper.id}, whose stingy choice caused the trouble.",
        ),
        (
            "What was the mystery to solve?",
            f"The town pump had gone dry even though one place stayed green and wet. {hero.id} had to figure out where the water was really going and why.",
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found {clue_cfg.label}. The chicory mattered because it was blooming where hidden water was still moving under the ground.",
        ),
        (
            f"Why was following the clue brave?",
            f"The trail led toward {obstacle_cfg.label}, which scared people for a good reason. {hero.id} kept going carefully with {gear_cfg.label}, so the bravery came from facing danger wisely, not from pretending there was none.",
        ),
        (
            "What secret did the clue reveal?",
            f"The clue led to {secret_cfg.label}. Once {hero.id} found it, everyone could see that the water had been diverted away from the town pump.",
        ),
        (
            f"How did the stingy keeper change?",
            f"{keeper.id} felt ashamed after the truth was uncovered. Then {keeper.pronoun()} fixed the waterworks and shared water with the town, which showed better moral value than hoarding it.",
        ),
        (
            "How did the story end?",
            f"The pump sang again, the town had water, and the keeper was not stingy anymore. The ending proves that bravery and fairness solved the mystery together.",
        ),
    ]
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags = {"chicory", "spring", "sharing", "bravery", "mystery"}
    gear_id = world.facts["gear_cfg"].id
    if gear_id in {"lantern", "rope", "boots"}:
        tags.add(gear_id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:20} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(P, K, S, C, O, G) :-
    place(P), keeper(K), secret(S), clue(C), obstacle(O), gear(G),
    keeper_secret(K, S),
    secret_clue(S, C),
    place_secret(P, S),
    place_obstacle(P, O),
    obstacle_gear(O, G).

outcome(solved) :-
    chosen_place(P), chosen_keeper(K), chosen_secret(S), chosen_clue(C),
    chosen_obstacle(O), chosen_gear(G),
    valid(P, K, S, C, O, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.affords_secrets):
            lines.append(asp.fact("place_secret", pid, sid))
        for oid in sorted(place.affords_obstacles):
            lines.append(asp.fact("place_obstacle", pid, oid))
    for kid, keeper in KEEPERS.items():
        lines.append(asp.fact("keeper", kid))
        for sid in sorted(keeper.secret_ids):
            lines.append(asp.fact("keeper_secret", kid, sid))
    for sid, secret in SECRETS.items():
        lines.append(asp.fact("secret", sid))
        for cid in sorted(secret.clue_ids):
            lines.append(asp.fact("secret_clue", sid, cid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        for gid in sorted(obstacle.gear_ids):
            lines.append(asp.fact("obstacle_gear", oid, gid))
    for gid in GEARS:
        lines.append(asp.fact("gear", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_keeper", params.keeper),
        asp.fact("chosen_secret", params.secret),
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_gear", params.gear),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"FAILED: resolve_params crashed for seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} scenario outcomes differ.")

    smoke_cases = cases[:3] if len(cases) >= 3 else cases
    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if not sample.story_qa or not sample.world_qa:
                raise StoryError("generated empty QA")
            buf = io.StringIO()
            saved = sys.stdout
            try:
                sys.stdout = buf
                emit(sample, trace=False, qa=False, header="")
            finally:
                sys.stdout = saved
        print(f"OK: smoke-tested generate()/emit() on {len(smoke_cases)} samples.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"FAILED smoke test: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale mystery storyworld: a brave child follows chicory clues to uncover a stingy water secret."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--secret", choices=SECRETS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.keeper and args.secret and not keeper_matches(KEEPERS[args.keeper], SECRETS[args.secret]):
        raise StoryError(explain_rejection(args.place, args.keeper, args.secret, args.clue, args.obstacle, args.gear))
    if args.secret and args.clue and not clue_matches(SECRETS[args.secret], CLUES[args.clue]):
        raise StoryError(explain_rejection(args.place, args.keeper, args.secret, args.clue, args.obstacle, args.gear))
    if args.obstacle and args.gear and not gear_matches(OBSTACLES[args.obstacle], GEARS[args.gear]):
        raise StoryError(explain_rejection(args.place, args.keeper, args.secret, args.clue, args.obstacle, args.gear))
    if args.place and args.secret and args.obstacle and not place_supports(PLACES[args.place], SECRETS[args.secret], OBSTACLES[args.obstacle]):
        raise StoryError(explain_rejection(args.place, args.keeper, args.secret, args.clue, args.obstacle, args.gear))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.keeper is None or combo[1] == args.keeper)
        and (args.secret is None or combo[2] == args.secret)
        and (args.clue is None or combo[3] == args.clue)
        and (args.obstacle is None or combo[4] == args.obstacle)
        and (args.gear is None or combo[5] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, keeper, secret, clue, obstacle, gear = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = PLACES[place].helper_type
    helper_name = rng.choice(HELPER_NAMES[helper_type])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        keeper=keeper,
        secret=secret,
        clue=clue,
        obstacle=obstacle,
        gear=gear,
        hero_name=name,
        hero_gender=gender,
        helper_name=helper_name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.keeper not in KEEPERS:
        raise StoryError(f"Unknown keeper: {params.keeper}")
    if params.secret not in SECRETS:
        raise StoryError(f"Unknown secret: {params.secret}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.gear not in GEARS:
        raise StoryError(f"Unknown gear: {params.gear}")
    if outcome_of(params) != "solved":
        raise StoryError(explain_rejection(params.place, params.keeper, params.secret, params.clue, params.obstacle, params.gear))

    world = tell(
        place=PLACES[params.place],
        keeper_cfg=KEEPERS[params.keeper],
        secret_cfg=SECRETS[params.secret],
        clue_cfg=CLUES[params.clue],
        obstacle_cfg=OBSTACLES[params.obstacle],
        gear_cfg=GEARS[params.gear],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        helper_name=params.helper_name,
    )
    hero = world.get("hero")
    if params.trait and params.trait not in hero.traits:
        hero.traits.append(params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
    StoryParams(
        place="prairie",
        keeper="miller",
        secret="windmill_valve",
        clue="chicory_crown",
        obstacle="muddy_ditch",
        gear="boots",
        hero_name="June",
        hero_gender="girl",
        helper_name="Grandma Wren",
        trait="plucky",
    ),
    StoryParams(
        place="canyon",
        keeper="orcharder",
        secret="sluice_gate",
        clue="chicory_line",
        obstacle="creaky_bridge",
        gear="rope",
        hero_name="Beau",
        hero_gender="boy",
        helper_name="Grandpa Flint",
        trait="steady",
    ),
    StoryParams(
        place="riverbend",
        keeper="storekeeper",
        secret="stone_lid",
        clue="chicory_ring",
        obstacle="dark_culvert",
        gear="lantern",
        hero_name="Pearl",
        hero_gender="girl",
        helper_name="Aunt Rue",
        trait="sharp-eyed",
    ),
    StoryParams(
        place="riverbend",
        keeper="miller",
        secret="windmill_valve",
        clue="chicory_line",
        obstacle="muddy_ditch",
        gear="boots",
        hero_name="Jasper",
        hero_gender="boy",
        helper_name="Aunt Lark",
        trait="kind",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, keeper, secret, clue, obstacle, gear) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.clue} -> {p.secret} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
