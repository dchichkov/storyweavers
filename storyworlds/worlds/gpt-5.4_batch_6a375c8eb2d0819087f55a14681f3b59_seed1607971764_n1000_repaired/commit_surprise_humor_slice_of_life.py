#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/commit_surprise_humor_slice_of_life.py
=================================================================

A standalone story world about two children trying to carry a small surprise
snack to a grown-up. One child says, "I commit to carrying it myself," the
other sees the wobble coming, and the story turns on whether they accept help,
use a steady method, or make a funny little spill and recover together.

The domain is deliberately small and classical:

- typed entities with physical meters and emotional memes
- a short state-driven screenplay with a clear beginning, turn, and ending
- a Python reasonableness gate plus an inline ASP twin
- three QA sets grounded in world state, not parsed from English

Run it
------
    python storyworlds/worlds/gpt-5.4/commit_surprise_humor_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/commit_surprise_humor_slice_of_life.py --snack soup --carrier tea_tray --route stairs
    python storyworlds/worlds/gpt-5.4/commit_surprise_humor_slice_of_life.py --response dash
    python storyworlds/worlds/gpt-5.4/commit_surprise_humor_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/commit_surprise_humor_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/commit_surprise_humor_slice_of_life.py --verify
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
CONFIDENT_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    vessel: str = ""
    supported_vessels: set[str] = field(default_factory=set)
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
class Snack:
    id: str
    label: str
    phrase: str
    vessel: str
    wobble: int
    smear: str
    remade_as: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    stability: int
    supports: set[str] = field(default_factory=set)
    comic: str = ""
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
class Route:
    id: str
    label: str
    destination: str
    bumps: int
    detail: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"eager", "cautioner"}]


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
    carrier = world.entities.get("carrier")
    snack = world.entities.get("snack")
    floor = world.entities.get("floor")
    eager = world.entities.get("eager")
    cautioner = world.entities.get("cautioner")
    if not all((carrier, snack, floor, eager, cautioner)):
        return out
    if carrier.meters["shaky"] < THRESHOLD:
        return out
    sig = ("wobble", int(carrier.meters["shaky"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snack.meters["wobble"] += 1
    eager.memes["alarm"] += 1
    cautioner.memes["alarm"] += 1
    floor.meters["risk"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    snack = world.entities.get("snack")
    floor = world.entities.get("floor")
    parent = world.entities.get("parent")
    eager = world.entities.get("eager")
    cautioner = world.entities.get("cautioner")
    if not all((snack, floor, parent, eager, cautioner)):
        return out
    if snack.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill", world.facts.get("snack_id", "?"))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    floor.meters["mess"] += 1
    parent.meters["cleanup"] += 1
    eager.memes["embarrassed"] += 1
    cautioner.memes["concern"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def supports(snack: Snack, carrier: Carrier) -> bool:
    return snack.vessel in carrier.supports


def needed_steadying(snack: Snack, carrier: Carrier, route: Route) -> int:
    return max(1, snack.wobble + route.bumps - carrier.stability)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def possible(snack: Snack, carrier: Carrier, route: Route) -> bool:
    if not supports(snack, carrier):
        return False
    need = needed_steadying(snack, carrier, route)
    return any(r.power >= need for r in sensible_responses())


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, eager_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > eager_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > CONFIDENT_INIT


def predict_spill(world: World) -> dict:
    sim = world.copy()
    carrier = sim.get("carrier")
    snack = sim.get("snack")
    carrier.meters["shaky"] = float(sim.facts["need"])
    propagate(sim, narrate=False)
    spilled = sim.facts["response_power"] < sim.facts["need"]
    if spilled:
        snack.meters["spilled"] += 1
        propagate(sim, narrate=False)
    return {
        "wobble": snack.meters["wobble"] >= THRESHOLD,
        "spill": snack.meters["spilled"] >= THRESHOLD,
        "mess": sim.get("floor").meters["mess"],
    }


def introduce(world: World, eager: Entity, cautioner: Entity, parent: Entity, route: Route) -> None:
    world.say(
        f"Late one ordinary afternoon, {eager.id} and {cautioner.id} were in the kitchen while "
        f"{parent.label_word} rested {route.destination}. {route.detail}"
    )
    world.say(
        f"The house felt so quiet that even a spoon tapping a cup sounded important."
    )


def plan_surprise(world: World, eager: Entity, cautioner: Entity, snack: Snack, parent: Entity) -> None:
    eager.memes["care"] += 1
    cautioner.memes["care"] += 1
    world.say(
        f'"Let\'s bring {parent.label_word} {snack.phrase} as a surprise," {cautioner.id} whispered.'
    )
    world.say(
        f'{eager.id} grinned. "Yes. I commit to carrying it myself."'
    )


def prepare(world: World, eager: Entity, cautioner: Entity, snack: Snack, carrier: Carrier) -> None:
    world.say(
        f"They set {snack.label} on {carrier.phrase}. {carrier.comic}"
    )
    if snack.id == "cocoa":
        world.say(
            f"A little brown foam kissed the rim, and {eager.id} accidentally made a tiny cocoa mustache while checking the smell."
        )
    elif snack.id == "jelly_toast":
        world.say(
            f"The jelly shone so brightly that both children leaned in at the same time and bumped foreheads."
        )
    elif snack.id == "soup":
        world.say(
            f"The soup made one soft slosh, as if it had already started telling a joke."
        )
    else:
        world.say(
            f"The apple slices slid into a neat fan, and {cautioner.id} straightened them until they looked very serious for such a small snack."
        )


def warn(world: World, eager: Entity, cautioner: Entity, snack: Snack, carrier: Carrier, route: Route, parent: Entity) -> None:
    pred = predict_spill(world)
    cautioner.memes["caution"] += 1
    world.facts["predicted_spill"] = pred["spill"]
    need = world.facts["need"]
    extra = ""
    if route.id == "dog_bed":
        extra = " The sleepy dog was right in the bend of the hallway."
    elif route.id == "stairs":
        extra = " Stairs made every wobble feel bigger."
    elif route.id == "rug":
        extra = " The fluffy rug loved catching little feet."
    world.say(
        f'{cautioner.id} looked at the {carrier.label}, then at the path. '
        f'"If it tilts even once, the {snack.label} could spill," {cautioner.pronoun()} said. '
        f'"We need a steady plan."{extra}'
    )
    world.say(
        f'{cautioner.id} was not trying to spoil the surprise. {cautioner.pronoun().capitalize()} was trying to keep the surprise off the floor.'
    )
    world.facts["predicted_need_words"] = need


def back_down(world: World, eager: Entity, cautioner: Entity, response: Response, parent: Entity, snack: Snack) -> None:
    eager.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    world.say(
        f'{eager.id} looked at the wobble, then at {cautioner.id}, and gave a small nod. '
        f'"Okay," {eager.pronoun()} said. "I can commit to doing it the smart way instead."'
    )
    world.say(
        f"They used {response.text}, and the surprise stayed secret all the way to {parent.label_word}."
    )


def set_off(world: World, eager: Entity, response: Response, route: Route) -> None:
    eager.memes["pride"] += 1
    world.say(
        f'They started along {route.label}, using {response.text}.'
    )


def near_wobble(world: World, snack: Snack, carrier: Carrier, route: Route) -> None:
    carrier.meters["shaky"] = float(world.facts["need"])
    propagate(world, narrate=False)
    world.say(
        f"Halfway there, {carrier.phrase} gave a tiny wobble. The {snack.label} shivered, and everyone froze for one breath."
    )
    if route.id == "stairs":
        world.say("One drop almost escaped over the edge, then thought better of it.")
    elif route.id == "rug":
        world.say("A toe caught in the rug fringe, but only for a blink.")
    elif route.id == "dog_bed":
        world.say("The dog opened one eye as if to judge the whole project.")
    else:
        world.say("Even the hallway seemed to lean in and watch.")


def arrive_ok(world: World, eager: Entity, cautioner: Entity, parent: Entity, snack: Snack, response: Response) -> None:
    for kid in (eager, cautioner):
        kid.memes["joy"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"But {response.text} worked, and the {snack.label} reached {parent.label_word} safely."
    )
    world.say(
        f'{parent.label_word.capitalize()} looked up, blinked in surprise, and then laughed at {eager.id}\'s still-noticeable snack face.'
    )
    if snack.id == "cocoa":
        world.say(
            f'"I was surprised by the cocoa," {parent.pronoun()} said, "but I was even more surprised by the mustache."'
        )
    elif snack.id == "soup":
        world.say(
            f'"A secret soup delivery?" {parent.pronoun()} said. "That is the most serious silly thing I have seen today."'
        )
    elif snack.id == "jelly_toast":
        world.say(
            f'"You brought me toast and matching foreheads," {parent.pronoun()} said, and all three of them laughed.'
        )
    else:
        world.say(
            f'"A fancy snack parade just for me?" {parent.pronoun()} said, smiling so hard that both children giggled too.'
        )


def spill(world: World, eager: Entity, cautioner: Entity, parent: Entity, snack: Snack, route: Route, response: Response) -> None:
    world.get("snack").meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the plan slipped. They {response.fail}, and the {snack.label} landed with a soft, ridiculous splat."
    )
    if snack.id == "soup":
        world.say("For one amazed second, a carrot slice rode down the tray like a tiny orange sled.")
    elif snack.id == "jelly_toast":
        world.say("The toast flipped once and landed jelly-side down, as if it knew exactly how to be dramatic.")
    elif snack.id == "cocoa":
        world.say("A brown dot appeared on {0}'s nose before {0} even noticed.".format(eager.id))
    else:
        world.say("One apple slice skated away farther than seemed fair.")
    world.say(
        f'{parent.label_word.capitalize()} hurried over, saw that everyone was safe, and let out the kind of laugh that comes after a scare turns out small.'
    )
    world.say(
        f'"No one is in trouble," {parent.pronoun()} said. "The floor can survive a surprise."'
    )
    eager.memes["embarrassed"] += 1
    cautioner.memes["care"] += 1


def remake(world: World, eager: Entity, cautioner: Entity, parent: Entity, snack: Snack) -> None:
    eager.memes["lesson"] += 1
    cautioner.memes["lesson"] += 1
    eager.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    world.say(
        f"Together they wiped up the spill and made {snack.remade_as} instead."
    )
    world.say(
        f"This time they carried it together, slower and wiser, and the second surprise reached {parent.label_word} without any acrobatics."
    )
    world.say(
        f'{parent.label_word.capitalize()} took a bite, smiled, and said, "My favorite part is that you tried, cleaned up, and tried again."'
    )


def closing_image(world: World, eager: Entity, cautioner: Entity, parent: Entity, snack: Snack, outcome: str) -> None:
    if outcome == "spilled":
        world.say(
            f"By the end, the kitchen smelled better than before, the floor was clean again, and {eager.id} could finally laugh about the whole thing."
        )
    else:
        world.say(
            f"By the end, the snack was gone, the surprise had landed, and the quiet afternoon felt warmer around the edges."
        )


def tell(
    snack: Snack,
    carrier: Carrier,
    route: Route,
    response: Response,
    eager_name: str = "Milo",
    eager_gender: str = "boy",
    cautioner_name: str = "June",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    relation: str = "siblings",
    eager_age: int = 5,
    cautioner_age: int = 7,
) -> World:
    world = World()
    eager = world.add(Entity(
        id=eager_name,
        kind="character",
        type=eager_gender,
        role="eager",
        age=eager_age,
        attrs={"relation": relation},
    ))
    cautioner = world.add(Entity(
        id=cautioner_name,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="floor", type="floor", label="the floor"))
    world.add(Entity(id="snack", type="snack", label=snack.label, vessel=snack.vessel))
    world.add(Entity(
        id="carrier",
        type="carrier",
        label=carrier.label,
        supported_vessels=set(carrier.supports),
    ))

    eager.memes["confidence"] = CONFIDENT_INIT
    cautioner.memes["caution"] = initial_caution(trait)

    need = needed_steadying(snack, carrier, route)
    world.facts.update(
        snack_cfg=snack,
        carrier_cfg=carrier,
        route=route,
        response=response,
        eager=eager,
        cautioner=cautioner,
        parent=parent,
        snack_id=snack.id,
        need=need,
        response_power=response.power,
        relation=relation,
    )

    introduce(world, eager, cautioner, parent, route)
    plan_surprise(world, eager, cautioner, snack, parent)

    world.para()
    prepare(world, eager, cautioner, snack, carrier)
    warn(world, eager, cautioner, snack, carrier, route, parent)

    averted = would_avert(relation, eager_age, cautioner_age, trait)
    contained = False

    world.para()
    if averted:
        back_down(world, eager, cautioner, response, parent, snack)
        near_wobble(world, snack, world.get("carrier"), route)
        arrive_ok(world, eager, cautioner, parent, snack, response)
        outcome = "averted"
        contained = True
    else:
        set_off(world, eager, response, route)
        near_wobble(world, snack, world.get("carrier"), route)
        contained = response.power >= need
        world.para()
        if contained:
            arrive_ok(world, eager, cautioner, parent, snack, response)
            outcome = "arrived"
        else:
            spill(world, eager, cautioner, parent, snack, route, response)
            world.para()
            remake(world, eager, cautioner, parent, snack)
            outcome = "spilled"

    world.para()
    closing_image(world, eager, cautioner, parent, snack, outcome)

    world.facts.update(
        outcome=outcome,
        contained=contained,
        averted=averted,
        spill_happened=outcome == "spilled",
        delivered=outcome in {"averted", "arrived"},
    )
    return world


SNACKS = {
    "cocoa": Snack(
        id="cocoa",
        label="hot cocoa",
        phrase="a mug of hot cocoa",
        vessel="mug",
        wobble=2,
        smear="brown cocoa on the floor",
        remade_as="buttered toast cut into stars",
        tags={"cocoa", "mug"},
    ),
    "soup": Snack(
        id="soup",
        label="tomato soup",
        phrase="a warm bowl of tomato soup",
        vessel="bowl",
        wobble=3,
        smear="red soup on the floor",
        remade_as="crackers and apple slices",
        tags={"soup", "bowl"},
    ),
    "jelly_toast": Snack(
        id="jelly_toast",
        label="jelly toast",
        phrase="a plate of jelly toast",
        vessel="plate",
        wobble=2,
        smear="a shiny jelly blot on the floor",
        remade_as="plain toast with smiling banana slices",
        tags={"toast", "plate"},
    ),
    "apple_slices": Snack(
        id="apple_slices",
        label="apple slices",
        phrase="a plate of apple slices",
        vessel="plate",
        wobble=1,
        smear="one pale apple fan on the floor",
        remade_as="apple slices with peanut butter dots",
        tags={"apple", "plate"},
    ),
}

CARRIERS = {
    "sturdy_tray": Carrier(
        id="sturdy_tray",
        label="sturdy tray",
        phrase="a sturdy wooden tray with handles",
        stability=3,
        supports={"mug", "bowl", "plate"},
        comic="It looked so solid that even the napkin seemed to sit up straighter.",
        tags={"tray"},
    ),
    "cookie_sheet": Carrier(
        id="cookie_sheet",
        label="cookie sheet",
        phrase="a shiny cookie sheet",
        stability=2,
        supports={"mug", "plate"},
        comic="It made the snack look as if it were about to be baked instead of delivered.",
        tags={"tray"},
    ),
    "tea_tray": Carrier(
        id="tea_tray",
        label="tiny tea tray",
        phrase="a tiny toy tea tray",
        stability=1,
        supports={"mug", "plate"},
        comic="It was charming, which is not always the same thing as helpful.",
        tags={"tray"},
    ),
    "placemat": Carrier(
        id="placemat",
        label="placemat",
        phrase="a flat placemat",
        stability=0,
        supports={"plate"},
        comic="It had no handles at all, only optimism.",
        tags={"tray"},
    ),
}

ROUTES = {
    "hall": Route(
        id="hall",
        label="the short hall",
        destination="on the couch in the living room",
        bumps=1,
        detail="From the kitchen door they could see the short hall leading to the living room.",
        tags={"hall"},
    ),
    "rug": Route(
        id="rug",
        label="the long way around the fluffy rug",
        destination="in the armchair by the window",
        bumps=2,
        detail="A fluffy rug lay between the kitchen and the sunny chair by the window.",
        tags={"rug"},
    ),
    "dog_bed": Route(
        id="dog_bed",
        label="the bend by the dog's bed",
        destination="at the table with the newspaper",
        bumps=2,
        detail="The hallway bent around the family dog's bed before reaching the table.",
        tags={"dog"},
    ),
    "stairs": Route(
        id="stairs",
        label="the stairs to the landing",
        destination="upstairs with a blanket and a book",
        bumps=3,
        detail="The stairs rose right out of the hall, narrow and a little creaky.",
        tags={"stairs"},
    ),
}

RESPONSES = {
    "ask_helper": Response(
        id="ask_helper",
        sense=3,
        power=3,
        text="both hands and a helper's free hand under the edge",
        fail="tried to walk carefully, but even that was not enough",
        qa_text="used both hands and let the other child steady the tray",
        tags={"helper", "two_hands"},
    ),
    "tiny_steps": Response(
        id="tiny_steps",
        sense=3,
        power=2,
        text="tiny steps and both hands",
        fail="took tiny steps, but the tray still tipped too far",
        qa_text="used tiny steps and both hands to steady the tray",
        tags={"two_hands"},
    ),
    "one_hand": Response(
        id="one_hand",
        sense=2,
        power=1,
        text="one hand under the tray and one hand out for balance",
        fail="balanced with one hand, and that left the tray too loose",
        qa_text="balanced the tray with one hand",
        tags={"balance"},
    ),
    "dash": Response(
        id="dash",
        sense=1,
        power=0,
        text="a fast proud march",
        fail="hurried too fast",
        qa_text="hurried too fast with the tray",
        tags={"rushing"},
    ),
}

GIRL_NAMES = ["June", "Mia", "Nora", "Ella", "Lucy", "Ava", "Zoe", "Ruby"]
BOY_NAMES = ["Milo", "Ben", "Theo", "Sam", "Eli", "Noah", "Finn", "Max"]
TRAITS = ["careful", "cautious", "steady", "curious", "cheerful", "sensible"]


@dataclass
class StoryParams:
    snack: str
    carrier: str
    route: str
    response: str
    eager_name: str
    eager_gender: str
    cautioner_name: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    eager_age: int = 5
    cautioner_age: int = 7
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
    "cocoa": [
        (
            "What is hot cocoa?",
            "Hot cocoa is a warm chocolate drink. Because it is a liquid in a mug, it can slosh if you carry it too quickly.",
        )
    ],
    "soup": [
        (
            "Why is soup easy to spill?",
            "Soup is liquid in a bowl, so it moves when the bowl tilts. A bump or a shaky hand can send it over the edge.",
        )
    ],
    "toast": [
        (
            "Why can toast make a sticky mess?",
            "Toast itself is light, but jelly on top can smear when it falls. That is why jelly toast can leave a sticky spot.",
        )
    ],
    "apple": [
        (
            "Why are apple slices easier to carry than soup?",
            "Apple slices do not slosh around like a liquid. They can still slide, but they are usually steadier than soup.",
        )
    ],
    "tray": [
        (
            "What is a tray for?",
            "A tray helps you carry food or drinks from one place to another. Handles and a firm bottom make it easier to keep things steady.",
        )
    ],
    "stairs": [
        (
            "Why are stairs harder for carrying food?",
            "Stairs make your body move up and down with every step. That extra motion can make a drink or bowl wobble more.",
        )
    ],
    "dog": [
        (
            "Why should you watch where a dog is sleeping?",
            "A sleeping dog needs quiet and space. If you step around the bed carefully, you are less likely to trip or startle the dog.",
        )
    ],
    "two_hands": [
        (
            "Why do two hands help you carry something safely?",
            "Two hands give better balance and control. When both hands help, a tray is less likely to tip.",
        )
    ],
    "helper": [
        (
            "Why is asking for help a smart idea?",
            "Asking for help does not mean you failed. It means you cared enough to keep everyone safe and make the job go better.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cocoa", "soup", "toast", "apple", "tray", "stairs", "dog", "two_hands", "helper"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for snack_id, snack in SNACKS.items():
        for carrier_id, carrier in CARRIERS.items():
            for route_id, route in ROUTES.items():
                if possible(snack, carrier, route):
                    combos.append((snack_id, carrier_id, route_id))
    return combos


def explain_rejection(snack: Snack, carrier: Carrier, route: Route) -> str:
    if not supports(snack, carrier):
        return (
            f"(No story: {carrier.phrase} cannot reasonably carry {snack.phrase}. "
            f"{snack.vessel.capitalize()} items need a carrier that supports a {snack.vessel}.)"
        )
    need = needed_steadying(snack, carrier, route)
    best = max(r.power for r in sensible_responses()) if sensible_responses() else 0
    return (
        f"(No story: {snack.phrase} on {carrier.phrase} over {route.label} is too unstable. "
        f"It needs steadying power {need}, but the best sensible plan in this world only provides {best}.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a steadier plan such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.eager_age, params.cautioner_age, params.trait):
        return "averted"
    snack = SNACKS[params.snack]
    carrier = CARRIERS[params.carrier]
    route = ROUTES[params.route]
    response = RESPONSES[params.response]
    need = needed_steadying(snack, carrier, route)
    return "arrived" if response.power >= need else "spilled"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    eager = f["eager"]
    cautioner = f["cautioner"]
    snack = f["snack_cfg"]
    parent = f["parent"]
    route = f["route"]
    outcome = f["outcome"]
    if outcome == "spilled":
        return [
            f'Write a slice-of-life story for a 3-to-5-year-old where a child says "I commit to carrying it myself" while bringing {snack.phrase} as a surprise.',
            f"Tell a gentle, funny surprise story where {eager.id} and {cautioner.id} try to carry {snack.phrase} along {route.label}, make a small spill, and then fix it together.",
            f'Write a humorous home story where the surprise goes wrong in a safe way, nobody gets in trouble, and the ending shows kindness after the mess.',
        ]
    if outcome == "averted":
        return [
            f'Write a slice-of-life surprise story where a child wants to carry {snack.phrase} alone, says "commit", and then listens to an older sibling.',
            f"Tell a cozy funny story where {cautioner.id} spots the wobble before it happens, and the children change their plan without losing the surprise.",
            f'Write a child-friendly story with humor, caution, and a warm home ending where asking for help keeps a surprise intact.',
        ]
    return [
        f'Write a short slice-of-life story for a 3-to-5-year-old where children carry {snack.phrase} to surprise a parent.',
        f"Tell a funny home story where {eager.id} tries to carry the snack alone, but a careful plan keeps the surprise safe.",
        f'Write a gentle story with surprise and humor where a wobble almost ruins the snack, but the children manage it in the end.',
    ]


def pair_noun(eager: Entity, cautioner: Entity, relation: str) -> str:
    if relation == "siblings":
        if eager.type == "boy" and cautioner.type == "boy":
            return "two brothers"
        if eager.type == "girl" and cautioner.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    eager = f["eager"]
    cautioner = f["cautioner"]
    parent = f["parent"]
    snack = f["snack_cfg"]
    carrier = f["carrier_cfg"]
    route = f["route"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(eager, cautioner, relation)
    pw = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {eager.id} and {cautioner.id}, who wanted to surprise their {pw} with {snack.phrase}. The story follows their small home adventure from the kitchen to {route.destination}.",
        ),
        (
            "What surprise did the children plan?",
            f"They planned to carry {snack.phrase} to their {pw}. It was meant to be a quiet, kind surprise during an ordinary afternoon.",
        ),
        (
            f"Why did {cautioner.id} warn {eager.id}?",
            f"{cautioner.id} could see that {snack.phrase} on {carrier.phrase} might wobble along {route.label}. {cautioner.pronoun().capitalize()} was trying to protect the surprise, not ruin it.",
        ),
    ]

    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed after {eager.id} said {eager.pronoun('object')} would commit to carrying it alone?",
                f"{eager.id} listened to {cautioner.id} and changed the plan before the spill happened. That choice kept the surprise safe and turned confidence into teamwork.",
            )
        )
    elif f["outcome"] == "arrived":
        qa.append(
            (
                "How did the children keep the snack from spilling?",
                f"They used {response.qa_text}. That steadier method was strong enough for the wobble on the route, so the snack reached their {pw} safely.",
            )
        )
    else:
        qa.append(
            (
                "Why did the snack spill?",
                f"It spilled because the tray-and-route combination needed more steady control than the children used. Once the wobble started, the snack tipped and made a funny little mess on the floor.",
            )
        )
        qa.append(
            (
                "What happened after the spill?",
                f"Their {pw} checked that everyone was safe, laughed gently, and helped them slow down. Then the children cleaned up and made {snack.remade_as} instead, so the surprise still ended warmly.",
            )
        )

    qa.append(
        (
            "How did the story end?",
            f"It ended with the family together and the surprise finally landing in some form. The ending image shows that the children learned to care about steadiness and help, not just hurry.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["snack_cfg"].tags) | set(f["carrier_cfg"].tags) | set(f["route"].tags) | set(f["response"].tags)
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
        if ent.vessel:
            bits.append(f"vessel={ent.vessel}")
        if ent.supported_vessels:
            bits.append(f"supports={sorted(ent.supported_vessels)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        snack="cocoa",
        carrier="sturdy_tray",
        route="hall",
        response="tiny_steps",
        eager_name="Milo",
        eager_gender="boy",
        cautioner_name="June",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        eager_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        snack="jelly_toast",
        carrier="tea_tray",
        route="dog_bed",
        response="ask_helper",
        eager_name="Nora",
        eager_gender="girl",
        cautioner_name="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        relation="friends",
        eager_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        snack="soup",
        carrier="sturdy_tray",
        route="stairs",
        response="tiny_steps",
        eager_name="Theo",
        eager_gender="boy",
        cautioner_name="Mia",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        relation="siblings",
        eager_age=7,
        cautioner_age=5,
    ),
    StoryParams(
        snack="apple_slices",
        carrier="placemat",
        route="hall",
        response="ask_helper",
        eager_name="Ella",
        eager_gender="girl",
        cautioner_name="Lucy",
        cautioner_gender="girl",
        parent="father",
        trait="sensible",
        relation="siblings",
        eager_age=4,
        cautioner_age=8,
    ),
    StoryParams(
        snack="cocoa",
        carrier="tea_tray",
        route="rug",
        response="ask_helper",
        eager_name="Finn",
        eager_gender="boy",
        cautioner_name="Ruby",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="friends",
        eager_age=6,
        cautioner_age=6,
    ),
]


ASP_RULES = r"""
supports_snack(S, C) :- snack(S), carrier(C), vessel(S, V), supports(C, V).
need(S, C, R, N) :- snack(S), carrier(C), route(R),
                    wobble(S, W), bumps(R, B), stability(C, St),
                    X = W + B - St, X <= 1, N = 1.
need(S, C, R, N) :- snack(S), carrier(C), route(R),
                    wobble(S, W), bumps(R, B), stability(C, St),
                    X = W + B - St, X > 1, N = X.

sensible(Rs) :- response(Rs), sense(Rs, Sc), sense_min(M), Sc >= M.
possible(S, C, R) :- supports_snack(S, C), need(S, C, R, N), sensible(Rs), power(Rs, P), P >= N.
valid(S, C, R) :- snack(S), carrier(C), route(R), possible(S, C, R).

cautious_now(T) :- trait(T), cautious_trait(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sib :- relation(siblings), eager_age(EA), cautioner_age(CA), CA > EA.
authority(C + 1 + B) :- init_caution(C), B = 3, older_sib.
authority(C + 1 + 0) :- init_caution(C), not older_sib.
averted :- older_sib, authority(A), confident_init(CI), A > CI.

scenario_need(N) :- chosen_snack(S), chosen_carrier(C), chosen_route(R), need(S, C, R, N).
contained :- chosen_response(Rs), power(Rs, P), scenario_need(N), P >= N.

outcome(averted) :- averted.
outcome(arrived) :- not averted, contained.
outcome(spilled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("vessel", sid, snack.vessel))
        lines.append(asp.fact("wobble", sid, snack.wobble))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("stability", cid, carrier.stability))
        for vessel in sorted(carrier.supports):
            lines.append(asp.fact("supports", cid, vessel))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("bumps", rid, route.bumps))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("confident_init", int(CONFIDENT_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_snack", params.snack),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("eager_age", params.eager_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child commits to carrying a surprise snack, and the day turns on wobble, help, and humor."
    )
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--eager-age", type=int, choices=[4, 5, 6, 7, 8])
    ap.add_argument("--cautioner-age", type=int, choices=[4, 5, 6, 7, 8])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    if args.snack and args.carrier and args.route:
        snack = SNACKS[args.snack]
        carrier = CARRIERS[args.carrier]
        route = ROUTES[args.route]
        if not possible(snack, carrier, route):
            raise StoryError(explain_rejection(snack, carrier, route))

    combos = [
        combo for combo in valid_combos()
        if (args.snack is None or combo[0] == args.snack)
        and (args.carrier is None or combo[1] == args.carrier)
        and (args.route is None or combo[2] == args.route)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    snack, carrier, route = rng.choice(sorted(combos))
    response_choices = [r.id for r in sensible_responses()]
    response = args.response or rng.choice(sorted(response_choices))
    eager_name, eager_gender = _pick_kid(rng)
    cautioner_name, cautioner_gender = _pick_kid(rng, avoid=eager_name)
    parent = args.parent or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    trait = rng.choice(TRAITS)
    eager_age = args.eager_age if args.eager_age is not None else rng.choice([4, 5, 6, 7, 8])
    cautioner_age = args.cautioner_age if args.cautioner_age is not None else rng.choice([4, 5, 6, 7, 8])

    return StoryParams(
        snack=snack,
        carrier=carrier,
        route=route,
        response=response,
        eager_name=eager_name,
        eager_gender=eager_gender,
        cautioner_name=cautioner_name,
        cautioner_gender=cautioner_gender,
        parent=parent,
        trait=trait,
        relation=relation,
        eager_age=eager_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    snack = SNACKS[params.snack]
    carrier = CARRIERS[params.carrier]
    route = ROUTES[params.route]
    if not possible(snack, carrier, route):
        raise StoryError(explain_rejection(snack, carrier, route))

    world = tell(
        snack=snack,
        carrier=carrier,
        route=route,
        response=RESPONSES[params.response],
        eager_name=params.eager_name,
        eager_gender=params.eager_gender,
        cautioner_name=params.cautioner_name,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        relation=params.relation,
        eager_age=params.eager_age,
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
    for s in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        lines = smoke.story.splitlines()
        if not lines:
            raise StoryError("(Smoke test produced no story lines.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
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
        print(f"{len(combos)} compatible (snack, carrier, route) combos:\n")
        for snack, carrier, route in combos:
            print(f"  {snack:12} {carrier:12} {route}")
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
            header = f"### {p.eager_name} & {p.cautioner_name}: {p.snack} via {p.carrier} on {p.route} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
