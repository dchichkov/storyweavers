#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pathetic_cautionary_teamwork_bad_ending_adventure.py
================================================================================

A standalone story world for a small adventure tale about two children who try to
reach a tiny island fort. They need teamwork to cross the water, but a warning
about a pathetic old raft may or may not be heeded. Some variants end happily;
others end sadly when the cargo is lost and the adventure must be given up.

Run it
------
    python storyworlds/worlds/gpt-5.4/pathetic_cautionary_teamwork_bad_ending_adventure.py
    python storyworlds/worlds/gpt-5.4/pathetic_cautionary_teamwork_bad_ending_adventure.py --waterway river --craft old_raft
    python storyworlds/worlds/gpt-5.4/pathetic_cautionary_teamwork_bad_ending_adventure.py --craft tube
    python storyworlds/worlds/gpt-5.4/pathetic_cautionary_teamwork_bad_ending_adventure.py --all
    python storyworlds/worlds/gpt-5.4/pathetic_cautionary_teamwork_bad_ending_adventure.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
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
SENSE_MIN = 2
CAUTIOUS_TRAITS = {"careful", "steady", "patient", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    floating: bool = False
    waterproof: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "ranger_woman"}
        male = {"boy", "father", "man", "ranger_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
        }.get(self.type, self.type)
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
class Theme:
    id: str
    scene: str
    goal: str
    fort: str
    cheer: str
    ending: str
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
class Waterway:
    id: str
    label: str
    phrase: str
    current: int
    shore: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    purpose: str
    dry_word: str
    floating_desc: str
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
class Craft:
    id: str
    label: str
    phrase: str
    capacity: int
    stability: int
    sense: int
    launch_text: str
    recover_text: str
    pathetic: bool = False
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


def _r_wobble_fear(world: World) -> list[str]:
    out: list[str] = []
    craft = world.entities.get("craft")
    water = world.entities.get("water")
    if not craft or not water:
        return out
    if craft.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    water.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_tip_soak(world: World) -> list[str]:
    out: list[str] = []
    craft = world.entities.get("craft")
    cargo = world.entities.get("cargo")
    water = world.entities.get("water")
    if not craft or not cargo or not water:
        return out
    if craft.meters["tipped"] < THRESHOLD:
        return out
    sig = ("tipped",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["wet"] += 1
    cargo.meters["overboard"] += 1
    water.meters["danger"] += 1
    for kid in world.kids():
        kid.meters["wet"] += 1
        kid.memes["fear"] += 1
    out.append("__tipped__")
    return out


def _r_lost_cargo(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.entities.get("cargo")
    if not cargo:
        return out
    if cargo.meters["overboard"] < THRESHOLD:
        return out
    sig = ("lost",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cargo.meters["lost"] += 1
    out.append("__lost__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble_fear", tag="physical", apply=_r_wobble_fear),
    Rule(name="tip_soak", tag="physical", apply=_r_tip_soak),
    Rule(name="lost_cargo", tag="physical", apply=_r_lost_cargo),
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
        for s in produced:
            world.say(s)
    return produced


def teamwork_power(relation: str, trust: int, trait: str) -> int:
    power = 1
    if relation == "siblings":
        power += 1
    if trust >= 6:
        power += 1
    if trait in CAUTIOUS_TRAITS:
        power += 1
    return power


def crossing_severity(water: Waterway, cargo: Cargo, craft: Craft) -> int:
    return water.current + cargo.weight + max(0, 2 - craft.stability)


def crossing_success(craft: Craft, water: Waterway, cargo: Cargo,
                     relation: str, trust: int, trait: str) -> bool:
    return craft.stability + teamwork_power(relation, trust, trait) > crossing_severity(water, cargo, craft)


def would_avert(relation: str, leader_age: int, partner_age: int, trait: str) -> bool:
    return relation == "siblings" and partner_age > leader_age and trait in CAUTIOUS_TRAITS


def sensible_crafts() -> list[Craft]:
    return [c for c in CRAFTS.values() if c.sense >= SENSE_MIN]


def can_carry(craft: Craft, cargo: Cargo) -> bool:
    return craft.capacity >= cargo.weight


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for water_id, water in WATERWAYS.items():
            for cargo_id, cargo in CARGOS.items():
                for craft_id, craft in CRAFTS.items():
                    if craft.sense >= SENSE_MIN and can_carry(craft, cargo):
                        combos.append((theme_id, water_id, cargo_id, craft_id))
    return combos


def predict_crossing(world: World, water_id: str, cargo_id: str, craft_id: str,
                     relation: str, trust: int, trait: str) -> dict:
    sim = world.copy()
    craft = sim.get("craft")
    cargo = sim.get("cargo")
    water = sim.get("water")
    craft_cfg = CRAFTS[craft_id]
    cargo_cfg = CARGOS[cargo_id]
    water_cfg = WATERWAYS[water_id]
    craft.meters["wobble"] = float(max(0, crossing_severity(water_cfg, cargo_cfg, craft_cfg) - teamwork_power(relation, trust, trait)))
    if not crossing_success(craft_cfg, water_cfg, cargo_cfg, relation, trust, trait):
        craft.meters["tipped"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("water").meters["danger"],
        "lost": sim.get("cargo").meters["lost"] >= THRESHOLD,
    }


def setup_adventure(world: World, leader: Entity, partner: Entity, theme: Theme,
                    water: Waterway, cargo: Cargo) -> None:
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    partner.memes["teamwork"] = 1.0
    leader.memes["teamwork"] = 1.0
    world.say(
        f"After breakfast, {leader.id} and {partner.id} turned the edge of the park into {theme.scene}. "
        f"Beyond {water.phrase}, they could see {theme.fort} waiting in the sun."
    )
    world.say(
        f'"{theme.cheer}!" {leader.id} cried. They had promised to bring {cargo.phrase} there, {cargo.purpose}.'
    )


def need_crossing(world: World, partner: Entity, water: Waterway) -> None:
    world.say(
        f"But {water.label} rushed between the children and the little fort. {water.shore}"
    )
    world.say(
        f'{partner.id} squinted at the water. "We can only do this if we cross together," {partner.pronoun()} said.'
    )


def tempt(world: World, leader: Entity, craft: Craft) -> None:
    leader.memes["bravado"] += 1
    if craft.pathetic:
        world.say(
            f"Near the bank sat {craft.phrase}. It looked pathetic, but to {leader.id} it still looked like adventure."
        )
    else:
        world.say(
            f"Near the bank waited {craft.phrase}, bobbing softly against the reeds."
        )
    world.say(f'"Let\'s use {craft.label}!" {leader.id} said.')


def warn(world: World, partner: Entity, leader: Entity, ranger: Entity,
         water: Waterway, cargo: Cargo, craft: Craft, relation: str, trust: int, trait: str) -> None:
    pred = predict_crossing(world, water.id, cargo.id, craft.id, relation, trust, trait)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_loss"] = pred["lost"]
    partner.memes["caution"] += 1
    extra = ""
    if craft.pathetic:
        extra = " It looked too thin and shaky for a real crossing."
    world.say(
        f'{partner.id} shook {partner.pronoun("possessive")} head. "The ranger said not to trust that raft.{extra} '
        f'If {cargo.label} goes into the water, our whole trip is spoiled."'
    )
    if pred["lost"]:
        world.say(
            f'{ranger.label_word.capitalize()} stood by the sign and added, "A team should use good gear, not brave words."'
        )


def defy(world: World, leader: Entity, partner: Entity, craft: Craft) -> None:
    leader.memes["defiance"] += 1
    if leader.attrs.get("relation") == "siblings" and leader.age > partner.age:
        world.say(
            f'"We can handle it," {leader.id} said. Because {leader.id} was the older one, {partner.id} could not stop {leader.pronoun("object")}.'
        )
    else:
        world.say(f'"We can handle it," {leader.id} said, and hurried toward {craft.label}.')


def back_down(world: World, leader: Entity, partner: Entity, ranger: Entity,
              theme: Theme, cargo: Cargo) -> None:
    leader.memes["relief"] += 1
    partner.memes["relief"] += 1
    world.say(
        f'{leader.id} stared at the water, then at {partner.id}, and let out a long breath. "All right," {leader.pronoun()} said. "Not that way."'
    )
    world.say(
        f'{ranger.label_word.capitalize()} smiled and led them to a sturdy rowboat tied farther downstream. Soon the team was heading for {theme.fort} with {cargo.label} safe between them.'
    )


def launch(world: World, leader: Entity, partner: Entity, water: Waterway,
           cargo: Cargo, craft: Craft, relation: str, trust: int, trait: str) -> None:
    world.say(craft.launch_text)
    world.say(
        f"{leader.id} knelt in front while {partner.id} kept the {cargo.label} hugged tight. "
        f"They tried to match each other's moves like a real adventure team."
    )
    wobble = max(0, crossing_severity(water, cargo, craft) - teamwork_power(relation, trust, trait))
    world.get("craft").meters["wobble"] = float(wobble)
    propagate(world, narrate=False)
    if wobble > 0:
        world.say(
            f"The water slapped the sides, and {craft.label} wobbled so hard that both children grabbed for balance."
        )
    else:
        world.say(
            f"Their teamwork made the crossing feel steady at first, and the little fort seemed to float closer."
        )


def cross_successfully(world: World, leader: Entity, partner: Entity, theme: Theme,
                       cargo: Cargo) -> None:
    world.get("cargo").meters["delivered"] += 1
    leader.memes["pride"] += 1
    partner.memes["pride"] += 1
    world.say(
        f"Stroke by stroke, the team made it across. They climbed onto the far bank and carried {cargo.phrase} up to {theme.fort} together."
    )
    world.say(
        f"There they set it down proudly, and the whole morning felt bigger because they had used teamwork and listened before acting."
    )
    world.say(theme.ending)


def tip_and_lose(world: World, leader: Entity, partner: Entity, ranger: Entity,
                 cargo: Cargo, craft: Craft, theme: Theme) -> None:
    world.get("craft").meters["tipped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then one side dipped, the other side jumped, and {craft.label} tipped. Cold water splashed over their knees as {cargo.floating_desc}"
    )
    world.say(
        f'{ranger.label_word.capitalize()} ran along the bank and threw a rope. The children worked together to catch it, and that teamwork got them safely back to shore.'
    )
    leader.memes["regret"] += 1
    partner.memes["regret"] += 1
    leader.memes["fear"] = max(leader.memes["fear"], 1.0)
    partner.memes["fear"] = max(partner.memes["fear"], 1.0)
    world.say(
        f"But the adventure was over. {cargo.label.capitalize()} was gone, and {theme.fort} waited across the water with nobody left to bring the promised gift."
    )
    world.say(
        f"Walking home in wet shoes, {leader.id} looked smaller than before. Even the game felt quiet now, because brave teams need safe plans as much as brave hearts."
    )


THEMES = {
    "island_fort": Theme(
        id="island_fort",
        scene="an explorer kingdom",
        goal="the island fort",
        fort="a tiny stick fort on the island",
        cheer="Fort team, forward",
        ending="At sunset they looked back at the tiny fort and knew adventure felt best when courage and care traveled together.",
    ),
    "reed_castle": Theme(
        id="reed_castle",
        scene="a marsh expedition",
        goal="the reed castle",
        fort="a reed-walled castle on a grassy bump",
        cheer="Castle team, forward",
        ending="As the reeds rustled around them, the children grinned at the castle and at the good choice that had helped them reach it.",
    ),
    "treasure_post": Theme(
        id="treasure_post",
        scene="a treasure quest",
        goal="the treasure post",
        fort="a little treasure post made from driftwood",
        cheer="Treasure team, forward",
        ending="They planted their treasure at the post and learned that the best adventures leave everyone smiling at the end.",
    ),
}

WATERWAYS = {
    "creek": Waterway(
        id="creek",
        label="the creek",
        phrase="the bright creek",
        current=1,
        shore="Pebbles clicked under the water, and the current tugged harder in the middle.",
        tags={"water", "creek"},
    ),
    "river": Waterway(
        id="river",
        label="the river",
        phrase="the brown river",
        current=3,
        shore="The middle swirled fast, and even the reeds leaned away from it.",
        tags={"water", "river"},
    ),
    "channel": Waterway(
        id="channel",
        label="the marsh channel",
        phrase="the narrow marsh channel",
        current=2,
        shore="The water looked calm near the edge, but it slid quickly between the reeds.",
        tags={"water", "channel"},
    ),
}

CARGOS = {
    "flag": Cargo(
        id="flag",
        label="flag",
        phrase="a bright camp flag",
        weight=1,
        purpose="so the fort would have something to wave above its roof",
        dry_word="dry",
        floating_desc="the bright flag slipped from their hands and went spinning downstream.",
        tags={"flag", "teamwork"},
    ),
    "snack_basket": Cargo(
        id="snack_basket",
        label="snack basket",
        phrase="a picnic basket of apples and buns",
        weight=2,
        purpose="for the hungry fort guards they imagined inside",
        dry_word="dry",
        floating_desc="the basket bobbed once, tipped open, and sent apples swirling away.",
        tags={"basket", "food", "teamwork"},
    ),
    "map_tube": Cargo(
        id="map_tube",
        label="map tube",
        phrase="a long tube holding the treasure map",
        weight=1,
        purpose="so their map would stay safe until it reached the fort",
        dry_word="dry",
        floating_desc="the map tube shot away like a stick and vanished into the reeds.",
        tags={"map", "teamwork"},
    ),
}

CRAFTS = {
    "old_raft": Craft(
        id="old_raft",
        label="the old raft",
        phrase="a pathetic old raft made from three logs and fraying rope",
        capacity=2,
        stability=1,
        sense=2,
        launch_text="They pushed the old raft into the edge of the water and climbed on before it could drift away.",
        recover_text="the old raft bumped back against the muddy bank",
        pathetic=True,
        tags={"raft", "water"},
    ),
    "rowboat": Craft(
        id="rowboat",
        label="the rowboat",
        phrase="a sturdy rowboat with two smooth oars",
        capacity=3,
        stability=3,
        sense=3,
        launch_text="They untied the rowboat, settled carefully, and dipped the oars together.",
        recover_text="the rowboat rode the ripples and waited for the next trip",
        pathetic=False,
        tags={"boat", "water"},
    ),
    "canoe": Craft(
        id="canoe",
        label="the canoe",
        phrase="a narrow canoe with fresh blue paint",
        capacity=2,
        stability=2,
        sense=3,
        launch_text="They slid the canoe off the grass and stepped in one at a time, just as the ranger had shown them before.",
        recover_text="the canoe skimmed neatly back toward shore",
        pathetic=False,
        tags={"canoe", "water"},
    ),
    "tube": Craft(
        id="tube",
        label="the rubber tube",
        phrase="a single rubber tube left near the dock",
        capacity=1,
        stability=0,
        sense=1,
        launch_text="They dragged the rubber tube to the water.",
        recover_text="the tube bounced on the bank",
        pathetic=False,
        tags={"tube", "water"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ava", "Zoe", "Ivy", "Ruby", "Tess"]
BOY_NAMES = ["Finn", "Leo", "Max", "Owen", "Sam", "Eli", "Theo", "Ben"]
TRAITS = ["careful", "steady", "patient", "sensible", "curious", "bold"]


@dataclass
class StoryParams:
    theme: str
    waterway: str
    cargo: str
    craft: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    ranger: str
    ranger_gender: str
    trait: str
    relation: str = "friends"
    trust: int = 5
    leader_age: int = 6
    partner_age: int = 6
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
    "water": [
        (
            "Why can moving water be dangerous?",
            "Moving water keeps pushing even when it looks small. That steady push can tip light boats or carry things away."
        )
    ],
    "raft": [
        (
            "What is a raft?",
            "A raft is a simple floating platform, often made from logs or boards tied together. A weak raft can wobble or break if it is used the wrong way."
        )
    ],
    "boat": [
        (
            "Why is a sturdy boat safer than a weak raft?",
            "A sturdy boat is built to stay balanced in the water. Strong sides and better shape make it less likely to tip."
        )
    ],
    "canoe": [
        (
            "What is a canoe?",
            "A canoe is a narrow boat moved with paddles. People in a canoe have to balance carefully and work together."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people helping each other do one job together. Good teamwork is strongest when everyone also listens and plans carefully."
        )
    ],
    "flag": [
        (
            "What is a flag for?",
            "A flag is a piece of cloth that can show who a group is or mark a special place. People often carry one in games and celebrations."
        )
    ],
    "map": [
        (
            "What does a map do?",
            "A map helps people know where to go. If a map gets lost, it can be much harder to finish a trip."
        )
    ],
    "food": [
        (
            "Why should food stay dry and clean?",
            "Food should stay dry and clean so it is nice to eat. Wet or dirty food may be spoiled."
        )
    ],
    "ranger": [
        (
            "What does a ranger do?",
            "A ranger helps keep outdoor places safe. Rangers warn people about risks and help when someone gets in trouble."
        )
    ],
}
KNOWLEDGE_ORDER = ["water", "raft", "boat", "canoe", "teamwork", "flag", "map", "food", "ranger"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    theme = f["theme"]
    craft = f["craft_cfg"]
    cargo = f["cargo_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short adventure story for a 3-to-5-year-old about two children trying to reach {theme.goal} with teamwork. '
        f'Include the word "pathetic".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a cautionary adventure where {leader.id} wants to use {craft.label}, but {partner.id} stops the plan and the team chooses a safer crossing.",
            f"Write a gentle teamwork story where the children listen to a warning, protect {cargo.label}, and still reach the fort."
        ]
    if outcome == "crossed":
        return [
            base,
            f"Tell a story where {leader.id} and {partner.id} work together in {craft.label} and make it safely to the fort with {cargo.label}.",
            f"Write a teamwork adventure that warns children to use good gear before crossing water."
        ]
    return [
        base,
        f"Tell a cautionary adventure where {leader.id} and {partner.id} try to carry {cargo.label} across in {craft.label}, are rescued, but lose the cargo and the quest ends sadly.",
        f"Write a bad-ending teamwork story where the children are safe but learn that courage without a safe plan can ruin an adventure."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    ranger = f["ranger"]
    theme = f["theme"]
    water = f["water_cfg"]
    cargo = f["cargo_cfg"]
    craft = f["craft_cfg"]
    relation = f["relation"]
    pair = pair_noun(leader, partner, relation)
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.id} and {partner.id}, on an adventure to {theme.goal}. A ranger nearby warns them about the crossing."
        ),
        (
            "What were they trying to do?",
            f"They wanted to bring {cargo.phrase} to {theme.fort}. That gave the game a real mission and made the crossing feel important."
        ),
        (
            "Why did they need teamwork?",
            f"They had to cross {water.label} while keeping {cargo.label} safe. One child had to balance and the other had to protect the cargo, so they could not do it well alone."
        ),
        (
            f"Why did {partner.id} worry about {craft.label}?",
            f"{partner.id} worried because the crossing looked risky and the raft was weak for the job. If it tipped, {cargo.label} could be lost and the adventure would end badly."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed {leader.id}'s mind?",
                f"{leader.id} listened to {partner.id}'s warning and looked at the water more carefully. That moment of caution turned the team away from the unsafe raft."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended well because the children used a safer boat and still reached {theme.goal}. The ending shows that listening can save an adventure instead of spoiling it."
            )
        )
    elif outcome == "crossed":
        qa.append(
            (
                "How did they get across safely?",
                f"They matched their movements and shared the job instead of splashing in a hurry. Their teamwork and better balance helped the craft stay steady."
            )
        )
        qa.append(
            (
                "What lesson did they learn?",
                f"They learned that teamwork works best with sensible choices. Brave hearts helped, but safe gear mattered too."
            )
        )
    else:
        qa.append(
            (
                "Were the children safe in the end?",
                f"Yes. The ranger pulled them back to shore, and the children worked together to catch the rope. They were safe even though the quest was ruined."
            )
        )
        qa.append(
            (
                "Why is this a sad ending?",
                f"It is sad because {cargo.label} was lost and they could not finish the mission to {theme.goal}. The children walked home wiser, but their adventure did not get the ending they wanted."
            )
        )
        qa.append(
            (
                "What lesson did they learn?",
                f"They learned that courage by itself is not enough. A team must listen to warnings and choose safe tools before starting something risky."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["water_cfg"].tags) | set(f["cargo_cfg"].tags) | set(f["craft_cfg"].tags) | {"ranger"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("floating", e.floating), ("waterproof", e.waterproof)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(theme: Theme, water_cfg: Waterway, cargo_cfg: Cargo, craft_cfg: Craft,
         leader_name: str = "Finn", leader_gender: str = "boy",
         partner_name: str = "Maya", partner_gender: str = "girl",
         ranger_name: str = "Ranger Jo", ranger_gender: str = "ranger_woman",
         trait: str = "careful", relation: str = "friends",
         trust: int = 5, leader_age: int = 6, partner_age: int = 6) -> World:
    world = World()
    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            role="leader",
            age=leader_age,
            attrs={"relation": relation},
            traits=["bold"],
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            age=partner_age,
            attrs={"relation": relation},
            traits=[trait],
        )
    )
    ranger = world.add(
        Entity(
            id=ranger_name,
            kind="character",
            type=ranger_gender,
            role="ranger",
            label="the ranger",
        )
    )
    world.add(Entity(id="water", type="water", label=water_cfg.label))
    world.add(Entity(id="craft", type="craft", label=craft_cfg.label, floating=True))
    world.add(Entity(id="cargo", type="cargo", label=cargo_cfg.label, waterproof=False))

    world.facts["relation"] = relation
    world.facts["predicted_danger"] = 0
    world.facts["predicted_loss"] = False

    setup_adventure(world, leader, partner, theme, water_cfg, cargo_cfg)
    need_crossing(world, partner, water_cfg)

    world.para()
    tempt(world, leader, craft_cfg)
    warn(world, partner, leader, ranger, water_cfg, cargo_cfg, craft_cfg, relation, trust, trait)

    averted = would_avert(relation, leader_age, partner_age, trait)
    if averted:
        back_down(world, leader, partner, ranger, theme, cargo_cfg)
        world.para()
        cross_successfully(world, leader, partner, theme, cargo_cfg)
        outcome = "averted"
    else:
        defy(world, leader, partner, craft_cfg)
        world.para()
        launch(world, leader, partner, water_cfg, cargo_cfg, craft_cfg, relation, trust, trait)
        succeeded = crossing_success(craft_cfg, water_cfg, cargo_cfg, relation, trust, trait)
        world.para()
        if succeeded:
            cross_successfully(world, leader, partner, theme, cargo_cfg)
            outcome = "crossed"
        else:
            tip_and_lose(world, leader, partner, ranger, cargo_cfg, craft_cfg, theme)
            outcome = "lost"

    world.facts.update(
        leader=leader,
        partner=partner,
        ranger=ranger,
        theme=theme,
        water_cfg=water_cfg,
        cargo_cfg=cargo_cfg,
        craft_cfg=craft_cfg,
        outcome=outcome,
        trust=trust,
        trait=trait,
        averted=averted,
        delivered=world.get("cargo").meters["delivered"] >= THRESHOLD,
        lost=world.get("cargo").meters["lost"] >= THRESHOLD,
    )
    return world


def explain_rejection(craft: Craft, cargo: Cargo) -> str:
    if craft.sense < SENSE_MIN:
        better = ", ".join(sorted(c.id for c in sensible_crafts()))
        return (
            f"(Refusing craft '{craft.id}': it is too unsafe for this story world "
            f"(sense={craft.sense} < {SENSE_MIN}). Try one of these instead: {better}.)"
        )
    return (
        f"(No story: {craft.label} cannot reasonably carry {cargo.label}. "
        f"The craft capacity is too small for that cargo.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.leader_age, params.partner_age, params.trait):
        return "averted"
    if crossing_success(
        CRAFTS[params.craft],
        WATERWAYS[params.waterway],
        CARGOS[params.cargo],
        params.relation,
        params.trust,
        params.trait,
    ):
        return "crossed"
    return "lost"


ASP_RULES = r"""
sensible_craft(C) :- craft(C), sense(C,S), sense_min(M), S >= M.
carry_ok(Cr,Cg)   :- craft(Cr), cargo(Cg), capacity(Cr,Cap), weight(Cg,W), Cap >= W.
valid(T,W,Cg,Cr)  :- theme(T), waterway(W), cargo(Cg), sensible_craft(Cr), carry_ok(Cr,Cg).

cautioner_older   :- relation(siblings), leader_age(LA), partner_age(PA), PA > LA.
averted           :- cautioner_older, cautious_trait(T), trait(T).

team_power(1 + SB + TB + CB) :-
    relation_bonus(SB), trust_bonus(TB), cautious_bonus(CB).
relation_bonus(1) :- relation(siblings).
relation_bonus(0) :- not relation(siblings).
trust_bonus(1)    :- trust(T), T >= 6.
trust_bonus(0)    :- trust(T), T < 6.
cautious_bonus(1) :- trait(T), cautious_trait(T).
cautious_bonus(0) :- trait(T), not cautious_trait(T).

severity(Cur + W + Pen) :-
    chosen_waterway(Wa), current(Wa,Cur),
    chosen_cargo(Cg), weight(Cg,W),
    chosen_craft(Cr), stability(Cr,St), penalty(Pen), Pen = 2 - St, Pen > 0.
severity(Cur + W + 0) :-
    chosen_waterway(Wa), current(Wa,Cur),
    chosen_cargo(Cg), weight(Cg,W),
    chosen_craft(Cr), stability(Cr,St), St >= 2.

crossed :- not averted, chosen_craft(Cr), stability(Cr,St), team_power(TP), severity(SV), St + TP > SV.

outcome(averted) :- averted.
outcome(crossed) :- not averted, crossed.
outcome(lost)    :- not averted, not crossed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for wid, w in WATERWAYS.items():
        lines.append(asp.fact("waterway", wid))
        lines.append(asp.fact("current", wid, w.current))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("weight", cid, c.weight))
    for crid, cr in CRAFTS.items():
        lines.append(asp.fact("craft", crid))
        lines.append(asp.fact("capacity", crid, cr.capacity))
        lines.append(asp.fact("stability", crid, cr.stability))
        lines.append(asp.fact("sense", crid, cr.sense))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", tr))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_waterway", params.waterway),
        asp.fact("chosen_cargo", params.cargo),
        asp.fact("chosen_craft", params.craft),
        asp.fact("relation", params.relation),
        asp.fact("leader_age", params.leader_age),
        asp.fact("partner_age", params.partner_age),
        asp.fact("trait", params.trait),
        asp.fact("trust", params.trust),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
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
        sample = generate(CURATED[0])
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a teamwork adventure across water, with caution and possible loss."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--waterway", choices=WATERWAYS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.craft is not None:
        craft = CRAFTS[args.craft]
        if craft.sense < SENSE_MIN:
            cargo = CARGOS[args.cargo] if args.cargo else next(iter(CARGOS.values()))
            raise StoryError(explain_rejection(craft, cargo))
    if args.craft is not None and args.cargo is not None:
        craft = CRAFTS[args.craft]
        cargo = CARGOS[args.cargo]
        if not can_carry(craft, cargo):
            raise StoryError(explain_rejection(craft, cargo))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.waterway is None or combo[1] == args.waterway)
        and (args.cargo is None or combo[2] == args.cargo)
        and (args.craft is None or combo[3] == args.craft)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, water_id, cargo_id, craft_id = rng.choice(sorted(combos))
    leader_name, leader_gender = _pick_kid(rng)
    partner_name, partner_gender = _pick_kid(rng, avoid=leader_name)
    ranger_gender = rng.choice(["ranger_woman", "ranger_man"])
    ranger_name = "Ranger Jo" if ranger_gender == "ranger_woman" else "Ranger Bo"
    relation = args.relation or rng.choice(["siblings", "friends"])
    trait = args.trait or rng.choice(TRAITS)
    trust = rng.randint(1, 10)
    leader_age, partner_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        theme=theme_id,
        waterway=water_id,
        cargo=cargo_id,
        craft=craft_id,
        leader=leader_name,
        leader_gender=leader_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        ranger=ranger_name,
        ranger_gender=ranger_gender,
        trait=trait,
        relation=relation,
        trust=trust,
        leader_age=leader_age,
        partner_age=partner_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        water = WATERWAYS[params.waterway]
        cargo = CARGOS[params.cargo]
        craft = CRAFTS[params.craft]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None

    if craft.sense < SENSE_MIN:
        raise StoryError(explain_rejection(craft, cargo))
    if not can_carry(craft, cargo):
        raise StoryError(explain_rejection(craft, cargo))

    world = tell(
        theme=theme,
        water_cfg=water,
        cargo_cfg=cargo,
        craft_cfg=craft,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        ranger_name=params.ranger,
        ranger_gender=params.ranger_gender,
        trait=params.trait,
        relation=params.relation,
        trust=params.trust,
        leader_age=params.leader_age,
        partner_age=params.partner_age,
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


CURATED = [
    StoryParams(
        theme="island_fort",
        waterway="creek",
        cargo="flag",
        craft="old_raft",
        leader="Finn",
        leader_gender="boy",
        partner="Maya",
        partner_gender="girl",
        ranger="Ranger Jo",
        ranger_gender="ranger_woman",
        trait="careful",
        relation="friends",
        trust=8,
        leader_age=6,
        partner_age=6,
    ),
    StoryParams(
        theme="reed_castle",
        waterway="river",
        cargo="snack_basket",
        craft="old_raft",
        leader="Leo",
        leader_gender="boy",
        partner="Nora",
        partner_gender="girl",
        ranger="Ranger Bo",
        ranger_gender="ranger_man",
        trait="steady",
        relation="friends",
        trust=4,
        leader_age=7,
        partner_age=6,
    ),
    StoryParams(
        theme="treasure_post",
        waterway="channel",
        cargo="map_tube",
        craft="canoe",
        leader="Ava",
        leader_gender="girl",
        partner="Ben",
        partner_gender="boy",
        ranger="Ranger Jo",
        ranger_gender="ranger_woman",
        trait="patient",
        relation="siblings",
        trust=7,
        leader_age=5,
        partner_age=7,
    ),
    StoryParams(
        theme="island_fort",
        waterway="creek",
        cargo="snack_basket",
        craft="rowboat",
        leader="Ruby",
        leader_gender="girl",
        partner="Theo",
        partner_gender="boy",
        ranger="Ranger Bo",
        ranger_gender="ranger_man",
        trait="sensible",
        relation="siblings",
        trust=9,
        leader_age=6,
        partner_age=8,
    ),
    StoryParams(
        theme="reed_castle",
        waterway="channel",
        cargo="flag",
        craft="canoe",
        leader="Max",
        leader_gender="boy",
        partner="Ivy",
        partner_gender="girl",
        ranger="Ranger Jo",
        ranger_gender="ranger_woman",
        trait="curious",
        relation="friends",
        trust=6,
        leader_age=7,
        partner_age=7,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, waterway, cargo, craft) combos:\n")
        for theme, water, cargo, craft in combos:
            print(f"  {theme:13} {water:8} {cargo:12} {craft}")
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
            header = f"### {p.leader} & {p.partner}: {p.craft} on {p.waterway} with {p.cargo} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
