#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/belt_intravenous_grunt_rhyme_surprise_mystery_to.py
==============================================================================

A standalone story world for a tiny fable-like clinic mystery:
a young animal helper hears a strange grunt, finds that the doctor's belt is
missing, follows small clues in rhyme, and discovers a surprising helper rather
than a thief. The missing belt matters because the doctor needs the pouch tied
to it to help a waiting patient, and in the hardest cases that help is an
intravenous drip.

This world models:
- physical state: weakness, waiting, belt missing/found, treatment given
- emotional state: worry, fear, relief, pride
- a reasonableness gate: each patient case only allows sensible treatments
- an inline ASP twin for parity with the Python gate and outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/belt_intravenous_grunt_rhyme_surprise_mystery_to.py
    python storyworlds/worlds/gpt-5.4/belt_intravenous_grunt_rhyme_surprise_mystery_to.py --case thirsty_fawn --treatment intravenous_drip
    python storyworlds/worlds/gpt-5.4/belt_intravenous_grunt_rhyme_surprise_mystery_to.py --case scraped_squirrel --treatment intravenous_drip
    python storyworlds/worlds/gpt-5.4/belt_intravenous_grunt_rhyme_surprise_mystery_to.py --all
    python storyworlds/worlds/gpt-5.4/belt_intravenous_grunt_rhyme_surprise_mystery_to.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"doe", "hen", "she"}
        male = {"boar", "bear", "buck", "he"}
        if self.attrs.get("gender") == "girl" or self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.attrs.get("gender") == "boy" or self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Hero:
    id: str
    species: str
    traits: list[str] = field(default_factory=list)
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
class PatientCase:
    id: str
    patient_name: str
    patient_species: str
    trouble: str
    sign: str
    severity: str
    allowed_treatments: set[str]
    opening: str
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
class Treatment:
    id: str
    label: str
    use_for: str
    action_text: str
    proof_text: str
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
class CulpritCase:
    id: str
    label: str
    species: str
    grunt_word: str
    place: str
    clue: str
    rhyme: str
    motive: str
    return_text: str
    delay: int
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


def _r_missing_belt_worry(world: World) -> list[str]:
    doctor = world.get("doctor")
    belt = world.get("belt")
    if belt.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry_missing", belt.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    doctor.memes["worry"] += 1
    return []


def _r_waiting_hurts(world: World) -> list[str]:
    patient = world.get("patient")
    if patient.meters["waiting"] < THRESHOLD or patient.meters["treated"] >= THRESHOLD:
        return []
    sig = ("waiting_hurts", patient.id, int(patient.meters["waiting"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts["case"].severity == "severe":
        patient.meters["weakness"] += 1
        patient.memes["fear"] += 1
    else:
        patient.memes["worry"] += 1
    return []


def _r_found_belt_relief(world: World) -> list[str]:
    belt = world.get("belt")
    if belt.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", belt.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("doctor").memes["worry"] = 0.0
    world.get("doctor").memes["relief"] += 1
    world.get("hero").memes["pride"] += 1
    return []


def _r_treatment_helps(world: World) -> list[str]:
    patient = world.get("patient")
    if patient.meters["treated"] < THRESHOLD:
        return []
    sig = ("helped", patient.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patient.meters["weakness"] = max(0.0, patient.meters["weakness"] - 2.0)
    patient.memes["fear"] = 0.0
    patient.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_belt_worry", tag="social", apply=_r_missing_belt_worry),
    Rule(name="waiting_hurts", tag="physical", apply=_r_waiting_hurts),
    Rule(name="found_belt_relief", tag="social", apply=_r_found_belt_relief),
    Rule(name="treatment_helps", tag="physical", apply=_r_treatment_helps),
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


def treatment_fits(case: PatientCase, treatment: Treatment) -> bool:
    return treatment.id in case.allowed_treatments


def delay_outcome(case: PatientCase, culprit: CulpritCase) -> str:
    if case.severity == "severe" and culprit.delay >= 2:
        return "strained"
    return "swift"


def predict_wait(world: World, culprit: CulpritCase) -> dict:
    sim = world.copy()
    patient = sim.get("patient")
    for _ in range(culprit.delay):
        patient.meters["waiting"] += 1
        propagate(sim, narrate=False)
    return {
        "weakness": patient.meters["weakness"],
        "fear": patient.memes["fear"],
    }


def introduce(world: World, hero: Entity, doctor: Entity, case: PatientCase) -> None:
    world.say(
        f"In a mossy clinic under the roots of an old oak, {hero.id} the {hero.type} "
        f"helped Doctor {doctor.id} sort leaves, spoons, and shining jars."
    )
    world.say(
        f"{case.opening} On a peg beside the door hung the doctor's green belt, "
        f"with little pouches for needles, herbs, and notes."
    )


def arrival(world: World, patient: Entity, case: PatientCase) -> None:
    patient.meters["waiting"] = 1.0
    if case.severity == "severe":
        patient.meters["weakness"] = 1.0
        patient.memes["fear"] = 1.0
    else:
        patient.memes["worry"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Soon {patient.id} came in, {case.sign}. The whole room grew quiet, "
        f"for the trouble was {case.trouble}."
    )


def need_help(world: World, doctor: Entity, case: PatientCase, treatment: Treatment) -> None:
    if treatment.id == "intravenous_drip":
        world.say(
            f'Doctor {doctor.id} peered kindly at the patient. "{treatment.label.capitalize()}," '
            f"{doctor.pronoun()} said. \"That will carry pear-water in drop by drop.\""
        )
    else:
        world.say(
            f'Doctor {doctor.id} nodded. "{treatment.label.capitalize()} first," '
            f"{doctor.pronoun()} said, ready to set gentle help in motion."
        )


def mystery_begins(world: World, hero: Entity, doctor: Entity, culprit: CulpritCase) -> None:
    belt = world.get("belt")
    belt.meters["missing"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But just then a low {culprit.grunt_word} came from {culprit.place}, "
        f"and the peg by the door was bare."
    )
    world.say(
        f'"My belt!" cried Doctor {doctor.id}. "Without the pouch on that belt, '
        f'I cannot begin."'
    )
    world.say(
        f"{hero.id} looked at the floor, then at the empty peg, and whispered a rhyme: "
        f'"A belt has fled; I\'ll use my head. I\'ll find the path that feet have led."'
    )


def investigate(world: World, hero: Entity, culprit: CulpritCase) -> None:
    pred = predict_wait(world, culprit)
    world.facts["predicted_weakness"] = pred["weakness"]
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"By the door lay {culprit.clue}. {hero.id} followed it toward {culprit.place} "
        f"and sang another small rhyme: {culprit.rhyme}"
    )
    if pred["weakness"] >= 2:
        world.say(
            f"Behind {hero.pronoun('possessive')} brave little song, {hero.pronoun()} hurried, "
            f"for every moment of waiting made the patient wobble more."
        )
    else:
        world.say(
            f"The clue was plain enough for careful eyes, and {hero.id} did not stop."
        )


def reveal(world: World, hero: Entity, culprit_ent: Entity, culprit: CulpritCase) -> None:
    belt = world.get("belt")
    patient = world.get("patient")
    for _ in range(culprit.delay):
        patient.meters["waiting"] += 1
        propagate(world, narrate=False)
    belt.meters["missing"] = 0.0
    belt.meters["found"] = 1.0
    propagate(world, narrate=False)
    culprit_ent.memes["embarrassed"] += 1
    culprit_ent.memes["care"] += 1
    world.say(
        f"There, in {culprit.place}, stood {culprit_ent.id} the {culprit_ent.type}, "
        f"holding the green belt. {culprit_ent.pronoun().capitalize()} gave one more "
        f"{culprit.grunt_word}, then blinked in surprise."
    )
    world.say(
        f'{culprit.motive} It was no thief at all. It was a muddled helper.'
    )
    world.say(
        f'{culprit_ent.id} bowed {culprit_ent.pronoun("possessive")} head. '
        f'"I should have asked first," {culprit_ent.pronoun()} said.'
    )


def return_belt(world: World, hero: Entity, doctor: Entity, culprit: CulpritCase) -> None:
    world.say(
        f"{hero.id} took the belt gently and hurried back. {culprit.return_text}"
    )
    world.say(
        f'Doctor {doctor.id} smiled. "Quick feet and kind eyes solved the mystery," '
        f"{doctor.pronoun()} said."
    )


def treat(world: World, doctor: Entity, patient: Entity, treatment: Treatment, case: PatientCase) -> None:
    patient.meters["treated"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then Doctor {doctor.id} {treatment.action_text}."
    )
    world.say(
        f"Soon {patient.id} {treatment.proof_text}."
    )
    if treatment.id == "intravenous_drip":
        world.say(
            "The clear drops shone like tiny beads, and even the room seemed to breathe more softly."
        )


def ending(world: World, hero: Entity, culprit_ent: Entity, patient: Entity, case: PatientCase, outcome: str) -> None:
    if outcome == "strained":
        world.say(
            f"{patient.id} had been very frightened, yet help came in time. "
            f"{hero.id} felt {hero.pronoun('possessive')} heart settle as the patient grew steady again."
        )
    else:
        world.say(
            f"The trouble passed before it could grow deep, and the clinic warmed with relief."
        )
    world.say(
        f"Before sunset, {culprit_ent.id} helped hang the belt back on its peg and promised to ask before borrowing anything."
    )
    world.say(
        f"And {hero.id} remembered the lesson of the day: when a mystery makes a room feel tight, seek the truth with patience, and let kindness bring the light."
    )


def tell(hero_cfg: Hero, case: PatientCase, treatment: Treatment, culprit: CulpritCase) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_cfg.id,
        kind="character",
        type=hero_cfg.species,
        role="hero",
        traits=list(hero_cfg.traits),
        attrs={"gender": "girl" if hero_cfg.species in {"mouse", "fox"} else "boy"},
    ))
    doctor = world.add(Entity(
        id="Mira",
        kind="character",
        type="owl",
        role="doctor",
        attrs={"gender": "girl"},
    ))
    patient = world.add(Entity(
        id=case.patient_name,
        kind="character",
        type=case.patient_species,
        role="patient",
        attrs={"gender": "girl" if case.patient_species in {"doe", "hen"} else "boy"},
    ))
    culprit_ent = world.add(Entity(
        id=culprit.label,
        kind="character",
        type=culprit.species,
        role="culprit",
        attrs={"gender": "boy"},
    ))
    belt = world.add(Entity(
        id="belt",
        kind="thing",
        type="belt",
        label="green belt",
    ))
    world.add(Entity(
        id="drip",
        kind="thing",
        type="tool",
        label="intravenous stand",
    ))
    world.facts.update(
        hero=hero,
        doctor=doctor,
        patient=patient,
        culprit=culprit_ent,
        belt=belt,
        case=case,
        treatment=treatment,
        culprit_cfg=culprit,
    )

    introduce(world, hero, doctor, case)
    arrival(world, patient, case)
    need_help(world, doctor, case, treatment)

    world.para()
    mystery_begins(world, hero, doctor, culprit)
    investigate(world, hero, culprit)

    world.para()
    reveal(world, hero, culprit_ent, culprit)
    return_belt(world, hero, doctor, culprit)
    treat(world, doctor, patient, treatment, case)

    world.para()
    out = delay_outcome(case, culprit)
    ending(world, hero, culprit_ent, patient, case, out)
    world.facts["outcome"] = out
    world.facts["resolved"] = True
    return world


HEROES = {
    "pip": Hero(
        id="Pip",
        species="mouse",
        traits=["careful", "bright"],
        tags={"mouse", "helper"},
    ),
    "fern": Hero(
        id="Fern",
        species="fox",
        traits=["quick", "thoughtful"],
        tags={"fox", "helper"},
    ),
    "tuck": Hero(
        id="Tuck",
        species="mole",
        traits=["steady", "patient"],
        tags={"mole", "helper"},
    ),
}

CASES = {
    "thirsty_fawn": PatientCase(
        id="thirsty_fawn",
        patient_name="Lark",
        patient_species="doe",
        trouble="too much sun and too little water",
        sign="with knees that trembled and lips that felt dry",
        severity="severe",
        allowed_treatments={"intravenous_drip"},
        opening="That morning the shelves smelled of mint and pear.",
        tags={"clinic", "intravenous", "water"},
    ),
    "feverish_hen": PatientCase(
        id="feverish_hen",
        patient_name="Dot",
        patient_species="hen",
        trouble="a hot little fever that had left her weak",
        sign="with drooping wings and a sleepy blink",
        severity="severe",
        allowed_treatments={"intravenous_drip"},
        opening="That morning rain tapped politely on the roots above.",
        tags={"clinic", "intravenous", "fever"},
    ),
    "scraped_squirrel": PatientCase(
        id="scraped_squirrel",
        patient_name="Nip",
        patient_species="squirrel",
        trouble="a scrape from slipping on bark",
        sign="holding one paw close and trying not to sniffle",
        severity="mild",
        allowed_treatments={"poultice"},
        opening="That morning sun-stripes lay across the jars like golden ribbons.",
        tags={"clinic", "poultice", "scrape"},
    ),
    "queasy_rabbit": PatientCase(
        id="queasy_rabbit",
        patient_name="Jun",
        patient_species="rabbit",
        trouble="a tummy churn from eating clover too fast",
        sign="with long ears drooping over worried eyes",
        severity="mild",
        allowed_treatments={"tea"},
        opening="That morning the kettle gave a soft hiss like a sleepy snake.",
        tags={"clinic", "tea", "tummy"},
    ),
}

TREATMENTS = {
    "intravenous_drip": Treatment(
        id="intravenous_drip",
        label="an intravenous pear-water drip",
        use_for="severe weakness",
        action_text="fastened the pouch to the belt, hung the intravenous bottle, and let cool pear-water travel in gentle drops",
        proof_text="stopped trembling so hard and lifted a brighter face",
        tags={"intravenous", "clinic", "water"},
    ),
    "poultice": Treatment(
        id="poultice",
        label="a cool comfrey poultice",
        use_for="scrapes",
        action_text="opened the pouch on the belt and spread a cool comfrey poultice over the scrape",
        proof_text="sighed, uncurled the sore paw, and even managed a small smile",
        tags={"poultice", "herbs"},
    ),
    "tea": Treatment(
        id="tea",
        label="warm chamomile tea",
        use_for="tummy aches",
        action_text="opened the belt pouch, measured sweet herbs, and poured warm chamomile tea into a little cup",
        proof_text="sipped slowly and found that the tummy no longer twisted so sharply",
        tags={"tea", "herbs"},
    ),
}

CULPRITS = {
    "piglet_pears": CulpritCase(
        id="piglet_pears",
        label="Brim",
        species="piglet",
        grunt_word="grunt",
        place="the pear shed",
        clue="pear skins and a knot tied in green thread",
        rhyme='"To pear shed near, the signs are clear; I follow truth and not my fear."',
        motive='Brim had borrowed the belt to tie a basket of pears, hoping to bring something useful for the weak patient.',
        return_text="Brim trotted behind, carrying the pear basket that had caused the mix-up.",
        delay=1,
        tags={"grunt", "pear", "surprise"},
    ),
    "boar_blanket": CulpritCase(
        id="boar_blanket",
        label="Orrin",
        species="boar",
        grunt_word="grunt",
        place="the blanket bench",
        clue="a loop of green cloth beside a rolled blanket",
        rhyme='"Past bench and latch, I seek the match; small clues can help a mystery hatch."',
        motive='Orrin had used the belt to cinch a blanket roll, thinking the shivery patient might need warmth before the doctor arrived.',
        return_text="Orrin lumbered after them with the blanket tucked under one arm.",
        delay=2,
        tags={"grunt", "blanket", "surprise"},
    ),
    "bear_bucket": CulpritCase(
        id="bear_bucket",
        label="Moss",
        species="bear",
        grunt_word="grunt",
        place="the rain barrel",
        clue="wet pawprints and a splash with a buckle mark",
        rhyme='"By splash and mark I make my start; the smallest sign can guide a heart."',
        motive='Moss had wrapped the belt around a water bucket handle, trying to carry more cool water without spilling it.',
        return_text="Moss padded along too, still holding the bucket with both paws.",
        delay=2,
        tags={"grunt", "water", "surprise"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hero_id in HEROES:
        for case_id, case in CASES.items():
            for treatment_id, treatment in TREATMENTS.items():
                if not treatment_fits(case, treatment):
                    continue
                for culprit_id in CULPRITS:
                    combos.append((hero_id, case_id, treatment_id, culprit_id))
    return combos


@dataclass
class StoryParams:
    hero: str
    case: str
    treatment: str
    culprit: str
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
    "belt": [
        (
            "What is a belt for?",
            "A belt is a strap that holds things in place or carries little pouches. In the clinic story, the doctor's belt helped keep important tools close."
        )
    ],
    "intravenous": [
        (
            "What does intravenous mean?",
            "Intravenous means a liquid goes into the body through a tiny tube instead of being drunk. Doctors use it when someone is too weak or too sick to drink enough by mouth."
        )
    ],
    "grunt": [
        (
            "What is a grunt?",
            "A grunt is a short, low sound some animals make. It can be a clue in a story when someone hears it and wonders who is nearby."
        )
    ],
    "poultice": [
        (
            "What is a poultice?",
            "A poultice is a soft, soothing covering made to rest on a sore spot. It helps cool or comfort a scrape."
        )
    ],
    "tea": [
        (
            "Why might warm tea help a tummy feel better?",
            "Warm tea can be gentle and calming. Some herbs are used to settle a twisty tummy."
        )
    ],
    "water": [
        (
            "Why is water important when someone is weak from heat?",
            "Bodies need water to work well. After too much heat or too little drinking, water helps the body steady itself again."
        )
    ],
    "surprise": [
        (
            "Why was the ending a surprise?",
            "The hero expected a thief, but found a helper who had made a muddle. Surprise endings can teach us not to judge too fast."
        )
    ],
}
KNOWLEDGE_ORDER = ["belt", "intravenous", "grunt", "poultice", "tea", "water", "surprise"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    case = world.facts["case"]
    treatment = world.facts["treatment"]
    culprit = world.facts["culprit_cfg"]
    return [
        f'Write a short fable for a 3-to-5-year-old about a young {hero.type} who must solve a clinic mystery after hearing a "{culprit.grunt_word}". Include the word "belt".',
        f'Write a rhyming animal story where a missing belt delays help for a patient with {case.trouble}, and the surprise is that the culprit meant to help.',
        f'Write a gentle mystery-to-solve tale that includes the word "{treatment.id.split("_")[0] if treatment.id != "intravenous_drip" else "intravenous"}" and ends with a clear lesson about asking before borrowing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    doctor = world.facts["doctor"]
    patient = world.facts["patient"]
    case = world.facts["case"]
    treatment = world.facts["treatment"]
    culprit_ent = world.facts["culprit"]
    culprit = world.facts["culprit_cfg"]
    outcome = world.facts["outcome"]
    pred_weak = world.facts.get("predicted_weakness", 0.0)

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, Doctor {doctor.id}, and {patient.id}, the patient who needed help. It also includes {culprit_ent.id}, whose strange {culprit.grunt_word} started the mystery."
        ),
        (
            "What mystery did the hero have to solve?",
            f"{hero.id} had to find Doctor {doctor.id}'s missing belt after hearing a {culprit.grunt_word} from {culprit.place}. The belt mattered because the doctor's pouch and tools were tied to it."
        ),
        (
            f"Why was the missing belt important in this story?",
            f"The belt carried what Doctor {doctor.id} needed to begin {treatment.label}. Without it, the patient had to wait longer, and waiting was risky because the trouble was {case.trouble}."
        ),
        (
            f"What clue helped {hero.id} solve the mystery?",
            f"{hero.id} noticed {culprit.clue} and followed that sign to {culprit.place}. The clue turned the mystery from a guess into something {hero.pronoun()} could truly solve."
        ),
        (
            f"Why was the ending a surprise?",
            f"It looked as if someone had stolen the belt, but {culprit_ent.id} had borrowed it while trying to help. The surprise changes the story from blame into understanding."
        ),
    ]
    if treatment.id == "intravenous_drip":
        qa.append(
            (
                f"Why did the patient need an intravenous drip?",
                f"{patient.id} was too weak from {case.trouble}, so Doctor {doctor.id} chose an intravenous drip to send pear-water in gently. That mattered because the patient needed help quickly and steadily."
            )
        )
    else:
        qa.append(
            (
                f"How did Doctor {doctor.id} help {patient.id} once the belt came back?",
                f"Doctor {doctor.id} used {treatment.label} for the right kind of trouble. It fit the problem because {case.trouble} needed gentle, simple care instead of a stronger treatment."
            )
        )
    if outcome == "strained":
        qa.append(
            (
                "Did the delay matter?",
                f"Yes. The delay made the patient more frightened and weak before the belt was found. Even so, the helpers moved fast enough that treatment still came in time."
            )
        )
    elif pred_weak >= 2:
        qa.append(
            (
                "Did the hero have to hurry?",
                f"Yes. {hero.id} understood that waiting would make the patient wobble more. That is why the rhyme stayed gentle, but the search stayed quick."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the patient feeling better, the belt hanging back on its peg, and everyone understanding the muddle. The ending image shows that truth and kindness set the room right again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    case = world.facts["case"]
    treatment = world.facts["treatment"]
    culprit = world.facts["culprit_cfg"]
    tags = set(case.tags) | set(treatment.tags) | set(culprit.tags) | {"belt"}
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="pip",
        case="thirsty_fawn",
        treatment="intravenous_drip",
        culprit="piglet_pears",
    ),
    StoryParams(
        hero="fern",
        case="feverish_hen",
        treatment="intravenous_drip",
        culprit="boar_blanket",
    ),
    StoryParams(
        hero="tuck",
        case="scraped_squirrel",
        treatment="poultice",
        culprit="bear_bucket",
    ),
    StoryParams(
        hero="pip",
        case="queasy_rabbit",
        treatment="tea",
        culprit="piglet_pears",
    ),
]


def explain_rejection(case: PatientCase, treatment: Treatment) -> str:
    if case.severity == "severe":
        good = ", ".join(sorted(case.allowed_treatments))
        return (
            f"(No story: {case.patient_name}'s case is severe, so {treatment.label} is not strong enough here. "
            f"Use one of: {good}.)"
        )
    good = ", ".join(sorted(case.allowed_treatments))
    return (
        f"(No story: {case.patient_name}'s problem is mild, so {treatment.label} would be unreasonable and fussy. "
        f"Use one of: {good}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return delay_outcome(CASES[params.case], CULPRITS[params.culprit])


ASP_RULES = r"""
fits(Case, Treat) :- allows(Case, Treat).

valid(Hero, Case, Treat, Culprit) :-
    hero(Hero), patient_case(Case), treatment(Treat), culprit(Culprit),
    fits(Case, Treat).

strained :- chosen_case(Case), severe(Case), chosen_culprit(Culprit), delay(Culprit, D), D >= 2.
outcome(strained) :- strained.
outcome(swift) :- not strained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for case_id, case in CASES.items():
        lines.append(asp.fact("patient_case", case_id))
        if case.severity == "severe":
            lines.append(asp.fact("severe", case_id))
        else:
            lines.append(asp.fact("mild", case_id))
        for treatment_id in sorted(case.allowed_treatments):
            lines.append(asp.fact("allows", case_id, treatment_id))
    for treatment_id in TREATMENTS:
        lines.append(asp.fact("treatment", treatment_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("delay", culprit_id, culprit.delay))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_case", params.case),
            asp.fact("chosen_culprit", params.culprit),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

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
        sample = generate(cases[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rhyming fable clinic mystery with a missing belt."
    )
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--treatment", choices=TREATMENTS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case is not None and args.treatment is not None:
        case = CASES[args.case]
        treatment = TREATMENTS[args.treatment]
        if not treatment_fits(case, treatment):
            raise StoryError(explain_rejection(case, treatment))

    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.case is None or combo[1] == args.case)
        and (args.treatment is None or combo[2] == args.treatment)
        and (args.culprit is None or combo[3] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, case_id, treatment_id, culprit_id = rng.choice(sorted(combos))
    return StoryParams(
        hero=hero_id,
        case=case_id,
        treatment=treatment_id,
        culprit=culprit_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hero not in HEROES:
        raise StoryError(f"(Unknown hero: {params.hero})")
    if params.case not in CASES:
        raise StoryError(f"(Unknown case: {params.case})")
    if params.treatment not in TREATMENTS:
        raise StoryError(f"(Unknown treatment: {params.treatment})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")

    hero_cfg = HEROES[params.hero]
    case = CASES[params.case]
    treatment = TREATMENTS[params.treatment]
    culprit = CULPRITS[params.culprit]

    if not treatment_fits(case, treatment):
        raise StoryError(explain_rejection(case, treatment))

    world = tell(hero_cfg, case, treatment, culprit)
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
        print(f"{len(combos)} valid (hero, case, treatment, culprit) combos:\n")
        for hero_id, case_id, treatment_id, culprit_id in combos:
            print(f"  {hero_id:5} {case_id:16} {treatment_id:18} {culprit_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero}: {p.case} with {p.treatment} ({p.culprit}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
