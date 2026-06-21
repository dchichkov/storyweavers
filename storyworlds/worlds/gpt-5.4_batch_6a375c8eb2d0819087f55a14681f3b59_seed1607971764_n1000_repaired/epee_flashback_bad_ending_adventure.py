#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/epee_flashback_bad_ending_adventure.py
=================================================================

A standalone story world for a small child-facing adventure tale built around a
pretend quest, a fencing epee, a flashback, and sometimes a bad ending.

Reference seed:
    Write a story that includes the following words and narrative instruments.
    Words: epee
    Features: Flashback, Bad Ending
    Style: Adventure

World idea
----------
A child and a companion go on a make-believe expedition through an old place to
recover a lost treasure token. The hero carries an epee from fencing practice
and feels brave. At the obstacle, a flashback returns: Coach Mira once warned
that an epee is for careful touches and balance, not for chopping, poking into
dark places, or using as a bridge-pole.

The world model decides whether the hero heeds that memory and uses the proper
gear for the obstacle, or ignores it and tries a shortcut with the epee. If the
hero ignores the lesson, the quest ends badly: someone gets a scrape, the token
is lost, and night closes the adventure.

Run it
------
    python storyworlds/worlds/gpt-5.4/epee_flashback_bad_ending_adventure.py
    python storyworlds/worlds/gpt-5.4/epee_flashback_bad_ending_adventure.py --all
    python storyworlds/worlds/gpt-5.4/epee_flashback_bad_ending_adventure.py --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/epee_flashback_bad_ending_adventure.py --place moonlit_garden --obstacle brambles --gear gloves
    python storyworlds/worlds/gpt-5.4/epee_flashback_bad_ending_adventure.py --place tower_path --obstacle brook
    python storyworlds/worlds/gpt-5.4/epee_flashback_bad_ending_adventure.py --place tower_path --obstacle brambles   # rejected
    python storyworlds/worlds/gpt-5.4/epee_flashback_bad_ending_adventure.py --verify
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
CAREFUL_TRAITS = {"careful", "steady", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
class Setting:
    id: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Obstacle:
    id: str
    label: str
    challenge: str
    path: str
    required_gear: str
    safe_text: str
    fail_text: str
    flashback_risk: str
    severity: int = 1
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
    action: str
    guards: set[str] = field(default_factory=set)
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
class Goal:
    id: str
    label: str
    phrase: str
    ending_image: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_unsafe(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    companion = world.get("companion")
    if hero.meters["unsafe_attempt"] < THRESHOLD:
        return out
    sig = ("unsafe",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["danger"] += 1
    world.get("path").meters["danger"] += 1
    hero.memes["fear"] += 1
    companion.memes["fear"] += 1
    out.append("__danger__")
    return out


def _r_hurt_loss(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    goal = world.get("goal")
    if hero.meters["hurt"] < THRESHOLD:
        return out
    sig = ("hurt_loss",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    goal.meters["lost"] += 1
    hero.memes["sad"] += 1
    hero.memes["regret"] += 1
    out.append("__loss__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="unsafe", tag="physical", apply=_r_unsafe),
    Rule(name="hurt_loss", tag="physical", apply=_r_hurt_loss),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def obstacle_supported(setting: Setting, obstacle: Obstacle) -> bool:
    return obstacle.id in setting.affords


def compatible_gear(obstacle: Obstacle, gear: Gear) -> bool:
    return obstacle.required_gear == gear.id and obstacle.id in gear.guards


def heed_flashback(relation: str, hero_age: int, companion_age: int, trait: str) -> bool:
    if trait in CAREFUL_TRAITS:
        return True
    if relation == "siblings" and companion_age > hero_age:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            if not obstacle_supported(setting, obstacle):
                continue
            for gear_id, gear in GEARS.items():
                if compatible_gear(obstacle, gear):
                    combos.append((place_id, obstacle_id, gear_id))
    return combos


def predict_epee_attempt(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["unsafe_attempt"] += 1
    hero.meters["hurt"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("path").meters["danger"],
        "hurt": hero.meters["hurt"],
        "goal_lost": sim.get("goal").meters["lost"],
        "risk_text": obstacle.flashback_risk,
    }


def introduce(world: World, hero: Entity, companion: Entity, goal: Goal) -> None:
    for kid in (hero, companion):
        kid.memes["joy"] += 1
    world.say(
        f"{hero.id} and {companion.id} set out like small adventurers, with the wind "
        f"moving over {world.setting.place} and making everything feel bigger than usual."
    )
    world.say(
        f"{hero.id} carried an epee from fencing practice in a cloth sleeve and called it "
        f"{hero.pronoun('possessive')} explorer's blade, though {hero.pronoun()} knew it was "
        f"meant for careful sport, not real battle."
    )
    world.say(
        f"They were hunting for {goal.phrase}, a prize they had promised to bring back "
        f"before evening."
    )


def discover_obstacle(world: World, hero: Entity, companion: Entity, obstacle: Obstacle, goal: Goal) -> None:
    world.say(
        f"The trail led them to {obstacle.path}, and there the quest stopped short. "
        f"{goal.phrase.capitalize()} gleamed on the far side, but {obstacle.challenge} stood in the way."
    )
    hero.memes["desire"] += 1
    companion.memes["focus"] += 1


def flashback(world: World, hero: Entity, companion: Entity, obstacle: Obstacle) -> None:
    pred = predict_epee_attempt(world, obstacle)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_hurt"] = pred["hurt"]
    world.facts["predicted_goal_lost"] = pred["goal_lost"]
    hero.memes["memory"] += 1
    companion.memes["caution"] += 1
    world.say(
        f"Then a flashback came to {hero.id} as sharp as a bell. {hero.pronoun().capitalize()} "
        f"remembered Coach Mira in the bright practice hall saying, "
        f'"An epee is for touches and balance, not for wild shortcuts. {obstacle.flashback_risk}."'
    )
    world.say(
        f'{companion.id} saw the same thought pass over {hero.id}\'s face and whispered, '
        f'"We brought better gear than bravery alone."'
    )


def safe_choice(world: World, hero: Entity, companion: Entity, obstacle: Obstacle, gear: Gear) -> None:
    hero.memes["prudence"] += 1
    companion.memes["trust"] += 1
    world.say(
        f"{hero.id} took a breath, slid the epee back into its sleeve, and reached for {gear.phrase}."
    )
    world.say(obstacle.safe_text.format(hero=hero.id, companion=companion.id, gear=gear.label))
    world.get("goal").meters["found"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    companion.memes["joy"] += 1


def bad_choice(world: World, hero: Entity, companion: Entity, obstacle: Obstacle, goal: Goal) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f'But the treasure looked close, and {hero.id} wanted the quick story more than the wise one. '
        f'"I can do it with the epee," {hero.pronoun()} said.'
    )
    hero.meters["unsafe_attempt"] += 1
    propagate(world, narrate=False)
    hero.meters["hurt"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.fail_text.format(hero=hero.id, companion=companion.id, goal=goal.label))
    world.say(
        f"{companion.id} hurried forward to help, but by then {goal.phrase} was gone and the trail no "
        f"longer felt brave at all."
    )


def success_ending(world: World, hero: Entity, companion: Entity, goal: Goal) -> None:
    world.say(
        f"They turned back with {goal.phrase} safe in their hands. The epee stayed quiet in its sleeve, "
        f"and that made {hero.id} feel braver than any grand pose had."
    )
    world.say(
        f"By the time the first evening star showed, {goal.ending_image}."
    )


def bad_ending(world: World, hero: Entity, companion: Entity, goal: Goal) -> None:
    hero.memes["lesson"] += 1
    companion.memes["sad"] += 1
    world.say(
        f"The adventure ended badly. {hero.id} limped home with a scraped knee and a heavy heart, and "
        f"{companion.id} walked beside {hero.pronoun('object')} without boasting or pretending the quest "
        f"could still be won."
    )
    world.say(
        f"At the gate, the epee hung silent at {hero.id}'s side while the dark came down, and "
        f"{goal.ending_image} stayed lost to them for the night."
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    gear: Gear,
    goal: Goal,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    companion_name: str = "Tom",
    companion_gender: str = "boy",
    trait: str = "careful",
    relation: str = "siblings",
    hero_age: int = 6,
    companion_age: int = 8,
    guardian_type: str = "aunt",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[trait],
            age=hero_age,
            attrs={"relation": relation},
        )
    )
    companion = world.add(
        Entity(
            id=companion_name,
            kind="character",
            type=companion_gender,
            role="companion",
            traits=["loyal"],
            age=companion_age,
            attrs={"relation": relation},
        )
    )
    guardian = world.add(
        Entity(
            id="Guardian",
            kind="character",
            type=guardian_type,
            role="guardian",
            label="the grown-up",
        )
    )
    path = world.add(Entity(id="path", type="path", label=obstacle.label))
    goal_ent = world.add(Entity(id="goal", type="goal", label=goal.label))
    gear_ent = world.add(Entity(id="gear", type="gear", label=gear.label))
    epee_ent = world.add(Entity(id="epee", type="epee", label="epee"))

    hero.meters["unsafe_attempt"] = 0.0
    hero.meters["hurt"] = 0.0
    hero.meters["danger"] = 0.0
    goal_ent.meters["lost"] = 0.0
    goal_ent.meters["found"] = 0.0
    path.meters["danger"] = 0.0
    hero.memes["memory"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["regret"] = 0.0
    companion.memes["fear"] = 0.0
    companion.memes["caution"] = 0.0

    introduce(world, hero, companion, goal)
    discover_obstacle(world, hero, companion, obstacle, goal)

    world.para()
    flashback(world, hero, companion, obstacle)

    world.para()
    heeds = heed_flashback(relation, hero_age, companion_age, trait)
    if heeds:
        safe_choice(world, hero, companion, obstacle, gear)
        world.para()
        success_ending(world, hero, companion, goal)
        outcome = "success"
    else:
        bad_choice(world, hero, companion, obstacle, goal)
        world.para()
        bad_ending(world, hero, companion, goal)
        outcome = "bad"

    world.facts.update(
        setting=setting,
        obstacle=obstacle,
        gear=gear,
        goal_cfg=goal,
        hero=hero,
        companion=companion,
        guardian=guardian,
        gear_ent=gear_ent,
        epee=epee_ent,
        relation=relation,
        heeded=heeds,
        outcome=outcome,
        hurt=hero.meters["hurt"] >= THRESHOLD,
        goal_lost=goal_ent.meters["lost"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "moonlit_garden": Setting(
        id="moonlit_garden",
        place="the moonlit garden ruins",
        mood="silver and secret",
        affords={"brambles", "brook"},
    ),
    "tower_path": Setting(
        id="tower_path",
        place="the broken tower path",
        mood="high and windy",
        affords={"stairs", "tunnel"},
    ),
    "cliff_fort": Setting(
        id="cliff_fort",
        place="the old cliff fort",
        mood="echoing and wild",
        affords={"brook", "stairs"},
    ),
}

OBSTACLES = {
    "brambles": Obstacle(
        id="brambles",
        label="brambles",
        challenge="a wall of thorny brambles",
        path="a low arch clogged with briars",
        required_gear="gloves",
        safe_text="{hero} pulled on the gloves and parted the thorny stems slowly, while {companion} held them back. In a few moments they were through without a scratch.",
        fail_text="{hero} thrust the epee into the brambles, but the blade tangled in the vines. The thorns snapped back, scratched {hero}'s hand, and sent the {goal} skittering deeper under the thorn patch.",
        flashback_risk="If you slash at thorns with it, the point can catch and the thorns can whip back at you",
        severity=1,
        tags={"brambles", "thorns"},
    ),
    "tunnel": Obstacle(
        id="tunnel",
        label="tunnel",
        challenge="a dark tunnel with a dip hidden in the floor",
        path="a stone tunnel that swallowed the light",
        required_gear="lantern",
        safe_text="{companion} raised the lantern and {hero} followed the circle of light step by step. The hidden dip showed itself at once, and they crossed safely.",
        fail_text="{hero} poked the epee into the dark and marched after it, but the point found nothing solid. {hero} stepped into the dip, stumbled hard, and the {goal} slipped out of sight into the black corner of the tunnel.",
        flashback_risk="If you use it to probe darkness, it cannot show you the holes your feet will find",
        severity=2,
        tags={"tunnel", "dark"},
    ),
    "brook": Obstacle(
        id="brook",
        label="brook",
        challenge="a narrow brook running fast over slippery stones",
        path="a cold brook with quick water over smooth rocks",
        required_gear="plank",
        safe_text="{hero} and {companion} laid the plank across the brook and tested it together. Then they crossed one small step at a time and reached the far bank dry.",
        fail_text="{hero} tried to balance beside the brook with the epee stretched out like a pole, but the stones rolled underfoot. {hero} splashed into the water, scraped a knee, and the {goal} spun away downstream.",
        flashback_risk="If you trust it like a bridge-pole on wet stones, you may still slip where the water is faster than you are",
        severity=2,
        tags={"brook", "water"},
    ),
    "stairs": Obstacle(
        id="stairs",
        label="stairs",
        challenge="a broken stair with gaps where the old boards had fallen away",
        path="a stair climbing past the wall with loose boards and open gaps",
        required_gear="rope",
        safe_text="{companion} looped the rope around the sound post above, and {hero} climbed carefully with one hand on the line. The missing boards no longer felt like a trap.",
        fail_text="{hero} lifted the epee and tried to use it for balance on the loose stair, but one board tipped under {hero}'s shoe. {hero} fell to the landing below, and the {goal} bounced away into a crack too narrow to reach.",
        flashback_risk="If you trust it to steady you on a broken climb, it cannot hold you when the wood drops away",
        severity=2,
        tags={"stairs", "height"},
    ),
}

GEARS = {
    "gloves": Gear(
        id="gloves",
        label="gloves",
        phrase="the thick garden gloves",
        action="pulled on the gloves",
        guards={"brambles"},
        tags={"gloves"},
    ),
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="the brass lantern",
        action="lit the lantern",
        guards={"tunnel"},
        tags={"lantern", "light"},
    ),
    "plank": Gear(
        id="plank",
        label="plank",
        phrase="the flat rescue plank",
        action="laid down the plank",
        guards={"brook"},
        tags={"plank", "bridge"},
    ),
    "rope": Gear(
        id="rope",
        label="rope",
        phrase="the coil of climbing rope",
        action="threw the rope over the post",
        guards={"stairs"},
        tags={"rope"},
    ),
}

GOALS = {
    "key": Goal(
        id="key",
        label="brass key",
        phrase="the brass key",
        ending_image="the brass key shone on the table beside their cocoa",
        tags={"key"},
    ),
    "banner": Goal(
        id="banner",
        label="scarlet banner",
        phrase="the scarlet banner",
        ending_image="the scarlet banner fluttered from the play fort at home",
        tags={"banner"},
    ),
    "compass": Goal(
        id="compass",
        label="small compass",
        phrase="the small compass",
        ending_image="the small compass rested warm in {hero}'s pocket",
        tags={"compass"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Ava", "Maya", "Zoe", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Tom", "Ben", "Sam", "Leo", "Finn", "Eli", "Max", "Theo"]
TRAITS = ["careful", "steady", "patient", "bold", "rash", "impatient"]
RELATIONS = ["siblings", "friends"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    gear: str
    goal: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    guardian: str
    trait: str
    relation: str = "siblings"
    hero_age: int = 6
    companion_age: int = 8
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


KNOWLEDGE = {
    "epee": [
        (
            "What is an epee?",
            "An epee is a fencing sword used in a careful sport with rules and safety gear. It is light and pointed, so it should never be used as a chopping tool or as a toy for dangerous stunts.",
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in a dark place?",
            "A lantern makes light so you can see where to put your feet. Seeing the ground helps you avoid holes, loose stones, and other surprises.",
        )
    ],
    "rope": [
        (
            "What is a rope good for on a climb?",
            "A rope gives your hands something strong to hold. It can help you keep balance and move more carefully on a steep or broken path.",
        )
    ],
    "gloves": [
        (
            "Why do gloves help with thorns?",
            "Gloves cover your hands and make it harder for sharp thorns to scratch your skin. They let you move prickly branches more safely.",
        )
    ],
    "water": [
        (
            "Why are wet stones slippery?",
            "Water makes the smooth tops of stones slick. Your shoes can slide on them more easily, so crossing too fast is risky.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick memory from an earlier time. It shows something from the past that helps a character decide what to do now.",
        )
    ],
    "tunnel": [
        (
            "Why can tunnels be dangerous when they are dark?",
            "In a dark tunnel you cannot easily see holes, dips, or sharp edges. That is why light and slow steps matter there.",
        )
    ],
    "thorns": [
        (
            "Why can thorny bushes hurt your hands?",
            "Thorny bushes have sharp points meant to protect the plant. If you grab or hit them carelessly, they can scratch you.",
        )
    ],
    "bridge": [
        (
            "Why should you test a bridge or plank before crossing?",
            "Testing it first tells you whether it is steady. A careful check can stop a wobble or a slip before your whole body is on it.",
        )
    ],
    "adventure": [
        (
            "What makes an adventure brave instead of reckless?",
            "A brave adventure still uses good judgment. Reckless choices ignore danger just to look daring.",
        )
    ],
}
KNOWLEDGE_ORDER = ["epee", "flashback", "adventure", "gloves", "lantern", "rope", "water", "tunnel", "thorns", "bridge"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    obstacle = f["obstacle"]
    goal = f["goal_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old that includes the word "epee", '
        f"a flashback, and a quest for {goal.phrase}."
    )
    if outcome == "bad":
        return [
            base,
            f"Tell a small adventure where {hero.id} remembers a warning about an epee but ignores it while facing {obstacle.challenge}, and the quest ends badly.",
            f"Write a child-friendly bad-ending story where {hero.id} and {companion.id} go on a brave quest, a flashback offers the right lesson, and the hero chooses the shortcut anyway.",
        ]
    return [
        base,
        f"Tell a gentle adventure where {hero.id} remembers a warning about an epee, uses the proper gear instead of a shortcut, and brings back {goal.phrase}.",
        f"Write a story with a flashback that helps two young adventurers choose caution over showing off.",
    ]


def pair_noun(hero: Entity, companion: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and companion.type == "boy":
            return "two brothers"
        if hero.type == "girl" and companion.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    obstacle = f["obstacle"]
    gear = f["gear"]
    goal = f["goal_cfg"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, companion, relation)}, {hero.id} and {companion.id}, who went on a quest for {goal.phrase}. They felt as if the old place had turned into a real adventure just for them.",
        ),
        (
            f"Why did {hero.id} carry an epee?",
            f"{hero.id} carried an epee from fencing practice because it made the quest feel grand and brave. But the story shows that the epee was not the right tool for solving every problem.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was a memory of Coach Mira warning that an epee is for careful touches, not for wild shortcuts. That memory mattered because it told {hero.id} exactly why the obstacle was dangerous.",
        ),
        (
            f"What was blocking the quest?",
            f"{obstacle.challenge.capitalize()} blocked the way to {goal.phrase}. The treasure could be seen on the far side, which made the shortcut feel tempting.",
        ),
    ]
    if f["outcome"] == "success":
        qa.append(
            (
                f"How did {hero.id} and {companion.id} get past the obstacle?",
                f"They used {gear.phrase} instead of the epee. That worked because {gear.label} matched the problem and let them cross the danger slowly and safely.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with {goal.phrase} brought home at evening. The quiet epee in its sleeve shows that real bravery came from listening to the flashback and choosing the wiser tool.",
            )
        )
    else:
        qa.append(
            (
                f"What went wrong when {hero.id} used the epee as a shortcut?",
                f"{hero.id} ignored the warning and tried to solve the obstacle with the epee. That led to a scrape and the loss of {goal.phrase}, because the epee could not do the job the proper gear was meant for.",
            )
        )
        qa.append(
            (
                "Why is this a bad ending?",
                f"It is a bad ending because the quest fails and {goal.phrase} is lost before night. The sad walk home also shows that wanting a quick victory made the whole adventure smaller instead of greater.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"epee", "flashback", "adventure"}
    obstacle = f["obstacle"]
    gear = f["gear"]
    if obstacle.id == "tunnel":
        tags.add("tunnel")
    if obstacle.id == "brambles":
        tags.add("thorns")
    if obstacle.id == "brook":
        tags |= {"water", "bridge"}
    if gear.id in KNOWLEDGE:
        tags.add(gear.id)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moonlit_garden",
        obstacle="brambles",
        gear="gloves",
        goal="key",
        hero="Nora",
        hero_gender="girl",
        companion="Tom",
        companion_gender="boy",
        guardian="aunt",
        trait="careful",
        relation="siblings",
        hero_age=6,
        companion_age=8,
    ),
    StoryParams(
        place="tower_path",
        obstacle="tunnel",
        gear="lantern",
        goal="banner",
        hero="Ben",
        hero_gender="boy",
        companion="Maya",
        companion_gender="girl",
        guardian="uncle",
        trait="rash",
        relation="friends",
        hero_age=7,
        companion_age=7,
    ),
    StoryParams(
        place="cliff_fort",
        obstacle="brook",
        gear="plank",
        goal="compass",
        hero="Lucy",
        hero_gender="girl",
        companion="Eli",
        companion_gender="boy",
        guardian="mother",
        trait="patient",
        relation="friends",
        hero_age=6,
        companion_age=6,
    ),
    StoryParams(
        place="cliff_fort",
        obstacle="stairs",
        gear="rope",
        goal="banner",
        hero="Max",
        hero_gender="boy",
        companion="Anna",
        companion_gender="girl",
        guardian="father",
        trait="bold",
        relation="siblings",
        hero_age=8,
        companion_age=6,
    ),
]


def explain_rejection(setting: Setting, obstacle: Obstacle, gear: Gear) -> str:
    if not obstacle_supported(setting, obstacle):
        return (
            f"(No story: {setting.place} does not contain the right kind of path for "
            f"{obstacle.label}. Pick a place that actually affords that obstacle.)"
        )
    return (
        f"(No story: {gear.label} does not honestly solve {obstacle.label}. "
        f"This world only allows gear that really matches the obstacle.)"
    )


def outcome_of(params: StoryParams) -> str:
    return (
        "success"
        if heed_flashback(params.relation, params.hero_age, params.companion_age, params.trait)
        else "bad"
    )


ASP_RULES = r"""
supports(P,O) :- affords(P,O).
compatible(O,G) :- requires(O,G), guards(G,O).
valid(P,O,G) :- supports(P,O), compatible(O,G).

careful_trait(T) :- trait(T), careful_word(T).
older_helper :- relation(siblings), companion_age(CA), hero_age(HA), CA > HA.
heeds_flashback :- careful_trait(T).
heeds_flashback :- older_helper.

outcome(success) :- heeds_flashback.
outcome(bad) :- not heeds_flashback.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("requires", obstacle_id, obstacle.required_gear))
    for gear_id, gear in GEARS.items():
        lines.append(asp.fact("gear", gear_id))
        for guarded in sorted(gear.guards):
            lines.append(asp.fact("guards", gear_id, guarded))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_word", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("companion_age", params.companion_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: generate() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure story world with an epee, a flashback, and sometimes a bad ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle:
        setting = SETTINGS[args.place]
        obstacle = OBSTACLES[args.obstacle]
        if not obstacle_supported(setting, obstacle):
            gear = GEARS[args.gear] if args.gear else GEARS[obstacle.required_gear]
            raise StoryError(explain_rejection(setting, obstacle, gear))
    if args.obstacle and args.gear:
        obstacle = OBSTACLES[args.obstacle]
        gear = GEARS[args.gear]
        if not compatible_gear(obstacle, gear):
            setting = SETTINGS[args.place] if args.place else next(iter(SETTINGS.values()))
            raise StoryError(explain_rejection(setting, obstacle, gear))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.gear is None or combo[2] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, gear_id = rng.choice(sorted(combos))
    goal = args.goal or rng.choice(sorted(GOALS))
    hero, hero_gender = _pick_name(rng)
    companion, companion_gender = _pick_name(rng, avoid=hero)
    guardian = args.guardian or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(RELATIONS)
    hero_age, companion_age = rng.sample([5, 6, 7, 8], 2)

    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        gear=gear_id,
        goal=goal,
        hero=hero,
        hero_gender=hero_gender,
        companion=companion,
        companion_gender=companion_gender,
        guardian=guardian,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        companion_age=companion_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")

    setting = SETTINGS[params.place]
    obstacle = OBSTACLES[params.obstacle]
    gear = GEARS[params.gear]
    goal = GOALS[params.goal]

    if not obstacle_supported(setting, obstacle) or not compatible_gear(obstacle, gear):
        raise StoryError(explain_rejection(setting, obstacle, gear))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        gear=gear,
        goal=goal,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        companion_name=params.companion,
        companion_gender=params.companion_gender,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        companion_age=params.companion_age,
        guardian_type=params.guardian,
    )

    story_text = world.render()
    if "{hero}" in story_text:
        hero_name = world.facts["hero"].id
        story_text = story_text.replace("{hero}", hero_name)

    return StorySample(
        params=params,
        story=story_text,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, gear) combos:\n")
        for place_id, obstacle_id, gear_id in combos:
            print(f"  {place_id:15} {obstacle_id:10} {gear_id}")
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
            header = f"### {p.hero} & {p.companion}: {p.obstacle} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
