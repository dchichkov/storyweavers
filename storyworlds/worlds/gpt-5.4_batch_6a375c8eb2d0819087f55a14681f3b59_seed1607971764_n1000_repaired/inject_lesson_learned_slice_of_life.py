#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/inject_lesson_learned_slice_of_life.py
=================================================================

A standalone story world about a child trying to help a droopy houseplant in a
too-direct way, learning that kind intentions need understanding. The required
seed word "inject" appears as part of the child's mistaken plan: trying to
inject water into a plant instead of learning what the plant really needs.

This world keeps a small slice-of-life frame:
- a child notices a household problem,
- tries a shortcut,
- a calm grown-up explains what is really wrong,
- they fix it together,
- and the ending image shows a changed habit.

Run it
------
    python storyworlds/worlds/gpt-5.4/inject_lesson_learned_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/inject_lesson_learned_slice_of_life.py --plant fern --issue thirsty --fix water_soil
    python storyworlds/worlds/gpt-5.4/inject_lesson_learned_slice_of_life.py --issue dusty --fix move_to_window
    python storyworlds/worlds/gpt-5.4/inject_lesson_learned_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/inject_lesson_learned_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/inject_lesson_learned_slice_of_life.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/inject_lesson_learned_slice_of_life.py --verify
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Plant:
    id: str
    label: str
    phrase: str
    home: str
    feature: str
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
    cue: str
    symptom: str
    cause_line: str
    need_line: str
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
    solves: set[str]
    act: str
    effect: str
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


@dataclass
class Temperament:
    id: str
    notice_line: str
    impatience: int
    lesson_line: str
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
class StoryParams:
    plant: str
    issue: str
    fix: str
    name: str
    gender: str
    parent: str
    temperament: str
    delay: int = 0
    seed: Optional[int] = None
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


def _r_issue_appearance(world: World) -> list[str]:
    plant = world.get("plant")
    issue = world.facts["issue_cfg"]
    sig = ("appearance", issue.id)
    if sig in world.fired:
        return []
    if plant.meters[issue.id] < THRESHOLD:
        return []
    world.fired.add(sig)
    if issue.id in {"thirsty", "shady"}:
        plant.meters["droopy"] += 1
    if issue.id == "dusty":
        plant.meters["dull"] += 1
    child = world.get("child")
    child.memes["worry"] += 1
    return []


def _r_inject_hurts(world: World) -> list[str]:
    plant = world.get("plant")
    child = world.get("child")
    if plant.meters["poked"] < THRESHOLD:
        return []
    sig = ("poked_hurts", plant.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["stress"] += 1
    child.memes["guilt"] += 1
    child.memes["worry"] += 1
    return []


def _r_fix_resolves(world: World) -> list[str]:
    plant = world.get("plant")
    fix = world.facts["fix_cfg"]
    issue = world.facts["issue_cfg"]
    sig = ("resolve", fix.id, issue.id)
    if sig in world.fired:
        return []
    if plant.meters["care_done"] < THRESHOLD:
        return []
    if issue.id not in fix.solves:
        return []
    world.fired.add(sig)
    plant.meters["revived"] += 1
    plant.meters["droopy"] = 0.0
    plant.meters["dull"] = 0.0
    plant.meters["stress"] = max(0.0, plant.meters["stress"] - 1.0)
    child = world.get("child")
    parent = world.get("parent")
    child.memes["relief"] += 1
    child.memes["understanding"] += 1
    parent.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="issue_appearance", tag="physical", apply=_r_issue_appearance),
    Rule(name="inject_hurts", tag="physical", apply=_r_inject_hurts),
    Rule(name="fix_resolves", tag="physical", apply=_r_fix_resolves),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLANTS = {
    "fern": Plant(
        id="fern",
        label="fern",
        phrase="a feathery fern",
        home="the bathroom shelf",
        feature="soft green fronds",
        tags={"fern", "plant"},
    ),
    "basil": Plant(
        id="basil",
        label="basil plant",
        phrase="a little basil plant",
        home="the kitchen sill",
        feature="sweet-smelling leaves",
        tags={"basil", "plant", "herbs"},
    ),
    "spider_plant": Plant(
        id="spider_plant",
        label="spider plant",
        phrase="a striped spider plant",
        home="the living-room bookcase",
        feature="long striped leaves",
        tags={"spider_plant", "plant"},
    ),
    "ivy": Plant(
        id="ivy",
        label="ivy",
        phrase="a trailing ivy",
        home="the hall table",
        feature="small dangling vines",
        tags={"ivy", "plant"},
    ),
}

ISSUES = {
    "thirsty": Issue(
        id="thirsty",
        cue="the soil felt dry as crumbs",
        symptom="its leaves looked limp",
        cause_line="Plants drink through their roots, not through little holes in their stems.",
        need_line="It needed a drink in the soil.",
        tags={"water", "roots", "thirsty"},
    ),
    "shady": Issue(
        id="shady",
        cue="the corner was dim all day",
        symptom="it kept leaning toward the light",
        cause_line="This plant was not asking for more water. It was asking for brighter light.",
        need_line="It needed a sunnier spot.",
        tags={"sunlight", "window", "light"},
    ),
    "dusty": Issue(
        id="dusty",
        cue="a thin gray coat sat on the leaves",
        symptom="the leaves looked dull instead of bright",
        cause_line="Dust was blocking some of the light from the leaves.",
        need_line="It needed clean leaves, not extra water.",
        tags={"dust", "leaves", "clean"},
    ),
}

FIXES = {
    "water_soil": Fix(
        id="water_soil",
        solves={"thirsty"},
        act="poured water slowly into the soil until it turned dark and cool",
        effect="After a while, the leaves lifted a little, as if the plant had finally had its drink.",
        qa_text="They watered the soil gently so the roots could drink.",
        tags={"watering", "roots"},
    ),
    "move_to_window": Fix(
        id="move_to_window",
        solves={"shady"},
        act="carried the pot to a brighter window where morning light could reach it",
        effect="Over the next days, the plant stopped stretching sadly and held itself up straighter.",
        qa_text="They moved the plant to a brighter window.",
        tags={"window", "sunlight"},
    ),
    "wipe_leaves": Fix(
        id="wipe_leaves",
        solves={"dusty"},
        act="wiped each leaf with a damp soft cloth until the green showed again",
        effect="Soon the leaves looked glossy, and the whole plant seemed awake again.",
        qa_text="They wiped the leaves clean with a soft damp cloth.",
        tags={"cloth", "leaves", "clean"},
    ),
}

TEMPERAMENTS = {
    "careful": Temperament(
        id="careful",
        notice_line="liked helping with small household jobs and usually tried to be gentle",
        impatience=0,
        lesson_line="Helping works best when you first learn what something needs.",
    ),
    "eager": Temperament(
        id="eager",
        notice_line="loved being useful and often moved before every thought had fully settled",
        impatience=1,
        lesson_line="A fast idea can come from a kind heart and still be the wrong fix.",
    ),
    "thoughtful": Temperament(
        id="thoughtful",
        notice_line="noticed little changes and wanted everything in the house to feel cared for",
        impatience=0,
        lesson_line="Looking closely before acting can be its own kind of kindness.",
    ),
    "hasty": Temperament(
        id="hasty",
        notice_line="wanted to solve problems at once and did not always wait for the whole answer",
        impatience=1,
        lesson_line="Not every problem wants the quickest tool; some want patience.",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    plant_issues = {
        "fern": {"thirsty", "shady"},
        "basil": {"thirsty", "shady"},
        "spider_plant": {"thirsty", "dusty"},
        "ivy": {"shady", "dusty"},
    }
    for plant_id, issues in plant_issues.items():
        for issue_id in issues:
            for fix_id, fix in FIXES.items():
                if issue_id in fix.solves:
                    combos.append((plant_id, issue_id, fix_id))
    return sorted(combos)


def explain_rejection(plant: Plant, issue: Issue, fix: Fix) -> str:
    if issue.id not in {
        combo_issue
        for combo_plant, combo_issue, _ in valid_combos()
        if combo_plant == plant.id
    }:
        return (
            f"(No story: {plant.phrase} is not modeled with the problem '{issue.id}' here. "
            f"Pick an issue that fits this plant, such as one of: "
            f"{', '.join(sorted({combo_issue for combo_plant, combo_issue, _ in valid_combos() if combo_plant == plant.id}))}.)"
        )
    return (
        f"(No story: {fix.id} does not honestly fix a {issue.id} {plant.label}. "
        f"The solution must match what the plant really needs.)"
    )


def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def predict_inject(world: World) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    plant.meters["poked"] += 1
    if sim.facts["issue_cfg"].id == "thirsty":
        plant.meters["water_inside_stem"] += 1
    propagate(sim, narrate=False)
    unresolved = plant.meters["revived"] < THRESHOLD
    return {
        "hurt": plant.meters["stress"] >= THRESHOLD,
        "unresolved": unresolved,
    }


def introduce(world: World, child: Entity, plant: Plant, temperament: Temperament) -> None:
    world.say(
        f"After breakfast, {child.id} padded through the house and stopped by {plant.home}, "
        f"where {plant.phrase} lived. {child.pronoun().capitalize()} {temperament.notice_line}."
    )
    world.say(
        f"That morning, though, {plant.feature} did not look quite right."
    )


def notice_problem(world: World, child: Entity, plant_cfg: Plant, issue_cfg: Issue) -> None:
    plant = world.get("plant")
    world.say(
        f"{child.id} leaned close. {issue_cfg.cue}, and {issue_cfg.symptom}."
    )
    if plant.meters["droopy"] >= THRESHOLD:
        world.say(
            f'"Oh no," {child.pronoun()} whispered. "My {plant_cfg.label} looks tired."'
        )
    else:
        world.say(
            f'"Oh no," {child.pronoun()} whispered. "My {plant_cfg.label} does not look happy."'
        )


def make_plan(world: World, child: Entity) -> None:
    child.memes["care"] += 1
    child.memes["confidence"] += 1
    world.say(
        f"On the counter sat a clean plastic syringe that was used for measuring liquids. "
        f"{child.id}'s eyes brightened."
    )
    world.say(
        f'"I know," {child.pronoun()} said. "I can inject a little water right into the plant, '
        f'and then it will feel better faster."'
    )


def warn(world: World, parent: Entity, child: Entity, issue_cfg: Issue) -> None:
    pred = predict_inject(world)
    world.facts["predicted_hurt"] = pred["hurt"]
    world.facts["predicted_unresolved"] = pred["unresolved"]
    child.memes["hesitation"] += 1
    extra = ""
    if pred["hurt"] and pred["unresolved"]:
        extra = " That could poke the plant and still not solve the real problem."
    world.say(
        f'{parent.label_word.capitalize()} looked over from the sink and came closer. '
        f'"Wait a second," {parent.pronoun()} said gently. "{issue_cfg.cause_line}{extra}"'
    )


def poke_first(world: World, child: Entity, plant_cfg: Plant) -> None:
    plant = world.get("plant")
    plant.meters["poked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {child.id} had already pressed the tip too close. The stem got a tiny nick, "
        f"and {child.pronoun()} froze."
    )
    world.say(
        f'"I was trying to help," {child.pronoun()} said, staring at the {plant_cfg.label}.'
    )


def stop_in_time(world: World, parent: Entity, child: Entity) -> None:
    child.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} laid a calm hand over the syringe before it touched the plant."
    )
    world.say(
        f'{child.id} blinked and lowered {child.pronoun("possessive")} hands. '
        f'"Okay," {child.pronoun()} said. "Show me the right way."'
    )


def explain_need(world: World, parent: Entity, issue_cfg: Issue) -> None:
    world.say(
        f'"See?" {parent.label_word.capitalize()} said. "{issue_cfg.need_line}"'
    )


def fix_problem(world: World, child: Entity, parent: Entity, fix_cfg: Fix) -> None:
    plant = world.get("plant")
    plant.meters["care_done"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {fix_cfg.act}."
    )
    world.say(fix_cfg.effect)
    if plant.meters["poked"] >= THRESHOLD:
        world.say(
            f"{child.id} touched the pot instead of the stem this time, very softly."
        )


def lesson(world: World, child: Entity, parent: Entity, temperament: Temperament) -> None:
    child.memes["lesson"] += 1
    child.memes["care"] += 1
    world.say(
        f'{parent.label_word.capitalize()} rinsed the syringe and set it high on the shelf. '
        f'"Wanting to help was good," {parent.pronoun()} said. "But first we ask what the plant needs."'
    )
    world.say(
        f"{child.id} nodded. {temperament.lesson_line}"
    )


def ending(world: World, child: Entity, plant_cfg: Plant) -> None:
    if world.facts["issue_cfg"].id == "thirsty":
        end_action = "checked the soil with one finger"
    elif world.facts["issue_cfg"].id == "shady":
        end_action = "looked to see where the light fell"
    else:
        end_action = "looked over the leaves for dust"
    world.say(
        f"That afternoon, {child.id} made a tiny care card for the {plant_cfg.label}. "
        f"The next time {child.pronoun()} wanted to help, {child.pronoun()} would first {end_action}."
    )
    world.say(
        f"By the window, the little plant looked quietly better, and so did {child.id}."
    )


def tell(
    plant_cfg: Plant,
    issue_cfg: Issue,
    fix_cfg: Fix,
    *,
    name: str,
    gender: str,
    parent_type: str,
    temperament_cfg: Temperament,
    delay: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="child",
            label=name,
            traits=[temperament_cfg.id],
            attrs={},
            tags=set(),
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={},
            tags=set(),
        )
    )
    plant = world.add(
        Entity(
            id="plant",
            kind="thing",
            type="plant",
            label=plant_cfg.label,
            attrs={"home": plant_cfg.home},
            tags=set(plant_cfg.tags),
        )
    )

    plant.meters[issue_cfg.id] = 1.0
    child.memes["care"] = 0.0
    child.memes["confidence"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["guilt"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["understanding"] = 0.0
    child.memes["lesson"] = 0.0
    parent.memes["pride"] = 0.0

    world.facts.update(
        plant_cfg=plant_cfg,
        issue_cfg=issue_cfg,
        fix_cfg=fix_cfg,
        child=child,
        parent=parent,
        delay=delay,
    )

    propagate(world, narrate=False)

    introduce(world, child, plant_cfg, temperament_cfg)
    notice_problem(world, child, plant_cfg, issue_cfg)

    world.para()
    make_plan(world, child)
    warn(world, parent, child, issue_cfg)

    world.para()
    if delay > 0:
        poke_first(world, child, plant_cfg)
    else:
        stop_in_time(world, parent, child)
    explain_need(world, parent, issue_cfg)
    fix_problem(world, child, parent, fix_cfg)

    world.para()
    lesson(world, child, parent, temperament_cfg)
    ending(world, child, plant_cfg)

    world.facts.update(
        outcome="nicked" if plant.meters["poked"] >= THRESHOLD else "stopped",
        revived=plant.meters["revived"] >= THRESHOLD,
        hurt=plant.meters["poked"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "plant": [
        (
            "How do houseplants drink water?",
            "Houseplants take in water through their roots in the soil. The roots move the water up through the plant."
        )
    ],
    "roots": [
        (
            "Why do you water the soil instead of poking water into a stem?",
            "The roots are the part made to take in water. Poking a stem can hurt the plant instead of helping it."
        )
    ],
    "sunlight": [
        (
            "Why do plants need sunlight?",
            "Plants use sunlight to make food for themselves. A plant in a dim spot can grow weak and lean toward the light."
        )
    ],
    "dust": [
        (
            "Why should dusty leaves be cleaned?",
            "A layer of dust can make leaves look dull and can block some light. Wiping the leaves gently helps the plant use light better."
        )
    ],
    "clean": [
        (
            "What is a gentle way to clean a plant leaf?",
            "Use a soft damp cloth and wipe carefully. Gentle cleaning helps without tearing the leaf."
        )
    ],
    "watering": [
        (
            "How can you tell if soil may need water?",
            "If the top of the soil feels dry and crumbly, the plant may be thirsty. Grown-ups can help check before watering."
        )
    ],
    "window": [
        (
            "Why might someone move a plant near a window?",
            "A brighter window can give a plant more light. Some plants perk up when they are moved out of a dim corner."
        )
    ],
    "cloth": [
        (
            "What is a soft cloth good for in plant care?",
            "A soft cloth can wipe dust away from leaves. It cleans gently without scratching the plant."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    plant_cfg = world.facts["plant_cfg"]
    issue_cfg = world.facts["issue_cfg"]
    child = world.facts["child"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "inject" and ends with a small lesson learned.',
        f"Tell a gentle home story where {child.id} wants to help a {plant_cfg.label} but chooses the wrong shortcut first, then learns what it really needs.",
        f"Write a story about a child noticing {issue_cfg.symptom} on a houseplant and learning to understand a problem before trying to fix it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    plant_cfg = world.facts["plant_cfg"]
    issue_cfg = world.facts["issue_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child trying to help a {plant_cfg.label}, and {child.pronoun('possessive')} {parent.label_word} who guides {child.pronoun('object')}. The story stays close to an ordinary morning at home."
        ),
        (
            f"Why did {child.id} think about trying to inject water into the plant?",
            f"{child.id} saw that the plant did not look right and wanted a fast way to help. {child.pronoun().capitalize()} guessed that putting water straight in would work quicker, but that guess did not match how the plant really solved its problem."
        ),
        (
            "What was the plant really needing?",
            f"The plant did not need a shortcut through the stem. {issue_cfg.need_line} That is why the grown-up stopped to explain before fixing it together."
        ),
        (
            "How did they solve the problem?",
            f"{fix_cfg.qa_text} The real fix worked because it matched the actual problem instead of the child's first guess."
        ),
    ]
    if outcome == "nicked":
        qa.append(
            (
                f"What happened when {child.id} moved too fast?",
                f"{child.id} nicked the stem a little before stopping. That moment made {child.pronoun('object')} see that a kind plan can still cause harm if {child.pronoun()} does not understand how something works."
            )
        )
    else:
        qa.append(
            (
                f"Did the plant get poked?",
                f"No. {child.id}'s {parent.label_word} stopped the syringe before it touched the plant. That gave them time to choose a gentler, smarter way to help."
            )
        )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned to ask what something needs before trying to fix it. The ending shows this lesson because {child.pronoun()} makes a little care card and plans to check carefully next time."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    issue_cfg = world.facts["issue_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    tags = {"plant"} | set(issue_cfg.tags) | set(fix_cfg.tags)
    order = ["plant", "roots", "watering", "sunlight", "window", "dust", "clean", "cloth"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        plant="fern",
        issue="thirsty",
        fix="water_soil",
        name="Lily",
        gender="girl",
        parent="mother",
        temperament="careful",
        delay=0,
    ),
    StoryParams(
        plant="basil",
        issue="shady",
        fix="move_to_window",
        name="Ben",
        gender="boy",
        parent="father",
        temperament="eager",
        delay=1,
    ),
    StoryParams(
        plant="spider_plant",
        issue="dusty",
        fix="wipe_leaves",
        name="Maya",
        gender="girl",
        parent="mother",
        temperament="thoughtful",
        delay=0,
    ),
    StoryParams(
        plant="ivy",
        issue="dusty",
        fix="wipe_leaves",
        name="Theo",
        gender="boy",
        parent="father",
        temperament="hasty",
        delay=1,
    ),
    StoryParams(
        plant="spider_plant",
        issue="thirsty",
        fix="water_soil",
        name="Nora",
        gender="girl",
        parent="mother",
        temperament="eager",
        delay=0,
    ),
]


ASP_RULES = r"""
valid(P, I, F) :- plant_issue(P, I), fix_solves(F, I).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    plant_issue_map = {
        "fern": {"thirsty", "shady"},
        "basil": {"thirsty", "shady"},
        "spider_plant": {"thirsty", "dusty"},
        "ivy": {"shady", "dusty"},
    }

    lines: list[str] = []
    for plant_id in PLANTS:
        lines.append(asp.fact("plant", plant_id))
    for issue_id in ISSUES:
        lines.append(asp.fact("issue", issue_id))
    for fix_id in FIXES:
        lines.append(asp.fact("fix", fix_id))
    for plant_id, issues in sorted(plant_issue_map.items()):
        for issue_id in sorted(issues):
            lines.append(asp.fact("plant_issue", plant_id, issue_id))
    for fix_id, fix in sorted(FIXES.items()):
        for issue_id in sorted(fix.solves):
            lines.append(asp.fact("fix_solves", fix_id, issue_id))
    return "\n".join(lines)


def asp_program(show_override: str = "") -> str:
    show = show_override or "#show valid/3."
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as exc:  # pragma: no cover - explicit verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("blank story during verify")
        except Exception as exc:  # pragma: no cover - explicit verify path
            rc = 1
            print(f"VERIFY GENERATION FAILED at seed {seed}: {exc}")
            break
    else:
        print("OK: random generation succeeded for seeds 0-9.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child tries to help a houseplant, learns to understand the problem before fixing it."
    )
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument(
        "--delay",
        type=int,
        choices=[0, 1],
        help="0 = parent stops the poke in time; 1 = the child nicks the stem first",
    )
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (plant, issue, fix) set from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plant and args.issue and args.fix:
        plant_cfg = PLANTS[args.plant]
        issue_cfg = ISSUES[args.issue]
        fix_cfg = FIXES[args.fix]
        if (args.plant, args.issue, args.fix) not in valid_combos():
            raise StoryError(explain_rejection(plant_cfg, issue_cfg, fix_cfg))

    filtered = [
        combo
        for combo in valid_combos()
        if (args.plant is None or combo[0] == args.plant)
        and (args.issue is None or combo[1] == args.issue)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not filtered:
        if args.plant and args.issue and args.fix:
            raise StoryError(explain_rejection(PLANTS[args.plant], ISSUES[args.issue], FIXES[args.fix]))
        raise StoryError("(No valid combination matches the given options.)")

    plant_id, issue_id, fix_id = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or pick_name(rng, gender)
    parent = args.parent or rng.choice(["mother", "father"])
    temperament = args.temperament or rng.choice(sorted(TEMPERAMENTS))
    delay = args.delay if args.delay is not None else min(1, TEMPERAMENTS[temperament].impatience)
    return StoryParams(
        plant=plant_id,
        issue=issue_id,
        fix=fix_id,
        name=name,
        gender=gender,
        parent=parent,
        temperament=temperament,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.issue not in ISSUES:
        raise StoryError(f"(Unknown issue: {params.issue})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(Unknown temperament: {params.temperament})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if (params.plant, params.issue, params.fix) not in valid_combos():
        raise StoryError(explain_rejection(PLANTS[params.plant], ISSUES[params.issue], FIXES[params.fix]))

    world = tell(
        PLANTS[params.plant],
        ISSUES[params.issue],
        FIXES[params.fix],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
        temperament_cfg=TEMPERAMENTS[params.temperament],
        delay=params.delay,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (plant, issue, fix) combos:\n")
        for plant_id, issue_id, fix_id in combos:
            print(f"  {plant_id:13} {issue_id:8} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.plant} / {p.issue} / {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
