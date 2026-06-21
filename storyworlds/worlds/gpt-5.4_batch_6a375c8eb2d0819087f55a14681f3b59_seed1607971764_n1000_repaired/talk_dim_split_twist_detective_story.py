#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py
==================================================================

A standalone story world for a small child-facing detective tale with a twist:
a prized object seems stolen, a clue points to the wrong conclusion, and the
young detective learns that asking before accusing matters.

The required seed words appear in the story world itself:
- "talk-dim" is a strange note the detective finds and misreads.
- "split" appears in the detective's search decision.

Run it
------
    python storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py
    python storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py --setting classroom --item badge
    python storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py --item badge --fix wash
    python storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/talk_dim_split_twist_detective_story.py --verify
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "teacher_f", "librarian_f"}
        male = {"boy", "man", "teacher_m", "librarian_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Registries
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
    label: str
    event: str
    affords: set[str] = field(default_factory=set)
    hideout_labels: dict[str, str] = field(default_factory=dict)
    dim_place: str = ""
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
class MissingThing:
    id: str
    label: str
    phrase: str
    material: str
    use_line: str
    ending_line: str
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
class Issue:
    id: str
    label: str
    material: str
    evidence_line: str
    problem_line: str
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
    material: str
    needs: str
    action_line: str
    result_line: str
    qa_line: str
    clue_mark: str
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
    for_fix: str
    found_line: str
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
    "classroom": Setting(
        id="classroom",
        label="the classroom",
        event="afternoon show-and-tell",
        affords={"work_table", "wash_sink"},
        hideout_labels={
            "work_table": "the craft table by the window",
            "wash_sink": "the little sink beside the paint jars",
        },
        dim_place="the coat nook under the low shelf",
        tags={"school", "detective"},
    ),
    "library": Setting(
        id="library",
        label="the library corner",
        event="story hour",
        affords={"work_table"},
        hideout_labels={
            "work_table": "the repair desk beside the atlas shelf",
        },
        dim_place="the shadowy corner behind the tall map stand",
        tags={"library", "detective"},
    ),
    "clubhouse": Setting(
        id="clubhouse",
        label="the clubhouse",
        event="junior detective meeting",
        affords={"work_table", "wash_sink"},
        hideout_labels={
            "work_table": "the old table under the round window",
            "wash_sink": "the tiny sink near the cocoa mugs",
        },
        dim_place="the dim loft above the coat pegs",
        tags={"clubhouse", "detective"},
    ),
}

ITEMS = {
    "badge": MissingThing(
        id="badge",
        label="detective badge",
        phrase="the shiny detective badge",
        material="metal",
        use_line="It was the piece that made the detective coat feel official.",
        ending_line="The badge flashed on the coat like a small silver moon.",
        tags={"badge", "metal"},
    ),
    "cape": MissingThing(
        id="cape",
        label="midnight cape",
        phrase="the midnight cape",
        material="cloth",
        use_line="It swirled behind the wearer and made every step feel brave.",
        ending_line="The cape floated behind the child like a dark, happy wave.",
        tags={"cape", "cloth"},
    ),
    "map": MissingThing(
        id="map",
        label="treasure map",
        phrase="the folded treasure map",
        material="paper",
        use_line="Without it, the whole mystery game had no ending.",
        ending_line="The map opened smooth and bright, ready to lead the case again.",
        tags={"map", "paper"},
    ),
}

ISSUES = {
    "tarnish": Issue(
        id="tarnish",
        label="a dull gray smudge",
        material="metal",
        evidence_line="a thumb-sized gray smear",
        problem_line="It had gone dull and cloudy instead of bright.",
        tags={"metal", "care"},
    ),
    "jam": Issue(
        id="jam",
        label="a sticky berry stain",
        material="cloth",
        evidence_line="a sweet purple spot",
        problem_line="A sticky berry stain would have marked it for the whole event.",
        tags={"cloth", "washing"},
    ),
    "split_fold": Issue(
        id="split_fold",
        label="a split fold",
        material="paper",
        evidence_line="a bent corner with a tiny crack",
        problem_line="One fold had split, and another hard tug could have torn it in two.",
        tags={"paper", "repair"},
    ),
}

FIXES = {
    "polish": Fix(
        id="polish",
        label="polish",
        material="metal",
        needs="work_table",
        action_line="rubbing the metal in careful circles with a soft cloth",
        result_line="until the silver shine came back",
        qa_line="polished the badge with a soft cloth",
        clue_mark="soft cloth",
        tags={"polish", "care"},
    ),
    "wash": Fix(
        id="wash",
        label="wash",
        material="cloth",
        needs="wash_sink",
        action_line="dabbing the cloth with warm water and soap",
        result_line="until the sticky stain faded away",
        qa_line="washed the cape gently at the sink",
        clue_mark="soap bubble",
        tags={"wash", "care"},
    ),
    "tape": Fix(
        id="tape",
        label="tape",
        material="paper",
        needs="work_table",
        action_line="laying the paper flat and pressing a neat strip of tape over the weak fold",
        result_line="so the map could open without tearing",
        qa_line="mended the split fold with a neat strip of tape",
        clue_mark="tape strip",
        tags={"repair", "paper"},
    ),
}

CLUES = {
    "cloth": Clue(
        id="cloth",
        label="soft cloth",
        for_fix="polish",
        found_line="A square of soft gray cloth lay under the bench like a quiet clue.",
        tags={"clue", "polish"},
    ),
    "bubble": Clue(
        id="bubble",
        label="soap bubble",
        for_fix="wash",
        found_line="A tiny soap bubble clung to the floorboard, shining in the light.",
        tags={"clue", "wash"},
    ),
    "tape_strip": Clue(
        id="tape_strip",
        label="tape strip",
        for_fix="tape",
        found_line="A short strip of striped tape stuck to the floor near the shelf.",
        tags={"clue", "repair"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lena", "Ivy", "Tess", "June", "Maya", "Cora"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Leo", "Jude", "Evan", "Nico", "Theo"]
HELPER_TRAITS = ["careful", "kind", "quiet", "patient"]
DETECTIVE_TRAITS = ["sharp-eyed", "curious", "steady", "thoughtful"]


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


def _r_case_open(world: World) -> list[str]:
    item = world.get("item")
    detective = world.get("detective")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("case_open", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["worry"] += 1
    detective.memes["focus"] += 1
    return []


def _r_suspicion(world: World) -> list[str]:
    detective = world.get("detective")
    helper = world.get("helper")
    if world.facts.get("clue_found", 0) < THRESHOLD:
        return []
    if world.facts.get("note_misread", 0) < THRESHOLD:
        return []
    sig = ("suspicion", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["suspicion"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    item = world.get("item")
    detective = world.get("detective")
    helper = world.get("helper")
    if item.meters["repaired"] < THRESHOLD:
        return []
    sig = ("relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["relief"] += 1
    helper.memes["pride"] += 1
    return []


def _r_apology(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.memes["suspicion"] < THRESHOLD:
        return []
    if world.facts.get("innocence_revealed", 0) < THRESHOLD:
        return []
    sig = ("apology", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["shame"] += 1
    detective.memes["respect"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="case_open", tag="emotion", apply=_r_case_open),
    Rule(name="suspicion", tag="emotion", apply=_r_suspicion),
    Rule(name="relief", tag="emotion", apply=_r_relief),
    Rule(name="apology", tag="emotion", apply=_r_apology),
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


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def item_issue_match(item: MissingThing, issue: Issue) -> bool:
    return item.material == issue.material


def item_fix_match(item: MissingThing, fix: Fix) -> bool:
    return item.material == fix.material


def clue_fix_match(clue: Clue, fix: Fix) -> bool:
    return clue.for_fix == fix.id


def setting_supports_fix(setting: Setting, fix: Fix) -> bool:
    return fix.needs in setting.affords


def valid_combo(setting: Setting, item: MissingThing, issue: Issue, fix: Fix, clue: Clue) -> bool:
    return (
        item_issue_match(item, issue)
        and item_fix_match(item, fix)
        and clue_fix_match(clue, fix)
        and setting_supports_fix(setting, fix)
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for issue_id, issue in ISSUES.items():
                for fix_id, fix in FIXES.items():
                    for clue_id, clue in CLUES.items():
                        if valid_combo(setting, item, issue, fix, clue):
                            combos.append((setting_id, item_id, issue_id, fix_id, clue_id))
    return combos


def explain_rejection(setting: Setting, item: MissingThing, issue: Issue, fix: Fix, clue: Clue) -> str:
    if not item_issue_match(item, issue):
        return (
            f"(No story: {issue.label} does not fit a {item.label}. "
            f"The problem must match the object's material.)"
        )
    if not item_fix_match(item, fix):
        return (
            f"(No story: {fix.label} is not a sensible way to fix a {item.label}. "
            f"Choose a fix that matches the object's material.)"
        )
    if not clue_fix_match(clue, fix):
        return (
            f"(No story: the clue '{clue.label}' points to a different kind of repair. "
            f"The clue must honestly match the hidden fixing method.)"
        )
    if not setting_supports_fix(setting, fix):
        return (
            f"(No story: {setting.label} has no place for the helper to {fix.label} the "
            f"{item.label}. The setting must afford the needed repair spot.)"
        )
    return "(No story: this combination is unreasonable.)"


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, detective: Entity, sidekick: Entity, setting: Setting) -> None:
    world.say(
        f"In {setting.label}, {detective.id} and {sidekick.id} liked to pretend they were real detectives. "
        f"{detective.id} was {detective.traits[0]}, and {sidekick.id} stayed close to notice the small things."
    )


def show_event(world: World, item: MissingThing, teacher: Entity, setting: Setting) -> None:
    world.say(
        f"That day they were getting ready for {setting.event}. "
        f"{teacher.id} had promised that the best clue-finder could carry {item.phrase} first."
    )
    world.say(item.use_line)


def discover_missing(world: World, detective: Entity, item_ent: Entity, item_cfg: MissingThing) -> None:
    item_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {detective.id} opened the costume box, the {item_cfg.label} was gone."
    )
    if detective.memes["worry"] >= THRESHOLD:
        world.say(
            f"{detective.id}'s heart gave a small thump. A case had opened right in the middle of the room."
        )


def first_clues(
    world: World,
    detective: Entity,
    sidekick: Entity,
    helper: Entity,
    clue: Clue,
    issue: Issue,
    setting: Setting,
) -> None:
    world.facts["clue_found"] = 1.0
    world.facts["note_misread"] = 1.0
    propagate(world, narrate=False)
    world.say(clue.found_line)
    world.say(
        f"Beside it lay a folded scrap of paper with one strange word on it: talk-dim."
    )
    world.say(
        f'"Should we split and search both sides of {setting.label}?" {sidekick.id} whispered.'
    )
    world.say(
        f'"Not yet," said {detective.id}. "A fresh clue can talk if we stay with it."'
    )
    world.say(
        f"{detective.id} remembered seeing {helper.id} nearby earlier, and the clue plus the odd note made the case feel sharper and more suspicious."
    )
    world.say(
        f"{detective.id} looked around and noticed {issue.evidence_line} near the box as well."
    )


def follow_trail(world: World, detective: Entity, sidekick: Entity, setting: Setting, fix: Fix) -> None:
    place = setting.hideout_labels[fix.needs]
    world.say(
        f"The two young detectives followed the tiny signs toward {place}. "
        f"They passed {setting.dim_place}, where the light went soft and shadowy."
    )
    world.say(
        f"For one second, the case felt spooky, but the clue was stronger than the fear."
    )


def reveal(
    world: World,
    detective: Entity,
    sidekick: Entity,
    helper: Entity,
    item_ent: Entity,
    item_cfg: MissingThing,
    issue: Issue,
    fix: Fix,
    setting: Setting,
) -> None:
    item_ent.meters["missing"] = 0.0
    item_ent.meters["repaired"] += 1
    item_ent.meters["damaged"] = 0.0
    world.facts["innocence_revealed"] = 1.0
    propagate(world, narrate=False)
    place = setting.hideout_labels[fix.needs]
    world.say(
        f"There they found {helper.id} at {place}, {fix.action_line} {item_cfg.phrase} {fix.result_line}."
    )
    world.say(
        f'{helper.id} looked up in surprise. "I was trying to help," {helper.pronoun()} said. '
        f'"{issue.problem_line} I wanted to bring it back looking better than before."'
    )
    world.say(
        f"Then the whole mystery turned inside out. {detective.id} had not found a thief at all, only a careful helper keeping a surprise secret."
    )
    world.say(
        f'The note did not mean a crook\'s password. It was {helper.id}\'s reminder to "talk-dim" in a whisper so the surprise would not be spoiled.'
    )


def apology_and_return(
    world: World,
    detective: Entity,
    helper: Entity,
    item_cfg: MissingThing,
    teacher: Entity,
) -> None:
    world.say(
        f'{detective.id} felt {detective.pronoun("possessive")} cheeks grow warm. '
        f'"I was wrong," {detective.pronoun()} said. "I should have asked before I guessed."'
    )
    world.say(
        f"{helper.id} smiled and handed over the {item_cfg.label}. "
        f'"That is part of being a good detective too," said {teacher.id}. '
        f'"You look hard, and you listen hard."'
    )


def ending(
    world: World,
    detective: Entity,
    sidekick: Entity,
    helper: Entity,
    item_cfg: MissingThing,
) -> None:
    world.say(
        f"Soon {detective.id}, {sidekick.id}, and {helper.id} stood together for the event, and {item_cfg.ending_line}"
    )
    world.say(
        f"After that, whenever {detective.id} opened a new case, {detective.pronoun()} remembered that the truest clue was not always the first one."
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def tell(
    setting: Setting,
    item: MissingThing,
    issue: Issue,
    fix: Fix,
    clue: Clue,
    detective_name: str = "Mira",
    detective_gender: str = "girl",
    sidekick_name: str = "Owen",
    sidekick_gender: str = "boy",
    helper_name: str = "Nora",
    helper_gender: str = "girl",
    guide_type: str = "teacher_f",
) -> World:
    world = World(setting)

    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            label=detective_name,
            role="detective",
            traits=[DETECTIVE_TRAITS[0]],
            attrs={"job": "junior detective"},
        )
    )
    sidekick = world.add(
        Entity(
            id=sidekick_name,
            kind="character",
            type=sidekick_gender,
            label=sidekick_name,
            role="sidekick",
            traits=["loyal"],
            attrs={"job": "assistant"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
            traits=[HELPER_TRAITS[0]],
            attrs={"secret_note": "talk-dim"},
        )
    )
    teacher = world.add(
        Entity(
            id="Ms. Hale" if guide_type == "teacher_f" else "Mr. Bell",
            kind="character",
            type=guide_type,
            label="the teacher",
            role="guide",
            traits=["calm"],
            attrs={},
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type=item.id,
            label=item.label,
            role="item",
            traits=[],
            attrs={"material": item.material},
        )
    )

    item_ent.meters["damaged"] = 1.0
    world.facts.update(
        detective=detective,
        sidekick=sidekick,
        helper=helper,
        teacher=teacher,
        item_cfg=item,
        issue=issue,
        fix=fix,
        clue=clue,
        setting=setting,
        hideout=setting.hideout_labels[fix.needs],
        clue_found=0.0,
        note_misread=0.0,
        innocence_revealed=0.0,
    )

    introduce(world, detective, sidekick, setting)
    show_event(world, item, teacher, setting)

    world.para()
    discover_missing(world, detective, item_ent, item)
    first_clues(world, detective, sidekick, helper, clue, issue, setting)

    world.para()
    follow_trail(world, detective, sidekick, setting, fix)
    reveal(world, detective, sidekick, helper, item_ent, item, issue, fix, setting)

    world.para()
    apology_and_return(world, detective, helper, item, teacher)
    ending(world, detective, sidekick, helper, item)

    world.facts.update(
        item=item_ent,
        solved=item_ent.meters["repaired"] >= THRESHOLD,
        twist=True,
        suspected_helper=detective.memes["suspicion"] >= THRESHOLD,
        apologized=detective.memes["shame"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    item: str
    issue: str
    fix: str
    clue: str
    detective: str
    detective_gender: str
    sidekick: str
    sidekick_gender: str
    helper: str
    helper_gender: str
    guide: str
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
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to figure out what really happened. A good detective also asks questions instead of guessing too fast."
        )
    ],
    "polish": [
        (
            "What does it mean to polish something metal?",
            "To polish metal is to rub it carefully so dull marks come off and the shine comes back. People do it gently so they do not scratch the surface."
        )
    ],
    "wash": [
        (
            "Why do cloth things sometimes need to be washed right away?",
            "Some stains sink in if they sit too long. Washing gently and quickly can help the cloth come clean before the mark stays."
        )
    ],
    "repair": [
        (
            "Why do people mend torn paper with tape?",
            "Tape can hold a weak place together so the paper does not tear farther. It is a simple way to help a map or picture last longer."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand something hidden. One clue may not tell the whole truth, so detectives look for more than one."
        )
    ],
    "asking": [
        (
            "Why is it good to ask before accusing someone?",
            "Asking gives the other person a chance to explain what really happened. Sometimes a thing that looks bad at first turns out to be kind or helpful."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "polish", "wash", "repair", "asking"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item_cfg"]
    setting = f["setting"]
    helper = f["helper"]
    detective = f["detective"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the word "talk-dim" and the word "split".',
        f"Tell a gentle mystery set in {setting.label} where {detective.id} thinks {helper.id} took a missing {item.label}, but the twist is that the object was being secretly fixed.",
        f"Write a child-facing detective tale with a clue, a wrong guess, and a kind twist ending where asking questions matters more than accusing."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    sidekick = f["sidekick"]
    helper = f["helper"]
    teacher = f["teacher"]
    item = f["item_cfg"]
    issue = f["issue"]
    fix = f["fix"]
    setting = f["setting"]
    place = f["hideout"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a young detective, {sidekick.id}, the sidekick, and {helper.id}, who seemed suspicious at first. It also includes {teacher.id}, who helps explain the truth at the end."
        ),
        (
            f"What was missing?",
            f"The missing thing was the {item.label}. Losing it mattered because {item.use_line.lower()}"
        ),
        (
            f"Why did {detective.id} first suspect {helper.id}?",
            f"{detective.id} found {f['clue'].label} and the odd note that said talk-dim, and remembered seeing {helper.id} nearby. Those signs pointed in {helper.pronoun('possessive')} direction, so the first guess felt like a theft case."
        ),
        (
            "Why did they not split up when they searched?",
            f"{detective.id} decided not to split because the clue was fresh and might lead somewhere if they stayed with it. Keeping together also made the dim part of {setting.label} feel less frightening."
        ),
        (
            "What was the twist?",
            f"The twist was that {helper.id} had not stolen the {item.label} at all. {helper.pronoun().capitalize()} had taken it to {fix.label} it because of {issue.label}, hoping to return it as a surprise."
        ),
        (
            f"What did the note 'talk-dim' really mean?",
            f"It was not a secret villain code. It was {helper.id}'s silly reminder to whisper and keep the surprise hidden until the {item.label} looked better again."
        ),
        (
            f"Where did {detective.id} find {helper.id}, and what was {helper.pronoun()} doing?",
            f"{detective.id} found {helper.id} at {place}. {helper.pronoun().capitalize()} was {fix.action_line}, trying to make the {item.label} ready again."
        ),
        (
            f"What did {detective.id} learn?",
            f"{detective.id} learned to ask before accusing. The first clue looked strong, but the truth was kinder than the guess."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "clue", "asking"}
    if f["fix"].id == "polish":
        tags.add("polish")
    elif f["fix"].id == "wash":
        tags.add("wash")
    else:
        tags.add("repair")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
match_item_issue(I, Iss) :- item_material(I, M), issue_material(Iss, M).
match_item_fix(I, F)     :- item_material(I, M), fix_material(F, M).
match_clue_fix(C, F)     :- clue_for(C, F).
setting_supports(S, F)   :- fix_needs(F, H), affords(S, H).

valid(S, I, Iss, F, C) :- setting(S), item(I), issue(Iss), fix(F), clue(C),
                          match_item_issue(I, Iss),
                          match_item_fix(I, F),
                          match_clue_fix(C, F),
                          setting_supports(S, F).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for afford in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, afford))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_material", item_id, item.material))
    for issue_id, issue in ISSUES.items():
        lines.append(asp.fact("issue", issue_id))
        lines.append(asp.fact("issue_material", issue_id, issue.material))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_material", fix_id, fix.material))
        lines.append(asp.fact("fix_needs", fix_id, fix.needs))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_for", clue_id, clue.for_fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolved story was empty")
        print("OK: default resolve/generate smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="classroom",
        item="badge",
        issue="tarnish",
        fix="polish",
        clue="cloth",
        detective="Mira",
        detective_gender="girl",
        sidekick="Owen",
        sidekick_gender="boy",
        helper="Nora",
        helper_gender="girl",
        guide="teacher_f",
    ),
    StoryParams(
        setting="clubhouse",
        item="cape",
        issue="jam",
        fix="wash",
        clue="bubble",
        detective="Finn",
        detective_gender="boy",
        sidekick="June",
        sidekick_gender="girl",
        helper="Ivy",
        helper_gender="girl",
        guide="teacher_f",
    ),
    StoryParams(
        setting="library",
        item="map",
        issue="split_fold",
        fix="tape",
        clue="tape_strip",
        detective="Lena",
        detective_gender="girl",
        sidekick="Milo",
        sidekick_gender="boy",
        helper="Theo",
        helper_gender="boy",
        guide="teacher_m",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Child-facing detective storyworld with a clue, a wrong guess, and a kind twist."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--guide", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if (
        args.setting is not None
        and args.item is not None
        and args.issue is not None
        and args.fix is not None
        and args.clue is not None
    ):
        setting = SETTINGS[args.setting]
        item = ITEMS[args.item]
        issue = ISSUES[args.issue]
        fix = FIXES[args.fix]
        clue = CLUES[args.clue]
        if not valid_combo(setting, item, issue, fix, clue):
            raise StoryError(explain_rejection(setting, item, issue, fix, clue))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.issue is None or combo[2] == args.issue)
        and (args.fix is None or combo[3] == args.fix)
        and (args.clue is None or combo[4] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, issue_id, fix_id, clue_id = rng.choice(sorted(combos))
    used: set[str] = set()
    detective, detective_gender = _pick_name(rng, used)
    used.add(detective)
    sidekick, sidekick_gender = _pick_name(rng, used)
    used.add(sidekick)
    helper, helper_gender = _pick_name(rng, used)
    guide = args.guide or rng.choice(["teacher_f", "teacher_m"])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        issue=issue_id,
        fix=fix_id,
        clue=clue_id,
        detective=detective,
        detective_gender=detective_gender,
        sidekick=sidekick,
        sidekick_gender=sidekick_gender,
        helper=helper,
        helper_gender=helper_gender,
        guide=guide,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.issue not in ISSUES:
        raise StoryError(f"(Unknown issue: {params.issue})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.guide not in {"teacher_f", "teacher_m"}:
        raise StoryError(f"(Unknown guide: {params.guide})")

    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    issue = ISSUES[params.issue]
    fix = FIXES[params.fix]
    clue = CLUES[params.clue]
    if not valid_combo(setting, item, issue, fix, clue):
        raise StoryError(explain_rejection(setting, item, issue, fix, clue))

    world = tell(
        setting=setting,
        item=item,
        issue=issue,
        fix=fix,
        clue=clue,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        sidekick_name=params.sidekick,
        sidekick_gender=params.sidekick_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        guide_type=params.guide,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, item, issue, fix, clue) combos:\n")
        for setting_id, item_id, issue_id, fix_id, clue_id in combos:
            print(f"  {setting_id:10} {item_id:6} {issue_id:11} {fix_id:6} {clue_id}")
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
            header = f"### {p.detective}: {p.item} in {p.setting} ({p.fix}, twist)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
