#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stripe_answer_bad_ending_reconciliation_heartwarming.py
==================================================================================

A standalone storyworld about two children making something together, a hurtful
answer that leads to a small disaster, and either a sad parting or a warm
reconciliation.

This domain is built to satisfy the seed words "stripe" and "answer" while
keeping the prose heartwarming. The world model is simple and concrete:

- two children are holding up and decorating a shared display
- one child paints a stripe while the paint is still wet
- the other child asks a helpful question
- a sharp answer hurts feelings and makes the helper step back
- without both pairs of hands, the display slips, smears, and tears
- if the sharp child apologizes in time and the chosen repair actually fits the
  material, they mend it together and reconcile
- otherwise the event begins with the display still torn, and the ending stays sad

Run it:
    python storyworlds/worlds/gpt-5.4/stripe_answer_bad_ending_reconciliation_heartwarming.py
    python storyworlds/worlds/gpt-5.4/stripe_answer_bad_ending_reconciliation_heartwarming.py --project banner --repair tape --apology quick
    python storyworlds/worlds/gpt-5.4/stripe_answer_bad_ending_reconciliation_heartwarming.py --project curtain --repair tape
    python storyworlds/worlds/gpt-5.4/stripe_answer_bad_ending_reconciliation_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/stripe_answer_bad_ending_reconciliation_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/stripe_answer_bad_ending_reconciliation_heartwarming.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    material: str
    place: str
    event: str
    opening: str
    ending_image: str
    tear_size: int
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
class Stripe:
    id: str
    color: str
    line: str
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
class AnswerStyle:
    id: str
    text: str
    hurt: int
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
class Repair:
    id: str
    label: str
    materials: set[str]
    sense: int
    strength: int
    text: str
    fail: str
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
class Apology:
    id: str
    timing: int
    text: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.role in {"painter", "holder"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def mark(self, event: str) -> None:
        self.history.append(event)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
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


def _r_withdraw(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    project = world.get("project")
    if helper.memes["hurt"] < THRESHOLD:
        return out
    sig = ("withdraw", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if helper.attrs.get("holding", False):
        helper.attrs["holding"] = False
        project.meters["support"] -= 1
        project.meters["crooked"] += 1
        world.mark("helper_withdrew")
        out.append("__withdraw__")
    return out


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["wet_paint"] < THRESHOLD or project.meters["support"] >= 2:
        return out
    sig = ("slip", project.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["fallen"] += 1
    project.meters["smeared"] += 1
    project.meters["torn"] += float(world.facts["project_cfg"].tear_size)
    for kid in world.kids():
        kid.memes["alarm"] += 1
    world.mark("project_slipped")
    out.append("__slip__")
    return out


def _r_event_lost(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["torn"] < THRESHOLD:
        return out
    sig = ("event_lost", project.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("teacher").memes["worry"] += 1
    world.mark("display_not_ready")
    return out


CAUSAL_RULES = [
    Rule(name="withdraw", tag="social", apply=_r_withdraw),
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="event_lost", tag="social", apply=_r_event_lost),
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
            if sent == "__withdraw__":
                helper = world.get("helper")
                world.say(
                    f"{helper.id}'s face fell. {helper.pronoun().capitalize()} let go of one corner and stepped back."
                )
            elif sent == "__slip__":
                project = world.facts["project_cfg"]
                world.say(
                    f"Without two steady pairs of hands, the {project.label} slipped sideways. Wet paint smeared, and one edge tore."
                )
    return produced


def repair_fits(project: Project, repair: Repair) -> bool:
    return project.material in repair.materials


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for project_id, project in PROJECTS.items():
        for stripe_id in STRIPES:
            for answer_id in ANSWERS:
                for repair_id, repair in REPAIRS.items():
                    if repair_fits(project, repair):
                        for apology_id in APOLOGIES:
                            combos.append((project_id, stripe_id, answer_id, repair_id, apology_id))
    return combos


def tear_can_be_fixed(project: Project, repair: Repair) -> bool:
    return repair.strength >= project.tear_size


def outcome_of(params: "StoryParams") -> str:
    project = PROJECTS[params.project]
    repair = REPAIRS[params.repair]
    apology = APOLOGIES[params.apology]
    if not repair_fits(project, repair):
        raise StoryError(explain_repair_rejection(project, repair))
    if apology.timing == 0 and tear_can_be_fixed(project, repair):
        return "reconciled"
    return "sad"


def predict_slip(world: World) -> dict:
    sim = world.copy()
    helper = sim.get("helper")
    helper.memes["hurt"] += float(sim.facts["answer_cfg"].hurt)
    propagate(sim, narrate=False)
    project = sim.get("project")
    return {
        "slips": project.meters["fallen"] >= THRESHOLD,
        "torn": project.meters["torn"],
    }


def introduce(world: World, painter: Entity, helper: Entity, teacher: Entity, project: Project) -> None:
    painter.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After lunch, {teacher.id} set out paper, cloth, and boxes of markers for {project.event}. "
        f"{painter.id} and {helper.id} were chosen to make {project.phrase}."
    )
    world.say(project.opening)


def hold_and_paint(world: World, painter: Entity, helper: Entity, project: Project, stripe: Stripe) -> None:
    item = world.get("project")
    painter.attrs["holding"] = True
    helper.attrs["holding"] = True
    item.meters["support"] = 2.0
    item.meters["wet_paint"] = 1.0
    item.attrs["stripe_color"] = stripe.color
    world.say(
        f"Together they lifted the {project.label} between them. {painter.id} dipped a brush and pulled a long {stripe.line} across the middle."
    )


def ask_question(world: World, helper: Entity) -> None:
    pred = predict_slip(world)
    world.facts["predicted_slip"] = pred["slips"]
    world.facts["predicted_torn"] = pred["torn"]
    helper.memes["care"] += 1
    world.say(
        f'"Should I hold this corner higher, or is the paint too wet?" {helper.id} asked.'
    )


def sharp_answer(world: World, painter: Entity, helper: Entity, answer: AnswerStyle) -> None:
    helper.memes["hurt"] += float(answer.hurt)
    painter.memes["pride"] += 1
    world.say(f'{painter.id} gave a quick answer: "{answer.text}"')
    propagate(world, narrate=True)


def see_damage(world: World, painter: Entity, helper: Entity, project: Project) -> None:
    painter.memes["regret"] += 1
    helper.memes["sadness"] += 1
    world.say(
        f"For a second both children only stared. The bright stripe was still there, but now it wobbled through a smear and a tear."
    )
    world.say(
        f"{painter.id} understood that the hurtful answer had mattered just as much as the slipping corner."
    )


def quick_apology(world: World, painter: Entity, helper: Entity, apology: Apology) -> None:
    painter.memes["kindness"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"{painter.id} took a breath, looked at {helper.id}, and {apology.text}"
    )
    helper.memes["hurt"] = 0.0
    helper.attrs["holding"] = True
    world.get("project").meters["support"] = 2.0
    world.mark("apology_made")


def no_apology_yet(world: World, painter: Entity, helper: Entity, apology: Apology) -> None:
    painter.memes["shame"] += 1
    helper.memes["distance"] += 1
    if apology.id == "late":
        world.say(
            f"{painter.id} wanted to say sorry, but the words stayed stuck for too long."
        )
    else:
        world.say(
            f"{painter.id} looked at the floor and gave no softer answer at all."
        )


def mend_together(world: World, painter: Entity, helper: Entity, teacher: Entity,
                  project: Project, repair: Repair) -> None:
    item = world.get("project")
    item.meters["torn"] = 0.0
    item.meters["smeared"] = 0.0
    item.meters["wet_paint"] = 0.0
    item.meters["mended"] += 1
    painter.memes["relief"] += 1
    helper.memes["relief"] += 1
    painter.memes["closeness"] += 1
    helper.memes["closeness"] += 1
    world.say(
        f"{teacher.id} knelt beside them, but only smiled and handed over {repair.label}. {painter.id} and {helper.id} {repair.text}"
    )
    world.say(
        f"When they lifted it again, the stripe was not perfect anymore, yet it looked brave and bright."
    )
    world.say(
        f"At {project.place}, everyone could see the careful mended place, and everyone could see that the two friends were smiling at each other again."
    )
    world.say(project.ending_image)
    world.mark("repaired_together")


def sad_event(world: World, painter: Entity, helper: Entity, teacher: Entity, project: Project) -> None:
    painter.memes["sadness"] += 1
    helper.memes["sadness"] += 1
    teacher.memes["gentleness"] += 1
    world.say(
        f"Soon the others were walking toward {project.place} for {project.event}, but the torn {project.label} stayed on the table."
    )
    world.say(
        f"{teacher.id} spoke softly and said they could try again another day, yet the room felt smaller than before."
    )
    world.say(
        f"{painter.id} and {helper.id} stood apart, each wishing for a kinder answer that had not come in time."
    )
    world.mark("sad_ending")


PROJECTS = {
    "banner": Project(
        id="banner",
        label="banner",
        phrase="a welcome banner",
        material="paper",
        place="the classroom door",
        event="the family reading afternoon",
        opening="They wanted it to be the first thing families saw when they came in.",
        ending_image="By the time the first families arrived, the banner fluttered over the door like a little promise kept.",
        tear_size=1,
        tags={"banner", "paper", "classroom"},
    ),
    "sign": Project(
        id="sign",
        label="sign",
        phrase="a garden sign",
        material="cardboard",
        place="the seedling table",
        event="the spring seed swap",
        opening="They decided their sign should point everyone toward the tiny green seedlings on the windowsill.",
        ending_image="Later, their sign leaned by the seedling table, and the mended stripe seemed to shine in the afternoon sun.",
        tear_size=2,
        tags={"sign", "cardboard", "garden"},
    ),
    "curtain": Project(
        id="curtain",
        label="curtain",
        phrase="a little reading-nook curtain",
        material="cloth",
        place="the reading corner",
        event="story circle",
        opening="They wanted the reading corner to feel like a snug little tent for story time.",
        ending_image="When story circle began, the curtain hung in the corner with its bright stripe and its tiny healed patch, cozy as a hug.",
        tear_size=2,
        tags={"curtain", "cloth", "reading"},
    ),
}

STRIPES = {
    "gold": Stripe(
        id="gold",
        color="gold",
        line="gold stripe",
        tags={"stripe", "paint"},
    ),
    "blue": Stripe(
        id="blue",
        color="blue",
        line="blue stripe",
        tags={"stripe", "paint"},
    ),
    "red": Stripe(
        id="red",
        color="red",
        line="red stripe",
        tags={"stripe", "paint"},
    ),
}

ANSWERS = {
    "snappy": AnswerStyle(
        id="snappy",
        text="Just keep still. I know where the stripe goes.",
        hurt=2,
        tags={"answer", "feelings"},
    ),
    "bossy": AnswerStyle(
        id="bossy",
        text="Don't ask again. You're making it harder.",
        hurt=2,
        tags={"answer", "feelings"},
    ),
    "brisk": AnswerStyle(
        id="brisk",
        text="I said hold it straight.",
        hurt=1,
        tags={"answer", "feelings"},
    ),
}

REPAIRS = {
    "tape": Repair(
        id="tape",
        label="clear tape",
        materials={"paper", "cardboard"},
        sense=3,
        strength=2,
        text="pressed the torn edge flat and smoothed clear tape over the rip together.",
        fail="tried to use tape, but it would not sit right on the material.",
        qa_text="mended the tear with clear tape",
        tags={"tape", "mend"},
    ),
    "glue": Repair(
        id="glue",
        label="school glue",
        materials={"paper"},
        sense=2,
        strength=1,
        text="matched the torn paper edge and held it gently while the glue dried.",
        fail="used glue, but the tear was too heavy and opened again.",
        qa_text="matched the paper edge and glued it carefully",
        tags={"glue", "mend"},
    ),
    "brace": Repair(
        id="brace",
        label="a stiff backing strip",
        materials={"cardboard"},
        sense=3,
        strength=3,
        text="set a stiff backing strip behind the tear and fixed the sign straight again.",
        fail="tried to brace it, but the sign still sagged.",
        qa_text="braced the torn sign from behind",
        tags={"brace", "mend"},
    ),
    "patch": Repair(
        id="patch",
        label="a soft cloth patch",
        materials={"cloth"},
        sense=3,
        strength=3,
        text="placed a soft cloth patch behind the tear and stitched the little curtain neatly.",
        fail="tried to patch it, but the cloth still pulled apart.",
        qa_text="patched the torn cloth and stitched it neatly",
        tags={"patch", "mend"},
    ),
}

APOLOGIES = {
    "quick": Apology(
        id="quick",
        timing=0,
        text='said, "I am sorry. That answer was unkind. Will you help me fix it?"',
        tags={"apology", "reconciliation"},
    ),
    "late": Apology(
        id="late",
        timing=1,
        text='whispered sorry only after the room had already grown quiet around them.',
        tags={"apology"},
    ),
    "none": Apology(
        id="none",
        timing=2,
        text="said nothing at all.",
        tags={"silence"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "eager", "thoughtful", "bright", "steady", "gentle"]


@dataclass
class StoryParams:
    project: str
    stripe: str
    answer: str
    repair: str
    apology: str
    painter: str
    painter_gender: str
    helper: str
    helper_gender: str
    teacher_name: str = "Ms. Vale"
    teacher_type: str = "teacher"
    painter_trait: str = "eager"
    helper_trait: str = "careful"
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


def explain_repair_rejection(project: Project, repair: Repair) -> str:
    mats = ", ".join(sorted(repair.materials))
    return (
        f"(No story: {repair.label} is not a reasonable way to mend a {project.material} "
        f"{project.label}. That repair fits {mats}, so choose a repair that matches the material.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    project = f["project_cfg"]
    stripe = f["stripe_cfg"]
    painter = f["painter"]
    helper = f["helper"]
    outcome = f["outcome"]
    base = (
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words '
        f'"stripe" and "answer". Two children are making a {project.label} together, '
        f'a hurtful answer causes trouble, and the story turns on whether they make peace.'
    )
    if outcome == "reconciled":
        return [
            base,
            f"Tell a gentle classroom story where {painter.id} paints a {stripe.color} stripe, gives {helper.id} a sharp answer, and then apologizes so they can mend the {project.label} together.",
            f"Write a warm story about a mistake, a torn {project.label}, and reconciliation in time for {project.event}.",
        ]
    return [
        base,
        f"Tell a sad but child-safe story where {painter.id} gives {helper.id} a hurtful answer while painting a stripe, and the torn {project.label} is not fixed in time.",
        f"Write a simple story showing how one unkind answer can spoil shared work when sorry comes too late.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    painter = f["painter"]
    helper = f["helper"]
    teacher = f["teacher"]
    project = f["project_cfg"]
    stripe = f["stripe_cfg"]
    answer = f["answer_cfg"]
    repair = f["repair_cfg"]
    apology = f["apology_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {painter.id} and {helper.id}, two children working together with {teacher.id}. They were making {project.phrase} for {project.event}.",
        ),
        (
            f"What were they making, and what did the stripe look like?",
            f"They were making {project.phrase}. {painter.id} painted a long {stripe.line} across it so it would look bright and special.",
        ),
        (
            f"What question did {helper.id} ask?",
            f"{helper.id} asked whether the corner should be held higher or whether the paint was still too wet. The question was meant to help keep the work steady.",
        ),
        (
            f"Why did the project slip and tear?",
            f"It slipped because {painter.id}'s answer hurt {helper.id}'s feelings, so {helper.pronoun()} stepped back and let go of one corner. With only one child holding it while the paint was wet, the {project.label} smeared and tore.",
        ),
    ]
    if f["outcome"] == "reconciled":
        qa.append(
            (
                f"How did they make peace?",
                f"{painter.id} apologized quickly and admitted the answer had been unkind. That helped {helper.id} come back, so they could work side by side again.",
            )
        )
        qa.append(
            (
                f"How did they fix the {project.label}?",
                f"They {repair.qa_text}. Because that repair matched the {project.material} material, the torn part could hold together.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly at {project.place}. The mended {project.label} was ready for {project.event}, and the children were smiling at each other again.",
            )
        )
    else:
        if apology.id == "late":
            sorry_clause = "The sorry came too late to bring them back into the work together."
        else:
            sorry_clause = "No apology came in time to heal the hurt."
        qa.append(
            (
                "Did they reconcile in time?",
                f"No. {sorry_clause} By then the torn {project.label} was still on the table, and the sad feeling stayed between them.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly when the others went to {project.place} for {project.event} without the finished {project.label}. {painter.id} and {helper.id} both wished the answer had been kinder.",
            )
        )
    return qa


KNOWLEDGE = {
    "stripe": [
        (
            "What is a stripe?",
            "A stripe is a long narrow band of color or pattern. You might see a stripe on clothes, a flag, or a painting.",
        )
    ],
    "answer": [
        (
            "Why can an answer hurt someone's feelings?",
            "An answer can hurt if it sounds mean or impatient. Words can make a person feel small even when nothing touches their body.",
        )
    ],
    "tape": [
        (
            "What does tape do when something paper or cardboard tears?",
            "Tape can hold the ripped edges together so they do not flap apart. It works best when the material is smooth and light.",
        )
    ],
    "glue": [
        (
            "What does glue do?",
            "Glue helps two pieces stick together after they come apart. It needs time to dry so the join can hold.",
        )
    ],
    "patch": [
        (
            "What is a patch?",
            "A patch is an extra piece of cloth used to cover or strengthen a torn spot. It helps weak fabric hold together again.",
        )
    ],
    "mend": [
        (
            "What does it mean to mend something?",
            "To mend something means to fix what was torn or broken. People can also mend feelings by telling the truth and saying sorry.",
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you are sorry for something hurtful or wrong. A real apology shows that you understand the hurt and want to make things better.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when people come back together after hurt or anger. It usually needs honesty, kindness, and a wish to repair what went wrong.",
        )
    ],
}
KNOWLEDGE_ORDER = ["stripe", "answer", "tape", "glue", "patch", "mend", "apology", "reconciliation"]


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"stripe", "answer", "mend"}
    tags |= set(world.facts["repair_cfg"].tags)
    if world.facts["outcome"] == "reconciled":
        tags |= {"apology", "reconciliation"}
    elif world.facts["apology_cfg"].id != "none":
        tags |= {"apology"}
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def tell(project: Project, stripe: Stripe, answer: AnswerStyle, repair: Repair, apology: Apology,
         painter_name: str = "Lily", painter_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         teacher_name: str = "Ms. Vale", teacher_type: str = "teacher",
         painter_trait: str = "eager", helper_trait: str = "careful") -> World:
    world = World()
    painter = world.add(
        Entity(
            id=painter_name,
            kind="character",
            type=painter_gender,
            role="painter",
            traits=[painter_trait],
            attrs={"holding": False},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="holder",
            traits=[helper_trait],
            attrs={"holding": False},
        )
    )
    teacher = world.add(
        Entity(
            id=teacher_name,
            kind="character",
            type=teacher_type,
            role="teacher",
            attrs={},
        )
    )
    display = world.add(
        Entity(
            id="project",
            kind="thing",
            type=project.material,
            label=project.label,
            phrase=project.phrase,
            attrs={"stripe_color": "", "ready": False},
        )
    )
    display.meters["support"] = 2.0
    display.meters["wet_paint"] = 0.0
    display.meters["torn"] = 0.0
    display.meters["smeared"] = 0.0
    display.meters["fallen"] = 0.0
    world.facts.update(
        project_cfg=project,
        stripe_cfg=stripe,
        answer_cfg=answer,
        repair_cfg=repair,
        apology_cfg=apology,
        painter=painter,
        helper=helper,
        teacher=teacher,
    )

    introduce(world, painter, helper, teacher, project)
    hold_and_paint(world, painter, helper, project, stripe)

    world.para()
    ask_question(world, helper)
    sharp_answer(world, painter, helper, answer)
    see_damage(world, painter, helper, project)

    world.para()
    if apology.timing == 0 and tear_can_be_fixed(project, repair):
        quick_apology(world, painter, helper, apology)
        mend_together(world, painter, helper, teacher, project, repair)
        outcome = "reconciled"
    else:
        no_apology_yet(world, painter, helper, apology)
        sad_event(world, painter, helper, teacher, project)
        outcome = "sad"

    world.facts["outcome"] = outcome
    world.facts["repair_possible"] = repair_fits(project, repair)
    world.facts["tear_fixed"] = outcome == "reconciled"
    return world


CURATED = [
    StoryParams(
        project="banner",
        stripe="gold",
        answer="snappy",
        repair="tape",
        apology="quick",
        painter="Lily",
        painter_gender="girl",
        helper="Ben",
        helper_gender="boy",
        teacher_name="Ms. Vale",
        teacher_type="teacher",
        painter_trait="eager",
        helper_trait="careful",
    ),
    StoryParams(
        project="sign",
        stripe="blue",
        answer="bossy",
        repair="brace",
        apology="quick",
        painter="Max",
        painter_gender="boy",
        helper="Ava",
        helper_gender="girl",
        teacher_name="Ms. Vale",
        teacher_type="teacher",
        painter_trait="bright",
        helper_trait="steady",
    ),
    StoryParams(
        project="curtain",
        stripe="red",
        answer="snappy",
        repair="patch",
        apology="quick",
        painter="Nora",
        painter_gender="girl",
        helper="Finn",
        helper_gender="boy",
        teacher_name="Ms. Vale",
        teacher_type="teacher",
        painter_trait="thoughtful",
        helper_trait="gentle",
    ),
    StoryParams(
        project="banner",
        stripe="blue",
        answer="bossy",
        repair="glue",
        apology="late",
        painter="Theo",
        painter_gender="boy",
        helper="Mia",
        helper_gender="girl",
        teacher_name="Ms. Vale",
        teacher_type="teacher",
        painter_trait="eager",
        helper_trait="careful",
    ),
    StoryParams(
        project="sign",
        stripe="gold",
        answer="brisk",
        repair="brace",
        apology="none",
        painter="Ella",
        painter_gender="girl",
        helper="Leo",
        helper_gender="boy",
        teacher_name="Ms. Vale",
        teacher_type="teacher",
        painter_trait="bright",
        helper_trait="steady",
    ),
]


ASP_RULES = r"""
repair_fits(P, R) :- project(P), repair(R), material(P, M), repair_material(R, M).
valid(P, S, A, R, Ap) :- project(P), stripe(S), answer_style(A), repair(R), apology(Ap), repair_fits(P, R).

tear_fixed :- chosen_project(P), chosen_repair(R), tear_size(P, T), repair_strength(R, S), S >= T.
reconciled :- chosen_apology(quick), tear_fixed.
sad :- not reconciled.

outcome(reconciled) :- reconciled.
outcome(sad) :- sad.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("material", pid, project.material))
        lines.append(asp.fact("tear_size", pid, project.tear_size))
    for sid in STRIPES:
        lines.append(asp.fact("stripe", sid))
    for aid in ANSWERS:
        lines.append(asp.fact("answer_style", aid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("repair_strength", rid, repair.strength))
        for material in sorted(repair.materials):
            lines.append(asp.fact("repair_material", rid, material))
    for apid in APOLOGIES:
        lines.append(asp.fact("apology", apid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_repair", params.repair),
            asp.fact("chosen_apology", params.apology),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a stripe, a hurtful answer, and either reconciliation or a sad missed moment."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--stripe", choices=STRIPES)
    ap.add_argument("--answer", choices=ANSWERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--apology", choices=APOLOGIES)
    ap.add_argument("--teacher-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and args.repair:
        project = PROJECTS[args.project]
        repair = REPAIRS[args.repair]
        if not repair_fits(project, repair):
            raise StoryError(explain_repair_rejection(project, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.stripe is None or combo[1] == args.stripe)
        and (args.answer is None or combo[2] == args.answer)
        and (args.repair is None or combo[3] == args.repair)
        and (args.apology is None or combo[4] == args.apology)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, stripe_id, answer_id, repair_id, apology_id = rng.choice(sorted(combos))
    painter_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    painter = _pick_name(rng, painter_gender)
    helper = _pick_name(rng, helper_gender, avoid=painter)
    teacher_name = args.teacher_name or "Ms. Vale"
    return StoryParams(
        project=project_id,
        stripe=stripe_id,
        answer=answer_id,
        repair=repair_id,
        apology=apology_id,
        painter=painter,
        painter_gender=painter_gender,
        helper=helper,
        helper_gender=helper_gender,
        teacher_name=teacher_name,
        teacher_type="teacher",
        painter_trait=rng.choice(TRAITS),
        helper_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    for key, registry in [
        ("project", PROJECTS),
        ("stripe", STRIPES),
        ("answer", ANSWERS),
        ("repair", REPAIRS),
        ("apology", APOLOGIES),
    ]:
        value = getattr(params, key)
        if value not in registry:
            raise StoryError(f"(Invalid {key}: {value})")

    project = PROJECTS[params.project]
    repair = REPAIRS[params.repair]
    if not repair_fits(project, repair):
        raise StoryError(explain_repair_rejection(project, repair))

    world = tell(
        project=project,
        stripe=STRIPES[params.stripe],
        answer=ANSWERS[params.answer],
        repair=repair,
        apology=APOLOGIES[params.apology],
        painter_name=params.painter,
        painter_gender=params.painter_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        teacher_name=params.teacher_name,
        teacher_type=params.teacher_type,
        painter_trait=params.painter_trait,
        helper_trait=params.helper_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed for seed {s}")
            break

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
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
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (project, stripe, answer, repair, apology) combos:\n")
        for project, stripe, answer, repair, apology in combos:
            print(f"  {project:8} {stripe:5} {answer:6} {repair:6} {apology}")
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
            header = f"### {p.painter} & {p.helper}: {p.project}, {p.apology}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
