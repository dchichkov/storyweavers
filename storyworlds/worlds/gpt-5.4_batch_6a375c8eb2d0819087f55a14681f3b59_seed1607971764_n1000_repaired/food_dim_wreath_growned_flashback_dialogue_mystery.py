#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/food_dim_wreath_growned_flashback_dialogue_mystery.py
=================================================================================

A standalone story world for a soft bedtime mystery: a child and a grown-up bake
a little bread wreath for the evening, discover that something is wrong with it,
and solve the mystery by following grounded clues and a remembered flashback.

This world is built from a TinyStories-style seed requiring the words
"food-dim", "wreath", and "growned", plus the features Flashback, Dialogue, and
Mystery to Solve. The resulting stories stay child-facing and concrete: warm
kitchen light, sleepy questions, a small puzzle, and an ending image that proves
what changed.

Premise
-------
A child and a caregiver bake a soft bread wreath for bedtime cocoa. Later they
find a small mystery: one shining topping is gone from the wreath. The child
spots a clue, remembers something from earlier, and the pair solve what
happened. The culprit is not dangerous or cruel; it is a little household
trouble that can be gently fixed.

Run it
------
    python storyworlds/worlds/gpt-5.4/food_dim_wreath_growned_flashback_dialogue_mystery.py
    python storyworlds/worlds/gpt-5.4/food_dim_wreath_growned_flashback_dialogue_mystery.py --culprit mouse
    python storyworlds/worlds/gpt-5.4/food_dim_wreath_growned_flashback_dialogue_mystery.py --clue pawprints
    python storyworlds/worlds/gpt-5.4/food_dim_wreath_growned_flashback_dialogue_mystery.py --all
    python storyworlds/worlds/gpt-5.4/food_dim_wreath_growned_flashback_dialogue_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/food_dim_wreath_growned_flashback_dialogue_mystery.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    edible: bool = False
    movable: bool = False
    # Physical and emotional axes.
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World content registries
# ---------------------------------------------------------------------------
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
    room: str
    hush: str
    storage: str
    window_place: str
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
class Topping:
    id: str
    label: str
    plural_label: str
    color: str
    scent: str
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
class Culprit:
    id: str
    label: str
    kind: str
    can_nibble: bool
    leaves: str
    move_text: str
    explain: str
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
    for_culprits: set[str]
    spot: str
    line: str
    answer_line: str
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
class Fix:
    id: str
    label: str
    for_culprits: set[str]
    action: str
    ending: str
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


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        room="the kitchen",
        hush="The house had its sleepy, tucked-in sound.",
        storage="the food-dim pantry",
        window_place="the little window over the sink",
        tags={"kitchen", "pantry"},
    ),
    "cottage": Setting(
        id="cottage",
        room="the cottage kitchen",
        hush="Outside, the night leaned softly against the cottage walls.",
        storage="the food-dim shelf by the bread box",
        window_place="the round window by the stove",
        tags={"kitchen", "shelf"},
    ),
    "bakery": Setting(
        id="bakery",
        room="the warm back room of the family bakery",
        hush="The last oven click had faded, and the room was getting quiet.",
        storage="the food-dim corner beside the flour bins",
        window_place="the tall window by the cooling rack",
        tags={"bakery", "corner"},
    ),
}

TOPPINGS = {
    "raisins": Topping(
        id="raisins",
        label="raisin",
        plural_label="raisins",
        color="dark and shiny",
        scent="sweet bread and warm cinnamon",
        tags={"raisins", "bread"},
    ),
    "blueberries": Topping(
        id="blueberries",
        label="blueberry",
        plural_label="blueberries",
        color="inky blue",
        scent="soft bread and berry jam",
        tags={"blueberries", "bread"},
    ),
    "cherries": Topping(
        id="cherries",
        label="cherry",
        plural_label="cherries",
        color="red and glossy",
        scent="vanilla bread and cherry syrup",
        tags={"cherries", "bread"},
    ),
}

CULPRITS = {
    "mouse": Culprit(
        id="mouse",
        label="a tiny mouse",
        kind="animal",
        can_nibble=True,
        leaves="nibbled",
        move_text="had scampered over the table edge and stolen one topping",
        explain="small teeth and quick little feet fit the clues best",
        tags={"mouse", "animal"},
    ),
    "cat": Culprit(
        id="cat",
        label="the family cat",
        kind="animal",
        can_nibble=True,
        leaves="licked away",
        move_text="had padded onto the chair, sniffed the sweet bread, and batted one topping free",
        explain="soft paws and a curious nose fit the clues best",
        tags={"cat", "animal"},
    ),
    "wind": Culprit(
        id="wind",
        label="the evening wind",
        kind="weather",
        can_nibble=False,
        leaves="shook loose",
        move_text="had slipped through the open window and jiggled one topping down",
        explain="a drifting breeze and a loose topping fit the clues best",
        tags={"wind", "weather"},
    ),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="floury pawprints",
        for_culprits={"mouse", "cat"},
        spot="across the chair and table edge",
        line="There were little floury pawprints across the chair and table edge.",
        answer_line="The floury pawprints showed that an animal, not the wind, had come close.",
        tags={"pawprints", "flour"},
    ),
    "open_window": Clue(
        id="open_window",
        label="an open window",
        for_culprits={"wind"},
        spot="beside the cooling rack",
        line="The window beside the cooling rack was still open, and the curtain kept breathing in and out.",
        answer_line="The open window meant the night breeze could reach the cooling bread.",
        tags={"window", "wind"},
    ),
    "crumbs": Clue(
        id="crumbs",
        label="a trail of crumbs",
        for_culprits={"mouse"},
        spot="from the wreath to a tiny crack by the baseboard",
        line="A neat little trail of crumbs ran from the wreath to a tiny crack by the baseboard.",
        answer_line="The crumb trail led away like a path, which made a small mouse the best answer.",
        tags={"crumbs", "mouse"},
    ),
    "fallen_fruit": Clue(
        id="fallen_fruit",
        label="one fallen topping",
        for_culprits={"wind", "cat"},
        spot="under the table",
        line="Under the table lay one squashed topping, as if it had been knocked or shaken loose.",
        answer_line="The fallen topping showed that the missing piece had not vanished by magic; it had been knocked down.",
        tags={"fallen", "table"},
    ),
}

FIXES = {
    "cover_bread": Fix(
        id="cover_bread",
        label="cover the bread with a towel",
        for_culprits={"mouse", "cat"},
        action="covered the wreath with a clean towel and set it higher up",
        ending="No more little nibblers could reach it there.",
        tags={"cover", "safe_food"},
    ),
    "close_window": Fix(
        id="close_window",
        label="close the window",
        for_culprits={"wind"},
        action="closed the window and tucked the curtain still",
        ending="The room grew calm, and the wreath could rest without wobbling.",
        tags={"window", "calm"},
    ),
    "share_piece": Fix(
        id="share_piece",
        label="replace the missing piece kindly",
        for_culprits={"mouse", "cat", "wind"},
        action="pressed one fresh topping into the empty place with gentle fingers",
        ending="The circle looked whole again.",
        tags={"repair", "bread"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Tessa", "Ivy", "Wren", "Mabel", "Elsie"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Jonah", "Milo", "Ben", "Arlo", "Ned"]
TRAITS = ["sleepy", "careful", "curious", "soft-voiced", "bright-eyed"]
CAREGIVERS = ["mother", "father", "grandmother", "grandfather"]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
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


def _r_missing_makes_worry(world: World) -> list[str]:
    out: list[str] = []
    wreath = world.get("wreath")
    child = world.get("child")
    caregiver = world.get("caregiver")
    if wreath.meters["missing_topping"] >= THRESHOLD:
        sig = ("worry", "missing")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["wonder"] += 1
            caregiver.memes["concern"] += 1
            out.append("__mystery__")
    return out


def _r_animal_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts["clue_cfg"]
    if clue.id != "pawprints":
        return out
    sig = ("animal_guess", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["deduction"] += 1
    world.facts["suspect_kind"] = "animal"
    return out


def _r_window_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts["clue_cfg"]
    if clue.id != "open_window":
        return out
    sig = ("wind_guess", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["deduction"] += 1
    world.facts["suspect_kind"] = "weather"
    return out


def _r_trail_points_mouse(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts["clue_cfg"]
    if clue.id != "crumbs":
        return out
    sig = ("mouse_guess", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["deduction"] += 1
    world.facts["suspect_id"] = "mouse"
    return out


def _r_fallen_points_not_magic(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts["clue_cfg"]
    if clue.id != "fallen_fruit":
        return out
    sig = ("fallen", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child = world.get("child")
    child.memes["deduction"] += 1
    world.facts["fell_not_vanished"] = True
    return out


CAUSAL_RULES = [
    Rule(name="missing_makes_worry", tag="emotion", apply=_r_missing_makes_worry),
    Rule(name="animal_clue", tag="reason", apply=_r_animal_clue),
    Rule(name="window_clue", tag="reason", apply=_r_window_clue),
    Rule(name="trail_points_mouse", tag="reason", apply=_r_trail_points_mouse),
    Rule(name="fallen_points_not_magic", tag="reason", apply=_r_fallen_points_not_magic),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def clue_matches(culprit: Culprit, clue: Clue) -> bool:
    return culprit.id in clue.for_culprits


def fixes_for(culprit: Culprit) -> list[Fix]:
    return [fix for fix in FIXES.values() if culprit.id in fix.for_culprits]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for culprit_id, culprit in CULPRITS.items():
            for clue_id, clue in CLUES.items():
                if clue_matches(culprit, clue) and fixes_for(culprit):
                    combos.append((setting_id, culprit_id, clue_id))
    return combos


def explain_rejection(culprit: Culprit, clue: Clue) -> str:
    return (
        f"(No story: {clue.label} does not fit {culprit.label}. "
        f"A solvable mystery needs a clue that honestly points toward the culprit.)"
    )


# ---------------------------------------------------------------------------
# Prediction / reasoning
# ---------------------------------------------------------------------------
def predict_solution(world: World, culprit_id: str, clue_id: str) -> dict:
    sim = world.copy()
    sim.facts["culprit_cfg"] = CULPRITS[culprit_id]
    sim.facts["clue_cfg"] = CLUES[clue_id]
    sim.get("wreath").meters["missing_topping"] = 1.0
    propagate(sim, narrate=False)
    suspect_id = sim.facts.get("suspect_id")
    suspect_kind = sim.facts.get("suspect_kind")
    fell = sim.facts.get("fell_not_vanished", False)
    return {
        "suspect_id": suspect_id,
        "suspect_kind": suspect_kind,
        "fell_not_vanished": fell,
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, caregiver: Entity, topping: Topping) -> None:
    world.say(
        f"In {world.setting.room}, {child.id} stood on a stool beside "
        f"{child.pronoun('possessive')} {caregiver.label_word}. {world.setting.hush}"
    )
    world.say(
        f"They had baked a soft little wreath of bread for bedtime cocoa, and it smelled of "
        f"{topping.scent}."
    )


def bake(world: World, child: Entity, topping: Topping) -> None:
    child.memes["joy"] += 1
    world.say(
        f'{child.id} pressed {topping.plural_label} into the dough one by one. '
        f'"Look," {child.pronoun()} whispered, "it is round like a tiny moon wreath."'
    )


def flashback_seed(world: World, child: Entity) -> None:
    child.memes["memory"] += 1
    world.say(
        f'A little while earlier, when the dough had puffed up in its bowl, {child.id} had clapped and said, '
        f'"It has growned!"'
    )
    world.say(
        "The grown-up had smiled at the sweet wrong word and let it stay, because some bedtime words are too cozy to fix."
    )


def cool_bread(world: World, caregiver: Entity) -> None:
    wreath = world.get("wreath")
    wreath.meters["cooling"] = 1.0
    world.say(
        f'"Now it must cool for a bit," said {caregiver.label_word.capitalize()}. '
        f'The wreath was set near {world.setting.window_place}, not far from {world.setting.storage}.'
    )


def discover_mystery(world: World, child: Entity, caregiver: Entity, topping: Topping) -> None:
    wreath = world.get("wreath")
    wreath.meters["missing_topping"] = 1.0
    wreath.meters["uneven"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"When they came back with two warm mugs of milk, {child.id} stopped short. "
        f"One {topping.label} was gone from the wreath, and a small empty place showed in the round."
    )
    world.say(
        f'"Oh," said {child.id}. "Our wreath has a mystery."'
    )
    world.say(
        f'{caregiver.label_word.capitalize()} set the mugs down very softly. '
        f'"Then let us solve it very softly too," {caregiver.pronoun()} said.'
    )


def notice_clue(world: World, child: Entity, clue: Clue) -> None:
    world.facts["clue_seen"] = clue.id
    world.say(clue.line)
    world.say(
        f'"That must matter," {child.id} said.'
    )
    propagate(world, narrate=False)


def flashback_reason(world: World, child: Entity, caregiver: Entity, culprit: Culprit, clue: Clue) -> None:
    pred = predict_solution(world, culprit.id, clue.id)
    world.facts["prediction"] = pred
    if clue.id == "open_window":
        world.say(
            f"Then {child.id} remembered the earlier baking time in a little flashback: "
            f'{caregiver.label_word.capitalize()} had opened the window to let the hot room breathe.'
        )
        world.say(
            f'"We left it open after the bread had growned and baked," {child.id} said. '
            f'"Maybe the night air reached the wreath."'
        )
    elif clue.id == "crumbs":
        world.say(
            f"Then a flashback blinked in {child.id}'s mind: before the bread went into the oven, "
            f"{child.pronoun()} had seen something small peep from the baseboard crack."
        )
        world.say(
            f'"I remember tiny whiskers," {child.id} whispered. "Maybe the same little visitor came back."'
        )
    elif clue.id == "pawprints":
        world.say(
            f"Then {child.id} had a flashback to the flour bowl tipping a little earlier, "
            f"when someone had laughed and not wiped the chair seat clean."
        )
        if culprit.id == "cat":
            world.say(
                f'"Mossy the cat jumped there before supper," {child.id} said. '
                f'"Those soft prints could be from her."'
            )
        else:
            world.say(
                f'"Something small must have stepped in the flour and crossed the chair," {child.id} said. '
                f'"The wind cannot make pawprints."'
            )
    elif clue.id == "fallen_fruit":
        world.say(
            f"Then a flashback came back: while the bread cooled, the curtain had stirred once against the table leg."
        )
        if culprit.id == "wind":
            world.say(
                f'"I remember the curtain moving," {child.id} said. "Maybe the breeze shook one {world.facts["topping_cfg"].label} down."'
            )
        else:
            world.say(
                f'"I remember hearing a tiny thump," {child.id} said. "Maybe somebody knocked one piece down before eating it or playing with it."'
            )


def solve(world: World, child: Entity, caregiver: Entity, culprit: Culprit, clue: Clue) -> None:
    child.memes["wonder"] += 1
    child.memes["deduction"] += 1
    caregiver.memes["pride"] += 1
    world.facts["solution"] = culprit.id
    if clue.id == "crumbs":
        reason = "The crumbs led away in a line, and the little crack was just mouse-sized."
    elif clue.id == "pawprints":
        if culprit.id == "cat":
            reason = "The prints were too soft and wide for wind, and the chair made a perfect cat step."
        else:
            reason = "The prints showed an animal had come close, and the smaller troublemaker in this room was the mouse."
    elif clue.id == "open_window":
        reason = "Nothing had bitten the bread; the open window and breathing curtain pointed to the breeze."
    else:
        if culprit.id == "wind":
            reason = "The fruit had fallen under the table, which fit a wobble more than a bite."
        else:
            reason = "Something had knocked the topping free, and the household cat was the biggest gentle jiggler nearby."
    world.facts["reason_text"] = reason
    world.say(
        f'"I know," said {child.id} at last. "It was {culprit.label}."'
    )
    world.say(
        f'{caregiver.label_word.capitalize()} nodded. "{reason}"'
    )
    world.say(
        f'That made the mystery feel smaller and kinder. It had not been magic after all, only a little piece of the evening going astray.'
    )


def mend(world: World, child: Entity, caregiver: Entity, fix1: Fix, fix2: Fix) -> None:
    wreath = world.get("wreath")
    wreath.meters["missing_topping"] = 0.0
    wreath.meters["uneven"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    caregiver.memes["relief"] += 1
    world.say(
        f"Together they {fix2.action}. Then {caregiver.label_word} {fix1.action}."
    )
    world.say(
        f"{fix2.ending} {fix1.ending}"
    )


def ending(world: World, child: Entity, caregiver: Entity, topping: Topping) -> None:
    world.say(
        f'Soon the little wreath sat whole again, shining with {topping.color} {topping.plural_label}.'
    )
    world.say(
        f'{child.id} took a careful bite and leaned against {child.pronoun("possessive")} {caregiver.label_word}. '
        f'"Mysteries feel less big when we look closely," {child.pronoun()} murmured.'
    )
    world.say(
        f'"That is true," said {caregiver.label_word}. "And bedtime is sweeter when the answer is gentle."'
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    topping: Topping,
    culprit: Culprit,
    clue: Clue,
    child_name: str = "Lila",
    child_gender: str = "girl",
    caregiver_type: str = "grandmother",
    child_trait: str = "curious",
) -> World:
    if not clue_matches(culprit, clue):
        raise StoryError(explain_rejection(culprit, clue))

    world = World(setting)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        traits=["little", child_trait],
        role="child",
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=caregiver_type,
        label="the caregiver",
        role="caregiver",
    ))
    wreath = world.add(Entity(
        id="wreath",
        kind="thing",
        type="bread",
        label="bread wreath",
        edible=True,
        movable=True,
    ))

    # Initialize all facts read by rules before any propagation.
    world.facts["setting_cfg"] = setting
    world.facts["topping_cfg"] = topping
    world.facts["culprit_cfg"] = culprit
    world.facts["clue_cfg"] = clue
    world.facts["suspect_kind"] = ""
    world.facts["suspect_id"] = ""
    world.facts["fell_not_vanished"] = False
    world.facts["clue_seen"] = ""
    world.facts["solution"] = ""
    world.facts["reason_text"] = ""

    fixes = fixes_for(culprit)
    cover_fix = next((f for f in fixes if f.id == "cover_bread"), FIXES["share_piece"])
    repair_fix = FIXES["share_piece"]

    introduce(world, child, caregiver, topping)
    bake(world, child, topping)
    flashback_seed(world, child)
    cool_bread(world, caregiver)

    world.para()
    discover_mystery(world, child, caregiver, topping)
    notice_clue(world, child, clue)
    flashback_reason(world, child, caregiver, culprit, clue)
    solve(world, child, caregiver, culprit, clue)

    world.para()
    mend(world, child, caregiver, cover_fix if culprit.id != "wind" else FIXES["close_window"], repair_fix)
    ending(world, child, caregiver, topping)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        wreath=wreath,
        clue_cfg=clue,
        culprit_cfg=culprit,
        topping_cfg=topping,
        fixes_used=(cover_fix if culprit.id != "wind" else FIXES["close_window"], repair_fix),
        solved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    topping: str
    culprit: str
    clue: str
    child_name: str
    child_gender: str
    caregiver: str
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
        setting="kitchen",
        topping="raisins",
        culprit="mouse",
        clue="crumbs",
        child_name="Lila",
        child_gender="girl",
        caregiver="grandmother",
        trait="curious",
    ),
    StoryParams(
        setting="cottage",
        topping="cherries",
        culprit="wind",
        clue="open_window",
        child_name="Owen",
        child_gender="boy",
        caregiver="grandfather",
        trait="careful",
    ),
    StoryParams(
        setting="bakery",
        topping="blueberries",
        culprit="cat",
        clue="pawprints",
        child_name="Mina",
        child_gender="girl",
        caregiver="mother",
        trait="bright-eyed",
    ),
    StoryParams(
        setting="kitchen",
        topping="raisins",
        culprit="wind",
        clue="fallen_fruit",
        child_name="Theo",
        child_gender="boy",
        caregiver="father",
        trait="sleepy",
    ),
    StoryParams(
        setting="cottage",
        topping="cherries",
        culprit="mouse",
        clue="pawprints",
        child_name="Elsie",
        child_gender="girl",
        caregiver="grandmother",
        trait="soft-voiced",
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bread": [
        (
            "What happens when bread dough rises?",
            "Bread dough puffs up because tiny bubbles get trapped inside it. That makes the dough grow bigger and softer before baking."
        )
    ],
    "mouse": [
        (
            "Why do mice like crumbs?",
            "Mice are small animals that look for easy little bits of food. Crumbs are tiny enough for them to carry and nibble."
        )
    ],
    "cat": [
        (
            "Why do cats bat things with their paws?",
            "Cats are curious and playful, so they often tap light things to see how they move. A soft paw can knock food or toys by accident."
        )
    ],
    "wind": [
        (
            "How can wind move light things in a room?",
            "If a window is open, moving air can push curtains and shake light objects. That is why a breeze can wobble paper, leaves, or loose toppings."
        )
    ],
    "window": [
        (
            "Why should warm food cool in a safe place?",
            "Warm food needs time to cool, but it should rest where pets, little animals, or strong breezes cannot bother it. A safe place keeps the food clean and steady."
        )
    ],
    "mystery": [
        (
            "What helps solve a mystery?",
            "A mystery gets easier when you look for clues and remember what happened before. Careful noticing helps you choose an answer that makes sense."
        )
    ],
}

KNOWLEDGE_ORDER = ["bread", "mouse", "cat", "wind", "window", "mystery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    culprit = f["culprit_cfg"]
    clue = f["clue_cfg"]
    topping = f["topping_cfg"]
    return [
        (
            f'Write a bedtime story for a 3-to-5-year-old about a child who bakes a little wreath of bread, '
            f'finds one missing {topping.label}, and solves the mystery with a flashback and gentle dialogue.'
        ),
        (
            f"Tell a cozy mystery where {child.id} and {child.pronoun('possessive')} {caregiver.label_word} notice "
            f"{clue.label} and realize that {culprit.label} touched the bread wreath."
        ),
        (
            'Write a soft, sleepy story that includes the exact words "food-dim" and "growned", and ends with a small mystery being kindly solved.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    culprit = f["culprit_cfg"]
    clue = f["clue_cfg"]
    topping = f["topping_cfg"]
    fix1, fix2 = f["fixes_used"]
    reason = f["reason_text"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {caregiver.label_word}, who baked a little bread wreath together. Later they had to solve a small bedtime mystery about the missing topping."
        ),
        (
            "What was the mystery?",
            f"One {topping.label} was missing from the wreath, so the round bread no longer looked even. That empty place is what made {child.id} stop and wonder what had happened."
        ),
        (
            f"What clue did {child.id} notice?",
            f"{child.id} noticed {clue.label}. {clue.answer_line}"
        ),
        (
            "How did the flashback help solve the mystery?",
            f"The flashback helped {child.id} remember an earlier moment that matched the clue. That memory turned the mystery from a guess into an answer that made sense."
        ),
        (
            f"Who took or moved the topping, and how did they know?",
            f"It was {culprit.label}. {reason}"
        ),
        (
            "How did they fix the problem?",
            f"They {fix2.action}, and then they {fix1.action}. That made the wreath whole again and helped keep the same trouble from happening twice."
        ),
        (
            "How did the story end?",
            f"The wreath looked whole again, and {child.id} ate a quiet bite beside {child.pronoun('possessive')} {caregiver.label_word}. The ending feels peaceful because the mystery was solved gently, not with fear."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"bread", "mystery"}
    culprit = f["culprit_cfg"]
    clue = f["clue_cfg"]
    if culprit.id in {"mouse", "cat", "wind"}:
        tags.add(culprit.id)
    if clue.id == "open_window":
        tags.add("window")
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
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    facts_show = {
        "setting": world.facts.get("setting_cfg").id if world.facts.get("setting_cfg") else "",
        "topping": world.facts.get("topping_cfg").id if world.facts.get("topping_cfg") else "",
        "culprit": world.facts.get("culprit_cfg").id if world.facts.get("culprit_cfg") else "",
        "clue": world.facts.get("clue_cfg").id if world.facts.get("clue_cfg") else "",
        "suspect_kind": world.facts.get("suspect_kind"),
        "suspect_id": world.facts.get("suspect_id"),
        "fell_not_vanished": world.facts.get("fell_not_vanished"),
        "solution": world.facts.get("solution"),
    }
    lines.append(f"  facts: {facts_show}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A clue is usable for a culprit if the registry says it fits.
valid(S, C, Cl) :- setting(S), culprit(C), clue(Cl), fits(Cl, C), has_fix(C).

% Reasoning atoms mirroring the Python hint rules.
suspect_kind(animal) :- chosen_clue(pawprints).
suspect_kind(weather) :- chosen_clue(open_window).
suspect_id(mouse)     :- chosen_clue(crumbs).
fell_not_vanished     :- chosen_clue(fallen_fruit).

solved(C) :- chosen_culprit(C), chosen_clue(Cl), fits(Cl, C).

#show valid/3.
#show solved/1.
#show suspect_kind/1.
#show suspect_id/1.
#show fell_not_vanished/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOPPINGS:
        lines.append(asp.fact("topping", tid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for culprit_id in sorted(clue.for_culprits):
            lines.append(asp.fact("fits", clue_id, culprit_id))
    for fix in FIXES.values():
        for culprit_id in sorted(fix.for_culprits):
            lines.append(asp.fact("has_fix", culprit_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_solve(params: StoryParams) -> dict:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_culprit", params.culprit),
        asp.fact("chosen_clue", params.clue),
    ])
    model = asp.one_model(asp_program(scenario))
    return {
        "solved": asp.atoms(model, "solved"),
        "suspect_kind": asp.atoms(model, "suspect_kind"),
        "suspect_id": asp.atoms(model, "suspect_id"),
        "fell_not_vanished": bool(asp.atoms(model, "fell_not_vanished")),
    }


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    for params in cases:
        got = asp_solve(params)
        if not got["solved"] or got["solved"][0][0] != params.culprit:
            rc = 1
            print(f"MISMATCH in solved culprit for {params}.")
            break
        pred = predict_solution(
            tell(
                setting=SETTINGS[params.setting],
                topping=TOPPINGS[params.topping],
                culprit=CULPRITS[params.culprit],
                clue=CLUES[params.clue],
                child_name=params.child_name,
                child_gender=params.child_gender,
                caregiver_type=params.caregiver,
                child_trait=params.trait,
            ),
            params.culprit,
            params.clue,
        )
        asp_kind = got["suspect_kind"][0][0] if got["suspect_kind"] else ""
        asp_id = got["suspect_id"][0][0] if got["suspect_id"] else ""
        if pred["suspect_kind"] != asp_kind or pred["suspect_id"] != asp_id or pred["fell_not_vanished"] != got["fell_not_vanished"]:
            rc = 1
            print(f"MISMATCH in clue reasoning for {params}.")
            break

    try:
        sample = generate(CURATED[0])
        if not sample.story or "wreath" not in sample.story or "food-dim" not in sample.story or "growned" not in sample.story:
            raise StoryError("Smoke test failed: generated story missing required seeded content.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime mystery storyworld: a bread wreath, a missing topping, a flashback, and a gentle solution."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--topping", choices=TOPPINGS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=CAREGIVERS)
    ap.add_argument("--trait", choices=TRAITS)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.clue:
        culprit = CULPRITS[args.culprit]
        clue = CLUES[args.clue]
        if not clue_matches(culprit, clue):
            raise StoryError(explain_rejection(culprit, clue))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, culprit_id, clue_id = rng.choice(sorted(combos))
    topping_id = args.topping or rng.choice(sorted(TOPPINGS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        topping=topping_id,
        culprit=culprit_id,
        clue=clue_id,
        child_name=name,
        child_gender=gender,
        caregiver=caregiver,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.topping not in TOPPINGS:
        raise StoryError(f"(Unknown topping: {params.topping})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.child_gender})")
    if params.caregiver not in CAREGIVERS:
        raise StoryError(f"(Unknown caregiver: {params.caregiver})")

    culprit = CULPRITS[params.culprit]
    clue = CLUES[params.clue]
    if not clue_matches(culprit, clue):
        raise StoryError(explain_rejection(culprit, clue))

    world = tell(
        setting=SETTINGS[params.setting],
        topping=TOPPINGS[params.topping],
        culprit=culprit,
        clue=clue,
        child_name=params.child_name,
        child_gender=params.child_gender,
        caregiver_type=params.caregiver,
        child_trait=params.trait,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, culprit, clue) combos:\n")
        for setting_id, culprit_id, clue_id in combos:
            print(f"  {setting_id:8} {culprit_id:6} {clue_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.culprit} / {p.clue} / {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
