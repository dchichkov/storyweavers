#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/environment_hand_pl_dim_humor_mystery_to.py
======================================================================

A standalone storyworld about a child doing a small home project when a desk lamp
keeps going dim. The child notices the odd label "hand-pl-dim" on the lamp and
treats it like a clue in a tiny household mystery. The real answer is funny and
ordinary: a cat tail, a little sibling's curious finger, or the child's own elbow
has been brushing the dimmer. The ending restores the light and proves the family
changed the setup.

Run it
------
    python storyworlds/worlds/gpt-5.4/environment_hand_pl_dim_humor_mystery_to.py
    python storyworlds/worlds/gpt-5.4/environment_hand_pl_dim_humor_mystery_to.py --setting bedroom_desk --culprit cat_tail
    python storyworlds/worlds/gpt-5.4/environment_hand_pl_dim_humor_mystery_to.py --fix blame_ghost
    python storyworlds/worlds/gpt-5.4/environment_hand_pl_dim_humor_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/environment_hand_pl_dim_humor_mystery_to.py --qa --json
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
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "grandpa", "man"}
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
            "grandpa": "grandpa",
            "aunt": "aunt",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
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
    place: str
    scene: str
    has_cat: bool = False
    has_sibling: bool = False
    crowded: bool = False
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
class Project:
    id: str
    noun: str
    setup: str
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


@dataclass
class Culprit:
    id: str
    label: str
    reveal: str
    clue: str
    requires: set[str] = field(default_factory=set)
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
    sense: int
    label: str
    action: str
    ending: str
    matches: set[str] = field(default_factory=set)
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
    "bedroom_desk": Setting(
        id="bedroom_desk",
        place="the bedroom desk",
        scene="A small lamp stood beside a cup of crayons and a stack of paper birds.",
        has_cat=True,
        has_sibling=False,
        crowded=True,
        tags={"lamp", "desk"},
    ),
    "kitchen_table": Setting(
        id="kitchen_table",
        place="the kitchen table",
        scene="A fruit bowl, a glue stick, and yesterday's mail shared the table without much elbow room.",
        has_cat=False,
        has_sibling=True,
        crowded=True,
        tags={"lamp", "table"},
    ),
    "hallway_bench": Setting(
        id="hallway_bench",
        place="the hallway bench",
        scene="Shoes waited below, scarves drooped from hooks, and the lamp made a warm yellow puddle on the bench.",
        has_cat=True,
        has_sibling=True,
        crowded=False,
        tags={"lamp", "hallway"},
    ),
}

PROJECTS = {
    "poster": Project(
        id="poster",
        noun="environment poster",
        setup="was making an environment poster for school, full of green leaves and smiling recycling bins",
        ending="The finished environment poster looked bright enough to cheer up the whole room.",
        tags={"environment", "school"},
    ),
    "chart": Project(
        id="chart",
        noun="environment chart",
        setup="was making an environment chart for school, with boxes for paper, glass, and food scraps",
        ending="The environment chart ended up neat and bright, with every box easy to read.",
        tags={"environment", "school"},
    ),
    "collage": Project(
        id="collage",
        noun="environment collage",
        setup="was making an environment collage for school, gluing tiny leaves beside pictures of buses and bikes",
        ending="The environment collage glowed in the fresh light, and every little leaf could be seen.",
        tags={"environment", "school"},
    ),
}

CULPRITS = {
    "cat_tail": Culprit(
        id="cat_tail",
        label="the cat's tail",
        reveal="the family cat kept flicking its tail across the shiny touch strip",
        clue="A stripe of orange fur lay beside the lamp, and the ribbon on the chair kept twitching.",
        requires={"has_cat"},
        tags={"cat", "touch_lamp"},
    ),
    "sibling_poke": Culprit(
        id="sibling_poke",
        label="a little sibling's finger",
        reveal="a little sibling had been stretching up to poke the glowing strip just to see what happened",
        clue="A tiny sticky fingerprint sat on the silver strip, and a quiet giggle came from under the table.",
        requires={"has_sibling"},
        tags={"sibling", "touch_lamp"},
    ),
    "elbow_bump": Culprit(
        id="elbow_bump",
        label="the child's own elbow",
        reveal="the child had been leaning over the page and brushing the dimmer with an elbow every time a marker rolled away",
        clue="There was a soft blue smudge on a sleeve and a crooked pile of markers crowding the lamp base.",
        requires={"crowded"},
        tags={"self", "touch_lamp"},
    ),
}

FIXES = {
    "cat_basket": Fix(
        id="cat_basket",
        sense=3,
        label="move the ribbon and set out the cat's basket",
        action="moved the ribbon away from the lamp and set the cat's basket on the other side of the room",
        ending="The cat curled into the basket instead, and the lamp stayed bright.",
        matches={"cat_tail"},
        tags={"cat", "solution"},
    ),
    "sibling_light": Fix(
        id="sibling_light",
        sense=3,
        label="give the little sibling a click light",
        action="handed the little sibling a tiny click light and a scrap of paper so there was a button meant just for small fingers",
        ending="The little sibling clicked happily on the floor, and the big lamp stopped dimming.",
        matches={"sibling_poke"},
        tags={"sibling", "solution"},
    ),
    "clear_space": Fix(
        id="clear_space",
        sense=3,
        label="clear the crowded work space",
        action="slid the markers into a cup and moved the lamp a little farther back, making room for elbows and paper",
        ending="With space around the lamp, no wandering elbow touched the strip again.",
        matches={"elbow_bump"},
        tags={"self", "solution"},
    ),
    "blame_ghost": Fix(
        id="blame_ghost",
        sense=1,
        label="blame a ghost",
        action="announced that maybe a ghost liked low light",
        ending="That did not help the lamp at all.",
        matches=set(),
        tags={"joke"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Noah", "Eli", "Theo", "Finn"]
TRAITS = ["careful", "curious", "busy", "cheerful", "thoughtful", "playful"]
HELPERS = ["mother", "father", "grandpa", "aunt"]


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def setting_supports(setting: Setting, culprit: Culprit) -> bool:
    req = culprit.requires
    return (
        ("has_cat" not in req or setting.has_cat)
        and ("has_sibling" not in req or setting.has_sibling)
        and ("crowded" not in req or setting.crowded)
    )


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def fix_matches(culprit_id: str, fix_id: str) -> bool:
    if culprit_id not in CULPRITS or fix_id not in FIXES:
        return False
    return culprit_id in FIXES[fix_id].matches


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for culprit_id, culprit in CULPRITS.items():
            if not setting_supports(setting, culprit):
                continue
            for fix in sensible_fixes():
                if culprit_id in fix.matches:
                    combos.append((setting_id, culprit_id, fix.id))
    return combos


def explain_setting_rejection(setting: Setting, culprit: Culprit) -> str:
    if "has_cat" in culprit.requires and not setting.has_cat:
        return (
            f"(No story: {setting.place} has no cat in this world, so a cat tail "
            f"cannot be the culprit there.)"
        )
    if "has_sibling" in culprit.requires and not setting.has_sibling:
        return (
            f"(No story: {setting.place} has no little sibling nearby, so that clue "
            f"would not make sense there.)"
        )
    if "crowded" in culprit.requires and not setting.crowded:
        return (
            f"(No story: {setting.place} is not crowded enough for an elbow-bump "
            f"mystery. The dimming needs a plausible physical cause.)"
        )
    return "(No story: that setting does not support this culprit.)"


def explain_fix_rejection(fix_id: str) -> str:
    fix = FIXES[fix_id]
    if fix.sense < SENSE_MIN:
        better = ", ".join(sorted(f.id for f in sensible_fixes()))
        return (
            f"(Refusing fix '{fix_id}': it is too silly to solve the mystery "
            f"(sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return "(No story: that fix does not match the real cause of the dim lamp.)"


# ---------------------------------------------------------------------------
# World model and rules
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


def _r_mystery(world: World) -> list[str]:
    lamp = world.get("lamp")
    child = world.get("child")
    if lamp.meters["brightness"] >= THRESHOLD:
        return []
    sig = ("mystery",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    world.facts["mystery_started"] = True
    return ["__mystery__"]


def _r_relief(world: World) -> list[str]:
    lamp = world.get("lamp")
    child = world.get("child")
    if lamp.meters["brightness"] < THRESHOLD:
        return []
    if not world.facts.get("mystery_started"):
        return []
    if not world.facts.get("solved"):
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="mystery", tag="emotion", apply=_r_mystery),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity, project: Project) -> None:
    world.say(
        f"After supper, {child.id} sat at {world.setting.place}. "
        f"{world.setting.scene}"
    )
    world.say(
        f"{child.pronoun().capitalize()} {project.setup}. "
        f'{helper.label_word.capitalize()} said the room looked very busy already.'
    )


def show_lamp(world: World) -> None:
    world.say(
        'On the lamp base was a tiny silver label that said "hand-pl-dim." '
        "It looked much too secret for such an ordinary evening."
    )


def work_begins(world: World, child: Entity, project: Project) -> None:
    child.memes["focus"] += 1
    world.say(
        f"{child.id} bent over the {project.noun}, choosing colors very seriously "
        "and humming in a crooked little tune."
    )


def lamp_dims(world: World, child: Entity) -> None:
    lamp = world.get("lamp")
    lamp.meters["brightness"] = 0.0
    lamp.meters["dimmed_times"] += 1
    propagate(world, narrate=False)
    world.say(
        "Then the light slid from bright to soft and dim, as if the room had taken a tiny sleepy sigh."
    )
    world.say(
        f'{child.id} blinked. "Who keeps doing that?" {child.pronoun()} asked.'
    )


def investigate(world: World, child: Entity, helper: Entity, culprit: Culprit) -> None:
    child.memes["curiosity"] += 1
    helper.memes["patience"] += 1
    world.say(
        f"{child.id} looked under the paper, behind the crayons, and even up at the ceiling."
    )
    world.say(
        f"{culprit.clue} {helper.label_word.capitalize()} did not laugh right away, but a smile began to sneak across {helper.pronoun('possessive')} face."
    )
    world.say(
        f'"Maybe the clue and the funny little label go together," {helper.label_word} said.'
    )


def make_guess(world: World, child: Entity) -> None:
    child.memes["humor"] += 1
    world.say(
        f'"I thought hand-pl-dim might be the name of a very small detective," {child.id} admitted.'
    )


def reveal(world: World, child: Entity, helper: Entity, culprit: Culprit) -> None:
    world.facts["culprit_revealed"] = True
    child.memes["surprise"] += 1
    child.memes["giggles"] += 1
    world.say(
        f"Then they saw it plainly: {culprit.reveal}."
    )
    world.say(
        f'{helper.label_word.capitalize()} pointed to the strip on the lamp. "It is not a code," {helper.pronoun()} said. "It means you can press it by hand to make it dim."'
    )
    world.say(
        f"{child.id} stared for one second and then laughed so hard that the paper leaves wiggled."
    )


def apply_fix(world: World, child: Entity, helper: Entity, fix: Fix) -> None:
    lamp = world.get("lamp")
    world.facts["solved"] = True
    fix_ent = world.get("fix")
    fix_ent.meters["used"] += 1
    lamp.meters["brightness"] = 2.0
    lamp.meters["steady"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {fix.action}. Then {helper.label_word} tapped the lamp back to bright."
    )
    world.say(fix.ending)
    child.memes["focus"] += 1


def finish_project(world: World, child: Entity, project: Project) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Soon {child.id} was back to work, and {project.ending}"
    )
    world.say(
        "The mystery had turned out to be part clue, part misunderstanding, and part family comedy."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    project: Project,
    culprit: Culprit,
    fix: Fix,
    *,
    child_name: str = "Lily",
    child_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "curious",
    sibling_name: str = "Nell",
    pet_name: str = "Pip",
) -> World:
    world = World(setting)

    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={"project": project.id},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            attrs={},
        )
    )
    lamp = world.add(
        Entity(
            id="lamp",
            kind="thing",
            type="lamp",
            label="desk lamp",
            attrs={"label_text": "hand-pl-dim"},
        )
    )
    culprit_ent = world.add(
        Entity(
            id="culprit",
            kind="thing",
            type="cause",
            label=culprit.label,
            attrs={"culprit_id": culprit.id, "pet_name": pet_name, "sibling_name": sibling_name},
        )
    )
    fix_ent = world.add(
        Entity(
            id="fix",
            kind="thing",
            type="fix",
            label=fix.label,
            attrs={"fix_id": fix.id},
        )
    )

    lamp.meters["brightness"] = 2.0
    lamp.meters["dimmed_times"] = 0.0
    lamp.meters["steady"] = 0.0
    child.memes["focus"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["surprise"] = 0.0
    child.memes["giggles"] = 0.0
    child.memes["joy"] = 0.0
    helper.memes["patience"] = 0.0
    fix_ent.meters["used"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        lamp=lamp,
        project=project,
        culprit=culprit,
        fix=fix,
        setting=setting,
        solved=False,
        mystery_started=False,
        culprit_revealed=False,
        sibling_name=sibling_name,
        pet_name=pet_name,
    )

    introduce(world, child, helper, project)
    show_lamp(world)
    work_begins(world, child, project)

    world.para()
    lamp_dims(world, child)
    investigate(world, child, helper, culprit)
    make_guess(world, child)

    world.para()
    reveal(world, child, helper, culprit)
    apply_fix(world, child, helper, fix)
    finish_project(world, child, project)
    return world


# ---------------------------------------------------------------------------
# Standard interface dataclass
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    project: str
    culprit: str
    fix: str
    child_name: str
    child_gender: str
    helper: str
    trait: str
    sibling_name: str = "Nell"
    pet_name: str = "Pip"
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
    "environment": [
        (
            "What does environment mean?",
            "Environment means the world around us, like the air, water, plants, animals, and the places where people live. When children make an environment poster, they are learning how to take care of those shared places."
        )
    ],
    "touch_lamp": [
        (
            "What is a touch lamp?",
            "A touch lamp is a lamp that changes when you tap or press part of it with your hand. Some touch lamps can switch between bright and dim light very easily."
        )
    ],
    "cat": [
        (
            "Why do cats knock or tap things by accident?",
            "Cats explore with their paws, whiskers, and tails, so they sometimes bump objects without meaning to. That can make a light switch or button change when a cat is nearby."
        )
    ],
    "sibling": [
        (
            "Why do little children press buttons?",
            "Little children are curious, so buttons and glowing strips are very tempting to test. They often want to see what will happen next."
        )
    ],
    "solution": [
        (
            "What is a good way to solve a small household mystery?",
            "Look for real clues, notice who was nearby, and try a simple fix that matches the cause. A calm guess is better than a wild one."
        )
    ],
    "lamp": [
        (
            "Why is bright light helpful for drawing or reading?",
            "Bright light helps your eyes see lines, colors, and small details more clearly. When the light goes dim, work can feel slower and more confusing."
        )
    ],
}
KNOWLEDGE_ORDER = ["environment", "lamp", "touch_lamp", "cat", "sibling", "solution"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    project = world.facts["project"]
    culprit = world.facts["culprit"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "environment" and "hand-pl-dim".',
        f"Tell a gentle home mystery where {child.id} is making a {project.noun}, the lamp goes dim, and the funny answer turns out to involve {culprit.label}.",
        "Write a child-facing story with humor, a mystery to solve, and a small surprise at the end, where the problem is solved by noticing ordinary clues.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    project = world.facts["project"]
    culprit = world.facts["culprit"]
    fix = world.facts["fix"]
    setting = world.facts["setting"]
    lamp = world.facts["lamp"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was working at {setting.place}, and {helper.label_word} who helped solve the problem. The story stays close to an ordinary family evening."
        ),
        (
            f"What was {child.id} making?",
            f"{child.id} was making a {project.noun} for school. The project mattered because {child.pronoun()} wanted the page bright enough to see every little detail."
        ),
        (
            'Why did the words "hand-pl-dim" seem mysterious?',
            f'The label looked like a secret clue because the lamp kept going dim at the same time. {child.id} did not know at first that the words were really instructions for the touch dimmer.'
        ),
        (
            "What clue helped them solve the mystery?",
            f"{culprit.clue} That clue pointed them toward the real cause instead of a silly guess."
        ),
        (
            "What was the real answer?",
            f"The real answer was {culprit.label}. The surprise was funny because the mystery felt dramatic, but the cause was small and ordinary."
        ),
        (
            "How did they fix the lamp problem?",
            f"They {fix.action}. That matched the real cause, so the lamp stayed bright instead of dimming again."
        ),
        (
            f"How did {child.id} feel at the end?",
            f"{child.id} felt relieved, proud, and giggly. Once the light stayed steady, {child.pronoun()} could finish the school project in a calm, happy way."
        ),
    ]
    if lamp.meters["dimmed_times"] >= THRESHOLD:
        qa.append(
            (
                "Why was the dim light a problem?",
                f"The dim light made it harder for {child.id} to work on the page. Because the project had little lines and colors, the fading lamp turned a normal evening into a mystery to solve."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"solution", "lamp"}
    tags |= set(world.facts["project"].tags)
    tags |= set(world.facts["culprit"].tags)
    tags |= set(world.facts["fix"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits: list[str] = []
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
supports(S, C) :- setting(S), culprit(C), requires(C, cat), has_cat(S).
supports(S, C) :- setting(S), culprit(C), requires(C, sibling), has_sibling(S).
supports(S, C) :- setting(S), culprit(C), requires(C, crowded), crowded(S).

ok_requirements(S, C) :- culprit(C), not needs_req(C).
ok_requirements(S, C) :- setting(S), culprit(C), needs_req(C),
                         not bad_req(S, C).

needs_req(C) :- requires(C, _).
bad_req(S, C) :- requires(C, cat), not has_cat(S).
bad_req(S, C) :- requires(C, sibling), not has_sibling(S).
bad_req(S, C) :- requires(C, crowded), not crowded(S).

sensible(F) :- fix(F), sense(F, N), sense_min(M), N >= M.
valid(S, C, F) :- setting(S), culprit(C), fix(F),
                  ok_requirements(S, C), sensible(F), matches(F, C).

solved(F, C) :- matches(F, C), sensible(F).
#show valid/3.
#show sensible/1.
#show solved/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.has_cat:
            lines.append(asp.fact("has_cat", sid))
        if setting.has_sibling:
            lines.append(asp.fact("has_sibling", sid))
        if setting.crowded:
            lines.append(asp.fact("crowded", sid))
    for cid, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        for req in sorted(culprit.requires):
            name = {"has_cat": "cat", "has_sibling": "sibling", "crowded": "crowded"}[req]
            lines.append(asp.fact("requires", cid, name))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        for cid in sorted(fix.matches):
            lines.append(asp.fact("matches", fid, cid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    py_sensible = {fix.id for fix in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible fixes:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sens))

    # Smoke test normal generation and emission.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    # Extra random generation checks through resolve_params().
    parser = build_parser()
    for seed in range(10):
        try:
            args = parser.parse_args(["--seed", str(seed)])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story from random resolve_params")
        except Exception as exc:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {exc}")
            break

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="bedroom_desk",
        project="poster",
        culprit="cat_tail",
        fix="cat_basket",
        child_name="Lily",
        child_gender="girl",
        helper="mother",
        trait="curious",
        pet_name="Pip",
        sibling_name="Nell",
    ),
    StoryParams(
        setting="kitchen_table",
        project="chart",
        culprit="sibling_poke",
        fix="sibling_light",
        child_name="Ben",
        child_gender="boy",
        helper="father",
        trait="thoughtful",
        sibling_name="Mila",
        pet_name="Pip",
    ),
    StoryParams(
        setting="bedroom_desk",
        project="collage",
        culprit="elbow_bump",
        fix="clear_space",
        child_name="Maya",
        child_gender="girl",
        helper="grandpa",
        trait="busy",
        sibling_name="Nell",
        pet_name="Pip",
    ),
    StoryParams(
        setting="hallway_bench",
        project="poster",
        culprit="cat_tail",
        fix="cat_basket",
        child_name="Theo",
        child_gender="boy",
        helper="aunt",
        trait="cheerful",
        sibling_name="June",
        pet_name="Pip",
    ),
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small slice-of-life mystery storyworld about a lamp that keeps dimming."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.culprit:
        setting = SETTINGS[args.setting]
        culprit = CULPRITS[args.culprit]
        if not setting_supports(setting, culprit):
            raise StoryError(explain_setting_rejection(setting, culprit))
    if args.fix:
        if args.fix not in FIXES:
            raise StoryError("(Unknown fix.)")
        if FIXES[args.fix].sense < SENSE_MIN:
            raise StoryError(explain_fix_rejection(args.fix))
    if args.culprit and args.fix and not fix_matches(args.culprit, args.fix):
        raise StoryError(explain_fix_rejection(args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, culprit_id, fix_id = rng.choice(sorted(combos))
    project_id = args.project or rng.choice(sorted(PROJECTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    sibling_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    pet_name = rng.choice(["Pip", "Marmalade", "Bean", "Pebble"])

    return StoryParams(
        setting=setting_id,
        project=project_id,
        culprit=culprit_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=gender,
        helper=helper,
        trait=trait,
        sibling_name=sibling_name,
        pet_name=pet_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.child_gender})")

    setting = SETTINGS[params.setting]
    culprit = CULPRITS[params.culprit]
    fix = FIXES[params.fix]
    if not setting_supports(setting, culprit):
        raise StoryError(explain_setting_rejection(setting, culprit))
    if fix.sense < SENSE_MIN or params.culprit not in fix.matches:
        raise StoryError(explain_fix_rejection(params.fix))

    world = tell(
        setting=setting,
        project=PROJECTS[params.project],
        culprit=culprit,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper,
        trait=params.trait,
        sibling_name=params.sibling_name,
        pet_name=params.pet_name,
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
        sensible = asp_sensible()
        print(f"sensible fixes: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (setting, culprit, fix) combos:\n")
        for setting_id, culprit_id, fix_id in combos:
            print(f"  {setting_id:13} {culprit_id:13} {fix_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.project} at {p.setting} ({p.culprit} -> {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
