#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chandelier_jar_quake_mystery_to_solve_adventure.py
==============================================================================

A standalone story world for a small "mystery to solve" adventure.

Premise
-------
Two children are helping a kindly keeper in an old room where a small important
object has gone missing. While they search, a little quake shakes the room. The
chandelier begins to sway, a jar on a shelf rattles, and the world itself
produces a clue. The children follow that clue and solve the mystery.

This world keeps a tight reasonableness constraint:
- the chosen room must actually contain the hiding spot,
- the chosen jar contents must be the kind that can reveal that spot,
- the chosen quake must be strong enough to make that clue appear.

So the prose is driven by simulated state, not by swapping nouns into one fixed
paragraph.

Run it
------
python storyworlds/worlds/gpt-5.4/chandelier_jar_quake_mystery_to_solve_adventure.py
python storyworlds/worlds/gpt-5.4/chandelier_jar_quake_mystery_to_solve_adventure.py --all
python storyworlds/worlds/gpt-5.4/chandelier_jar_quake_mystery_to_solve_adventure.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/chandelier_jar_quake_mystery_to_solve_adventure.py --asp
python storyworlds/worlds/gpt-5.4/chandelier_jar_quake_mystery_to_solve_adventure.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
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
class Setting:
    id: str
    label: str
    opening: str
    atmosphere: str
    chandelier_text: str
    jar_place: str
    supports: set[str] = field(default_factory=set)
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
class LostThing:
    id: str
    label: str
    phrase: str
    purpose: str
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
class Spot:
    id: str
    label: str
    the: str
    search_line: str
    found_line: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class JarFill:
    id: str
    label: str
    plural: bool
    min_quake: int
    supports: set[str] = field(default_factory=set)
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
class Quake:
    id: str
    label: str
    strength: int
    feel: str
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


def _r_quake_shakes(world: World) -> list[str]:
    room = world.get("room")
    chandelier = world.get("chandelier")
    jar = world.get("jar")
    if room.meters["quake"] < THRESHOLD:
        return []
    sig = ("quake_shakes", int(room.meters["quake"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chandelier.meters["swing"] += room.meters["quake"]
    jar.meters["rattle"] += room.meters["quake"]
    for kid in world.kids():
        kid.memes["surprise"] += 1
    return []


def _r_clue_appears(world: World) -> list[str]:
    jar = world.get("jar")
    chandelier = world.get("chandelier")
    if jar.meters["rattle"] < THRESHOLD or chandelier.meters["swing"] < THRESHOLD:
        return []
    fill = world.facts["jarfill"]
    quake = world.facts["quake_cfg"]
    if quake.strength < fill.min_quake:
        return []
    sig = ("clue_appears", fill.id, world.facts["spot_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    jar.meters["spilled"] += 1
    world.get("clue").meters["visible"] += 1
    for kid in world.kids():
        kid.memes["hope"] += 1
    return []


def _r_mystery_solved(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["visible"] < THRESHOLD:
        return []
    sig = ("mystery_solved", world.facts["spot_cfg"].id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lost = world.get("lost")
    lost.meters["found"] += 1
    for kid in world.kids():
        kid.memes["pride"] += 1
        kid.memes["relief"] += 1
    world.get("keeper").memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="quake_shakes", tag="physical", apply=_r_quake_shakes),
    Rule(name="clue_appears", tag="physical", apply=_r_clue_appears),
    Rule(name="mystery_solved", tag="resolution", apply=_r_mystery_solved),
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
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "ballroom": Setting(
        id="ballroom",
        label="the moonlit ballroom",
        opening="At the end of the old house stood a moonlit ballroom with long curtains and a wide rug.",
        atmosphere="Every sound in the room seemed to wait for a brave guess.",
        chandelier_text="Above them hung a grand chandelier with glass drops that winked whenever anyone moved.",
        jar_place="on a carved shelf by the wall",
        supports={"curtain_fold", "rug_fold"},
    ),
    "tower": Setting(
        id="tower",
        label="the round tower room",
        opening="High in the tower was a round room with a rug, a deep window ledge, and windy curtains.",
        atmosphere="The stones made the adventure feel secret and high above the world.",
        chandelier_text="A smaller brass chandelier hung from the beams, bright enough to toss rings of light over the floor.",
        jar_place="on a narrow shelf beside the stairs",
        supports={"window_ledge", "rug_fold"},
    ),
    "music_room": Setting(
        id="music_room",
        label="the old music room",
        opening="Beyond a quiet hall lay an old music room with velvet curtains, a faded rug, and a patient piano.",
        atmosphere="It felt like the sort of room where clues waited to be heard as well as seen.",
        chandelier_text="A silver chandelier floated over the room like a frozen burst of stars.",
        jar_place="on top of the piano",
        supports={"curtain_fold", "window_ledge"},
    ),
}

LOST_THINGS = {
    "star_key": LostThing(
        id="star_key",
        label="star key",
        phrase="a little star key",
        purpose="opened the painted treasure chest in the attic",
        tags={"key", "treasure"},
    ),
    "map_tube": LostThing(
        id="map_tube",
        label="map tube",
        phrase="a tiny map tube",
        purpose="held the paper map to the garden gate maze",
        tags={"map", "maze"},
    ),
    "moon_badge": LostThing(
        id="moon_badge",
        label="moon badge",
        phrase="a silver moon badge",
        purpose="was the prize for the evening's explorers' club",
        tags={"badge", "club"},
    ),
}

SPOTS = {
    "curtain_fold": Spot(
        id="curtain_fold",
        label="curtain fold",
        the="the fold of the curtain",
        search_line="They hurried to the curtain where the cloth bunched in a deep fold near the wall.",
        found_line="Tucked in the fold of the curtain was the missing thing.",
        tags={"curtain"},
    ),
    "rug_fold": Spot(
        id="rug_fold",
        label="rug fold",
        the="the lifted edge of the rug",
        search_line="They knelt where the rug made a little hump, as if the floor had tried to whisper a secret.",
        found_line="Under the lifted edge of the rug was the missing thing.",
        tags={"rug"},
    ),
    "window_ledge": Spot(
        id="window_ledge",
        label="window ledge",
        the="the deep window ledge",
        search_line="They climbed to the deep window ledge where moonlight pooled like silver milk.",
        found_line="Behind a flowerpot on the window ledge was the missing thing.",
        tags={"window"},
    ),
}

JAR_FILLS = {
    "marbles": JarFill(
        id="marbles",
        label="striped marbles",
        plural=True,
        min_quake=2,
        supports={"rug_fold", "window_ledge"},
        tags={"marbles"},
    ),
    "glitter": JarFill(
        id="glitter",
        label="gold glitter",
        plural=False,
        min_quake=1,
        supports={"curtain_fold", "rug_fold"},
        tags={"glitter"},
    ),
    "shell_beads": JarFill(
        id="shell_beads",
        label="tiny shell beads",
        plural=True,
        min_quake=1,
        supports={"curtain_fold", "window_ledge"},
        tags={"beads"},
    ),
}

QUAKES = {
    "tremble": Quake(
        id="tremble",
        label="a tiny tremble",
        strength=1,
        feel="The floor gave the gentlest shiver, just enough to make the room hold its breath.",
        tags={"quake"},
    ),
    "shimmy": Quake(
        id="shimmy",
        label="a quick shimmy",
        strength=2,
        feel="A quick quake ran through the floorboards, not dangerous, but strong enough to wake every loose thing in the room.",
        tags={"quake"},
    ),
    "rumble": Quake(
        id="rumble",
        label="a low rumble",
        strength=3,
        feel="A low quake rolled under their feet and made the old room murmur from wall to wall.",
        tags={"quake"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy", "Maya", "Ivy"]
BOY_NAMES = ["Tom", "Max", "Leo", "Finn", "Sam", "Eli", "Theo", "Jack"]
TRAITS = ["brave", "careful", "curious", "steady", "keen", "clever"]


@dataclass
class StoryParams:
    place: str
    lost: str
    spot: str
    jarfill: str
    quake: str
    leader: str
    leader_gender: str
    partner: str
    partner_gender: str
    keeper: str
    trait: str
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


CURATED = [
    StoryParams(
        place="ballroom",
        lost="star_key",
        spot="curtain_fold",
        jarfill="glitter",
        quake="tremble",
        leader="Lily",
        leader_gender="girl",
        partner="Tom",
        partner_gender="boy",
        keeper="grandmother",
        trait="curious",
        seed=101,
    ),
    StoryParams(
        place="tower",
        lost="map_tube",
        spot="rug_fold",
        jarfill="marbles",
        quake="shimmy",
        leader="Max",
        leader_gender="boy",
        partner="Ava",
        partner_gender="girl",
        keeper="grandfather",
        trait="steady",
        seed=102,
    ),
    StoryParams(
        place="music_room",
        lost="moon_badge",
        spot="window_ledge",
        jarfill="shell_beads",
        quake="tremble",
        leader="Nora",
        leader_gender="girl",
        partner="Finn",
        partner_gender="boy",
        keeper="grandmother",
        trait="brave",
        seed=103,
    ),
    StoryParams(
        place="tower",
        lost="star_key",
        spot="window_ledge",
        jarfill="marbles",
        quake="rumble",
        leader="Theo",
        leader_gender="boy",
        partner="Mia",
        partner_gender="girl",
        keeper="grandfather",
        trait="keen",
        seed=104,
    ),
    StoryParams(
        place="music_room",
        lost="map_tube",
        spot="curtain_fold",
        jarfill="shell_beads",
        quake="shimmy",
        leader="Lucy",
        leader_gender="girl",
        partner="Leo",
        partner_gender="boy",
        keeper="grandmother",
        trait="careful",
        seed=105,
    ),
]


def valid_combo(place: str, jarfill: str, spot: str, quake: str) -> bool:
    setting = SETTINGS[place]
    fill = JAR_FILLS[jarfill]
    q = QUAKES[quake]
    return spot in setting.supports and spot in fill.supports and q.strength >= fill.min_quake


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in SETTINGS:
        for jarfill in JAR_FILLS:
            for spot in SPOTS:
                for quake in QUAKES:
                    if valid_combo(place, jarfill, spot, quake):
                        combos.append((place, jarfill, spot, quake))
    return combos


def explain_rejection(place: Setting, fill: JarFill, spot: Spot, quake: Quake) -> str:
    if spot.id not in place.supports:
        return (
            f"(No story: {place.label} does not honestly contain {spot.the} as a good hiding place. "
            f"Pick a spot that fits the room.)"
        )
    if spot.id not in fill.supports:
        return (
            f"(No story: a jar of {fill.label} would not leave a clear clue pointing to {spot.the}. "
            f"Pick jar contents that could reveal that spot.)"
        )
    if quake.strength < fill.min_quake:
        return (
            f"(No story: {quake.label} is too weak to shake a jar of {fill.label} into a useful clue. "
            f"Pick a stronger quake or easier clue material.)"
        )
    return "(No story: this combination does not make a fair mystery.)"


def clue_sentence(fill: JarFill, spot: Spot) -> str:
    if fill.id == "marbles" and spot.id == "rug_fold":
        return (
            "The jar tipped, and three striped marbles skipped out. In the swinging chandelier light, "
            "they rolled in a bright little line and disappeared under the lifted edge of the rug."
        )
    if fill.id == "marbles" and spot.id == "window_ledge":
        return (
            "The jar tipped, and three striped marbles clattered out. They spun toward the wall until "
            "they tapped against the deep window ledge and came to rest below it."
        )
    if fill.id == "glitter" and spot.id == "curtain_fold":
        return (
            "The jar gave a soft hop, and a puff of gold glitter rose into the air. The chandelier threw it into sparkles, "
            "and the sparkles drifted straight into the fold of the curtain."
        )
    if fill.id == "glitter" and spot.id == "rug_fold":
        return (
            "The jar rattled open just enough for a dusting of gold glitter to slip out. In the moving chandelier light, "
            "the glitter settled in a shining crescent along the lifted edge of the rug."
        )
    if fill.id == "shell_beads" and spot.id == "curtain_fold":
        return (
            "The jar of tiny shell beads shivered on the shelf. A few beads bounced free and clicked softly until they hid "
            "themselves in the fold of the curtain."
        )
    if fill.id == "shell_beads" and spot.id == "window_ledge":
        return (
            "The jar of tiny shell beads rattled and let two beads jump out. They skipped across the piano top and landed by "
            "the deep window ledge, where the moonlight made them shine."
        )
    return "The shaking jar left a clue, and the swinging chandelier made it impossible to miss."


def solve_line(spot: Spot, lost: LostThing) -> str:
    return f"{spot.found_line} It was {lost.phrase}, exactly where the clue had led them."


def introduce(world: World, leader: Entity, partner: Entity, keeper: Entity, lost: LostThing) -> None:
    setting = world.setting
    leader.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(setting.opening)
    world.say(setting.atmosphere)
    world.say(setting.chandelier_text)
    world.say(
        f"On that shelf sat a glass jar, and beside it stood {keeper.label_word.capitalize()}, who had a mystery for "
        f"{leader.id} and {partner.id}."
    )
    world.say(
        f'"Somewhere in this room I have misplaced {lost.phrase}, and it {lost.purpose}," '
        f"{keeper.pronoun()} said. \"Will you two adventurers help me solve it?\""
    )


def accept_mission(world: World, leader: Entity, partner: Entity) -> None:
    leader.memes["bravery"] += 1
    partner.memes["trust"] += 1
    world.say(
        f'"A mystery!" {leader.id} said, straightening up as if a cape had suddenly landed on {leader.pronoun("possessive")} shoulders.'
    )
    world.say(
        f"{partner.id} nodded and looked from the chandelier to the jar to every shadowy corner. "
        f"Already the room felt like a map waiting to be read."
    )


def search(world: World, leader: Entity, partner: Entity, spot: Spot, lost: LostThing) -> None:
    leader.memes["focus"] += 1
    partner.memes["focus"] += 1
    world.say(
        f"They checked under chairs, peeked behind frames, and even asked whether the missing {lost.label} "
        f"might be hiding in plain sight."
    )
    world.say(
        f'But nothing turned up. "{spot.the.capitalize()} can wait," {partner.id} said. '
        f'"First we need a clue, not just another guess."'
    )


def do_quake(world: World, quake: Quake) -> None:
    room = world.get("room")
    room.meters["quake"] = float(quake.strength)
    world.say(quake.feel)
    world.say(
        f"The chandelier swayed overhead, and the jar {world.setting.jar_place} gave a quick answering rattle."
    )
    propagate(world, narrate=False)


def notice_clue(world: World, leader: Entity, partner: Entity, fill: JarFill, spot: Spot) -> None:
    leader.memes["wonder"] += 1
    partner.memes["wonder"] += 1
    world.say(clue_sentence(fill, spot))
    world.say(
        f'"Look!" {leader.id} cried. "{spot.the.capitalize()}!" {partner.id} was already moving.'
    )


def follow_clue(world: World, spot: Spot) -> None:
    world.say(spot.search_line)


def recover(world: World, keeper: Entity, lost: LostThing, spot: Spot, leader: Entity, partner: Entity) -> None:
    world.say(solve_line(spot, lost))
    world.say(
        f'{keeper.label_word.capitalize()} laughed with relief. "You solved it," {keeper.pronoun()} said. '
        f'"The quake shook the room, but you two watched carefully enough to turn a wobble into an answer."'
    )
    world.say(
        f"{leader.id} placed {lost.phrase} in {keeper.pronoun('possessive')} hand, and {partner.id} looked up at the chandelier, "
        f"which was settling back into stillness at last."
    )


def ending(world: World, keeper: Entity, lost: LostThing, leader: Entity, partner: Entity, fill: JarFill) -> None:
    keeper.memes["gratitude"] += 1
    leader.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f'Then {keeper.label_word.capitalize()} set the jar of {fill.label} straight again and said, '
        f'"A good adventure is not only about brave feet. It is also about brave eyes."'
    )
    world.say(
        f"With the mystery solved and {lost.phrase} safe again, {leader.id} and {partner.id} stood in the calm room a little taller, "
        f"ready for whatever secret the old house might whisper next."
    )


def tell(
    setting: Setting,
    lost: LostThing,
    spot: Spot,
    jarfill: JarFill,
    quake: Quake,
    leader_name: str = "Lily",
    leader_gender: str = "girl",
    partner_name: str = "Tom",
    partner_gender: str = "boy",
    keeper_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            role="leader",
            traits=[trait],
            attrs={},
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=["loyal"],
            attrs={},
        )
    )
    keeper = world.add(
        Entity(
            id="Keeper",
            kind="character",
            type=keeper_type,
            role="keeper",
            label="the keeper",
            attrs={},
        )
    )
    room = world.add(Entity(id="room", type="room", label=setting.label, attrs={}))
    chandelier = world.add(Entity(id="chandelier", type="chandelier", label="chandelier", attrs={}))
    jar = world.add(Entity(id="jar", type="jar", label="jar", attrs={}))
    clue = world.add(Entity(id="clue", type="clue", label="clue", attrs={}))
    lost_ent = world.add(Entity(id="lost", type="lost", label=lost.label, attrs={"spot": spot.id}))

    room.meters["quake"] = 0.0
    chandelier.meters["swing"] = 0.0
    jar.meters["rattle"] = 0.0
    jar.meters["spilled"] = 0.0
    clue.meters["visible"] = 0.0
    lost_ent.meters["found"] = 0.0

    for kid in (leader, partner):
        kid.memes["curiosity"] = 0.0
        kid.memes["bravery"] = 0.0
        kid.memes["focus"] = 0.0
        kid.memes["wonder"] = 0.0
        kid.memes["hope"] = 0.0
        kid.memes["pride"] = 0.0
        kid.memes["relief"] = 0.0
        kid.memes["joy"] = 0.0
        kid.memes["surprise"] = 0.0
        kid.memes["trust"] = 0.0
    keeper.memes["relief"] = 0.0
    keeper.memes["gratitude"] = 0.0

    world.facts.update(
        setting=setting,
        lost_cfg=lost,
        spot_cfg=spot,
        jarfill=jarfill,
        quake_cfg=quake,
        leader=leader,
        partner=partner,
        keeper=keeper,
    )

    introduce(world, leader, partner, keeper, lost)
    accept_mission(world, leader, partner)

    world.para()
    search(world, leader, partner, spot, lost)
    do_quake(world, quake)

    world.para()
    notice_clue(world, leader, partner, jarfill, spot)
    follow_clue(world, spot)
    propagate(world, narrate=False)

    world.para()
    recover(world, keeper, lost, spot, leader, partner)
    ending(world, keeper, lost, leader, partner, jarfill)

    world.facts.update(
        solved=lost_ent.meters["found"] >= THRESHOLD,
        clue_visible=clue.meters["visible"] >= THRESHOLD,
        spilled=jar.meters["spilled"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "quake": [
        (
            "What is a quake?",
            "A quake is a shaking of the ground. A small quake can rattle a room and make hanging things sway."
        )
    ],
    "chandelier": [
        (
            "What is a chandelier?",
            "A chandelier is a light that hangs from the ceiling, often with many arms or shiny pieces. If the room shakes, it can swing."
        )
    ],
    "jar": [
        (
            "What is a jar?",
            "A jar is a container with a wide mouth, often made of glass. People use jars to hold small things like beads, marbles, or glitter."
        )
    ],
    "marbles": [
        (
            "Why do marbles roll so easily?",
            "Marbles are round and smooth, so they can roll as soon as a floor tilts or a hand bumps them."
        )
    ],
    "glitter": [
        (
            "Why is glitter easy to notice in light?",
            "Glitter has many tiny shiny pieces. When light hits it, it sparkles and catches your eye."
        )
    ],
    "beads": [
        (
            "Why can little beads make a clue?",
            "Little beads bounce and click when they move. If they fall from a jar, they can lead you to the place where they stopped."
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key opens a lock that matches it. Small keys can be easy to lose, so people keep them in safe places."
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map helps people find their way. It shows where paths, places, or treasures are."
        )
    ],
    "badge": [
        (
            "What is a badge?",
            "A badge is a small sign or medal that shows a group, job, or reward. People often save badges because they are special."
        )
    ],
    "curtain": [
        (
            "What is a curtain fold?",
            "A curtain fold is a place where cloth bends and bunches up. Small objects can slip into it and hide there."
        )
    ],
    "rug": [
        (
            "Why can something hide under a rug edge?",
            "If a rug lifts a little, it can make a tiny pocket underneath. A small object can slide there and be hard to see."
        )
    ],
    "window": [
        (
            "What is a window ledge?",
            "A window ledge is the flat part at the bottom of a window. People often set flowerpots or little objects there."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "quake",
    "chandelier",
    "jar",
    "marbles",
    "glitter",
    "beads",
    "key",
    "map",
    "badge",
    "curtain",
    "rug",
    "window",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    lost = f["lost_cfg"]
    setting = f["setting"]
    return [
        'Write a short adventure story for a 3-to-5-year-old with a mystery to solve, and include the words "chandelier", "jar", and "quake".',
        f"Tell a gentle adventure where {leader.id} and {partner.id} help solve the mystery of a missing {lost.label} in {setting.label}.",
        f"Write a child-facing mystery where a small quake shakes a chandelier and a jar, creating the clue that helps two children find {lost.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    keeper = f["keeper"]
    lost = f["lost_cfg"]
    spot = f["spot_cfg"]
    fill = f["jarfill"]
    quake = f["quake_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two young adventurers, and {keeper.label_word} who asked them to help. "
            f"They were trying to find {lost.phrase}."
        ),
        (
            f"What was the mystery?",
            f"The mystery was where {lost.phrase} had gone in {world.setting.label}. "
            f"It mattered because it {lost.purpose}."
        ),
        (
            "What happened during the quake?",
            f"During {quake.label}, the chandelier began to swing and the jar began to rattle. "
            f"That shaking changed the room and made a hidden clue appear."
        ),
        (
            "How did the children solve the mystery?",
            f"They watched carefully after the quake instead of guessing wildly. "
            f"When the jar of {fill.label} left a clue and the chandelier light made it easy to see, they followed it to {spot.the}."
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                f"Where did they find the missing {lost.label}?",
                f"They found it at {spot.the}. "
                f"The clue led them there, and the search stopped being a mystery once they trusted what the room was showing them."
            )
        )
        qa.append(
            (
                f"How did {keeper.label_word} feel at the end?",
                f"{keeper.label_word.capitalize()} felt relieved and grateful. "
                f"The missing thing was safe again, and the children had turned a surprising moment into a solved adventure."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"quake", "chandelier", "jar"} | set(f["quake_cfg"].tags) | set(f["spot_cfg"].tags)
    tags |= set(f["jarfill"].tags)
    tags |= set(f["lost_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:11} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Jar, Spot, Quake) :-
    setting(Place),
    jarfill(Jar),
    spot(Spot),
    quake(Quake),
    supports_place(Place, Spot),
    reveals(Jar, Spot),
    strength(Quake, S),
    min_quake(Jar, M),
    S >= M.

solved :-
    chosen_place(Place),
    chosen_jar(Jar),
    chosen_spot(Spot),
    chosen_quake(Quake),
    valid(Place, Jar, Spot, Quake).

outcome(solved) :- solved.
outcome(invalid) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for spot in sorted(setting.supports):
            lines.append(asp.fact("supports_place", place, spot))
    for jar, fill in JAR_FILLS.items():
        lines.append(asp.fact("jarfill", jar))
        lines.append(asp.fact("min_quake", jar, fill.min_quake))
        for spot in sorted(fill.supports):
            lines.append(asp.fact("reveals", jar, spot))
    for spot in SPOTS:
        lines.append(asp.fact("spot", spot))
    for quake, q in QUAKES.items():
        lines.append(asp.fact("quake", quake))
        lines.append(asp.fact("strength", quake, q.strength))
    for lost in LOST_THINGS:
        lines.append(asp.fact("lost_thing", lost))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_jar", params.jarfill),
            asp.fact("chosen_spot", params.spot),
            asp.fact("chosen_quake", params.quake),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if valid_combo(params.place, params.jarfill, params.spot, params.quake) else "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combo gate matches ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        sink = io.StringIO()
        with contextlib.redirect_stdout(sink):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a chandelier, a jar, a quake, and a mystery solved by careful adventure."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--lost", choices=LOST_THINGS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--jarfill", choices=JAR_FILLS)
    ap.add_argument("--quake", choices=QUAKES)
    ap.add_argument("--keeper", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery setups derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.jarfill and args.spot and args.quake:
        setting = SETTINGS[args.place]
        fill = JAR_FILLS[args.jarfill]
        spot = SPOTS[args.spot]
        quake = QUAKES[args.quake]
        if not valid_combo(args.place, args.jarfill, args.spot, args.quake):
            raise StoryError(explain_rejection(setting, fill, spot, quake))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.jarfill is None or combo[1] == args.jarfill)
        and (args.spot is None or combo[2] == args.spot)
        and (args.quake is None or combo[3] == args.quake)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, jarfill, spot, quake = rng.choice(sorted(combos))
    lost = args.lost or rng.choice(sorted(LOST_THINGS))
    leader, leader_gender = _pick_kid(rng)
    partner, partner_gender = _pick_kid(rng, avoid=leader)
    keeper = args.keeper or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        lost=lost,
        spot=spot,
        jarfill=jarfill,
        quake=quake,
        leader=leader,
        leader_gender=leader_gender,
        partner=partner,
        partner_gender=partner_gender,
        keeper=keeper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.lost not in LOST_THINGS:
        raise StoryError(f"(Unknown lost item: {params.lost})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.jarfill not in JAR_FILLS:
        raise StoryError(f"(Unknown jarfill: {params.jarfill})")
    if params.quake not in QUAKES:
        raise StoryError(f"(Unknown quake: {params.quake})")
    if params.keeper not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown keeper type: {params.keeper})")

    setting = SETTINGS[params.place]
    fill = JAR_FILLS[params.jarfill]
    spot = SPOTS[params.spot]
    quake = QUAKES[params.quake]
    if not valid_combo(params.place, params.jarfill, params.spot, params.quake):
        raise StoryError(explain_rejection(setting, fill, spot, quake))

    world = tell(
        setting=setting,
        lost=LOST_THINGS[params.lost],
        spot=spot,
        jarfill=fill,
        quake=quake,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        keeper_type=params.keeper,
        trait=params.trait,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, jarfill, spot, quake) combos:\n")
        for place, jarfill, spot, quake in combos:
            print(f"  {place:10} {jarfill:11} {spot:13} {quake}")
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
            header = f"### {p.leader} & {p.partner}: {p.lost} in {p.place} ({p.jarfill}, {p.quake})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
