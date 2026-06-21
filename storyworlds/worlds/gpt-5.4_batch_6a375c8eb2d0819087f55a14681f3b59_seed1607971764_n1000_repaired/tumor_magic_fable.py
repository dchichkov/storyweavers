#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tumor_magic_fable.py
===============================================

A standalone storyworld for a gentle magical fable about a forest creature with
a tumor, a wise helper, and the patient kind of magic that truly helps.

This world models a small, classical domain:

- a woodland animal has a tumor that aches or weighs on them
- they wish to join some happy forest occasion anyway
- a wise healer chooses a matching kind of magic in the right place
- the remedy works only when it fits the tumor and the patient also rests
- the ending proves the fable's lesson: bright tricks are weaker than careful wisdom

Run it
------
    python storyworlds/worlds/gpt-5.4/tumor_magic_fable.py
    python storyworlds/worlds/gpt-5.4/tumor_magic_fable.py --tumor thorn_tumor --remedy moondew_poultice --place brookbank
    python storyworlds/worlds/gpt-5.4/tumor_magic_fable.py --tumor shadow_tumor --remedy moondew_poultice
    python storyworlds/worlds/gpt-5.4/tumor_magic_fable.py --all
    python storyworlds/worlds/gpt-5.4/tumor_magic_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tumor_magic_fable.py --json
    python storyworlds/worlds/gpt-5.4/tumor_magic_fable.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"doe", "hen", "ewe"}
        male = {"stag", "rooster", "ram"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain registries
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class PatientCfg:
    id: str
    name: str
    type: str
    label: str
    nature: str
    gift: str
    home: str
    festival: str
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
class TumorCfg:
    id: str
    label: str
    place: str
    ache: str
    appearance: str
    cause: str
    needs: str
    severity: int
    rest_need: int
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
class RemedyCfg:
    id: str
    label: str
    phrase: str
    place_need: str
    matches: str
    power: int
    making: str
    touch: str
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
class PlaceCfg:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
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
class HealerCfg:
    id: str
    name: str
    type: str
    title: str
    wisdom: str
    moral: str
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


PATIENTS = {
    "rabbit": PatientCfg(
        id="rabbit",
        name="Pip",
        type="rabbit",
        label="young rabbit",
        nature="quick-footed and eager",
        gift="leaping first and laughing fast",
        home="a burrow under the roots of an oak",
        festival="the lantern dance in the clearing",
        traits=["quick", "hopeful"],
        tags={"rabbit", "forest"},
    ),
    "fawn": PatientCfg(
        id="fawn",
        name="Mira",
        type="fawn",
        label="young fawn",
        nature="gentle and bright-eyed",
        gift="carrying songs softly through the trees",
        home="a fern bed near the silver stream",
        festival="the evening garland feast",
        traits=["gentle", "hopeful"],
        tags={"deer", "forest"},
    ),
    "hedgehog": PatientCfg(
        id="hedgehog",
        name="Bramble",
        type="hedgehog",
        label="young hedgehog",
        nature="small, tidy, and determined",
        gift="finding lost things under leaves",
        home="a mossy nook beside a fallen log",
        festival="the berry-sharing supper",
        traits=["steady", "hopeful"],
        tags={"hedgehog", "forest"},
    ),
}

HEALERS = {
    "owl": HealerCfg(
        id="owl",
        name="Aster",
        type="owl",
        title="the old owl healer",
        wisdom="had watched many seasons and trusted quiet signs more than loud guesses",
        moral="True magic listens before it shines.",
        tags={"owl", "wisdom", "magic"},
    ),
    "tortoise": HealerCfg(
        id="tortoise",
        name="Mossback",
        type="tortoise",
        title="the old tortoise healer",
        wisdom="moved slowly, but never chose a remedy before understanding the trouble",
        moral="The safest spell is the one that fits the need.",
        tags={"tortoise", "wisdom", "magic"},
    ),
}

TUMORS = {
    "thorn_tumor": TumorCfg(
        id="thorn_tumor",
        label="thorny tumor",
        place="by one front paw",
        ache="stung with each step",
        appearance="a small hard knot under the fur",
        cause="a spiteful thorn-spore had settled there after a windy day",
        needs="soften",
        severity=1,
        rest_need=1,
        tags={"tumor", "thorn", "care"},
    ),
    "shadow_tumor": TumorCfg(
        id="shadow_tumor",
        label="shadowy tumor",
        place="beneath one shoulder",
        ache="pulled like a little stone whenever the patient tried to dance",
        appearance="a dusky lump that seemed to swallow the light around it",
        cause="too many moonless nights of worry had gathered there, according to woodland lore",
        needs="light",
        severity=2,
        rest_need=2,
        tags={"tumor", "shadow", "care"},
    ),
    "moss_tumor": TumorCfg(
        id="moss_tumor",
        label="mossy tumor",
        place="behind one ear",
        ache="felt warm and heavy by evening",
        appearance="a soft green bump that puffed up after rain",
        cause="sleeping too often in a damp hollow had fed the strange growth",
        needs="warmth",
        severity=2,
        rest_need=2,
        tags={"tumor", "moss", "care"},
    ),
}

REMEDIES = {
    "moondew_poultice": RemedyCfg(
        id="moondew_poultice",
        label="moondew poultice",
        phrase="a moondew poultice",
        place_need="brookbank",
        matches="soften",
        power=1,
        making="gathered silver dew from reeds and stirred it with crushed mint in a shell cup",
        touch="laid the cool shining poultice over the sore place until the tightness loosened",
        tags={"magic", "dew", "poultice"},
    ),
    "sunbeam_song": RemedyCfg(
        id="sunbeam_song",
        label="sunbeam song",
        phrase="the sunbeam song",
        place_need="hilltop",
        matches="light",
        power=2,
        making="faced the east wind and sang a bright old tune that caught the first gold beams",
        touch="let the warm notes fall over the lump until its shadows thinned",
        tags={"magic", "song", "light"},
    ),
    "ember_moss_charm": RemedyCfg(
        id="ember_moss_charm",
        label="ember-moss charm",
        phrase="an ember-moss charm",
        place_need="hearth_cave",
        matches="warmth",
        power=2,
        making="braided ember-moss with rosemary threads beside a banked red fire",
        touch="rested the charm against the swelling until gentle warmth soaked through it",
        tags={"magic", "charm", "warmth"},
    ),
    "sparkle_flash": RemedyCfg(
        id="sparkle_flash",
        label="sparkle flash",
        phrase="a sparkle flash",
        place_need="crystal_glade",
        matches="glitter",
        power=0,
        making="snapped bright petals in the air so they burst into pretty sparks",
        touch="made everything glitter for a blink, but did nothing for the pain underneath",
        tags={"magic", "sparkle"},
    ),
}

PLACES = {
    "brookbank": PlaceCfg(
        id="brookbank",
        label="the brookbank",
        scene="where reeds bowed over clear water and moondew clung to every blade of grass",
        affords={"moondew_poultice"},
        tags={"brook", "dew", "forest"},
    ),
    "hilltop": PlaceCfg(
        id="hilltop",
        label="the hilltop",
        scene="where the dawn reached first and the wind carried clean bright light",
        affords={"sunbeam_song"},
        tags={"hill", "light", "forest"},
    ),
    "hearth_cave": PlaceCfg(
        id="hearth_cave",
        label="the hearth cave",
        scene="where old stones held a safe glow and the air smelled of rosemary",
        affords={"ember_moss_charm"},
        tags={"cave", "warmth", "forest"},
    ),
    "crystal_glade": PlaceCfg(
        id="crystal_glade",
        label="the crystal glade",
        scene="where flowers made lovely sparks when shaken, though little true healing lived there",
        affords={"sparkle_flash"},
        tags={"glade", "sparkle", "forest"},
    ),
}

NAMES = ["Pip", "Mira", "Bramble"]
REST_CHOICES = [1, 2]
TRACELESS_SPARKLE_WARNING = (
    "Many young creatures admired pretty sparks, but the old healers said that pretty was not the same as helpful."
)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


def _r_tumor_burden(world: World) -> list[str]:
    patient = world.get("patient")
    tumor = world.get("tumor")
    if tumor.meters["present"] < THRESHOLD:
        return []
    sig = ("tumor_burden",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    patient.meters["pain"] += tumor.attrs["severity"]
    patient.memes["worry"] += 1
    return ["__burden__"]


def _r_matching_magic(world: World) -> list[str]:
    patient = world.get("patient")
    tumor = world.get("tumor")
    remedy = world.get("remedy")
    place = world.get("place")
    if remedy.meters["cast"] < THRESHOLD:
        return []
    sig = ("matching_magic",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if remedy.attrs["matches"] == tumor.attrs["needs"] and remedy.id in place.attrs["affords"]:
        patient.meters["soothed"] += remedy.attrs["power"]
        patient.memes["hope"] += 1
        return ["__matched__"]
    patient.meters["pain"] += 1
    patient.memes["fear"] += 1
    return ["__mismatch__"]


def _r_heal_or_linger(world: World) -> list[str]:
    patient = world.get("patient")
    tumor = world.get("tumor")
    if patient.meters["soothed"] < tumor.attrs["severity"]:
        return []
    sig = ("heal_or_linger",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rest_nights = int(patient.attrs["rest_nights"])
    if rest_nights >= tumor.attrs["rest_need"]:
        tumor.meters["present"] = 0.0
        tumor.meters["calm"] += 1
        patient.meters["pain"] = 0.0
        patient.memes["relief"] += 1
        patient.memes["gratitude"] += 1
        return ["__healed__"]
    tumor.meters["smaller"] += 1
    patient.meters["pain"] = max(0.0, patient.meters["pain"] - 1.0)
    patient.memes["patience"] += 1
    patient.memes["hope"] += 1
    return ["__lingering__"]


CAUSAL_RULES = [
    Rule(name="tumor_burden", tag="physical", apply=_r_tumor_burden),
    Rule(name="matching_magic", tag="magic", apply=_r_matching_magic),
    Rule(name="heal_or_linger", tag="resolution", apply=_r_heal_or_linger),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def compatible(tumor: TumorCfg, remedy: RemedyCfg, place: PlaceCfg) -> bool:
    return remedy.matches == tumor.needs and remedy.id in place.affords


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for tumor_id, tumor in TUMORS.items():
        for remedy_id, remedy in REMEDIES.items():
            for place_id, place in PLACES.items():
                if compatible(tumor, remedy, place):
                    combos.append((tumor_id, remedy_id, place_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    tumor = TUMORS[params.tumor]
    if params.rest_nights >= tumor.rest_need:
        return "healed"
    return "lingering"


def explain_rejection(tumor: TumorCfg, remedy: RemedyCfg, place: PlaceCfg) -> str:
    if remedy.matches != tumor.needs:
        return (
            f"(No story: {remedy.label} does not fit a {tumor.label}. "
            f"This tumor needs magic that can {tumor.needs}, not a different kind of spell.)"
        )
    if remedy.id not in place.affords:
        return (
            f"(No story: {remedy.label} can only be worked properly at {PLACES[remedy.place_need].label}, "
            f"not at {place.label}.)"
        )
    return "(No story: this magic does not fit this tumor in this place.)"


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    remedy = sim.get("remedy")
    remedy.meters["cast"] += 1
    propagate(sim, narrate=False)
    tumor = sim.get("tumor")
    return {
        "healed": tumor.meters["present"] < THRESHOLD,
        "pain": sim.get("patient").meters["pain"],
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def introduce(world: World, patient: Entity, healer: Entity, patient_cfg: PatientCfg,
              healer_cfg: HealerCfg) -> None:
    patient.memes["joy"] += 1
    world.say(
        f"In the green heart of the forest lived {patient_cfg.name}, a {patient_cfg.label} who was "
        f"{patient_cfg.nature}. {patient.pronoun().capitalize()} was known for {patient_cfg.gift}."
    )
    world.say(
        f"Not far away lived {healer_cfg.name}, {healer_cfg.title}, who {healer_cfg.wisdom}."
    )


def discovery(world: World, patient: Entity, patient_cfg: PatientCfg, tumor_cfg: TumorCfg) -> None:
    world.say(
        f"On the morning of {patient_cfg.festival}, {patient_cfg.name} longed to hurry out from "
        f"{patient_cfg.home}. Yet {patient.pronoun('possessive')} step slowed, because a {tumor_cfg.label} "
        f"{tumor_cfg.place} {tumor_cfg.ache}."
    )
    world.say(
        f"It looked like {tumor_cfg.appearance}, and the elders would have called it a tumor. "
        f"{patient_cfg.name} tried to hide it under a brave smile."
    )


def seek_help(world: World, patient: Entity, healer: Entity,
              tumor_cfg: TumorCfg, patient_cfg: PatientCfg) -> None:
    world.say(
        f'"If I ignore it, perhaps I can still join {patient_cfg.festival}," thought {patient_cfg.name}.'
    )
    world.say(
        f"But when the ache grew sharper, {patient_cfg.name} went to {healer.id} and whispered, "
        f'"Please look. I want to be merry, but this tumor will not let me."'
    )
    patient.memes["trust"] += 1
    healer.memes["care"] += 1
    world.facts["cause"] = tumor_cfg.cause


def examine(world: World, patient: Entity, healer: Entity, tumor_cfg: TumorCfg) -> None:
    pred = predict_outcome(world)
    world.facts["predicted_healed"] = pred["healed"]
    healer.memes["wisdom"] += 1
    world.say(
        f"{healer.id} studied the swelling gently and said, "
        f'"This is no scratch. {tumor_cfg.cause.capitalize()}."'
    )
    world.say(
        f'{TRACELESS_SPARKLE_WARNING} "{tumor_cfg.label.capitalize()} does not fear noise," '
        f'{healer.id} said. "It yields only to the right kind of care."'
    )


def journey(world: World, patient_cfg: PatientCfg, place_cfg: PlaceCfg) -> None:
    world.say(
        f"So they went to {place_cfg.label}, {place_cfg.scene}."
    )


def craft_magic(world: World, healer: Entity, remedy_cfg: RemedyCfg) -> None:
    healer.memes["focus"] += 1
    world.say(
        f"There {healer.id} {remedy_cfg.making}."
    )


def cast_magic(world: World, patient: Entity, healer: Entity,
               remedy_cfg: RemedyCfg, tumor_cfg: TumorCfg) -> None:
    remedy = world.get("remedy")
    remedy.meters["cast"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {healer.id} used {remedy_cfg.phrase} and {remedy_cfg.touch}."
    )
    if patient.meters["soothed"] >= tumor_cfg.severity:
        world.say(
            f"{patient.id} felt the pain loosen, as if a hard fist had finally opened."
        )
    else:
        world.say(
            f"The air glittered, but the ache remained, and the little creature's eyes filled with worry."
        )


def rest(world: World, patient: Entity, patient_cfg: PatientCfg, tumor_cfg: TumorCfg) -> None:
    nights = int(patient.attrs["rest_nights"])
    if nights == 1:
        night_phrase = "one quiet night"
    else:
        night_phrase = f"{nights} quiet nights"
    world.say(
        f'"Now rest for {night_phrase}," said the healer. "Magic opens the door, but rest lets healing walk through it."'
    )
    patient.memes["obedience"] += 1


def ending(world: World, patient: Entity, healer_cfg: HealerCfg,
           patient_cfg: PatientCfg, tumor_cfg: TumorCfg) -> None:
    if world.get("tumor").meters["present"] < THRESHOLD:
        world.say(
            f"When the resting was done, the tumor was gone. {patient_cfg.name} stepped out lightly, "
            f"and at {patient_cfg.festival} {patient.pronoun()} moved with easy joy instead of pain."
        )
        world.say(
            f"From then on, whenever young creatures begged for loud bright tricks, {patient_cfg.name} would say, "
            f'"{healer_cfg.moral}"'
        )
    else:
        world.say(
            f"By dawn the tumor had grown smaller and kinder, though it had not gone away completely. "
            f"{patient_cfg.name} did not run to the feast at once."
        )
        world.say(
            f"Instead {patient.pronoun()} tucked up under a warm blanket of moss and chose patience over hurry, "
            f"knowing the right magic had begun the work. And {patient.pronoun()} repeated to {patient.pronoun('object')}self, "
            f'"{healer_cfg.moral}"'
        )


@dataclass
class StoryParams:
    patient: str = "rabbit"
    healer: str = "owl"
    tumor: str = "thorn_tumor"
    remedy: str = "moondew_poultice"
    place: str = "brookbank"
    rest_nights: int = 1
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


def tell(patient_cfg: PatientCfg, healer_cfg: HealerCfg, tumor_cfg: TumorCfg,
         remedy_cfg: RemedyCfg, place_cfg: PlaceCfg, rest_nights: int) -> World:
    world = World()
    patient = world.add(Entity(
        id=patient_cfg.name,
        kind="character",
        type=patient_cfg.type,
        label=patient_cfg.label,
        traits=list(patient_cfg.traits),
        role="patient",
        attrs={"rest_nights": rest_nights},
    ))
    healer = world.add(Entity(
        id=healer_cfg.name,
        kind="character",
        type=healer_cfg.type,
        label=healer_cfg.title,
        traits=["wise", "patient"],
        role="healer",
        attrs={},
    ))
    tumor = world.add(Entity(
        id="tumor",
        kind="thing",
        type="tumor",
        label=tumor_cfg.label,
        attrs={"needs": tumor_cfg.needs, "severity": tumor_cfg.severity, "rest_need": tumor_cfg.rest_need},
    ))
    remedy = world.add(Entity(
        id=remedy_cfg.id,
        kind="thing",
        type="remedy",
        label=remedy_cfg.label,
        attrs={"matches": remedy_cfg.matches, "power": remedy_cfg.power},
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place_cfg.label,
        attrs={"affords": set(place_cfg.affords)},
    ))

    tumor.meters["present"] = 1.0
    world.facts["rest_nights"] = rest_nights
    world.facts["outcome"] = outcome_of(
        StoryParams(
            patient=patient_cfg.id,
            healer=healer_cfg.id,
            tumor=tumor_cfg.id,
            remedy=remedy_cfg.id,
            place=place_cfg.id,
            rest_nights=rest_nights,
            seed=None,
        )
    )

    introduce(world, patient, healer, patient_cfg, healer_cfg)
    discovery(world, patient, patient_cfg, tumor_cfg)

    world.para()
    propagate(world, narrate=False)
    seek_help(world, patient, healer, tumor_cfg, patient_cfg)
    examine(world, patient, healer, tumor_cfg)

    world.para()
    journey(world, patient_cfg, place_cfg)
    craft_magic(world, healer, remedy_cfg)
    cast_magic(world, patient, healer, remedy_cfg, tumor_cfg)
    rest(world, patient, patient_cfg, tumor_cfg)

    world.para()
    ending(world, patient, healer_cfg, patient_cfg, tumor_cfg)

    world.facts.update(
        patient=patient,
        healer=healer,
        patient_cfg=patient_cfg,
        healer_cfg=healer_cfg,
        tumor_cfg=tumor_cfg,
        remedy_cfg=remedy_cfg,
        place_cfg=place_cfg,
        tumor=tumor,
        remedy=remedy,
        place=place,
        healed=tumor.meters["present"] < THRESHOLD,
        lingering=tumor.meters["present"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "tumor": [(
        "What is a tumor?",
        "A tumor is a lump or growth in the body. If someone has one, they should be cared for by wise grown-ups or healers."
    )],
    "magic": [(
        "What does magic mean in a fable?",
        "In a fable, magic is a story way of showing care, wisdom, or hidden truth. The best magic still follows the story's rules and helps for a reason."
    )],
    "dew": [(
        "What is dew?",
        "Dew is tiny water drops that rest on grass and leaves, especially in the early morning. In stories, it often feels gentle and fresh."
    )],
    "song": [(
        "Why can a song feel healing in a story?",
        "A song can calm a frightened heart and help someone feel brave enough to rest. In a fable, a song may also carry gentle magic."
    )],
    "warmth": [(
        "Why can warmth help someone rest?",
        "Warmth can help a body relax and feel safe. Rest is easier when pain eases and the body is calm."
    )],
    "patience": [(
        "Why is patience important when someone is healing?",
        "Healing can take time, even after the right help begins. Patience means not rushing the body before it is ready."
    )],
    "fable": [(
        "What is a fable?",
        "A fable is a short story that often uses animals or simple characters to teach a lesson. At the end, the change in the story shows the moral."
    )],
}
KNOWLEDGE_ORDER = ["tumor", "magic", "dew", "song", "warmth", "patience", "fable"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    patient_cfg = f["patient_cfg"]
    tumor_cfg = f["tumor_cfg"]
    remedy_cfg = f["remedy_cfg"]
    outcome = "healed" if f["healed"] else "lingering"
    base = (
        f'Write a short fable for young children about {patient_cfg.name}, a woodland creature with a {tumor_cfg.label}. '
        f'Include the word "tumor" and use gentle magic.'
    )
    if outcome == "healed":
        return [
            base,
            f"Tell a forest fable where a wise healer chooses {remedy_cfg.phrase} instead of flashy tricks, and the patient learns to rest.",
            f'Write a magical animal story with a clear moral: the right care, not the loudest sparkle, brings true healing.',
        ]
    return [
        base,
        f"Tell a fable where the right magic helps, but the patient still must wait and rest before the healing is complete.",
        f'Write a gentle moral tale showing that wisdom begins healing, and patience finishes it.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    patient_cfg = f["patient_cfg"]
    healer_cfg = f["healer_cfg"]
    tumor_cfg = f["tumor_cfg"]
    remedy_cfg = f["remedy_cfg"]
    place_cfg = f["place_cfg"]
    rest_nights = f["rest_nights"]
    patient = f["patient"]
    healer = f["healer"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {patient_cfg.name}, a {patient_cfg.label}, and {healer_cfg.name}, {healer_cfg.title}. "
            f"Their story begins when {patient_cfg.name} tries to be brave even though a tumor hurts."
        ),
        (
            f"Why did {patient_cfg.name} go to the healer?",
            f"{patient_cfg.name} wanted to join {patient_cfg.festival}, but the {tumor_cfg.label} {tumor_cfg.place} kept hurting. "
            f"{patient.pronoun().capitalize()} went for help because pretending to be fine did not make the pain go away."
        ),
        (
            f"Why did the healer take {patient_cfg.name} to {place_cfg.label}?",
            f"{healer_cfg.name} went there because {remedy_cfg.label} can be made properly only at {place_cfg.label}. "
            f"In this story, the place matters because the magic must fit both the tumor and the land."
        ),
        (
            f"What magic was used, and how did it help?",
            f"The healer used {remedy_cfg.phrase}. It matched what the {tumor_cfg.label} needed, so the pain loosened instead of growing worse."
        ),
    ]
    if f["healed"]:
        qa.append((
            f"How did the story end?",
            f"After resting for {rest_nights} quiet night{'s' if rest_nights != 1 else ''}, the tumor was gone and {patient_cfg.name} could move lightly again. "
            f"The ending shows the moral because careful magic and patient rest changed the day."
        ))
    else:
        qa.append((
            f"Was {patient_cfg.name} all better right away?",
            f"No. The right magic made the tumor smaller and kinder, but {patient_cfg.name} still needed more rest before it would be fully gone. "
            f"The story teaches that healing may begin quickly while finishing slowly."
        ))
        qa.append((
            f"What lesson did {patient_cfg.name} learn?",
            f"{patient.pronoun().capitalize()} learned not to chase a fast glittering answer. "
            f"{healer_cfg.moral} That lesson mattered because the body needed time as well as magic."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"tumor", "magic", "patience", "fable"}
    remedy = f["remedy_cfg"]
    if remedy.id == "moondew_poultice":
        tags.add("dew")
    elif remedy.id == "sunbeam_song":
        tags.add("song")
    elif remedy.id == "ember_moss_charm":
        tags.add("warmth")
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
        attrs = {k: v for k, v in ent.attrs.items() if v or v == 0}
        parts = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if attrs:
            parts.append(f"attrs={attrs}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        patient="rabbit",
        healer="owl",
        tumor="thorn_tumor",
        remedy="moondew_poultice",
        place="brookbank",
        rest_nights=1,
        seed=None,
    ),
    StoryParams(
        patient="fawn",
        healer="tortoise",
        tumor="shadow_tumor",
        remedy="sunbeam_song",
        place="hilltop",
        rest_nights=2,
        seed=None,
    ),
    StoryParams(
        patient="hedgehog",
        healer="owl",
        tumor="moss_tumor",
        remedy="ember_moss_charm",
        place="hearth_cave",
        rest_nights=1,
        seed=None,
    ),
    StoryParams(
        patient="rabbit",
        healer="tortoise",
        tumor="moss_tumor",
        remedy="ember_moss_charm",
        place="hearth_cave",
        rest_nights=2,
        seed=None,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% valid treatment when the remedy matches the tumor's need and the place affords it
compatible(T, R, P) :- tumor(T), remedy(R), place(P),
                       needs(T, N), matches(R, N), affords(P, R).

% outcome after a valid treatment depends on the amount of rest
outcome(healed) :- chosen_tumor(T), compatible(T, R, P), chosen_remedy(R), chosen_place(P),
                   rest_nights(N), rest_need(T, Need), N >= Need.
outcome(lingering) :- chosen_tumor(T), compatible(T, R, P), chosen_remedy(R), chosen_place(P),
                      rest_nights(N), rest_need(T, Need), N < Need.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tumor_id, tumor in TUMORS.items():
        lines.append(asp.fact("tumor", tumor_id))
        lines.append(asp.fact("needs", tumor_id, tumor.needs))
        lines.append(asp.fact("rest_need", tumor_id, tumor.rest_need))
        lines.append(asp.fact("severity", tumor_id, tumor.severity))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("matches", remedy_id, remedy.matches))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for remedy_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, remedy_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_tumor", params.tumor),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_place", params.place),
        asp.fact("rest_nights", params.rest_nights),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP valid combos match Python ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in ASP:", sorted(cset - pset))
        if pset - cset:
            print("  only in Python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve_params failure at seed {seed}.")
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            bad += 1
    if bad == 0:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(resolve_params(parser.parse_args([]), random.Random(123)))
        if not sample.story.strip():
            raise StoryError("empty story")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A magical forest fable about a tumor, the right remedy, and the patience healing needs."
    )
    ap.add_argument("--patient", choices=PATIENTS)
    ap.add_argument("--healer", choices=HEALERS)
    ap.add_argument("--tumor", choices=TUMORS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rest-nights", type=int, choices=REST_CHOICES, dest="rest_nights")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include generation prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible treatment triples from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tumor and args.remedy and args.place:
        if not compatible(TUMORS[args.tumor], REMEDIES[args.remedy], PLACES[args.place]):
            raise StoryError(explain_rejection(TUMORS[args.tumor], REMEDIES[args.remedy], PLACES[args.place]))

    combos = [
        combo for combo in valid_combos()
        if (args.tumor is None or combo[0] == args.tumor)
        and (args.remedy is None or combo[1] == args.remedy)
        and (args.place is None or combo[2] == args.place)
    ]
    if not combos:
        if args.tumor and args.remedy and args.place:
            raise StoryError(explain_rejection(TUMORS[args.tumor], REMEDIES[args.remedy], PLACES[args.place]))
        raise StoryError("(No valid combination matches the given options.)")

    tumor_id, remedy_id, place_id = rng.choice(sorted(combos))
    patient_id = args.patient or rng.choice(sorted(PATIENTS))
    healer_id = args.healer or rng.choice(sorted(HEALERS))
    rest_nights = args.rest_nights if args.rest_nights is not None else rng.choice(REST_CHOICES)

    return StoryParams(
        patient=patient_id,
        healer=healer_id,
        tumor=tumor_id,
        remedy=remedy_id,
        place=place_id,
        rest_nights=rest_nights,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.patient not in PATIENTS:
        raise StoryError(f"(Unknown patient: {params.patient})")
    if params.healer not in HEALERS:
        raise StoryError(f"(Unknown healer: {params.healer})")
    if params.tumor not in TUMORS:
        raise StoryError(f"(Unknown tumor: {params.tumor})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.rest_nights not in REST_CHOICES:
        raise StoryError(f"(Unsupported rest count: {params.rest_nights})")

    tumor_cfg = TUMORS[params.tumor]
    remedy_cfg = REMEDIES[params.remedy]
    place_cfg = PLACES[params.place]
    if not compatible(tumor_cfg, remedy_cfg, place_cfg):
        raise StoryError(explain_rejection(tumor_cfg, remedy_cfg, place_cfg))

    world = tell(
        patient_cfg=PATIENTS[params.patient],
        healer_cfg=HEALERS[params.healer],
        tumor_cfg=tumor_cfg,
        remedy_cfg=remedy_cfg,
        place_cfg=place_cfg,
        rest_nights=params.rest_nights,
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
        print(asp_program("", "#show compatible/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (tumor, remedy, place) combos:\n")
        for tumor_id, remedy_id, place_id in combos:
            print(f"  {tumor_id:14} {remedy_id:18} {place_id}")
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
            header = (
                f"### {PATIENTS[p.patient].name}: {p.tumor} with {p.remedy} at {p.place} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
