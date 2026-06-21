#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/complaint_lesson_learned_happy_ending_foreshadowing_folk.py
======================================================================================

A standalone story world for a small folk-tale domain built from the seed:
a child makes a complaint about a chore, an elder offers a warning that
foreshadows trouble, the child learns a lesson, and the ending is happy.

The world model is simple and classical:

- A village child is asked to secure a garden boundary before sunset.
- A weak boundary plus a roaming animal can threaten a food crop.
- The elder's warning ("an open gate invites hungry noses") foreshadows the turn.
- The child may ignore the chore long enough for an animal to get in, or may heed
  the warning in time.
- A sensible repair must match the actual weak boundary.
- The ending is always happy, but what changed is state-driven: either the child
  prevented damage, or helped mend the problem and saved the rest of the harvest.

Run it
------
    python storyworlds/worlds/gpt-5.4/complaint_lesson_learned_happy_ending_foreshadowing_folk.py
    python storyworlds/worlds/gpt-5.4/complaint_lesson_learned_happy_ending_foreshadowing_folk.py --boundary gate --animal goat --crop cabbages
    python storyworlds/worlds/gpt-5.4/complaint_lesson_learned_happy_ending_foreshadowing_folk.py --boundary wall
    python storyworlds/worlds/gpt-5.4/complaint_lesson_learned_happy_ending_foreshadowing_folk.py --all --qa
    python storyworlds/worlds/gpt-5.4/complaint_lesson_learned_happy_ending_foreshadowing_folk.py --verify
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
CAREFUL_MIN = 6


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
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
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
            "mother": "mother",
            "father": "father",
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
class Boundary:
    id: str
    label: str
    phrase: str
    weak_spot: str
    weak_verb: str
    breach_kind: str
    stops: set[str] = field(default_factory=set)
    repair_tools: set[str] = field(default_factory=set)
    proverb: str = ""
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
class AnimalCfg:
    id: str
    label: str
    plural_label: str
    move: str
    appetite: set[str] = field(default_factory=set)
    slips_through: set[str] = field(default_factory=set)
    threat: int = 1
    sound: str = ""
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
class CropCfg:
    id: str
    label: str
    patch: str
    edible_to: set[str] = field(default_factory=set)
    harvest_food: str = ""
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
class RepairCfg:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    power: int = 1
    closing_image: str = ""
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_hungry_animal(world: World) -> list[str]:
    out: list[str] = []
    boundary = world.get("boundary")
    animal = world.get("animal")
    crop = world.get("crop")
    if boundary.meters["secure"] >= THRESHOLD:
        return out
    if animal.meters["inside"] < THRESHOLD:
        return out
    sig = ("hungry", animal.id, crop.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    crop.meters["eaten"] += animal.attrs.get("threat", 1)
    crop.meters["harvest"] -= animal.attrs.get("threat", 1)
    world.get("child").memes["alarm"] += 1
    world.get("elder").memes["worry"] += 1
    out.append("__damage__")
    return out


def _r_mend_restores_hope(world: World) -> list[str]:
    out: list[str] = []
    boundary = world.get("boundary")
    if boundary.meters["mended"] < THRESHOLD:
        return out
    sig = ("hope",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["relief"] += 1
    world.get("child").memes["lesson"] += 1
    world.get("elder").memes["trust"] += 1
    out.append("__hope__")
    return out


CAUSAL_RULES = [
    Rule(name="hungry_animal", tag="physical", apply=_r_hungry_animal),
    Rule(name="mend_restores_hope", tag="social", apply=_r_mend_restores_hope),
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


def risk_exists(boundary: Boundary, animal: AnimalCfg, crop: CropCfg) -> bool:
    return animal.id in boundary.stops and crop.id in animal.appetite and animal.id in crop.edible_to


def repair_fits(boundary: Boundary, repair: RepairCfg) -> bool:
    return boundary.breach_kind in repair.fixes and repair.id in boundary.repair_tools


def careful_enough(trait: str, stubbornness: int) -> bool:
    base = {"patient": 6, "steady": 5, "kind": 4, "quick": 3, "proud": 2}.get(trait, 4)
    return base - stubbornness >= 2


def predict_damage(world: World) -> dict:
    sim = world.copy()
    sim.get("animal").meters["inside"] += 1
    propagate(sim, narrate=False)
    crop = sim.get("crop")
    return {
        "animal_enters": sim.get("animal").meters["inside"] >= THRESHOLD,
        "eaten": crop.meters["eaten"],
        "harvest": crop.meters["harvest"],
    }


def introduce(world: World, child: Entity, elder: Entity, crop: CropCfg) -> None:
    world.say(
        f"In a small village ringed with fields, {child.id} lived with {child.pronoun('possessive')} "
        f"{elder.label_word}. Behind their cottage grew {crop.patch}, and every row mattered when winter came."
    )


def duty(world: World, child: Entity, boundary: Boundary) -> None:
    world.say(
        f"Each evening, {child.id} was meant to check {boundary.phrase}, where {boundary.weak_spot} "
        f"sometimes {boundary.weak_verb}."
    )


def complaint(world: World, child: Entity, boundary: Boundary) -> None:
    child.memes["complaint"] += 1
    child.memes["resentment"] += 1
    world.say(
        f'One golden dusk, {child.id} let out a complaint. "{boundary.label.capitalize()} again?" '
        f'{child.pronoun().capitalize()} sighed. "The sun is soft, the swallows are circling, '
        f'and I would rather chase my shadow than fuss with {boundary.label}."'
    )


def foreshadow(world: World, elder: Entity, child: Entity, boundary: Boundary, animal: AnimalCfg) -> None:
    pred = predict_damage(world)
    world.facts["predicted_eaten"] = pred["eaten"]
    elder.memes["caution"] += 1
    world.say(
        f'{elder.label_word.capitalize()} looked toward the garden and said, "{boundary.proverb}. '
        f'Tonight the {animal.plural_label} are {animal.move}, and hungry feet remember small openings."'
    )


def choose_neglect(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} only nudged a pebble with {child.pronoun('possessive')} toe and wandered off beneath the pear tree, "
        f"leaving the work half-done."
    )


def choose_heed(world: World, child: Entity, boundary: Boundary) -> None:
    boundary_ent = world.get("boundary")
    boundary_ent.meters["secure"] += 1
    child.memes["care"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} listened, though the chore still felt heavy. With a small breath and slower hands, "
        f"{child.pronoun()} set {boundary.label} right before the sky went red."
    )


def animal_enters(world: World, animal: AnimalCfg) -> None:
    ent = world.get("animal")
    ent.meters["inside"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before the first star had fully opened, there came {animal.sound} by the garden, and then the soft rustle of leaves."
    )


def discover(world: World, child: Entity, animal: AnimalCfg, crop: CropCfg) -> None:
    eaten = int(world.get("crop").meters["eaten"])
    if eaten <= 1:
        harm = f"one row of {crop.label}"
    else:
        harm = f"several rows of {crop.label}"
    world.say(
        f"{child.id} ran to the patch and found a {animal.label} among the beds, nosing through {harm}. "
        f"The warning no longer sounded like an old saying. It sounded true."
    )


def call_elder(world: World, child: Entity, elder: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f'"{elder.label_word.capitalize()}!" {child.id} cried. "{child.pronoun("possessive").capitalize()} hands made this trouble. '
        f'Please help me mend it."'
    )


def mend(world: World, child: Entity, elder: Entity, boundary: Boundary, repair: RepairCfg, animal: AnimalCfg, crop: CropCfg) -> None:
    boundary_ent = world.get("boundary")
    boundary_ent.meters["secure"] = 1.0
    boundary_ent.meters["mended"] += 1
    world.get("animal").meters["inside"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Together they guided the {animal.label} back out, then {repair.phrase}. "
        f"After that, {child.id} stood watch while the moon climbed and made the silver edges of the {crop.patch} shine."
    )


def lesson(world: World, child: Entity, elder: Entity, boundary: Boundary, repair: RepairCfg, damaged: bool) -> None:
    child.memes["humility"] += 1
    child.memes["lesson"] += 1
    if damaged:
        world.say(
            f'{elder.label_word.capitalize()} put a calm hand on {child.id}\'s shoulder. '
            f'"A small chore may look smaller than play," {elder.pronoun()} said, '
            f'"but little gaps invite big trouble. Remember this night, and let your hands finish what your mouth complains about."'
        )
    else:
        world.say(
            f'{elder.label_word.capitalize()} smiled at {child.id}. "You heard the warning before trouble came," '
            f'{elder.pronoun()} said. "That is how a wise heart grows."'
        )
    world.say(
        f"{child.id} touched the freshly mended {boundary.label} and nodded. "
        f"{child.pronoun().capitalize()} understood that careful work could be as kind as a loaf on the table."
    )
    world.facts["repair_image"] = repair.closing_image


def happy_ending(world: World, child: Entity, elder: Entity, crop: CropCfg, damaged: bool) -> None:
    crop_ent = world.get("crop")
    saved = max(0, int(crop_ent.meters["harvest"]))
    if damaged:
        world.say(
            f"In the morning, enough of the {crop.label} still stood green and proud. They gathered what was saved, "
            f"and the cottage kettle bubbled with {crop.harvest_food} just the same."
        )
    else:
        world.say(
            f"In the morning, every row of {crop.label} waited bright with dew. They gathered the whole patch, "
            f"and the cottage kettle bubbled with {crop.harvest_food}."
        )
    world.say(
        f"From that day on, whenever evening folded over the village, {child.id} checked the garden first and made no complaint. "
        f"{elder.label_word.capitalize()} would glance at {child.pronoun('object')} and smile, and the house felt full, warm, and safe."
    )
    world.facts["saved_rows"] = saved


def tell(
    boundary: Boundary,
    animal: AnimalCfg,
    crop: CropCfg,
    repair: RepairCfg,
    child_name: str = "Mara",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "patient",
    stubbornness: int = 1,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"stubbornness": stubbornness},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        attrs={},
    ))
    world.add(Entity(
        id="boundary",
        kind="thing",
        type=boundary.id,
        label=boundary.label,
        role="boundary",
        attrs={"breach_kind": boundary.breach_kind},
    ))
    world.add(Entity(
        id="animal",
        kind="thing",
        type=animal.id,
        label=animal.label,
        role="animal",
        attrs={"threat": animal.threat},
    ))
    world.add(Entity(
        id="crop",
        kind="thing",
        type=crop.id,
        label=crop.label,
        role="crop",
        attrs={},
    ))

    world.get("boundary").meters["secure"] = 0.0
    world.get("boundary").meters["mended"] = 0.0
    world.get("animal").meters["inside"] = 0.0
    world.get("crop").meters["eaten"] = 0.0
    world.get("crop").meters["harvest"] = 4.0
    child.memes["complaint"] = 0.0
    child.memes["defiance"] = 0.0
    child.memes["care"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["alarm"] = 0.0
    child.memes["lesson"] = 0.0
    elder.memes["caution"] = 0.0
    elder.memes["worry"] = 0.0
    elder.memes["trust"] = 0.0

    world.facts.update(
        boundary_cfg=boundary,
        animal_cfg=animal,
        crop_cfg=crop,
        repair_cfg=repair,
        child=child,
        elder=elder,
        outcome="",
        damaged=False,
    )

    introduce(world, child, elder, crop)
    duty(world, child, boundary)

    world.para()
    complaint(world, child, boundary)
    foreshadow(world, elder, child, boundary, animal)

    heed = careful_enough(trait, stubbornness)
    if heed:
        world.para()
        choose_heed(world, child, boundary)
        lesson(world, child, elder, boundary, repair, damaged=False)
        world.para()
        happy_ending(world, child, elder, crop, damaged=False)
        world.facts["outcome"] = "heeded"
        world.facts["damaged"] = False
    else:
        world.para()
        choose_neglect(world, child)
        animal_enters(world, animal)
        discover(world, child, animal, crop)
        call_elder(world, child, elder)

        world.para()
        mend(world, child, elder, boundary, repair, animal, crop)
        lesson(world, child, elder, boundary, repair, damaged=True)

        world.para()
        happy_ending(world, child, elder, crop, damaged=True)
        world.facts["outcome"] = "mended"
        world.facts["damaged"] = True

    return world


BOUNDARIES = {
    "gate": Boundary(
        id="gate",
        label="gate",
        phrase="the garden gate",
        weak_spot="the latch",
        weak_verb="swung loose",
        breach_kind="latch",
        stops={"goat", "pig"},
        repair_tools={"latch_pin", "bar"},
        proverb="An open gate teaches hunger the way home",
        tags={"gate", "garden"},
    ),
    "fence": Boundary(
        id="fence",
        label="fence",
        phrase="the woven fence",
        weak_spot="one low place in the willow weaving",
        weak_verb="sagged inward",
        breach_kind="weave",
        stops={"goose", "goat"},
        repair_tools={"weave", "bar"},
        proverb="A crooked fence speaks plainly to wandering mouths",
        tags={"fence", "garden"},
    ),
    "pen": Boundary(
        id="pen",
        label="pen door",
        phrase="the little pen door beside the patch",
        weak_spot="the peg",
        weak_verb="slipped from its hole",
        breach_kind="peg",
        stops={"pig", "goose"},
        repair_tools={"peg_tie", "bar"},
        proverb="A loose peg tells the night where supper sleeps",
        tags={"pen", "garden"},
    ),
    "wall": Boundary(
        id="wall",
        label="stone wall",
        phrase="the stone wall",
        weak_spot="the stones",
        weak_verb="stood firm",
        breach_kind="stone",
        stops=set(),
        repair_tools=set(),
        proverb="A true wall keeps its own counsel",
        tags={"wall"},
    ),
}

ANIMALS = {
    "goat": AnimalCfg(
        id="goat",
        label="goat",
        plural_label="goats",
        move="coming down from the hill paths",
        appetite={"cabbages", "beans"},
        slips_through={"gate", "fence"},
        threat=2,
        sound="a blunt little bleat",
        tags={"goat"},
    ),
    "goose": AnimalCfg(
        id="goose",
        label="goose",
        plural_label="geese",
        move="padding home from the stream bank",
        appetite={"beans", "onions"},
        slips_through={"fence", "pen"},
        threat=1,
        sound="a sharp hiss and flutter",
        tags={"goose"},
    ),
    "pig": AnimalCfg(
        id="pig",
        label="pig",
        plural_label="pigs",
        move="snuffling along the lane",
        appetite={"turnips", "cabbages"},
        slips_through={"gate", "pen"},
        threat=2,
        sound="a busy snort in the dust",
        tags={"pig"},
    ),
}

CROPS = {
    "cabbages": CropCfg(
        id="cabbages",
        label="cabbages",
        patch="a patch of cabbages",
        edible_to={"goat", "pig"},
        harvest_food="cabbage soup",
        tags={"cabbages", "garden_food"},
    ),
    "beans": CropCfg(
        id="beans",
        label="beans",
        patch="rows of climbing beans",
        edible_to={"goat", "goose"},
        harvest_food="bean stew",
        tags={"beans", "garden_food"},
    ),
    "turnips": CropCfg(
        id="turnips",
        label="turnips",
        patch="round rows of turnips",
        edible_to={"pig"},
        harvest_food="turnip pot",
        tags={"turnips", "garden_food"},
    ),
    "onions": CropCfg(
        id="onions",
        label="onions",
        patch="silver-green rows of onions",
        edible_to={"goose"},
        harvest_food="onion broth",
        tags={"onions", "garden_food"},
    ),
}

REPAIRS = {
    "latch_pin": RepairCfg(
        id="latch_pin",
        label="a new latch pin",
        phrase="cut a neat new latch pin and set it through the gate",
        fixes={"latch"},
        power=2,
        closing_image="the gate resting straight on its pin",
        tags={"latch", "repair"},
    ),
    "weave": RepairCfg(
        id="weave",
        label="fresh willow weaving",
        phrase="wove fresh willow switches through the open place until the fence stood tight again",
        fixes={"weave"},
        power=1,
        closing_image="the willow fence woven tight as a basket",
        tags={"weave", "repair"},
    ),
    "peg_tie": RepairCfg(
        id="peg_tie",
        label="a cord and peg",
        phrase="tied the peg fast with cord and drove it deep where it belonged",
        fixes={"peg"},
        power=1,
        closing_image="the little peg sitting firm and true",
        tags={"peg", "repair"},
    ),
    "bar": RepairCfg(
        id="bar",
        label="a stout wooden bar",
        phrase="set a stout wooden bar across the opening so no nose or beak could push through",
        fixes={"latch", "weave", "peg"},
        power=2,
        closing_image="a stout bar holding the night outside",
        tags={"bar", "repair"},
    ),
}

GIRL_NAMES = ["Mara", "Tala", "Ina", "Nela", "Ruth", "Lena", "Sela", "Anya"]
BOY_NAMES = ["Tobin", "Ivo", "Milo", "Ren", "Pavel", "Elias", "Bram", "Oren"]
TRAITS = ["patient", "steady", "kind", "quick", "proud"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for boundary_id, boundary in BOUNDARIES.items():
        for animal_id, animal in ANIMALS.items():
            for crop_id, crop in CROPS.items():
                if not risk_exists(boundary, animal, crop):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair_fits(boundary, repair):
                        combos.append((boundary_id, animal_id, crop_id, repair_id))
    return combos


@dataclass
class StoryParams:
    boundary: str
    animal: str
    crop: str
    repair: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    stubbornness: int = 1
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
    "goat": [(
        "Why can a goat be a problem in a garden?",
        "Goats like to nibble leaves and stems, so they can chew through a garden quickly. A small opening can feel like an invitation to a hungry goat."
    )],
    "goose": [(
        "Why should geese be kept out of vegetable beds?",
        "Geese peck and pull at tender plants, and their feet can trample rows. Even one goose can spoil a neat patch if it gets inside."
    )],
    "pig": [(
        "Why can a pig damage a garden?",
        "A pig pushes with its nose and feet while it looks for food. That can break plants and dig up rows very fast."
    )],
    "gate": [(
        "What is a garden gate for?",
        "A garden gate lets people enter and leave, but it also keeps animals out when it is shut well. A gate only helps if its latch is secure."
    )],
    "fence": [(
        "Why does a fence need to be kept tight?",
        "A loose fence can leave gaps where animals push through. Tight weaving keeps the garden safe and the rows undisturbed."
    )],
    "pen": [(
        "Why does a peg matter on a pen door?",
        "A peg is a small thing, but it holds the door in place. When a little piece fails, a bigger problem can walk right in."
    )],
    "repair": [(
        "Why is it wise to mend a small problem early?",
        "Small problems are easier to fix before they grow. A little care at the right time can save a great deal of trouble later."
    )],
    "garden_food": [(
        "Why do families protect their garden crops?",
        "Garden crops become meals for the household, especially in lean seasons. Protecting them is one way of caring for everyone at home."
    )],
    "lesson": [(
        "What lesson do folk tales often teach about chores?",
        "They often teach that humble work matters more than it first seems. Finishing a small duty can protect something precious."
    )],
}
KNOWLEDGE_ORDER = ["gate", "fence", "pen", "goat", "goose", "pig", "repair", "garden_food", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    boundary = f["boundary_cfg"]
    animal = f["animal_cfg"]
    crop = f["crop_cfg"]
    if f["outcome"] == "heeded":
        return [
            f'Write a short folk tale for a young child that includes the word "complaint" and a warning proverb.',
            f"Tell a folk-style story where {child.id} complains about checking a {boundary.label}, but listens to {elder.label_word}'s warning before the {animal.plural_label} can reach the {crop.label}.",
            "Write a gentle lesson story with foreshadowing, a small chore, and a happy ending where wisdom arrives before harm does.",
        ]
    return [
        f'Write a short folk tale for a young child that includes the word "complaint" and a happy ending.',
        f"Tell a folk-style story where {child.id}'s complaint about the {boundary.label} leads to a hungry {animal.label} getting into the {crop.label}, and then the child helps mend the trouble.",
        "Write a lesson story with foreshadowing, a mistake, and a warm ending that shows the child has changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    boundary = f["boundary_cfg"]
    animal = f["animal_cfg"]
    crop = f["crop_cfg"]
    repair = f["repair_cfg"]
    out = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who lived with {child.pronoun('possessive')} {elder.label_word}, and about the little garden that fed them. The trouble began around {boundary.phrase}."
        ),
        (
            "What was the child's complaint?",
            f"{child.id} complained about having to check {boundary.phrase} at evening. {child.pronoun().capitalize()} wanted to play instead of finishing the small chore."
        ),
        (
            "How did the story foreshadow trouble?",
            f"{elder.label_word.capitalize()} warned that {boundary.proverb.lower()}. That warning hinted that a hungry {animal.label} would come if the opening stayed weak."
        ),
    ]
    if out == "heeded":
        qa.extend([
            (
                f"Why did no animal get into the {crop.label}?",
                f"No animal got in because {child.id} listened and secured the {boundary.label} before dark. The warning changed {child.pronoun('possessive')} choice before the danger could become real."
            ),
            (
                "What lesson did the child learn?",
                f"{child.id} learned that a small duty can protect something important. Finishing the chore was a quiet kind of care for the whole household."
            ),
        ])
    else:
        eaten = int(world.get("crop").meters["eaten"])
        qa.extend([
            (
                f"What happened when {child.id} ignored the warning?",
                f"A {animal.label} got into the garden and ate part of the {crop.label}. That happened because the weak {boundary.label} was left half-done, just as the warning had foretold."
            ),
            (
                f"How did {child.id} fix the problem?",
                f"{child.id} called {elder.label_word} and helped {repair.phrase}. Together they drove the {animal.label} out and made the boundary secure again."
            ),
            (
                "What lesson did the child learn?",
                f"{child.id} learned that little gaps can invite big trouble. After seeing {eaten} part of the harvest lost, {child.pronoun()} understood why careful chores matter."
            ),
        ])
    qa.append((
        "How did the story end happily?",
        f"The household still had enough {crop.label} for {crop.harvest_food}, and {child.id} changed {child.pronoun('possessive')} ways. The happy ending is not just the meal, but the wiser habit that came after it."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    boundary = f["boundary_cfg"]
    animal = f["animal_cfg"]
    crop = f["crop_cfg"]
    repair = f["repair_cfg"]
    tags |= boundary.tags
    tags |= animal.tags
    tags |= crop.tags
    tags |= repair.tags
    tags.add("lesson")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        boundary="gate",
        animal="goat",
        crop="cabbages",
        repair="latch_pin",
        child_name="Mara",
        child_gender="girl",
        elder_type="grandmother",
        trait="proud",
        stubbornness=2,
    ),
    StoryParams(
        boundary="fence",
        animal="goose",
        crop="beans",
        repair="weave",
        child_name="Tobin",
        child_gender="boy",
        elder_type="grandfather",
        trait="patient",
        stubbornness=1,
    ),
    StoryParams(
        boundary="pen",
        animal="pig",
        crop="turnips",
        repair="peg_tie",
        child_name="Ina",
        child_gender="girl",
        elder_type="grandmother",
        trait="quick",
        stubbornness=2,
    ),
    StoryParams(
        boundary="gate",
        animal="pig",
        crop="cabbages",
        repair="bar",
        child_name="Ren",
        child_gender="boy",
        elder_type="grandfather",
        trait="steady",
        stubbornness=1,
    ),
]


def explain_rejection(boundary: Boundary, animal: AnimalCfg, crop: CropCfg, repair: Optional[RepairCfg] = None) -> str:
    if not risk_exists(boundary, animal, crop):
        return (
            f"(No story: a {animal.label} is not a believable threat to {crop.label} through the {boundary.label}. "
            f"The hazard must make sense before a lesson can grow from it.)"
        )
    if repair is not None and not repair_fits(boundary, repair):
        return (
            f"(No story: {repair.label} does not properly fix the weak part of the {boundary.label}. "
            f"The repair must actually match the breach.)"
        )
    return "(No story: this combination does not fit the world's common-sense rules.)"


def outcome_of(params: StoryParams) -> str:
    return "heeded" if careful_enough(params.trait, params.stubbornness) else "mended"


ASP_RULES = r"""
risk(B,A,C) :- boundary(B), animal(A), crop(C), stops(B,A), likes(A,C), edible_to(C,A).
fits(B,R)   :- boundary(B), repair(R), breach(B,K), fixes(R,K), allows_repair(B,R).
valid(B,A,C,R) :- risk(B,A,C), fits(B,R).

care_value(6) :- chosen_trait(patient).
care_value(5) :- chosen_trait(steady).
care_value(4) :- chosen_trait(kind).
care_value(3) :- chosen_trait(quick).
care_value(2) :- chosen_trait(proud).

heed :- care_value(V), stubbornness(S), V - S >= 2.
outcome(heeded) :- heed.
outcome(mended) :- not heed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for boundary_id, boundary in BOUNDARIES.items():
        lines.append(asp.fact("boundary", boundary_id))
        lines.append(asp.fact("breach", boundary_id, boundary.breach_kind))
        for animal in sorted(boundary.stops):
            lines.append(asp.fact("stops", boundary_id, animal))
        for repair_id in sorted(boundary.repair_tools):
            lines.append(asp.fact("allows_repair", boundary_id, repair_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for crop_id in sorted(animal.appetite):
            lines.append(asp.fact("likes", animal_id, crop_id))
    for crop_id, crop in CROPS.items():
        lines.append(asp.fact("crop", crop_id))
        for animal_id in sorted(crop.edible_to):
            lines.append(asp.fact("edible_to", crop_id, animal_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for fix in sorted(repair.fixes):
            lines.append(asp.fact("fixes", repair_id, fix))
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
        asp.fact("chosen_trait", params.trait),
        asp.fact("stubbornness", params.stubbornness),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if a - p:
            print("  only in clingo:", sorted(a - p))
        if p - a:
            print("  only in python:", sorted(p - a))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = [params for params in cases if asp_outcome(params) != outcome_of(params)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcome disagreements.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: a complaint, a warning, a lesson, and a happy ending."
    )
    ap.add_argument("--boundary", choices=BOUNDARIES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--crop", choices=CROPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--stubbornness", type=int, choices=[1, 2, 3])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.boundary and args.boundary not in BOUNDARIES:
        raise StoryError("(Unknown boundary.)")
    if args.animal and args.animal not in ANIMALS:
        raise StoryError("(Unknown animal.)")
    if args.crop and args.crop not in CROPS:
        raise StoryError("(Unknown crop.)")
    if args.repair and args.repair not in REPAIRS:
        raise StoryError("(Unknown repair.)")

    if args.boundary and args.animal and args.crop:
        boundary = BOUNDARIES[args.boundary]
        animal = ANIMALS[args.animal]
        crop = CROPS[args.crop]
        if not risk_exists(boundary, animal, crop):
            raise StoryError(explain_rejection(boundary, animal, crop))
    if args.boundary and args.repair:
        boundary = BOUNDARIES[args.boundary]
        repair = REPAIRS[args.repair]
        if not repair_fits(boundary, repair):
            animal = ANIMALS[args.animal] if args.animal else next(iter(ANIMALS.values()))
            crop = CROPS[args.crop] if args.crop else next(iter(CROPS.values()))
            raise StoryError(explain_rejection(boundary, animal, crop, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.boundary is None or combo[0] == args.boundary)
        and (args.animal is None or combo[1] == args.animal)
        and (args.crop is None or combo[2] == args.crop)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    boundary_id, animal_id, crop_id, repair_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or _pick_name(rng, gender)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    stubbornness = args.stubbornness if args.stubbornness is not None else rng.choice([1, 2, 3])

    return StoryParams(
        boundary=boundary_id,
        animal=animal_id,
        crop=crop_id,
        repair=repair_id,
        child_name=name,
        child_gender=gender,
        elder_type=elder,
        trait=trait,
        stubbornness=stubbornness,
    )


def generate(params: StoryParams) -> StorySample:
    if params.boundary not in BOUNDARIES:
        raise StoryError("(Unknown boundary in StoryParams.)")
    if params.animal not in ANIMALS:
        raise StoryError("(Unknown animal in StoryParams.)")
    if params.crop not in CROPS:
        raise StoryError("(Unknown crop in StoryParams.)")
    if params.repair not in REPAIRS:
        raise StoryError("(Unknown repair in StoryParams.)")

    boundary = BOUNDARIES[params.boundary]
    animal = ANIMALS[params.animal]
    crop = CROPS[params.crop]
    repair = REPAIRS[params.repair]

    if not risk_exists(boundary, animal, crop):
        raise StoryError(explain_rejection(boundary, animal, crop))
    if not repair_fits(boundary, repair):
        raise StoryError(explain_rejection(boundary, animal, crop, repair))

    world = tell(
        boundary=boundary,
        animal=animal,
        crop=crop,
        repair=repair,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        trait=params.trait,
        stubbornness=params.stubbornness,
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
        print(f"{len(combos)} compatible (boundary, animal, crop, repair) combos:\n")
        for boundary, animal, crop, repair in combos:
            print(f"  {boundary:8} {animal:6} {crop:9} {repair}")
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
            header = (
                f"### {p.child_name}: {p.boundary}, {p.animal}, {p.crop}, {p.repair} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
