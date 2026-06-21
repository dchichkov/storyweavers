#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py
=====================================================================

A standalone story world about a small camp mystery: something important at camp
is damaged, one child is blamed too quickly, a careful camper follows the clue,
and the real culprit admits an accident and helps restore what was harmed.

The domain is intentionally narrow and state-driven:

- a camp object at a place (banner, poster, or sign)
- an accidental kind of damage with a physical clue
- a wrong accusation that creates conflict
- a sleuth who reasons from the clue
- a voluntary repair that restores trust and the camp object

Run it
------
    python storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py
    python storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py --place lodge --damage berry_stain
    python storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py --task kite_chasing --repair glue_flatten
    python storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py --asp
    python storyworlds/worlds/gpt-5.4/camp_voluntary_restore_conflict_whodunit.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    material: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "counselor_f", "woman"}
        male = {"boy", "father", "counselor_m", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "counselor_f": "counselor",
            "counselor_m": "counselor",
            "mother": "mom",
            "father": "dad",
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
class Place:
    id: str
    label: str
    object_label: str
    object_phrase: str
    material: str
    scene: str
    suspicious_detail: str
    tasks: set[str] = field(default_factory=set)
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
class Damage:
    id: str
    label: str
    verb: str
    clue_label: str
    discover_text: str
    materials: set[str] = field(default_factory=set)
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
class Task:
    id: str
    label: str
    gerund: str
    prop: str
    clue_phrase: str
    causes: str
    accident_text: str
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
    does: str
    materials: set[str] = field(default_factory=set)
    fixes: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_damage_tension(world: World) -> list[str]:
    obj = world.get("object")
    camp = world.get("camp")
    if obj.meters["damaged"] < THRESHOLD:
        return []
    sig = ("damage_tension",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    camp.meters["mess"] += 1
    for role in ("sleuth", "accused", "culprit"):
        world.get(role).memes["worry"] += 1
    return []


def _r_false_blame_conflict(world: World) -> list[str]:
    accused = world.get("accused")
    camp = world.get("camp")
    culprit = world.get("culprit")
    if accused.memes["blamed"] < THRESHOLD or accused.memes["innocent"] < THRESHOLD:
        return []
    sig = ("false_blame_conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accused.memes["hurt"] += 1
    accused.memes["anger"] += 1
    culprit.memes["guilt"] += 1
    camp.meters["conflict"] += 1
    return []


def _r_restore_peace(world: World) -> list[str]:
    camp = world.get("camp")
    obj = world.get("object")
    culprit = world.get("culprit")
    accused = world.get("accused")
    if obj.meters["restored"] < THRESHOLD or culprit.memes["apology"] < THRESHOLD:
        return []
    sig = ("restore_peace",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    camp.meters["mess"] = 0.0
    camp.meters["conflict"] = 0.0
    accused.memes["hurt"] = 0.0
    accused.memes["anger"] = 0.0
    accused.memes["relief"] += 1
    culprit.memes["relief"] += 1
    culprit.memes["responsibility"] += 1
    world.get("sleuth").memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage_tension", tag="physical", apply=_r_damage_tension),
    Rule(name="false_blame_conflict", tag="social", apply=_r_false_blame_conflict),
    Rule(name="restore_peace", tag="social", apply=_r_restore_peace),
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
            world.say(s)
    return produced


PLACES = {
    "lodge": Place(
        id="lodge",
        label="the lodge porch",
        object_label="welcome banner",
        object_phrase="the big cloth welcome banner over the lodge steps",
        material="cloth",
        scene="Pine Needle Camp was waking up with shoe taps on the porch and the smell of toast from the dining hall.",
        suspicious_detail="The banner was the first thing everyone saw when they came down the hill.",
        tasks={"berry_bucket", "kite_chasing", "sign_painting"},
        tags={"camp", "banner"},
    ),
    "craft_shed": Place(
        id="craft_shed",
        label="the craft shed",
        object_label="camp map poster",
        object_phrase="the paper camp map poster taped beside the paint shelves",
        material="paper",
        scene="The craft shed buzzed with quiet little sounds: brush bristles in jars, scissors snipping, and benches scraping.",
        suspicious_detail="Every camper checked the map poster to find the way to canoe hour and the berry patch.",
        tasks={"kite_chasing", "sign_painting"},
        tags={"camp", "poster"},
    ),
    "garden_gate": Place(
        id="garden_gate",
        label="the garden gate",
        object_label="trail sign",
        object_phrase="the wooden trail sign beside the garden gate",
        material="wood",
        scene="Near the garden gate, bees hummed over marigolds and the path curved toward the creek.",
        suspicious_detail="The trail sign pointed new campers toward the garden, the cabins, and the lake path.",
        tasks={"berry_bucket", "sign_painting"},
        tags={"camp", "sign"},
    ),
}

DAMAGES = {
    "paint_smear": Damage(
        id="paint_smear",
        label="blue paint smear",
        verb="smeared with bright blue paint",
        clue_label="blue paint",
        discover_text="A bright blue streak dragged across it like a hasty thumb.",
        materials={"cloth", "paper", "wood"},
        tags={"paint", "clue"},
    ),
    "berry_stain": Damage(
        id="berry_stain",
        label="berry stain",
        verb="spotted with crushed berry juice",
        clue_label="berry juice",
        discover_text="Purple dots and a sticky shine showed where berries had burst.",
        materials={"cloth", "wood"},
        tags={"berries", "clue"},
    ),
    "torn_corner": Damage(
        id="torn_corner",
        label="torn corner",
        verb="left with one corner torn loose",
        clue_label="kite string",
        discover_text="One corner flapped sadly, and a thread of kite string was caught on the tear.",
        materials={"cloth", "paper"},
        tags={"tear", "clue"},
    ),
}

TASKS = {
    "sign_painting": Task(
        id="sign_painting",
        label="painting arrow signs for the afternoon hike",
        gerund="painting arrow signs",
        prop="a paint tray",
        clue_phrase="blue paint on a sleeve and the smell of fresh tempera",
        causes="paint_smear",
        accident_text="a paint tray tipped when the camper turned too fast",
        tags={"paint", "hike"},
    ),
    "berry_bucket": Task(
        id="berry_bucket",
        label="carrying a bucket of berries from the patch",
        gerund="carrying berries",
        prop="a berry bucket",
        clue_phrase="berry seeds on a hand and a sweet purple drip on the bucket handle",
        causes="berry_stain",
        accident_text="the berry bucket bumped the object and a few berries burst",
        tags={"berries", "garden"},
    ),
    "kite_chasing": Task(
        id="kite_chasing",
        label="chasing a runaway kite string",
        gerund="chasing a kite",
        prop="a kite reel",
        clue_phrase="frayed kite string looped around a wrist",
        causes="torn_corner",
        accident_text="the kite string snagged on the corner as the camper dashed by",
        tags={"kite", "wind"},
    ),
}

REPAIRS = {
    "rinse_repaint": Repair(
        id="rinse_repaint",
        label="rinse and repaint",
        does="washed the mark away, then painted the color back neatly",
        materials={"cloth", "paper", "wood"},
        fixes={"paint_smear", "berry_stain"},
        tags={"restore", "paint"},
    ),
    "patch_rehang": Repair(
        id="patch_rehang",
        label="patch and rehang",
        does="sewed a careful patch behind the tear and hung it straight again",
        materials={"cloth"},
        fixes={"torn_corner"},
        tags={"restore", "patch"},
    ),
    "glue_flatten": Repair(
        id="glue_flatten",
        label="glue and flatten",
        does="smoothed the torn part with paste, pressed it flat, and set the corners firm again",
        materials={"paper"},
        fixes={"torn_corner"},
        tags={"restore", "paper"},
    ),
    "sand_repaint": Repair(
        id="sand_repaint",
        label="sand and repaint",
        does="rubbed the wood smooth, cleaned the stain away, and repainted the letters",
        materials={"wood"},
        fixes={"paint_smear", "berry_stain"},
        tags={"restore", "wood"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "sharp-eyed", "quiet", "steady", "patient", "thoughtful"]
FEELINGS = ["grumpy", "rushed", "cross", "huffy"]


def damage_possible(place: Place, damage: Damage) -> bool:
    return place.material in damage.materials


def task_possible(place: Place, task: Task) -> bool:
    return task.id in place.tasks


def clue_matches(damage: Damage, task: Task) -> bool:
    return task.causes == damage.id


def repair_works(place: Place, damage: Damage, repair: Repair) -> bool:
    return place.material in repair.materials and damage.id in repair.fixes


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for damage_id, damage in DAMAGES.items():
            if not damage_possible(place, damage):
                continue
            for task_id, task in TASKS.items():
                if not task_possible(place, task):
                    continue
                if not clue_matches(damage, task):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair_works(place, damage, repair):
                        combos.append((place_id, damage_id, task_id, repair_id))
    return sorted(combos)


def culprit_identity_from_task(task_id: str) -> str:
    return task_id


def predict_solution(place: Place, damage: Damage, task: Task, repair: Repair) -> dict:
    return {
        "clue_match": clue_matches(damage, task),
        "repair_success": repair_works(place, damage, repair),
        "restores": clue_matches(damage, task) and repair_works(place, damage, repair),
    }


def introduce(world: World, sleuth: Entity, accused: Entity, culprit: Entity, counselor: Entity, place: Place) -> None:
    world.say(
        f"At camp, {place.scene} {sleuth.id} liked mysteries so much that even a squeaky door could feel like the start of a case."
    )
    world.say(
        f"That morning, {sleuth.id}, {accused.id}, and {culprit.id} hurried toward {place.label}, while {counselor.label_word} Rowan checked the day's list."
    )
    world.say(
        f"There, everyone could see {place.object_phrase}. {place.suspicious_detail}"
    )


def small_conflict(world: World, accused: Entity, culprit: Entity, feeling: str) -> None:
    accused.memes["annoyed"] += 1
    culprit.memes["annoyed"] += 1
    world.say(
        f"Before anything went wrong, {accused.id} and {culprit.id} had a small conflict about whose turn it was to carry supplies. "
        f"{accused.id} walked off looking {feeling}, and that detail stayed in everybody's mind."
    )


def discover_damage(world: World, place: Place, damage: Damage) -> None:
    obj = world.get("object")
    obj.meters["damaged"] += 1
    obj.meters[damage.id] += 1
    propagate(world, narrate=False)
    world.say(
        f"A little later, a shout rose from {place.label}. The {place.object_label} had been {damage.verb}. {damage.discover_text}"
    )


def false_accusation(world: World, accused: Entity, culprit: Entity, damage: Damage) -> None:
    accused.memes["blamed"] += 1
    accused.memes["innocent"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"It must have been {accused.id}," said {culprit.id} too quickly. "You were stomping around here before."'
    )
    world.say(
        f'{accused.id} stared at the mark and went red in the face. "I did not do that. I was upset, but I would never ruin camp things."'
    )
    if accused.memes["anger"] >= THRESHOLD:
        world.say(
            f"The porch air felt tight at once. A fast guess had turned the mystery into a real hurt feeling."
        )


def investigate(world: World, sleuth: Entity, damage: Damage, task: Task, accused: Entity, culprit: Entity) -> None:
    sleuth.memes["focus"] += 1
    world.say(
        f'{sleuth.id} knelt down and looked closer. "{damage.clue_label.capitalize()} tells a story," {sleuth.pronoun()} said softly.'
    )
    world.say(
        f"{sleuth.pronoun().capitalize()} noticed {task.clue_phrase}. That clue fit {task.gerund}, not a grumpy walk past the porch."
    )
    world.say(
        f'"So if {accused.id} did not make this mess," {sleuth.id} said, "who was doing the job that leaves exactly that clue?"'
    )


def reveal(world: World, culprit: Entity, task: Task, counselor: Entity) -> None:
    culprit.memes["cornered"] += 1
    culprit.memes["guilt"] += 1
    world.say(
        f"{culprit.id}'s eyes dropped to {culprit.pronoun('possessive')} hands. There it was again: {task.clue_phrase}."
    )
    world.say(
        f'{counselor.label_word.capitalize()} Rowan did not sound angry. "{culprit.id}," {counselor.pronoun()} said, "was it an accident?"'
    )
    culprit.memes["confessed"] += 1
    world.say(
        f'{culprit.id} nodded. "{task.accident_text.capitalize()}," {culprit.pronoun()} whispered. "I got scared and blamed {world.get("accused").id} instead."'
    )


def apology(world: World, culprit: Entity, accused: Entity) -> None:
    culprit.memes["apology"] += 1
    accused.memes["heard_apology"] += 1
    world.say(
        f'{culprit.id} turned to {accused.id}. "I am sorry. I tried to hide my mistake with another mistake."'
    )
    world.say(
        f'{accused.id} let out the breath {accused.pronoun()} had been holding. "{culprit.id}, that was not fair," {accused.pronoun()} said, "but thank you for telling the truth."'
    )


def voluntary_restore(world: World, culprit: Entity, accused: Entity, sleuth: Entity, counselor: Entity, repair: Repair, place: Place) -> None:
    obj = world.get("object")
    obj.meters["restored"] += 1
    obj.meters["damaged"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f'Nobody had to command them. {culprit.id} asked for a voluntary repair job, and {accused.id} and {sleuth.id} joined in.'
    )
    world.say(
        f"Together they {repair.does}, trying to restore the {place.object_label} before lunch was over."
    )
    world.say(
        f'When they finished, the {place.object_label} looked ready to welcome camp all over again. Even the quarrel sounded smaller under the noon birds.'
    )
    world.say(
        f'{counselor.label_word.capitalize()} Rowan smiled. "A mystery solved is good," {counselor.pronoun()} said, "but telling the truth and helping restore the harm is better."'
    )


def tell(
    place: Place,
    damage: Damage,
    task: Task,
    repair: Repair,
    sleuth_name: str = "Lily",
    sleuth_gender: str = "girl",
    accused_name: str = "Tom",
    accused_gender: str = "boy",
    culprit_name: str = "Max",
    culprit_gender: str = "boy",
    counselor_type: str = "counselor_f",
    sleuth_trait: str = "careful",
    conflict_feeling: str = "grumpy",
) -> World:
    world = World(place)
    sleuth = world.add(
        Entity(
            id=sleuth_name,
            kind="character",
            type=sleuth_gender,
            role="sleuth",
            traits=[sleuth_trait],
            attrs={},
        )
    )
    accused = world.add(
        Entity(
            id=accused_name,
            kind="character",
            type=accused_gender,
            role="accused",
            traits=["earnest"],
            attrs={},
        )
    )
    culprit = world.add(
        Entity(
            id=culprit_name,
            kind="character",
            type=culprit_gender,
            role="culprit",
            traits=["rushed"],
            attrs={"task": task.id},
        )
    )
    counselor = world.add(
        Entity(
            id="Rowan",
            kind="character",
            type=counselor_type,
            role="counselor",
            label="the counselor",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="camp",
            kind="thing",
            type="camp",
            label="camp",
            role="setting",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="object",
            kind="thing",
            type="camp_object",
            label=place.object_label,
            role="object",
            material=place.material,
            attrs={},
        )
    )

    # Initialize meters/memes read by rules before any propagate() calls.
    for ent in list(world.entities.values()):
        ent.meters["damaged"] += 0.0
        ent.meters["restored"] += 0.0
        ent.memes["blamed"] += 0.0
        ent.memes["innocent"] += 0.0
        ent.memes["apology"] += 0.0
    world.get("camp").meters["mess"] += 0.0
    world.get("camp").meters["conflict"] += 0.0

    introduce(world, sleuth, accused, culprit, counselor, place)
    world.para()
    small_conflict(world, accused, culprit, conflict_feeling)
    discover_damage(world, place, damage)
    false_accusation(world, accused, culprit, damage)

    world.para()
    investigate(world, sleuth, damage, task, accused, culprit)
    reveal(world, culprit, task, counselor)
    apology(world, culprit, accused)

    world.para()
    voluntary_restore(world, culprit, accused, sleuth, counselor, repair, place)

    world.facts.update(
        place=place,
        damage=damage,
        task=task,
        repair=repair,
        sleuth=sleuth,
        accused=accused,
        culprit=culprit,
        counselor=counselor,
        object=world.get("object"),
        conflict=True,
        culprit_found=clue_matches(damage, task),
        restored=world.get("object").meters["restored"] >= THRESHOLD,
        voluntary=True,
        wrong_accusation=accused.memes["blamed"] >= THRESHOLD,
        conflict_feeling=conflict_feeling,
    )
    return world


KNOWLEDGE = {
    "camp": [
        (
            "What is a camp counselor?",
            "A camp counselor is a grown-up who helps children stay safe, solve problems, and have a good day at camp."
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a piece of cloth with words or pictures on it. People hang one up so everyone can see a welcome or a message."
        )
    ],
    "poster": [
        (
            "What is a poster?",
            "A poster is a large sheet with words or pictures on it. It can help people learn where to go or what to do."
        )
    ],
    "sign": [
        (
            "What does a trail sign do?",
            "A trail sign points the way. It helps people know where a path leads."
        )
    ],
    "paint": [
        (
            "Why does wet paint leave clues?",
            "Wet paint sticks to things it touches. That means it can leave a colored mark on objects, hands, or clothes."
        )
    ],
    "berries": [
        (
            "Why can berries make stains?",
            "Berries have strong juice inside them. When they burst, the juice can leave purple or red marks."
        )
    ],
    "tear": [
        (
            "How can a tear happen by accident?",
            "A tear can happen when cloth or paper gets snagged on something sharp or pulled too fast. Accidents can still leave a mess that needs fixing."
        )
    ],
    "restore": [
        (
            "What does restore mean?",
            "Restore means to fix something so it is right again. You try to bring it back after it was hurt, broken, or messy."
        )
    ],
    "conflict": [
        (
            "What is a conflict?",
            "A conflict is a problem or disagreement between people. It can start with hurt feelings, but it can also be solved with truth and care."
        )
    ],
}
KNOWLEDGE_ORDER = ["camp", "banner", "poster", "sign", "paint", "berries", "tear", "restore", "conflict"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    damage = f["damage"]
    task = f["task"]
    accused = f["accused"]
    culprit = f["culprit"]
    sleuth = f["sleuth"]
    return [
        f'Write a gentle camp whodunit for a 3-to-5-year-old that includes the words "camp", "voluntary", and "restore". Make the mystery about a {place.object_label} with a {damage.label}.',
        f"Tell a short mystery where {accused.id} is blamed too quickly, but {sleuth.id} studies the clue and finds out that {culprit.id} caused the damage by accident while {task.gerund}.",
        f"Write a story with Conflict, a wrong accusation, and a kind ending where the children choose a voluntary way to restore what was damaged.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two campers"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place = f["place"]
    damage = f["damage"]
    task = f["task"]
    repair = f["repair"]
    sleuth = f["sleuth"]
    accused = f["accused"]
    culprit = f["culprit"]
    counselor = f["counselor"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about three campers at camp: {sleuth.id}, {accused.id}, and {culprit.id}, with counselor Rowan nearby. The mystery starts when the {place.object_label} at {place.label} is damaged."
        ),
        (
            f"What was the mystery?",
            f"The mystery was who had harmed the {place.object_label}. It had been {damage.verb}, so everyone wanted to know how it happened and who had done it."
        ),
        (
            f"Why did people blame {accused.id} at first?",
            f"People remembered that {accused.id} had just had a small conflict with {culprit.id} and had walked away looking {f['conflict_feeling']}. That made the fast guess feel believable, even though it was not true."
        ),
        (
            f"How did {sleuth.id} solve the mystery?",
            f"{sleuth.id} looked carefully at the clue on the damaged object and matched it to {task.gerund}. The clue fit {culprit.id}'s job, not {accused.id}'s mood, so the mystery was solved by noticing the right detail."
        ),
        (
            f"Why did {culprit.id} accuse {accused.id}?",
            f"{culprit.id} had caused the damage by accident and felt scared. Blaming {accused.id} was a quick way to hide that fear, but it also made the conflict worse."
        ),
        (
            "How was the problem fixed?",
            f"The children chose a voluntary repair job and worked together to {repair.does}. That helped restore the {place.object_label} and also restore trust after the wrong accusation."
        ),
        (
            "How did the story end?",
            f"It ended with the mystery solved, the apology spoken out loud, and the camp object looking right again. The ending image shows that truth and help changed the whole mood at camp."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"camp", "restore", "conflict"}
    tags |= set(world.facts["place"].tags)
    tags |= set(world.facts["damage"].tags)
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
        if e.material:
            bits.append(f"material={e.material}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    damage: str
    task: str
    repair: str
    sleuth: str
    sleuth_gender: str
    accused: str
    accused_gender: str
    culprit: str
    culprit_gender: str
    counselor: str
    trait: str
    feeling: str
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


CURATED = [
    StoryParams(
        place="lodge",
        damage="berry_stain",
        task="berry_bucket",
        repair="rinse_repaint",
        sleuth="Lily",
        sleuth_gender="girl",
        accused="Tom",
        accused_gender="boy",
        culprit="Max",
        culprit_gender="boy",
        counselor="counselor_f",
        trait="careful",
        feeling="grumpy",
    ),
    StoryParams(
        place="craft_shed",
        damage="paint_smear",
        task="sign_painting",
        repair="rinse_repaint",
        sleuth="Ben",
        sleuth_gender="boy",
        accused="Mia",
        accused_gender="girl",
        culprit="Zoe",
        culprit_gender="girl",
        counselor="counselor_m",
        trait="sharp-eyed",
        feeling="cross",
    ),
    StoryParams(
        place="lodge",
        damage="torn_corner",
        task="kite_chasing",
        repair="patch_rehang",
        sleuth="Nora",
        sleuth_gender="girl",
        accused="Sam",
        accused_gender="boy",
        culprit="Eli",
        culprit_gender="boy",
        counselor="counselor_f",
        trait="patient",
        feeling="huffy",
    ),
    StoryParams(
        place="craft_shed",
        damage="torn_corner",
        task="kite_chasing",
        repair="glue_flatten",
        sleuth="Theo",
        sleuth_gender="boy",
        accused="Lucy",
        accused_gender="girl",
        culprit="Finn",
        culprit_gender="boy",
        counselor="counselor_m",
        trait="thoughtful",
        feeling="rushed",
    ),
    StoryParams(
        place="garden_gate",
        damage="paint_smear",
        task="sign_painting",
        repair="sand_repaint",
        sleuth="Ava",
        sleuth_gender="girl",
        accused="Noah",
        accused_gender="boy",
        culprit="Rose",
        culprit_gender="girl",
        counselor="counselor_f",
        trait="steady",
        feeling="cross",
    ),
]


def explain_rejection(place: Place, damage: Damage, task: Task, repair: Repair) -> str:
    reasons: list[str] = []
    if not damage_possible(place, damage):
        reasons.append(
            f"{place.object_label} is made of {place.material}, so a {damage.label} does not fit this object choice"
        )
    if not task_possible(place, task):
        reasons.append(
            f"{task.gerund} does not happen naturally at {place.label}"
        )
    if not clue_matches(damage, task):
        reasons.append(
            f"{task.gerund} leaves the wrong clue for {damage.label}"
        )
    if not repair_works(place, damage, repair):
        reasons.append(
            f"{repair.label} would not honestly restore this kind of damage on {place.material}"
        )
    if not reasons:
        reasons.append("this combination is not reasonable in this world")
    return "(No story: " + "; ".join(reasons) + ".)"


ASP_RULES = r"""
damage_possible(P,D) :- place(P), damage(D), material(P,M), damage_material(D,M).
task_possible(P,T)   :- place(P), task(T), allowed_task(P,T).
clue_match(D,T)      :- damage(D), task(T), causes(T,D).
repair_works(P,D,R)  :- place(P), damage(D), repair(R), material(P,M), repair_material(R,M), fixes(R,D).

valid(P,D,T,R) :- damage_possible(P,D), task_possible(P,T), clue_match(D,T), repair_works(P,D,R).

solved(P,D,T,R) :- valid(P,D,T,R).
outcome(restored) :- chosen(P,D,T,R), solved(P,D,T,R).
#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("material", pid, place.material))
        for tid in sorted(place.tasks):
            lines.append(asp.fact("allowed_task", pid, tid))
    for did, damage in DAMAGES.items():
        lines.append(asp.fact("damage", did))
        for mat in sorted(damage.materials):
            lines.append(asp.fact("damage_material", did, mat))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("causes", tid, task.causes))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        for mat in sorted(repair.materials):
            lines.append(asp.fact("repair_material", rid, mat))
        for did in sorted(repair.fixes):
            lines.append(asp.fact("fixes", rid, did))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen", params.place, params.damage, params.task, params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    if (
        params.place not in PLACES
        or params.damage not in DAMAGES
        or params.task not in TASKS
        or params.repair not in REPAIRS
    ):
        return "invalid"
    place = PLACES[params.place]
    damage = DAMAGES[params.damage]
    task = TASKS[params.task]
    repair = REPAIRS[params.repair]
    return "restored" if (
        damage_possible(place, damage)
        and task_possible(place, task)
        and clue_matches(damage, task)
        and repair_works(place, damage, repair)
    ) else "invalid"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a camp mystery, a false accusation, and a voluntary repair that restores trust."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--damage", choices=DAMAGES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--counselor", choices=["counselor_f", "counselor_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: set[str]) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n not in avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.damage and args.task and args.repair:
        place = PLACES[args.place]
        damage = DAMAGES[args.damage]
        task = TASKS[args.task]
        repair = REPAIRS[args.repair]
        if (args.place, args.damage, args.task, args.repair) not in set(valid_combos()):
            raise StoryError(explain_rejection(place, damage, task, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.damage is None or combo[1] == args.damage)
        and (args.task is None or combo[2] == args.task)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, damage_id, task_id, repair_id = rng.choice(combos)
    sleuth, sg = _pick_child(rng, avoid=set())
    accused, ag = _pick_child(rng, avoid={sleuth})
    culprit, cg = _pick_child(rng, avoid={sleuth, accused})
    counselor = args.counselor or rng.choice(["counselor_f", "counselor_m"])
    trait = rng.choice(TRAITS)
    feeling = rng.choice(FEELINGS)
    return StoryParams(
        place=place_id,
        damage=damage_id,
        task=task_id,
        repair=repair_id,
        sleuth=sleuth,
        sleuth_gender=sg,
        accused=accused,
        accused_gender=ag,
        culprit=culprit,
        culprit_gender=cg,
        counselor=counselor,
        trait=trait,
        feeling=feeling,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.damage not in DAMAGES:
        raise StoryError(f"(No story: unknown damage '{params.damage}'.)")
    if params.task not in TASKS:
        raise StoryError(f"(No story: unknown task '{params.task}'.)")
    if params.repair not in REPAIRS:
        raise StoryError(f"(No story: unknown repair '{params.repair}'.)")

    place = PLACES[params.place]
    damage = DAMAGES[params.damage]
    task = TASKS[params.task]
    repair = REPAIRS[params.repair]

    if (params.place, params.damage, params.task, params.repair) not in set(valid_combos()):
        raise StoryError(explain_rejection(place, damage, task, repair))

    world = tell(
        place=place,
        damage=damage,
        task=task,
        repair=repair,
        sleuth_name=params.sleuth,
        sleuth_gender=params.sleuth_gender,
        accused_name=params.accused,
        accused_gender=params.accused_gender,
        culprit_name=params.culprit,
        culprit_gender=params.culprit_gender,
        counselor_type=params.counselor,
        sleuth_trait=params.trait,
        conflict_feeling=params.feeling,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

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
        if not sample.story.strip():
            raise StoryError("empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, damage, task, repair) combos:\n")
        for place, damage, task, repair in combos:
            print(f"  {place:12} {damage:12} {task:14} {repair}")
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
            header = f"### {p.place}: {p.damage} from {p.task} ({p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
