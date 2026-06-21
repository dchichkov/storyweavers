#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/coal_reconciliation_adventure.py
===========================================================

A standalone storyworld about two children on a small adventure who quarrel over
a piece of coal, then reconcile by using it together in a sensible way.

The world model is built around one practical constraint: coal can help as a
marking tool only when the adventure setting offers pale, dry surfaces that will
actually show dark trail arrows. The story therefore refuses combinations where
the chosen surface is too dark or too wet to mark.

Run it
------
    python storyworlds/worlds/gpt-5.4/coal_reconciliation_adventure.py
    python storyworlds/worlds/gpt-5.4/coal_reconciliation_adventure.py --setting quarry_path --obstacle fork --surface pale_stone
    python storyworlds/worlds/gpt-5.4/coal_reconciliation_adventure.py --surface wet_rock
    python storyworlds/worlds/gpt-5.4/coal_reconciliation_adventure.py --all
    python storyworlds/worlds/gpt-5.4/coal_reconciliation_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/coal_reconciliation_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import io
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
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    goal: str
    affords: set[str] = field(default_factory=set)
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
    hook: str
    danger: str
    solve: str
    severity: int
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
class Surface:
    id: str
    label: str
    phrase: str
    markable: bool
    reason: str
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
class StoryParams:
    setting: str
    obstacle: str
    surface: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    relation: str
    parent: str
    peacemaker_trait: str
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


def _r_split_confusion(world: World) -> list[str]:
    team = world.get("team")
    trail = world.get("trail")
    if team.meters["separated"] < THRESHOLD or trail.meters["marked"] >= THRESHOLD:
        return []
    sig = ("split_confusion",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    trail.meters["lostness"] += 1
    for kid_id in ("leader", "partner"):
        world.get(kid_id).memes["fear"] += 1
    return ["__confusion__"]


def _r_marking_guides(world: World) -> list[str]:
    trail = world.get("trail")
    coal = world.get("coal")
    if coal.meters["shared"] < THRESHOLD or trail.meters["marked"] < THRESHOLD:
        return []
    sig = ("marking_guides",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if trail.meters["lostness"] >= THRESHOLD:
        trail.meters["lostness"] = 0.0
    for kid_id in ("leader", "partner"):
        kid = world.get(kid_id)
        kid.memes["hope"] += 1
        kid.memes["trust"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    leader = world.get("leader")
    partner = world.get("partner")
    team = world.get("team")
    if leader.memes["apology"] < THRESHOLD or partner.memes["forgiveness"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    team.memes["harmony"] += 1
    leader.memes["hurt"] = 0.0
    partner.memes["hurt"] = 0.0
    leader.memes["pride"] = 0.0
    partner.memes["pride"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="split_confusion", tag="physical", apply=_r_split_confusion),
    Rule(name="marking_guides", tag="physical", apply=_r_marking_guides),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


SETTINGS = {
    "quarry_path": Setting(
        id="quarry_path",
        place="the pale path beside the old quarry",
        scene="broken walls, bright weeds, and stones the color of bread crusts",
        goal="a little lookout nook above the path",
        affords={"fork", "echo"},
        tags={"quarry", "adventure"},
    ),
    "shed_hill": Setting(
        id="shed_hill",
        place="the cinder hill behind the shed",
        scene="wooden planks, a rusty cart, and a windy path that curled like a dragon tail",
        goal="a tiny flag stuck in the top of the hill",
        affords={"wind", "fork"},
        tags={"hill", "adventure"},
    ),
    "orchard_wall": Setting(
        id="orchard_wall",
        place="the old orchard wall at the edge of the field",
        scene="fallen apples, cracked white stones, and narrow turns between bushes",
        goal="a secret arch in the broken wall",
        affords={"hedge", "fork"},
        tags={"orchard", "adventure"},
    ),
}

OBSTACLES = {
    "fork": Obstacle(
        id="fork",
        label="a fork in the path",
        hook="the path split in two and both ways looked brave enough to be right",
        danger="if they chose different ways, they could circle around and miss each other",
        solve="marking arrows where the path split",
        severity=2,
        tags={"path", "direction"},
    ),
    "echo": Obstacle(
        id="echo",
        label="an echoing turn",
        hook="their voices bounced off the stone and came back from the wrong direction",
        danger="echoes could make the way home feel mixed up",
        solve="drawing a dark trail line on the wall",
        severity=2,
        tags={"echo", "direction"},
    ),
    "wind": Obstacle(
        id="wind",
        label="a windy bend",
        hook="a gust snatched their paper sketch and sent it tumbling away",
        danger="without a map, every bend looked almost the same",
        solve="drawing fresh arrow marks on the boards",
        severity=1,
        tags={"wind", "direction"},
    ),
    "hedge": Obstacle(
        id="hedge",
        label="a hedge maze turn",
        hook="the narrow gaps between the bushes all looked alike",
        danger="one wrong turn could send them back where they started",
        solve="making dark signs on the pale wall stones",
        severity=1,
        tags={"hedge", "direction"},
    ),
}

SURFACES = {
    "pale_stone": Surface(
        id="pale_stone",
        label="pale stone",
        phrase="the pale stone beside the trail",
        markable=True,
        reason="dark coal shows clearly on pale stone",
        tags={"stone", "marking"},
    ),
    "dry_planks": Surface(
        id="dry_planks",
        label="dry planks",
        phrase="the dry wooden planks nearby",
        markable=True,
        reason="coal can leave dark arrow marks on dry wood",
        tags={"wood", "marking"},
    ),
    "white_wall": Surface(
        id="white_wall",
        label="a white wall",
        phrase="the cracked white wall by the path",
        markable=True,
        reason="coal leaves easy-to-see lines on a white wall",
        tags={"wall", "marking"},
    ),
    "wet_rock": Surface(
        id="wet_rock",
        label="wet rock",
        phrase="the wet black rock nearby",
        markable=False,
        reason="wet dark rock would hide the coal marks",
        tags={"rock"},
    ),
    "black_pipe": Surface(
        id="black_pipe",
        label="a black pipe",
        phrase="the old black pipe near the trail",
        markable=False,
        reason="black metal would not show dark coal arrows well",
        tags={"metal"},
    ),
}

CALM_TRAITS = {"gentle", "steady", "careful"}
TRAITS = ["gentle", "steady", "careful", "bossy", "hasty", "proud"]

GIRL_NAMES = ["Lila", "Mina", "Tess", "Nora", "Ivy", "Poppy", "June", "Ava"]
BOY_NAMES = ["Ben", "Arlo", "Finn", "Theo", "Max", "Jude", "Eli", "Leo"]


def hazard_explanation(setting: Setting, obstacle: Obstacle, surface: Surface) -> str:
    if obstacle.id not in setting.affords:
        choices = ", ".join(sorted(setting.affords))
        return (
            f"(No story: {setting.place} does not fit {obstacle.label}. "
            f"Try an obstacle this setting supports: {choices}.)"
        )
    return (
        f"(No story: {surface.label} is a poor place to mark with coal because "
        f"{surface.reason}. This adventure needs a surface where trail arrows can be seen.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for obstacle_id, obstacle in OBSTACLES.items():
            if obstacle_id not in setting.affords:
                continue
            for surface_id, surface in SURFACES.items():
                if surface.markable:
                    combos.append((setting_id, obstacle_id, surface_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    if params.peacemaker_trait in CALM_TRAITS and obstacle.severity <= 1:
        return "early"
    return "late"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def pair_noun(leader: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "boy" and partner.type == "boy":
            return "two brothers"
        if leader.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("team").meters["separated"] += 1
    propagate(sim, narrate=False)
    return {
        "lostness": sim.get("trail").meters["lostness"],
        "fear": sum(sim.get(kid_id).memes["fear"] for kid_id in ("leader", "partner")),
    }


def introduce(world: World, leader: Entity, partner: Entity, setting: Setting) -> None:
    relation = world.facts["relation"]
    world.say(
        f"One bright afternoon, {leader.id} and {partner.id}, {pair_noun(leader, partner, relation)}, "
        f"set out on an adventure at {setting.place}. Around them were {setting.scene}."
    )
    world.say(
        f"They called themselves the Cliff-Finder Club, and their mission was to reach {setting.goal} before snack time."
    )


def find_coal(world: World, leader: Entity, partner: Entity) -> None:
    coal = world.get("coal")
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"Near the start of the trail, {leader.id} spotted a shiny lump of coal half hidden in the dust. "
        f"{leader.pronoun().capitalize()} picked it up, and its black sparkle made it feel like pirate treasure."
    )
    coal.meters["found"] += 1
    world.say(
        f'"Look!" {leader.id} said. "A real treasure stone." But {partner.id} looked at the path and saw another use for it.'
    )


def argue(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, surface: Surface) -> None:
    lead_pos = leader.pronoun("possessive")
    part_pos = partner.pronoun("possessive")
    leader.memes["pride"] += 1
    leader.memes["hurt"] += 1
    partner.memes["pride"] += 1
    partner.memes["hurt"] += 1
    pred = predict_trouble(world)
    world.facts["predicted_lostness"] = pred["lostness"]
    world.say(
        f"Soon they came to {obstacle.label}, and {obstacle.hook}. "
        f'{partner.id} said, "We should use the coal for {obstacle.solve} on {surface.phrase}."'
    )
    world.say(
        f'{leader.id} hugged the coal to {lead_pos} chest. "No, it is my treasure." '
        f'{partner.id} frowned. "{obstacle.danger.capitalize()}."'
    )
    if pred["lostness"] >= THRESHOLD:
        world.say(
            f"For a moment, each one felt more busy being right than staying together."
        )


def early_reconciliation(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, surface: Surface) -> None:
    leader.memes["apology"] += 1
    partner.memes["forgiveness"] += 1
    world.say(
        f"Then {partner.id} took a slow breath. {partner.pronoun().capitalize()} touched {leader.pronoun('possessive')} sleeve and said, "
        f'"I do not want to grab it away. I just do not want us to get mixed up at {obstacle.label}."'
    )
    world.say(
        f"{leader.id} looked from the coal to {surface.phrase}. The black lump was still treasure, but it could be useful treasure."
    )
    world.say(
        f'"I am sorry I only thought about keeping it," {leader.id} said. "We can share it." '
        f'"Thank you," said {partner.id}, and the tight feeling between them softened.'
    )
    propagate(world, narrate=False)


def separate(world: World, leader: Entity, partner: Entity) -> None:
    world.get("team").meters["separated"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But nobody apologized in time. {leader.id} marched one way with the coal, and {partner.id} took the other way for three quick steps."
    )


def late_reconciliation(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, surface: Surface) -> None:
    trail = world.get("trail")
    leader.memes["apology"] += 1
    partner.memes["forgiveness"] += 1
    fear_line = ""
    if trail.meters["lostness"] >= THRESHOLD:
        fear_line = (
            f" The quiet suddenly felt much bigger, and both children heard how lonely adventure could sound when they were cross."
        )
    world.say(
        f"At once, {leader.id} could not tell which bend was the brave one and which bend was the wrong one.{fear_line}"
    )
    world.say(
        f'{leader.id} stopped and called, "{partner.id}, wait. I am sorry. The coal matters less than staying together."'
    )
    world.say(
        f'{partner.id} hurried back and nodded. "I was cross too," {partner.pronoun()} said. '
        f'"Let us use it together on {surface.phrase}."'
    )
    propagate(world, narrate=False)


def mark_trail(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, surface: Surface) -> None:
    coal = world.get("coal")
    trail = world.get("trail")
    team = world.get("team")
    coal.meters["shared"] += 1
    trail.meters["marked"] += 1
    team.meters["separated"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"So {leader.id} held the coal, and {partner.id} pointed to {surface.phrase}. Together they drew dark arrows for {obstacle.solve}."
    )
    world.say(
        f"Each mark turned the path from a muddle into a plan. Now the way back could not hide from them."
    )


def reach_goal(world: World, leader: Entity, partner: Entity, setting: Setting) -> None:
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    leader.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f"With the trail marked, they reached {setting.goal}. From there, the whole little world looked open and friendly again."
    )


def ending_image(world: World, leader: Entity, partner: Entity, parent: Entity) -> None:
    relation = world.facts["relation"]
    pw = parent.label_word
    if relation == "siblings":
        relation_line = "When they climbed down, they were still dusty, still excited, and brother-and-sister close again." if leader.type != partner.type else "When they climbed down, they were still dusty, still excited, and sibling-close again."
    else:
        relation_line = "When they climbed down, they were still dusty, still excited, and good friends again."
    world.say(relation_line)
    world.say(
        f"Back home, they used the last smudge of coal to draw a map of the adventure for their {pw}. "
        f"This time, both names stood side by side at the top: Trail Finder and Arrow Maker."
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    surface: Surface,
    leader_name: str = "Ben",
    leader_gender: str = "boy",
    partner_name: str = "Lila",
    partner_gender: str = "girl",
    relation: str = "friends",
    parent_type: str = "mother",
    peacemaker_trait: str = "gentle",
) -> World:
    world = World()
    leader = world.add(Entity(
        id="leader",
        kind="character",
        type=leader_gender,
        label=leader_name,
        role="leader",
        traits=["bold"],
        attrs={"name": leader_name, "relation": relation},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        traits=[peacemaker_trait],
        attrs={"name": partner_name, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    world.add(Entity(id="coal", type="coal", label="coal", tags={"coal"}))
    world.add(Entity(id="trail", type="trail", label="the trail"))
    world.add(Entity(id="team", type="team", label="the team"))

    leader.memes["pride"] = 0.0
    leader.memes["hurt"] = 0.0
    leader.memes["fear"] = 0.0
    leader.memes["apology"] = 0.0
    leader.memes["trust"] = 1.0
    leader.memes["hope"] = 0.0
    partner.memes["pride"] = 0.0
    partner.memes["hurt"] = 0.0
    partner.memes["fear"] = 0.0
    partner.memes["forgiveness"] = 0.0
    partner.memes["trust"] = 1.0
    partner.memes["hope"] = 0.0

    world.facts.update(
        setting=setting,
        obstacle=obstacle,
        surface=surface,
        relation=relation,
        leader=leader,
        partner=partner,
        parent=parent,
        leader_name=leader_name,
        partner_name=partner_name,
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            obstacle=obstacle.id,
            surface=surface.id,
            leader_name=leader_name,
            leader_gender=leader_gender,
            partner_name=partner_name,
            partner_gender=partner_gender,
            relation=relation,
            parent=parent_type,
            peacemaker_trait=peacemaker_trait,
        )),
    )

    introduce(world, leader, partner, setting)
    find_coal(world, leader, partner)

    world.para()
    argue(world, leader, partner, obstacle, surface)

    if world.facts["outcome"] == "early":
        early_reconciliation(world, leader, partner, obstacle, surface)
    else:
        separate(world, leader, partner)
        late_reconciliation(world, leader, partner, obstacle, surface)

    world.para()
    mark_trail(world, leader, partner, obstacle, surface)
    reach_goal(world, leader, partner, setting)

    world.para()
    ending_image(world, leader, partner, parent)

    world.facts.update(
        reconciled=world.get("team").memes["harmony"] >= THRESHOLD,
        used_coal=world.get("coal").meters["shared"] >= THRESHOLD,
        was_lost=world.get("trail").meters["lostness"] >= THRESHOLD or world.facts["outcome"] == "late",
        marks_visible=surface.markable,
    )
    return world


KNOWLEDGE = {
    "coal": [
        (
            "What is coal?",
            "Coal is a black rock that came from plants long, long ago. It can leave dark marks when you rub it on the right surface."
        )
    ],
    "direction": [
        (
            "Why do trail marks help on an adventure?",
            "Trail marks help you remember which way you went. A clear sign can turn a confusing path into one you can follow safely."
        )
    ],
    "sorry": [
        (
            "Why is saying sorry important after a quarrel?",
            "Saying sorry helps mend hurt feelings. It shows you care more about the other person than about winning."
        )
    ],
    "forgive": [
        (
            "What does it mean to forgive someone?",
            "To forgive means you choose to stop holding on to the hurt after someone truly says sorry. It makes room for people to work together again."
        )
    ],
    "stone": [
        (
            "Why does dark coal show up on pale stone?",
            "The dark color stands out against the light surface. That makes arrows and marks easier to see."
        )
    ],
    "wood": [
        (
            "Can you draw with coal on dry wood?",
            "Yes, dry wood can catch a dark smudge from coal. That can make a simple sign if the wood is light enough."
        )
    ],
    "wall": [
        (
            "Why would a white wall be good for trail signs?",
            "A white wall is bright, so dark marks show clearly on it. That makes it easier to notice arrows while walking."
        )
    ],
    "wind": [
        (
            "Why can wind make an adventure harder?",
            "Wind can blow away papers, hats, and little maps. Then you need another way to remember the path."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after it hits something hard, like a wall. It can make voices seem to come from the wrong place."
        )
    ],
}

KNOWLEDGE_ORDER = ["coal", "direction", "sorry", "forgive", "stone", "wood", "wall", "wind", "echo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    setting = f["setting"]
    obstacle = f["obstacle"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "coal" and ends in reconciliation.',
        f"Tell a gentle adventure where {leader.attrs['name']} and {partner.attrs['name']} quarrel during an expedition at {setting.place}, then make peace by solving {obstacle.label} together.",
        "Write a child-facing story where a disagreement turns into teamwork, and the ending image proves the children are friends again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    parent = f["parent"]
    setting = f["setting"]
    obstacle = f["obstacle"]
    surface = f["surface"]
    outcome = f["outcome"]
    relation = f["relation"]
    lead_name = leader.attrs["name"]
    part_name = partner.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(leader, partner, relation)}, {lead_name} and {part_name}. They set out on a small adventure together."
        ),
        (
            "What did the children find near the trail?",
            f"They found a shiny lump of coal. At first it felt like treasure to {lead_name}, and that is what started the quarrel."
        ),
        (
            f"Why did {part_name} want to use the coal?",
            f"{part_name} wanted to use the coal to make trail marks at {obstacle.label}. {part_name} knew that clear signs on {surface.phrase} could help them find the right way."
        ),
        (
            "What was the problem in the middle of the story?",
            f"The children argued over whether the coal should be kept or used. Because of that quarrel, {obstacle.danger}, which made the adventure feel risky instead of fun."
        ),
    ]
    if outcome == "early":
        qa.append(
            (
                "Did they make peace before getting into trouble?",
                f"Yes. {part_name} spoke gently, and {lead_name} realized the coal could be shared instead of hoarded. That apology softened the hurt before they truly lost their way."
            )
        )
    else:
        qa.append(
            (
                "What made them finally reconcile?",
                f"They started to separate at the confusing part of the trail, and the adventure suddenly felt lonely and unsafe. That scare helped {lead_name} say sorry, and {part_name} forgave {leader.pronoun('object')} so they could work together again."
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They used the coal together to draw dark arrows for {obstacle.solve}. The marks turned a confusing path into a clear one, so teamwork solved both the adventure problem and the hurt feelings."
        )
    )
    qa.append(
        (
            "How can you tell the children were reconciled at the end?",
            f"At the end they made one map together for their {parent.label_word}, with both names on it. That ending image shows they were proud of the adventure together instead of pulling apart."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"coal", "direction", "sorry", "forgive"}
    surface = world.facts["surface"]
    obstacle = world.facts["obstacle"]
    if surface.id == "pale_stone":
        tags.add("stone")
    elif surface.id == "dry_planks":
        tags.add("wood")
    elif surface.id == "white_wall":
        tags.add("wall")
    if obstacle.id == "wind":
        tags.add("wind")
    if obstacle.id == "echo":
        tags.add("echo")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="shed_hill",
        obstacle="wind",
        surface="dry_planks",
        leader_name="Ben",
        leader_gender="boy",
        partner_name="Lila",
        partner_gender="girl",
        relation="friends",
        parent="mother",
        peacemaker_trait="gentle",
    ),
    StoryParams(
        setting="orchard_wall",
        obstacle="hedge",
        surface="white_wall",
        leader_name="Nora",
        leader_gender="girl",
        partner_name="June",
        partner_gender="girl",
        relation="siblings",
        parent="father",
        peacemaker_trait="steady",
    ),
    StoryParams(
        setting="quarry_path",
        obstacle="echo",
        surface="pale_stone",
        leader_name="Arlo",
        leader_gender="boy",
        partner_name="Mina",
        partner_gender="girl",
        relation="friends",
        parent="mother",
        peacemaker_trait="bossy",
    ),
    StoryParams(
        setting="shed_hill",
        obstacle="fork",
        surface="dry_planks",
        leader_name="Ivy",
        leader_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        relation="siblings",
        parent="father",
        peacemaker_trait="hasty",
    ),
]


ASP_RULES = r"""
valid(S,O,U) :- setting(S), obstacle(O), surface(U), affords(S,O), markable(U).

early_reconcile :- chosen_trait(T), calm_trait(T), chosen_obstacle(O), severity(O,V), V <= 1.
outcome(early) :- early_reconcile.
outcome(late)  :- not early_reconcile.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for obstacle_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("severity", obstacle_id, obstacle.severity))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        if surface.markable:
            lines.append(asp.fact("markable", surface_id))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_trait", params.peacemaker_trait),
        asp.fact("chosen_obstacle", params.obstacle),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small adventure, a quarrel over coal, and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--leader-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--leader-name")
    ap.add_argument("--partner-name")
    ap.add_argument("--peacemaker-trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle:
        if args.obstacle not in SETTINGS[args.setting].affords:
            raise StoryError(hazard_explanation(SETTINGS[args.setting], OBSTACLES[args.obstacle], next(iter(SURFACES.values()))))
    if args.surface:
        surface = SURFACES[args.surface]
        if not surface.markable:
            setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
            obstacle = OBSTACLES[args.obstacle] if args.obstacle else OBSTACLES[next(iter(setting.affords))]
            raise StoryError(hazard_explanation(setting, obstacle, surface))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.surface is None or combo[2] == args.surface)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, surface_id = rng.choice(sorted(combos))
    leader_gender = args.leader_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    leader_name = args.leader_name or _pick_name(rng, leader_gender)
    partner_name = args.partner_name or _pick_name(rng, partner_gender, avoid=leader_name)
    relation = args.relation or rng.choice(["siblings", "friends"])
    parent = args.parent or rng.choice(["mother", "father"])
    peacemaker_trait = args.peacemaker_trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        surface=surface_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        relation=relation,
        parent=parent,
        peacemaker_trait=peacemaker_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.surface not in SURFACES:
        raise StoryError(f"(Unknown surface: {params.surface})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.relation not in {"siblings", "friends"}:
        raise StoryError(f"(Unknown relation: {params.relation})")
    if params.peacemaker_trait not in TRAITS:
        raise StoryError(f"(Unknown peacemaker trait: {params.peacemaker_trait})")

    setting = SETTINGS[params.setting]
    obstacle = OBSTACLES[params.obstacle]
    surface = SURFACES[params.surface]
    if params.obstacle not in setting.affords or not surface.markable:
        raise StoryError(hazard_explanation(setting, obstacle, surface))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        surface=surface,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        relation=params.relation,
        parent_type=params.parent,
        peacemaker_trait=params.peacemaker_trait,
    )
    leader = world.facts["leader"]
    partner = world.facts["partner"]
    story = world.render().replace("leader", leader.attrs["name"]).replace("partner", partner.attrs["name"])
    story = story.replace("parent", world.facts["parent"].label_word)
    # Restore true names in dialogue-bearing narrative while avoiding internal ids.
    story = story.replace(world.facts["leader"].id, leader.attrs["name"])
    story = story.replace(world.facts["partner"].id, partner.attrs["name"])
    sample = StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    sample.story = sample.story.replace("  ", " ")
    return sample


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
        print(f"{len(combos)} compatible (setting, obstacle, surface) combos:\n")
        for setting_id, obstacle_id, surface_id in combos:
            print(f"  {setting_id:12} {obstacle_id:8} {surface_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = (
                f"### {p.leader_name} & {p.partner_name}: {p.setting}, {p.obstacle}, "
                f"{p.surface} ({outcome_of(p)} reconciliation)"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
