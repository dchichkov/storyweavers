#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/suggest_laundry_sole_steep_hill_path_twist.py
========================================================================

A standalone story world for a small folk-tale domain:

A child climbs a steep hill path with family laundry. On the way, the sole of a
shoe comes loose. The path is steep, the basket is heavy, and a tumble would
scatter the washing down the slope. A stranger appears, suggests a sensible
plan, shares the load, and helps tie the loose sole. At the top comes a gentle
twist: the helper is not a random traveler after all, but someone already tied
to the family or the hill.

The world prefers a narrow set of plausible stories over broad weak coverage.
Not every helper can carry every load, and not every repair can sensibly fix
every kind of shoe. Invalid explicit choices raise StoryError with a readable
reason.

Run it
------
    python storyworlds/worlds/gpt-5.4/suggest_laundry_sole_steep_hill_path_twist.py
    python storyworlds/worlds/gpt-5.4/suggest_laundry_sole_steep_hill_path_twist.py --load basket --footwear sandal
    python storyworlds/worlds/gpt-5.4/suggest_laundry_sole_steep_hill_path_twist.py --repair leather_lace --footwear sandal
    python storyworlds/worlds/gpt-5.4/suggest_laundry_sole_steep_hill_path_twist.py --all
    python storyworlds/worlds/gpt-5.4/suggest_laundry_sole_steep_hill_path_twist.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/suggest_laundry_sole_steep_hill_path_twist.py --verify
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
STEEP_PATH = "the steep hill path"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "washerwoman"}
        male = {"boy", "man", "father", "shepherd", "potter"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {"mother": "mom", "father": "dad", "grandmother": "grandmother"}
        return mapping.get(self.type, self.label or self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Load:
    id: str
    label: str
    phrase: str
    weight: int
    cloths: str
    spill: str
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
class Footwear:
    id: str
    label: str
    phrase: str
    sole_name: str
    loosen_text: str
    supports: set[str] = field(default_factory=set)
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
class Repair:
    id: str
    label: str
    phrase: str
    method: str
    supports: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    type: str
    phrase: str
    carry_power: int
    suggest_text: str
    reveal_text: str
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


def _r_slip_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    shoe = world.get("shoe")
    load = world.get("load")
    if shoe.meters["loose"] >= THRESHOLD and load.meters["burden"] >= THRESHOLD:
        sig = ("slip_risk", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["slip_risk"] += 1
            child.memes["worry"] += 1
            out.append("__risk__")
    return out


def _r_share_relief(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    load = world.get("load")
    if load.meters["shared"] >= THRESHOLD:
        sig = ("share_relief", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["trust"] += 1
            child.meters["slip_risk"] = 0.0
    return out


def _r_repair_relief(world: World) -> list[str]:
    out: list[str] = []
    shoe = world.get("shoe")
    child = world.get("child")
    if shoe.meters["tied"] >= THRESHOLD:
        sig = ("repair_relief", shoe.id)
        if sig not in world.fired:
            world.fired.add(sig)
            shoe.meters["loose"] = 0.0
            child.meters["slip_risk"] = 0.0
            child.memes["relief"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip_risk", tag="physical", apply=_r_slip_risk),
    Rule(name="share_relief", tag="social", apply=_r_share_relief),
    Rule(name="repair_relief", tag="physical", apply=_r_repair_relief),
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


def repair_fits(footwear: Footwear, repair: Repair) -> bool:
    return footwear.id in repair.supports


def helper_can_share(load: Load, helper: Helper) -> bool:
    return helper.carry_power >= load.weight


def valid_combo(load: Load, footwear: Footwear, helper: Helper, repair: Repair) -> bool:
    return helper_can_share(load, helper) and repair_fits(footwear, repair)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for load_id, load in LOADS.items():
        for footwear_id, footwear in FOOTWEAR.items():
            for helper_id, helper in HELPERS.items():
                for repair_id, repair in REPAIRS.items():
                    if valid_combo(load, footwear, helper, repair):
                        combos.append((load_id, footwear_id, helper_id, repair_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "slip_risk": child.meters["slip_risk"],
        "worry": child.memes["worry"],
    }


def introduce(world: World, child: Entity, parent: Entity, load: Load) -> None:
    child.memes["duty"] += 1
    world.say(
        f"Long ago, when people still measured kindness by the weight they carried for one another, "
        f"{child.id} set out with {load.phrase}. {child.pronoun('possessive').capitalize()} {parent.label_word} "
        f"had asked {child.pronoun('object')} to bring the laundry up {STEEP_PATH} to the sunny line by the cottage."
    )
    world.say(
        f"The bundle held {load.cloths}, and {child.id} was proud to help, though the climb was no small one."
    )


def begin_climb(world: World, child: Entity, shoe: Entity) -> None:
    world.say(
        f"The morning wind moved through the grass, and stones peeked out along {STEEP_PATH}. "
        f"{child.id} climbed carefully in {shoe.phrase}."
    )


def sole_loosens(world: World, child: Entity, footwear: Footwear, load: Load) -> None:
    shoe = world.get("shoe")
    basket = world.get("load")
    shoe.meters["loose"] = 1.0
    basket.meters["burden"] = float(load.weight)
    propagate(world, narrate=False)
    world.say(
        f"Halfway up, {footwear.loosen_text} The word {footwear.sole_name} seemed suddenly as sharp in "
        f"{child.id}'s mind as a pebble in the road."
    )
    if world.get("child").meters["slip_risk"] >= THRESHOLD:
        world.say(
            f"{child.id} wobbled. If {child.pronoun()} slipped, {load.spill} might fly down the hill like white birds."
        )


def helper_arrives(world: World, child: Entity, helper: Entity, helper_cfg: Helper) -> None:
    child.memes["hope"] += 1
    world.say(
        f"Just then {helper.phrase} came around the bend with quiet steps. "
        f"{helper.pronoun().capitalize()} saw the loose shoe, the heavy washing, and the worry on {child.id}'s face."
    )
    world.say(
        f'"May I suggest a wiser way?" {helper.id} asked. "{helper_cfg.suggest_text}"'
    )


def accept_plan(world: World, child: Entity, helper: Entity, repair: Repair, load: Load) -> None:
    child.memes["trust"] += 1
    world.say(
        f"{child.id} had been taught not to trust every stranger, but there was steadiness in {helper.id}'s voice. "
        f"{child.pronoun().capitalize()} nodded."
    )
    world.say(
        f"{helper.id} took part of the laundry, and together they set the bundle between them so neither pair of hands "
        f"had to bear the whole of it."
    )
    world.get("load").meters["shared"] = 1.0
    world.get("load").meters["burden"] = 0.0
    world.get("shoe").meters["tied"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then {helper.id} used {repair.phrase} and {repair.method}. The loose step grew firm again."
    )


def shared_climb(world: World, child: Entity, helper: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"So they climbed the steep hill path side by side, sharing the work. "
        f"Where one stone was sharp, {helper.id} pointed it out; where the path bent, {child.id} warned of the rut ahead."
    )


def reveal_twist(world: World, child: Entity, helper: Entity, helper_cfg: Helper, parent: Entity) -> None:
    child.memes["surprise"] += 1
    child.memes["gratitude"] += 1
    world.say(
        f"At the top, {parent.label_word} came out to greet them, and then the surprise came. "
        f"{helper_cfg.reveal_text}"
    )
    world.say(
        f"{child.id} stared, then laughed, for the world had turned larger and kinder in a single climb."
    )


def ending(world: World, child: Entity, helper: Entity, load: Load) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"They spread out {load.cloths} in the high clean wind. The washing shone in the sun, and not one piece of laundry "
        f"was lost to the slope."
    )
    world.say(
        f"From that day on, {child.id} remembered that a steep hill grows gentler when a burden is shared, "
        f"and that good counsel may come from the bend you least expect."
    )


def tell(load: Load, footwear: Footwear, helper_cfg: Helper, repair: Repair,
         child_name: str = "Mira", child_gender: str = "girl",
         parent_type: str = "grandmother", trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the elder at the cottage",
        role="parent",
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_cfg.label.title(),
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={},
    ))
    shoe = world.add(Entity(
        id="shoe",
        kind="thing",
        type="footwear",
        label=footwear.label,
        phrase=footwear.phrase,
        owner=child.id,
        attrs={},
    ))
    basket = world.add(Entity(
        id="load",
        kind="thing",
        type="load",
        label=load.label,
        phrase=load.phrase,
        owner=child.id,
        attrs={},
    ))

    child.meters["slip_risk"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["relief"] = 0.0
    shoe.meters["loose"] = 0.0
    shoe.meters["tied"] = 0.0
    basket.meters["burden"] = 0.0
    basket.meters["shared"] = 0.0

    world.facts.update(
        child=child,
        parent=parent,
        helper=helper,
        load_cfg=load,
        footwear_cfg=footwear,
        repair_cfg=repair,
        helper_cfg=helper_cfg,
        safe=False,
        twist=False,
    )

    introduce(world, child, parent, load)
    begin_climb(world, child, shoe)

    world.para()
    sole_loosens(world, child, footwear, load)
    danger = predict_trouble(world)
    world.facts["predicted_slip_risk"] = danger["slip_risk"]

    helper_arrives(world, child, helper, helper_cfg)
    accept_plan(world, child, helper, repair, load)

    world.para()
    shared_climb(world, child, helper)
    reveal_twist(world, child, helper, helper_cfg, parent)
    ending(world, child, helper, load)

    world.facts["safe"] = (
        world.get("shoe").meters["loose"] < THRESHOLD
        and world.get("load").meters["shared"] >= THRESHOLD
        and world.get("child").meters["slip_risk"] < THRESHOLD
    )
    world.facts["twist"] = True
    return world


LOADS = {
    "basket": Load(
        id="basket",
        label="basket",
        phrase="a wicker basket full of clean laundry",
        weight=2,
        cloths="shirts, aprons, and bright towels",
        spill="the shirts and towels",
        tags={"laundry", "sharing"},
    ),
    "bundle": Load(
        id="bundle",
        label="bundle",
        phrase="a tied bundle of folded laundry",
        weight=1,
        cloths="small shirts and table cloths",
        spill="the folded cloths",
        tags={"laundry", "sharing"},
    ),
    "sheet_roll": Load(
        id="sheet_roll",
        label="sheet roll",
        phrase="a long roll of laundry with two big sheets wrapped around the rest",
        weight=3,
        cloths="sheets, pillowcases, and a patchwork cover",
        spill="the sheets and pillowcases",
        tags={"laundry", "sharing"},
    ),
}

FOOTWEAR = {
    "sandal": Footwear(
        id="sandal",
        label="sandal",
        phrase="old leather sandals",
        sole_name="sole",
        loosen_text="the sole of one sandal peeled loose at the toe.",
        supports={"reed_twine", "cloth_strip"},
        tags={"sole", "shoe"},
    ),
    "shoe": Footwear(
        id="shoe",
        label="shoe",
        phrase="sturdy walking shoes",
        sole_name="sole",
        loosen_text="the sole of one shoe flapped with a tired little slap against the ground.",
        supports={"cloth_strip", "leather_lace"},
        tags={"sole", "shoe"},
    ),
    "clog": Footwear(
        id="clog",
        label="clog",
        phrase="wooden clogs with leather straps",
        sole_name="sole",
        loosen_text="one clog shifted badly, and its leather bottom came half loose.",
        supports={"leather_lace"},
        tags={"sole", "shoe"},
    ),
}

REPAIRS = {
    "reed_twine": Repair(
        id="reed_twine",
        label="reed twine",
        phrase="a twist of reed twine",
        method="looped it twice around the front and knotted the sole snugly to the strap",
        supports={"sandal"},
        tags={"repair", "sole"},
    ),
    "cloth_strip": Repair(
        id="cloth_strip",
        label="cloth strip",
        phrase="a narrow cloth strip",
        method="wrapped it under the loose sole and over the upper until the shoe held together",
        supports={"sandal", "shoe"},
        tags={"repair", "sole"},
    ),
    "leather_lace": Repair(
        id="leather_lace",
        label="leather lace",
        phrase="a strong leather lace",
        method="threaded it through the side holes and tied the sole firm against the foot",
        supports={"shoe", "clog"},
        tags={"repair", "sole"},
    ),
}

HELPERS = {
    "washerwoman": Helper(
        id="washerwoman",
        label="Old Fen",
        type="washerwoman",
        phrase="an old washerwoman with rolled sleeves and a willow stick",
        carry_power=2,
        suggest_text="Let me carry half the washing, and let us bind that sole before the hill takes its due.",
        reveal_text='The washerwoman smiled at the elder and said, "I am the sister she told you about, the one coming over the ridge today."',
        tags={"sharing", "surprise", "twist"},
    ),
    "shepherd": Helper(
        id="shepherd",
        label="Tarin",
        type="shepherd",
        phrase="a young shepherd with a crook across his shoulders",
        carry_power=3,
        suggest_text="We will share the weight, and I will tie your sole fast before one more stone can trouble you.",
        reveal_text='The shepherd bowed and said, "Grandmother, I have brought your message from the upper pasture." Only then did Mira learn he was the kinsman the family had awaited.',
        tags={"sharing", "surprise", "twist"},
    ),
    "potter": Helper(
        id="potter",
        label="Bran",
        type="potter",
        phrase="a potter dusted with pale clay",
        carry_power=3,
        suggest_text="A hill is kinder to two carriers than to one. Share the laundry with me, and let me mend that sole as well.",
        reveal_text='The potter set down the basket and laughed softly. He was the new neighbor from the other side of the hill, the very guest the cottage had been preparing to welcome.',
        tags={"sharing", "surprise", "twist"},
    ),
}

GIRL_NAMES = ["Mira", "Tala", "Lina", "Rosa", "Niva", "Sela"]
BOY_NAMES = ["Ivo", "Marek", "Tobin", "Pavel", "Rian", "Sorin"]
TRAITS = ["careful", "kind", "steady", "dutiful", "patient"]


@dataclass
class StoryParams:
    load: str
    footwear: str
    helper: str
    repair: str
    child_name: str
    child_gender: str
    parent_type: str
    trait: str
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
    "laundry": [
        (
            "What is laundry?",
            "Laundry is clothing or cloth that has been washed or is waiting to be washed. People often carry it in a basket or bundle."
        )
    ],
    "sole": [
        (
            "What is the sole of a shoe?",
            "The sole is the bottom part of a shoe or sandal. It is the part that touches the ground when you walk."
        )
    ],
    "sharing": [
        (
            "Why does sharing a heavy load help?",
            "Sharing a heavy load means each person carries less weight. That makes walking steadier and less tiring."
        )
    ],
    "repair": [
        (
            "Why should a loose shoe be fixed before walking farther?",
            "A loose shoe can catch on stones or slip under your foot. Fixing it first helps you walk safely."
        )
    ],
    "hill": [
        (
            "Why is a steep hill path harder than a flat road?",
            "A steep hill path makes your legs work harder and can make you lose balance more easily. Loose stones and sharp slopes add to the trouble."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    load = f["load_cfg"]
    footwear = f["footwear_cfg"]
    return [
        'Write a short folk-tale style story for a 3-to-5-year-old set on a steep hill path that includes the words "suggest", "laundry", and "sole".',
        f"Tell a gentle story where {child.id} climbs a steep hill path with {load.label}, the {footwear.sole_name} comes loose, and {helper.id} suggests sharing the load.",
        "Write a story with a small twist and a happy surprise ending, where help comes from someone unexpected and sharing makes the danger go away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    helper = f["helper"]
    load = f["load_cfg"]
    footwear = f["footwear_cfg"]
    repair = f["repair_cfg"]
    helper_cfg = f["helper_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was carrying laundry up a steep hill path, and {helper.id}, who came to help. The elder at the cottage was waiting at the top."
        ),
        (
            f"What problem did {child.id} have on the hill?",
            f"{footwear.loosen_text[0].upper()}{footwear.loosen_text[1:]} That made the climb dangerous because {child.id} was already carrying a heavy load of laundry."
        ),
        (
            f"What did {helper.id} suggest?",
            f"{helper.id} suggested sharing the laundry and fixing the loose sole before climbing farther. That plan helped with both the weight and the slipping danger."
        ),
        (
            f"How did they solve the problem?",
            f"They split the laundry between them, and {helper.id} used {repair.phrase} to fix the shoe. Because the load was shared and the sole was tied firm, {child.id} could climb safely again."
        ),
        (
            "What was the surprise at the end?",
            f"{helper_cfg.reveal_text} The surprise showed that the helper was already connected to the home at the top, not just a passerby."
        ),
        (
            "What changed by the end of the story?",
            f"At first the hill felt dangerous and lonely, but by the end it felt manageable because the burden was shared. The clean laundry reached the line safely, and {child.id} learned that asking for and accepting help can be wise."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"laundry", "sole", "sharing", "repair", "hill"}
    out: list[tuple[str, str]] = []
    for key in ["laundry", "sole", "sharing", "repair", "hill"]:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(load: Load, footwear: Footwear, helper: Helper, repair: Repair) -> str:
    if not helper_can_share(load, helper):
        return (
            f"(No story: {helper.label} cannot reasonably carry enough of the {load.label} to make sharing help on a steep hill path. "
            f"Pick a lighter load or a stronger helper.)"
        )
    if not repair_fits(footwear, repair):
        return (
            f"(No story: {repair.label} is not a sensible fix for the loose {footwear.sole_name} of that {footwear.label}. "
            f"Pick a repair that actually fits the footwear.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def outcome_of(params: StoryParams) -> str:
    load = LOADS[params.load]
    footwear = FOOTWEAR[params.footwear]
    helper = HELPERS[params.helper]
    repair = REPAIRS[params.repair]
    return "safe" if valid_combo(load, footwear, helper, repair) else "spill"


ASP_RULES = r"""
can_share(H, L) :- helper(H), load(L), carry_power(H, P), weight(L, W), P >= W.
repair_fits(F, R) :- footwear(F), repair(R), supports(R, F).
valid(L, F, H, R) :- load(L), footwear(F), helper(H), repair(R), can_share(H, L), repair_fits(F, R).

outcome(safe) :- chosen_load(L), chosen_footwear(F), chosen_helper(H), chosen_repair(R), valid(L, F, H, R).
outcome(spill) :- chosen_load(L), chosen_footwear(F), chosen_helper(H), chosen_repair(R), not valid(L, F, H, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for load_id, load in LOADS.items():
        lines.append(asp.fact("load", load_id))
        lines.append(asp.fact("weight", load_id, load.weight))
    for footwear_id in FOOTWEAR:
        lines.append(asp.fact("footwear", footwear_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("carry_power", helper_id, helper.carry_power))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for footwear_id in sorted(repair.supports):
            lines.append(asp.fact("supports", repair_id, footwear_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_load", params.load),
            asp.fact("chosen_footwear", params.footwear),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_repair", params.repair),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        load="basket",
        footwear="sandal",
        helper="washerwoman",
        repair="reed_twine",
        child_name="Mira",
        child_gender="girl",
        parent_type="grandmother",
        trait="careful",
    ),
    StoryParams(
        load="sheet_roll",
        footwear="shoe",
        helper="shepherd",
        repair="leather_lace",
        child_name="Ivo",
        child_gender="boy",
        parent_type="grandmother",
        trait="steady",
    ),
    StoryParams(
        load="bundle",
        footwear="shoe",
        helper="potter",
        repair="cloth_strip",
        child_name="Lina",
        child_gender="girl",
        parent_type="grandmother",
        trait="kind",
    ),
    StoryParams(
        load="bundle",
        footwear="clog",
        helper="potter",
        repair="leather_lace",
        child_name="Rian",
        child_gender="boy",
        parent_type="grandmother",
        trait="dutiful",
    ),
    StoryParams(
        load="basket",
        footwear="shoe",
        helper="shepherd",
        repair="cloth_strip",
        child_name="Tala",
        child_gender="girl",
        parent_type="grandmother",
        trait="patient",
    ),
]


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed for seed {s}")
            break

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
        sample = generate(CURATED[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test generated an incomplete sample")
        print("OK: smoke test generate() produced story and QA.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folk-tale of laundry, a loose sole, and help on a steep hill path."
    )
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--footwear", choices=FOOTWEAR)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother", "mother", "father"], help="adult waiting at the cottage")
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.load and args.footwear and args.helper and args.repair:
        if not valid_combo(LOADS[args.load], FOOTWEAR[args.footwear], HELPERS[args.helper], REPAIRS[args.repair]):
            raise StoryError(explain_rejection(LOADS[args.load], FOOTWEAR[args.footwear], HELPERS[args.helper], REPAIRS[args.repair]))

    combos = [
        c for c in valid_combos()
        if (args.load is None or c[0] == args.load)
        and (args.footwear is None or c[1] == args.footwear)
        and (args.helper is None or c[2] == args.helper)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        if args.load and args.footwear and args.helper and args.repair:
            raise StoryError(explain_rejection(LOADS[args.load], FOOTWEAR[args.footwear], HELPERS[args.helper], REPAIRS[args.repair]))
        raise StoryError("(No valid combination matches the given options.)")

    load_id, footwear_id, helper_id, repair_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_type = args.parent or "grandmother"
    trait = rng.choice(TRAITS)
    return StoryParams(
        load=load_id,
        footwear=footwear_id,
        helper=helper_id,
        repair=repair_id,
        child_name=name,
        child_gender=gender,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        load = LOADS[params.load]
        footwear = FOOTWEAR[params.footwear]
        helper = HELPERS[params.helper]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not valid_combo(load, footwear, helper, repair):
        raise StoryError(explain_rejection(load, footwear, helper, repair))

    world = tell(
        load=load,
        footwear=footwear,
        helper_cfg=helper,
        repair=repair,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (load, footwear, helper, repair) combos:\n")
        for load_id, footwear_id, helper_id, repair_id in combos:
            print(f"  {load_id:10} {footwear_id:8} {helper_id:12} {repair_id}")
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
            header = f"### {p.child_name}: {p.load}, {p.footwear}, {p.helper}, {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
