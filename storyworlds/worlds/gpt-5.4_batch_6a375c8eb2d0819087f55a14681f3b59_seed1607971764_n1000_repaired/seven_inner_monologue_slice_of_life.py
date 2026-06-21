#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/seven_inner_monologue_slice_of_life.py
=================================================================

A standalone story world about a child trying to carry seven pieces of fruit in
one trip. The tiny domain stays close to slice-of-life: a home, a small helpful
task, a moment of impatience, a gentle correction, and an ending image at the
table. The stories use inner monologue as part of the action, not as decoration.

The core constraint is simple and physical:

- the child wants to carry exactly seven pieces of fruit
- an unsafe quick method should feel tempting but should not honestly be good
  enough for all seven
- the fix tool must really be able to carry seven pieces safely and cleanly

Run it
------
    python storyworlds/worlds/gpt-5.4/seven_inner_monologue_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/seven_inner_monologue_slice_of_life.py --qa
    python storyworlds/worlds/gpt-5.4/seven_inner_monologue_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/seven_inner_monologue_slice_of_life.py --produce clementines --method pockets
    python storyworlds/worlds/gpt-5.4/seven_inner_monologue_slice_of_life.py --method toy_truck
    python storyworlds/worlds/gpt-5.4/seven_inner_monologue_slice_of_life.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SEVEN = 7
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    source: str
    table: str
    detail: str
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
class Produce:
    id: str
    label: str
    phrase: str
    plant: str
    color: str
    tenderness: int
    roundness: int
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
class Method:
    id: str
    label: str
    phrase: str
    capacity: int
    squeeze: int
    food_safe: bool
    sense: int
    thought: str
    action: str
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
class FixTool:
    id: str
    label: str
    phrase: str
    capacity: int
    rigid: bool
    food_safe: bool
    carry_verb: str
    ending_image: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "load_count": 0,
            "current_method": "",
            "current_fix": "",
            "produce_cfg": None,
        }

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


def _r_overload(world: World) -> list[str]:
    basket = world.get("load")
    method_id = world.facts.get("current_method", "")
    if not method_id or basket.meters["attempting"] < THRESHOLD:
        return []
    method = METHODS[method_id]
    count = int(world.facts.get("load_count", 0))
    if count <= method.capacity:
        return []
    sig = ("overload", method_id, count)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basket.meters["wobble"] += 1
    child = world.get("child")
    child.memes["worry"] += 1
    return ["__wobble__"]


def _r_squeeze(world: World) -> list[str]:
    basket = world.get("load")
    method_id = world.facts.get("current_method", "")
    produce = world.facts.get("produce_cfg")
    if not method_id or basket.meters["attempting"] < THRESHOLD or produce is None:
        return []
    method = METHODS[method_id]
    if method.squeeze < produce.tenderness:
        return []
    sig = ("squeeze", method_id, produce.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basket.meters["bruised"] += 1
    world.get("child").memes["worry"] += 1
    return ["__bruised__"]


def _r_roll(world: World) -> list[str]:
    basket = world.get("load")
    produce = world.facts.get("produce_cfg")
    if produce is None or basket.meters["wobble"] < THRESHOLD:
        return []
    if produce.roundness < 2:
        return []
    sig = ("roll", produce.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basket.meters["rolled"] += 1
    basket.meters["fallen"] += 1
    world.get("child").memes["alarm"] += 1
    return ["__rolled__"]


CAUSAL_RULES = [
    Rule(name="overload", tag="physical", apply=_r_overload),
    Rule(name="squeeze", tag="physical", apply=_r_squeeze),
    Rule(name="roll", tag="physical", apply=_r_roll),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            made = rule.apply(world)
            if made:
                changed = True
                out.extend(m for m in made if not m.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


def load_risk(method: Method, produce: Produce) -> tuple[bool, bool]:
    wobble = SEVEN > method.capacity
    bruise = method.squeeze >= produce.tenderness
    return wobble, bruise


def safe_fix(fix: FixTool) -> bool:
    return fix.food_safe and fix.rigid and fix.capacity >= SEVEN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for produce_id in sorted(place.affords):
            produce = PRODUCE[produce_id]
            for method_id, method in METHODS.items():
                wobble, bruise = load_risk(method, produce)
                if method.sense < SENSE_MIN or not method.food_safe:
                    continue
                if not (wobble or bruise):
                    continue
                for fix_id, fix in FIX_TOOLS.items():
                    if safe_fix(fix):
                        combos.append((place_id, produce_id, method_id, fix_id))
    return sorted(combos)


def predict_attempt(world: World, method_id: str) -> dict:
    sim = world.copy()
    sim.facts["current_method"] = method_id
    sim.get("load").meters["attempting"] += 1
    propagate(sim, narrate=False)
    load = sim.get("load")
    return {
        "wobble": load.meters["wobble"] >= THRESHOLD,
        "rolled": load.meters["rolled"] >= THRESHOLD,
        "bruised": load.meters["bruised"] >= THRESHOLD,
    }


def outcome_of(params: "StoryParams") -> str:
    if params.produce not in PRODUCE or params.method not in METHODS:
        raise StoryError("(Unknown params: cannot compute outcome.)")
    produce = PRODUCE[params.produce]
    method = METHODS[params.method]
    wobble, bruise = load_risk(method, produce)
    if wobble and bruise:
        return "both"
    if wobble:
        return "roll"
    if bruise:
        return "bruise"
    return "calm"


def introduce(world: World, child: Entity, helper: Entity, place: Place, produce: Produce) -> None:
    child.memes["eager"] += 1
    world.say(
        f"Morning light lay across {place.label}. {place.detail}"
    )
    world.say(
        f"On {place.source}, there were seven {produce.label}, {produce.color} and ready for breakfast."
    )
    world.say(
        f'{child.id} wanted to help carry them to {place.table} before {helper.label_word} poured the tea.'
    )


def inner_plan(world: World, child: Entity, method: Method, produce: Produce) -> None:
    child.memes["pride"] += 1
    world.say(
        f'{child.id} looked at the seven {produce.label} and thought, "{method.thought}"'
    )
    world.say(
        f'{child.pronoun().capitalize()} decided to use {method.phrase}.'
    )


def try_carry(world: World, child: Entity, method: Method, produce: Produce) -> None:
    world.facts["current_method"] = method.id
    load = world.get("load")
    load.meters["attempting"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} {method.action}."
    )
    if load.meters["rolled"] >= THRESHOLD and load.meters["bruised"] >= THRESHOLD:
        world.say(
            f"Halfway there, one {produce.label[:-1] if produce.label.endswith('s') else produce.label} slipped free and another took a soft thumb mark. "
            f"{child.id}'s heart gave a jump."
        )
    elif load.meters["rolled"] >= THRESHOLD:
        world.say(
            f"Halfway there, one {produce.label[:-1] if produce.label.endswith('s') else produce.label} slipped free and rolled in a quick little arc across the floor."
        )
    elif load.meters["bruised"] >= THRESHOLD:
        world.say(
            f"By the time {child.pronoun()} reached the doorway, one of the {produce.label} had a new soft dent where {child.pronoun('possessive')} fingers pressed too hard."
        )
    else:
        world.say(
            f"For one hopeful second, it almost seemed as if the quick plan might work."
        )


def notice_and_help(world: World, helper: Entity, child: Entity, produce: Produce, fix: FixTool) -> None:
    child.memes["embarrassment"] += 1
    child.memes["relief"] += 1
    helper.memes["care"] += 1
    load = world.get("load")
    if load.meters["rolled"] >= THRESHOLD:
        world.say(
            f'{helper.label_word.capitalize()} caught the runaway {produce.label[:-1] if produce.label.endswith("s") else produce.label} with a slippered foot and bent down with a small smile.'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} saw the tight look on {child.id}\'s face and came closer.'
        )
    world.say(
        f'"Seven is a lot for {METHODS[world.facts["current_method"]].label}," {helper.pronoun()} said. '
        f'"Let\'s use {fix.phrase} instead."'
    )


def inner_shift(world: World, child: Entity, load: Entity, produce: Produce, fix: FixTool) -> None:
    if load.meters["rolled"] >= THRESHOLD and load.meters["bruised"] >= THRESHOLD:
        thought = (
            f'I wanted one fast trip, but fast is not helping. {fix.label.capitalize()} first, then careful steps.'
        )
    elif load.meters["rolled"] >= THRESHOLD:
        thought = (
            f'Oh no, they really can run away from me. {fix.label.capitalize()} first, then I can walk slowly.'
        )
    else:
        thought = (
            f'I was squeezing too hard. {fix.label.capitalize()} will let my hands rest.'
        )
    child.memes["lesson"] += 1
    world.say(f'{child.id} thought, "{thought}"')


def carry_safely(world: World, child: Entity, helper: Entity, produce: Produce, fix: FixTool) -> None:
    world.facts["current_fix"] = fix.id
    load = world.get("load")
    load.meters["settled"] = 1.0
    child.memes["calm"] += 1
    child.memes["pride"] += 1
    world.say(
        f"Together they set all seven {produce.label} into {fix.phrase}."
    )
    world.say(
        f"{child.id} {fix.carry_verb} to {world.place.table}, one careful step after another."
    )
    if load.meters["bruised"] >= THRESHOLD:
        world.say(
            f"The marked one was tucked on top, still good enough for breakfast."
        )
    world.say(
        f"When they arrived, {fix.ending_image}"
    )


def ending(world: World, child: Entity, helper: Entity, produce: Produce) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'{helper.label_word.capitalize()} rinsed the fruit, and {child.id} counted softly under {child.pronoun("possessive")} breath: "one, two, three, four, five, six, seven."'
    )
    world.say(
        f"The kitchen felt ordinary and warm again, and that made the little job feel important."
    )
    world.say(
        f'{child.id} thought, "I can still help, just not in such a hurry."'
    )
def tell(
    produce: Produce,
    method: Method,
    fix: Fix,
    child_name: str,
    child_gender: str,
    helper_type: HelperType,
    trait: Trait,
    place=None,
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
    ))
    load = world.add(Entity(
        id="load",
        kind="thing",
        type="produce_group",
        label=produce.label,
        phrase=produce.phrase,
    ))

    world.facts.update(
        place=place,
        produce_cfg=produce,
        method_cfg=method,
        fix_cfg=fix,
        child=child,
        helper=helper,
        load_count=SEVEN,
    )

    introduce(world, child, helper, place, produce)
    world.para()
    inner_plan(world, child, method, produce)
    pred = predict_attempt(world, method.id)
    world.facts["predicted_roll"] = pred["rolled"]
    world.facts["predicted_bruise"] = pred["bruised"]
    try_carry(world, child, method, produce)
    world.para()
    notice_and_help(world, helper, child, produce, fix)
    inner_shift(world, child, load, produce, fix)
    carry_safely(world, child, helper, produce, fix)
    world.para()
    ending(world, child, helper, produce)

    world.facts.update(
        outcome=outcome_of(StoryParams(
            place=place.id,
            produce=produce.id,
            method=method.id,
            fix=fix.id,
            name=child_name,
            gender=child_gender,
            helper=helper_type,
            trait=trait,
            seed=None,
        )),
        rolled=load.meters["rolled"] >= THRESHOLD,
        bruised=load.meters["bruised"] >= THRESHOLD,
        settled=load.meters["settled"] >= THRESHOLD,
    )
    return world
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


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        source="the cool counter by the window",
        table="the small breakfast table",
        detail="A dish towel hung from the oven handle, and a thin stripe of sun touched the floorboards.",
        affords={"plums", "clementines"},
        tags={"kitchen"},
    ),
    "balcony": Place(
        id="balcony",
        label="the narrow balcony",
        source="the little crate beside the door",
        table="the table just inside",
        detail="The rail was still cool from the night, and the plants nodded in the soft air.",
        affords={"apricots", "clementines"},
        tags={"balcony"},
    ),
    "backyard": Place(
        id="backyard",
        label="the backyard",
        source="the old wooden step under the tree",
        table="the table on the porch",
        detail="The grass held a few bright drops of water, and the porch smelled faintly of toast.",
        affords={"plums", "apricots"},
        tags={"yard"},
    ),
}

PRODUCE = {
    "plums": Produce(
        id="plums",
        label="plums",
        phrase="seven ripe plums",
        plant="tree",
        color="purple-blue",
        tenderness=2,
        roundness=2,
        tags={"plums", "fruit"},
    ),
    "apricots": Produce(
        id="apricots",
        label="apricots",
        phrase="seven soft apricots",
        plant="tree",
        color="golden",
        tenderness=2,
        roundness=1,
        tags={"apricots", "fruit"},
    ),
    "clementines": Produce(
        id="clementines",
        label="clementines",
        phrase="seven bright clementines",
        plant="bowl",
        color="orange",
        tenderness=1,
        roundness=2,
        tags={"clementines", "fruit"},
    ),
}

METHODS = {
    "hands": Method(
        id="hands",
        label="two hands",
        phrase="both hands and the crook of one elbow",
        capacity=3,
        squeeze=1,
        food_safe=True,
        sense=2,
        thought="Seven is a lot, but I am big enough now. If I stack them carefully, I can do it in one trip.",
        action="stacked fruit against the warm front of the shirt and started walking",
        tags={"hands"},
    ),
    "shirt_hem": Method(
        id="shirt_hem",
        label="a shirt hem",
        phrase="the front of the shirt folded into a little pouch",
        capacity=5,
        squeeze=1,
        food_safe=True,
        sense=2,
        thought="If I make my shirt into a pocket, I will be done before anyone can tell me to slow down.",
        action="pinched up the shirt hem, tipped the fruit in, and took quick careful steps",
        tags={"shirt"},
    ),
    "pockets": Method(
        id="pockets",
        label="pockets",
        phrase="deep pockets",
        capacity=4,
        squeeze=2,
        food_safe=True,
        sense=2,
        thought="Pockets hold treasures all the time. They can hold breakfast too, just for one little walk.",
        action="filled both pockets and tried to balance the rest in small crowded hands",
        tags={"pockets"},
    ),
    "toy_truck": Method(
        id="toy_truck",
        label="a toy dump truck",
        phrase="a toy dump truck from under the bench",
        capacity=7,
        squeeze=0,
        food_safe=False,
        sense=1,
        thought="The truck can carry seven, easy.",
        action="loaded the fruit into a toy truck and pushed it along",
        tags={"toy"},
    ),
}

FIX_TOOLS = {
    "blue_bowl": FixTool(
        id="blue_bowl",
        label="blue bowl",
        phrase="the blue bowl",
        capacity=8,
        rigid=True,
        food_safe=True,
        carry_verb="carried the bowl with both hands",
        ending_image="all seven sat together in a neat shining pile, as if they had wanted a proper place all along.",
        tags={"bowl"},
    ),
    "woven_basket": FixTool(
        id="woven_basket",
        label="woven basket",
        phrase="the little woven basket",
        capacity=8,
        rigid=True,
        food_safe=True,
        carry_verb="held the basket by both small handles",
        ending_image="the seven pieces of fruit rested against one another without slipping, bright as marbles and much calmer.",
        tags={"basket"},
    ),
    "colander": FixTool(
        id="colander",
        label="colander",
        phrase="the white colander",
        capacity=8,
        rigid=True,
        food_safe=True,
        carry_verb="hugged the colander to the middle of the chest",
        ending_image="all seven were there, safe behind the curved metal sides, waiting for water and breakfast.",
        tags={"colander"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Lucy", "Zoe", "Ella", "Maya"]
BOY_NAMES = ["Theo", "Ben", "Sam", "Leo", "Noah", "Eli", "Max", "Finn"]
TRAITS = ["careful", "busy", "eager", "thoughtful", "helpful", "sleepy"]


KNOWLEDGE = {
    "plums": [(
        "What happens when a plum gets bumped too hard?",
        "A plum can bruise and turn soft where it was pressed or dropped. The fruit is often still fine to eat, but it needs gentler hands."
    )],
    "apricots": [(
        "Why do apricots need careful hands?",
        "Apricots are soft fruit, so they can dent or bruise when someone squeezes them. Carrying them in a bowl or basket gives them room."
    )],
    "clementines": [(
        "Why do clementines roll away so easily?",
        "Clementines are round, so they can start rolling when they slip from your hands. A bowl with sides helps keep them together."
    )],
    "pockets": [(
        "Why are pockets not a good place for fruit?",
        "Pockets squeeze fruit and make it bump against your legs when you walk. Soft fruit can bruise, and round fruit can pop out when you reach in."
    )],
    "shirt": [(
        "Why can a shirt pouch spill things?",
        "A shirt is soft and floppy, so it does not have firm sides. If you carry too much in it, things can wobble or slide out."
    )],
    "bowl": [(
        "Why is a bowl good for carrying fruit?",
        "A bowl has curved sides that help keep fruit together. When you hold it with both hands, the fruit has a safer place to rest."
    )],
    "basket": [(
        "What makes a basket useful for small jobs?",
        "A basket gives things one place to sit while you carry them. It is easier to walk slowly and keep them steady."
    )],
    "colander": [(
        "What is a colander?",
        "A colander is a bowl with little holes in it. People often use it to wash fruit or vegetables."
    )],
    "fruit": [(
        "Why is it easier to carry many things in a container?",
        "A container holds the group together, so your hands do not have to pinch every piece at once. That means less dropping and less squishing."
    )],
}
KNOWLEDGE_ORDER = [
    "plums",
    "apricots",
    "clementines",
    "pockets",
    "shirt",
    "bowl",
    "basket",
    "colander",
    "fruit",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    produce = f["produce_cfg"]
    method = f["method_cfg"]
    fix = f["fix_cfg"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that uses inner monologue and includes the word "seven". The child should try to help with {produce.label} at home.',
        f"Tell a gentle home story where {child.id} tries to carry seven {produce.label} using {method.label}, then learns to slow down and use {fix.label} instead.",
        f"Write a small everyday story about a child helping {helper.label_word} with breakfast, thinking private thoughts along the way, and ending with a calmer second try.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    produce = f["produce_cfg"]
    method = f["method_cfg"]
    fix = f["fix_cfg"]
    place = f["place"]
    out = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child trying to help at home, and {helper.label_word} nearby. The story follows one small breakfast job from the first idea to the safer second try."
        ),
        (
            f"Why did {child.id} try to carry the fruit alone?",
            f"{child.id} wanted to be helpful and wanted the little job done quickly. The inner thoughts show that {child.pronoun()} also wanted to prove {child.pronoun()} was big enough for seven {produce.label} in one trip."
        ),
        (
            f"Where were the seven {produce.label} going?",
            f"They were being carried from {place.source} to {place.table} for breakfast. That ordinary trip is what turns into the story's problem and solution."
        ),
        (
            f"What went wrong with {method.label}?",
            _qa_outcome_text(child, produce, method, out)
        ),
        (
            f"How did {helper.label_word} help?",
            f'{helper.label_word.capitalize()} did not scold. {helper.pronoun().capitalize()} noticed what the quick plan was doing, suggested {fix.phrase}, and helped {child.id} start again in a calmer way.'
        ),
        (
            "How did the story end?",
            f"They reached the table with all seven {produce.label} gathered safely in {fix.phrase}. The ending image shows that the child still got to help, but with slower hands and a better tool."
        ),
    ]
    return qa


def _qa_outcome_text(child: Entity, produce: Produce, method: Method, outcome: str) -> str:
    if outcome == "both":
        return (
            f"{method.label.capitalize()} made two problems at once: there was too much to hold, and the fruit was pressed too tightly. One {produce.label[:-1] if produce.label.endswith('s') else produce.label} slipped away while another was bruised, which is why {child.id} suddenly felt worried."
        )
    if outcome == "roll":
        return (
            f"{method.label.capitalize()} could not safely hold all seven {produce.label}, so one slipped and rolled away. The trouble came from trying to hurry with more fruit than that method could really carry."
        )
    if outcome == "bruise":
        return (
            f"{method.label.capitalize()} pressed too hard on the soft fruit, so one piece ended up dented. Nothing terrible happened, but the mark showed that the plan was rougher than it looked."
        )
    return (
        f"This time nothing serious went wrong, but the world still treats the quick method as weak. The safer container mattered because seven pieces of fruit needed a steadier place."
    )


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["produce_cfg"].tags)
    tags |= set(world.facts["method_cfg"].tags)
    tags |= set(world.facts["fix_cfg"].tags)
    tags.add("fruit")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:13}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} predicted_roll={world.facts.get('predicted_roll')} predicted_bruise={world.facts.get('predicted_bruise')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    place: str
    produce: str
    method: str
    fix: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        place="kitchen",
        produce="plums",
        method="shirt_hem",
        fix="blue_bowl",
        name="Mina",
        gender="girl",
        helper="grandmother",
        trait="eager",
        seed=None,
    ),
    StoryParams(
        place="balcony",
        produce="clementines",
        method="hands",
        fix="woven_basket",
        name="Theo",
        gender="boy",
        helper="father",
        trait="helpful",
        seed=None,
    ),
    StoryParams(
        place="backyard",
        produce="apricots",
        method="pockets",
        fix="colander",
        name="Lila",
        gender="girl",
        helper="mother",
        trait="busy",
        seed=None,
    ),
    StoryParams(
        place="kitchen",
        produce="clementines",
        method="pockets",
        fix="blue_bowl",
        name="Sam",
        gender="boy",
        helper="grandfather",
        trait="thoughtful",
        seed=None,
    ),
]


def explain_place(place_id: str, produce_id: str) -> str:
    place = PLACES[place_id]
    return (
        f"(No story: {produce_id} are not part of the little world at {place.label}. "
        f"Try one of: {', '.join(sorted(place.affords))}.)"
    )


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    if not method.food_safe:
        return (
            f"(Refusing method '{method_id}': {method.label} is not a sensible food-carrying choice here. "
            f"Pick a tempting but ordinary quick method like hands, shirt_hem, or pockets.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method_id}': it scores too low on common sense.)"
        )
    return (
        f"(No story: {method.label} is not the right kind of troubled shortcut for this world.)"
    )


def explain_fix(fix_id: str) -> str:
    fix = FIX_TOOLS[fix_id]
    return (
        f"(No story: {fix.label} is not a safe container for seven pieces of fruit in this world. "
        f"The fix must be food-safe, rigid, and large enough for all seven.)"
    )


ASP_RULES = r"""
% basic gate
unsafe_method(M, P) :- method(M), produce(P), count(C), capacity(M, K), C > K.
unsafe_method(M, P) :- method(M), produce(P), squeeze(M, S), tenderness(P, T), S >= T.

safe_fix(F) :- fix(F), fix_food_safe(F), rigid(F), fix_capacity(F, K), count(C), K >= C.

valid(Place, P, M, F) :-
    affords(Place, P),
    method(M), method_food_safe(M), sense(M, S), sense_min(Min), S >= Min,
    unsafe_method(M, P),
    safe_fix(F).

% outcome
rolled :- chosen_method(M), chosen_produce(P), count(C), capacity(M, K), C > K, roundness(P, R), R >= 2.
bruised :- chosen_method(M), chosen_produce(P), squeeze(M, S), tenderness(P, T), S >= T.

outcome(both) :- rolled, bruised.
outcome(roll) :- rolled, not bruised.
outcome(bruise) :- bruised, not rolled.
outcome(calm) :- not rolled, not bruised.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("count", SEVEN), asp.fact("sense_min", SENSE_MIN)]
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for produce_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, produce_id))
    for produce_id, produce in PRODUCE.items():
        lines.append(asp.fact("produce", produce_id))
        lines.append(asp.fact("tenderness", produce_id, produce.tenderness))
        lines.append(asp.fact("roundness", produce_id, produce.roundness))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("capacity", method_id, method.capacity))
        lines.append(asp.fact("squeeze", method_id, method.squeeze))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.food_safe:
            lines.append(asp.fact("method_food_safe", method_id))
    for fix_id, fix in FIX_TOOLS.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("fix_capacity", fix_id, fix.capacity))
        if fix.food_safe:
            lines.append(asp.fact("fix_food_safe", fix_id))
        if fix.rigid:
            lines.append(asp.fact("rigid", fix_id))
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
        asp.fact("chosen_produce", params.produce),
        asp.fact("chosen_method", params.method),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child tries to carry seven pieces of fruit in one trip and learns a calmer way."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--produce", choices=PRODUCE)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--fix", choices=FIX_TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.produce and args.produce not in PLACES[args.place].affords:
        raise StoryError(explain_place(args.place, args.produce))
    if args.method:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN or not method.food_safe:
            raise StoryError(explain_method(args.method))
    if args.fix:
        if not safe_fix(FIX_TOOLS[args.fix]):
            raise StoryError(explain_fix(args.fix))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.produce is None or combo[1] == args.produce)
        and (args.method is None or combo[2] == args.method)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, produce_id, method_id, fix_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        produce=produce_id,
        method=method_id,
        fix=fix_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.produce not in PRODUCE:
        raise StoryError(f"(Unknown produce: {params.produce})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.fix not in FIX_TOOLS:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.produce not in PLACES[params.place].affords:
        raise StoryError(explain_place(params.place, params.produce))
    method = METHODS[params.method]
    fix = FIX_TOOLS[params.fix]
    produce = PRODUCE[params.produce]
    wobble, bruise = load_risk(method, produce)
    if method.sense < SENSE_MIN or not method.food_safe:
        raise StoryError(explain_method(params.method))
    if not (wobble or bruise):
        raise StoryError("(No story: that method would not honestly create this world's small problem.)")
    if not safe_fix(fix):
        raise StoryError(explain_fix(params.fix))

    world = tell(
        place=PLACES[params.place],
        produce=produce,
        method=method,
        fix=fix,
        child_name=params.name,
        child_gender=params.gender,
        helper_type=params.helper,
        trait=params.trait,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py_out} asp={asp_out}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        sink = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = sink
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if "seven" not in sample.story.lower():
            raise StoryError("story did not mention seven")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, produce, method, fix) combos:\n")
        for place, produce, method, fix in combos:
            print(f"  {place:9} {produce:12} {method:10} {fix}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.produce} at {p.place} ({p.method} -> {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
