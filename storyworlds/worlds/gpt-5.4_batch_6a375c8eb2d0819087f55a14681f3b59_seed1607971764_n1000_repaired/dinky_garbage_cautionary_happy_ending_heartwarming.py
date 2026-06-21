#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dinky_garbage_cautionary_happy_ending_heartwarming.py
=================================================================================

A standalone story world about a child who wants to help carry garbage with a
dinky little hauler. The unsafe plan can be averted by a wiser older sibling,
or it can spill and then be cleaned up the safe way with a grown-up. The ending
is heartwarming: the child still gets to help, but with the right tool.

Run it
------
    python storyworlds/worlds/gpt-5.4/dinky_garbage_cautionary_happy_ending_heartwarming.py
    python storyworlds/worlds/gpt-5.4/dinky_garbage_cautionary_happy_ending_heartwarming.py --place kitchen --hauler wagon --garbage peels
    python storyworlds/worlds/gpt-5.4/dinky_garbage_cautionary_happy_ending_heartwarming.py --hauler basket --garbage wrappers
    python storyworlds/worlds/gpt-5.4/dinky_garbage_cautionary_happy_ending_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/dinky_garbage_cautionary_happy_ending_heartwarming.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLD_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "sensible", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    sturdy: bool = False
    washable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    floor: str
    path: str
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
class Hauler:
    id: str
    label: str
    phrase: str
    stability: int
    toyish: bool
    ride_line: str
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
class GarbageKind:
    id: str
    label: str
    phrase: str
    bag_phrase: str
    mess: int
    smell: int
    wobble: int
    spill_text: str
    safe_sort: str
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"carrier", "cautioner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return World(
            place=self.place,
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts={},
        )
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    bag = world.entities.get("bag")
    if bag is None or bag.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill", "bag")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    floor = world.get("floor")
    floor.meters["dirty"] += 1
    floor.meters["smell"] += bag.meters["smell_load"]
    hauler = world.get("hauler")
    hauler.meters["dirty"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__mess__")
    return out


def _r_clean(world: World) -> list[str]:
    out: list[str] = []
    floor = world.entities.get("floor")
    if floor is None or floor.meters["dirty"] < THRESHOLD:
        return out
    if world.facts.get("cleaning_started", 0) < THRESHOLD:
        return out
    sig = ("clean", "floor")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    floor.meters["dirty"] = 0.0
    floor.meters["smell"] = max(0.0, floor.meters["smell"] - 1.0)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["care"] += 1
    out.append("__clean__")
    return out


CAUSAL_RULES = [
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="clean", tag="physical", apply=_r_clean),
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


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        floor="the checkerboard kitchen floor",
        path="to the back door",
        tags={"kitchen"},
    ),
    "porch": Place(
        id="porch",
        label="the back porch",
        floor="the wooden porch boards",
        path="to the outdoor bin",
        tags={"porch"},
    ),
    "hall": Place(
        id="hall",
        label="the apartment hall",
        floor="the smooth hall floor",
        path="to the big trash room",
        tags={"hall"},
    ),
}

HAULERS = {
    "wagon": Hauler(
        id="wagon",
        label="wagon",
        phrase="a dinky red wagon with one wiggly wheel",
        stability=1,
        toyish=True,
        ride_line="It looked perfect for toy bears and blocks, not for real work.",
        tags={"wagon", "dinky"},
    ),
    "dump_truck": Hauler(
        id="dump_truck",
        label="toy dump truck",
        phrase="a dinky toy dump truck with a tiny tipping bed",
        stability=1,
        toyish=True,
        ride_line="Its little bed could tip if anything lumpy slid inside.",
        tags={"truck", "dinky"},
    ),
    "basket": Hauler(
        id="basket",
        label="plastic basket",
        phrase="a dinky plastic basket with short blue handles",
        stability=2,
        toyish=False,
        ride_line="It was stronger than a toy, but it still swung when carried fast.",
        tags={"basket", "dinky"},
    ),
}

GARBAGE = {
    "peels": GarbageKind(
        id="peels",
        label="banana peels and apple cores",
        phrase="banana peels and apple cores from snack time",
        bag_phrase="a small garbage bag with banana peels and apple cores inside",
        mess=2,
        smell=1,
        wobble=3,
        spill_text="The bag lurched, and a peel slid out first. Then the whole little heap flopped onto the floor with a damp plop.",
        safe_sort="held the bag open while the scraps were tucked neatly back inside",
        tags={"garbage", "banana_peel"},
    ),
    "sticky_cups": GarbageKind(
        id="sticky_cups",
        label="sticky yogurt cups and napkins",
        phrase="sticky yogurt cups and crumpled napkins",
        bag_phrase="a garbage bag with sticky cups and crumpled napkins",
        mess=2,
        smell=1,
        wobble=2,
        spill_text="A sticky cup rolled free, and then the rest of the garbage slipped after it in a sloppy little tumble.",
        safe_sort="picked up each cup and napkin and dropped them into the real bin one by one",
        tags={"garbage", "recycling"},
    ),
    "wrappers": GarbageKind(
        id="wrappers",
        label="crinkly wrappers and paper scraps",
        phrase="crinkly wrappers and paper scraps",
        bag_phrase="a light garbage bag full of wrappers and paper scraps",
        mess=1,
        smell=0,
        wobble=1,
        spill_text="The bag tipped sideways, and the wrappers fluttered out like noisy little birds all over the floor.",
        safe_sort="gathered the wrappers and paper scraps before they skittered away",
        tags={"garbage", "paper"},
    ),
    "drippy_plate": GarbageKind(
        id="drippy_plate",
        label="drippy sauce cups and a paper plate",
        phrase="drippy sauce cups and a soggy paper plate",
        bag_phrase="a drippy garbage bag with sauce cups and a soggy paper plate",
        mess=3,
        smell=1,
        wobble=3,
        spill_text="One sauce cup popped open, and then the bag sagged apart. Garbage splashed onto the floor in a gooey little mess.",
        safe_sort="wiped the drips first and then lifted the soggy pieces into the sturdy bin",
        tags={"garbage", "sticky"},
    ),
}

RESPONSES = {
    "rolling_bin": Response(
        id="rolling_bin",
        sense=3,
        power=4,
        text="brought over the sturdy rolling bin, pulled on cleaning gloves, and showed the children how to lift the bag low and slow",
        fail="brought the rolling bin too late, after the mess had already spread farther than one quick trip could fix",
        qa_text="used the sturdy rolling bin and cleaning gloves to tidy the spill",
        tags={"bin", "gloves"},
    ),
    "gloves_and_tongs": Response(
        id="gloves_and_tongs",
        sense=3,
        power=3,
        text="slid on rubber gloves, used the kitchen tongs for the yucky bits, and set a real trash can beside them",
        fail="tried gloves and tongs, but the mess had already been tracked too far across the floor",
        qa_text="used gloves, tongs, and a real trash can to clean the garbage up",
        tags={"gloves", "tongs"},
    ),
    "mop_only": Response(
        id="mop_only",
        sense=1,
        power=1,
        text="swished a mop over the mess",
        fail="swished a mop around, but it only smeared the garbage farther",
        qa_text="mopped at the mess",
        tags={"mop"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Ruby", "Ella", "June"]
BOY_NAMES = ["Ben", "Max", "Theo", "Sam", "Leo", "Eli", "Finn", "Noah"]
TRAITS = ["careful", "steady", "curious", "eager", "sensible", "gentle"]
COMFORTS = ["soft bunny", "little bear", "striped blanket", "plush duck"]


def hazard_at_risk(hauler: Hauler, garbage: GarbageKind) -> bool:
    return garbage.wobble > hauler.stability


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def spill_severity(garbage: GarbageKind, delay: int) -> int:
    return garbage.mess + delay


def is_cleaned(response: Response, garbage: GarbageKind, delay: int) -> bool:
    return response.power >= spill_severity(garbage, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, carrier_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > carrier_age
    authority = initial_care(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > BOLD_INIT


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for place_id in PLACES:
        for hauler_id, hauler in HAULERS.items():
            for garbage_id, garbage in GARBAGE.items():
                if hazard_at_risk(hauler, garbage):
                    combos.append((place_id, hauler_id, garbage_id))
    return combos


def predict_spill(world: World, garbage_id: str) -> dict:
    sim = world.copy()
    bag = sim.get("bag")
    garbage = GARBAGE[garbage_id]
    bag.meters["spilled"] += 1
    bag.meters["smell_load"] = float(garbage.smell)
    propagate(sim, narrate=False)
    return {
        "spill": bag.meters["spilled"] >= THRESHOLD,
        "floor_dirty": sim.get("floor").meters["dirty"],
        "smell": sim.get("floor").meters["smell"],
    }


def introduce(world: World, carrier: Entity, cautioner: Entity, hauler: Hauler) -> None:
    carrier.memes["joy"] += 1
    cautioner.memes["joy"] += 1
    world.say(
        f"After supper, {carrier.id} wanted to help with chores. By the wall sat {hauler.phrase}, "
        f"and to {carrier.pronoun('object')} it looked wonderfully useful."
    )
    world.say(hauler.ride_line)
    world.say(
        f'{carrier.id} patted the side of it. "I can help take out the garbage!" '
        f'{carrier.pronoun().capitalize()} said.'
    )


def show_bag(world: World, cautioner: Entity, garbage: GarbageKind) -> None:
    world.say(
        f"Nearby was {garbage.bag_phrase}. {cautioner.id} looked at it and then at the small hauler."
    )


def tempt(world: World, carrier: Entity, garbage: GarbageKind, place: Place) -> None:
    carrier.memes["bold"] += 1
    world.say(
        f"{carrier.id} reached for the bag anyway. {carrier.pronoun().capitalize()} could already imagine "
        f"pulling it across {place.path} all by {carrier.pronoun('object')}self."
    )
    world.say(
        f"The job was real, and that made helping feel important."
    )


def warn(world: World, cautioner: Entity, carrier: Entity, hauler: Hauler, garbage: GarbageKind, parent: Entity) -> None:
    cautioner.memes["care"] += 1
    pred = predict_spill(world, garbage.id)
    world.facts["predicted_floor_dirty"] = pred["floor_dirty"]
    world.facts["predicted_smell"] = pred["smell"]
    extra = ""
    if cautioner.memes["care"] >= 6:
        extra = f" {cautioner.pronoun().capitalize()} sounded very sure."
    world.say(
        f'{cautioner.id} shook {cautioner.pronoun("possessive")} head. "{carrier.id}, that hauler is dinky. '
        f'''The garbage could wobble and spill on {world.place.floor}. Let's ask {parent.label_word} for the real bin."{extra}"'''
    )


def defy(world: World, carrier: Entity, cautioner: Entity) -> None:
    carrier.memes["defiance"] += 1
    if carrier.attrs.get("relation") == "siblings" and carrier.age > cautioner.age:
        world.say(
            f'"It will be fine," {carrier.id} said. Because {carrier.pronoun()} was the older one just then, '
            f"{cautioner.id} could not stop {carrier.pronoun('object')}."
        )
    else:
        world.say(
            f'"It will be fine," {carrier.id} said, and before anyone could stop {carrier.pronoun("object")}, '
            f'{carrier.pronoun()} tugged the hauler into place.'
        )


def back_down(world: World, carrier: Entity, cautioner: Entity, parent: Entity) -> None:
    carrier.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    carrier.memes["bold"] = 0.0
    sib = ""
    if cautioner.attrs.get("relation") == "siblings":
        sib = " older"
    world.say(
        f'{carrier.id} looked at {cautioner.id} and then at the bag again. '
        f'{cautioner.id} was {carrier.pronoun("possessive")}{sib} sibling, and the warning landed at last.'
    )
    world.say(
        f'"Okay," {carrier.pronoun()} whispered. "Let\'s do it the safe way." Together they called for {parent.label_word}.'
    )


def spill(world: World, carrier: Entity, garbage: GarbageKind, hauler: Hauler) -> None:
    bag = world.get("bag")
    bag.meters["spilled"] += 1
    bag.meters["smell_load"] = float(garbage.smell)
    world.get("hauler").meters["strain"] = float(garbage.wobble)
    propagate(world, narrate=False)
    world.say(
        f"{carrier.id} set the bag into the {hauler.label}. For one tiny roll it seemed to work."
    )
    world.say(garbage.spill_text)


def alarm(world: World, cautioner: Entity, parent: Entity) -> None:
    world.say(
        f'"Oh no! The garbage spilled!" {cautioner.id} cried. "{parent.label_word.capitalize()}, please help!"'
    )


def clean_up(world: World, parent: Entity, response: Response, garbage: GarbageKind) -> None:
    world.facts["cleaning_started"] = 1.0
    world.say(
        f"{parent.label_word.capitalize()} came right away and {response.text}."
    )
    world.say(
        f"Soon {garbage.safe_sort}, and the worst of the mess was gone."
    )
    propagate(world, narrate=False)


def lesson(world: World, parent: Entity, carrier: Entity, cautioner: Entity, hauler: Hauler) -> None:
    for kid in (carrier, cautioner):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["worry"] = 0.0
    comfort = cautioner.attrs.get("comfort", "")
    comfort_line = ""
    if comfort:
        comfort_line = f" {cautioner.id} hugged {cautioner.pronoun('possessive')} {comfort} and nodded."
    world.say(
        f"Then {parent.label_word.capitalize()} knelt beside them. "
        f'"I love that you wanted to help," {parent.pronoun()} said softly. '
        f'"But garbage needs a sturdy bin, not a dinky {hauler.label}. Asking for help is part of helping."{comfort_line}'
    )


def safe_try(world: World, parent: Entity, carrier: Entity, cautioner: Entity, response: Response, place: Place) -> None:
    for kid in (carrier, cautioner):
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"Together they tried again, this time with the real bin close to the floor and {parent.label_word} guiding their hands."
    )
    world.say(
        f"{carrier.id} carried one light piece at a time, and {cautioner.id} held the lid steady. "
        f"They made it across {place.path} without one thing dropping."
    )
    world.say(
        f"Afterward the little {world.get('hauler').label} was washed clean and saved for toys, while the real garbage went where it belonged."
    )


def cozy_end(world: World, carrier: Entity, cautioner: Entity, hauler: Hauler) -> None:
    world.say(
        f"Later, the children tucked toy animals into the {hauler.label} and pulled them gently in a tidy parade. "
        f"The dinky helper had the right job at last, and the whole home felt calm again."
    )
@dataclass
class StoryParams:
    place: str
    hauler: str
    garbage: str
    response: str
    carrier_name: str
    carrier_gender: str
    cautioner_name: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    carrier_age: int = 5
    cautioner_age: int = 7
    relation: str = "siblings"
    comfort: str = ""
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
    "garbage": [
        (
            "What is garbage?",
            "Garbage is the leftover stuff people are finished with, like peels, wrappers, or empty cups. It belongs in a trash bin so floors stay clean.",
        )
    ],
    "banana_peel": [
        (
            "Why can a banana peel make a floor messy?",
            "A banana peel is soft and slippery. If it falls on the floor, it can leave a squishy mess and be easy to step on.",
        )
    ],
    "paper": [
        (
            "Why do wrappers blow or skitter around?",
            "Wrappers are light and crinkly, so they slide and flutter easily. That makes them hard to gather if they spill out.",
        )
    ],
    "gloves": [
        (
            "Why do grown-ups wear cleaning gloves for garbage?",
            "Cleaning gloves keep sticky or yucky garbage off your hands. They also make cleanup feel safer and easier.",
        )
    ],
    "bin": [
        (
            "Why is a sturdy bin better than a toy for garbage?",
            "A sturdy bin stands up straighter and is made for heavy, messy things. A toy can wobble or tip too easily.",
        )
    ],
    "tongs": [
        (
            "What are tongs used for?",
            "Tongs help pick things up without touching them with your hands. Grown-ups can use them for hot or messy things.",
        )
    ],
    "wagon": [
        (
            "What is a wagon good for?",
            "A wagon is good for pulling toys or other safe things from one place to another. A small wagon is not the best tool for messy garbage.",
        )
    ],
    "truck": [
        (
            "What is a toy dump truck for?",
            "A toy dump truck is made for pretend play. It is fun for blocks and stuffed animals, but not for real trash.",
        )
    ],
    "dinky": [
        (
            "What does dinky mean?",
            "Dinky means very small and a little flimsy or cute. Something dinky may be fine for play, but not strong enough for a hard job.",
        )
    ],
}
KNOWLEDGE_ORDER = ["garbage", "banana_peel", "paper", "gloves", "bin", "tongs", "wagon", "truck", "dinky"]


def pair_noun(carrier: Entity, cautioner: Entity, relation: str) -> str:
    if relation == "siblings":
        if carrier.type == "boy" and cautioner.type == "boy":
            return "two brothers"
        if carrier.type == "girl" and cautioner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    carrier = f["carrier"]
    cautioner = f["cautioner"]
    hauler = f["hauler_cfg"]
    garbage = f["garbage_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a heartwarming cautionary story for a 3-to-5-year-old that uses the words '
        f'"dinky" and "garbage". A child wants to help with a chore using {hauler.phrase}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {carrier.id} wants to haul garbage with a dinky {hauler.label}, "
            f"but {cautioner.id} wisely stops the mistake before anything spills.",
            f'Write a cozy sibling story with a warning, a safer plan, and a happy ending where the child still gets to help.',
        ]
    if outcome == "cleaned":
        return [
            base,
            f"Tell a story where {carrier.id} tries to carry {garbage.label} in a dinky {hauler.label}, "
            f"the garbage spills, and a calm grown-up teaches a safer way to help.",
            f'Write a heartwarming cautionary tale that begins with a mess and ends with the children helping together the right way.',
        ]
    return [
        base,
        f"Tell a cautionary story where a child ignores a warning about a dinky {hauler.label} and makes a much bigger garbage mess.",
        f"Write a story that teaches why the right tool matters for chores.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    carrier = f["carrier"]
    cautioner = f["cautioner"]
    parent = f["parent"]
    place = f["place_cfg"]
    hauler = f["hauler_cfg"]
    garbage = f["garbage_cfg"]
    response = f["response"]
    relation = world.facts.get("relation", "friends")
    pair = pair_noun(carrier, cautioner, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {carrier.id} and {cautioner.id}, and their {pw}. "
            f"They were trying to handle a real household chore in {place.label}.",
        ),
        (
            f"Why did {carrier.id} want the {hauler.label}?",
            f"{carrier.id} wanted to help take out the garbage, and the little {hauler.label} looked useful. "
            f"But it only looked right because it was small and inviting, not because it was sturdy.",
        ),
        (
            f"Why did {cautioner.id} warn {carrier.id}?",
            f"{cautioner.id} knew the dinky {hauler.label} could wobble with that garbage bag. "
            f"The warning came from seeing that the bag might spill onto {place.floor}.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed {carrier.id}'s mind?",
                f"{carrier.id} finally listened to {cautioner.id}'s warning and chose the safe plan instead. "
                f"That choice mattered because it stopped the garbage from spilling at all.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended warmly: the children helped with the real bin, and the dinky {hauler.label} was saved for toys. "
                f"The ending shows they learned the right job for each thing.",
            )
        )
    elif f["outcome"] == "cleaned":
        qa.append(
            (
                "What happened when the chore was tried the unsafe way?",
                f"The garbage spilled out and made a mess. "
                f"That happened because the bag was too wobbly for the small {hauler.label}.",
            )
        )
        qa.append(
            (
                f"How did their {pw} fix the problem?",
                f"{pw.capitalize()} {response.qa_text}. "
                f"Then {pw} showed the children how to help slowly and safely with the real bin.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the mess cleaned up and the children still getting to help. "
                f"The dinky {hauler.label} went back to being a toy, and the real garbage went into the proper bin.",
            )
        )
    else:
        qa.append(
            (
                "Why was the ending unhappy?",
                f"The cleanup started too late for such a messy spill, so the whole evening stayed sour. "
                f"The mistake began with using a small shaky hauler for a job it was not made to do.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["garbage_cfg"].tags) | set(f["response"].tags) | set(f["hauler_cfg"].tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        hauler="wagon",
        garbage="peels",
        response="rolling_bin",
        carrier_name="Ben",
        carrier_gender="boy",
        cautioner_name="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        carrier_age=5,
        cautioner_age=7,
        relation="siblings",
        comfort="soft bunny",
    ),
    StoryParams(
        place="porch",
        hauler="dump_truck",
        garbage="sticky_cups",
        response="gloves_and_tongs",
        carrier_name="Mia",
        carrier_gender="girl",
        cautioner_name="Noah",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        carrier_age=6,
        cautioner_age=5,
        relation="friends",
        comfort="",
    ),
    StoryParams(
        place="hall",
        hauler="wagon",
        garbage="drippy_plate",
        response="rolling_bin",
        carrier_name="Theo",
        carrier_gender="boy",
        cautioner_name="Ruby",
        cautioner_gender="girl",
        parent="mother",
        trait="gentle",
        delay=0,
        carrier_age=4,
        cautioner_age=8,
        relation="siblings",
        comfort="little bear",
    ),
]


def explain_rejection(hauler: Hauler, garbage: GarbageKind) -> str:
    return (
        f"(No story: {garbage.label} is not risky enough in a {hauler.label} to make a believable cautionary turn here. "
        f"Pick wobblier garbage or a shakier hauler.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores below the common-sense minimum "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.carrier_age, params.cautioner_age, params.trait):
        return "averted"
    garbage = GARBAGE[params.garbage]
    response = RESPONSES[params.response]
    return "cleaned" if is_cleaned(response, garbage, params.delay) else "lingering"


ASP_RULES = r"""
hazard(H, G) :- stability(H, S), wobble(G, W), W > S.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, H, G) :- place(P), hauler(H), garbage(G), hazard(H, G).

careful_now(T) :- trait(T), careful_trait(T).
init_care(5) :- trait(T), careful_now(T).
init_care(3) :- trait(T), not careful_now(T).

older_sibling :- relation(siblings), carrier_age(CA), cautioner_age(ZA), ZA > CA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- older_sibling, authority(A), bold_init(BI), A > BI.

severity(M + D) :- chosen_garbage(G), mess(G, M), delay(D).
cleaned :- chosen_response(R), power(R, P), severity(SV), P >= SV.

outcome(averted) :- averted.
outcome(cleaned) :- not averted, cleaned.
outcome(lingering) :- not averted, not cleaned.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for hid, hauler in HAULERS.items():
        lines.append(asp.fact("hauler", hid))
        lines.append(asp.fact("stability", hid, hauler.stability))
    for gid, garbage in GARBAGE.items():
        lines.append(asp.fact("garbage", gid))
        lines.append(asp.fact("mess", gid, garbage.mess))
        lines.append(asp.fact("wobble", gid, garbage.wobble))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bold_init", int(BOLD_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
            asp.fact("chosen_garbage", params.garbage),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("carrier_age", params.carrier_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outcomes = asp.atoms(model, "outcome")
    return outcomes[0][0] if outcomes else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child tries to help with garbage using a dinky hauler."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hauler", choices=HAULERS)
    ap.add_argument("--garbage", choices=GARBAGE)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra time before cleanup starts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hauler and args.garbage:
        if not hazard_at_risk(HAULERS[args.hauler], GARBAGE[args.garbage]):
            raise StoryError(explain_rejection(HAULERS[args.hauler], GARBAGE[args.garbage]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hauler is None or combo[1] == args.hauler)
        and (args.garbage is None or combo[2] == args.garbage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hauler_id, garbage_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    carrier_name, carrier_gender = _pick_child(rng)
    cautioner_name, cautioner_gender = _pick_child(rng, avoid=carrier_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else 0
    relation = rng.choice(["siblings", "friends"])
    carrier_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    comfort = rng.choice(COMFORTS + ["", ""])
    return StoryParams(
        place=place_id,
        hauler=hauler_id,
        garbage=garbage_id,
        response=response_id,
        carrier_name=carrier_name,
        carrier_gender=carrier_gender,
        cautioner_name=cautioner_name,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        delay=delay,
        carrier_age=carrier_age,
        cautioner_age=cautioner_age,
        relation=relation,
        comfort=comfort,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.hauler not in HAULERS:
        raise StoryError(f"(Unknown hauler: {params.hauler})")
    if params.garbage not in GARBAGE:
        raise StoryError(f"(Unknown garbage kind: {params.garbage})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    hauler = HAULERS[params.hauler]
    garbage = GARBAGE[params.garbage]
    response = RESPONSES[params.response]

    if not hazard_at_risk(hauler, garbage):
        raise StoryError(explain_rejection(hauler, garbage))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=PLACES[params.place],
        hauler=hauler,
        garbage=garbage,
        response=response,
        carrier_name=params.carrier_name,
        carrier_gender=params.carrier_gender,
        cautioner_name=params.cautioner_name,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        carrier_age=params.carrier_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        comfort=params.comfort,
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

    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: valid-combo gate matches ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sense = set(asp_sensible())
    python_sense = {r.id for r in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses:")
        print("  clingo:", sorted(clingo_sense))
        print("  python:", sorted(python_sense))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure for seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke test")
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, hauler, garbage) combos:\n")
        for place_id, hauler_id, garbage_id in combos:
            print(f"  {place_id:8} {hauler_id:12} {garbage_id}")
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
            header = f"### {p.carrier_name} & {p.cautioner_name}: {p.garbage} in {p.hauler} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    place: Place,
    hauler: Hauler,
    garbage: GarbageKind,
    response: Response,
    *,
    carrier_name: str = "Ben",
    carrier_gender: str = "boy",
    cautioner_name: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    carrier_age: int = 5,
    cautioner_age: int = 7,
    relation: str = "siblings",
    comfort: str = "",
) -> World:
    world = World(place=place)
    carrier = world.add(Entity(
        id=carrier_name,
        kind="character",
        type=carrier_gender,
        role="carrier",
        age=carrier_age,
        traits=["helpful"],
        attrs={"relation": relation},
    ))
    cautioner = world.add(Entity(
        id=cautioner_name,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation, "comfort": comfort},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(
        id="floor",
        type="floor",
        label=place.floor,
        washable=True,
    ))
    world.add(Entity(
        id="hauler",
        type="hauler",
        label=hauler.label,
        phrase=hauler.phrase,
    ))
    world.add(Entity(
        id="bag",
        type="garbage_bag",
        label="garbage bag",
        phrase=garbage.bag_phrase,
    ))

    carrier.memes["bold"] = BOLD_INIT
    cautioner.memes["care"] = initial_care(trait)
    world.facts["cleaning_started"] = 0.0
    world.facts["relation"] = relation

    introduce(world, carrier, cautioner, hauler)
    show_bag(world, cautioner, garbage)

    world.para()
    tempt(world, carrier, garbage, place)
    warn(world, cautioner, carrier, hauler, garbage, parent)

    averted = would_avert(relation, carrier_age, cautioner_age, trait)
    severity = 0
    cleaned = True

    if averted:
        back_down(world, carrier, cautioner, parent)
        world.para()
        clean_up(world, parent, response, garbage)
        lesson(world, parent, carrier, cautioner, hauler)
        world.para()
        safe_try(world, parent, carrier, cautioner, response, place)
        cozy_end(world, carrier, cautioner, hauler)
    else:
        defy(world, carrier, cautioner)
        world.para()
        spill(world, carrier, garbage, hauler)
        alarm(world, cautioner, parent)

        severity = spill_severity(garbage, delay)
        world.get("bag").meters["severity"] = float(severity)
        cleaned = is_cleaned(response, garbage, delay)

        world.para()
        if cleaned:
            clean_up(world, parent, response, garbage)
            lesson(world, parent, carrier, cautioner, hauler)
            world.para()
            safe_try(world, parent, carrier, cautioner, response, place)
            cozy_end(world, carrier, cautioner, hauler)
        else:
            world.say(
                f"{parent.label_word.capitalize()} {response.fail}."
            )
            world.say(
                "The floor was finally scrubbed, but the whole evening stayed sour and tired."
            )
            world.say(
                f"{carrier.id} learned that a small shaky hauler can turn one quick chore into a much bigger mess."
            )

    outcome = "averted" if averted else ("cleaned" if cleaned else "lingering")
    world.facts.update(
        carrier=carrier,
        cautioner=cautioner,
        parent=parent,
        place_cfg=place,
        hauler_cfg=hauler,
        garbage_cfg=garbage,
        response=response,
        outcome=outcome,
        severity=severity,
        delay=delay,
        spilled=world.get("bag").meters["spilled"] >= THRESHOLD,
    )
    return world

if __name__ == "__main__":
    main()
