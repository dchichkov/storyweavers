#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/course_nurture_reconciliation_curiosity_folk_tale.py
================================================================================

A standalone story world in a gentle folk-tale mode: two children are trusted to
guide water along its proper course and nurture a small growing patch. Curiosity
pulls one child toward a glittering distraction, the water is diverted, the
plants droop, feelings are hurt, and the children must reconcile while they put
the water right again.

The world model is classical and state-driven:
- typed entities carry physical meters and emotional memes
- forward-chaining rules turn low water into wilting and apology + shared work
  into reconciliation
- a reasonableness gate only allows waterways that can honestly nurture the
  chosen plants, and refuses weak repairs
- an inline ASP twin checks parity with the Python gate and outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/course_nurture_reconciliation_curiosity_folk_tale.py
    python storyworlds/worlds/gpt-5.4/course_nurture_reconciliation_curiosity_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/course_nurture_reconciliation_curiosity_folk_tale.py --qa --seed 7
    python storyworlds/worlds/gpt-5.4/course_nurture_reconciliation_curiosity_folk_tale.py --trace
    python storyworlds/worlds/gpt-5.4/course_nurture_reconciliation_curiosity_folk_tale.py --verify
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
CURIOUS_PULL = 5.0
PATIENT_TRAITS = {"patient", "steady", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
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
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
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
    scene: str
    home: str
    elder_title: str
    ending_image: str
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
class Waterway:
    id: str
    label: str
    course_phrase: str
    sound: str
    flow: int
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
class Plant:
    id: str
    label: str
    patch: str
    tender_word: str
    thirst: int
    resilience: int
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
class Lure:
    id: str
    label: str
    glint: str
    chase: str
    diversion: int
    safe_alt: str
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
    power: int
    text: str
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

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"curious", "companion"}]

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


def _r_wilt(world: World) -> list[str]:
    patch = world.get("patch")
    severity = int(patch.meters["water_loss"])
    if patch.meters["water"] >= THRESHOLD:
        return []
    sig = ("wilt", severity)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patch.meters["wilt"] += 1
    patch.meters["wilt_severity"] = float(severity)
    for child in world.children():
        child.memes["worry"] += 1
    world.get("companion").memes["hurt"] += 1
    return ["__wilt__"]


def _r_recover(world: World) -> list[str]:
    patch = world.get("patch")
    if patch.meters["water"] < THRESHOLD or patch.meters["wilt"] < THRESHOLD:
        return []
    stress = int(patch.meters["water_loss"])
    plant_cfg = world.facts["plant_cfg"]
    if fix_success(plant_cfg, stress, int(world.facts["fix"].power)):
        sig = ("recover", stress)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        patch.meters["revived"] += 1
        for child in world.children():
            child.memes["relief"] += 1
        return ["__recover__"]
    return []


def _r_reconcile(world: World) -> list[str]:
    curious = world.get("curious")
    companion = world.get("companion")
    if curious.memes["apology"] < THRESHOLD or curious.memes["shared_work"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    curious.memes["peace"] += 1
    companion.memes["peace"] += 1
    curious.memes["guilt"] = 0.0
    companion.memes["hurt"] = 0.0
    companion.memes["trust"] += 1
    return ["__reconcile__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wilt", tag="physical", apply=_r_wilt),
    Rule(name="recover", tag="physical", apply=_r_recover),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


def can_nurture(waterway: Waterway, plant: Plant) -> bool:
    return waterway.flow >= plant.thirst


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def stress_of(lure: Lure, delay: int) -> int:
    return lure.diversion + delay


def fix_success(plant: Plant, stress: int, power: int) -> bool:
    return power + plant.resilience >= stress + 2


def would_avert(relation: str, curious_age: int, companion_age: int, trait: str) -> bool:
    patient = trait in PATIENT_TRAITS
    companion_older = relation == "siblings" and companion_age > curious_age
    authority = (5.0 if patient else 3.0) + (3.0 if companion_older else 0.0)
    return companion_older and authority > CURIOUS_PULL


def predict_wilt(world: World, lure: Lure, delay: int) -> dict:
    sim = world.copy()
    patch = sim.get("patch")
    patch.meters["water"] = 0.0
    patch.meters["water_loss"] = float(stress_of(lure, delay))
    propagate(sim, narrate=False)
    return {
        "wilts": patch.meters["wilt"] >= THRESHOLD,
        "stress": int(patch.meters["water_loss"]),
    }


def introduce(world: World, curious: Entity, companion: Entity, elder: Entity,
              waterway: Waterway, plant: Plant) -> None:
    world.say(
        f"In {world.setting.scene}, where {waterway.sound}, "
        f"{elder.label_word} trusted {curious.id} and {companion.id} with a small and hopeful task."
    )
    world.say(
        f"They were to guide the water along its proper course to {plant.patch} and "
        f"nurture the young {plant.label} there until the soil drank deeply."
    )


def show_patch(world: World, plant: Plant, companion: Entity) -> None:
    companion.memes["care"] += 1
    world.say(
        f"The {plant.patch} was full of {plant.tender_word} green, and {companion.id} bent low to touch the leaves "
        f"as gently as if greeting birds."
    )


def tempt(world: World, curious: Entity, lure: Lure, waterway: Waterway) -> None:
    curious.memes["curiosity"] += 1
    world.say(
        f"Then {lure.glint} beside the little channel. "
        f'{curious.id} stopped and whispered, "Look! {lure.label}!"'
    )
    world.say(
        f"The sight tugged at {curious.pronoun('possessive')} curiosity so strongly that the murmuring {waterway.label} "
        f"seemed to be telling a secret."
    )


def warn(world: World, companion: Entity, curious: Entity, elder: Entity,
         lure: Lure, delay: int) -> None:
    pred = predict_wilt(world, lure, delay)
    world.facts["predicted_wilt"] = pred["wilts"]
    world.facts["predicted_stress"] = pred["stress"]
    companion.memes["caution"] += 1
    extra = ""
    if companion.memes["trust"] < 4:
        extra = f" {companion.id} had seen {curious.id} chase bright wonders before, and {companion.pronoun()} worried all the more."
    world.say(
        f'{companion.id} caught {curious.id}\'s sleeve. "If the water leaves the patch, the {world.facts["plant_cfg"].label} will droop," '
        f'{companion.pronoun()} said. "{elder.label_word.capitalize()} asked us to keep the water true."{extra}'
    )


def back_down(world: World, curious: Entity, companion: Entity, lure: Lure) -> None:
    curious.memes["relief"] += 1
    curious.memes["respect"] += 1
    companion.memes["relief"] += 1
    curious.memes["apology"] += 1
    curious.memes["shared_work"] += 1
    world.say(
        f"{curious.id} stood still, listened to the channel's soft hush, and let curiosity settle."
    )
    world.say(
        f'"You are right," {curious.pronoun()} said. "I wanted to follow {lure.label}, but I will not steal the water from the roots."'
    )
    propagate(world, narrate=False)


def divert(world: World, curious: Entity, lure: Lure, waterway: Waterway, delay: int) -> None:
    patch = world.get("patch")
    patch.meters["water"] = 0.0
    patch.meters["water_loss"] = float(stress_of(lure, delay))
    curious.memes["defiance"] += 1
    curious.memes["guilt"] += 1
    world.say(
        f"But curiosity ran ahead of obedience. {curious.id} nudged a row of pebbles aside and bent the {waterway.label} "
        f"toward {lure.chase}."
    )
    world.say(
        f"For a few delighted breaths, the water slipped after the wonder instead of hurrying to the roots."
    )
    propagate(world, narrate=False)


def notice_wilt(world: World, companion: Entity, plant: Plant) -> None:
    patch = world.get("patch")
    if patch.meters["wilt"] >= THRESHOLD:
        world.say(
            f"Soon the {plant.label} lifted no cheerful heads. Their leaves hung like little hands asking for a drink."
        )
    world.say(
        f'{companion.id} looked at the patch and then at {curious_name(world)}. "Now they are thirsty," {companion.pronoun()} said, and the words came out hurt.'
    )


def quarrel(world: World, curious: Entity, companion: Entity) -> None:
    curious.memes["shame"] += 1
    companion.memes["anger"] += 1
    world.say(
        f"{curious.id} opened {curious.pronoun('possessive')} mouth to speak, but no brave answer came."
    )
    world.say(
        f"For one sad moment, the two children stood apart, with dry soil between them and sore feelings on both sides."
    )


def elder_enters(world: World, elder: Entity) -> None:
    world.say(
        f"Just then, {elder.label_word} came from {world.setting.home}, carrying a willow basket and seeing more than either child wished to tell."
    )


def mend_and_fix(world: World, elder: Entity, curious: Entity, companion: Entity,
                 plant: Plant, fix: Fix) -> None:
    patch = world.get("patch")
    curious.memes["apology"] += 1
    curious.memes["shared_work"] += 1
    companion.memes["shared_work"] += 1
    world.say(
        f'{elder.label_word.capitalize()} did not scold at once. "{companion.id}, tell your hurt. {curious.id}, tell your truth," '
        f'{elder.pronoun()} said.'
    )
    world.say(
        f'{companion.id} said, "I was afraid for the {plant.label}, and I was angry because you would not listen." '
        f'{curious.id} bowed {curious.pronoun("possessive")} head. "I am sorry. I followed the wonder and forgot the roots."'
    )
    body = fix.text.replace("{patch}", plant.patch)
    world.say(
        f"Then all three knelt down together and {body}."
    )
    patch.meters["water"] = 1.0
    world.facts["repair_done"] = True
    propagate(world, narrate=False)


def full_ending(world: World, curious: Entity, companion: Entity, plant: Plant, lure: Lure) -> None:
    world.say(
        f"Water found its old course again, and before long the {plant.label} lifted themselves as if waking from a bad dream."
    )
    world.say(
        f"{curious.id} and {companion.id} worked shoulder to shoulder, and the hurt between them loosened like a knot in wet string."
    )
    world.say(
        f"After that, when {lure.safe_alt}, they looked first, asked first, and kept the roots watered all the while."
    )
    world.say(world.setting.ending_image)


def partial_ending(world: World, curious: Entity, companion: Entity, plant: Plant, lure: Lure) -> None:
    patch = world.get("patch")
    patch.meters["tending_days"] = 3.0
    world.say(
        f"Water returned, yet some of the {plant.label} stayed bent and pale. They were not lost, but they would need patient nurture for several mornings."
    )
    world.say(
        f"So {curious.id} and {companion.id} came back at dawn with small cups, speaking kindly to one another as they watered each root."
    )
    world.say(
        f"By the third morning, the patch looked greener, and their friendship had grown green with it."
    )
    world.say(
        f"From then on, when {lure.safe_alt}, curiosity walked beside care instead of tugging it away."
    )
    world.say(world.setting.ending_image)


def curious_name(world: World) -> str:
    return world.get("curious").id


def tell(setting: Setting, waterway: Waterway, plant: Plant, lure: Lure, fix: Fix,
         curious_name_value: str = "Lina", curious_gender: str = "girl",
         companion_name: str = "Toma", companion_gender: str = "boy",
         companion_trait: str = "patient", elder_type: str = "grandmother",
         delay: int = 0, curious_age: int = 5, companion_age: int = 7,
         relation: str = "siblings", trust: int = 6) -> World:
    world = World(setting)
    curious = world.add(Entity(
        id=curious_name_value,
        kind="character",
        type=curious_gender,
        label=curious_name_value,
        role="curious",
        traits=["curious"],
        age=curious_age,
        attrs={"relation": relation},
    ))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_gender,
        label=companion_name,
        role="companion",
        traits=[companion_trait],
        age=companion_age,
        attrs={"relation": relation},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        traits=["wise"],
    ))
    patch = world.add(Entity(
        id="patch",
        type="patch",
        label=plant.patch,
        attrs={"plant": plant.id},
    ))
    channel = world.add(Entity(
        id="channel",
        type="waterway",
        label=waterway.label,
        attrs={"course_phrase": waterway.course_phrase},
    ))

    patch.meters["water"] = 1.0
    patch.meters["water_loss"] = 0.0
    patch.meters["wilt"] = 0.0
    patch.meters["revived"] = 0.0
    patch.meters["tending_days"] = 0.0
    curious.memes["curiosity"] = 0.0
    curious.memes["guilt"] = 0.0
    curious.memes["apology"] = 0.0
    curious.memes["shared_work"] = 0.0
    companion.memes["trust"] = float(trust)
    companion.memes["caution"] = 5.0 if companion_trait in PATIENT_TRAITS else 3.0
    companion.memes["hurt"] = 0.0
    world.facts["repair_done"] = False
    world.facts["relation"] = relation
    world.facts["delay"] = delay
    world.facts["plant_cfg"] = plant
    world.facts["waterway_cfg"] = waterway
    world.facts["lure"] = lure
    world.facts["fix"] = fix

    introduce(world, curious, companion, elder, waterway, plant)
    show_patch(world, plant, companion)

    world.para()
    tempt(world, curious, lure, waterway)
    warn(world, companion, curious, elder, lure, delay)

    averted = would_avert(relation, curious_age, companion_age, companion_trait)

    if averted:
        back_down(world, curious, companion, lure)
        world.para()
        full_ending(world, curious, companion, plant, lure)
        outcome = "averted"
    else:
        divert(world, curious, lure, waterway, delay)
        world.para()
        notice_wilt(world, companion, plant)
        quarrel(world, curious, companion)
        elder_enters(world, elder)
        world.para()
        mend_and_fix(world, elder, curious, companion, plant, fix)
        stress = stress_of(lure, delay)
        if fix_success(plant, stress, fix.power):
            full_ending(world, curious, companion, plant, lure)
            outcome = "restored"
        else:
            partial_ending(world, curious, companion, plant, lure)
            outcome = "tended"

    world.facts.update(
        setting=setting,
        waterway=waterway,
        plant=patch,
        elder=elder,
        curious=curious,
        companion=companion,
        outcome=outcome,
        stress=stress_of(lure, delay),
        averted=averted,
        relation=relation,
        companion_trait=companion_trait,
    )
    return world


SETTINGS = {
    "valley": Setting(
        id="valley",
        scene="a small green valley under blue hills",
        home="the stone cottage",
        elder_title="grandmother",
        ending_image="And in the evening light, the patch shone silver with water, while two children walked home with one peace between them.",
        tags={"village", "folk"}),
    "terrace": Setting(
        id="terrace",
        scene="a hillside of old terraces above the village roofs",
        home="the clay house",
        elder_title="grandfather",
        ending_image="And when the last sun touched the terraces, the shining channels looked like bright threads sewing the family back together.",
        tags={"hill", "folk"}),
    "orchard": Setting(
        id="orchard",
        scene="an orchard where pears nodded over narrow ditches",
        home="the orchard gate",
        elder_title="grandmother",
        ending_image="By sunset the orchard was quiet again, and the children's laughter moved with the water instead of against it.",
        tags={"orchard", "folk"}),
}

WATERWAYS = {
    "brook": Waterway(
        id="brook",
        label="brook",
        course_phrase="its stony course",
        sound="a brook talked over stones",
        flow=3,
        tags={"water", "brook", "course"}),
    "runnel": Waterway(
        id="runnel",
        label="runnel",
        course_phrase="its narrow course",
        sound="a runnel whispered along the earth",
        flow=2,
        tags={"water", "runnel", "course"}),
    "springlet": Waterway(
        id="springlet",
        label="springlet",
        course_phrase="its bright course",
        sound="a springlet sang out of the hill",
        flow=1,
        tags={"water", "spring", "course"}),
}

PLANTS = {
    "beans": Plant(
        id="beans",
        label="bean vines",
        patch="the bean patch",
        tender_word="tender",
        thirst=1,
        resilience=2,
        tags={"beans", "plants", "nurture"}),
    "rice": Plant(
        id="rice",
        label="rice shoots",
        patch="the rice bed",
        tender_word="slender",
        thirst=3,
        resilience=3,
        tags={"rice", "plants", "nurture"}),
    "mint": Plant(
        id="mint",
        label="mint stems",
        patch="the herb bed",
        tender_word="small",
        thirst=2,
        resilience=2,
        tags={"mint", "plants", "nurture"}),
    "pumpkins": Plant(
        id="pumpkins",
        label="pumpkin seedlings",
        patch="the pumpkin mound",
        tender_word="round-leafed",
        thirst=2,
        resilience=1,
        tags={"pumpkin", "plants", "nurture"}),
}

LURES = {
    "fish": Lure(
        id="fish",
        label="a silver fish-tail flashing in the side pool",
        glint="a silver fish-tail flashed",
        chase="the side pool where the fish had darted",
        diversion=1,
        safe_alt="they glimpsed fish in the shallows",
        tags={"fish", "curiosity"}),
    "beetle": Lure(
        id="beetle",
        label="a green beetle bright as a jewel",
        glint="a green beetle bright as a jewel trembled on a reed",
        chase="the reed-bed to see where the beetle would go",
        diversion=1,
        safe_alt="a jeweled beetle landed nearby",
        tags={"beetle", "curiosity"}),
    "shell": Lure(
        id="shell",
        label="a shell with a moon-pale shine",
        glint="a shell with a moon-pale shine winked from the silt",
        chase="the bend where the pale shell lay half-buried",
        diversion=2,
        safe_alt="something shiny glimmered in the mud",
        tags={"shell", "curiosity"}),
}

FIXES = {
    "lift_stones": Fix(
        id="lift_stones",
        sense=3,
        power=3,
        text="lifted the pebbles back into place, opened the little mouth of {patch}, and patted the banks firm",
        qa_text="lifted the pebbles back and opened the channel to the patch again",
        tags={"repair", "water"}),
    "dig_channel": Fix(
        id="dig_channel",
        sense=3,
        power=2,
        text="used a small hoe to draw a clean line of water back to {patch} and broke the crusted soil so it could drink",
        qa_text="dug a clean little channel and guided the water back to the roots",
        tags={"repair", "channel"}),
    "scoop_water": Fix(
        id="scoop_water",
        sense=2,
        power=1,
        text="filled cups at the stream and carried water by hand to {patch} while they straightened the bank",
        qa_text="carried water by hand in cups while they straightened the bank",
        tags={"repair", "cups"}),
    "sing_to_plants": Fix(
        id="sing_to_plants",
        sense=1,
        power=0,
        text="sang to the leaves and hoped the song alone would help",
        qa_text="sang to the leaves and hoped for the best",
        tags={"song"}),
}

GIRL_NAMES = ["Lina", "Mira", "Anya", "Sela", "Niva", "Tali", "Rina", "Mara"]
BOY_NAMES = ["Toma", "Ivo", "Niko", "Pavel", "Luka", "Milan", "Sorin", "Darin"]
TRAITS = ["patient", "steady", "gentle", "watchful", "calm", "quiet"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_fixes():
        return combos
    for setting_id in SETTINGS:
        for waterway_id, waterway in WATERWAYS.items():
            for plant_id, plant in PLANTS.items():
                if can_nurture(waterway, plant):
                    combos.append((setting_id, waterway_id, plant_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    waterway: str
    plant: str
    lure: str
    fix: str
    curious_name: str
    curious_gender: str
    companion_name: str
    companion_gender: str
    elder: str
    companion_trait: str
    delay: int = 0
    curious_age: int = 5
    companion_age: int = 7
    relation: str = "siblings"
    trust: int = 6
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
    "course": [(
        "What is the course of a stream?",
        "The course of a stream is the path the water follows along the ground. If something blocks or bends that path, the water goes somewhere else."
    )],
    "nurture": [(
        "What does nurture mean?",
        "To nurture something is to care for it as it grows. You give it what it needs, like water, time, and gentle attention."
    )],
    "water": [(
        "Why do plants need water?",
        "Plants need water to stay alive and keep their leaves firm. Without enough water, they can droop and wilt."
    )],
    "repair": [(
        "How can people guide water to plants?",
        "People can clear a little channel, move stones, or open a small path in the soil so water can reach the roots. The water follows the shape of the ground."
    )],
    "cups": [(
        "Can carrying water in cups help a thirsty plant?",
        "Yes, it can help for a little while. But it is slower than opening the proper channel, so the roots may still need more care afterward."
    )],
    "channel": [(
        "What is a water channel?",
        "A water channel is a narrow path made to guide water where people want it to go. Gardens and fields often use channels to share water."
    )],
    "fish": [(
        "Why do shiny things make people curious?",
        "Shiny or quick-moving things catch our eyes and make us want to look closer. Curiosity can be good, but we still have to remember our job."
    )],
    "beetle": [(
        "What is a beetle?",
        "A beetle is a small insect with a hard shell on its back. Some beetles shine in the light like little jewels."
    )],
    "shell": [(
        "Why might a shell gleam in water?",
        "A smooth shell can catch the light and reflect it brightly. That is why it can look special from far away."
    )],
    "plants": [(
        "What does it mean when a plant wilts?",
        "A wilted plant droops because it does not have enough water or strength. If help comes in time, it may stand up again."
    )],
    "reconciliation": [(
        "What is reconciliation?",
        "Reconciliation means making peace after people have been hurt or angry with each other. It often starts with telling the truth, listening, and trying to repair what went wrong."
    )],
}
KNOWLEDGE_ORDER = [
    "course",
    "nurture",
    "water",
    "repair",
    "cups",
    "channel",
    "fish",
    "beetle",
    "shell",
    "plants",
    "reconciliation",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    curious = f["curious"]
    companion = f["companion"]
    plant_cfg = f["plant_cfg"]
    lure = f["lure"]
    outcome = f["outcome"]
    base = (
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "course" and "nurture". '
        f'Two children must guide water to {plant_cfg.patch}, and curiosity about {lure.label} causes trouble.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle folk tale where {curious.id} wants to follow {lure.label}, but listens to {companion.id} and keeps the water on its course.",
            'Write a child-facing story about curiosity, care, and reconciliation, where no lasting harm happens because one child stops and listens in time.',
        ]
    if outcome == "restored":
        return [
            base,
            f"Tell a folk-tale style story where {curious.id} diverts the water, the plants droop, and the children reconcile while putting the channel right again.",
            'Write a simple tale where curiosity pulls water away from young plants, but apology, shared work, and wise guidance restore both the garden and the friendship.',
        ]
    return [
        base,
        f"Tell a folk tale where {curious.id}'s curiosity bends the water away, and even after the repair the children must keep nurturing the patch for days.",
        'Write a tender cautionary tale where reconciliation happens quickly, but the living things still need patient care after a mistake.',
    ]


def pair_noun(curious: Entity, companion: Entity, relation: str) -> str:
    if relation == "siblings":
        if curious.type == "boy" and companion.type == "boy":
            return "two brothers"
        if curious.type == "girl" and companion.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    curious = f["curious"]
    companion = f["companion"]
    elder = f["elder"]
    plant_cfg = f["plant_cfg"]
    waterway = f["waterway_cfg"]
    lure = f["lure"]
    fix = f["fix"]
    outcome = f["outcome"]
    pair = pair_noun(curious, companion, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {curious.id} and {companion.id}, and their {elder.label_word} who helps them make things right."
        ),
        (
            "What were the children asked to do?",
            f"They were asked to guide the water along its proper course to {plant_cfg.patch} and nurture the young {plant_cfg.label}. That task is what made the mistake matter."
        ),
        (
            f"What made {curious.id} lose focus?",
            f"{lure.label.capitalize()} caught {curious.pronoun('possessive')} eye and pulled hard on {curious.pronoun('possessive')} curiosity. {curious.id} wanted to follow the wonder instead of keeping watch over the water."
        ),
        (
            f"Why did {companion.id} warn {curious.id}?",
            f"{companion.id} knew the roots needed water and feared the patch would wilt if the stream left its course. The warning came from care for the plants and from wanting to keep the promise they had been given."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"What happened after {companion.id} warned {curious.id}?",
            f"{curious.id} listened, stopped, and let the water keep flowing to {plant_cfg.patch}. Because the choice changed in time, the {plant_cfg.label} stayed healthy and the children felt relieved."
        ))
        qa.append((
            "How did the story show reconciliation?",
            f"The children made peace by speaking honestly and working together again at once. Even though they disagreed for a moment, they ended on the same side of the task."
        ))
    else:
        qa.append((
            "What happened to the plants when the water was diverted?",
            f"The {plant_cfg.label} drooped because the water no longer reached their roots. The patch became thirsty, which is why the quarrel felt serious instead of small."
        ))
        qa.append((
            f"How did the elder help the children reconcile?",
            f"The {elder.label_word} asked each child to tell the truth about hurt and mistake before helping them fix the channel. That made the apology real and turned the repair into something they did together."
        ))
        qa.append((
            f"How did they try to save {plant_cfg.patch}?",
            f"They {fix.qa_text}. The repair gave the roots water again and showed that caring work can follow a wrong choice."
        ))
        if outcome == "restored":
            qa.append((
                "How did the story end?",
                f"It ended with the {plant_cfg.label} lifting again and the children at peace. The garden recovered because help came in time and the children worked together after reconciling."
            ))
        else:
            qa.append((
                "How did the story end?",
                f"It ended gently but not all at once: the water returned, yet some plants still needed several mornings of nurture. The friendship healed quickly, but the living patch taught them that some mistakes take time to mend."
            ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"course", "nurture", "water", "plants", "reconciliation"}
    tags |= set(f["waterway_cfg"].tags)
    tags |= set(f["plant_cfg"].tags)
    tags |= set(f["lure"].tags)
    if f["outcome"] != "averted":
        tags |= set(f["fix"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="valley",
        waterway="brook",
        plant="rice",
        lure="fish",
        fix="lift_stones",
        curious_name="Lina",
        curious_gender="girl",
        companion_name="Toma",
        companion_gender="boy",
        elder="grandmother",
        companion_trait="patient",
        delay=0,
        curious_age=5,
        companion_age=7,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        setting="terrace",
        waterway="runnel",
        plant="mint",
        lure="shell",
        fix="dig_channel",
        curious_name="Ivo",
        curious_gender="boy",
        companion_name="Mira",
        companion_gender="girl",
        elder="grandfather",
        companion_trait="watchful",
        delay=0,
        curious_age=6,
        companion_age=6,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        setting="orchard",
        waterway="runnel",
        plant="pumpkins",
        lure="shell",
        fix="scoop_water",
        curious_name="Mara",
        curious_gender="girl",
        companion_name="Niko",
        companion_gender="boy",
        elder="grandmother",
        companion_trait="steady",
        delay=1,
        curious_age=6,
        companion_age=7,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        setting="valley",
        waterway="springlet",
        plant="beans",
        lure="beetle",
        fix="lift_stones",
        curious_name="Sorin",
        curious_gender="boy",
        companion_name="Pavel",
        companion_gender="boy",
        elder="grandfather",
        companion_trait="gentle",
        delay=0,
        curious_age=4,
        companion_age=7,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        setting="terrace",
        waterway="brook",
        plant="rice",
        lure="shell",
        fix="scoop_water",
        curious_name="Anya",
        curious_gender="girl",
        companion_name="Rina",
        companion_gender="girl",
        elder="grandmother",
        companion_trait="calm",
        delay=2,
        curious_age=7,
        companion_age=7,
        relation="friends",
        trust=3,
    ),
]


def explain_combo(waterway: Waterway, plant: Plant) -> str:
    return (
        f"(No story: the {waterway.label} is too slight to nurture {plant.patch}. "
        f"{plant.label.capitalize()} need more water than that stream can honestly carry.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of the sturdier repairs: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.curious_age, params.companion_age, params.companion_trait):
        return "averted"
    stress = stress_of(LURES[params.lure], params.delay)
    return "restored" if fix_success(PLANTS[params.plant], stress, FIXES[params.fix].power) else "tended"


ASP_RULES = r"""
can_nurture(W,P) :- flow(W,F), thirst(P,T), F >= T.
sensible_fix(Fx) :- fix(Fx), sense(Fx,S), sense_min(M), S >= M.
valid(S,W,P) :- setting(S), waterway(W), plant(P), can_nurture(W,P).

patient_trait(T) :- trait_name(T), patient(T).
init_caution(5) :- trait_name(T), patient_trait(T).
init_caution(3) :- trait_name(T), not patient_trait(T).
older_bonus(3) :- relation(siblings), companion_age(CA), curious_age(QA), CA > QA.
older_bonus(0) :- not relation(siblings).
older_bonus(0) :- relation(siblings), companion_age(CA), curious_age(QA), CA <= QA.
authority(C + B) :- init_caution(C), older_bonus(B).
averted :- relation(siblings), companion_age(CA), curious_age(QA), CA > QA, authority(A), curious_pull(P), A > P.

stress(Dv + Dl) :- chosen_lure(L), diversion(L,Dv), delay(Dl).
restored :- chosen_plant(P), chosen_fix(Fx), resilience(P,R), power(Fx,Pw), stress(S), Pw + R >= S + 2.

outcome(averted) :- averted.
outcome(restored) :- not averted, restored.
outcome(tended) :- not averted, not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid, waterway in WATERWAYS.items():
        lines.append(asp.fact("waterway", wid))
        lines.append(asp.fact("flow", wid, waterway.flow))
    for pid, plant in PLANTS.items():
        lines.append(asp.fact("plant", pid))
        lines.append(asp.fact("thirst", pid, plant.thirst))
        lines.append(asp.fact("resilience", pid, plant.resilience))
    for lid, lure in LURES.items():
        lines.append(asp.fact("lure", lid))
        lines.append(asp.fact("diversion", lid, lure.diversion))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("patient", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curious_pull", int(CURIOUS_PULL)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(fx for (fx,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_lure", params.lure),
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_plant", params.plant),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("curious_age", params.curious_age),
        asp.fact("companion_age", params.companion_age),
        asp.fact("trait_name", params.companion_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    c_fix = set(asp_sensible_fixes())
    p_fix = {f.id for f in sensible_fixes()}
    if c_fix == p_fix:
        print(f"OK: sensible fixes match ({sorted(c_fix)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_fix)} python={sorted(p_fix)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child bends water from its course, a patch thirsts, and reconciliation grows through repair."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--waterway", choices=WATERWAYS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--lure", choices=LURES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the patch goes without water")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.waterway and args.plant:
        waterway = WATERWAYS[args.waterway]
        plant = PLANTS[args.plant]
        if not can_nurture(waterway, plant):
            raise StoryError(explain_combo(waterway, plant))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.waterway is None or combo[1] == args.waterway)
        and (args.plant is None or combo[2] == args.plant)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, waterway_id, plant_id = rng.choice(sorted(combos))
    lure_id = args.lure or rng.choice(sorted(LURES))
    fix_id = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    curious_name_value, curious_gender = _pick_child(rng)
    companion_name, companion_gender = _pick_child(rng, avoid=curious_name_value)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    companion_trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    curious_age, companion_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(2, 8)

    return StoryParams(
        setting=setting_id,
        waterway=waterway_id,
        plant=plant_id,
        lure=lure_id,
        fix=fix_id,
        curious_name=curious_name_value,
        curious_gender=curious_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        elder=elder_type,
        companion_trait=companion_trait,
        delay=delay,
        curious_age=curious_age,
        companion_age=companion_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.waterway not in WATERWAYS:
        raise StoryError(f"(Unknown waterway: {params.waterway})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.lure not in LURES:
        raise StoryError(f"(Unknown lure: {params.lure})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))
    if not can_nurture(WATERWAYS[params.waterway], PLANTS[params.plant]):
        raise StoryError(explain_combo(WATERWAYS[params.waterway], PLANTS[params.plant]))

    world = tell(
        setting=SETTINGS[params.setting],
        waterway=WATERWAYS[params.waterway],
        plant=PLANTS[params.plant],
        lure=LURES[params.lure],
        fix=FIXES[params.fix],
        curious_name_value=params.curious_name,
        curious_gender=params.curious_gender,
        companion_name=params.companion_name,
        companion_gender=params.companion_gender,
        companion_trait=params.companion_trait,
        elder_type=params.elder,
        delay=params.delay,
        curious_age=params.curious_age,
        companion_age=params.companion_age,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        fixes = asp_sensible_fixes()
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(fixes)}\n")
        print(f"{len(combos)} compatible (setting, waterway, plant) combos:\n")
        for setting_id, waterway_id, plant_id in combos:
            print(f"  {setting_id:9} {waterway_id:10} {plant_id}")
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
            header = (
                f"### {p.curious_name} & {p.companion_name}: {p.waterway} to {p.plant} "
                f"({p.setting}, {p.lure}, {p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
