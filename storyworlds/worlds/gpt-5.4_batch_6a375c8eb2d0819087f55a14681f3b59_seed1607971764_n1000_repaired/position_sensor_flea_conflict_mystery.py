#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py
==================================================================

A standalone storyworld for a small child-facing mystery: something in a secret
play space keeps ending up in the wrong position, one child blames another, and
a tiny sensor reveals the real culprit. The culprit is not a sneaky friend after
all, but an itchy little animal bothered by a flea.

The world model drives the prose:
- a marker begins in the correct position
- an unseen culprit slips into the play space and scratches
- that scratching bumps the marker out of place
- the children argue because one child thinks the other moved it
- they set a sensor trap
- the sensor proves who really did it
- the conflict ends with an apology and a practical fix

Run it
------
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py --place fort --sensor bell_sensor --culprit kitten
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py --place porch --sensor beam_sensor --culprit puppy
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py --all
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py --json
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py --asp
    python storyworlds/worlds/gpt-5.4/position_sensor_flea_conflict_mystery.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "animal"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        animal = {"kitten", "cat", "puppy", "dog"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


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
class Place:
    id: str
    label: str
    intro: str
    nook: str
    entry: str
    indoor: bool = True
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
class SensorCfg:
    id: str
    label: str
    phrase: str
    detects: set[str] = field(default_factory=set)
    works_in: set[str] = field(default_factory=set)
    sound: str = ""
    setup: str = ""
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
class CulpritCfg:
    id: str
    label: str
    animal_type: str
    size: str
    enters: str
    scratch: str
    reveal: str
    remedy: str
    places: set[str] = field(default_factory=set)
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
class MarkerCfg:
    id: str
    label: str
    phrase: str
    place_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


def _r_shift_marker(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    marker = world.get("marker")
    if culprit.meters["inside"] < THRESHOLD or culprit.meters["itch"] < THRESHOLD:
        return out
    sig = ("shift", culprit.id, int(marker.meters["moved"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    marker.meters["moved"] += 1
    marker.meters["in_position"] = 0.0
    culprit.meters["scratched"] += 1
    out.append("__shift__")
    return out


def _r_trip_sensor(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    sensor = world.get("sensor")
    if culprit.meters["inside"] < THRESHOLD or sensor.meters["armed"] < THRESHOLD:
        return out
    if not sensor.attrs.get("works_here", False):
        return out
    if culprit.attrs.get("size") not in sensor.attrs.get("detects", set()):
        return out
    sig = ("trip", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sensor.meters["beep"] += 1
    sensor.memes["proof"] += 1
    out.append("__beep__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="shift_marker", tag="physical", apply=_r_shift_marker),
    Rule(name="trip_sensor", tag="physical", apply=_r_trip_sensor),
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
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def sensor_can_catch(place: Place, sensor: SensorCfg, culprit: CulpritCfg) -> bool:
    return place.id in culprit.places and place.id in sensor.works_in and culprit.size in sensor.detects


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for sensor_id, sensor in SENSORS.items():
            for culprit_id, culprit in CULPRITS.items():
                if sensor_can_catch(place, sensor, culprit):
                    combos.append((place_id, sensor_id, culprit_id))
    return combos


def explain_rejection(place: Place, sensor: SensorCfg, culprit: CulpritCfg) -> str:
    if place.id not in culprit.places:
        return (
            f"(No story: {culprit.label} cannot reasonably slip into {place.label}, "
            f"so it could not disturb the mystery there.)"
        )
    if place.id not in sensor.works_in:
        return (
            f"(No story: {sensor.label} is not a good sensor for {place.label}. "
            f"Pick a sensor that works in that place.)"
        )
    if culprit.size not in sensor.detects:
        return (
            f"(No story: {sensor.label} would miss a {culprit.size} culprit like "
            f"{culprit.label}, so the mystery would not be solved honestly.)"
        )
    return "(No story: this sensor cannot reasonably catch that culprit in that place.)"


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    sensor = SENSORS[params.sensor]
    culprit = CULPRITS[params.culprit]
    return "resolved" if sensor_can_catch(place, sensor, culprit) else "unsolved"


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------
def initial_disturbance(world: World) -> None:
    culprit = world.get("culprit")
    culprit.meters["inside"] = 1.0
    culprit.meters["itch"] = 1.0
    propagate(world, narrate=False)
    culprit.meters["inside"] = 0.0


def trigger_night_watch(world: World) -> None:
    culprit = world.get("culprit")
    culprit.meters["inside"] = 1.0
    culprit.meters["itch"] = 1.0
    propagate(world, narrate=False)


# ---------------------------------------------------------------------------
# Prose beats
# ---------------------------------------------------------------------------
def introduce(world: World, finder: Entity, accused: Entity, place: Place, marker: MarkerCfg) -> None:
    for child in (finder, accused):
        child.memes["curious"] += 1
        child.memes["joy"] += 1
    world.say(
        f"{finder.id} and {accused.id} had made {place.intro}. "
        f"In the middle of it they kept {marker.phrase}, and every night they left it {marker.place_text}."
    )
    world.say(
        f"They liked to whisper that the place had rules of its own, the sort of rules a mystery might use."
    )


def discover(world: World, finder: Entity, accused: Entity, marker: MarkerCfg) -> None:
    marker_ent = world.get("marker")
    if marker_ent.meters["moved"] >= THRESHOLD:
        world.say(
            f"The next morning, {finder.id} ducked inside and stopped short. "
            f"{marker.phrase.capitalize()} was not in the same position as yesterday."
        )
        world.say(
            f'"{accused.id}, did you move it?" {finder.id} asked. The room felt suddenly still.'
        )


def accuse(world: World, finder: Entity, accused: Entity) -> None:
    finder.memes["suspicion"] += 1
    accused.memes["hurt"] += 1
    finder.memes["conflict"] += 1
    accused.memes["conflict"] += 1
    world.say(
        f'"I did not," said {accused.id}, cheeks hot. "You always think it was me."'
    )
    world.say(
        f"For a minute the mystery turned into a quarrel, and that felt worse than the moved clue."
    )


def decide_trap(world: World, finder: Entity, accused: Entity, place: Place, sensor: SensorCfg) -> None:
    sensor_ent = world.get("sensor")
    sensor_ent.meters["armed"] = 1.0
    world.say(
        f"{accused.id} crossed {accused.pronoun('possessive')} arms, then took a breath. "
        f'"If we want the truth, let\'s use {sensor.phrase}," {accused.pronoun()} said.'
    )
    world.say(
        f"They tucked the {sensor.label} {place.entry}. {sensor.setup}"
    )
    world.facts["sensor_armed"] = True


def night_watch(world: World, finder: Entity, accused: Entity, place: Place, sensor: SensorCfg) -> None:
    world.say(
        f"That evening they hid nearby and watched the dark mouth of {place.nook}. "
        f"Nobody spoke above a whisper."
    )
    trigger_night_watch(world)
    sensor_ent = world.get("sensor")
    if sensor_ent.meters["beep"] >= THRESHOLD:
        world.say(
            f"After a long wait, {sensor.sound} The sensor gave a tiny cry in the dark."
        )


def reveal(world: World, finder: Entity, accused: Entity, culprit: CulpritCfg, marker: MarkerCfg) -> None:
    culprit_ent = world.get("culprit")
    marker_ent = world.get("marker")
    if culprit_ent.meters["scratched"] >= THRESHOLD and marker_ent.meters["moved"] >= THRESHOLD:
        world.say(
            f"Out crept {culprit.reveal}. It stopped to scratch hard at its neck, where one little flea kept bothering it."
        )
        world.say(
            f"With that wiggly scratching, it bumped {marker.phrase} and pushed it out of place all over again."
        )
        world.facts["proof_found"] = True


def repair_conflict(world: World, finder: Entity, accused: Entity, culprit: CulpritCfg, parent: Entity, marker: MarkerCfg) -> None:
    finder.memes["conflict"] = 0.0
    accused.memes["conflict"] = 0.0
    finder.memes["guilt"] += 1
    finder.memes["relief"] += 1
    accused.memes["relief"] += 1
    accused.memes["trust"] += 1
    world.say(
        f'{finder.id} looked at {accused.id} at once. "I am sorry," {finder.pronoun()} said. '
        f'"I blamed you before we had clues."'
    )
    world.say(
        f'{accused.id} nodded. "Now we know," {accused.pronoun()} said, and the hard feeling between them melted.'
    )
    world.say(
        f"{parent.label_word.capitalize()} helped with {culprit.remedy}, and together they set {marker.phrase} back in its right position."
    )
    world.say(
        f"After that, the mystery place felt peaceful again. If anything seemed strange, the children promised to look for proof before starting a conflict."
    )


def tell(
    place: Place,
    sensor: SensorCfg,
    culprit_cfg: CulpritCfg,
    marker: MarkerCfg,
    finder_name: str = "Mina",
    finder_gender: str = "girl",
    accused_name: str = "Jonah",
    accused_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    finder = world.add(Entity(
        id=finder_name,
        kind="character",
        type=finder_gender,
        role="finder",
        traits=["curious"],
        attrs={},
    ))
    accused = world.add(Entity(
        id=accused_name,
        kind="character",
        type=accused_gender,
        role="accused",
        traits=["careful"],
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
    marker_ent = world.add(Entity(
        id="marker",
        kind="thing",
        type="marker",
        label=marker.label,
        attrs={},
    ))
    marker_ent.meters["in_position"] = 1.0
    sensor_ent = world.add(Entity(
        id="sensor",
        kind="thing",
        type="sensor",
        label=sensor.label,
        attrs={
            "works_here": place.id in sensor.works_in,
            "detects": set(sensor.detects),
        },
    ))
    sensor_ent.meters["armed"] = 0.0
    culprit_ent = world.add(Entity(
        id="culprit",
        kind="animal",
        type=culprit_cfg.animal_type,
        label=culprit_cfg.label,
        attrs={
            "size": culprit_cfg.size,
            "places": set(culprit_cfg.places),
        },
    ))
    culprit_ent.meters["inside"] = 0.0
    culprit_ent.meters["itch"] = 1.0
    culprit_ent.meters["scratched"] = 0.0

    world.facts.update(
        place=place,
        sensor_cfg=sensor,
        culprit_cfg=culprit_cfg,
        marker_cfg=marker,
        finder=finder,
        accused=accused,
        parent=parent,
        proof_found=False,
        sensor_armed=False,
    )

    initial_disturbance(world)

    introduce(world, finder, accused, place, marker)
    world.para()
    discover(world, finder, accused, marker)
    accuse(world, finder, accused)
    world.para()
    decide_trap(world, finder, accused, place, sensor)
    night_watch(world, finder, accused, place, sensor)
    reveal(world, finder, accused, culprit_cfg, marker)
    world.para()
    repair_conflict(world, finder, accused, culprit_cfg, parent, marker)

    world.facts.update(
        marker_moved=world.get("marker").meters["moved"] >= THRESHOLD,
        sensor_beeped=world.get("sensor").meters["beep"] >= THRESHOLD,
        resolved=world.facts["proof_found"],
        outcome="resolved" if world.facts["proof_found"] else "unsolved",
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "fort": Place(
        id="fort",
        label="the blanket fort",
        intro="a blanket fort that looked like a moonlit detective office",
        nook="the low flap of the fort",
        entry="beside the low flap",
        indoor=True,
        tags={"fort", "mystery"},
    ),
    "porch": Place(
        id="porch",
        label="the screened porch",
        intro="a screened porch they called the Night Clue Club",
        nook="the wicker chair by the screen",
        entry="under the wicker chair",
        indoor=False,
        tags={"porch", "mystery"},
    ),
    "shed": Place(
        id="shed",
        label="the potting shed",
        intro="a potting shed that smelled of rain boots and secrets",
        nook="the shelf by the cracked door",
        entry="by the cracked door",
        indoor=False,
        tags={"shed", "mystery"},
    ),
}

SENSORS = {
    "bell_sensor": SensorCfg(
        id="bell_sensor",
        label="bell sensor",
        phrase="a little bell sensor",
        detects={"small", "medium"},
        works_in={"fort", "porch", "shed"},
        sound="Ting-ting!",
        setup="Even a quiet visitor would have to nudge it to get through.",
        tags={"sensor", "bell"},
    ),
    "beam_sensor": SensorCfg(
        id="beam_sensor",
        label="beam sensor",
        phrase="a tiny light-beam sensor",
        detects={"small"},
        works_in={"fort"},
        sound="Pip!",
        setup="A body crossing the narrow beam would break the light and wake the mystery.",
        tags={"sensor", "beam"},
    ),
    "mat_sensor": SensorCfg(
        id="mat_sensor",
        label="floor mat sensor",
        phrase="a soft floor sensor mat",
        detects={"medium"},
        works_in={"fort", "shed"},
        sound="Bloop!",
        setup="Anything heavy enough to step on it would make it murmur.",
        tags={"sensor", "mat"},
    ),
}

CULPRITS = {
    "kitten": CulpritCfg(
        id="kitten",
        label="the neighbor's kitten",
        animal_type="kitten",
        size="small",
        enters="slipped through the gap as quietly as a shadow",
        scratch="scratched at its collar",
        reveal="the neighbor's kitten, bright-eyed and dusty",
        remedy="a gentle flea comb and a check from a grown-up",
        places={"fort", "porch", "shed"},
        tags={"kitten", "flea", "pet"},
    ),
    "puppy": CulpritCfg(
        id="puppy",
        label="the puppy from next door",
        animal_type="puppy",
        size="medium",
        enters="blundered in with a soft snuffle",
        scratch="scratched behind one ear",
        reveal="the puppy from next door, all paws and surprise",
        remedy="a warm bath and flea soap from a grown-up",
        places={"fort", "porch"},
        tags={"puppy", "flea", "pet"},
    ),
    "cat": CulpritCfg(
        id="cat",
        label="the old porch cat",
        animal_type="cat",
        size="small",
        enters="slid through the opening with whiskers first",
        scratch="scratched under its chin",
        reveal="the old porch cat with one torn ear",
        remedy="a careful flea comb while a grown-up kept it calm",
        places={"porch", "shed"},
        tags={"cat", "flea", "pet"},
    ),
}

MARKERS = {
    "moon_pin": MarkerCfg(
        id="moon_pin",
        label="moon pin",
        phrase="their silver moon pin",
        place_text="balanced at the center of the clue map",
        tags={"marker", "moon"},
    ),
    "red_arrow": MarkerCfg(
        id="red_arrow",
        label="red arrow",
        phrase="their red arrow marker",
        place_text="pointing exactly at the secret X on the floor map",
        tags={"marker", "map"},
    ),
    "brass_key": MarkerCfg(
        id="brass_key",
        label="brass key",
        phrase="their little brass key",
        place_text="resting on the edge of the treasure notebook",
        tags={"marker", "key"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Ruby", "Nora", "June", "Ava", "Pia"]
BOY_NAMES = ["Jonah", "Eli", "Max", "Theo", "Owen", "Finn", "Sam", "Leo"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    sensor: str
    culprit: str
    marker: str
    finder: str
    finder_gender: str
    accused: str
    accused_gender: str
    parent: str
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
    "sensor": [
        (
            "What is a sensor?",
            "A sensor is something that notices a change, like movement or pressure, and gives a signal. It can help people learn what really happened."
        )
    ],
    "flea": [
        (
            "What is a flea?",
            "A flea is a tiny jumping bug that can bother animals by biting their skin. That can make a pet itchy and scratch a lot."
        )
    ],
    "apology": [
        (
            "Why is it good to apologize after blaming someone unfairly?",
            "An apology helps mend hurt feelings and shows you want to tell the truth. It is a way of fixing the conflict after you learn you were wrong."
        )
    ],
    "proof": [
        (
            "Why should you look for proof in a mystery?",
            "Proof helps you know what is true instead of only guessing. That keeps a mystery from turning into an unfair argument."
        )
    ],
    "pet": [
        (
            "What should you do if a pet might have fleas?",
            "Tell a grown-up so the pet can be checked and helped. Grown-ups can use the right comb, soap, or medicine."
        )
    ],
}
KNOWLEDGE_ORDER = ["sensor", "flea", "proof", "apology", "pet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    sensor = f["sensor_cfg"]
    culprit = f["culprit_cfg"]
    marker = f["marker_cfg"]
    finder = f["finder"]
    accused = f["accused"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "position", "sensor", and "flea".',
        f"Tell a gentle conflict mystery where {finder.id} thinks {accused.id} moved {marker.phrase}, but a {sensor.label} in {place.label} reveals the real culprit.",
        f"Write a child-facing story about a clue in the wrong position, a quarrel between two children, and {culprit.label} solving the mystery by accident.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    accused = f["accused"]
    parent = f["parent"]
    place = f["place"]
    sensor = f["sensor_cfg"]
    culprit = f["culprit_cfg"]
    marker = f["marker_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery at the beginning?",
            f"The mystery was that {marker.phrase} was no longer where the children had left it. Its position had changed during the night, so {finder.id} thought someone had touched it."
        ),
        (
            f"Why did {finder.id} and {accused.id} start arguing?",
            f"They started arguing because {finder.id} guessed that {accused.id} had moved the clue. The mystery became a conflict when the blame came before any proof."
        ),
        (
            f"Why did the children use a {sensor.label}?",
            f"They wanted the truth instead of another guess, so they set a {sensor.label} by the entrance. The sensor could notice a visitor and show who was really coming in."
        ),
    ]
    if f.get("sensor_beeped"):
        qa.append(
            (
                "What did the sensor reveal?",
                f"It revealed that {culprit.label} was the one slipping into {place.label}. When the sensor sounded, the children could see the real visitor for themselves."
            )
        )
    if f.get("resolved"):
        qa.append(
            (
                f"How did the flea matter in the story?",
                f"The flea made the little animal itchy, so it kept scratching. That scratching bumped {marker.phrase} out of place, which is why the mystery kept happening."
            )
        )
        qa.append(
            (
                f"How was the conflict solved?",
                f"{finder.id} apologized for blaming {accused.id} too soon, and the hurt feelings eased. Then {parent.label_word} helped care for the itchy pet, and the children put the clue back in the right position."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sensor", "proof", "apology", "pet", "flea"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {}
            for key, value in e.attrs.items():
                if isinstance(value, set):
                    shown[key] = sorted(value)
                else:
                    shown[key] = value
            bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="fort",
        sensor="bell_sensor",
        culprit="kitten",
        marker="moon_pin",
        finder="Mina",
        finder_gender="girl",
        accused="Jonah",
        accused_gender="boy",
        parent="mother",
    ),
    StoryParams(
        place="porch",
        sensor="bell_sensor",
        culprit="puppy",
        marker="red_arrow",
        finder="Ruby",
        finder_gender="girl",
        accused="Leo",
        accused_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="shed",
        sensor="bell_sensor",
        culprit="cat",
        marker="brass_key",
        finder="Theo",
        finder_gender="boy",
        accused="Nora",
        accused_gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="fort",
        sensor="beam_sensor",
        culprit="kitten",
        marker="red_arrow",
        finder="Lila",
        finder_gender="girl",
        accused="Max",
        accused_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="fort",
        sensor="mat_sensor",
        culprit="puppy",
        marker="moon_pin",
        finder="Eli",
        finder_gender="boy",
        accused="June",
        accused_gender="girl",
        parent="mother",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_enter(P, C) :- place(P), culprit(C), allowed(C, P).
sensor_works(P, S) :- place(P), sensor(S), works_in(S, P).
sensor_catches(S, C) :- sensor(S), culprit(C), detects(S, Z), size(C, Z).

valid(P, S, C) :- can_enter(P, C), sensor_works(P, S), sensor_catches(S, C).

outcome(resolved) :- chosen_place(P), chosen_sensor(S), chosen_culprit(C), valid(P, S, C).
outcome(unsolved) :- chosen_place(P), chosen_sensor(S), chosen_culprit(C), not valid(P, S, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for sensor_id, sensor in SENSORS.items():
        lines.append(asp.fact("sensor", sensor_id))
        for place_id in sorted(sensor.works_in):
            lines.append(asp.fact("works_in", sensor_id, place_id))
        for size in sorted(sensor.detects):
            lines.append(asp.fact("detects", sensor_id, size))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("size", culprit_id, culprit.size))
        for place_id in sorted(culprit.places):
            lines.append(asp.fact("allowed", culprit_id, place_id))
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
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_sensor", params.sensor),
            asp.fact("chosen_culprit", params.culprit),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="")
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a moved clue, a sensor trap, and a gentle mystery conflict."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sensor", choices=SENSORS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--marker", choices=MARKERS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.sensor is not None and args.culprit is not None:
        place = PLACES[args.place]
        sensor = SENSORS[args.sensor]
        culprit = CULPRITS[args.culprit]
        if not sensor_can_catch(place, sensor, culprit):
            raise StoryError(explain_rejection(place, sensor, culprit))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sensor is None or combo[1] == args.sensor)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sensor_id, culprit_id = rng.choice(sorted(combos))
    marker_id = args.marker or rng.choice(sorted(MARKERS))
    finder, finder_gender = _pick_child(rng)
    accused, accused_gender = _pick_child(rng, avoid=finder)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        sensor=sensor_id,
        culprit=culprit_id,
        marker=marker_id,
        finder=finder,
        finder_gender=finder_gender,
        accused=accused,
        accused_gender=accused_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.sensor not in SENSORS:
        raise StoryError(f"(Unknown sensor: {params.sensor})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.marker not in MARKERS:
        raise StoryError(f"(Unknown marker: {params.marker})")

    place = PLACES[params.place]
    sensor = SENSORS[params.sensor]
    culprit = CULPRITS[params.culprit]
    if not sensor_can_catch(place, sensor, culprit):
        raise StoryError(explain_rejection(place, sensor, culprit))

    world = tell(
        place=place,
        sensor=sensor,
        culprit_cfg=culprit,
        marker=MARKERS[params.marker],
        finder_name=params.finder,
        finder_gender=params.finder_gender,
        accused_name=params.accused,
        accused_gender=params.accused_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (place, sensor, culprit) combos:\n")
        for place_id, sensor_id, culprit_id in combos:
            print(f"  {place_id:7} {sensor_id:12} {culprit_id}")
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
            header = f"### {p.finder} & {p.accused}: {p.place}, {p.sensor}, {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
