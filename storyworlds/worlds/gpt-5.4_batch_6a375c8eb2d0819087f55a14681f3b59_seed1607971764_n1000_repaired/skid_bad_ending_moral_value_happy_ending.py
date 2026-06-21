#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/skid_bad_ending_moral_value_happy_ending.py
======================================================================

A standalone storyworld for a tiny detective-style domain: two children play
junior detectives, hurry after a clue on wheels, and face a choice between
rushing on a slippery path or slowing down and thinking clearly.

The world is built around one concrete hazard: a fast wheeled chase on a slick
surface can cause a skid. The stories branch into three grounded outcomes:

* averted   -- the partner talks the rider out of rushing, so no skid happens
* solved    -- a skid happens, but a grown-up helps sensibly and the case is solved
* lost      -- the skid happens, the rescue is too weak or too late, and the clue is lost

The moral value is not stated as a slogan alone; it is embedded in the world:
good detectives slow down, watch the ground, and ask for help before a clue is
gone.

Run it
------
    python storyworlds/worlds/gpt-5.4/skid_bad_ending_moral_value_happy_ending.py
    python storyworlds/worlds/gpt-5.4/skid_bad_ending_moral_value_happy_ending.py --case badge --ride scooter --surface tiles
    python storyworlds/worlds/gpt-5.4/skid_bad_ending_moral_value_happy_ending.py --surface carpet
    python storyworlds/worlds/gpt-5.4/skid_bad_ending_moral_value_happy_ending.py --response jump_off
    python storyworlds/worlds/gpt-5.4/skid_bad_ending_moral_value_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/skid_bad_ending_moral_value_happy_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/skid_bad_ending_moral_value_happy_ending.py --verify
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
NERVE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    slippery: bool = False
    wheeled: bool = False
    evidence: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man", "groundskeeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "librarian": "librarian",
            "groundskeeper": "groundskeeper",
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
class CaseFile:
    id: str
    missing_item: str
    owner: str
    opening: str
    clue: str
    trail: str
    solved_image: str
    lost_image: str
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
class Ride:
    id: str
    label: str
    phrase: str
    plural: bool = False
    wheeled: bool = True
    quick: int = 1
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
class Surface:
    id: str
    label: str
    phrase: str
    clue_place: str
    skid_sound: str
    slip: int = 1
    slippery: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
class Response:
    id: str
    sense: int
    power: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"rider", "partner"}]

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


def _r_skid(world: World) -> list[str]:
    rider = world.get("rider")
    surface = world.get("surface")
    clue = world.get("clue")
    if rider.meters["speed"] < THRESHOLD:
        return []
    if surface.meters["slick"] < THRESHOLD:
        return []
    sig = ("skid", rider.id, surface.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    rider.meters["skidding"] += 1
    rider.meters["fallen"] += 1
    clue.meters["dropped"] += 1
    clue.meters["risk"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    return ["__skid__"]


def _r_clue_slides(world: World) -> list[str]:
    clue = world.get("clue")
    surface = world.get("surface")
    if clue.meters["dropped"] < THRESHOLD:
        return []
    sig = ("slide", clue.id, surface.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clue.meters["slid"] += 1
    clue.meters["risk"] += surface.meters["slick"]
    return ["__slide__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="skid", tag="physical", apply=_r_skid),
    Rule(name="clue_slides", tag="physical", apply=_r_clue_slides),
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


def hazard_at_risk(ride: Ride, surface: Surface) -> bool:
    return ride.wheeled and surface.slippery


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def skid_severity(surface: Surface, delay: int) -> int:
    return surface.slip + delay


def clue_saved(response: Response, surface: Surface, delay: int) -> bool:
    return response.power >= skid_severity(surface, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, rider_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > rider_age
    authority = (initial_caution(trait) + 1.0) + (3.0 if partner_older else 0.0)
    return partner_older and authority > NERVE_INIT


def predict_skid(world: World) -> dict:
    sim = world.copy()
    rider = sim.get("rider")
    rider.meters["speed"] += 1
    propagate(sim, narrate=False)
    clue = sim.get("clue")
    return {
        "skid": rider.meters["skidding"] >= THRESHOLD,
        "risk": clue.meters["risk"],
    }


def introduce(world: World, rider: Entity, partner: Entity, case: CaseFile) -> None:
    for kid in (rider, partner):
        kid.memes["curiosity"] += 1
    world.say(
        f"After school, {rider.id} and {partner.id} opened their detective notebook "
        f"for a brand-new case. {case.opening}"
    )
    world.say(
        f"They whispered the clue to each other -- {case.clue} -- and agreed that "
        f"real detectives must notice every tiny sign."
    )


def set_trail(world: World, case: CaseFile, surface: Surface) -> None:
    surf = surface.label
    world.say(
        f"Soon they spotted {case.trail} across {surface.phrase}. The marks pointed "
        f"toward {surface.clue_place}, and the case suddenly felt urgent."
    )


def tempt(world: World, rider: Entity, ride: Ride) -> None:
    rider.memes["boldness"] += 1
    world.say(
        f'{rider.id} grinned and tapped {ride.phrase}. "If I hurry on {ride.label}, '
        f'''I can reach the next clue first," {rider.pronoun()} said."'''
    )


def warn(world: World, partner: Entity, rider: Entity, ride: Ride, surface: Surface, helper: Entity) -> None:
    pred = predict_skid(world)
    partner.memes["caution"] += 1
    world.facts["predicted_risk"] = pred["risk"]
    extra = ""
    if pred["skid"]:
        extra = f" {partner.pronoun().capitalize()} could almost picture the wheels slipping sideways."
    world.say(
        f'{partner.id} lowered the magnifying glass. "Wait. {surface.the.capitalize()} is slick, '
        f"and quick wheels can skid there. {helper.label_word.capitalize()} always says good detectives "
        f'''slow down before they lose the evidence."{extra}'''
    )


def back_down(world: World, rider: Entity, partner: Entity, ride: Ride, case: CaseFile) -> None:
    rider.memes["relief"] += 1
    partner.memes["relief"] += 1
    rider.meters["speed"] = 0.0
    world.say(
        f"{rider.id} put one foot on the floor and thought about it. Then {rider.pronoun()} nodded, "
        f"rolled {ride.phrase} beside {partner.id} instead of racing, and kept the notebook tucked safe."
    )
    world.say(
        f"Step by step, the two detectives followed the clue carefully, and careful feet turned out to be faster than a wipeout would have been."
    )
    world.say(case.solved_image)


def defy(world: World, rider: Entity, partner: Entity, ride: Ride) -> None:
    rider.memes["defiance"] += 1
    older = rider.attrs.get("relation") == "siblings" and rider.age > partner.age
    if older:
        world.say(
            f'"I only need one fast push," {rider.id} said. Because {rider.pronoun()} was the older child, '
            f"{partner.id} could not stop {rider.pronoun('object')} in time."
        )
    else:
        world.say(
            f'"I only need one fast push," {rider.id} said, and darted ahead before {partner.id} could catch {rider.pronoun('object')}.'
        )


def chase(world: World, rider: Entity, ride: Ride, surface: Surface) -> None:
    rider.meters["speed"] += float(ride.quick)
    surface_ent = world.get("surface")
    surface_ent.meters["slick"] = float(surface.slip)
    propagate(world, narrate=False)
    world.say(
        f"The little wheels rattled over {surface.phrase}. Then came a sudden {surface.skid_sound} -- a skid so sharp it sounded like the whole hallway had gasped."
    )


def spill(world: World, rider: Entity, partner: Entity, case: CaseFile, surface: Surface) -> None:
    world.say(
        f"{rider.id} windmilled both arms and stumbled. The clue sheet flew from the notebook, skittered over {surface.phrase}, and headed straight toward {surface.clue_place}."
    )
    world.say(f'"The clue!" {partner.id} cried.')
    world.facts["skid_happened"] = True
    world.facts["danger_place"] = surface.clue_place
    world.facts["case_item"] = case.missing_item


def rescue(world: World, helper: Entity, response: Response, case: CaseFile) -> None:
    clue = world.get("clue")
    rider = world.get("rider")
    partner = world.get("partner")
    clue.meters["lost"] = 0.0
    clue.meters["saved"] += 1
    rider.meters["skidding"] = 0.0
    body = response.text.replace("{place}", world.facts["danger_place"])
    world.say(
        f"{helper.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"Nothing was badly hurt except {rider.id}'s pride. A little later, the clue lay flat again between {partner.id}'s careful fingers."
    )
    rider.memes["relief"] += 1
    partner.memes["relief"] += 1
    rider.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    world.say(
        f'{helper.label_word.capitalize()} brushed the paper smooth and said, "A good detective watches the ground as well as the clues. Fast is only useful when it is safe."'
    )
    world.say(case.solved_image)


def rescue_fail(world: World, helper: Entity, response: Response, case: CaseFile) -> None:
    clue = world.get("clue")
    rider = world.get("rider")
    partner = world.get("partner")
    clue.meters["lost"] += 1
    clue.meters["saved"] = 0.0
    body = response.fail.replace("{place}", world.facts["danger_place"])
    world.say(
        f"{helper.label_word.capitalize()} hurried over and {body}."
    )
    world.say(
        f"By the time the children reached the edge, the clue was gone. The case file suddenly felt terribly light in {partner.id}'s hands."
    )
    rider.memes["sadness"] += 1
    partner.memes["sadness"] += 1
    rider.memes["lesson"] += 1
    partner.memes["lesson"] += 1
    world.say(
        f'{helper.label_word.capitalize()} knelt beside them. "You are safe, and that matters most," {helper.pronoun()} said. "But detectives who rush can lose what they came to save."'
    )
    world.say(case.lost_image)


def later_safe_success(world: World, rider: Entity, partner: Entity, case: CaseFile) -> None:
    rider.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f"Later that week, when another clue appeared, {rider.id} did not race. {rider.pronoun().capitalize()} walked beside {partner.id}, eyes open and steps steady."
    )
    world.say(
        f"That time they solved the puzzle with dry knees, flat papers, and smiles that looked very pleased with themselves."
    )
@dataclass
class StoryParams:
    case: str
    ride: str
    surface: str
    response: str
    rider_name: str
    rider_gender: str
    partner_name: str
    partner_gender: str
    helper: str
    trait: str
    delay: int = 0
    rider_age: int = 6
    partner_age: int = 7
    relation: str = "siblings"
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
    "scooter": [
        (
            "Why can a scooter skid on a wet floor?",
            "A scooter has small hard wheels, so when the ground is slick the wheels can slide sideways instead of gripping. That is why riders need to slow down on wet places.",
        )
    ],
    "bicycle": [
        (
            "Why should you slow a bicycle on slippery ground?",
            "A bicycle needs good tire grip to turn and stop safely. On slippery ground the tires can slide, so slower riding gives you more control.",
        )
    ],
    "skates": [
        (
            "Why are roller skates tricky on slippery ground?",
            "Roller skates have little wheels under both feet, so a slick surface can make both feet slide at once. Careful, slow movement helps keep balance.",
        )
    ],
    "slippery": [
        (
            "What does slippery mean?",
            "Slippery means a surface is smooth or wet enough that feet or wheels can slide on it. When something is slippery, moving slowly is safer.",
        )
    ],
    "wet": [
        (
            "Why is a wet floor dangerous for wheels?",
            "Water can make the ground less grippy, so wheels do not hold the surface as well. Then a fast turn or push can end in a skid.",
        )
    ],
    "gravel": [
        (
            "Why can gravel make wheels slide?",
            "Loose gravel moves under wheels instead of staying firm. That shifting can make the rider wobble or skid.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Detectives look closely at clues because one tiny detail can lead to the answer.",
        )
    ],
    "library": [
        (
            "What do detectives do in stories?",
            "Detectives notice clues, ask careful questions, and think before they act. Solving the mystery usually takes patience as much as speed.",
        )
    ],
    "adult_help": [
        (
            "Why is it smart to call a grown-up when something unsafe happens?",
            "A grown-up can help quickly and calmly when a problem gets dangerous. Asking for help can save people and important things.",
        )
    ],
    "broom": [
        (
            "How can a long tool help reach something safely?",
            "A long tool can reach farther without making someone crawl into a risky spot. It lets the helper keep control while moving the object back.",
        )
    ],
    "save_clue": [
        (
            "Why should detectives protect the clue itself?",
            "If the clue gets ruined or lost, it becomes harder to solve the case. Good detectives guard the evidence as carefully as they follow it.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "scooter",
    "bicycle",
    "skates",
    "slippery",
    "wet",
    "gravel",
    "clue",
    "library",
    "adult_help",
    "broom",
    "save_clue",
]


def pair_noun(rider: Entity, partner: Entity, relation: str) -> str:
    if relation == "siblings":
        if rider.type == "boy" and partner.type == "boy":
            return "two brothers"
        if rider.type == "girl" and partner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case = f["case"]
    ride = f["ride_cfg"]
    surface = f["surface_cfg"]
    rider = f["rider"]
    partner = f["partner"]
    outcome = f["outcome"]
    base = (
        f'Write a detective story for a 3-to-5-year-old where two child detectives chase a clue, '
        f"someone may skid on {surface.phrase}, and the mystery teaches patience as well as courage."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle detective story where {partner.label} warns {rider.label} not to rush on {surface.phrase}, so no skid happens and they solve the case by walking carefully.",
            f'Write a mystery about {case.missing_item} where the children choose slow, careful steps over a fast ride and still find the missing thing.',
        ]
    if outcome == "lost":
        return [
            base,
            f"Tell a cautionary detective story where {rider.label} races on {ride.label}, has a skid on {surface.phrase}, and the clue is lost even though everyone gets home safe.",
            f'Write a mystery with a sad ending that teaches a moral: rushing after evidence can lose the case, and good detectives must slow down.',
        ]
    return [
        base,
        f"Tell a detective story where {rider.label} rushes on {ride.label}, has a skid on {surface.phrase}, and a calm grown-up saves the clue before it is lost.",
        f'Write a mystery that includes the word "skid" and ends happily because the children learn to slow down and protect the evidence.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rider = f["rider"]
    partner = f["partner"]
    helper = f["helper"]
    case = f["case"]
    ride = f["ride_cfg"]
    surface = f["surface_cfg"]
    response = f["response"]
    pair = pair_noun(rider, partner, f["relation"])
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {rider.label} and {partner.label}, who were pretending to be detectives. Their case was to find {case.missing_item}.",
        ),
        (
            "What clue were they following?",
            f"They were following {case.clue} and a small trail that pointed ahead. Those details made the children think they were close to solving the mystery.",
        ),
        (
            f"Why did {partner.label} warn {rider.label} not to rush?",
            f"{partner.label} knew that {surface.label} was slippery and that quick wheels can skid there. The warning was about protecting both the rider and the clue sheet.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed after {partner.label} spoke?",
                f"{rider.label} stopped trying to race and rolled along carefully instead. Because no skid happened, the evidence stayed safe and the case could be solved.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily with the missing item found. The ending shows that patient detectives can solve a case without taking a risky shortcut.",
            )
        )
    elif f["outcome"] == "solved":
        qa.append(
            (
                f"What happened during the skid?",
                f"{rider.label} slid and dropped the clue sheet, and it skittered toward {surface.clue_place}. The danger was not only the fall, but also losing the evidence they needed.",
            )
        )
        qa.append(
            (
                f"How did the {helper_word} save the case?",
                f"The {helper_word} {response.qa_text}. That quick, calm help protected the evidence before the mystery trail could disappear.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that good detectives do not let hurry boss their feet. Slowing down kept later clues safe and helped them solve the case the right way.",
            )
        )
    elif f["outcome"] == "lost":
        qa.append(
            (
                f"Why was the ending sad?",
                f"The clue slid away after the skid, so the children could not finish the case that day. Everyone was safe, but the mystery stayed unsolved because the evidence was lost.",
            )
        )
        qa.append(
            (
                "What moral value does the story teach?",
                f"It teaches patience, self-control, and asking for help before a problem grows. The bad ending matters because it shows how rushing can spoil something important.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["ride_cfg"].tags) | set(f["surface_cfg"].tags) | set(f["case"].tags)
    tags.add("clue")
    tags.add("library")
    if f["outcome"] != "averted":
        tags |= set(f["response"].tags)
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
        flags = [name for name, on in (("slippery", e.slippery), ("wheeled", e.wheeled), ("evidence", e.evidence)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        case="badge",
        ride="scooter",
        surface="tiles",
        response="block_and_grab",
        rider_name="Nora",
        rider_gender="girl",
        partner_name="Max",
        partner_gender="boy",
        helper="librarian",
        trait="careful",
        delay=0,
        rider_age=5,
        partner_age=7,
        relation="siblings",
    ),
    StoryParams(
        case="note",
        ride="bicycle",
        surface="waxed_floor",
        response="broom_hook",
        rider_name="Leo",
        rider_gender="boy",
        partner_name="Maya",
        partner_gender="girl",
        helper="groundskeeper",
        trait="bright",
        delay=0,
        rider_age=6,
        partner_age=6,
        relation="friends",
    ),
    StoryParams(
        case="ribbon",
        ride="roller_skates",
        surface="tiles",
        response="reach_by_hand",
        rider_name="Ava",
        rider_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        helper="librarian",
        trait="patient",
        delay=2,
        rider_age=7,
        partner_age=5,
        relation="siblings",
    ),
    StoryParams(
        case="badge",
        ride="bicycle",
        surface="gravel",
        response="block_and_grab",
        rider_name="Finn",
        rider_gender="boy",
        partner_name="Theo",
        partner_gender="boy",
        helper="groundskeeper",
        trait="steady",
        delay=0,
        rider_age=5,
        partner_age=7,
        relation="siblings",
    ),
]


def explain_rejection(ride: Ride, surface: Surface) -> str:
    if not surface.slippery:
        return (
            f"(No story: {surface.phrase} is not slippery enough for a skid, so there is no honest detective hazard here. "
            f"Pick a surface like tiles, gravel, or a waxed floor.)"
        )
    if not ride.wheeled:
        return f"(No story: {ride.label} has no wheels, so it cannot produce the skid this world is about.)"
    return "(No story: this combination does not create a believable skid hazard.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.rider_age, params.partner_age, params.trait):
        return "averted"
    response = RESPONSES[params.response]
    surface = SURFACES[params.surface]
    return "solved" if clue_saved(response, surface, params.delay) else "lost"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense (sense={response.sense} < {SENSE_MIN}). "
        f"Try one of the safer helper actions instead: {better}.)"
    )


ASP_RULES = r"""
hazard(R, S) :- wheeled(R), slippery(S).
sensible(X)  :- response(X), sense(X, N), sense_min(M), N >= M.
valid(C, R, S) :- case(C), ride(R), surface(S), hazard(R, S).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
partner_older :- relation(siblings), rider_age(RA), partner_age(PA), PA > RA.
bonus(3) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), nerve_init(N), A > N.

severity(SL + D) :- chosen_surface(S), slip(S, SL), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
saved :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(solved) :- not averted, saved.
outcome(lost) :- not averted, not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for case_id in CASES:
        lines.append(asp.fact("case", case_id))
    for ride_id, ride in RIDES.items():
        lines.append(asp.fact("ride", ride_id))
        if ride.wheeled:
            lines.append(asp.fact("wheeled", ride_id))
        lines.append(asp.fact("quick", ride_id, ride.quick))
    for surface_id, surface in SURFACES.items():
        lines.append(asp.fact("surface", surface_id))
        if surface.slippery:
            lines.append(asp.fact("slippery", surface_id))
        lines.append(asp.fact("slip", surface_id, surface.slip))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("nerve_init", int(NERVE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_surface", params.surface),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("rider_age", params.rider_age),
            asp.fact("partner_age", params.partner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-story world: a child detective rushes after a clue, may skid, and learns that patient steps solve cases better."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--ride", choices=RIDES)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["librarian", "groundskeeper", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start the clue gets while sliding")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.surface and not SURFACES[args.surface].slippery:
        ride = RIDES[args.ride] if args.ride else next(iter(RIDES.values()))
        raise StoryError(explain_rejection(ride, SURFACES[args.surface]))
    if args.ride and args.surface:
        ride = RIDES[args.ride]
        surface = SURFACES[args.surface]
        if not hazard_at_risk(ride, surface):
            raise StoryError(explain_rejection(ride, surface))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.case is None or combo[0] == args.case)
        and (args.ride is None or combo[1] == args.ride)
        and (args.surface is None or combo[2] == args.surface)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, ride_id, surface_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    rider_name, rider_gender = _pick_child(rng)
    partner_name, partner_gender = _pick_child(rng, avoid=rider_name)
    helper = args.helper or rng.choice(["librarian", "groundskeeper", "mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    rider_age, partner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        case=case_id,
        ride=ride_id,
        surface=surface_id,
        response=response_id,
        rider_name=rider_name,
        rider_gender=rider_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        helper=helper,
        trait=trait,
        delay=delay,
        rider_age=rider_age,
        partner_age=partner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        case = CASES[params.case]
        ride = RIDES[params.ride]
        surface = SURFACES[params.surface]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter value: {exc})") from None

    if not hazard_at_risk(ride, surface):
        raise StoryError(explain_rejection(ride, surface))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        case=case,
        ride=ride,
        surface=surface,
        response=response,
        rider_name=params.rider_name,
        rider_gender=params.rider_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        trait=params.trait,
        helper_type=params.helper,
        delay=params.delay,
        rider_age=params.rider_age,
        partner_age=params.partner_age,
        relation=params.relation,
    )

    story_text = world.render().replace("rider", params.rider_name).replace("partner", params.partner_name)
    story_text = story_text.replace("helper", world.facts["helper"].label_word.capitalize())

    for old, new in {
        "rider": params.rider_name,
        "partner": params.partner_name,
    }.items():
        story_text = story_text.replace(old, new)

    story_text = story_text.replace("rider", params.rider_name)
    story_text = story_text.replace("partner", params.partner_name)

    story_text = story_text.replace("rider.label", params.rider_name)
    story_text = story_text.replace("partner.label", params.partner_name)

    story_text = story_text.replace("rider.id", params.rider_name)
    story_text = story_text.replace("partner.id", params.partner_name)

    story_text = story_text.replace("helper.label_word", world.facts["helper"].label_word)

    story_text = story_text.replace("rider", params.rider_name)
    story_text = story_text.replace("partner", params.partner_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (case, ride, surface) combos:\n")
        for case_id, ride_id, surface_id in combos:
            print(f"  {case_id:8} {ride_id:14} {surface_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.rider_name} & {p.partner_name}: {p.case}, {p.ride} on {p.surface} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    case: CaseFile,
    ride: Ride,
    surface: Surface,
    response: Response,
    *,
    rider_name: str = "Nora",
    rider_gender: str = "girl",
    partner_name: str = "Max",
    partner_gender: str = "boy",
    trait: str = "careful",
    helper_type: str = "librarian",
    delay: int = 0,
    rider_age: int = 6,
    partner_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    rider = world.add(
        Entity(
            id="rider",
            kind="character",
            type=rider_gender,
            label=rider_name,
            role="rider",
            age=rider_age,
            attrs={"relation": relation},
            traits=["eager"],
        )
    )
    partner = world.add(
        Entity(
            id="partner",
            kind="character",
            type=partner_gender,
            label=partner_name,
            role="partner",
            age=partner_age,
            attrs={"relation": relation},
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    world.add(Entity(id="ride", type="ride", label=ride.label, wheeled=ride.wheeled))
    world.add(Entity(id="surface", type="surface", label=surface.label, slippery=surface.slippery))
    world.add(Entity(id="clue", type="clue", label="clue sheet", evidence=True))

    rider.memes["nerve"] = NERVE_INIT
    partner.memes["caution"] = initial_caution(trait)
    world.facts["predicted_risk"] = 0.0
    world.facts["skid_happened"] = False
    world.facts["danger_place"] = surface.clue_place
    world.facts["case_item"] = case.missing_item

    introduce(world, rider, partner, case)
    set_trail(world, case, surface)

    world.para()
    tempt(world, rider, ride)
    warn(world, partner, rider, ride, surface, helper)

    averted = would_avert(relation, rider_age, partner_age, trait)

    if averted:
        back_down(world, rider, partner, ride, case)
        world.para()
        later_safe_success(world, rider, partner, case)
        severity = 0
        saved = True
        outcome = "averted"
    else:
        defy(world, rider, partner, ride)
        world.para()
        chase(world, rider, ride, surface)
        spill(world, rider, partner, case, surface)

        severity = skid_severity(surface, delay)
        world.get("clue").meters["severity"] = float(severity)
        saved = clue_saved(response, surface, delay)

        world.para()
        if saved:
            rescue(world, helper, response, case)
            world.para()
            later_safe_success(world, rider, partner, case)
            outcome = "solved"
        else:
            rescue_fail(world, helper, response, case)
            outcome = "lost"

    world.facts.update(
        rider=rider,
        partner=partner,
        helper=helper,
        case=case,
        ride_cfg=ride,
        surface_cfg=surface,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        clue_saved=saved,
        clue_lost=world.get("clue").meters["lost"] >= THRESHOLD,
    )
    return world


CASES = {
    "badge": CaseFile(
        id="badge",
        missing_item="the gold hall-monitor badge",
        owner="the principal",
        opening="The principal's gold hall-monitor badge had gone missing from the library desk.",
        clue="a tiny star-shaped sticker and a bent corner of yellow paper",
        trail="faint chalk arrows",
        solved_image="At the end of the trail, they found the badge tucked behind a dictionary stand, shining like a solved secret.",
        lost_image="That evening the empty badge hook in the office looked lonelier than ever, and the children wished they had guarded the clue instead of racing it.",
        tags={"badge", "clue", "library"},
    ),
    "note": CaseFile(
        id="note",
        missing_item="the class picnic note",
        owner="their teacher",
        opening="A folded note about the class picnic had blown away before anyone could read where the treasure-map game would start.",
        clue="a paper scrap with blue ink dots",
        trail="tiny wet wheel marks",
        solved_image="Behind the umbrella stand they found the note, still folded and safe, and the start place for the picnic game was finally clear.",
        lost_image="When the clue vanished, so did the trail to the picnic note, and the game had to be called off for the day.",
        tags={"note", "paper", "school"},
    ),
    "ribbon": CaseFile(
        id="ribbon",
        missing_item="the winner's ribbon for the reading contest",
        owner="the reading club",
        opening="The reading club's bright ribbon had slipped away before the afternoon photo.",
        clue="a thread of red cloth caught on a cart wheel",
        trail="tiny red fibers",
        solved_image="Near the coat hooks they found the ribbon looped around a rolling cart handle, ready for the smiling photo after all.",
        lost_image="Without the clue, the ribbon was nowhere to be seen, and the reading club picture had one sad empty space in the middle.",
        tags={"ribbon", "reading", "school"},
    ),
}

RIDES = {
    "scooter": Ride(
        id="scooter",
        label="a scooter",
        phrase="the scooter",
        quick=2,
        tags={"scooter", "wheels"},
    ),
    "bicycle": Ride(
        id="bicycle",
        label="a little bicycle",
        phrase="the little bicycle",
        quick=2,
        tags={"bicycle", "wheels"},
    ),
    "roller_skates": Ride(
        id="roller_skates",
        label="roller skates",
        phrase="the roller skates",
        plural=True,
        quick=2,
        tags={"skates", "wheels"},
    ),
}

SURFACES = {
    "tiles": Surface(
        id="tiles",
        label="rain-slick tiles",
        phrase="the rain-slick tiles by the front hall",
        clue_place="the floor drain near the front mat",
        skid_sound="scrrrk",
        slip=3,
        slippery=True,
        tags={"tiles", "wet", "slippery"},
    ),
    "gravel": Surface(
        id="gravel",
        label="loose gravel",
        phrase="the loose gravel by the bike rack",
        clue_place="the narrow crack under the fence",
        skid_sound="crunch-swish",
        slip=2,
        slippery=True,
        tags={"gravel", "yard", "slippery"},
    ),
    "waxed_floor": Surface(
        id="waxed_floor",
        label="freshly waxed floor",
        phrase="the freshly waxed floor outside the office",
        clue_place="the gap beneath the radiator cover",
        skid_sound="skriiip",
        slip=2,
        slippery=True,
        tags={"floor", "school", "slippery"},
    ),
    "carpet": Surface(
        id="carpet",
        label="dry carpet",
        phrase="the dry carpet in the reading corner",
        clue_place="the book bin",
        skid_sound="huff",
        slip=0,
        slippery=False,
        tags={"carpet"},
    ),
}

RESPONSES = {
    "block_and_grab": Response(
        id="block_and_grab",
        sense=3,
        power=4,
        text="stepped in front of the sliding paper, pinned one corner with a shoe, and lifted it away from {place}",
        fail="tried to pin the paper before it reached {place}, but it slipped past",
        qa_text="stepped on one corner and picked the clue up before it could vanish",
        tags={"adult_help", "save_clue"},
    ),
    "broom_hook": Response(
        id="broom_hook",
        sense=3,
        power=3,
        text="used the long broom from the closet to hook the clue back before it disappeared into {place}",
        fail="reached with a broom toward {place}, but the clue had already gone too far",
        qa_text="used a long broom to hook the clue back",
        tags={"adult_help", "broom"},
    ),
    "reach_by_hand": Response(
        id="reach_by_hand",
        sense=2,
        power=2,
        text="dropped to one knee and caught the clue by hand just before {place}",
        fail="lunged by hand toward {place}, but the clue slid out of reach",
        qa_text="caught the clue by hand just in time",
        tags={"adult_help"},
    ),
    "jump_off": Response(
        id="jump_off",
        sense=1,
        power=1,
        text="told the children to jump after the paper near {place}",
        fail="called for a desperate jump near {place}, but it only made everyone scramble",
        qa_text="told them to leap after the clue",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Zoe", "Ava", "Lucy", "Ella", "Ivy"]
BOY_NAMES = ["Max", "Leo", "Ben", "Finn", "Theo", "Sam", "Eli", "Jack"]
TRAITS = ["careful", "steady", "patient", "thoughtful", "bright", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for case_id in CASES:
        for ride_id, ride in RIDES.items():
            for surface_id, surface in SURFACES.items():
                if hazard_at_risk(ride, surface):
                    combos.append((case_id, ride_id, surface_id))
    return combos

if __name__ == "__main__":
    main()
