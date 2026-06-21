#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fearsome_glamorous_puffer_teamwork_sharing_superhero_story.py
=========================================================================================

A standalone story world for a tiny superhero domain built from the seed words
"fearsome", "glamorous", and "puffer", with the core features Teamwork and
Sharing.

Premise
-------
Two children at a make-believe superhero training ground face one fearsome
obstacle, but there is only one glamorous puffer item that can help. A selfish
or solo plan leaves them stuck. The problem resolves only when they share the
item and move as a team.

Run it
------
    python storyworlds/worlds/gpt-5.4/fearsome_glamorous_puffer_teamwork_sharing_superhero_story.py
    python storyworlds/worlds/gpt-5.4/fearsome_glamorous_puffer_teamwork_sharing_superhero_story.py --arena skywalk --obstacle gust_gate
    python storyworlds/worlds/gpt-5.4/fearsome_glamorous_puffer_teamwork_sharing_superhero_story.py --gear star_coat --obstacle bumper_ramp
    python storyworlds/worlds/gpt-5.4/fearsome_glamorous_puffer_teamwork_sharing_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/fearsome_glamorous_puffer_teamwork_sharing_superhero_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/fearsome_glamorous_puffer_teamwork_sharing_superhero_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Arena:
    id: str
    place: str
    opening: str
    finish: str
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
    intro: str
    hazard: str
    need: str
    threat: str
    teamwork_required: bool
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
    protects: set[str]
    share_modes: set[str]
    wear_text: str
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
class Method:
    id: str
    label: str
    teamwork: bool
    action_text: str
    success_text: str
    qa_text: str
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


class World:
    def __init__(self, arena: Arena) -> None:
        self.arena = arena
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "attempt": False,
            "shared": False,
            "protected_team": False,
            "coordinated": False,
            "success": False,
            "setback": False,
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.arena)
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


def _r_left_out(world: World) -> list[str]:
    if not world.facts["attempt"]:
        return []
    if world.facts["shared"]:
        return []
    leader = world.get("leader")
    partner = world.get("partner")
    sig = ("left_out", partner.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    partner.memes["left_out"] += 1
    leader.memes["worry"] += 1
    return ["__left_out__"]


def _r_setback(world: World) -> list[str]:
    if not world.facts["attempt"]:
        return []
    if world.facts["protected_team"] and world.facts["coordinated"]:
        return []
    sig = ("setback", world.facts.get("obstacle_id", "?"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("team").meters["stuck"] += 1
    world.facts["setback"] = True
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__setback__"]


def _r_success(world: World) -> list[str]:
    if not world.facts["attempt"]:
        return []
    if not (world.facts["protected_team"] and world.facts["coordinated"]):
        return []
    sig = ("success", world.facts.get("obstacle_id", "?"))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("team").meters["goal"] += 1
    world.facts["success"] = True
    for kid in world.kids():
        kid.memes["courage"] += 1
        kid.memes["joy"] += 1
    return ["__success__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="left_out", tag="social", apply=_r_left_out),
    Rule(name="setback", tag="physical", apply=_r_setback),
    Rule(name="success", tag="social", apply=_r_success),
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


def compatible(gear: Gear, obstacle: Obstacle, method: Method) -> bool:
    if obstacle.need not in gear.protects:
        return False
    if method.id not in gear.share_modes:
        return False
    if obstacle.teamwork_required and not method.teamwork:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for arena_id in ARENAS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for gear_id, gear in GEARS.items():
                for method_id, method in METHODS.items():
                    if compatible(gear, obstacle, method):
                        combos.append((arena_id, obstacle_id, gear_id, method_id))
    return combos


def predict_outcome(world: World, gear: Gear, obstacle: Obstacle, method: Method) -> dict:
    sim = world.copy()
    sim.facts["attempt"] = True
    sim.facts["shared"] = True
    sim.facts["protected_team"] = compatible(gear, obstacle, method)
    sim.facts["coordinated"] = method.teamwork
    sim.facts["obstacle_id"] = obstacle.id
    propagate(sim, narrate=False)
    return {
        "success": sim.facts["success"],
        "stuck": sim.get("team").meters["stuck"],
    }


def introduce(world: World, leader: Entity, partner: Entity, mentor: Entity, gear: Gear) -> None:
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"After school, {leader.id} and {partner.id} raced into {world.arena.place}, "
        f"where {mentor.label_word} had turned the place into a superhero academy."
    )
    world.say(world.arena.opening)
    world.say(
        f"{leader.id} wore {gear.phrase}. It looked so glamorous that even the mirrors "
        f"seemed to stand taller when {leader.pronoun()} hurried past."
    )


def mission(world: World, leader: Entity, partner: Entity) -> None:
    world.say(
        f'"Heroes of the Bright Team," {leader.id} announced, "we have to reach {world.arena.finish} before the bell rings!"'
    )
    world.say(
        f"{partner.id} grinned and bumped shoulders with {leader.id}. "
        f"They had practiced brave poses all week, and today they wanted a real rescue mission."
    )


def encounter(world: World, obstacle: Obstacle) -> None:
    world.say(
        f"But halfway there, {obstacle.intro}. It looked fearsome enough to stop even pretend heroes in their tracks."
    )
    world.say(obstacle.threat)


def solo_plan(world: World, leader: Entity, partner: Entity, gear: Gear, obstacle: Obstacle) -> None:
    leader.memes["pride"] += 1
    world.say(
        f'{leader.id} touched {gear.label} and whispered, "I can go first. I have the puffer gear."'
    )
    world.say(
        f'{partner.id} looked at the obstacle, then at the single {gear.label}. '
        f'"But what about me?" {partner.pronoun()} asked.'
    )


def failed_try(world: World, leader: Entity, partner: Entity, obstacle: Obstacle) -> None:
    world.facts["attempt"] = True
    world.facts["shared"] = False
    world.facts["protected_team"] = False
    world.facts["coordinated"] = False
    world.facts["obstacle_id"] = obstacle.id
    propagate(world, narrate=False)
    world.say(
        f"{leader.id} took one bold step toward the obstacle, but the moment the challenge roared at them, both children hopped back."
    )
    if partner.memes["left_out"] >= THRESHOLD:
        world.say(
            f"{partner.id}'s brave face crumpled a little. Being left out felt worse than the loud noise."
        )
    if world.facts["setback"]:
        world.say(
            f"The team was stuck. The fearsome challenge was too big for one child and one plan."
        )


def rethink(world: World, mentor: Entity, leader: Entity, partner: Entity, gear: Gear, obstacle: Obstacle, method: Method) -> None:
    pred = predict_outcome(world, gear, obstacle, method)
    world.facts["predicted_success"] = pred["success"]
    mentor.memes["calm"] += 1
    world.say(
        f'{mentor.label_word.capitalize()} knelt beside them and said, "A superhero tool shines brightest when it helps a whole team."'
    )
    world.say(
        f"{leader.id} looked at {gear.label}, then at {partner.id}, and understood that the problem was not the obstacle alone. "
        f"It was trying to keep all the help for one pair of hands."
    )


def share_plan(world: World, leader: Entity, partner: Entity, gear: Gear, method: Method) -> None:
    world.facts["shared"] = True
    leader.memes["generosity"] += 1
    partner.memes["trust"] += 1
    world.say(
        f'"Let\'s share {gear.label}," {leader.id} said. "{method.action_text}"'
    )
    world.say(
        f"{partner.id}'s eyes brightened at once. The plan felt fair, and it felt brave."
    )


def team_attempt(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, gear: Gear, method: Method) -> None:
    world.facts["attempt"] = True
    world.facts["shared"] = True
    world.facts["protected_team"] = compatible(gear, obstacle, method)
    world.facts["coordinated"] = method.teamwork
    world.facts["obstacle_id"] = obstacle.id
    propagate(world, narrate=False)
    world.say(
        f"{leader.id} and {partner.id} {method.success_text}."
    )
    if world.facts["success"]:
        world.say(
            f"Step by step, they passed the obstacle together until the fearsome part was behind them."
        )


def ending(world: World, leader: Entity, partner: Entity, mentor: Entity, gear: Gear) -> None:
    leader.memes["love"] += 1
    partner.memes["love"] += 1
    world.say(
        f"At {world.arena.finish}, they lifted the mission token high above their heads and laughed so hard that their capes shook."
    )
    world.say(
        f'{mentor.label_word.capitalize()} clapped. "That is real superhero work," {mentor.pronoun()} said. '
        f'"Sharing made room for teamwork, and teamwork made both of you strong."'
    )
    world.say(
        f"On the way home, {leader.id} no longer strutted ahead with {gear.label} all to {leader.pronoun('object')}. "
        f"{leader.pronoun().capitalize()} held it open so {partner.id} could walk close beside {leader.pronoun('object')}, and the glamorous puffer gear looked even better with two heroes under its shine."
    )


def tell(
    arena: Arena,
    obstacle: Obstacle,
    gear: Gear,
    method: Method,
    leader_name: str = "Nora",
    leader_gender: str = "girl",
    partner_name: str = "Max",
    partner_gender: str = "boy",
    mentor_type: str = "mother",
    leader_trait: str = "sparky",
    partner_trait: str = "steady",
) -> World:
    world = World(arena)
    leader = world.add(Entity(
        id="leader",
        kind="character",
        type=leader_gender,
        label=leader_name,
        role="leader",
        traits=[leader_trait],
        attrs={"name": leader_name},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        traits=[partner_trait],
        attrs={"name": partner_name},
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type=mentor_type,
        label="the grown-up coach",
        role="mentor",
        attrs={"name": mentor_type},
    ))
    team = world.add(Entity(
        id="team",
        kind="thing",
        type="team",
        label="the Bright Team",
    ))
    item = world.add(Entity(
        id="gear",
        kind="thing",
        type="gear",
        label=gear.label,
        owner="leader",
        attrs={"phrase": gear.phrase},
    ))
    world.facts.update(
        arena=arena,
        obstacle=obstacle,
        gear=gear,
        method=method,
        leader=leader,
        partner=partner,
        mentor=mentor,
        item=item,
    )

    introduce(world, leader, partner, mentor, gear)
    mission(world, leader, partner)

    world.para()
    encounter(world, obstacle)
    solo_plan(world, leader, partner, gear, obstacle)
    failed_try(world, leader, partner, obstacle)

    world.para()
    rethink(world, mentor, leader, partner, gear, obstacle, method)
    share_plan(world, leader, partner, gear, method)
    team_attempt(world, leader, partner, obstacle, gear, method)

    world.para()
    ending(world, leader, partner, mentor, gear)

    world.facts.update(
        success=world.facts["success"],
        setback=world.facts["setback"],
        shared=world.facts["shared"],
    )
    return world


ARENAS = {
    "skywalk": Arena(
        id="skywalk",
        place="the library roof garden",
        opening="Silver stars hung from the railings, and a chalk lightning trail curled between flower pots.",
        finish="the golden signal bell",
        tags={"roof", "academy"},
    ),
    "gym": Arena(
        id="gym",
        place="the school gym",
        opening="Cardboard towers lined the walls, and a bright ribbon marked the Hero Line across the floor.",
        finish="the moon-colored rescue badge",
        tags={"gym", "academy"},
    ),
    "courtyard": Arena(
        id="courtyard",
        place="the apartment courtyard",
        opening="Blankets draped over benches became secret lairs, and a red bucket served as the city's alarm beacon.",
        finish="the shiny rescue lantern",
        tags={"yard", "academy"},
    ),
}

OBSTACLES = {
    "gust_gate": Obstacle(
        id="gust_gate",
        label="the gust gate",
        intro="a fearsome wall of wind burst from a row of giant fans",
        hazard="wind",
        need="wind",
        threat="Paper arrows skittered over the floor, and every cape-tail snapped in the air like a flag in a storm.",
        teamwork_required=True,
        tags={"wind", "fans"},
    ),
    "sleet_tunnel": Obstacle(
        id="sleet_tunnel",
        label="the sleet tunnel",
        intro="a fearsome tunnel of icy mist hissed between two benches",
        hazard="cold",
        need="cold",
        threat="Tiny cold drops floated through the beam of a flashlight, and the path beyond looked shivery and gray.",
        teamwork_required=True,
        tags={"cold", "mist"},
    ),
    "bumper_ramp": Obstacle(
        id="bumper_ramp",
        label="the bumper ramp",
        intro="a fearsome ramp of wobbling foam meteors blocked the path",
        hazard="bumps",
        need="bumps",
        threat="Each soft meteor rolled and bounced just enough to knock a small hero sideways.",
        teamwork_required=True,
        tags={"foam", "bumps"},
    ),
}

GEARS = {
    "comet_cape": Gear(
        id="comet_cape",
        label="the comet cape",
        phrase="a glamorous silver puffer cape with stitched-on stars",
        protects={"wind", "cold"},
        share_modes={"hold_between", "wrap_under"},
        wear_text="The cape puffed around the shoulders like a tiny cloud.",
        tags={"cape", "puffer", "sharing"},
    ),
    "star_coat": Gear(
        id="star_coat",
        label="the star coat",
        phrase="a glamorous gold puffer coat with a moon-bright zipper",
        protects={"cold"},
        share_modes={"wrap_under"},
        wear_text="The coat gleamed every time it caught the light.",
        tags={"coat", "puffer", "sharing"},
    ),
    "cloud_shield": Gear(
        id="cloud_shield",
        label="the cloud shield",
        phrase="a glamorous blue puffer shield sewn from soft quilted cloth",
        protects={"wind", "bumps"},
        share_modes={"hold_between"},
        wear_text="The shield was light, round, and puffy enough to hug.",
        tags={"shield", "puffer", "sharing"},
    ),
}

METHODS = {
    "hold_between": Method(
        id="hold_between",
        label="hold it between them",
        teamwork=True,
        action_text="We can hold it between us like one big hero shield.",
        success_text="held the gear between them, shoulder to shoulder, and leaned into the challenge as one team",
        qa_text="They held the shared gear between them like one shield and moved together.",
        tags={"teamwork", "sharing"},
    ),
    "wrap_under": Method(
        id="wrap_under",
        label="wrap under it together",
        teamwork=True,
        action_text="We can both fit under it if we stay close and walk together.",
        success_text="ducked under the shared gear together and shuffled forward in the same brave rhythm",
        qa_text="They shared the gear by staying under it together and taking the path side by side.",
        tags={"teamwork", "sharing"},
    ),
    "take_turns": Method(
        id="take_turns",
        label="take turns",
        teamwork=False,
        action_text="One of us can use it first and then pass it back.",
        success_text="took turns with the gear",
        qa_text="They tried to use it one at a time.",
        tags={"sharing"},
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Ava", "Lily", "Zoe", "Ella", "Ruby", "June"]
BOY_NAMES = ["Max", "Leo", "Finn", "Theo", "Eli", "Noah", "Sam", "Jack"]
TRAITS = ["sparky", "steady", "bold", "gentle", "quick", "thoughtful"]


@dataclass
class StoryParams:
    arena: str
    obstacle: str
    gear: str
    method: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    mentor: str
    leader_trait: str
    partner_trait: str
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
    "wind": [
        (
            "Why can strong wind make it hard to walk?",
            "Strong wind pushes against your body and can wobble your balance. That is why walking into a gust feels much harder than walking on a calm day.",
        )
    ],
    "cold": [
        (
            "Why does cold mist make people huddle close?",
            "Cold mist carries chilly water through the air and can make skin and clothes feel cold fast. Huddling close helps people keep warm together.",
        )
    ],
    "bumps": [
        (
            "Why does a soft shield still help against bumps?",
            "A soft shield can spread out a bump instead of letting it hit one small spot. That makes little knocks feel gentler and easier to handle.",
        )
    ],
    "puffer": [
        (
            "What is a puffer coat or puffer cape?",
            "A puffer coat or puffer cape is made with soft stuffed sections that trap air. That puffiness can make it warm and cushy.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else use something good with you or after you. It helps everyone feel included instead of left out.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another and act together toward one goal. A team can do jobs that are too hard for one person alone.",
        )
    ],
    "cape": [
        (
            "What does a cape do in superhero play?",
            "A cape is part of make-believe dress-up that helps a hero feel ready and brave. In stories, it often shows movement and courage.",
        )
    ],
    "shield": [
        (
            "What is a shield for?",
            "A shield is something you hold in front of yourself to block a push or a bump. It helps protect you while you move.",
        )
    ],
}
KNOWLEDGE_ORDER = ["sharing", "teamwork", "puffer", "wind", "cold", "bumps", "cape", "shield"]


CURATED = [
    StoryParams(
        arena="skywalk",
        obstacle="gust_gate",
        gear="comet_cape",
        method="hold_between",
        leader_name="Nora",
        leader_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        mentor="mother",
        leader_trait="bold",
        partner_trait="steady",
    ),
    StoryParams(
        arena="gym",
        obstacle="sleet_tunnel",
        gear="star_coat",
        method="wrap_under",
        leader_name="Theo",
        leader_gender="boy",
        partner_name="Ava",
        partner_gender="girl",
        mentor="father",
        leader_trait="quick",
        partner_trait="gentle",
    ),
    StoryParams(
        arena="courtyard",
        obstacle="bumper_ramp",
        gear="cloud_shield",
        method="hold_between",
        leader_name="Ruby",
        leader_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        mentor="mother",
        leader_trait="sparky",
        partner_trait="thoughtful",
    ),
    StoryParams(
        arena="gym",
        obstacle="gust_gate",
        gear="cloud_shield",
        method="hold_between",
        leader_name="Leo",
        leader_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        mentor="father",
        leader_trait="bold",
        partner_trait="steady",
    ),
]


def generation_prompts(world: World) -> list[str]:
    leader = world.facts["leader"]
    partner = world.facts["partner"]
    obstacle = world.facts["obstacle"]
    gear = world.facts["gear"]
    arena = world.facts["arena"]
    leader_name = leader.attrs["name"]
    partner_name = partner.attrs["name"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that uses the words "fearsome", "glamorous", and "puffer".',
        f"Tell a superhero story where {leader_name} and {partner_name} face {obstacle.label} at {arena.place}, but succeed only after sharing {gear.label} and working together.",
        f"Write a gentle action story about teamwork and sharing, where one child first tries to solve a fearsome problem alone and then learns to share a glamorous puffer item.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    leader = world.facts["leader"]
    partner = world.facts["partner"]
    mentor = world.facts["mentor"]
    obstacle = world.facts["obstacle"]
    gear = world.facts["gear"]
    method = world.facts["method"]
    leader_name = leader.attrs["name"]
    partner_name = partner.attrs["name"]
    mentor_word = mentor.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two pretend superheroes, {leader_name} and {partner_name}. They are training together while a grown-up coach watches nearby.",
        ),
        (
            f"What problem did {leader_name} and {partner_name} face?",
            f"They had to get past {obstacle.label}, which looked fearsome and stopped them in the middle of their mission. The obstacle was too hard for one child to handle alone.",
        ),
        (
            f"Why did the first plan fail?",
            f"The first plan failed because only {leader_name} was going to use {gear.label}. That left {partner_name} out, and the team was still unready for the obstacle.",
        ),
        (
            f"How did sharing help them win?",
            f"{leader_name} decided to share {gear.label} instead of keeping it alone. Then {leader_name} and {partner_name} used it together, and that teamwork let them move through the challenge safely.",
        ),
        (
            f"What did {mentor_word} teach them?",
            f"{mentor_word.capitalize()} taught them that a superhero tool is best when it helps the whole team. The lesson was not just to be brave, but to be generous too.",
        ),
        (
            "How did the story end?",
            f"They reached {world.arena.finish} together and finished the mission laughing. The ending shows that the glamorous puffer gear worked best once it was shared.",
        ),
    ]
    if world.facts["success"]:
        qa.append(
            (
                f"How exactly did they get past {obstacle.label}?",
                f"{method.qa_text} They stayed side by side instead of splitting apart, which is why the plan finally worked.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"sharing", "teamwork", "puffer"}
    tags |= set(world.facts["obstacle"].tags)
    tags |= set(world.facts["gear"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(obstacle: Obstacle, gear: Gear, method: Method) -> str:
    if obstacle.need not in gear.protects:
        return (
            f"(No story: {gear.label} cannot honestly protect the team from {obstacle.hazard}. "
            f"Pick gear that helps with {obstacle.need}.)"
        )
    if method.id not in gear.share_modes:
        return (
            f"(No story: {gear.label} is not the kind of item the children can use with the method '{method.id}'. "
            f"Pick a sharing method the gear actually allows.)"
        )
    if obstacle.teamwork_required and not method.teamwork:
        return (
            f"(No story: {obstacle.label} needs both children moving together. "
            f"The method '{method.id}' is sharing, but not teamwork, so it is refused.)"
        )
    return "(No story: this combination does not make a reasonable superhero challenge.)"


def outcome_of(params: StoryParams) -> str:
    if compatible(GEARS[params.gear], OBSTACLES[params.obstacle], METHODS[params.method]):
        return "success"
    return "rejected"


ASP_RULES = r"""
compatible(O, G, M) :- obstacle(O), gear(G), method(M),
                       needs(O, Need), protects(G, Need),
                       allows(G, M),
                       teamwork_needed(O), teamwork_method(M).

rejected(O, G, M) :- obstacle(O), gear(G), method(M), not compatible(O, G, M).

outcome(success)  :- chosen_obstacle(O), chosen_gear(G), chosen_method(M), compatible(O, G, M).
outcome(rejected) :- chosen_obstacle(O), chosen_gear(G), chosen_method(M), rejected(O, G, M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for arena_id in ARENAS:
        lines.append(asp.fact("arena", arena_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("needs", obstacle_id, obstacle.need))
        if obstacle.teamwork_required:
            lines.append(asp.fact("teamwork_needed", obstacle_id))
    for gear_id, gear in GEARS.items():
        lines.append(asp.fact("gear", gear_id))
        for need in sorted(gear.protects):
            lines.append(asp.fact("protects", gear_id, need))
        for mode in sorted(gear.share_modes):
            lines.append(asp.fact("allows", gear_id, mode))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        if method.teamwork:
            lines.append(asp.fact("teamwork_method", method_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_gear", params.gear),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set((o, g, m) for (_, o, g, m) in valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP compatibility matches Python gate ({len(python_set)} obstacle/gear/method combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test story came out empty")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero team learns that sharing glamorous puffer gear makes teamwork possible."
    )
    ap.add_argument("--arena", choices=ARENAS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--leader-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.gear and args.method:
        obstacle = OBSTACLES[args.obstacle]
        gear = GEARS[args.gear]
        method = METHODS[args.method]
        if not compatible(gear, obstacle, method):
            raise StoryError(explain_rejection(obstacle, gear, method))

    combos = [
        combo for combo in valid_combos()
        if (args.arena is None or combo[0] == args.arena)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.gear is None or combo[2] == args.gear)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        if args.obstacle and args.gear and args.method:
            raise StoryError(explain_rejection(OBSTACLES[args.obstacle], GEARS[args.gear], METHODS[args.method]))
        raise StoryError("(No valid combination matches the given options.)")

    arena_id, obstacle_id, gear_id, method_id = rng.choice(sorted(combos))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    leader_name = args.leader_name or _pick_name(rng, leader_gender)
    partner_name = args.partner_name or _pick_name(rng, partner_gender, avoid=leader_name)
    mentor = args.mentor or rng.choice(["mother", "father"])
    leader_trait = rng.choice(TRAITS)
    partner_trait = rng.choice([trait for trait in TRAITS if trait != leader_trait] or TRAITS)
    return StoryParams(
        arena=arena_id,
        obstacle=obstacle_id,
        gear=gear_id,
        method=method_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        mentor=mentor,
        leader_trait=leader_trait,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.arena not in ARENAS:
        raise StoryError(f"(Unknown arena: {params.arena})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    arena = ARENAS[params.arena]
    obstacle = OBSTACLES[params.obstacle]
    gear = GEARS[params.gear]
    method = METHODS[params.method]
    if not compatible(gear, obstacle, method):
        raise StoryError(explain_rejection(obstacle, gear, method))

    world = tell(
        arena=arena,
        obstacle=obstacle,
        gear=gear,
        method=method,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        mentor_type=params.mentor,
        leader_trait=params.leader_trait,
        partner_trait=params.partner_trait,
    )

    return StorySample(
        params=params,
        story=world.render(),
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
        print(asp_program("", "#show compatible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (obstacle, gear, method) combos:\n")
        for obstacle, gear, method in combos:
            arenas = sorted(arena for arena, o, g, m in valid_combos() if (o, g, m) == (obstacle, gear, method))
            print(f"  {obstacle:12} {gear:12} {method:12}  [{', '.join(arenas)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.partner_name}: {p.obstacle} with {p.gear} via {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
