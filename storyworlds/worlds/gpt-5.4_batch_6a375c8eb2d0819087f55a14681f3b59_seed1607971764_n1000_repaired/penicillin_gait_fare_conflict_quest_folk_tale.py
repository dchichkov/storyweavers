#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/penicillin_gait_fare_conflict_quest_folk_tale.py
==============================================================================

A standalone story world for a small folk-tale domain: a child sees an elder's
hurt, limping gait, sets out on a quest for penicillin, and meets a conflict at
the river ferry over the fare.

The world model prefers a grounded problem/fix pair:
- the patient must have an infection serious enough that penicillin is a
  reasonable medicine,
- the child must need the ferry,
- and the way of paying the fare must be something the ferryman would honestly
  accept.

The story then branches by urgency and delay:
- if the child settles the fare quickly enough, the medicine returns in time and
  the ending is bright;
- if too much time is lost, the patient is safe but weak, and the ending is
  quieter and sadder.

Run it
------
    python storyworlds/worlds/gpt-5.4/penicillin_gait_fare_conflict_quest_folk_tale.py
    python storyworlds/worlds/gpt-5.4/penicillin_gait_fare_conflict_quest_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/penicillin_gait_fare_conflict_quest_folk_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/penicillin_gait_fare_conflict_quest_folk_tale.py --qa
    python storyworlds/worlds/gpt-5.4/penicillin_gait_fare_conflict_quest_folk_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/penicillin_gait_fare_conflict_quest_folk_tale.py --asp
    python storyworlds/worlds/gpt-5.4/penicillin_gait_fare_conflict_quest_folk_tale.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man", "ferryman"}
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
            "ferryman": "ferryman",
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
    home: str
    river: str
    far_bank: str
    clinic: str
    image: str
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
class Infection:
    id: str
    wound: str
    limb: str
    gait_line: str
    reason: str
    severity: int
    needs_penicillin: bool = True
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
class FareMethod:
    id: str
    label: str
    accepted: bool
    quick: bool
    settle_text: str
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
class FerryMood:
    id: str
    stern_text: str
    soften_text: str
    mercy_text: str
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


def _r_infection_hurts(world: World) -> list[str]:
    out: list[str] = []
    patient = world.get("patient")
    if patient.meters["infected"] < THRESHOLD:
        return out
    sig = ("infection_hurts", patient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient.meters["pain"] += 1
    patient.meters["slow_gait"] += 1
    patient.memes["worry"] += 1
    seeker = world.get("seeker")
    seeker.memes["concern"] += 1
    out.append("__gait__")
    return out


def _r_delay_worsens(world: World) -> list[str]:
    out: list[str] = []
    patient = world.get("patient")
    if patient.meters["delay"] < THRESHOLD:
        return out
    sig = ("delay_worsens", patient.id, int(patient.meters["delay"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient.meters["fever"] += 1
    patient.memes["worry"] += 1
    seeker = world.get("seeker")
    seeker.memes["urgency"] += 1
    out.append("__fever__")
    return out


def _r_medicine_heals(world: World) -> list[str]:
    out: list[str] = []
    patient = world.get("patient")
    satchel = world.get("medicine")
    if satchel.meters["delivered"] < THRESHOLD:
        return out
    sig = ("medicine_heals", patient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    patient.meters["infected"] = 0.0
    patient.meters["pain"] = 0.0
    patient.meters["fever"] = 0.0
    patient.meters["slow_gait"] = 0.0
    patient.memes["relief"] += 1
    seeker = world.get("seeker")
    seeker.memes["relief"] += 1
    out.append("__healed__")
    return out


CAUSAL_RULES = [
    Rule(name="infection_hurts", tag="physical", apply=_r_infection_hurts),
    Rule(name="delay_worsens", tag="physical", apply=_r_delay_worsens),
    Rule(name="medicine_heals", tag="physical", apply=_r_medicine_heals),
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


def valid_fare(method: FareMethod) -> bool:
    return method.accepted


def medicine_is_reasonable(infection: Infection) -> bool:
    return infection.needs_penicillin and infection.severity >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for infection_id, infection in INFECTIONS.items():
            if not medicine_is_reasonable(infection):
                continue
            for fare_id, fare in FARE_METHODS.items():
                if not valid_fare(fare):
                    continue
                for mood_id in FERRY_MOODS:
                    combos.append((setting_id, infection_id, fare_id, mood_id))
    return combos


def predicted_ending(infection: Infection, fare: FareMethod, delay: int) -> str:
    total_delay = delay + (0 if fare.quick else 1)
    if total_delay <= infection.severity - 1:
        return "timely"
    return "late"


def predict_world(infection: Infection, fare: FareMethod, delay: int) -> dict:
    total_delay = delay + (0 if fare.quick else 1)
    return {"total_delay": total_delay, "ending": predicted_ending(infection, fare, delay)}


def introduce(world: World, seeker: Entity, patient: Entity) -> None:
    world.say(
        f"In {world.setting.home}, where {world.setting.image}, there lived {seeker.id} "
        f"and {seeker.pronoun('possessive')} {patient.label_word}, {patient.id}."
    )


def show_hurt(world: World, patient: Entity, infection: Infection) -> None:
    patient.meters["infected"] += 1
    world.facts["gait_phrase"] = infection.gait_line
    propagate(world, narrate=False)
    world.say(
        f"One morning, {patient.id} had {infection.wound}, {infection.reason}. "
        f"When {patient.pronoun()} crossed the yard, {patient.pronoun('possessive')} "
        f"gait had grown {infection.gait_line}."
    )


def healer_advice(world: World, seeker: Entity, patient: Entity, infection: Infection) -> None:
    seeker.memes["duty"] += 1
    world.say(
        f'The herb-wife touched the {infection.limb} and shook her head. '
        f'"This is beyond rosemary and honey," she said. "From the stone clinic '
        f'across {world.setting.river}, bring back penicillin before the sun leans low."'
    )


def vow(world: World, seeker: Entity) -> None:
    seeker.memes["courage"] += 1
    world.say(
        f'{seeker.id} tied a small satchel at {seeker.pronoun("possessive")} side and said, '
        f'"Then I will go at once."'
    )


def reach_ferry(world: World, seeker: Entity, ferryman: Entity) -> None:
    world.say(
        f"So {seeker.id} came to the ferry at {world.setting.river}, where the boat "
        f"rocked against its rope and {ferryman.id} watched the water."
    )


def conflict(world: World, seeker: Entity, ferryman: Entity, mood: FerryMood) -> None:
    seeker.memes["frustration"] += 1
    ferryman.memes["duty"] += 1
    world.say(
        f'"I must cross to {world.setting.clinic}," said {seeker.id}. '
        f'{ferryman.id} answered, "{mood.stern_text} The fare must be paid."'
    )


def plead(world: World, seeker: Entity, patient: Entity, ferryman: Entity, infection: Infection) -> None:
    pred = predict_world(INFECTIONS[world.facts["infection_id"]], FARE_METHODS[world.facts["fare_id"]], world.facts["delay"])
    world.facts["predicted_total_delay"] = pred["total_delay"]
    world.say(
        f'{seeker.id} told him of {patient.id}, of the sore {infection.limb}, and of the '
        f"slow gait that had come from pain. For a moment even the river seemed to listen."
    )


def settle_fare(world: World, seeker: Entity, ferryman: Entity, fare: FareMethod, mood: FerryMood) -> None:
    ferryman.memes["softened"] += 1
    seeker.meters["fare_paid"] += 1
    world.say(
        f"{fare.settle_text} {ferryman.id}'s face changed, and he said, "
        f'"{mood.soften_text}"'
    )


def cross_and_fetch(world: World, seeker: Entity, infection: Infection, fare: FareMethod) -> None:
    medicine = world.get("medicine")
    seeker.meters["crossed"] += 1
    medicine.meters["fetched"] += 1
    world.say(
        f"The ferry slid over the black-green water to {world.setting.far_bank}. "
        f"{seeker.id} ran up to {world.setting.clinic}, where a quiet doctor wrapped "
        f"a bottle of penicillin in cloth and warned, \"Bring it straight home.\""
    )


def return_with_delay(world: World, seeker: Entity, patient: Entity, fare: FareMethod, delay: int) -> None:
    patient.meters["delay"] += float(delay + (0 if fare.quick else 1))
    propagate(world, narrate=False)
    world.say(
        f"Back over the river came {seeker.id}, holding the little bottle close "
        f"through every step and splash."
    )
    if patient.meters["fever"] >= THRESHOLD:
        world.say(
            f"But the sun had already drooped behind the reeds, and {patient.id} lay "
            f"hot and pale beneath a blanket."
        )


def heal_in_time(world: World, seeker: Entity, patient: Entity, ferryman: Entity, mood: FerryMood) -> None:
    medicine = world.get("medicine")
    medicine.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The doctor from the village mixed the penicillin and gave the first dose "
        f"before night had fully closed."
    )
    world.say(
        f"By dawn, {patient.id}'s brow was cool. When {patient.pronoun()} stood in the doorway, "
        f"{patient.pronoun('possessive')} gait was easy again, and the yard no longer looked too wide."
    )
    world.say(
        f"From the river came a call: {ferryman.id} lifted his pole in salute, and {seeker.id} "
        f"waved back, knowing the quest had mended more than one fear."
    )


def heal_late(world: World, seeker: Entity, patient: Entity, ferryman: Entity, mood: FerryMood) -> None:
    medicine = world.get("medicine")
    medicine.meters["delivered"] += 1
    propagate(world, narrate=False)
    patient.meters["weakness"] += 1
    world.say(
        f"The penicillin was given at last, and it turned the sickness away, but the long day "
        f"had wrung the strength from {patient.id}."
    )
    world.say(
        f"For many mornings after, {patient.pronoun()} walked with a careful gait and leaned on "
        f"a stick by the door while the swallows wheeled above the river."
    )
    world.say(
        f"{seeker.id} never forgot how a small quarrel over fare can grow heavy when time is thin, "
        f"and {ferryman.id} thereafter kept one place in his boat for urgent need."
    )


def tell(
    setting: Setting,
    infection: Infection,
    fare: FareMethod,
    mood: FerryMood,
    seeker_name: str = "Mira",
    seeker_type: str = "girl",
    patient_name: str = "Grandmother Brin",
    patient_type: str = "grandmother",
    ferryman_name: str = "Old Taren",
    delay: int = 0,
) -> World:
    world = World(setting)
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        role="seeker",
        traits=["brave", "small"],
        attrs={},
    ))
    patient = world.add(Entity(
        id=patient_name,
        kind="character",
        type=patient_type,
        role="patient",
        label=patient_type,
        traits=["kind", "elder"],
        attrs={},
    ))
    ferryman = world.add(Entity(
        id=ferryman_name,
        kind="character",
        type="ferryman",
        role="ferryman",
        label="the ferryman",
        traits=["watchful"],
        attrs={},
    ))
    world.add(Entity(
        id="medicine",
        kind="thing",
        type="medicine",
        label="penicillin",
        attrs={},
    ))
    world.facts["infection_id"] = infection.id
    world.facts["fare_id"] = fare.id
    world.facts["delay"] = delay
    world.facts["setting_id"] = setting.id
    world.facts["mood_id"] = mood.id

    introduce(world, seeker, patient)
    show_hurt(world, patient, infection)
    healer_advice(world, seeker, patient, infection)
    vow(world, seeker)

    world.para()
    reach_ferry(world, seeker, ferryman)
    conflict(world, seeker, ferryman, mood)
    plead(world, seeker, patient, ferryman, infection)
    settle_fare(world, seeker, ferryman, fare, mood)

    world.para()
    cross_and_fetch(world, seeker, infection, fare)
    return_with_delay(world, seeker, patient, fare, delay)

    world.para()
    ending = predicted_ending(infection, fare, delay)
    if ending == "timely":
        heal_in_time(world, seeker, patient, ferryman, mood)
    else:
        heal_late(world, seeker, patient, ferryman, mood)

    world.facts.update(
        seeker=seeker,
        patient=patient,
        ferryman=ferryman,
        infection=infection,
        fare=fare,
        mood=mood,
        ending=ending,
        total_delay=delay + (0 if fare.quick else 1),
        medicine_needed=True,
        medicine_name="penicillin",
    )
    return world


SETTINGS = {
    "reedbank": Setting(
        id="reedbank",
        home="the village of Reedbank",
        river="the Willow River",
        far_bank="the eastern bank",
        clinic="the stone clinic under the hill",
        image="willows combed the wind and geese cried at dusk",
        tags={"river", "village"},
    ),
    "fogford": Setting(
        id="fogford",
        home="the hamlet of Fogford",
        river="the Gray River",
        far_bank="the misty bank",
        clinic="the white clinic by the mill",
        image="the fog lay low in the fields and the bells sounded soft",
        tags={"river", "mist"},
    ),
    "sunmeadow": Setting(
        id="sunmeadow",
        home="the village of Sunmeadow",
        river="the Brightwater",
        far_bank="the willow bank",
        clinic="the hill clinic with blue shutters",
        image="larks rose from the grass and the river flashed like tin",
        tags={"river", "meadow"},
    ),
}

INFECTIONS = {
    "thorn_heel": Infection(
        id="thorn_heel",
        wound="a thorn-deep cut in her heel",
        limb="heel",
        gait_line="short and uneven",
        reason="made angry by dirt from the sheep path",
        severity=2,
        needs_penicillin=True,
        tags={"heel", "infection", "gait"},
    ),
    "splinter_ankle": Infection(
        id="splinter_ankle",
        wound="a swollen gash above his ankle",
        limb="ankle",
        gait_line="slow and crooked",
        reason="that had festered after chopping wood",
        severity=3,
        needs_penicillin=True,
        tags={"ankle", "infection", "gait"},
    ),
    "stone_foot": Infection(
        id="stone_foot",
        wound="a cut along her foot",
        limb="foot",
        gait_line="careful and limping",
        reason="after she slipped on the river stones",
        severity=2,
        needs_penicillin=True,
        tags={"foot", "infection", "gait"},
    ),
    "sore_hand": Infection(
        id="sore_hand",
        wound="a sore on his hand",
        limb="hand",
        gait_line="unchanged",
        reason="from a cracked handle",
        severity=1,
        needs_penicillin=False,
        tags={"hand"},
    ),
}

FARE_METHODS = {
    "coin": FareMethod(
        id="coin",
        label="a silver coin",
        accepted=True,
        quick=True,
        settle_text="From a hemmed pocket, the child brought out a silver coin and paid the fare.",
        qa_text="The child paid the fare with a silver coin, so the boat left at once.",
        tags={"coin", "fare"},
    ),
    "net_mending": FareMethod(
        id="net_mending",
        label="mending the ferry net",
        accepted=True,
        quick=False,
        settle_text="Seeing a torn net in the boat, the child knelt and mended it with quick fingers before paying the fare in work.",
        qa_text="The child settled the fare by mending the ferryman's torn net, which helped but cost precious time.",
        tags={"work", "fare"},
    ),
    "song": FareMethod(
        id="song",
        label="a song",
        accepted=False,
        quick=False,
        settle_text="The child offered only a song for the fare.",
        qa_text="The child tried to offer only a song, but the ferryman would not count that as real fare.",
        tags={"song"},
    ),
    "berries": FareMethod(
        id="berries",
        label="a basket of berries",
        accepted=True,
        quick=True,
        settle_text="The child opened a basket of late berries, and the ferryman accepted them as the fare for the crossing.",
        qa_text="The child used a basket of berries as the fare, and the ferryman agreed right away.",
        tags={"berries", "fare"},
    ),
}

FERRY_MOODS = {
    "stern": FerryMood(
        id="stern",
        stern_text="River law is river law.",
        soften_text="Very well. Need has its own weight. Step in.",
        mercy_text="I cannot leave a sick elder waiting.",
        tags={"strict"},
    ),
    "weary": FerryMood(
        id="weary",
        stern_text="Oars crack and ropes fray; I cannot row for nothing.",
        soften_text="You have paid honestly. Climb aboard.",
        mercy_text="Even a tired man must bend before true need.",
        tags={"weary"},
    ),
    "gruff": FerryMood(
        id="gruff",
        stern_text="No one crosses this water without proper fare.",
        soften_text="A fair fare for a fair crossing. In you come.",
        mercy_text="Hush now. I know what haste means.",
        tags={"gruff"},
    ),
}

GIRL_NAMES = ["Mira", "Tala", "Elsa", "Nella", "Bryn", "Lina", "Anya", "Pia"]
BOY_NAMES = ["Ivo", "Tomas", "Niko", "Pavel", "Soren", "Milan", "Eli", "Joren"]
GRANDMOTHERS = ["Grandmother Brin", "Grandmother Elow", "Grandmother Sela"]
GRANDFATHERS = ["Grandfather Orrin", "Grandfather Vale", "Grandfather Toma"]
FERRYMEN = ["Old Taren", "Moss Rowan", "Ferryman Hale"]


@dataclass
class StoryParams:
    setting: str
    infection: str
    fare: str
    mood: str
    seeker_name: str
    seeker_type: str
    patient_name: str
    patient_type: str
    ferryman_name: str
    delay: int = 0
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
    "penicillin": [
        (
            "What is penicillin?",
            "Penicillin is a medicine that helps fight some kinds of harmful bacteria. Doctors use it when an infection needs stronger help than rest alone."
        )
    ],
    "gait": [
        (
            "What is a gait?",
            "A gait is the way someone walks. Pain in a foot, heel, or ankle can change a person's gait and make it look slow, uneven, or limping."
        )
    ],
    "fare": [
        (
            "What does fare mean in a ferry story?",
            "Fare is the payment you give for a ride. On a ferry, the fare might be money or another agreed payment before the boat carries you across."
        )
    ],
    "ferry": [
        (
            "What is a ferry?",
            "A ferry is a boat that carries people or things across water. It goes back and forth between two banks."
        )
    ],
    "infection": [
        (
            "Why can an infected cut be dangerous?",
            "An infected cut can become swollen, painful, and hot. If it gets worse, a doctor may need to treat it quickly so the sickness does not spread."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey taken for an important reason. In folk tales, the traveler usually faces a problem on the way and must keep going bravely."
        )
    ],
}
KNOWLEDGE_ORDER = ["penicillin", "gait", "fare", "ferry", "infection", "quest"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    patient = f["patient"]
    infection = f["infection"]
    fare = f["fare"]
    ending = f["ending"]
    base = (
        f'Write a short folk tale for a 3-to-5-year-old that uses the words "penicillin", '
        f'"gait", and "fare", and includes a quest and a conflict at a river ferry.'
    )
    if ending == "timely":
        return [
            base,
            f"Tell a gentle folk tale where {seeker.id} hurries across a river to bring penicillin for {patient.id}, whose gait has grown {infection.gait_line}, and settles the fare in time.",
            f"Write a village quest story with a ferryman conflict, honest payment of the fare, and a hopeful ending where medicine arrives before night."
        ]
    return [
        base,
        f"Tell a bittersweet folk tale where {seeker.id} brings penicillin back for {patient.id}, but losing time over the fare makes the healing slower.",
        f"Write a quest story with a stern ferryman, a delay at the ferry, and an ending that is safe but teaches that small conflicts can cost precious time."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    patient = f["patient"]
    ferryman = f["ferryman"]
    infection = f["infection"]
    fare = f["fare"]
    ending = f["ending"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id}, {seeker.pronoun('possessive')} {patient.label_word} {patient.id}, and {ferryman.id} at the river ferry."
        ),
        (
            f"Why did {seeker.id} start the quest?",
            f"{seeker.id} started the quest because {patient.id} had {infection.wound} and needed penicillin from the clinic across the river. The pain had changed {patient.pronoun('possessive')} gait, which showed the sickness was serious."
        ),
        (
            "What was the conflict at the river?",
            f"The ferryman would not row the boat until the fare was settled. That clash mattered because every pause kept the medicine farther away."
        ),
        (
            f"How was the fare settled?",
            f"{fare.qa_text} Once the fare was accepted, the child could cross to the clinic and begin the way home."
        ),
    ]
    if ending == "timely":
        qa.append(
            (
                f"How did the story end?",
                f"The penicillin came back in time, and {patient.id} began to mend before night was deep. By morning, {patient.pronoun('possessive')} gait was easy again, which showed the quest had truly changed the day."
            )
        )
    else:
        qa.append(
            (
                f"How did the story end?",
                f"The penicillin still helped and turned the sickness away, but it arrived after too much time had passed. {patient.id} lived and slowly healed, yet {patient.pronoun('possessive')} gait stayed careful for many mornings because the delay had made the illness harder on {patient.pronoun('object')}."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"penicillin", "gait", "fare", "ferry", "infection", "quest"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:18} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: ending={world.facts.get('ending')} total_delay={world.facts.get('total_delay')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="reedbank",
        infection="thorn_heel",
        fare="coin",
        mood="stern",
        seeker_name="Mira",
        seeker_type="girl",
        patient_name="Grandmother Brin",
        patient_type="grandmother",
        ferryman_name="Old Taren",
        delay=0,
    ),
    StoryParams(
        setting="fogford",
        infection="splinter_ankle",
        fare="net_mending",
        mood="weary",
        seeker_name="Ivo",
        seeker_type="boy",
        patient_name="Grandfather Orrin",
        patient_type="grandfather",
        ferryman_name="Moss Rowan",
        delay=0,
    ),
    StoryParams(
        setting="sunmeadow",
        infection="stone_foot",
        fare="berries",
        mood="gruff",
        seeker_name="Tala",
        seeker_type="girl",
        patient_name="Grandmother Sela",
        patient_type="grandmother",
        ferryman_name="Ferryman Hale",
        delay=1,
    ),
    StoryParams(
        setting="reedbank",
        infection="splinter_ankle",
        fare="coin",
        mood="weary",
        seeker_name="Niko",
        seeker_type="boy",
        patient_name="Grandfather Vale",
        patient_type="grandfather",
        ferryman_name="Old Taren",
        delay=1,
    ),
    StoryParams(
        setting="fogford",
        infection="thorn_heel",
        fare="berries",
        mood="stern",
        seeker_name="Lina",
        seeker_type="girl",
        patient_name="Grandmother Elow",
        patient_type="grandmother",
        ferryman_name="Moss Rowan",
        delay=0,
    ),
]


def explain_rejection(infection: Infection, fare: FareMethod) -> str:
    if not medicine_is_reasonable(infection):
        return (
            f"(No story: {infection.wound} does not make penicillin a grounded choice here. "
            f"Pick a stronger leg or foot infection so the quest and the changed gait make sense.)"
        )
    if not valid_fare(fare):
        return (
            f"(No story: offering {fare.label} is not a believable fare payment in this world. "
            f"Choose coin, berries, or work the ferryman would truly accept.)"
        )
    return "(No story: this combination is unreasonable.)"


ASP_RULES = r"""
reasonable_infection(I) :- infection(I), needs_penicillin(I), severity(I,S), S >= 2.
valid_fare(F) :- fare_method(F), accepted(F).
valid(S,I,F,M) :- setting(S), reasonable_infection(I), valid_fare(F), ferry_mood(M).

extra_delay(0) :- chosen_fare(F), fare_quick(F).
extra_delay(1) :- chosen_fare(F), not fare_quick(F).
total_delay(D + E) :- chosen_delay(D), extra_delay(E).
timely :- chosen_infection(I), severity(I,S), total_delay(T), T <= S - 1.
late :- not timely.

outcome(timely) :- timely.
outcome(late) :- late.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, inf in INFECTIONS.items():
        lines.append(asp.fact("infection", iid))
        if inf.needs_penicillin:
            lines.append(asp.fact("needs_penicillin", iid))
        lines.append(asp.fact("severity", iid, inf.severity))
    for fid, fare in FARE_METHODS.items():
        lines.append(asp.fact("fare_method", fid))
        if fare.accepted:
            lines.append(asp.fact("accepted", fid))
        if fare.quick:
            lines.append(asp.fact("fare_quick", fid))
    for mid in FERRY_MOODS:
        lines.append(asp.fact("ferry_mood", mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_infection", params.infection),
        asp.fact("chosen_fare", params.fare),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _check_params_exist(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.infection not in INFECTIONS:
        raise StoryError(f"(Unknown infection: {params.infection})")
    if params.fare not in FARE_METHODS:
        raise StoryError(f"(Unknown fare method: {params.fare})")
    if params.mood not in FERRY_MOODS:
        raise StoryError(f"(Unknown ferry mood: {params.mood})")
    if params.delay not in {0, 1, 2}:
        raise StoryError("(Delay must be 0, 1, or 2.)")


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
    for s in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        py = predicted_ending(INFECTIONS[params.infection], FARE_METHODS[params.fare], params.delay)
        asp_res = asp_outcome(params)
        if py != asp_res:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a folk-tale quest for penicillin across a ferry, with conflict over the fare."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--infection", choices=INFECTIONS)
    ap.add_argument("--fare", choices=FARE_METHODS)
    ap.add_argument("--mood", choices=FERRY_MOODS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time lost before the medicine comes home")
    ap.add_argument("--seeker-name")
    ap.add_argument("--seeker-type", choices=["girl", "boy"])
    ap.add_argument("--patient-type", choices=["grandmother", "grandfather"])
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


def _pick_seeker(rng: random.Random, forced_type: Optional[str] = None) -> tuple[str, str]:
    seeker_type = forced_type or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if seeker_type == "girl" else BOY_NAMES
    return rng.choice(pool), seeker_type


def _pick_patient(rng: random.Random, patient_type: str) -> str:
    if patient_type == "grandmother":
        return rng.choice(GRANDMOTHERS)
    return rng.choice(GRANDFATHERS)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.infection and args.fare:
        infection = INFECTIONS[args.infection]
        fare = FARE_METHODS[args.fare]
        if not (medicine_is_reasonable(infection) and valid_fare(fare)):
            raise StoryError(explain_rejection(infection, fare))
    if args.infection and not medicine_is_reasonable(INFECTIONS[args.infection]):
        raise StoryError(explain_rejection(INFECTIONS[args.infection], FARE_METHODS["coin"]))
    if args.fare and not valid_fare(FARE_METHODS[args.fare]):
        raise StoryError(explain_rejection(INFECTIONS["thorn_heel"], FARE_METHODS[args.fare]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.infection is None or c[1] == args.infection)
        and (args.fare is None or c[2] == args.fare)
        and (args.mood is None or c[3] == args.mood)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, infection_id, fare_id, mood_id = rng.choice(sorted(combos))
    seeker_name, seeker_type = _pick_seeker(rng, args.seeker_type)
    if args.seeker_name:
        seeker_name = args.seeker_name
    patient_type = args.patient_type or rng.choice(["grandmother", "grandfather"])
    patient_name = _pick_patient(rng, patient_type)
    ferryman_name = rng.choice(FERRYMEN)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        infection=infection_id,
        fare=fare_id,
        mood=mood_id,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        patient_name=patient_name,
        patient_type=patient_type,
        ferryman_name=ferryman_name,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    _check_params_exist(params)
    infection = INFECTIONS[params.infection]
    fare = FARE_METHODS[params.fare]
    if not medicine_is_reasonable(infection) or not valid_fare(fare):
        raise StoryError(explain_rejection(infection, fare))

    world = tell(
        setting=SETTINGS[params.setting],
        infection=infection,
        fare=fare,
        mood=FERRY_MOODS[params.mood],
        seeker_name=params.seeker_name,
        seeker_type=params.seeker_type,
        patient_name=params.patient_name,
        patient_type=params.patient_type,
        ferryman_name=params.ferryman_name,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, infection, fare, mood) combos:\n")
        for setting_id, infection_id, fare_id, mood_id in combos:
            print(f"  {setting_id:10} {infection_id:14} {fare_id:12} {mood_id}")
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
                f"### {p.seeker_name}: {p.infection} via {p.fare} at {p.setting} "
                f"({predicted_ending(INFECTIONS[p.infection], FARE_METHODS[p.fare], p.delay)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
