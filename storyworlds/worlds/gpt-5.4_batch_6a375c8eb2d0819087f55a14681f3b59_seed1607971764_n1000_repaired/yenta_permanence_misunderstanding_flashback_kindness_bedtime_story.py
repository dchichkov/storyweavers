#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/yenta_permanence_misunderstanding_flashback_kindness_bedtime_story.py
=================================================================================================

A standalone story world about a bedtime misunderstanding: a child thinks a
beloved bedtime object is gone for good, remembers an earlier kindness, and
learns that "overnight" is not forever.

Seed requirements carried into the world:
- uses the words "yenta" and "permanence"
- features misunderstanding, flashback, kindness
- child-facing bedtime-story tone

World premise
-------------
A child depends on a bedtime object -- a blanket, rabbit, bear, or pillow.
That object has a small problem before bed: it is wet, torn, or missing a
button. A kindly, chatty neighbor or grandmother takes it briefly to help.
The child overhears an ambiguous phrase like "I'll keep it overnight" and
misunderstands it as permanence: gone forever. In the middle, the child's fear
is challenged by a flashback to an earlier moment when the same grown-up
carefully returned something precious. The story ends when the object comes back
safe, the child offers a small kindness in return, and bedtime becomes calm.

Run it
------
    python storyworlds/worlds/gpt-5.4/yenta_permanence_misunderstanding_flashback_kindness_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/yenta_permanence_misunderstanding_flashback_kindness_bedtime_story.py --object rabbit --problem torn
    python storyworlds/worlds/gpt-5.4/yenta_permanence_misunderstanding_flashback_kindness_bedtime_story.py --helper grandmother --problem wet
    python storyworlds/worlds/gpt-5.4/yenta_permanence_misunderstanding_flashback_kindness_bedtime_story.py --problem dusty
    python storyworlds/worlds/gpt-5.4/yenta_permanence_misunderstanding_flashback_kindness_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/yenta_permanence_misunderstanding_flashback_kindness_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/yenta_permanence_misunderstanding_flashback_kindness_bedtime_story.py --verify
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
    kind: str = "thing"            # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "neighbor_woman"}
        male = {"boy", "father", "grandfather", "man", "neighbor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "neighbor_woman": "neighbor",
            "neighbor_man": "neighbor",
        }
        return mapping.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Config registries
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class BedObject:
    id: str
    label: str
    phrase: str
    storage: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Problem:
    id: str
    label: str
    past: str
    danger: str
    need: str
    fix_tag: str
    carried_to: str
    overnight_ok: bool
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
class HelperCfg:
    id: str
    type: str
    title: str
    room: str
    call: str
    style: str
    yenta_ok: bool
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
class FixMethod:
    id: str
    label: str
    fixes: set[str]
    text: str
    return_text: str
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
class MemoryCfg:
    id: str
    lost_item: str
    found_place: str
    careful_act: str
    shows_returning: bool = True
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


def _r_separation_distress(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    bed_obj = world.get("bed_object")
    if bed_obj.attrs.get("away") and child.memes["worry"] >= THRESHOLD:
        sig = ("separation", bed_obj.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            out.append("__separation__")
    return out


def _r_memory_softens(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["remembering"] >= THRESHOLD and child.meters["trust_evidence"] >= THRESHOLD:
        sig = ("soften", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 1
            child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
            out.append("__memory__")
    return out


def _r_return_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    bed_obj = world.get("bed_object")
    if not bed_obj.attrs.get("away") and bed_obj.meters["fixed"] >= THRESHOLD:
        sig = ("return_relief", bed_obj.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] = 0.0
            child.memes["worry"] = 0.0
            child.memes["relief"] += 1
            child.memes["gratitude"] += 1
            out.append("__return__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="separation_distress", tag="emotional", apply=_r_separation_distress),
    Rule(name="memory_softens", tag="emotional", apply=_r_memory_softens),
    Rule(name="return_relief", tag="emotional", apply=_r_return_relief),
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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def helper_can_fix(helper: HelperCfg, method: FixMethod, problem: Problem) -> bool:
    if problem.fix_tag not in method.fixes:
        return False
    if helper.id == "neighbor" and problem.id == "wet":
        return True
    if helper.id == "neighbor" and problem.id == "torn":
        return True
    if helper.id == "neighbor" and problem.id == "button":
        return True
    if helper.id == "grandmother" and problem.id == "torn":
        return True
    if helper.id == "grandmother" and problem.id == "button":
        return True
    if helper.id == "grandmother" and problem.id == "wet":
        return True
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for obj_id in BED_OBJECTS:
        for prob_id, prob in PROBLEMS.items():
            for helper_id, helper in HELPERS.items():
                for method_id, method in METHODS.items():
                    if helper_can_fix(helper, method, prob):
                        combos.append((obj_id, prob_id, helper_id, method_id))
    return sorted(combos)


def explain_rejection(problem: Problem, helper: HelperCfg, method: FixMethod) -> str:
    if problem.fix_tag not in method.fixes:
        return (
            f"(No story: {method.label} does not actually fix something that is "
            f"{problem.label}. Pick a method that matches the problem.)"
        )
    return (
        f"(No story: {helper.title} is not a sensible helper for {method.label} "
        f"with this bedtime problem in this world.)"
    )


# ---------------------------------------------------------------------------
# Prediction / misunderstanding model
# ---------------------------------------------------------------------------
def predict_misunderstanding(helper: HelperCfg, problem: Problem, wording: str) -> dict:
    permanence_risk = 0
    if wording == "overnight":
        permanence_risk += 2
    if problem.overnight_ok:
        permanence_risk += 1
    if helper.id == "neighbor":
        permanence_risk += 1
    return {
        "away_tonight": problem.overnight_ok,
        "permanence_risk": permanence_risk,
        "likely_misunderstanding": permanence_risk >= 2,
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, bed_obj: Entity) -> None:
    world.say(
        f"In a small warm room, {child.id} got ready for bed with {child.pronoun('possessive')} "
        f"{bed_obj.label}, {bed_obj.phrase}. Every night {bed_obj.it()} rested {bed_obj.attrs['usual_spot']}, "
        f"and that little place helped the room feel safe."
    )


def bedtime_need(world: World, child: Entity, bed_obj: Entity) -> None:
    child.memes["attachment"] += 1
    world.say(
        f"{child.id} liked the soft hush of bedtime best when {bed_obj.it()} was close. "
        f"Without {bed_obj.it()}, the shadows by the curtains seemed longer."
    )


def problem_appears(world: World, child: Entity, bed_obj: Entity, problem: Problem) -> None:
    bed_obj.meters["damaged"] += 1
    world.say(
        f"But that evening, {child.pronoun('possessive')} {bed_obj.label} was {problem.past}. "
        f"It {problem.danger}, and {child.id} stared at it with a small, pinched face."
    )


def helper_arrives(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    yenta_line = ""
    if helper_cfg.yenta_ok:
        yenta_line = (
            f' Grown-ups in the building sometimes called {helper.id} the hall\'s kind yenta, '
            f'because {helper.pronoun()} always noticed who needed soup, thread, or a listening ear.'
        )
    world.say(
        f"Just then, {helper_cfg.title} came from {helper_cfg.room}. {helper.pronoun().capitalize()} "
        f"{helper_cfg.style}.{yenta_line}"
    )


def offer_help(world: World, helper: Entity, helper_cfg: HelperCfg, bed_obj: Entity,
               problem: Problem, method: FixMethod) -> None:
    world.say(
        f'"Oh, dear," {helper.id} said. "I can help. I\'ll take {bed_obj.it()} to {problem.carried_to} '
        f'and {method.text}."'
    )


def misunderstanding(world: World, child: Entity, helper: Entity, bed_obj: Entity,
                      helper_cfg: HelperCfg, problem: Problem, wording: str) -> None:
    pred = predict_misunderstanding(helper_cfg, problem, wording)
    world.facts["predicted_permanence_risk"] = pred["permanence_risk"]
    child.memes["worry"] += 1
    if pred["likely_misunderstanding"]:
        child.memes["misunderstanding"] += 1
    bed_obj.attrs["away"] = True
    world.say(
        f"Then {helper.id} added, \"I'll keep {bed_obj.it()} {wording}.\""
    )
    propagate(world, narrate=False)
    world.say(
        f"{child.id} heard only the words keep and overnight. {child.pronoun().capitalize()} did not know the big word permanence very well, "
        f"but in {child.pronoun('possessive')} heart it suddenly sounded like forever."
    )
    world.say(
        f'"Do you mean {bed_obj.it()} is going away for always?" {child.pronoun()} whispered.'
    )


def parent_explains(world: World, parent: Entity, child: Entity, helper: Entity,
                    bed_obj: Entity) -> None:
    child.memes["confusion"] += 1
    parent.memes["care"] += 1
    world.say(
        f"{child.id}'s {parent.label_word} sat beside {child.pronoun('object')} at once. "
        f'"No, sweetheart," {parent.pronoun()} said. "{helper.id} is helping, not keeping. '
        f'{bed_obj.it()[0].upper()}{bed_obj.it()[1:]} is still yours."'
    )


def doubt_lingers(world: World, child: Entity, bed_obj: Entity) -> None:
    if child.memes["fear"] >= THRESHOLD or child.memes["misunderstanding"] >= THRESHOLD:
        world.say(
            f"But worry can be stubborn at bedtime. {child.id} looked at the empty place {bed_obj.attrs['usual_spot']}, "
            f"and the room felt different without {bed_obj.it()} there."
        )


def flashback(world: World, child: Entity, helper: Entity, memory: MemoryCfg) -> None:
    child.memes["remembering"] += 1
    child.meters["trust_evidence"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a memory came back like a small lamp turning on. Last week, {child.id} had cried over {memory.lost_item} "
        f"that was missing from {memory.found_place}."
    )
    world.say(
        f"{helper.id} had found it and {memory.careful_act}. {helper.pronoun().capitalize()} had brought it back with both hands, "
        f"as if returning a treasure."
    )
    world.say(
        f"Remembering that, {child.id}'s breathing slowed. Maybe kind hands returned precious things after all."
    )


def choose_kindness(world: World, child: Entity, helper: Entity) -> None:
    child.memes["kindness"] += 1
    world.say(
        f"Instead of crying harder, {child.id} decided to do something gentle too. {child.pronoun().capitalize()} made room on the bedside stool "
        f"for when the helped thing came home, and asked if {helper.id} might like a drawing in the morning."
    )


def return_fixed(world: World, child: Entity, helper: Entity, bed_obj: Entity,
                 method: FixMethod, problem: Problem) -> None:
    bed_obj.attrs["away"] = False
    bed_obj.meters["fixed"] += 1
    bed_obj.meters["damaged"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Before the moon climbed very high, there came a soft tap at the door. {helper.id} stood there smiling, "
        f"holding {bed_obj.it()}."
    )
    world.say(
        method.return_text.format(obj=bed_obj.label, problem=problem.label)
    )


def resolution(world: World, child: Entity, helper: Entity, bed_obj: Entity) -> None:
    world.say(
        f"{child.id} hugged {bed_obj.it()} close and then hugged {helper.id}'s middle too. "
        f'"Thank you for helping and bringing {bed_obj.it()} back," {child.pronoun()} said.'
    )
    world.say(
        f'{helper.id} kissed the top of {child.pronoun("possessive")} head. "Kind things go out and come back," '
        f'{helper.pronoun()} said. "Overnight is only overnight."'
    )
    world.say(
        f"Soon {bed_obj.it()} was back {bed_obj.attrs['usual_spot']}, the room felt right again, "
        f"and bedtime settled softly around them all."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(
    obj_cfg: BedObject,
    problem_cfg: Problem,
    helper_cfg: HelperCfg,
    method_cfg: FixMethod,
    memory_cfg: MemoryCfg,
    *,
    child_name: str = "Mira",
    child_type: str = "girl",
    parent_type: str = "mother",
    wording: str = "overnight",
) -> World:
    world = World()

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        label=child_name,
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_cfg.title,
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.title,
        attrs={},
    ))
    bed_obj = world.add(Entity(
        id="bed_object",
        kind="thing",
        type=obj_cfg.id,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        role="comfort",
        attrs={"usual_spot": obj_cfg.storage, "away": False},
    ))

    world.facts["predicted_permanence_risk"] = 0
    child.memes["worry"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["remembering"] = 0.0
    child.meters["trust_evidence"] = 0.0

    introduce(world, child, bed_obj)
    bedtime_need(world, child, bed_obj)

    world.para()
    problem_appears(world, child, bed_obj, problem_cfg)
    helper_arrives(world, helper, helper_cfg)
    offer_help(world, helper, helper_cfg, bed_obj, problem_cfg, method_cfg)
    misunderstanding(world, child, helper, bed_obj, helper_cfg, problem_cfg, wording)
    parent_explains(world, parent, child, helper, bed_obj)
    doubt_lingers(world, child, bed_obj)

    world.para()
    flashback(world, child, helper, memory_cfg)
    choose_kindness(world, child, helper)

    world.para()
    return_fixed(world, child, helper, bed_obj, method_cfg, problem_cfg)
    resolution(world, child, helper, bed_obj)

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper,
        object_cfg=obj_cfg,
        problem_cfg=problem_cfg,
        helper_cfg=helper_cfg,
        method_cfg=method_cfg,
        memory_cfg=memory_cfg,
        wording=wording,
        misunderstanding=child.memes["misunderstanding"] >= THRESHOLD,
        flashed_back=child.memes["remembering"] >= THRESHOLD,
        returned=bed_obj.meters["fixed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
BED_OBJECTS = {
    "blanket": BedObject(
        id="blanket",
        label="blanket",
        phrase="a small blanket with a moon stitched in one corner",
        storage="at the foot of the bed",
        plural=False,
        tags={"blanket", "bedtime"},
    ),
    "rabbit": BedObject(
        id="rabbit",
        label="rabbit",
        phrase="a floppy cloth rabbit with one bent ear",
        storage="by the pillow",
        plural=False,
        tags={"stuffed_toy", "bedtime"},
    ),
    "bear": BedObject(
        id="bear",
        label="bear",
        phrase="a round teddy bear with sleepy button eyes",
        storage="under one arm",
        plural=False,
        tags={"stuffed_toy", "bedtime"},
    ),
    "pillow": BedObject(
        id="pillow",
        label="pillow",
        phrase="a little star pillow that smelled like soap and sleep",
        storage="under the chin",
        plural=False,
        tags={"pillow", "bedtime"},
    ),
}

PROBLEMS = {
    "wet": Problem(
        id="wet",
        label="wet",
        past="damp from a spilled cup of water",
        danger="needed time to dry before it could feel cozy again",
        need="drying",
        fix_tag="dry",
        carried_to="the warm laundry room",
        overnight_ok=True,
        tags={"wet", "care"},
    ),
    "torn": Problem(
        id="torn",
        label="torn",
        past="torn at one seam",
        danger="needed a careful stitch before the stuffing or softness slipped out",
        need="sewing",
        fix_tag="sew",
        carried_to="the sewing basket",
        overnight_ok=False,
        tags={"tear", "care"},
    ),
    "button": Problem(
        id="button",
        label="missing a button",
        past="missing a little button from one corner",
        danger="needed a tiny fix so no sharp thread would scratch",
        need="sewing",
        fix_tag="button",
        carried_to="the sewing basket",
        overnight_ok=False,
        tags={"button", "care"},
    ),
    "dusty": Problem(
        id="dusty",
        label="dusty",
        past="dusty from the top shelf",
        danger="was not a real bedtime emergency at all",
        need="dusting",
        fix_tag="dust",
        carried_to="the hallway",
        overnight_ok=False,
        tags={"dust"},
    ),
}

HELPERS = {
    "neighbor": HelperCfg(
        id="neighbor",
        type="neighbor_woman",
        title="Mrs. Dalia",
        room="the next apartment",
        call="neighbor",
        style="spoke in a warm, busy whisper that somehow felt cozy instead of loud",
        yenta_ok=True,
        tags={"neighbor", "yenta"},
    ),
    "grandmother": HelperCfg(
        id="grandmother",
        type="grandmother",
        title="Grandma Ruth",
        room="the guest room",
        call="grandma",
        style="came in with soft slippers and a basket that always seemed to hold exactly the right thing",
        yenta_ok=False,
        tags={"grandmother"},
    ),
}

METHODS = {
    "dry_rack": FixMethod(
        id="dry_rack",
        label="a warm drying line",
        fixes={"dry"},
        text="hang it where the warm air can reach every corner",
        return_text='"{obj.capitalize()} is dry now," the helper said. "Nothing has been lost, only helped."',
        tags={"drying"},
    ),
    "needle_thread": FixMethod(
        id="needle_thread",
        label="needle and thread",
        fixes={"sew", "button"},
        text="mend it with small patient stitches",
        return_text='"{obj.capitalize()} is mended now," the helper said. "I made the hurt part smaller, not your ownership."',
        tags={"sewing"},
    ),
    "button_tin": FixMethod(
        id="button_tin",
        label="a button tin and thread",
        fixes={"button"},
        text="choose a matching button and sew it on tight",
        return_text='"{obj.capitalize()} has its little button back," the helper said. "It still belongs right here with you."',
        tags={"sewing", "button"},
    ),
}

MEMORIES = {
    "mitten": MemoryCfg(
        id="mitten",
        lost_item="a red mitten",
        found_place="the radiator shelf downstairs",
        careful_act="brushed off the dust and tucked it into a clean napkin",
        shows_returning=True,
        tags={"returning"},
    ),
    "crayon": MemoryCfg(
        id="crayon",
        lost_item="a favorite silver crayon",
        found_place="the crack beside the sofa",
        careful_act="wrapped it in tissue so the paper would not peel",
        shows_returning=True,
        tags={"returning"},
    ),
    "shell": MemoryCfg(
        id="shell",
        lost_item="a shiny beach shell",
        found_place="the pocket of last Sunday's coat",
        careful_act="set it on a saucer and carried it level all the way down the hall",
        shows_returning=True,
        tags={"returning"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Tess", "Ivy", "Maya", "Elsie", "Ruby"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Eli", "Theo", "Nico", "Jude", "Leo"]

WORDINGS = ["overnight"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    object: str
    problem: str
    helper: str
    method: str
    memory: str
    child_name: str
    child_type: str
    parent_type: str
    wording: str = "overnight"
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
    "yenta": [
        (
            "What is a yenta?",
            "A yenta is a very talkative person who always seems to know what is going on. In this story, the word is used fondly for a neighbor who notices people and helps them."
        )
    ],
    "permanence": [
        (
            "What does permanence mean?",
            "Permanence means something lasts and does not just disappear right away. A child can misunderstand and think a short goodbye means forever, even when it only means for a little while."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly remembers something that happened before. It can help a character understand what is happening now."
        )
    ],
    "bedtime": [
        (
            "Why do bedtime routines help children feel calm?",
            "Bedtime routines help because the same steps happen in the same order, so the room feels predictable and safe. Familiar things like a blanket or toy can make that calm even stronger."
        )
    ],
    "neighbor": [
        (
            "How can a kind neighbor help a family?",
            "A kind neighbor can notice when something is wrong and offer help. Small help, like mending or returning something precious, can make a home feel warmer."
        )
    ],
    "grandmother": [
        (
            "Why are grandparents often good at comforting children?",
            "Grandparents often comfort children by moving slowly, speaking gently, and remembering what helps. Their calm can make a worried child feel steadier."
        )
    ],
    "sewing": [
        (
            "What does sewing do?",
            "Sewing joins cloth with thread so a tear can close or a button can stay on. Careful stitches can help something useful last longer."
        )
    ],
    "drying": [
        (
            "Why does something wet need time to dry?",
            "Wet cloth feels cold and heavy until the water goes away. Drying lets it become soft and cozy again."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or care for someone. It can be as small as returning a toy carefully or saying gentle words at the right time."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "yenta",
    "permanence",
    "flashback",
    "bedtime",
    "neighbor",
    "grandmother",
    "sewing",
    "drying",
    "kindness",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    obj = f["object_cfg"]
    helper = f["helper_cfg"]
    problem = f["problem_cfg"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "yenta" and "permanence". A child misunderstands what happens when a beloved {obj.label} is taken away to be helped.',
        f"Tell a gentle story where {child.id} worries that {child.pronoun('possessive')} {obj.label} is gone forever after {helper.title} says {child.pronoun('possessive')} helper words badly, but a flashback and a kind return make bedtime feel safe again.",
        f"Write a cozy misunderstanding story where a {problem.label} bedtime object leaves the room for help, a child fears permanence, and kindness brings it home again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper = f["helper"]
    obj = f["object_cfg"]
    problem = f["problem_cfg"]
    memory = f["memory_cfg"]
    items: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} bedtime {obj.label}, {child.id}'s {parent.label_word}, and {helper.id}, who offered to help. The story happens during a worried bedtime that becomes peaceful again."
        ),
        (
            f"Why was {child.id} upset?",
            f"{child.id} was upset because {child.pronoun('possessive')} {obj.label} was {problem.label} and had to leave the room for help. When {helper.id} said {f['wording']}, {child.pronoun()} misunderstood and thought it might mean forever."
        ),
        (
            f"What misunderstanding did {child.id} have about permanence?",
            f"{child.id} heard the words keep and {f['wording']} and worried they meant permanence, as if the {obj.label} would never come back. The fear was bigger than the real situation, because the helper only meant to fix it for a short time."
        ),
        (
            "What was the flashback about?",
            f"The flashback was about when {helper.id} found {memory.lost_item} from {memory.found_place} and returned it carefully. That memory mattered because it reminded {child.id} that {helper.id} had already shown kindness with precious things."
        ),
        (
            f"How did kindness change the story?",
            f"{helper.id} showed kindness by helping the {obj.label} instead of ignoring the problem, and then bringing it back safely. {child.id} answered with kindness too by choosing a gentle idea instead of only crying, which made the ending feel warm instead of sharp."
        ),
        (
            "How did the story end?",
            f"It ended with the {obj.label} back in its usual place and bedtime feeling safe again. The ending image proves what changed, because the empty spot was full again and {child.id} could rest."
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"permanence", "flashback", "bedtime", "kindness"}
    helper_cfg = world.facts["helper_cfg"]
    if helper_cfg.id == "neighbor":
        tags |= {"neighbor", "yenta"}
    else:
        tags |= {"grandmother"}
    method = world.facts["method_cfg"]
    if "sewing" in method.tags or "button" in method.tags:
        tags |= {"sewing"}
    if "drying" in method.tags:
        tags |= {"drying"}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:12} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A method is compatible if it fixes the problem's needed fix-tag.
compatible(Problem, Method) :- problem(Problem), method(Method),
                               needs_fix(Problem, Tag), fixes(Method, Tag).

% A helper is allowed for a problem+method pair when that pair is declared.
valid(Object, Problem, Helper, Method) :-
    bed_object(Object), problem(Problem), helper(Helper), method(Method),
    compatible(Problem, Method),
    helper_allows(Helper, Problem, Method).

% Misunderstanding risk: "overnight" plus an away-tonight problem is enough.
permanence_risk(2) :- wording(overnight), away_tonight.
permanence_risk(1) :- wording(overnight), not away_tonight.
likely_misunderstanding :- permanence_risk(R), R >= 2.

% The flashback works when the memory shows a returned item.
flashback_helps :- memory_returns.

% Happy ending if the story is valid and the helper returns the object.
resolved_return :- flashback_helps, likely_misunderstanding.
outcome(resolved) :- resolved_return.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for obj_id in BED_OBJECTS:
        lines.append(asp.fact("bed_object", obj_id))
    for prob_id, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", prob_id))
        lines.append(asp.fact("needs_fix", prob_id, prob.fix_tag))
        if prob.overnight_ok:
            lines.append(asp.fact("away_problem", prob_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for tag in sorted(method.fixes):
            lines.append(asp.fact("fixes", method_id, tag))
    for obj_id, prob_id, helper_id, method_id in valid_combos():
        lines.append(asp.fact("helper_allows", helper_id, prob_id, method_id))
    for mem_id, mem in MEMORIES.items():
        lines.append(asp.fact("memory", mem_id))
        if mem.shows_returning:
            lines.append(asp.fact("memory_returns_fact", mem_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    prob = PROBLEMS[params.problem]
    mem = MEMORIES[params.memory]
    extra_lines = [
        asp.fact("wording", params.wording),
    ]
    if prob.overnight_ok:
        extra_lines.append("away_tonight.")
    if mem.shows_returning:
        extra_lines.append("memory_returns.")
    model = asp.one_model(asp_program("\n".join(extra_lines), "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    bad = 0
    for params in cases:
        expected = "resolved"
        got = asp_outcome(params)
        if got != expected:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches expected resolved ending on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differed.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Parser / resolution / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime misunderstanding about a beloved object, a flashback, and a kind return."
    )
    ap.add_argument("--object", choices=BED_OBJECTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.problem not in PROBLEMS:
        raise StoryError("(Unknown problem.)")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("(Unknown helper.)")
    if args.method and args.method not in METHODS:
        raise StoryError("(Unknown method.)")
    if args.object and args.object not in BED_OBJECTS:
        raise StoryError("(Unknown object.)")
    if args.memory and args.memory not in MEMORIES:
        raise StoryError("(Unknown memory.)")

    if args.problem and args.helper and args.method:
        problem = PROBLEMS[args.problem]
        helper = HELPERS[args.helper]
        method = METHODS[args.method]
        if not helper_can_fix(helper, method, problem):
            raise StoryError(explain_rejection(problem, helper, method))

    combos = [
        combo for combo in valid_combos()
        if (args.object is None or combo[0] == args.object)
        and (args.problem is None or combo[1] == args.problem)
        and (args.helper is None or combo[2] == args.helper)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    obj_id, problem_id, helper_id, method_id = rng.choice(sorted(combos))
    memory_id = args.memory or rng.choice(sorted(MEMORIES))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    parent_type = args.parent or rng.choice(["mother", "father"])
    wording = "overnight"

    return StoryParams(
        object=obj_id,
        problem=problem_id,
        helper=helper_id,
        method=method_id,
        memory=memory_id,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        wording=wording,
    )


def generate(params: StoryParams) -> StorySample:
    if params.object not in BED_OBJECTS:
        raise StoryError(f"(Unknown object '{params.object}').")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem '{params.problem}').")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}').")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}').")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory '{params.memory}').")
    if params.wording not in WORDINGS:
        raise StoryError(f"(Unknown wording '{params.wording}').")

    obj_cfg = BED_OBJECTS[params.object]
    problem_cfg = PROBLEMS[params.problem]
    helper_cfg = HELPERS[params.helper]
    method_cfg = METHODS[params.method]
    memory_cfg = MEMORIES[params.memory]

    if not helper_can_fix(helper_cfg, method_cfg, problem_cfg):
        raise StoryError(explain_rejection(problem_cfg, helper_cfg, method_cfg))

    world = tell(
        obj_cfg=obj_cfg,
        problem_cfg=problem_cfg,
        helper_cfg=helper_cfg,
        method_cfg=method_cfg,
        memory_cfg=memory_cfg,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
        wording=params.wording,
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
        object="rabbit",
        problem="torn",
        helper="neighbor",
        method="needle_thread",
        memory="mitten",
        child_name="Mira",
        child_type="girl",
        parent_type="mother",
        wording="overnight",
    ),
    StoryParams(
        object="blanket",
        problem="wet",
        helper="grandmother",
        method="dry_rack",
        memory="shell",
        child_name="Owen",
        child_type="boy",
        parent_type="father",
        wording="overnight",
    ),
    StoryParams(
        object="bear",
        problem="button",
        helper="grandmother",
        method="button_tin",
        memory="crayon",
        child_name="Nora",
        child_type="girl",
        parent_type="mother",
        wording="overnight",
    ),
    StoryParams(
        object="pillow",
        problem="torn",
        helper="neighbor",
        method="needle_thread",
        memory="shell",
        child_name="Theo",
        child_type="boy",
        parent_type="father",
        wording="overnight",
    ),
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (object, problem, helper, method) combos:\n")
        for obj_id, prob_id, helper_id, method_id in combos:
            print(f"  {obj_id:8} {prob_id:8} {helper_id:11} {method_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.object} / {p.problem} / {p.helper} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
