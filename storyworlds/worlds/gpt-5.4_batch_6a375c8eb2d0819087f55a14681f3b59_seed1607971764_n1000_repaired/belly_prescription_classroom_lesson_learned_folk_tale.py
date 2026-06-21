#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/belly_prescription_classroom_lesson_learned_folk_tale.py
===================================================================================

A standalone story world for a small classroom folk tale about a child with a
troubled belly, a healer's prescription, a tempting classroom treat, and the
lesson learned by the end.

The world models a simple causal pattern:

    tender belly + wrong treat        -> belly pain worsens
    worsened belly                    -> fear / class concern
    right prescription + quick care   -> comfort and recovery
    strong warning from trusted elder -> temptation may be averted entirely

The prose is driven by simulated state rather than a frozen template, and the
world includes:
- a Python reasonableness gate (`valid_combos`)
- an inline ASP twin (`ASP_RULES`, `asp_facts`, `--verify`)
- three QA sets generated from world state
- trace / json / curated / random modes

Run it
------
    python storyworlds/worlds/gpt-5.4/belly_prescription_classroom_lesson_learned_folk_tale.py
    python storyworlds/worlds/gpt-5.4/belly_prescription_classroom_lesson_learned_folk_tale.py --belly sweet_belly --temptation honey_bun --prescription mint_tea
    python storyworlds/worlds/gpt-5.4/belly_prescription_classroom_lesson_learned_folk_tale.py --belly grease_belly --prescription quiet_rest
    python storyworlds/worlds/gpt-5.4/belly_prescription_classroom_lesson_learned_folk_tale.py --all --qa
    python storyworlds/worlds/gpt-5.4/belly_prescription_classroom_lesson_learned_folk_tale.py --verify
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
TRUST_TO_AVERT = 7
WISE_TRAITS = {"wise", "careful", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_woman"}
        male = {"boy", "father", "man", "teacher_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "teacher_woman": "teacher",
            "teacher_man": "teacher",
            "mother": "mother",
            "father": "father",
        }
        return mapping.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class BellyKind:
    id: str
    label: str
    sign: str
    warning: str
    triggers: set[str] = field(default_factory=set)
    severity: int = 2
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
class Temptation:
    id: str
    label: str
    phrase: str
    tray: str
    bite: str
    class_use: str
    taste: str
    triggers: set[str] = field(default_factory=set)
    burden: int = 2
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
class Prescription:
    id: str
    label: str
    phrase: str
    text: str
    action: str
    ending: str
    cures: set[str] = field(default_factory=set)
    strength: int = 2
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_belly_alarm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["belly_pain"] < THRESHOLD:
        return out
    sig = ("belly_alarm", child.id, int(child.meters["belly_pain"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper = world.get("helper")
    teacher = world.get("teacher")
    helper.memes["concern"] += 1
    teacher.memes["concern"] += 1
    world.get("classroom").meters["hush"] += 1
    out.append("__belly_alarm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="belly_alarm", tag="physical", apply=_r_belly_alarm),
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


def trigger_overlap(belly: BellyKind, temptation: Temptation) -> bool:
    return bool(set(belly.triggers) & set(temptation.triggers))


def prescription_matches(belly: BellyKind, prescription: Prescription) -> bool:
    return belly.id in prescription.cures


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for belly_id, belly in BELLIES.items():
        for temptation_id, temptation in TEMPTATIONS.items():
            for prescription_id, prescription in PRESCRIPTIONS.items():
                if trigger_overlap(belly, temptation) and prescription_matches(belly, prescription):
                    combos.append((belly_id, temptation_id, prescription_id))
    return sorted(combos)


def discomfort_value(belly: BellyKind, temptation: Temptation, delay: int) -> int:
    return belly.severity + temptation.burden + delay


def is_soothed(belly: BellyKind, prescription: Prescription, temptation: Temptation, delay: int) -> bool:
    return prescription.strength >= discomfort_value(belly, temptation, delay)


def would_obey(relation: str, child_age: int, helper_age: int, trait: str, trust: int) -> bool:
    older_and_close = relation == "cousins" and helper_age > child_age
    wise = trait in WISE_TRAITS
    return older_and_close and wise and trust >= TRUST_TO_AVERT


def predict_trouble(world: World, belly: BellyKind, temptation: Temptation) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["belly_pain"] += float(belly.severity + temptation.burden)
    child.meters["worse"] += 1.0
    propagate(sim, narrate=False)
    return {
        "pain": child.meters["belly_pain"],
        "class_hush": sim.get("classroom").meters["hush"],
    }


def opening(world: World, child: Entity, helper: Entity, teacher: Entity, belly: BellyKind) -> None:
    child.memes["hope"] += 1
    helper.memes["friendship"] += 1
    world.say(
        f"In a small classroom with tall windows and a blackboard dark as a crow's wing, "
        f"{child.id} sat beside {helper.id} while {teacher.id} rang the morning bell."
    )
    world.say(
        f"But {child.id} kept one hand over {child.pronoun('possessive')} belly, for it had "
        f"been grumbling since dawn with {belly.sign}."
    )


def healer_note(world: World, child: Entity, teacher: Entity, belly: BellyKind, prescription: Prescription) -> None:
    child.meters["belly_tender"] = 1.0
    world.facts["prescription_text"] = prescription.text
    world.say(
        f"Tucked in {child.pronoun('possessive')} reader was a little folded note from the village healer. "
        f'It was a prescription that said, "{prescription.text}."'
    )
    world.say(
        f"{teacher.id} read the note, nodded once, and set {prescription.phrase} on the side table in case it was needed."
    )


def lesson_setup(world: World, teacher: Entity, temptation: Temptation) -> None:
    world.say(
        f"That day the lesson was about counting and sharing, so {teacher.id} brought out {temptation.tray}."
    )
    world.say(
        f"The room filled with {temptation.taste}, and every child sat a little straighter at the sight."
    )


def temptation_beat(world: World, child: Entity, temptation: Temptation) -> None:
    child.memes["desire"] += 1
    world.say(
        f"When the tray passed by, {child.id} looked at {temptation.phrase} and thought how fine {temptation.bite} would taste."
    )


def warning(world: World, helper: Entity, child: Entity, belly: BellyKind, temptation: Temptation) -> None:
    pred = predict_trouble(world, belly, temptation)
    helper.memes["caution"] += 1
    world.facts["predicted_pain"] = pred["pain"]
    extra = ""
    if helper.memes["trustworthy"] >= 1:
        extra = f" {helper.id} spoke as one who truly wanted to keep {child.id} safe."
    world.say(
        f'{helper.id} touched the edge of the desk and whispered, "Remember the prescription. '
        f'{temptation.label.capitalize()} will trouble your belly again."{extra}'
    )


def obey(world: World, child: Entity, helper: Entity, teacher: Entity, prescription: Prescription) -> None:
    child.memes["restraint"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    teacher.memes["approval"] += 1
    world.say(
        f"{child.id} drew {child.pronoun('possessive')} hand back, folded it in {child.pronoun('possessive')} lap, "
        f"and let the treat pass on."
    )
    world.say(
        f"When the sums were done, {teacher.id} gave {child.id} {prescription.phrase}, and the morning grew gentle again."
    )


def sneak_bite(world: World, child: Entity, helper: Entity, temptation: Temptation, belly: BellyKind) -> None:
    child.memes["defiance"] += 1
    child.meters["belly_pain"] += float(belly.severity + temptation.burden)
    child.meters["worse"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"But wanting was stronger than wisdom for one foolish moment. {child.id} slipped {temptation.bite} into "
        f"{child.pronoun('possessive')} mouth while {teacher_name(world)} turned to write on the board."
    )
    world.say(
        f"At first the room stayed bright and ordinary. Then a hard twist ran through {child.pronoun('possessive')} belly, "
        f"and {child.pronoun()} bent over the desk with wide eyes."
    )


def teacher_name(world: World) -> str:
    return world.get("teacher").id


def classroom_hush(world: World, helper: Entity, teacher: Entity, child: Entity) -> None:
    helper.memes["fear"] += 1
    teacher.memes["concern"] += 1
    world.say(
        f'"Teacher!" cried {helper.id}. The chalk paused in {teacher.id}\'s hand, and the whole classroom fell quiet around {child.id}.'
    )


def soothing(world: World, teacher: Entity, child: Entity, prescription: Prescription) -> None:
    child.meters["belly_pain"] = 0.0
    child.memes["relief"] += 1
    child.memes["gratitude"] += 1
    teacher.memes["care"] += 1
    world.say(
        f"{teacher.id} followed the prescription exactly and {prescription.action}."
    )
    world.say(
        f"Little by little, the tight knot in {child.pronoun('possessive')} belly loosened, and color came back to {child.pronoun('possessive')} face."
    )


def send_home(world: World, teacher: Entity, child: Entity, prescription: Prescription) -> None:
    child.meters["belly_pain"] += 1.0
    child.memes["shame"] += 1
    child.memes["weariness"] += 1
    teacher.memes["care"] += 1
    world.say(
        f"{teacher.id} hurried to {prescription.action}, yet the ache had already grown stubborn."
    )
    world.say(
        f"So {teacher.pronoun()} wrapped {child.id} in a shawl from the classroom peg and sent {child.pronoun('object')} home early, "
        f"moving slowly as if even the floorboards should not jar {child.pronoun('possessive')} belly."
    )


def lesson_end(world: World, child: Entity, helper: Entity, teacher: Entity, temptation: Temptation, prescription: Prescription, outcome: str) -> None:
    child.memes["lesson"] += 1
    helper.memes["friendship"] += 1
    if outcome == "averted":
        world.say(
            f"Before the last bell, {teacher.id} smiled at {child.id} and said that wisdom is often quieter than hunger."
        )
        world.say(
            f"From that day on, whenever sweet smells wandered through the classroom, {child.id} remembered the healer's prescription and chose patience first."
        )
    elif outcome == "soothed":
        world.say(
            f"After the pain passed, {child.id} looked at {helper.id} and then at the untouched crumbs on the desk."
        )
        world.say(
            f'"A warning is a lantern before a ditch," said {teacher.id}. {child.id} nodded, and from that day on kept the prescription closer than any treat.'
        )
    else:
        world.say(
            f"That afternoon the empty desk seemed to speak its own plain lesson to every child in the room."
        )
        world.say(
            f"When {child.id} returned to the classroom the next morning, {child.pronoun()} thanked {helper.id} for the warning and said that {temptation.label} was never worth a hurting belly."
        )
    world.say(
        f"And so the lesson was learned: a small slip of good advice may look light as paper, yet it can weigh more than a feast."
    )


def tell(
    belly: BellyKind,
    temptation: Temptation,
    prescription: Prescription,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    helper_name: str = "Tomas",
    helper_gender: str = "boy",
    helper_trait: str = "wise",
    teacher_name_value: str = "Master Ivo",
    teacher_gender: str = "teacher_man",
    delay: int = 0,
    child_age: int = 7,
    helper_age: int = 9,
    relation: str = "cousins",
    trust: int = 8,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        age=child_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[helper_trait],
        attrs={"relation": relation},
    ))
    teacher = world.add(Entity(
        id=teacher_name_value,
        kind="character",
        type=teacher_gender,
        role="teacher",
    ))
    classroom = world.add(Entity(
        id="classroom",
        kind="thing",
        type="room",
        label="classroom",
    ))
    world.facts["setting"] = "classroom"
    world.facts["delay"] = delay
    world.facts["relation"] = relation
    world.facts["trust"] = trust
    world.facts["predicted_pain"] = 0.0
    helper.memes["trustworthy"] = 1.0 if helper_trait in WISE_TRAITS else 0.0

    opening(world, child, helper, teacher, belly)
    healer_note(world, child, teacher, belly, prescription)

    world.para()
    lesson_setup(world, teacher, temptation)
    temptation_beat(world, child, temptation)
    warning(world, helper, child, belly, temptation)

    averted = would_obey(relation, child_age, helper_age, helper_trait, trust)
    if averted:
        obey(world, child, helper, teacher, prescription)
        outcome = "averted"
    else:
        world.para()
        sneak_bite(world, child, helper, temptation, belly)
        classroom_hush(world, helper, teacher, child)
        world.para()
        if is_soothed(belly, prescription, temptation, delay):
            soothing(world, teacher, child, prescription)
            outcome = "soothed"
        else:
            send_home(world, teacher, child, prescription)
            outcome = "sent_home"

    world.para()
    lesson_end(world, child, helper, teacher, temptation, prescription, outcome)

    world.facts.update(
        child=child,
        helper=helper,
        teacher=teacher,
        belly_cfg=belly,
        temptation=temptation,
        prescription=prescription,
        outcome=outcome,
        averted=averted,
        pain=child.meters["belly_pain"],
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


BELLIES = {
    "sweet_belly": BellyKind(
        id="sweet_belly",
        label="a sugar-tender belly",
        sign="small sugary turns",
        warning="too much sweetness makes the belly cramp",
        triggers={"sweet"},
        severity=2,
        tags={"belly", "sweet_food"},
    ),
    "grease_belly": BellyKind(
        id="grease_belly",
        label="a heavy, greasy belly",
        sign="slow heavy churns",
        warning="greasy food sits like a stone in the belly",
        triggers={"greasy"},
        severity=3,
        tags={"belly", "greasy_food"},
    ),
    "sour_belly": BellyKind(
        id="sour_belly",
        label="a sour little belly",
        sign="sharp sour flips",
        warning="sour things make the belly pinch",
        triggers={"sour"},
        severity=2,
        tags={"belly", "sour_food"},
    ),
}

TEMPTATIONS = {
    "honey_bun": Temptation(
        id="honey_bun",
        label="honey bun",
        phrase="the glazed honey bun",
        tray="a wicker tray of little honey buns",
        bite="a soft golden bite",
        class_use="counting",
        taste="warm sweetness",
        triggers={"sweet"},
        burden=2,
        tags={"sweet_food", "sharing"},
    ),
    "fried_twist": Temptation(
        id="fried_twist",
        label="fried twist",
        phrase="the shiny fried twist",
        tray="a tin plate of fried twists for the arithmetic lesson",
        bite="a crisp salty bite",
        class_use="arithmetic",
        taste="hot oil and salt",
        triggers={"greasy"},
        burden=2,
        tags={"greasy_food", "sharing"},
    ),
    "pickle_plum": Temptation(
        id="pickle_plum",
        label="pickled plum",
        phrase="the wrinkled pickled plum",
        tray="a blue bowl of pickled plums for a measuring game",
        bite="a brave little bite",
        class_use="measuring",
        taste="sharp sour fruit",
        triggers={"sour"},
        burden=2,
        tags={"sour_food", "sharing"},
    ),
}

PRESCRIPTIONS = {
    "mint_tea": Prescription(
        id="mint_tea",
        label="mint tea",
        phrase="a cup of mint tea",
        text="Sip mint tea slowly and leave rich treats alone until your belly is calm",
        action="poured the mint tea into a small cup and had the child sip it slowly by the window",
        ending="kept a gentle cup near the slate pencils",
        cures={"sweet_belly", "sour_belly"},
        strength=5,
        tags={"prescription", "tea"},
    ),
    "rice_broth": Prescription(
        id="rice_broth",
        label="rice broth",
        phrase="a little bowl of rice broth",
        text="Take plain rice broth in small spoons and do not touch fried food today",
        action="brought a little bowl of rice broth and waited while the child took careful spoonfuls",
        ending="set a warm bowl where the steam could rise softly",
        cures={"grease_belly"},
        strength=5,
        tags={"prescription", "plain_food"},
    ),
    "quiet_rest": Prescription(
        id="quiet_rest",
        label="quiet rest",
        phrase="a folded shawl for quiet rest",
        text="Sit quietly, drink water, and let the belly settle before eating anything sweet",
        action="settled the child on the reading rug with water and a folded shawl for quiet rest",
        ending="left a shawl and cup waiting by the reading rug",
        cures={"sweet_belly"},
        strength=3,
        tags={"prescription", "rest"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Anya", "Rosa", "Talia", "Nella", "Iris", "Vera"]
BOY_NAMES = ["Tomas", "Milan", "Pavel", "Nico", "Ivo", "Joren", "Luka", "Petar"]
TEACHERS = [
    ("Master Ivo", "teacher_man"),
    ("Teacher Mara", "teacher_woman"),
]
HELPER_TRAITS = ["wise", "careful", "steady", "kind", "bright"]


@dataclass
class StoryParams:
    belly: str
    temptation: str
    prescription: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    helper_trait: str
    teacher_name: str
    teacher_gender: str
    delay: int = 0
    child_age: int = 7
    helper_age: int = 9
    relation: str = "cousins"
    trust: int = 8
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
    "belly": [
        (
            "What does it mean when your belly hurts?",
            "It means your stomach does not feel right. Sometimes it needs rest, plain food, or help from a grown-up."
        )
    ],
    "prescription": [
        (
            "What is a prescription?",
            "A prescription is careful health advice from a healer, nurse, or doctor. It tells what will help your body get better and what to avoid."
        )
    ],
    "tea": [
        (
            "Why can warm tea help someone feel better?",
            "Warm tea can feel gentle in the throat and belly. A grown-up may give it in small sips when that is the right care."
        )
    ],
    "plain_food": [
        (
            "Why do people sometimes eat plain food when their belly hurts?",
            "Plain food is gentle and simple. It is less likely to bother a sore belly than rich or greasy food."
        )
    ],
    "rest": [
        (
            "Why can resting help a hurting belly?",
            "Rest gives the body time to settle down. Being quiet can help you notice whether the pain is getting better or worse."
        )
    ],
    "sweet_food": [
        (
            "Why can too much sweet food upset a belly?",
            "Very sweet food can feel heavy or sharp if your stomach is already tender. That is why a grown-up may say to wait before eating it."
        )
    ],
    "greasy_food": [
        (
            "Why can greasy food make a sore belly feel worse?",
            "Greasy food is rich and heavy. If your belly already hurts, it can make the ache last longer."
        )
    ],
    "sour_food": [
        (
            "Why can sour food bother some people?",
            "Sour food has a sharp taste. For some sore bellies, that sharpness can make the pain feel stronger."
        )
    ],
    "sharing": [
        (
            "Why do teachers ask children to share treats fairly?",
            "Sharing teaches patience and kindness. It helps a classroom feel calm and fair for everyone."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "belly",
    "prescription",
    "sweet_food",
    "greasy_food",
    "sour_food",
    "tea",
    "plain_food",
    "rest",
    "sharing",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    belly = f["belly_cfg"]
    temptation = f["temptation"]
    prescription = f["prescription"]
    outcome = f["outcome"]
    base = (
        f'Write a classroom folk tale for a 3-to-5-year-old that uses the words "belly" and '
        f'"prescription". A child has {belly.label} and faces {temptation.phrase}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle folk tale where {helper.id}, a trusted older {f['relation'].rstrip('s') if f['relation'].endswith('s') else f['relation']}, "
            f"reminds {child.id} to follow a healer's prescription, so the child lets the treat pass by.",
            f"Write a lesson-learned story in a classroom where patience proves wiser than hunger and the child is helped by {prescription.label}.",
        ]
    if outcome == "soothed":
        return [
            base,
            f"Tell a folk tale where {child.id} ignores a warning, hurts {child.pronoun('possessive')} belly, and a teacher carefully follows the prescription to help.",
            f"Write a lesson-learned classroom story where one foolish bite leads to pain, care, and wiser choices afterward.",
        ]
    return [
        base,
        f"Tell a sadder folk-tale classroom story where {child.id} ignores the prescription, the belly pain grows too strong, and the child must go home early.",
        f"Write a lesson-learned story showing that good advice looks small at first but matters more than a tempting treat.",
    ]


def relation_phrase(relation: str) -> str:
    if relation == "cousins":
        return "cousins"
    if relation == "siblings":
        return "brother and sister" if relation == "siblings" else relation
    return "schoolmates"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    teacher = f["teacher"]
    belly = f["belly_cfg"]
    temptation = f["temptation"]
    prescription = f["prescription"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} in a classroom, {helper.id} who tries to help, and {teacher.id} who watches over the lesson."
        ),
        (
            "What was the problem at the start of the story?",
            f"{child.id} already had {belly.label}, and there was a healer's prescription about what would help. That made the classroom treat a real danger instead of a harmless snack."
        ),
        (
            "Why did the treat matter so much?",
            f"The treat matched the very kind of food that upset {child.id}'s belly. So one tempting bite could make the ache much worse, not better."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"Why did {child.id} not eat the {temptation.label}?",
            f"{helper.id} reminded {child.id} about the prescription before any harm was done. Because {child.id} trusted the warning, the treat passed by and the pain did not grow."
        ))
        qa.append((
            f"How did the story end?",
            f"It ended quietly and wisely. {teacher.id} gave {child.id} the care named in the prescription, and {child.id} learned that patience can protect a hurting belly."
        ))
    elif outcome == "soothed":
        qa.append((
            f"What happened after {child.id} ate the {temptation.label}?",
            f"{child.id}'s belly twisted painfully, and the whole classroom went still. Then {teacher.id} followed the prescription carefully, which helped the pain loosen little by little."
        ))
        qa.append((
            f"What lesson did {child.id} learn?",
            f"{child.id} learned that a warning should be heeded before trouble arrives. The prescription was not just a scrap of paper; it was good advice meant to keep the body safe."
        ))
    else:
        qa.append((
            f"Why was {child.id} sent home?",
            f"The ache had grown too strong before the prescription could fully help. Because the wrong treat had already upset the belly badly, {teacher.id} had to send {child.pronoun('object')} home to rest."
        ))
        qa.append((
            f"What lesson did the classroom learn?",
            f"Everyone saw that ignoring good advice can turn a small problem into a larger one. The empty desk the next day made the lesson plain before a word was spoken."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["belly_cfg"].tags) | set(f["temptation"].tags) | set(f["prescription"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        belly="sweet_belly",
        temptation="honey_bun",
        prescription="mint_tea",
        child_name="Mira",
        child_gender="girl",
        helper_name="Tomas",
        helper_gender="boy",
        helper_trait="wise",
        teacher_name="Master Ivo",
        teacher_gender="teacher_man",
        delay=0,
        child_age=7,
        helper_age=9,
        relation="cousins",
        trust=9,
    ),
    StoryParams(
        belly="grease_belly",
        temptation="fried_twist",
        prescription="rice_broth",
        child_name="Lina",
        child_gender="girl",
        helper_name="Nico",
        helper_gender="boy",
        helper_trait="kind",
        teacher_name="Teacher Mara",
        teacher_gender="teacher_woman",
        delay=0,
        child_age=7,
        helper_age=7,
        relation="schoolmates",
        trust=5,
    ),
    StoryParams(
        belly="sweet_belly",
        temptation="honey_bun",
        prescription="quiet_rest",
        child_name="Pavel",
        child_gender="boy",
        helper_name="Rosa",
        helper_gender="girl",
        helper_trait="bright",
        teacher_name="Teacher Mara",
        teacher_gender="teacher_woman",
        delay=1,
        child_age=8,
        helper_age=8,
        relation="schoolmates",
        trust=4,
    ),
    StoryParams(
        belly="sour_belly",
        temptation="pickle_plum",
        prescription="mint_tea",
        child_name="Anya",
        child_gender="girl",
        helper_name="Vera",
        helper_gender="girl",
        helper_trait="careful",
        teacher_name="Master Ivo",
        teacher_gender="teacher_man",
        delay=0,
        child_age=6,
        helper_age=8,
        relation="cousins",
        trust=8,
    ),
]


def explain_rejection(belly: BellyKind, temptation: Temptation, prescription: Prescription) -> str:
    if not trigger_overlap(belly, temptation):
        return (
            f"(No story: {temptation.label} would not be the food that troubles this kind of belly, "
            f"so the warning would not be honest. Pick a temptation that really worsens the belly pain.)"
        )
    if not prescription_matches(belly, prescription):
        return (
            f"(No story: {prescription.label} is not a fitting prescription for this belly trouble. "
            f"Choose a prescription that truly matches the child's ailment.)"
        )
    return "(No story: this combination does not form a sensible lesson-learned tale.)"


def outcome_of(params: StoryParams) -> str:
    if would_obey(params.relation, params.child_age, params.helper_age, params.helper_trait, params.trust):
        return "averted"
    belly = BELLIES[params.belly]
    temptation = TEMPTATIONS[params.temptation]
    prescription = PRESCRIPTIONS[params.prescription]
    return "soothed" if is_soothed(belly, prescription, temptation, params.delay) else "sent_home"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
aggravates(B, T) :- belly(B), temptation(T), trigger(B, K), trigger_t(T, K).
fits(B, P)       :- belly(B), prescription(P), cures(P, B).
valid(B, T, P)   :- aggravates(B, T), fits(B, P).

% --- outcome model ---------------------------------------------------------
older_close      :- relation(cousins), helper_age(HA), child_age(CA), HA > CA.
wise_helper      :- helper_trait(T), wise_trait(T).
averted          :- older_close, wise_helper, trust(V), trust_min(M), V >= M.

discomfort(S + Bu + D) :- chosen_belly(B), chosen_temptation(T), chosen_prescription(P),
                          severity(B, S), burden(T, Bu), delay(D), fits(B, P).
soothed          :- chosen_belly(B), chosen_prescription(P), chosen_temptation(T),
                    discomfort(V), strength(P, S), S >= V, not averted.

outcome(averted)   :- averted.
outcome(soothed)   :- not averted, soothed.
outcome(sent_home) :- not averted, not soothed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for belly_id, belly in BELLIES.items():
        lines.append(asp.fact("belly", belly_id))
        lines.append(asp.fact("severity", belly_id, belly.severity))
        for trig in sorted(belly.triggers):
            lines.append(asp.fact("trigger", belly_id, trig))
    for temptation_id, temptation in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", temptation_id))
        lines.append(asp.fact("burden", temptation_id, temptation.burden))
        for trig in sorted(temptation.triggers):
            lines.append(asp.fact("trigger_t", temptation_id, trig))
    for prescription_id, prescription in PRESCRIPTIONS.items():
        lines.append(asp.fact("prescription", prescription_id))
        lines.append(asp.fact("strength", prescription_id, prescription.strength))
        for belly_id in sorted(prescription.cures):
            lines.append(asp.fact("cures", prescription_id, belly_id))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
    lines.append(asp.fact("trust_min", TRUST_TO_AVERT))
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
        asp.fact("chosen_belly", params.belly),
        asp.fact("chosen_temptation", params.temptation),
        asp.fact("chosen_prescription", params.prescription),
        asp.fact("relation", params.relation),
        asp.fact("helper_age", params.helper_age),
        asp.fact("child_age", params.child_age),
        asp.fact("helper_trait", params.helper_trait),
        asp.fact("trust", params.trust),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Classroom folk tale storyworld: a hurting belly, a prescription, and a lesson learned."
    )
    ap.add_argument("--belly", choices=sorted(BELLIES))
    ap.add_argument("--temptation", choices=sorted(TEMPTATIONS))
    ap.add_argument("--prescription", choices=sorted(PRESCRIPTIONS))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long care waits after the foolish bite")
    ap.add_argument("--teacher", choices=["master_ivo", "teacher_mara"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def teacher_choice(key: Optional[str], rng: random.Random) -> tuple[str, str]:
    mapping = {
        "master_ivo": ("Master Ivo", "teacher_man"),
        "teacher_mara": ("Teacher Mara", "teacher_woman"),
    }
    if key:
        return mapping[key]
    return rng.choice(TEACHERS)


def pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.belly and args.temptation and args.prescription:
        belly = BELLIES[args.belly]
        temptation = TEMPTATIONS[args.temptation]
        prescription = PRESCRIPTIONS[args.prescription]
        if not (trigger_overlap(belly, temptation) and prescription_matches(belly, prescription)):
            raise StoryError(explain_rejection(belly, temptation, prescription))
    combos = [
        c for c in valid_combos()
        if (args.belly is None or c[0] == args.belly)
        and (args.temptation is None or c[1] == args.temptation)
        and (args.prescription is None or c[2] == args.prescription)
    ]
    if not combos:
        if args.belly and args.temptation and args.prescription:
            raise StoryError(explain_rejection(BELLIES[args.belly], TEMPTATIONS[args.temptation], PRESCRIPTIONS[args.prescription]))
        raise StoryError("(No valid combination matches the given options.)")

    belly_id, temptation_id, prescription_id = rng.choice(combos)
    child_name, child_gender = pick_child(rng)
    helper_name, helper_gender = pick_child(rng, avoid=child_name)
    helper_trait = rng.choice(HELPER_TRAITS)
    teacher_name_value, teacher_gender = teacher_choice(args.teacher, rng)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["cousins", "schoolmates"])
    child_age, helper_age = rng.sample([6, 7, 8, 9], 2)
    trust = rng.randint(3, 10)
    return StoryParams(
        belly=belly_id,
        temptation=temptation_id,
        prescription=prescription_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        teacher_name=teacher_name_value,
        teacher_gender=teacher_gender,
        delay=delay,
        child_age=child_age,
        helper_age=helper_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        belly = BELLIES[params.belly]
        temptation = TEMPTATIONS[params.temptation]
        prescription = PRESCRIPTIONS[params.prescription]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc.args[0]})") from None
    if not trigger_overlap(belly, temptation) or not prescription_matches(belly, prescription):
        raise StoryError(explain_rejection(belly, temptation, prescription))

    world = tell(
        belly=belly,
        temptation=temptation,
        prescription=prescription,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        teacher_name_value=params.teacher_name,
        teacher_gender=params.teacher_gender,
        delay=params.delay,
        child_age=params.child_age,
        helper_age=params.helper_age,
        relation=params.relation,
        trust=params.trust,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for s in range(100):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (belly, temptation, prescription) combos:\n")
        for belly, temptation, prescription in combos:
            print(f"  {belly:13} {temptation:12} {prescription}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.child_name}: {p.belly} / {p.temptation} / {p.prescription} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
