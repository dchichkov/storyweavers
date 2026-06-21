#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tough_millimeter_sure_surprise_misunderstanding_problem_solving.py
================================================================================================

A standalone storyworld for a tiny rhyming tale about building a little bridge
for a toy parade.

Seed requirements carried into the world model
----------------------------------------------
- Words used in story space: "tough", "millimeter", "sure"
- Features: Surprise, Misunderstanding, Problem Solving
- Style: close to a Rhyming Story

World sketch
------------
Two children want a small toy to cross a tiny gap on the floor. One child
measures the gap in millimeters and asks for a bridge piece. The helper
misunderstands the request and brings a wrong, flimsy object. A surprise bump or
puff makes the mistake obvious. Then the children solve the problem by measuring
again, choosing a tough support and a good fastener, and sending the toy safely
across.

Reasonableness constraint
-------------------------
A good final solution must:
- span the gap with overlap,
- use a support tough enough for the toy,
- and use a fastener steady enough for the surprise risk.

Invalid explicit choices raise StoryError with a legible reason. Random
generation chooses only valid combinations.

Run it
------
python storyworlds/worlds/gpt-5.4/tough_millimeter_sure_surprise_misunderstanding_problem_solving.py
python storyworlds/worlds/gpt-5.4/tough_millimeter_sure_surprise_misunderstanding_problem_solving.py --vehicle train --gap rug_ripple
python storyworlds/worlds/gpt-5.4/tough_millimeter_sure_surprise_misunderstanding_problem_solving.py --support ribbon
python storyworlds/worlds/gpt-5.4/tough_millimeter_sure_surprise_misunderstanding_problem_solving.py --all --qa
python storyworlds/worlds/gpt-5.4/tough_millimeter_sure_surprise_misunderstanding_problem_solving.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
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
OVERLAP_MM = 2


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Vehicle:
    id: str
    label: str
    phrase: str
    movement: str
    sound: str
    weight: int
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
class Gap:
    id: str
    label: str
    place: str
    width_mm: int
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
class Support:
    id: str
    label: str
    phrase: str
    length_mm: int
    strength: int
    texture: str
    wrong_item: str
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
class Fastener:
    id: str
    label: str
    phrase: str
    grip: int
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
class Surprise:
    id: str
    label: str
    text: str
    risk: int
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
        return [e for e in self.entities.values() if e.role in {"builder", "helper"}]

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
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
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


def _r_bridge_state(world: World) -> list[str]:
    bridge = world.get("bridge")
    support = world.get("support")
    fastener = world.get("fastener")
    gap = world.get("gap")
    toy = world.get("toy")
    out: list[str] = []

    if bridge.attrs.get("installed") and bridge.attrs.get("solution") == "wrong":
        sig = ("wrong_bridge",)
        if sig not in world.fired:
            world.fired.add(sig)
            bridge.meters["unsafe"] += 1
            out.append("__wrong_bridge__")
        return out

    if not bridge.attrs.get("installed") or bridge.attrs.get("solution") != "final":
        return out

    spans = support.meters["length_mm"] >= gap.meters["width_mm"] + OVERLAP_MM
    tough = support.meters["strength"] >= toy.meters["weight"]
    steady = (
        support.meters["strength"] + fastener.meters["grip"]
        >= toy.meters["weight"] + world.facts["surprise_risk"]
    )

    if spans and tough and steady:
        sig = ("safe_bridge",)
        if sig not in world.fired:
            world.fired.add(sig)
            bridge.meters["safe"] += 1
            out.append("__safe_bridge__")
    else:
        sig = ("unsafe_bridge",)
        if sig not in world.fired:
            world.fired.add(sig)
            bridge.meters["unsafe"] += 1
            out.append("__unsafe_bridge__")
    return out


def _r_surprise_wobble(world: World) -> list[str]:
    bridge = world.get("bridge")
    toy = world.get("toy")
    if world.facts["surprise_happened"] < THRESHOLD:
        return []
    if bridge.meters["unsafe"] < THRESHOLD:
        return []
    sig = ("wobble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toy.meters["tilted"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    return ["__wobble__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="bridge_state", tag="physical", apply=_r_bridge_state),
    Rule(name="surprise_wobble", tag="physical", apply=_r_surprise_wobble),
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


def spans_gap(support: Support, gap: Gap) -> bool:
    return support.length_mm >= gap.width_mm + OVERLAP_MM


def tough_enough(support: Support, vehicle: Vehicle) -> bool:
    return support.strength >= vehicle.weight


def steady_enough(support: Support, fastener: Fastener, vehicle: Vehicle, surprise: Surprise) -> bool:
    return support.strength + fastener.grip >= vehicle.weight + surprise.risk


def solution_works(vehicle: Vehicle, gap: Gap, support: Support, fastener: Fastener, surprise: Surprise) -> bool:
    return spans_gap(support, gap) and tough_enough(support, vehicle) and steady_enough(
        support, fastener, vehicle, surprise
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for vehicle_id, vehicle in VEHICLES.items():
        for gap_id, gap in GAPS.items():
            for support_id, support in SUPPORTS.items():
                for fastener_id, fastener in FASTENERS.items():
                    for surprise_id, surprise in SURPRISES.items():
                        if solution_works(vehicle, gap, support, fastener, surprise):
                            combos.append((vehicle_id, gap_id, support_id, fastener_id, surprise_id))
    return combos


def predict_wrong_bridge(world: World) -> dict:
    sim = world.copy()
    bridge = sim.get("bridge")
    bridge.attrs["installed"] = True
    bridge.attrs["solution"] = "wrong"
    propagate(sim, narrate=False)
    sim.facts["surprise_happened"] = 1.0
    propagate(sim, narrate=False)
    return {
        "unsafe": sim.get("bridge").meters["unsafe"] >= THRESHOLD,
        "tilted": sim.get("toy").meters["tilted"] >= THRESHOLD,
    }


def introduce(world: World, builder: Entity, helper: Entity, toy_cfg: Vehicle, gap_cfg: Gap) -> None:
    for kid in (builder, helper):
        kid.memes["joy"] += 1
    world.say(
        f"{builder.id} and {helper.id} played a floor-parade game, all hum and hop and happy sway. "
        f"{toy_cfg.phrase.capitalize()} waited by {gap_cfg.place}, where a tiny break cut through the play."
    )
    world.say(
        f'"Across that little gap," said {builder.id}, "our {toy_cfg.label} wants to {toy_cfg.movement} today."'
    )


def inspect_gap(world: World, builder: Entity, gap_cfg: Gap) -> None:
    gap = world.get("gap")
    gap.meters["width_mm"] = float(gap_cfg.width_mm)
    builder.memes["focus"] += 1
    world.say(
        f"They knelt to look. The crack looked small, but small can still send wheels astray."
    )
    world.say(
        f'"It is {gap_cfg.width_mm} millimeters wide," said {builder.id}. '
        f'"Not a millimeter more, I am sure."'
    )


def ask_for_help(world: World, builder: Entity, helper: Entity, support_cfg: Support) -> None:
    helper.memes["trust"] += 1
    world.say(
        f'"Please bring {support_cfg.phrase}," said {builder.id}, '
        f'"something tough enough to make a bridge that will not sway."'
    )
    world.say(
        f"{helper.id} nodded fast and dashed away, eager to help without delay."
    )


def misunderstanding(world: World, helper: Entity, support_cfg: Support) -> None:
    wrong = support_cfg.wrong_item
    world.facts["wrong_item"] = wrong
    helper.memes["pride"] += 1
    helper.memes["mistake"] += 1
    world.say(
        f"But here came the misunderstanding, a twisty turn inside the play. "
        f"{helper.id} came back with {wrong}, smiling wide as if to say, "
        f'"See? I was quick. I found it right away!"'
    )


def test_wrong_item(world: World, builder: Entity, helper: Entity, toy_cfg: Vehicle) -> None:
    bridge = world.get("bridge")
    bridge.attrs["installed"] = True
    bridge.attrs["solution"] = "wrong"
    propagate(world, narrate=False)
    builder.memes["doubt"] += 1
    world.say(
        f"{builder.id} blinked once. {helper.id} had tried so hard that {builder.pronoun()} did not wish to snap or scold."
    )
    world.say(
        f'So {builder.pronoun()} set the little {toy_cfg.label} near the edge and whispered, '
        f'"Maybe this will work. Maybe. I am not quite sure."'
    )


def surprise_event(world: World, surprise_cfg: Surprise, toy_cfg: Vehicle, builder: Entity, helper: Entity) -> None:
    world.facts["surprise_happened"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then came the surprise, quick as a sigh: {surprise_cfg.text}."
    )
    if world.get("toy").meters["tilted"] >= THRESHOLD:
        world.say(
            f"The little {toy_cfg.label} tipped with a {toy_cfg.sound}, and both children gasped, eyes round and high."
        )
        world.say(
            f'"Oh!" cried {helper.id}. "I brought the wrong thing."'
        )
    else:
        world.say(
            f"The bridge held still, but the children watched with careful eyes."
        )


def solve_problem(
    world: World,
    builder: Entity,
    helper: Entity,
    toy_cfg: Vehicle,
    gap_cfg: Gap,
    support_cfg: Support,
    fastener_cfg: Fastener,
) -> None:
    support = world.get("support")
    fastener = world.get("fastener")
    bridge = world.get("bridge")

    support.label = support_cfg.label
    support.attrs["item"] = support_cfg.id
    support.meters["length_mm"] = float(support_cfg.length_mm)
    support.meters["strength"] = float(support_cfg.strength)

    fastener.label = fastener_cfg.label
    fastener.attrs["item"] = fastener_cfg.id
    fastener.meters["grip"] = float(fastener_cfg.grip)

    bridge.attrs["installed"] = False
    bridge.attrs["solution"] = ""
    bridge.meters["unsafe"] = 0.0
    bridge.meters["safe"] = 0.0
    world.fired = {sig for sig in world.fired if sig not in {("safe_bridge",), ("unsafe_bridge",), ("wrong_bridge",), ("wobble",)}}
    world.get("toy").meters["tilted"] = 0.0

    builder.memes["focus"] += 1
    helper.memes["learning"] += 1

    world.para()
    world.say(
        f"{builder.id} took a calm breath. No blame, no storm, no stomp or sting."
    )
    world.say(
        f'"Let us measure once again," said {builder.pronoun()}. '
        f'"{gap_cfg.width_mm} millimeters wide means we need room on each side too."'
    )
    world.say(
        f'{helper.id} leaned close and listened. "{support_cfg.label.capitalize()} and {fastener_cfg.label}," '
        f'{helper.pronoun()} said. "Now I see what we should do."'
    )

    bridge.attrs["installed"] = True
    bridge.attrs["solution"] = "final"
    propagate(world, narrate=False)

    world.say(
        f"So they laid down {support_cfg.phrase}, {support_cfg.texture}, neat and true, "
        f"and fixed it with {fastener_cfg.phrase} so the tiny bridge sat snug and new."
    )
    if bridge.meters["safe"] >= THRESHOLD:
        world.say(
            f"The bridge looked small, yet brave and tough, a patient path of steady stuff."
        )


def cross_and_end(world: World, builder: Entity, helper: Entity, toy_cfg: Vehicle) -> None:
    toy = world.get("toy")
    bridge = world.get("bridge")
    if bridge.meters["safe"] < THRESHOLD:
        raise StoryError("(Internal error: final bridge was not safe.)")
    toy.meters["crossed"] += 1
    builder.memes["relief"] += 1
    helper.memes["relief"] += 1
    builder.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{builder.id} gave the little {toy_cfg.label} a gentle start."
    )
    world.say(
        f"It {toy_cfg.movement} over the bridge without a slip, without a bluff. "
        f"Across it went with {toy_cfg.sound} and shine, neat as a song and smooth as rhyme."
    )
    world.say(
        f'{helper.id} laughed and clapped. "{builder.id}, you were right." '
        f'"And you were kind," said {builder.id}. "That helped us solve it, line by line."'
    )
    world.say(
        f"After that, when tools or words seemed blurry in the middle of play, "
        f"they checked, asked, and measured first, then built the sturdy, clever way."
    )


def tell(
    vehicle: Vehicle,
    gap: Gap,
    support: Support,
    fastener: Fastener,
    surprise: Surprise,
    builder_name: str = "Nia",
    builder_gender: str = "girl",
    helper_name: str = "Toby",
    helper_gender: str = "boy",
    relation: str = "friends",
) -> World:
    world = World()
    builder = world.add(
        Entity(
            id=builder_name,
            kind="character",
            type=builder_gender,
            role="builder",
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            attrs={"relation": relation},
        )
    )
    toy = world.add(
        Entity(
            id="toy",
            type="toy",
            label=vehicle.label,
            attrs={"vehicle": vehicle.id},
        )
    )
    gap_ent = world.add(
        Entity(
            id="gap",
            type="gap",
            label=gap.label,
            attrs={"gap": gap.id},
        )
    )
    support_ent = world.add(
        Entity(
            id="support",
            type="support",
            label="wrong item",
            attrs={"item": ""},
        )
    )
    fastener_ent = world.add(
        Entity(
            id="fastener",
            type="fastener",
            label="",
            attrs={"item": ""},
        )
    )
    bridge = world.add(
        Entity(
            id="bridge",
            type="bridge",
            label="bridge",
            attrs={"installed": False, "solution": ""},
        )
    )

    toy.meters["weight"] = float(vehicle.weight)
    gap_ent.meters["width_mm"] = float(gap.width_mm)
    support_ent.meters["length_mm"] = 0.0
    support_ent.meters["strength"] = 0.0
    fastener_ent.meters["grip"] = 0.0
    bridge.meters["safe"] = 0.0
    bridge.meters["unsafe"] = 0.0
    toy.meters["tilted"] = 0.0
    toy.meters["crossed"] = 0.0

    world.facts["surprise_happened"] = 0.0
    world.facts["surprise_risk"] = surprise.risk
    world.facts["builder"] = builder
    world.facts["helper"] = helper
    world.facts["vehicle_cfg"] = vehicle
    world.facts["gap_cfg"] = gap
    world.facts["support_cfg"] = support
    world.facts["fastener_cfg"] = fastener
    world.facts["surprise_cfg"] = surprise
    world.facts["wrong_item"] = ""
    world.facts["prediction"] = predict_wrong_bridge(world)

    introduce(world, builder, helper, vehicle, gap)
    inspect_gap(world, builder, gap)

    world.para()
    ask_for_help(world, builder, helper, support)
    misunderstanding(world, helper, support)
    test_wrong_item(world, builder, helper, vehicle)
    surprise_event(world, surprise, vehicle, builder, helper)

    world.para()
    solve_problem(world, builder, helper, vehicle, gap, support, fastener)
    cross_and_end(world, builder, helper, vehicle)

    world.facts["outcome"] = "safe" if world.get("bridge").meters["safe"] >= THRESHOLD else "unsafe"
    world.facts["tilted"] = world.get("toy").meters["tilted"] >= THRESHOLD
    world.facts["crossed"] = world.get("toy").meters["crossed"] >= THRESHOLD
    return world


VEHICLES = {
    "train": Vehicle(
        id="train",
        label="train",
        phrase="a red toy train",
        movement="chug",
        sound="chug-chug",
        weight=2,
        tags={"train", "bridge"},
    ),
    "duck_cart": Vehicle(
        id="duck_cart",
        label="duck cart",
        phrase="a yellow duck cart",
        movement="roll",
        sound="rumble-tum",
        weight=1,
        tags={"duck", "bridge"},
    ),
    "robot_rover": Vehicle(
        id="robot_rover",
        label="robot rover",
        phrase="a silver robot rover",
        movement="whirr",
        sound="whirr-whirr",
        weight=3,
        tags={"robot", "bridge"},
    ),
}

GAPS = {
    "tile_crack": Gap(
        id="tile_crack",
        label="tile crack",
        place="a tiny tile crack",
        width_mm=3,
        tags={"measurement", "floor"},
    ),
    "book_gap": Gap(
        id="book_gap",
        label="book gap",
        place="a gap between two big books",
        width_mm=5,
        tags={"measurement", "books"},
    ),
    "rug_ripple": Gap(
        id="rug_ripple",
        label="rug ripple",
        place="a lifted rug ripple",
        width_mm=7,
        tags={"measurement", "rug"},
    ),
}

SUPPORTS = {
    "craft_stick": Support(
        id="craft_stick",
        label="craft stick",
        phrase="a craft stick",
        length_mm=20,
        strength=3,
        texture="flat and tidy",
        wrong_item="a string",
        tags={"craft_stick", "bridge"},
    ),
    "card_strip": Support(
        id="card_strip",
        label="card strip",
        phrase="a card strip",
        length_mm=12,
        strength=2,
        texture="smooth and bright",
        wrong_item="a play card",
        tags={"cardboard", "bridge"},
    ),
    "foam_strip": Support(
        id="foam_strip",
        label="foam strip",
        phrase="a foam strip",
        length_mm=14,
        strength=2,
        texture="springy and light",
        wrong_item="a ribbon",
        tags={"foam", "bridge"},
    ),
    "ribbon": Support(
        id="ribbon",
        label="ribbon",
        phrase="a ribbon",
        length_mm=18,
        strength=0,
        texture="soft and fluttery",
        wrong_item="a ribbon",
        tags={"ribbon"},
    ),
}

FASTENERS = {
    "tape": Fastener(
        id="tape",
        label="tape",
        phrase="a neat line of tape",
        grip=1,
        qa_text="held it down with tape",
        tags={"tape"},
    ),
    "clips": Fastener(
        id="clips",
        label="clips",
        phrase="two tiny clips",
        grip=2,
        qa_text="snapped it in place with clips",
        tags={"clips"},
    ),
}

SURPRISES = {
    "ball_bump": Surprise(
        id="ball_bump",
        label="ball bump",
        text="a runaway ball came bump-bump-bumping by",
        risk=1,
        tags={"surprise", "ball"},
    ),
    "cat_sneeze": Surprise(
        id="cat_sneeze",
        label="cat sneeze",
        text="the cat gave a great achoo that shook the quiet room",
        risk=2,
        tags={"surprise", "cat"},
    ),
    "fan_puff": Surprise(
        id="fan_puff",
        label="fan puff",
        text="a fan sent a sudden puff of air across the floor",
        risk=1,
        tags={"surprise", "air"},
    ),
}

GIRL_NAMES = ["Nia", "Mina", "Lila", "Rosa", "Poppy", "June", "Tess", "Mara"]
BOY_NAMES = ["Toby", "Milo", "Finn", "Owen", "Eli", "Jude", "Max", "Noel"]


@dataclass
class StoryParams:
    vehicle: str
    gap: str
    support: str
    fastener: str
    surprise: str
    builder: str
    builder_gender: str
    helper: str
    helper_gender: str
    relation: str = "friends"
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
    "measurement": [
        (
            "What is a millimeter?",
            "A millimeter is a very tiny unit for measuring length. You use it when something is so small that centimeters feel too big.",
        )
    ],
    "bridge": [
        (
            "What makes a little bridge strong?",
            "A little bridge needs something stiff enough not to bend too much and long enough to reach both sides. It also helps if you hold it still so it cannot slip away.",
        )
    ],
    "tape": [
        (
            "What does tape do?",
            "Tape sticks things together or holds them in place. It is useful when you need something small to stay put.",
        )
    ],
    "clips": [
        (
            "What do clips do?",
            "Clips pinch things and hold them steady. They are handy when tape alone might not be strong enough.",
        )
    ],
    "ribbon": [
        (
            "Why is a ribbon not a tough bridge?",
            "A ribbon is soft and bendy. It can look pretty, but it sags when something heavy tries to cross it.",
        )
    ],
    "train": [
        (
            "Why do toy trains need a steady track?",
            "Toy trains roll best when the path stays flat and steady. If the track wiggles, the wheels can tilt or slide off.",
        )
    ],
    "robot": [
        (
            "Why does a robot rover need a strong path?",
            "A robot rover is a heavier toy with wheels or treads. A weak path can bend under it and make it tip.",
        )
    ],
    "duck": [
        (
            "Why can a small duck cart use a smaller bridge than a heavy toy?",
            "A lighter toy puts less weight on the bridge. That means a smaller support can sometimes hold it safely.",
        )
    ],
    "surprise": [
        (
            "Why do surprises matter when building something?",
            "A surprise bump or puff tests whether something is really steady. A good solution works even when the room does something unexpected.",
        )
    ],
}
KNOWLEDGE_ORDER = ["measurement", "bridge", "tape", "clips", "ribbon", "train", "robot", "duck", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    builder = f["builder"]
    helper = f["helper"]
    vehicle = f["vehicle_cfg"]
    gap = f["gap_cfg"]
    wrong = f["wrong_item"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that uses the words "tough", "millimeter", and "sure".',
        f"Tell a gentle story where {builder.id} measures {gap.place}, {helper.id} misunderstands a request and brings {wrong}, and the children solve the problem together.",
        f"Write a child-facing verse story about a little {vehicle.label} that cannot cross a tiny gap until careful measuring and teamwork save the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    builder = f["builder"]
    helper = f["helper"]
    vehicle = f["vehicle_cfg"]
    gap = f["gap_cfg"]
    support = f["support_cfg"]
    fastener = f["fastener_cfg"]
    surprise = f["surprise_cfg"]
    wrong = f["wrong_item"]
    prediction = f["prediction"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {builder.id} and {helper.id}, who were trying to help a little {vehicle.label} cross {gap.place}. They worked through a mistake together instead of giving up.",
        ),
        (
            "What was the problem at the start?",
            f"The toy could not cross because the gap was {gap.width_mm} millimeters wide, which was enough to stop its wheels. Even a tiny break can matter when a toy path must stay flat and steady.",
        ),
        (
            f"What did {builder.id} ask for, and what did {helper.id} bring?",
            f"{builder.id} asked for {support.phrase}, but {helper.id} brought {wrong} instead. That misunderstanding happened because {helper.id} hurried to help and did not check carefully.",
        ),
    ]
    if prediction["tilted"]:
        qa.append(
            (
                "What was the surprise, and why did it matter?",
                f"The surprise was that {surprise.text}, and it made the wrong bridge wobble. That showed the first idea was not safe enough when the room gave it an extra little test.",
            )
        )
    qa.append(
        (
            "How did they solve the problem?",
            f"They measured again, chose {support.phrase}, and {fastener.qa_text}. The final bridge worked because it was tough enough and steady enough for the toy and the surprise risk.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The little {vehicle.label} crossed safely, and both children felt happy and relieved. The ending shows they learned to check words and measurements before building.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"measurement", "bridge", "surprise"}
    tags |= set(f["fastener_cfg"].tags)
    tags |= set(f["support_cfg"].tags)
    tags |= set(f["vehicle_cfg"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v not in ("", False, 0)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        vehicle="train",
        gap="tile_crack",
        support="card_strip",
        fastener="tape",
        surprise="ball_bump",
        builder="Nia",
        builder_gender="girl",
        helper="Toby",
        helper_gender="boy",
        relation="friends",
    ),
    StoryParams(
        vehicle="duck_cart",
        gap="book_gap",
        support="foam_strip",
        fastener="clips",
        surprise="fan_puff",
        builder="Mina",
        builder_gender="girl",
        helper="Eli",
        helper_gender="boy",
        relation="siblings",
    ),
    StoryParams(
        vehicle="robot_rover",
        gap="rug_ripple",
        support="craft_stick",
        fastener="clips",
        surprise="cat_sneeze",
        builder="Finn",
        builder_gender="boy",
        helper="Rosa",
        helper_gender="girl",
        relation="friends",
    ),
    StoryParams(
        vehicle="train",
        gap="book_gap",
        support="craft_stick",
        fastener="tape",
        surprise="fan_puff",
        builder="June",
        builder_gender="girl",
        helper="Max",
        helper_gender="boy",
        relation="siblings",
    ),
]


def explain_rejection(vehicle: Vehicle, gap: Gap, support: Support, fastener: Fastener, surprise: Surprise) -> str:
    if not spans_gap(support, gap):
        need = gap.width_mm + OVERLAP_MM
        return (
            f"(No story: {support.label} is only {support.length_mm} mm long, but the bridge needs at least "
            f"{need} mm to reach across {gap.label} with overlap on both sides.)"
        )
    if not tough_enough(support, vehicle):
        return (
            f"(No story: {support.label} is not tough enough for the {vehicle.label}. "
            f"Pick a sturdier support.)"
        )
    return (
        f"(No story: {support.label} with {fastener.label} would not stay steady enough if "
        f"{surprise.label} happened. Pick a stronger hold.)"
    )


def outcome_of(params: StoryParams) -> str:
    vehicle = VEHICLES[params.vehicle]
    gap = GAPS[params.gap]
    support = SUPPORTS[params.support]
    fastener = FASTENERS[params.fastener]
    surprise = SURPRISES[params.surprise]
    return "safe" if solution_works(vehicle, gap, support, fastener, surprise) else "unsafe"


ASP_RULES = r"""
spans(S,G) :- support(S), gap(G), support_length(S,L), gap_width(G,W), overlap_mm(O), L >= W + O.
tough(S,V) :- support(S), vehicle(V), strength(S,SS), weight(V,VW), SS >= VW.
steady(S,F,V,Z) :- support(S), fastener(F), vehicle(V), surprise(Z),
                   strength(S,SS), grip(F,GG), weight(V,VW), risk(Z,RR),
                   SS + GG >= VW + RR.
valid(V,G,S,F,Z) :- vehicle(V), gap(G), support(S), fastener(F), surprise(Z),
                    spans(S,G), tough(S,V), steady(S,F,V,Z).
outcome(safe) :- chosen_vehicle(V), chosen_gap(G), chosen_support(S), chosen_fastener(F), chosen_surprise(Z),
                 valid(V,G,S,F,Z).
outcome(unsafe) :- chosen_vehicle(V), chosen_gap(G), chosen_support(S), chosen_fastener(F), chosen_surprise(Z),
                   not valid(V,G,S,F,Z).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("overlap_mm", OVERLAP_MM)]
    for vid, v in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        lines.append(asp.fact("weight", vid, v.weight))
    for gid, g in GAPS.items():
        lines.append(asp.fact("gap", gid))
        lines.append(asp.fact("gap_width", gid, g.width_mm))
    for sid, s in SUPPORTS.items():
        lines.append(asp.fact("support", sid))
        lines.append(asp.fact("support_length", sid, s.length_mm))
        lines.append(asp.fact("strength", sid, s.strength))
    for fid, f in FASTENERS.items():
        lines.append(asp.fact("fastener", fid))
        lines.append(asp.fact("grip", fid, f.grip))
    for zid, z in SURPRISES.items():
        lines.append(asp.fact("surprise", zid))
        lines.append(asp.fact("risk", zid, z.risk))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_vehicle", params.vehicle),
            asp.fact("chosen_gap", params.gap),
            asp.fact("chosen_support", params.support),
            asp.fact("chosen_fastener", params.fastener),
            asp.fact("chosen_surprise", params.surprise),
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

    checked = 0
    for vehicle in VEHICLES:
        for gap in GAPS:
            for support in SUPPORTS:
                for fastener in FASTENERS:
                    for surprise in SURPRISES:
                        params = StoryParams(
                            vehicle=vehicle,
                            gap=gap,
                            support=support,
                            fastener=fastener,
                            surprise=surprise,
                            builder="Nia",
                            builder_gender="girl",
                            helper="Toby",
                            helper_gender="boy",
                            relation="friends",
                        )
                        py = outcome_of(params)
                        asp_out = asp_outcome(params)
                        checked += 1
                        if py != asp_out:
                            rc = 1
                            print("MISMATCH in outcome:", params, py, asp_out)
                            break

    if rc == 0:
        print(f"OK: outcome model matches outcome_of() on {checked} scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny bridge, a misunderstanding, a surprise, and problem solving."
    )
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--gap", choices=GAPS)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--fastener", choices=FASTENERS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--builder")
    ap.add_argument("--helper")
    ap.add_argument("--builder-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vehicle and args.vehicle not in VEHICLES:
        raise StoryError("(No story: unknown vehicle.)")
    if args.gap and args.gap not in GAPS:
        raise StoryError("(No story: unknown gap.)")
    if args.support and args.support not in SUPPORTS:
        raise StoryError("(No story: unknown support.)")
    if args.fastener and args.fastener not in FASTENERS:
        raise StoryError("(No story: unknown fastener.)")
    if args.surprise and args.surprise not in SURPRISES:
        raise StoryError("(No story: unknown surprise.)")

    if args.vehicle and args.gap and args.support and args.fastener and args.surprise:
        vehicle = VEHICLES[args.vehicle]
        gap = GAPS[args.gap]
        support = SUPPORTS[args.support]
        fastener = FASTENERS[args.fastener]
        surprise = SURPRISES[args.surprise]
        if not solution_works(vehicle, gap, support, fastener, surprise):
            raise StoryError(explain_rejection(vehicle, gap, support, fastener, surprise))

    combos = [
        combo
        for combo in valid_combos()
        if (args.vehicle is None or combo[0] == args.vehicle)
        and (args.gap is None or combo[1] == args.gap)
        and (args.support is None or combo[2] == args.support)
        and (args.fastener is None or combo[3] == args.fastener)
        and (args.surprise is None or combo[4] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    vehicle, gap, support, fastener, surprise = rng.choice(sorted(combos))
    builder_gender = args.builder_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    builder = args.builder or _pick_name(rng, builder_gender)
    helper = args.helper or _pick_name(rng, helper_gender, avoid=builder)
    relation = args.relation or rng.choice(["friends", "siblings"])
    return StoryParams(
        vehicle=vehicle,
        gap=gap,
        support=support,
        fastener=fastener,
        surprise=surprise,
        builder=builder,
        builder_gender=builder_gender,
        helper=helper,
        helper_gender=helper_gender,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        vehicle = VEHICLES[params.vehicle]
        gap = GAPS[params.gap]
        support = SUPPORTS[params.support]
        fastener = FASTENERS[params.fastener]
        surprise = SURPRISES[params.surprise]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err}.)") from None

    if not solution_works(vehicle, gap, support, fastener, surprise):
        raise StoryError(explain_rejection(vehicle, gap, support, fastener, surprise))

    world = tell(
        vehicle=vehicle,
        gap=gap,
        support=support,
        fastener=fastener,
        surprise=surprise,
        builder_name=params.builder,
        builder_gender=params.builder_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        relation=params.relation,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (vehicle, gap, support, fastener, surprise) combos:\n")
        for vehicle, gap, support, fastener, surprise in combos:
            print(f"  {vehicle:11} {gap:10} {support:11} {fastener:8} {surprise}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.builder} & {p.helper}: {p.vehicle} over {p.gap} "
                f"with {p.support} + {p.fastener} ({p.surprise})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
