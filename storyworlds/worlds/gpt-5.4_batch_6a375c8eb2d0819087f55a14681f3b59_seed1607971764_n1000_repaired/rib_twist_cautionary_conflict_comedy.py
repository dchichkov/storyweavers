#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rib_twist_cautionary_conflict_comedy.py
==================================================================

A small story world about two children on a rainy day, a high-up object, a bad
idea involving an umbrella rib, a conflict over whether to try it, and a safe,
funny ending with a twist.

The engine models a live world: entities carry physical meters and emotional
memes; a few causal rules push the state forward; the prose reads back what
actually happened. A reasonableness gate refuses combinations where the chosen
safe helper could not honestly retrieve the target. An inline ASP twin mirrors
the Python gate and the simple outcome logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/rib_twist_cautionary_conflict_comedy.py
    python storyworlds/worlds/gpt-5.4/rib_twist_cautionary_conflict_comedy.py --all
    python storyworlds/worlds/gpt-5.4/rib_twist_cautionary_conflict_comedy.py --qa
    python storyworlds/worlds/gpt-5.4/rib_twist_cautionary_conflict_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/rib_twist_cautionary_conflict_comedy.py --verify
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    shelf: str
    room_line: str
    height: int
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
class Target:
    id: str
    label: str
    phrase: str
    goal_guess: str
    actual: str
    reveal_line: str
    grasp: str
    weight: int
    min_height: int
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
class Helper:
    id: str
    label: str
    phrase: str
    reach: int
    carry: int
    grasps: set[str]
    action: str
    qa_text: str
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
class StoryParams:
    place: str
    target: str
    helper: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 5
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("instigator")
    perch = world.get("perch")
    if child.meters["climbing"] < THRESHOLD or child.meters["reaching"] < THRESHOLD:
        return out
    if perch.meters["wobble"] >= THRESHOLD:
        return out
    sig = ("wobble", child.id, perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    perch.meters["wobble"] += 1
    world.get("room").meters["danger"] += 1
    child.memes["alarm"] += 1
    world.get("cautioner").memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_poke(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("instigator")
    umbrella = world.get("umbrella")
    target = world.get("target")
    if child.meters["poking"] < THRESHOLD:
        return out
    sig = ("poke", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    umbrella.meters["bent"] += 1
    target.meters["shifted"] += 1
    child.memes["embarrassment"] += 1
    out.append("__poke__")
    return out


def _r_nearfall(world: World) -> list[str]:
    out: list[str] = []
    perch = world.get("perch")
    target = world.get("target")
    if perch.meters["wobble"] < THRESHOLD or target.meters["shifted"] < THRESHOLD:
        return out
    sig = ("nearfall",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("instigator").meters["nearfall"] += 1
    world.get("instigator").memes["fear"] += 1
    world.get("cautioner").memes["fear"] += 1
    world.get("parent").memes["protective"] += 1
    out.append("__nearfall__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="poke", tag="physical", apply=_r_poke),
    Rule(name="nearfall", tag="physical", apply=_r_nearfall),
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


PLACES = {
    "hallway": Place(
        id="hallway",
        label="the front hallway",
        shelf="the narrow top shelf by the coat hooks",
        room_line="Rain tapped at the door, and coats and boots made the hallway smell like wet weather.",
        height=2,
        tags={"hallway", "high_shelf"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        shelf="the highest pantry shelf",
        room_line="The kitchen windows were gray with rain, and the floor felt too clean for running games.",
        height=3,
        tags={"kitchen", "high_shelf"},
    ),
    "mudroom": Place(
        id="mudroom",
        label="the mudroom",
        shelf="the tall cubby over the bench",
        room_line="The mudroom was crowded with boots, hats, and dripping jackets after the rain.",
        height=2,
        tags={"mudroom", "high_shelf"},
    ),
}

TARGETS = {
    "cookie_tin": Target(
        id="cookie_tin",
        label="cookie tin",
        phrase="a round blue cookie tin",
        goal_guess="cookies",
        actual="button noses and paper mustaches for an old dress-up game",
        reveal_line='When it opened, no cookies tumbled out at all. Inside were button noses and paper mustaches for an old dress-up game.',
        grasp="rim",
        weight=1,
        min_height=2,
        tags={"cookie_tin", "twist"},
    ),
    "party_box": Target(
        id="party_box",
        label="party box",
        phrase="a striped party box",
        goal_guess="party hats",
        actual="three squeaky clown noses and a bag of tiny bells",
        reveal_line='The box was not full of hats. It held three squeaky clown noses and a bag of tiny bells.',
        grasp="box",
        weight=1,
        min_height=2,
        tags={"party_box", "twist"},
    ),
    "soup_pot": Target(
        id="soup_pot",
        label="soup pot",
        phrase="a shiny soup pot with a lid",
        goal_guess="a drum for their game",
        actual="a wooden spoon and a note that said SOUP FOR DINNER, NOT FOR DRUM SOLO",
        reveal_line='Inside was only a wooden spoon and a note that said, "SOUP FOR DINNER, NOT FOR DRUM SOLO."',
        grasp="handle",
        weight=3,
        min_height=3,
        tags={"soup_pot", "twist"},
    ),
    "puppet_bag": Target(
        id="puppet_bag",
        label="puppet bag",
        phrase="a cloth puppet bag",
        goal_guess="a dragon puppet",
        actual="a dragon puppet wearing tiny sunglasses",
        reveal_line='The bag held a dragon puppet wearing tiny sunglasses, which made both children laugh at once.',
        grasp="loop",
        weight=1,
        min_height=2,
        tags={"puppet_bag", "twist"},
    ),
}

HELPERS = {
    "step_ladder": Helper(
        id="step_ladder",
        label="step ladder",
        phrase="a little folding step ladder",
        reach=3,
        carry=3,
        grasps={"rim", "box", "handle", "loop"},
        action="set up the step ladder, climbed carefully, and brought the item down with one steady hand",
        qa_text="used the step ladder and brought it down carefully",
        tags={"ladder", "ask_adult"},
    ),
    "grabber": Helper(
        id="grabber",
        label="grabber claw",
        phrase="a long grabber claw",
        reach=3,
        carry=1,
        grasps={"rim", "box", "loop"},
        action="took out the long grabber claw, pinched the item gently, and lowered it without any wobbling at all",
        qa_text="used the grabber claw to pinch it and lower it safely",
        tags={"grabber", "ask_adult"},
    ),
    "tongs": Helper(
        id="tongs",
        label="kitchen tongs",
        phrase="a pair of kitchen tongs",
        reach=2,
        carry=1,
        grasps={"rim", "loop"},
        action="stood flat on the floor, reached up with the kitchen tongs, and guided the item down into waiting hands",
        qa_text="reached it with the kitchen tongs and guided it down",
        tags={"tongs", "ask_adult"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli"]
TRAITS = ["careful", "sensible", "steady", "thoughtful", "bossy", "curious"]
CAUTIOUS_TRAITS = {"careful", "sensible", "steady", "thoughtful"}


def helper_fits(place: Place, target: Target, helper: Helper) -> bool:
    return (
        helper.reach >= place.height
        and helper.carry >= target.weight
        and target.grasp in helper.grasps
        and place.height >= target.min_height
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for target_id, target in TARGETS.items():
            if place.height < target.min_height:
                continue
            for helper_id, helper in HELPERS.items():
                if helper_fits(place, target, helper):
                    combos.append((place_id, target_id, helper_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    if relation != "siblings":
        return False
    if cautioner_age <= instigator_age:
        return False
    return initial_caution(trait) + 1.0 > 5.0


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("instigator")
    child.meters["climbing"] += 1
    child.meters["reaching"] += 1
    child.meters["poking"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("perch").meters["wobble"] >= THRESHOLD,
        "bent_rib": sim.get("umbrella").meters["bent"] >= THRESHOLD,
        "nearfall": sim.get("instigator").meters["nearfall"] >= THRESHOLD,
    }


def rainy_setup(world: World, a: Entity, b: Entity, target: Target) -> None:
    for kid in (a, b):
        kid.memes["bored"] += 1
        kid.memes["play"] += 1
    place = world.place
    world.say(
        f"One rainy afternoon, {a.id} and {b.id} had used up every quiet game they knew in {place.label}."
    )
    world.say(place.room_line)
    world.say(
        f"Then {a.id} spotted {target.phrase} sitting on {place.shelf}, much too high for small hands."
    )


def goal_guess(world: World, a: Entity, b: Entity, target: Target) -> None:
    world.say(
        f'"I bet it has {target.goal_guess} in it," {a.id} whispered. {b.id} looked up too, and suddenly the shelf seemed much more interesting than the rain.'
    )


def temptation(world: World, a: Entity) -> None:
    a.memes["scheming"] += 1
    world.say(
        f'By the door leaned a closed umbrella, and one skinny metal rib poked out where the cloth had slipped.'
    )
    world.say(
        f'"Easy," said {a.id}. "I can stand on the bench and use that umbrella rib like a hook."'
    )


def warning(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    pred = predict_trouble(world)
    b.memes["caution"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_nearfall"] = pred["nearfall"]
    extra = " and that bent rib could snag the box the wrong way" if pred["bent_rib"] else ""
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. The bench will wobble{extra}. {parent.label_word.capitalize()} said we should ask for help with high things."'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"It will take one second," {a.id} said. {b.id} stayed close, frowning hard, but {a.id} had already grabbed the umbrella.'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked from the high shelf to {b.id}\'s serious face and let the umbrella droop. "Fine," {a.pronoun()} muttered, though not very loudly.'
    )
    world.say(
        f'Together they called for {parent.label_word}, and the bad idea stopped before it could wobble into a problem.'
    )


def attempt(world: World, a: Entity, target: Target) -> None:
    a.meters["climbing"] += 1
    a.meters["reaching"] += 1
    a.meters["poking"] += 1
    propagate(world, narrate=False)
    bench = world.get("perch")
    umbrella = world.get("umbrella")
    world.say(
        f"{a.id} climbed onto the bench, stretched on tiptoe, and lifted the umbrella toward {target.the}."
    )
    if bench.meters["wobble"] >= THRESHOLD:
        world.say("The bench gave a silly little shimmy under those small feet.")
    if umbrella.meters["bent"] >= THRESHOLD:
        world.say(
            "The metal rib scraped the shelf, bent with a tiny ping, and shoved the thing sideways instead of helping."
        )
    if world.get("instigator").meters["nearfall"] >= THRESHOLD:
        world.say(
            f"{a.id}'s knees windmilled, and for one scary blink it looked as if {a.pronoun()} might tumble right into the boot tray."
        )


def alarm(world: World, b: Entity, parent: Entity) -> None:
    b.memes["alarm"] += 1
    world.say(f'"{parent.label_word.upper()}!" {b.id} yelped. "The bench is wobbling!"')


def safe_rescue(world: World, parent: Entity, helper: Helper, target: Target) -> None:
    world.get("target").meters["down"] += 1
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came in fast, steadied the bench, took the umbrella away, and {helper.action}."
    )
    world.say(
        f'In another moment {target.the} was on the floor, while the bent umbrella rib looked very proud of being retired.'
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt down and checked both children from shoes to noses. "No climbing on wobbly furniture for high things," {parent.pronoun()} said. "A laugh is nice, but not if someone bumps their head first."'
    )


def reveal_twist(world: World, target: Target, a: Entity, b: Entity) -> None:
    a.memes["surprise"] += 1
    b.memes["surprise"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(target.reveal_line)


def funny_end(world: World, a: Entity, b: Entity, target: Target) -> None:
    if target.id == "cookie_tin":
        image = f'Soon {a.id} had a paper mustache under {a.pronoun("possessive")} nose, {b.id} wore a button nose, and both of them marched around the hallway like very serious pickle inspectors.'
    elif target.id == "party_box":
        image = f'One by one the clown noses squeaked, the bells jingled, and even {a.id} had to laugh at the ridiculous concert they made.'
    elif target.id == "soup_pot":
        image = f'The note made {b.id} snort, and {a.id} bowed to the soup pot as if it were the strictest audience in the world.'
    else:
        image = f'The dragon puppet in tiny sunglasses stared so grandly that {a.id} and {b.id} both burst out laughing.'
    world.say(
        f"{image} The umbrella stayed by the door, and from then on high shelves meant asking first, not poking upward."
    )


def tell(
    place: Place,
    target: Target,
    helper: Helper,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 5,
) -> World:
    world = World(place=place)
    a = world.add(
        Entity(
            id="instigator",
            kind="character",
            type=instigator_gender,
            label=instigator,
            role="instigator",
            age=instigator_age,
            attrs={"name": instigator, "relation": relation},
        )
    )
    b = world.add(
        Entity(
            id="cautioner",
            kind="character",
            type=cautioner_gender,
            label=cautioner,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"name": cautioner, "relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    world.add(Entity(id="room", type="room", label=place.label))
    world.add(Entity(id="perch", type="bench", label="bench"))
    world.add(Entity(id="umbrella", type="umbrella", label="umbrella"))
    world.add(Entity(id="target", type="target", label=target.label))

    world.facts.update(
        place=place,
        target_cfg=target,
        helper=helper,
        instigator=a,
        cautioner=b,
        parent=parent,
        relation=relation,
        target_guess=target.goal_guess,
    )

    rainy_setup(world, a, b, target)
    goal_guess(world, a, b, target)

    world.para()
    temptation(world, a)
    warning(world, a, b, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent)
        world.para()
        safe_rescue(world, parent, helper, target)
        lesson(world, parent, a, b)
        world.para()
        reveal_twist(world, target, a, b)
        funny_end(world, a, b, target)
        outcome = "averted"
    else:
        defy(world, a, b)
        world.para()
        attempt(world, a, target)
        alarm(world, b, parent)
        world.para()
        safe_rescue(world, parent, helper, target)
        lesson(world, parent, a, b)
        world.para()
        reveal_twist(world, target, a, b)
        funny_end(world, a, b, target)
        outcome = "rescued"

    world.facts.update(
        outcome=outcome,
        averted=averted,
        nearfall=world.get("instigator").meters["nearfall"] >= THRESHOLD,
        bent_rib=world.get("umbrella").meters["bent"] >= THRESHOLD,
        target_down=world.get("target").meters["down"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "rib": [
        (
            "What is an umbrella rib?",
            "An umbrella rib is one of the thin rods that holds the umbrella open. It is not a toy hook, and a bent one can snag things the wrong way.",
        )
    ],
    "high_shelf": [
        (
            "Why are high shelves tricky for children?",
            "High shelves make children stretch, climb, or stand on things that may wobble. That is why it is safer to ask a grown-up for help.",
        )
    ],
    "balance": [
        (
            "Why can a bench wobble when someone climbs on it?",
            "A bench can wobble if someone stands near the edge or reaches too far. When balance shifts suddenly, feet can slip or the bench can rock.",
        )
    ],
    "ask_adult": [
        (
            "What should a child do if something is too high to reach?",
            "Stop and ask a grown-up to help. A safe tool or a careful adult is better than climbing and poking at something overhead.",
        )
    ],
    "ladder": [
        (
            "Why is a step ladder safer than climbing furniture?",
            "A step ladder is made for reaching high places and standing still. Furniture meant for sitting can tip or wobble when someone climbs on it.",
        )
    ],
    "grabber": [
        (
            "What is a grabber claw for?",
            "A grabber claw is a long tool that can pinch light things and bring them closer. It helps people reach without climbing.",
        )
    ],
    "tongs": [
        (
            "What are kitchen tongs used for?",
            "Kitchen tongs are for gripping things from a little farther away, usually while cooking. They can help with a light item, but they are not for rough play.",
        )
    ],
}
KNOWLEDGE_ORDER = ["rib", "high_shelf", "balance", "ask_adult", "ladder", "grabber", "tongs"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    target = f["target_cfg"]
    relation = f["relation"]
    if f["outcome"] == "averted":
        return [
            f'Write a funny cautionary story for a 3-to-5-year-old that includes the word "rib" and has two children tempted to hook down {target.the} with an umbrella.',
            f"Tell a comedy where {a.attrs['name']} wants to poke a high shelf with an umbrella rib, but {b.attrs['name']} talks {a.pronoun('object')} out of it and a grown-up helps instead.",
            f"Write a light story with conflict, a warning about climbing furniture, and a silly twist when {target.the} finally comes down.",
        ]
    rel = "siblings" if relation == "siblings" else "friends"
    return [
        f'Write a funny cautionary story for a 3-to-5-year-old that includes the word "rib", a conflict over a bad idea, and a safe ending.',
        f"Tell a comedy where two {rel} try to reach {target.the} on a high shelf, a child uses an umbrella rib, and a grown-up stops the trouble in time.",
        f"Write a short story with conflict, a near accident, and a twist reveal when the high-up item is finally opened.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    place = f["place"]
    target = f["target_cfg"]
    helper = f["helper"]
    pair = pair_noun(a, b, f["relation"])
    aname = a.attrs["name"]
    bname = b.attrs["name"]
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {aname} and {bname}, on a rainy day with their {pw}. They became interested in {target.the} on {place.shelf}.",
        ),
        (
            f"Why did {aname} want to reach {target.the}?",
            f"{aname} guessed it might hold {target.goal_guess}, which made it feel exciting and important. The guessing is what turned an ordinary high shelf into a tempting problem.",
        ),
        (
            f"What did {bname} warn about?",
            f"{bname} warned that the bench could wobble and that the umbrella rib could snag the item the wrong way. The warning came from seeing that reaching and poking overhead was a bad mix.",
        ),
    ]

    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after {bname} warned {aname}?",
                f"{aname} backed down and called for their {pw} instead of climbing. That changed the whole story, because the wobble stayed a bad idea instead of becoming a real scare.",
            )
        )
    else:
        qa.append(
            (
                f"What went wrong when {aname} tried to use the umbrella?",
                f"The bench wobbled and the metal rib bent with a tiny ping, pushing the item sideways instead of helping. For a moment {aname} nearly tumbled, which is why {bname} shouted for their {pw}.",
            )
        )

    qa.append(
        (
            f"How did their {pw} solve the problem?",
            f"Their {pw} {helper.qa_text}. That worked because the helper could reach the shelf safely without any climbing or wobbling.",
        )
    )
    qa.append(
        (
            f"What was the twist when {target.the} was opened?",
            f"They expected {target.goal_guess}, but inside was {target.actual}. The surprise turned the scary moment into a funny ending.",
        )
    )
    qa.append(
        (
            "What did the children learn?",
            f"They learned not to climb on wobbly furniture or poke at high things with an umbrella rib. Asking a grown-up first kept the ending silly instead of painful.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"rib", "high_shelf", "balance", "ask_adult"} | set(f["helper"].tags)
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, target: Target, helper: Helper) -> str:
    reasons: list[str] = []
    if place.height < target.min_height:
        reasons.append(f"{target.the} would not reasonably be stored at {place.shelf}")
    if helper.reach < place.height:
        reasons.append(f"{helper.label} is too short for {place.shelf}")
    if helper.carry < target.weight:
        reasons.append(f"{helper.label} cannot safely manage something as heavy as {target.the}")
    if target.grasp not in helper.grasps:
        reasons.append(f"{helper.label} cannot get a good hold on {target.the}")
    if not reasons:
        reasons.append("this combination is unreasonable in this world")
    return "(No story: " + "; ".join(reasons) + ".)"


def validate_params(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.target not in TARGETS:
        raise StoryError(f"(No story: unknown target '{params.target}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.relation not in {"siblings", "friends"}:
        raise StoryError(f"(No story: unknown relation '{params.relation}'.)")
    place = PLACES[params.place]
    target = TARGETS[params.target]
    helper = HELPERS[params.helper]
    if not helper_fits(place, target, helper):
        raise StoryError(explain_rejection(place, target, helper))


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait) else "rescued"


CURATED = [
    StoryParams(
        place="hallway",
        target="cookie_tin",
        helper="tongs",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=6,
        cautioner_age=7,
    ),
    StoryParams(
        place="mudroom",
        target="party_box",
        helper="grabber",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="father",
        trait="bossy",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
    ),
    StoryParams(
        place="kitchen",
        target="soup_pot",
        helper="step_ladder",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        relation="siblings",
        instigator_age=7,
        cautioner_age=6,
    ),
    StoryParams(
        place="hallway",
        target="puppet_bag",
        helper="grabber",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ella",
        cautioner_gender="girl",
        parent="father",
        trait="steady",
        relation="siblings",
        instigator_age=4,
        cautioner_age=6,
    ),
]


ASP_RULES = r"""
% Reasonableness gate.
fits(P,T,H) :- place(P), target(T), helper(H),
               shelf_height(P,PH), min_height(T,MH), PH >= MH,
               reach(H,R), R >= PH,
               weight(T,W), carry(H,C), C >= W,
               grasp(T,G), helper_grasp(H,G).

valid(P,T,H) :- fits(P,T,H).

% Outcome logic.
cautious(T) :- trait(T), cautious_trait(T).
older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
init_caution(5) :- trait(T), cautious(T).
init_caution(3) :- trait(T), not cautious(T).
averted :- older_sibling, init_caution(C), C + 1 > 5.
outcome(averted) :- averted.
outcome(rescued) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("shelf_height", place_id, place.height))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("weight", target_id, target.weight))
        lines.append(asp.fact("min_height", target_id, target.min_height))
        lines.append(asp.fact("grasp", target_id, target.grasp))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("reach", helper_id, helper.reach))
        lines.append(asp.fact("carry", helper_id, helper.carry))
        for grasp in sorted(helper.grasps):
            lines.append(asp.fact("helper_grasp", helper_id, grasp))
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
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() smoke sampling at seed {seed}.")
            break

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
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a rainy-day conflict, an umbrella rib, and a safe funny twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, target, helper) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    pool = [n for n in names if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.target and args.helper:
        place = PLACES[args.place]
        target = TARGETS[args.target]
        helper = HELPERS[args.helper]
        if not helper_fits(place, target, helper):
            raise StoryError(explain_rejection(place, target, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.target is None or combo[1] == args.target)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, target_id, helper_id = rng.choice(sorted(combos))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        place=place_id,
        target=target_id,
        helper=helper_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        place=PLACES[params.place],
        target=TARGETS[params.target],
        helper=HELPERS[params.helper],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
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
        print(f"{len(combos)} compatible (place, target, helper) combos:\n")
        for place, target, helper in combos:
            print(f"  {place:8} {target:11} {helper}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.target} at {p.place} ({outcome_of(p)}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
