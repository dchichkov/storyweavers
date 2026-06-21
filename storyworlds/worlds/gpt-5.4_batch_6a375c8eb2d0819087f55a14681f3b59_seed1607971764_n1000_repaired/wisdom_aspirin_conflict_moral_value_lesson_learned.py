#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wisdom_aspirin_conflict_moral_value_lesson_learned.py
=================================================================================

A standalone story world for a gentle animal tale about **wisdom, conflict, and
learning not to grab medicine alone**.

This world rebuilds a small family-safe pattern:

- two young animals are together
- one hurts and becomes cross
- the other sees an aspirin tin and wants to fix everything quickly
- a wise grown-up teaches that real wisdom means asking for help
- the right care is given for the actual problem
- the friends repair the hurt between them and end with a changed habit

The model refuses unreasonable combinations. A cause must match the ailment, and
the grown-up's care must genuinely fit that ailment. The aspirin tin is part of
the conflict and lesson, not a child solution.

Run it
------
    python storyworlds/worlds/gpt-5.4/wisdom_aspirin_conflict_moral_value_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/wisdom_aspirin_conflict_moral_value_lesson_learned.py --cause drum_circle --ailment headache --care cool_cloth
    python storyworlds/worlds/gpt-5.4/wisdom_aspirin_conflict_moral_value_lesson_learned.py --cause thorn_prick --ailment tummyache
    python storyworlds/worlds/gpt-5.4/wisdom_aspirin_conflict_moral_value_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/wisdom_aspirin_conflict_moral_value_lesson_learned.py --qa --json
    python storyworlds/worlds/gpt-5.4/wisdom_aspirin_conflict_moral_value_lesson_learned.py --verify
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
CAUTIOUS_TRAITS = {"careful", "patient", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    species: str = ""
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    medicine: bool = False
    # world axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Cause:
    id: str
    label: str
    scene: str
    verb: str
    leads_to: str
    sore_text: str
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
class Ailment:
    id: str
    label: str
    feeling: str
    snap_line: str
    body_place: str
    needs_quiet: bool = False
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
class Care:
    id: str
    label: str
    phrase: str
    soothes: set[str] = field(default_factory=set)
    action_text: str = ""
    ending_text: str = ""
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


def _r_pain_to_grumpiness(world: World) -> list[str]:
    out: list[str] = []
    patient = world.get("patient")
    if patient.meters["pain"] >= THRESHOLD and ("grumpy", patient.id) not in world.fired:
        world.fired.add(("grumpy", patient.id))
        patient.memes["irritability"] += 1
        out.append("__grumpy__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    patient = world.get("patient")
    if patient.memes["irritability"] >= THRESHOLD and hero.memes["invited_play"] >= THRESHOLD:
        sig = ("conflict", hero.id, patient.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["hurt"] += 1
            patient.memes["guilt_seed"] += 1
            out.append("__conflict__")
    return out


def _r_wrong_medicine_danger(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("attempted_medicine") and ("danger", "medicine") not in world.fired:
        world.fired.add(("danger", "medicine"))
        world.get("hero").memes["worry"] += 1
        world.get("patient").memes["worry"] += 1
        world.get("room").meters["danger"] += 1
        out.append("__danger__")
    return out


def _r_care_relieves(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("care_given") and ("relief", "patient") not in world.fired:
        world.fired.add(("relief", "patient"))
        patient = world.get("patient")
        patient.meters["pain"] = 0.0
        patient.memes["comfort"] += 1
        patient.memes["irritability"] = 0.0
        world.get("hero").memes["relief"] += 1
        world.get("room").meters["danger"] = 0.0
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="pain_to_grumpiness", tag="meme", apply=_r_pain_to_grumpiness),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="wrong_medicine_danger", tag="safety", apply=_r_wrong_medicine_danger),
    Rule(name="care_relieves", tag="physical", apply=_r_care_relieves),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def cause_matches(cause: Cause, ailment: Ailment) -> bool:
    return cause.leads_to == ailment.id


def care_matches(care: Care, ailment: Ailment) -> bool:
    return ailment.id in care.soothes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cause_id, cause in CAUSES.items():
        for ailment_id, ailment in AILMENTS.items():
            if not cause_matches(cause, ailment):
                continue
            for care_id, care in CARES.items():
                if care_matches(care, ailment):
                    combos.append((cause_id, ailment_id, care_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_back_down(relation: str, hero_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > hero_age
    return older and initial_caution(trait) + 1.0 > 5.0


def predict_medicine_grab(world: World) -> dict:
    sim = world.copy()
    sim.facts["attempted_medicine"] = True
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "hero_worry": sim.get("hero").memes["worry"],
    }


def introduce(world: World, hero: Entity, patient: Entity, place: str) -> None:
    world.say(
        f"In {place}, {hero.id} the young {hero.species} and {patient.id} the little "
        f"{patient.species} spent the morning together."
    )
    world.say(
        f"They had been building a game out of pebbles, leaves, and twigs, and the whole "
        f"path smelled sweet and green."
    )


def show_cause(world: World, patient: Entity, cause: Cause, ailment: Ailment) -> None:
    patient.meters["pain"] += 1
    world.facts["pain_started"] = True
    propagate(world, narrate=False)
    world.say(
        f"But after {cause.scene}, {patient.id} slowed down. {cause.sore_text}"
    )
    world.say(
        f"Soon {patient.pronoun().capitalize()} had {ailment.feeling} in {patient.pronoun('possessive')} "
        f"{ailment.body_place}."
    )


def invitation_and_snap(world: World, hero: Entity, patient: Entity, cause: Cause, ailment: Ailment) -> None:
    hero.memes["invited_play"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Come on," said {hero.id}. "Let us {cause.verb} again."'
    )
    if patient.memes["irritability"] >= THRESHOLD:
        patient.memes["snapped"] += 1
        world.say(
            f'But {patient.id} winced and snapped, "{ailment.snap_line}"'
        )
        if hero.memes["hurt"] >= THRESHOLD:
            world.say(
                f"The sharp answer pricked {hero.id}'s heart. For a moment, {hero.pronoun()} wondered "
                f"whether {patient.id} was being unkind."
            )


def temptation(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["helpfulness"] += 1
    tin = world.get("aspirin_tin")
    world.say(
        f"Then {hero.id} noticed {elder.id}'s {tin.label} shining on a high shelf."
    )
    world.say(
        f'"That aspirin tin might fix everything fast," {hero.pronoun()} whispered. '
        f'"If I bring it down, {patient_name(world)} can play again."'
    )


def patient_name(world: World) -> str:
    return world.get("patient").id


def warning(world: World, cautioner: Entity, hero: Entity, elder: Entity) -> None:
    pred = predict_medicine_grab(world)
    world.facts["predicted_danger"] = pred["danger"]
    cautioner.memes["caution"] += 1
    world.say(
        f'{cautioner.id} shook {cautioner.pronoun("possessive")} head. '
        f'"That is {elder.id}\'s aspirin tin," {cautioner.pronoun()} said. '
        f'"Wisdom is not grabbing medicine by yourself. We must ask a grown-up first."'
    )
    if pred["danger"] >= THRESHOLD:
        world.say(
            f"{cautioner.id} looked up at the shelf and imagined the tin slipping, rattling, "
            f"and making the whole room jump."
        )


def back_down(world: World, hero: Entity, cautioner: Entity, elder: Entity) -> None:
    hero.memes["restraint"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} reached one paw toward the shelf, then pulled it back."
    )
    world.say(
        f'"You are right," {hero.pronoun()} said. "Real wisdom asks {elder.id}." '
        f"Together, the two young animals went to find the grown-up instead of touching the aspirin."
    )


def attempt_and_interrupt(world: World, hero: Entity, elder: Entity) -> None:
    world.facts["attempted_medicine"] = True
    propagate(world, narrate=False)
    hero.memes["defiance"] += 1
    world.say(
        f"But hurry tugged at {hero.id}. {hero.pronoun().capitalize()} dragged over a little stool and "
        f"stretched up toward the aspirin tin."
    )
    world.say(
        f"Before {hero.pronoun()} could touch it, the stool wobbled and the tin gave a hard metallic rattle."
    )
    world.say(
        f"{elder.id} turned at once, hurried over, and lifted the tin safely away."
    )


def elder_lesson(world: World, elder: Entity, hero: Entity, patient: Entity) -> None:
    world.say(
        f'"Medicine is never for little paws to choose alone," said {elder.id} gently. '
        f'"A caring heart is good, but wisdom means asking before acting."'
    )
    if world.get("room").meters["danger"] >= THRESHOLD:
        world.say(
            f"{hero.id} lowered {hero.pronoun('possessive')} ears. The fast plan had almost made the trouble bigger."
        )


def examine_and_explain(world: World, elder: Entity, patient: Entity, cause: Cause, ailment: Ailment) -> None:
    patient.memes["truth"] += 1
    world.say(
        f"Then {elder.id} knelt beside {patient.id} and listened carefully."
    )
    world.say(
        f'"I was not trying to be mean," {patient.id} murmured. "After {cause.scene}, '
        f'my {ailment.body_place} hurt, and it made me cross."'
    )


def give_care(world: World, elder: Entity, patient: Entity, care: Care, ailment: Ailment) -> None:
    world.facts["care_given"] = True
    world.facts["care_used"] = care.id
    propagate(world, narrate=False)
    quiet = " The room grew still around them." if ailment.needs_quiet else ""
    world.say(
        f"{elder.id} {care.action_text}.{quiet}"
    )
    world.say(
        f"Little by little, the tight look left {patient.id}'s face."
    )


def apology_and_repair(world: World, hero: Entity, patient: Entity) -> None:
    hero.memes["kindness"] += 1
    patient.memes["kindness"] += 1
    hero.memes["hurt"] = 0.0
    patient.memes["guilt_seed"] = 0.0
    world.say(
        f'"I am sorry I thought a quick grab was the wise thing," said {hero.id}. '
        f'"I wanted to help, but I should have asked."'
    )
    world.say(
        f'"And I am sorry I snapped," said {patient.id}. "The pain was real, but I should have used gentle words."'
    )


def changed_ending(world: World, hero: Entity, patient: Entity, elder: Entity, care: Care) -> None:
    hero.memes["lesson"] += 1
    patient.memes["lesson"] += 1
    world.say(
        f"{care.ending_text}"
    )
    world.say(
        f"At the door, {hero.id} looked once more at the shelf where the aspirin tin rested far above."
    )
    world.say(
        f"This time {hero.pronoun()} only smiled and said, "
        f'"Now I know: wisdom means kind paws, patient hearts, and asking {elder.id} first."'
    )


def tell(
    cause: Cause,
    ailment: Ailment,
    care: Care,
    *,
    place: str,
    hero_name: str,
    hero_species: str,
    patient_name_value: str,
    patient_species: str,
    cautioner_name: str,
    cautioner_species: str,
    elder_name: str,
    elder_species: str,
    trait: str,
    relation: str,
    hero_age: int,
    cautioner_age: int,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="child",
            species=hero_species,
            role="hero",
            traits=["eager"],
            age=hero_age,
            attrs={"relation": relation},
        )
    )
    patient = world.add(
        Entity(
            id=patient_name_value,
            kind="character",
            type="child",
            species=patient_species,
            role="patient",
            traits=["sensitive"],
            age=max(3, hero_age),
            attrs={},
        )
    )
    cautioner = world.add(
        Entity(
            id=cautioner_name,
            kind="character",
            type="child",
            species=cautioner_species,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type="adult",
            species=elder_species,
            role="elder",
            traits=["wise"],
            age=12,
            attrs={},
        )
    )
    world.add(Entity(id="room", type="place", label="the room", attrs={}))
    world.add(
        Entity(
            id="aspirin_tin",
            type="thing",
            label="aspirin tin",
            portable=True,
            medicine=True,
            attrs={"owner": elder.id, "shelf": "high shelf"},
        )
    )

    hero.memes["helpfulness"] = 0.0
    hero.memes["invited_play"] = 0.0
    hero.memes["hurt"] = 0.0
    hero.memes["worry"] = 0.0
    patient.meters["pain"] = 0.0
    patient.memes["irritability"] = 0.0
    patient.memes["guilt_seed"] = 0.0
    cautioner.memes["caution"] = initial_caution(trait)
    world.facts["attempted_medicine"] = False
    world.facts["care_given"] = False
    world.facts["pain_started"] = False
    world.facts["care_used"] = ""
    world.facts["place"] = place

    introduce(world, hero, patient, place)
    show_cause(world, patient, cause, ailment)

    world.para()
    invitation_and_snap(world, hero, patient, cause, ailment)
    temptation(world, hero, elder)
    warning(world, cautioner, hero, elder)

    averted = would_back_down(relation, hero_age, cautioner_age, trait)
    world.facts["averted"] = averted

    world.para()
    if averted:
        back_down(world, hero, cautioner, elder)
    else:
        attempt_and_interrupt(world, hero, elder)
        elder_lesson(world, elder, hero, patient)

    examine_and_explain(world, elder, patient, cause, ailment)
    give_care(world, elder, patient, care, ailment)

    world.para()
    apology_and_repair(world, hero, patient)
    changed_ending(world, hero, patient, elder, care)

    world.facts.update(
        hero=hero,
        patient=patient,
        cautioner=cautioner,
        elder=elder,
        cause_cfg=cause,
        ailment_cfg=ailment,
        care_cfg=care,
        outcome="averted" if averted else "interrupted",
        relation=relation,
        hero_age=hero_age,
        cautioner_age=cautioner_age,
        lesson_learned=hero.memes["lesson"] >= THRESHOLD,
        conflict_happened=hero.memes["invited_play"] >= THRESHOLD and patient.memes["snapped"] >= THRESHOLD,
    )
    return world


CAUSES = {
    "drum_circle": Cause(
        id="drum_circle",
        label="drum circle",
        scene="a long, loud drum circle under the oak tree",
        verb="tap the pebbles like tiny drums",
        leads_to="headache",
        sore_text="The banging had been cheerful at first, but now every little thump sounded too big.",
        tags={"noise", "headache"},
    ),
    "too_many_plums": Cause(
        id="too_many_plums",
        label="too many plums",
        scene="eating too many sweet plums by the stream",
        verb="sort the shiny plum pits into piles",
        leads_to="tummyache",
        sore_text="The sweet snack had seemed wonderful, yet now the tummy-full feeling was heavy and twisty.",
        tags={"food", "tummy"},
    ),
    "thorn_prick": Cause(
        id="thorn_prick",
        label="thorn prick",
        scene="hurrying through a bramble arch",
        verb="finish the leaf bridge",
        leads_to="sore_paw",
        sore_text="One small thorn had found a tender paw, and every step came out slow.",
        tags={"briar", "paw"},
    ),
    "camp_smoke": Cause(
        id="camp_smoke",
        label="camp smoke",
        scene="standing too near a smoky cooking fire",
        verb="stack acorn cups for supper",
        leads_to="headache",
        sore_text="The smoke had curled in the air until even the sunlight felt blurry.",
        tags={"smoke", "headache"},
    ),
    "slippery_stone": Cause(
        id="slippery_stone",
        label="slippery stone",
        scene="slipping on a mossy stone near the brook",
        verb="launch bark boats again",
        leads_to="sore_paw",
        sore_text="Nothing was badly wrong, but one forepaw had landed with a sharp little sting.",
        tags={"brook", "paw"},
    ),
}

AILMENTS = {
    "headache": Ailment(
        id="headache",
        label="headache",
        feeling="a soft pounding ache",
        snap_line="Please do not make more noise right now.",
        body_place="head",
        needs_quiet=True,
        tags={"headache"},
    ),
    "tummyache": Ailment(
        id="tummyache",
        label="tummy ache",
        feeling="a twisty ache",
        snap_line="I do not want to play another game this minute.",
        body_place="tummy",
        needs_quiet=False,
        tags={"tummyache"},
    ),
    "sore_paw": Ailment(
        id="sore_paw",
        label="sore paw",
        feeling="a sharp little soreness",
        snap_line="I cannot race when my paw hurts.",
        body_place="paw",
        needs_quiet=False,
        tags={"paw"},
    ),
}

CARES = {
    "cool_cloth": Care(
        id="cool_cloth",
        label="cool cloth",
        phrase="a cool cloth",
        soothes={"headache"},
        action_text="laid a cool cloth across the aching brow and dimmed the lantern",
        ending_text="Soon the young animals were sitting on the step, whispering a new game soft as moss.",
        tags={"cool_cloth", "rest"},
    ),
    "quiet_nest": Care(
        id="quiet_nest",
        label="quiet nest",
        phrase="a quiet nest with a pillow of feathers",
        soothes={"headache"},
        action_text="tucked a feather pillow under the sore head and made a quiet nest by the window",
        ending_text="Later they watched leaves drift past the window and played a silent counting game together.",
        tags={"quiet", "rest"},
    ),
    "mint_tea": Care(
        id="mint_tea",
        label="mint tea",
        phrase="warm mint tea",
        soothes={"tummyache"},
        action_text="steeped warm mint tea and waited beside the chair until the sipping was slow and easy",
        ending_text="Before long they were sorting buttons instead of racing, and the gentle game felt just right.",
        tags={"tea", "tummy"},
    ),
    "warm_water": Care(
        id="warm_water",
        label="warm water",
        phrase="a cup of warm water and a rest on the bench",
        soothes={"tummyache"},
        action_text="brought a cup of warm water and let the little belly rest before any more running",
        ending_text="After a while the friends sat by the brook and skipped only ideas, not stones or snacks.",
        tags={"water", "tummy"},
    ),
    "bandage": Care(
        id="bandage",
        label="bandage",
        phrase="a neat little bandage",
        soothes={"sore_paw"},
        action_text="washed the sore paw, pulled out the tiny thorn, and wrapped it in a neat little bandage",
        ending_text="By sunset the pair were drawing hopscotch squares in the dust, careful and cheerful both.",
        tags={"bandage", "paw"},
    ),
    "rest_stool": Care(
        id="rest_stool",
        label="resting stool",
        phrase="a small stool and a cushion for resting",
        soothes={"sore_paw"},
        action_text="set a cushion on a low stool and asked for quiet resting until the sting faded",
        ending_text="Soon they turned their race into a sitting game of shell trading and smiling guesses.",
        tags={"rest", "paw"},
    ),
}

ANIMAL_NAMES = {
    "mouse": ["Mimi", "Pip", "Nibbles"],
    "rabbit": ["Bramble", "Tansy", "Moss"],
    "squirrel": ["Hazel", "Nutmeg", "Pico"],
    "duck": ["Dabble", "Reed", "Puddle"],
    "fox": ["Fern", "Rory", "Maple"],
    "hedgehog": ["Bram", "Thistle", "Poppy"],
}

PLACES = [
    "a little clearing by the elder tree",
    "the mossy room of the hill burrow",
    "a sunny kitchen nook near the brook",
    "the round front room of Owl Hollow",
]

TRAITS = ["careful", "patient", "thoughtful", "gentle", "quick", "bold", "busy"]


@dataclass
class StoryParams:
    cause: str
    ailment: str
    care: str
    place: str
    hero_name: str
    hero_species: str
    patient_name: str
    patient_species: str
    cautioner_name: str
    cautioner_species: str
    elder_name: str
    elder_species: str
    trait: str
    relation: str = "siblings"
    hero_age: int = 4
    cautioner_age: int = 6
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
    "aspirin": [
        (
            "What is aspirin?",
            "Aspirin is a kind of medicine. Medicine should only be given by a grown-up who knows what is safe."
        )
    ],
    "wisdom": [
        (
            "What does wisdom mean?",
            "Wisdom means using good sense and being patient before you act. Sometimes the wisest thing is to stop and ask for help."
        )
    ],
    "headache": [
        (
            "What is a headache?",
            "A headache is pain in your head. Quiet, rest, and help from a grown-up can matter when someone's head hurts."
        )
    ],
    "tummyache": [
        (
            "What is a tummy ache?",
            "A tummy ache is pain in your belly. Rest and gentle care can help while a grown-up decides what to do."
        )
    ],
    "paw": [
        (
            "Why should a sore paw be checked?",
            "A sore paw can hide a thorn or a little cut. Looking carefully helps the right fix happen."
        )
    ],
    "kind_words": [
        (
            "Why do kind words matter when someone hurts?",
            "Pain can make a friend sound cross, but kind words still matter. Speaking gently helps everyone understand the real problem."
        )
    ],
    "ask_adult": [
        (
            "What should a child do when medicine is on a shelf?",
            "Leave it there and ask a grown-up. Medicine is not for children to choose by themselves."
        )
    ],
    "cool_cloth": [
        (
            "Why can a cool cloth feel nice on a sore head?",
            "A cool cloth can feel calming and gentle on an aching forehead. It also reminds someone to slow down and rest."
        )
    ],
    "mint_tea": [
        (
            "Why does warm mint tea feel gentle?",
            "A warm drink can feel soothing when someone needs to sit still and settle down. A grown-up decides when it is the right choice."
        )
    ],
    "bandage": [
        (
            "What does a bandage do?",
            "A bandage helps protect a small hurt place while it rests. It can keep the sore spot cleaner and safer."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "aspirin",
    "wisdom",
    "headache",
    "tummyache",
    "paw",
    "kind_words",
    "ask_adult",
    "cool_cloth",
    "mint_tea",
    "bandage",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    patient = f["patient"]
    elder = f["elder"]
    cause = f["cause_cfg"]
    ailment = f["ailment_cfg"]
    care = f["care_cfg"]
    return [
        (
            f'Write a short animal story for a 3-to-5-year-old that includes the words '
            f'"wisdom" and "aspirin", with a conflict caused by pain and a gentle moral about asking a grown-up for help.'
        ),
        (
            f"Tell a story where {hero.id} the {hero.species} sees an aspirin tin and thinks "
            f"a quick fix will solve {patient.id}'s {ailment.label}, but {elder.id} teaches what real wisdom is."
        ),
        (
            f"Write a simple forest tale in which {cause.label} leads to a quarrel, "
            f"the right care is {care.phrase}, and the ending shows a lesson learned."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    patient = f["patient"]
    cautioner = f["cautioner"]
    elder = f["elder"]
    cause = f["cause_cfg"]
    ailment = f["ailment_cfg"]
    care = f["care_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.species}, {patient.id} the {patient.species}, "
            f"{cautioner.id} the {cautioner.species}, and {elder.id} the wise {elder.species}."
        ),
        (
            f"Why did {patient.id} sound cross?",
            f"{patient.id} sounded cross because after {cause.scene}, {patient.pronoun('possessive')} "
            f"{ailment.body_place} hurt. The pain made {patient.pronoun('object')} snappy, even though "
            f"{patient.pronoun()} was not trying to be mean."
        ),
        (
            f"Why did {hero.id} look at the aspirin tin?",
            f"{hero.id} wanted to help fast and thought the aspirin tin might solve the problem at once. "
            f"But the story shows that quick guessing is not the same as wisdom."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {cautioner.id} help {hero.id} do?",
                f"{cautioner.id} helped {hero.id} stop before touching the aspirin tin. "
                f"That mattered because medicine should be chosen by a grown-up, not by children in a hurry."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {hero.id} tried to reach the aspirin tin?",
                f"The stool wobbled and the tin rattled, and {elder.id} hurried over before anything worse happened. "
                f"The moment showed how a rushed plan could have made the trouble bigger."
            )
        )
    qa.extend(
        [
            (
                f"How did {elder.id} solve the real problem?",
                f"{elder.id} listened first, learned that the problem was {ailment.label}, and then used {care.phrase}. "
                f"The right care fit the hurt, so {patient.id} slowly felt better."
            ),
            (
                "What is the moral value in the story?",
                f"The story values kindness, patience, and responsibility. "
                f"It says caring hearts should slow down, use gentle words, and ask for help before touching medicine."
            ),
            (
                "What lesson did the friends learn?",
                f"They learned that wisdom is more than wanting to help quickly. "
                f"They also learned to speak kindly during pain and to let a grown-up choose medicine or care."
            ),
        ]
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"aspirin", "wisdom", "kind_words", "ask_adult"}
    ailment = f["ailment_cfg"].id
    if ailment == "headache":
        tags.add("headache")
    if ailment == "tummyache":
        tags.add("tummyache")
    if ailment == "sore_paw":
        tags.add("paw")
    care = f["care_cfg"].id
    if care == "cool_cloth":
        tags.add("cool_cloth")
    if care == "mint_tea":
        tags.add("mint_tea")
    if care == "bandage":
        tags.add("bandage")
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
        if e.species:
            bits.append(f"species={e.species}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cause="drum_circle",
        ailment="headache",
        care="cool_cloth",
        place="the round front room of Owl Hollow",
        hero_name="Pip",
        hero_species="mouse",
        patient_name="Hazel",
        patient_species="squirrel",
        cautioner_name="Bramble",
        cautioner_species="rabbit",
        elder_name="Oona",
        elder_species="owl",
        trait="patient",
        relation="siblings",
        hero_age=4,
        cautioner_age=7,
    ),
    StoryParams(
        cause="too_many_plums",
        ailment="tummyache",
        care="mint_tea",
        place="a sunny kitchen nook near the brook",
        hero_name="Fern",
        hero_species="fox",
        patient_name="Puddle",
        patient_species="duck",
        cautioner_name="Thistle",
        cautioner_species="hedgehog",
        elder_name="Moss",
        elder_species="rabbit",
        trait="gentle",
        relation="friends",
        hero_age=5,
        cautioner_age=5,
    ),
    StoryParams(
        cause="thorn_prick",
        ailment="sore_paw",
        care="bandage",
        place="the mossy room of the hill burrow",
        hero_name="Nutmeg",
        hero_species="squirrel",
        patient_name="Rory",
        patient_species="fox",
        cautioner_name="Mimi",
        cautioner_species="mouse",
        elder_name="Tansy",
        elder_species="rabbit",
        trait="careful",
        relation="siblings",
        hero_age=6,
        cautioner_age=4,
    ),
    StoryParams(
        cause="camp_smoke",
        ailment="headache",
        care="quiet_nest",
        place="a little clearing by the elder tree",
        hero_name="Poppy",
        hero_species="hedgehog",
        patient_name="Reed",
        patient_species="duck",
        cautioner_name="Maple",
        cautioner_species="fox",
        elder_name="Hazel",
        elder_species="squirrel",
        trait="thoughtful",
        relation="friends",
        hero_age=5,
        cautioner_age=6,
    ),
    StoryParams(
        cause="slippery_stone",
        ailment="sore_paw",
        care="rest_stool",
        place="the round front room of Owl Hollow",
        hero_name="Moss",
        hero_species="rabbit",
        patient_name="Pico",
        patient_species="squirrel",
        cautioner_name="Dabble",
        cautioner_species="duck",
        elder_name="Oona",
        elder_species="owl",
        trait="quick",
        relation="friends",
        hero_age=4,
        cautioner_age=4,
    ),
]


def explain_rejection(cause: Cause, ailment: Ailment, care: Optional[Care] = None) -> str:
    if not cause_matches(cause, ailment):
        return (
            f"(No story: {cause.label} would not honestly lead to {ailment.label}. "
            f"The conflict must begin from a plausible hurt.)"
        )
    if care is not None and not care_matches(care, ailment):
        return (
            f"(No story: {care.label} does not fit {ailment.label}. "
            f"The grown-up's care must actually match the problem.)"
        )
    return "(No story: this combination does not make a reasonable tale.)"


def validate_params(params: StoryParams) -> None:
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.ailment not in AILMENTS:
        raise StoryError(f"(Unknown ailment: {params.ailment})")
    if params.care not in CARES:
        raise StoryError(f"(Unknown care: {params.care})")
    cause = CAUSES[params.cause]
    ailment = AILMENTS[params.ailment]
    care = CARES[params.care]
    if not cause_matches(cause, ailment):
        raise StoryError(explain_rejection(cause, ailment))
    if not care_matches(care, ailment):
        raise StoryError(explain_rejection(cause, ailment, care))
    if params.hero_name in {params.patient_name, params.cautioner_name, params.elder_name}:
        raise StoryError("(No story: each character needs a different name.)")
    if params.patient_name in {params.cautioner_name, params.elder_name}:
        raise StoryError("(No story: each character needs a different name.)")
    if params.cautioner_name == params.elder_name:
        raise StoryError("(No story: each character needs a different name.)")


ASP_RULES = r"""
cause_matches(C,A) :- cause(C), ailment(A), leads_to(C,A).
care_matches(K,A)  :- care(K), ailment(A), soothes(K,A).
valid(C,A,K)       :- cause_matches(C,A), care_matches(K,A).

older_cautioner :- relation(siblings), cautioner_age(CA), hero_age(HA), CA > HA.
strong_trait    :- trait(T), cautious_trait(T).
back_down       :- older_cautioner, strong_trait.

outcome(averted)     :- back_down.
outcome(interrupted) :- not back_down.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("leads_to", cid, cause.leads_to))
    for aid in AILMENTS:
        lines.append(asp.fact("ailment", aid))
    for kid, care in CARES.items():
        lines.append(asp.fact("care", kid))
        for ailment in sorted(care.soothes):
            lines.append(asp.fact("soothes", kid, ailment))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_back_down(params.relation, params.hero_age, params.cautioner_age, params.trait) else "interrupted"


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for bad in mismatches[:5]:
            print(" ", bad)

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: conflict, wisdom, aspirin on the shelf, and a lesson learned."
    )
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--ailment", choices=AILMENTS)
    ap.add_argument("--care", choices=CARES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (cause, ailment, care) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_animal(rng: random.Random, avoid_species: set[str], avoid_names: set[str]) -> tuple[str, str]:
    species_options = [s for s in sorted(ANIMAL_NAMES) if s not in avoid_species] or sorted(ANIMAL_NAMES)
    species = rng.choice(species_options)
    name_pool = [n for n in ANIMAL_NAMES[species] if n not in avoid_names]
    if not name_pool:
        name_pool = list(ANIMAL_NAMES[species])
    return rng.choice(name_pool), species


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.ailment:
        if not cause_matches(CAUSES[args.cause], AILMENTS[args.ailment]):
            raise StoryError(explain_rejection(CAUSES[args.cause], AILMENTS[args.ailment]))
    if args.ailment and args.care:
        if not care_matches(CARES[args.care], AILMENTS[args.ailment]):
            cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
            raise StoryError(explain_rejection(cause, AILMENTS[args.ailment], CARES[args.care]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.cause is None or combo[0] == args.cause)
        and (args.ailment is None or combo[1] == args.ailment)
        and (args.care is None or combo[2] == args.care)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cause_id, ailment_id, care_id = rng.choice(sorted(combos))
    place = args.place or rng.choice(PLACES)
    relation = args.relation or rng.choice(["siblings", "friends"])
    trait = args.trait or rng.choice(TRAITS)

    hero_name, hero_species = pick_animal(rng, avoid_species=set(), avoid_names=set())
    patient_name, patient_species = pick_animal(rng, avoid_species={hero_species}, avoid_names={hero_name})
    cautioner_name, cautioner_species = pick_animal(
        rng, avoid_species={hero_species, patient_species}, avoid_names={hero_name, patient_name}
    )
    elder_name, elder_species = pick_animal(
        rng,
        avoid_species={hero_species, patient_species, cautioner_species},
        avoid_names={hero_name, patient_name, cautioner_name},
    )

    hero_age = rng.randint(4, 6)
    cautioner_age = rng.randint(4, 7)

    return StoryParams(
        cause=cause_id,
        ailment=ailment_id,
        care=care_id,
        place=place,
        hero_name=hero_name,
        hero_species=hero_species,
        patient_name=patient_name,
        patient_species=patient_species,
        cautioner_name=cautioner_name,
        cautioner_species=cautioner_species,
        elder_name=elder_name,
        elder_species=elder_species,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        cause=CAUSES[params.cause],
        ailment=AILMENTS[params.ailment],
        care=CARES[params.care],
        place=params.place,
        hero_name=params.hero_name,
        hero_species=params.hero_species,
        patient_name_value=params.patient_name,
        patient_species=params.patient_species,
        cautioner_name=params.cautioner_name,
        cautioner_species=params.cautioner_species,
        elder_name=params.elder_name,
        elder_species=params.elder_species,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        cautioner_age=params.cautioner_age,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cause, ailment, care) combos:\n")
        for cause, ailment, care in combos:
            print(f"  {cause:14} {ailment:10} {care}")
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
            header = f"### {p.hero_name} / {p.patient_name}: {p.cause} -> {p.ailment} -> {p.care} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
