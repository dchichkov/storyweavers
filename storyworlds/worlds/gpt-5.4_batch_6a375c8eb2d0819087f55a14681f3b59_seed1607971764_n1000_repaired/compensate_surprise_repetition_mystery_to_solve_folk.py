#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/compensate_surprise_repetition_mystery_to_solve_folk.py
==================================================================================

A standalone storyworld in a folk-tale mode: a careful village keeper notices
that food keeps vanishing from the garden, sees the loss repeat, follows the
clues, solves the mystery, and is surprised to find a speaking animal asking to
compensate for what it took.

The world is small on purpose. A single edible crop is taken on three nights in
a row. The culprit leaves species-specific clues. On the third night the keeper
keeps watch, solves the mystery, and the culprit offers a concrete way to
compensate. Only combinations where the animal both plausibly steals the crop
and can plausibly compensate for the loss are allowed.

Run it
------
    python storyworlds/worlds/gpt-5.4/compensate_surprise_repetition_mystery_to_solve_folk.py
    python storyworlds/worlds/gpt-5.4/compensate_surprise_repetition_mystery_to_solve_folk.py --crop beans --culprit rabbit
    python storyworlds/worlds/gpt-5.4/compensate_surprise_repetition_mystery_to_solve_folk.py --crop beans --culprit hedgehog
    python storyworlds/worlds/gpt-5.4/compensate_surprise_repetition_mystery_to_solve_folk.py --all
    python storyworlds/worlds/gpt-5.4/compensate_surprise_repetition_mystery_to_solve_folk.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/compensate_surprise_repetition_mystery_to_solve_folk.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/compensate_surprise_repetition_mystery_to_solve_folk.py --verify
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
THEFT_NIGHTS = 3
COMPENSATION_MIN = THEFT_NIGHTS


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Crop:
    id: str
    label: str
    phrase: str
    plural_word: str
    patch: str
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
class CulpritCfg:
    id: str
    label: str
    type: str
    clue: str
    clue_detail: str
    entry: str
    speech: str
    diets: set[str] = field(default_factory=set)
    compensation_ids: set[str] = field(default_factory=set)
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
class Compensation:
    id: str
    label: str
    power: int
    text: str
    ending: str
    qa_text: str
    helpers: set[str] = field(default_factory=set)
    good_for: set[str] = field(default_factory=set)
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
        self.facts: dict = {"clues_seen": [], "nights": []}

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


def _r_missing_bring_worry(world: World) -> list[str]:
    keeper = world.get("keeper")
    patch = world.get("patch")
    produced: list[str] = []
    if patch.meters["missing"] >= THRESHOLD and ("worry",) not in world.fired:
        world.fired.add(("worry",))
        keeper.memes["worry"] += 1
        produced.append("__worry__")
    if patch.meters["missing"] >= 2 * THRESHOLD and ("curiosity",) not in world.fired:
        world.fired.add(("curiosity",))
        keeper.memes["curiosity"] += 1
        produced.append("__curiosity__")
    if patch.meters["missing"] >= 3 * THRESHOLD and ("resolve",) not in world.fired:
        world.fired.add(("resolve",))
        keeper.memes["resolve"] += 1
        produced.append("__resolve__")
    return produced


def _r_compensation_restores(world: World) -> list[str]:
    keeper = world.get("keeper")
    patch = world.get("patch")
    culprit = world.get("culprit")
    if culprit.meters["help_given"] >= culprit.meters["debt"] >= THRESHOLD:
        sig = ("restored",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        patch.meters["restored"] += 1
        keeper.memes["relief"] += 1
        keeper.memes["trust"] += 1
        culprit.memes["gratitude"] += 1
        return ["__restored__"]
    return []


CAUSAL_RULES = [
    Rule(name="missing_bring_worry", tag="emotional", apply=_r_missing_bring_worry),
    Rule(name="compensation_restores", tag="resolution", apply=_r_compensation_restores),
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


def can_steal(crop: Crop, culprit: CulpritCfg) -> bool:
    return crop.id in culprit.diets


def can_compensate(crop: Crop, culprit: CulpritCfg, payment: Compensation) -> bool:
    return (
        culprit.id in payment.helpers
        and crop.id in payment.good_for
        and payment.id in culprit.compensation_ids
        and payment.power >= COMPENSATION_MIN
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for crop_id, crop in CROPS.items():
        for culprit_id, culprit in CULPRITS.items():
            if not can_steal(crop, culprit):
                continue
            for comp_id, payment in COMPENSATIONS.items():
                if can_compensate(crop, culprit, payment):
                    combos.append((crop_id, culprit_id, comp_id))
    return sorted(combos)


def predict_restore(crop: Crop, culprit: CulpritCfg, payment: Compensation) -> dict:
    return {
        "theft_count": THEFT_NIGHTS,
        "restored": can_compensate(crop, culprit, payment),
        "help_power": payment.power,
    }


def introduce(world: World, keeper: Entity, crop: Crop) -> None:
    keeper.memes["contentment"] += 1
    world.say(
        f"In a small village where evening smoke rose blue from the chimneys, "
        f"there lived {keeper.id}, who kept {crop.patch} behind a clay-walled cottage."
    )
    world.say(
        f"{keeper.pronoun().capitalize()} prized {crop.phrase} and counted "
        f"{crop.plural_word} every dusk, because winter was never far from a wise heart."
    )


def first_loss(world: World, crop: Crop) -> None:
    world.say(
        f"On the first morning, {world.get('keeper').id} found that one {crop.label} "
        f"was gone. In the soft earth lay {world.facts['clues_seen'][-1]}."
    )


def repeated_loss(world: World, day_word: str, crop: Crop) -> None:
    world.say(
        f"On the {day_word} morning, again one {crop.label} was gone. Again there lay "
        f"{world.facts['clues_seen'][-1]}."
    )


def night_steal(world: World, crop: Crop, culprit_cfg: CulpritCfg, number: int) -> None:
    patch = world.get("patch")
    culprit = world.get("culprit")
    patch.meters["missing"] += 1
    patch.meters["stock"] -= 1
    culprit.meters["hunger"] = max(0.0, culprit.meters["hunger"] - 1.0)
    culprit.meters["debt"] += 1
    world.facts["clues_seen"].append(culprit_cfg.clue)
    world.facts["nights"].append(number)
    propagate(world, narrate=False)
    if number == 1:
        first_loss(world, crop)
    elif number == 2:
        repeated_loss(world, "second", crop)
    else:
        repeated_loss(world, "third", crop)


def clue_reflection(world: World, culprit_cfg: CulpritCfg) -> None:
    keeper = world.get("keeper")
    if keeper.memes["worry"] >= THRESHOLD:
        world.say(
            f"{keeper.id} frowned. {culprit_cfg.clue_detail}"
        )
    if keeper.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"Two mornings of the same sign made a true mystery, and {keeper.id} "
            f"resolved to read the garden as if it were a page of old wisdom."
        )


def watch_night(world: World, keeper: Entity, crop: Crop) -> None:
    keeper.memes["patience"] += 1
    world.say(
        f"On the third night, instead of sleeping, {keeper.id} wrapped up in a shawl, "
        f"sat beside {crop.patch}, and waited with only the moon and a little lantern for company."
    )


def reveal(world: World, keeper: Entity, crop: Crop, culprit_cfg: CulpritCfg) -> None:
    culprit = world.get("culprit")
    keeper.memes["surprise"] += 1
    world.say(
        f"At midnight the leaves parted, and out came {culprit_cfg.entry}. "
        f"{keeper.id} caught {culprit.pronoun('object')} just as {culprit.pronoun()} reached for another {crop.label}."
    )
    world.say(
        f"Then came the surprise: {culprit_cfg.speech} "
        f'"Please do not fear me," said {culprit.label_word}. '
        f'"I was hungry, and I meant no cruelty."'
    )


def bargain(world: World, keeper: Entity, crop: Crop, payment: Compensation) -> None:
    culprit = world.get("culprit")
    plan = predict_restore(CROPS[world.facts["crop"].id], CULPRITS[world.facts["culprit_cfg"].id], payment)
    keeper.memes["pity"] += 1
    world.say(
        f'{keeper.id} was startled, yet {keeper.pronoun()} heard the hunger in the small voice. '
        f'"Three {crop.plural_word} are missing," {keeper.pronoun()} said. '
        f'"How will you compensate for that?"'
    )
    if plan["restored"]:
        world.say(
            f'"I can {payment.text}," said {culprit.label_word}. '
            f'"If you spare me this once, I will compensate with work before dawn."'
        )


def compensation_scene(world: World, keeper: Entity, crop: Crop, payment: Compensation) -> None:
    culprit = world.get("culprit")
    culprit.meters["help_given"] += payment.power
    patch = world.get("patch")
    patch.meters["health"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So the two made a bargain. Before the stars faded, {culprit.label_word} {payment.text}."
    )
    world.say(
        f"{keeper.id} watched in wonder as the debt of the three missing {crop.plural_word} was answered with patient labor."
    )


def ending(world: World, keeper: Entity, crop: Crop, payment: Compensation) -> None:
    culprit = world.get("culprit")
    if world.get("patch").meters["restored"] >= THRESHOLD:
        world.say(
            f"When dawn came, {payment.ending}."
        )
        world.say(
            f"From that day on, {keeper.id} left one small share at the edge of the garden for {culprit.label_word}, "
            f"and no more was ever stolen. Thus the mystery was solved, the loss was mended, and kindness walked beside fairness."
        )


def tell(
    crop: Crop,
    culprit_cfg: CulpritCfg,
    payment: Compensation,
    keeper_name: str = "Mara",
    keeper_type: str = "grandmother",
) -> World:
    world = World()
    keeper = world.add(
        Entity(
            id=keeper_name,
            kind="character",
            type=keeper_type,
            label="the keeper",
            role="keeper",
            attrs={},
            tags={"keeper"},
        )
    )
    patch = world.add(
        Entity(
            id="patch",
            kind="thing",
            type="garden_patch",
            label=crop.label,
            role="patch",
            attrs={},
            tags=set(crop.tags),
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            kind="character",
            type=culprit_cfg.type,
            label=culprit_cfg.label,
            role="culprit",
            attrs={},
            tags=set(culprit_cfg.tags),
        )
    )
    patch.meters["stock"] = 6.0
    patch.meters["missing"] = 0.0
    patch.meters["restored"] = 0.0
    patch.meters["health"] = 1.0
    culprit.meters["hunger"] = float(THEFT_NIGHTS)
    culprit.meters["debt"] = 0.0
    culprit.meters["help_given"] = 0.0
    keeper.memes["worry"] = 0.0
    keeper.memes["curiosity"] = 0.0
    keeper.memes["resolve"] = 0.0
    keeper.memes["surprise"] = 0.0
    keeper.memes["pity"] = 0.0
    keeper.memes["trust"] = 0.0
    world.facts.update(
        keeper=keeper,
        crop=crop,
        culprit_cfg=culprit_cfg,
        payment=payment,
        solved=False,
        repeated=True,
    )

    introduce(world, keeper, crop)

    world.para()
    night_steal(world, crop, culprit_cfg, 1)
    clue_reflection(world, culprit_cfg)

    world.para()
    night_steal(world, crop, culprit_cfg, 2)
    clue_reflection(world, culprit_cfg)

    world.para()
    watch_night(world, keeper, crop)
    night_steal(world, crop, culprit_cfg, 3)
    reveal(world, keeper, crop, culprit_cfg)

    world.para()
    bargain(world, keeper, crop, payment)
    compensation_scene(world, keeper, crop, payment)
    ending(world, keeper, crop, payment)

    world.facts.update(
        solved=True,
        clue=culprit_cfg.clue,
        missing_count=int(world.get("patch").meters["missing"]),
        restored=world.get("patch").meters["restored"] >= THRESHOLD,
        debt_cleared=world.get("culprit").meters["help_given"] >= world.get("culprit").meters["debt"],
    )
    return world


CROPS = {
    "apples": Crop(
        id="apples",
        label="apple",
        phrase="a row of red apples in a low orchard strip",
        plural_word="apples",
        patch="an apple row",
        tags={"apples", "garden"},
    ),
    "cabbages": Crop(
        id="cabbages",
        label="cabbage",
        phrase="round green cabbages under broad leaves",
        plural_word="cabbages",
        patch="the cabbage bed",
        tags={"cabbages", "garden"},
    ),
    "beans": Crop(
        id="beans",
        label="bean pod",
        phrase="long bean pods hanging from thin poles",
        plural_word="bean pods",
        patch="the bean poles",
        tags={"beans", "garden"},
    ),
}

CULPRITS = {
    "goat": CulpritCfg(
        id="goat",
        label="the gray goat",
        type="animal",
        clue="small hoofprints by the gate",
        clue_detail="The marks were too neat for wind and too light for a cart.",
        entry="a gray goat squeezing through the crooked gate",
        speech="The goat bowed its head and spoke in a voice as scratchy as dry straw.",
        diets={"apples", "cabbages"},
        compensation_ids={"haul_water", "pull_weeds"},
        tags={"goat"},
    ),
    "rabbit": CulpritCfg(
        id="rabbit",
        label="the moon-white rabbit",
        type="animal",
        clue="tiny tooth marks and soft tracks under the leaves",
        clue_detail="No child would nibble so neatly, and no bird would step so softly.",
        entry="a moon-white rabbit hopping from the bean shadows",
        speech="The rabbit stood on its hind feet and spoke as softly as moss.",
        diets={"cabbages", "beans"},
        compensation_ids={"dig_furrows", "pull_weeds"},
        tags={"rabbit"},
    ),
    "hedgehog": CulpritCfg(
        id="hedgehog",
        label="the prickly hedgehog",
        type="animal",
        clue="a rustling tunnel in the grass and a little bitten peel",
        clue_detail="The peel said teeth, yet the hidden path said a low and careful traveler.",
        entry="a prickly hedgehog nosing through the grass",
        speech="The hedgehog lifted its nose and spoke in a voice no louder than a dry leaf.",
        diets={"apples"},
        compensation_ids={"gather_falls"},
        tags={"hedgehog"},
    ),
}

COMPENSATIONS = {
    "haul_water": Compensation(
        id="haul_water",
        label="haul water",
        power=3,
        text="hauled three yoke-buckets from the well and watered every thirsty root",
        ending="the leaves stood fresh and bright, and the whole patch looked richer than it had before the taking",
        qa_text="hauled water from the well and watered the whole garden",
        helpers={"goat"},
        good_for={"cabbages", "beans"},
        tags={"well", "watering"},
    ),
    "pull_weeds": Compensation(
        id="pull_weeds",
        label="pull weeds",
        power=3,
        text="pulled bitter weeds from between the rows until the soil lay clean and loose",
        ending="the beds looked so tidy that even the morning sun seemed pleased to rest on them",
        qa_text="pulled weeds from the beds until the rows were clean",
        helpers={"goat", "rabbit"},
        good_for={"cabbages", "beans"},
        tags={"weeds", "garden_work"},
    ),
    "dig_furrows": Compensation(
        id="dig_furrows",
        label="dig furrows",
        power=3,
        text="dug three straight new furrows where next week's seeds could sleep in warm earth",
        ending="the bean poles stood beside fresh rows ready for more planting, so the garden promised more than it had lost",
        qa_text="dug new furrows for planting",
        helpers={"rabbit"},
        good_for={"beans", "cabbages"},
        tags={"furrows", "planting"},
    ),
    "gather_falls": Compensation(
        id="gather_falls",
        label="gather fallen fruit",
        power=3,
        text="rolled and nudged fallen apples from the grass into a neat shining heap by the door",
        ending="there by the cottage step lay more sound apples than had vanished, all polished by dew",
        qa_text="gathered fallen apples into a neat heap",
        helpers={"hedgehog"},
        good_for={"apples"},
        tags={"apples", "harvest"},
    ),
    "sing_apology": Compensation(
        id="sing_apology",
        label="sing apology",
        power=1,
        text="sang an apology to the moon",
        ending="the song was sweet, but songs do not fill a winter shelf",
        qa_text="sang an apology",
        helpers={"goat", "rabbit", "hedgehog"},
        good_for={"apples", "cabbages", "beans"},
        tags={"song"},
    ),
}

KEEPER_NAMES = ["Mara", "Ina", "Toma", "Sela", "Brana", "Neda"]


def explain_rejection(crop: Crop, culprit: CulpritCfg, payment: Optional[Compensation] = None) -> str:
    if not can_steal(crop, culprit):
        return (
            f"(No story: {culprit.label} is not a plausible taker of {crop.plural_word}, "
            f"so the mystery would not be grounded in this little world.)"
        )
    if payment is not None and payment.power < COMPENSATION_MIN:
        return (
            f"(No story: '{payment.id}' does not truly compensate for three missing "
            f"{crop.plural_word}. The repair must match the loss.)"
        )
    if payment is not None and not can_compensate(crop, culprit, payment):
        return (
            f"(No story: {culprit.label} cannot reasonably compensate for missing "
            f"{crop.plural_word} by '{payment.id}'. Pick a matching form of help.)"
        )
    return "(No story: this combination is outside the world's rules.)"


@dataclass
class StoryParams:
    crop: str
    culprit: str
    compensation: str
    keeper_name: str
    keeper_type: str = "grandmother"
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
    "garden": [
        (
            "Why do gardeners count their food carefully before winter?",
            "People count garden food before winter because stored food helps them through cold months when little is growing. In old village life, even a small loss could matter."
        )
    ],
    "apples": [
        (
            "Why do apples sometimes hide in grass under a tree?",
            "Apples can fall into grass where they are hard to see. That is why gathering fallen fruit can save food that might otherwise be missed."
        )
    ],
    "cabbages": [
        (
            "Why do cabbages need open, weed-free soil?",
            "Cabbages grow better when weeds are pulled away because weeds steal water and food from the soil. Clean rows help the cabbage heads grow full and strong."
        )
    ],
    "beans": [
        (
            "Why are bean plants often grown by poles?",
            "Bean plants climb, so poles help them reach up toward the sun. Keeping the rows neat also makes the pods easier to find and pick."
        )
    ],
    "goat": [
        (
            "What kind of clues can a goat leave in a garden?",
            "A goat may leave hoofprints, chewed leaves, or hair caught on a gate. Those clues help someone guess what sort of animal came by."
        )
    ],
    "rabbit": [
        (
            "What kind of clues can a rabbit leave behind?",
            "A rabbit can leave soft tracks and neat little bite marks. Small clues like that can help solve a mystery."
        )
    ],
    "hedgehog": [
        (
            "How might a hedgehog move through a garden?",
            "A hedgehog moves low to the ground and can make a little rustling path through grass. Because it is small, its trail can be easy to miss at first."
        )
    ],
    "well": [
        (
            "Why does carrying water help a garden?",
            "Plants need water to stay alive and keep growing. When someone carries water in dry weather, the leaves and roots can recover."
        )
    ],
    "weeds": [
        (
            "Why does pulling weeds help crops?",
            "Weeds take up water, space, and sunlight that the crop needs. Pulling them gives the good plants a better chance to grow."
        )
    ],
    "furrows": [
        (
            "What is a furrow?",
            "A furrow is a long narrow groove in the soil for planting. Seeds rest there where earth can cover and protect them."
        )
    ],
    "harvest": [
        (
            "Why is gathering fallen fruit useful?",
            "Fruit that has fallen can still be good to eat if it is found quickly and has not spoiled. Gathering it means less food is wasted."
        )
    ],
    "song": [
        (
            "Why is an apology alone not always enough?",
            "Saying sorry matters, but sometimes a person or animal must also repair the harm. Kind words and helpful action belong together."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "garden",
    "apples",
    "cabbages",
    "beans",
    "goat",
    "rabbit",
    "hedgehog",
    "well",
    "weeds",
    "furrows",
    "harvest",
    "song",
]


def generation_prompts(world: World) -> list[str]:
    keeper = world.facts["keeper"]
    crop = world.facts["crop"]
    culprit_cfg = world.facts["culprit_cfg"]
    payment = world.facts["payment"]
    return [
        f'Write a short folk tale for a young child about a village keeper who notices the same loss three times and solves a mystery. Include the word "compensate".',
        f"Tell a folk-style story where {keeper.id} finds that {crop.plural_word} keep disappearing, follows repeating clues, and discovers that {culprit_cfg.label} is the thief.",
        f"Write a gentle mystery tale with surprise and repetition, where a hungry animal promises to compensate by how it helps: {payment.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    keeper = world.facts["keeper"]
    crop = world.facts["crop"]
    culprit_cfg = world.facts["culprit_cfg"]
    payment = world.facts["payment"]
    missing_count = world.facts["missing_count"]
    clue = world.facts["clue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {keeper.id}, who cared for {crop.patch}, and {culprit_cfg.label}, who kept taking food at night. Their meeting turned a little loss into a mystery and then into a bargain."
        ),
        (
            f"What kept happening in the garden?",
            f"For three mornings in a row, one {crop.label} was missing. The repetition is what told {keeper.id} that this was not chance or wind, but something living and deliberate."
        ),
        (
            f"What clue helped {keeper.id} solve the mystery?",
            f"The clue was {clue}. Seeing the same kind of sign again and again let {keeper.id} guess what sort of visitor had come and decide to keep watch on the third night."
        ),
        (
            "What was the surprise in the story?",
            f"The surprise was that the thief was not only a hungry animal but a speaking one. {culprit_cfg.label.capitalize()} spoke politely and asked for mercy instead of running away."
        ),
        (
            f"Why did {keeper.id} ask how the culprit would compensate?",
            f"{keeper.id} had lost three {crop.plural_word}, so a simple apology was not enough. Asking how the culprit would compensate made the repair match the harm."
        ),
        (
            f"How did {culprit_cfg.label} compensate for the loss?",
            f"{culprit_cfg.label.capitalize()} {payment.qa_text}. That work answered the missing food with real help, so the garden ended stronger than before."
        ),
        (
            "How did the story end?",
            f"It ended with the mystery solved and the loss mended: {missing_count} stolen {crop.plural_word} had been answered by helpful work. After that, {keeper.id} left a small share at the edge of the garden, and nothing more was taken in secret."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    crop = world.facts["crop"]
    culprit_cfg = world.facts["culprit_cfg"]
    payment = world.facts["payment"]
    tags = {"garden"} | set(crop.tags) | set(culprit_cfg.tags) | set(payment.tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  clues_seen: {world.facts.get('clues_seen', [])}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        crop="apples",
        culprit="hedgehog",
        compensation="gather_falls",
        keeper_name="Mara",
        keeper_type="grandmother",
    ),
    StoryParams(
        crop="cabbages",
        culprit="goat",
        compensation="pull_weeds",
        keeper_name="Ina",
        keeper_type="grandmother",
    ),
    StoryParams(
        crop="beans",
        culprit="rabbit",
        compensation="dig_furrows",
        keeper_name="Sela",
        keeper_type="grandmother",
    ),
    StoryParams(
        crop="cabbages",
        culprit="rabbit",
        compensation="pull_weeds",
        keeper_name="Brana",
        keeper_type="grandmother",
    ),
    StoryParams(
        crop="beans",
        culprit="goat",
        compensation="haul_water",
        keeper_name="Neda",
        keeper_type="grandmother",
    ),
]


ASP_RULES = r"""
can_steal(C, K) :- diet(K, C).

can_compensate(C, K, P) :-
    helper(P, K),
    good_for(P, C),
    offers(K, P),
    power(P, N),
    compensation_min(M),
    N >= M.

valid(C, K, P) :- crop(C), culprit(K), payment(P), can_steal(C, K), can_compensate(C, K, P).

debt(3) :- theft_nights(3).
restored :- chosen(C, K, P), valid(C, K, P), debt(D), power(P, N), N >= D.
outcome(restored) :- restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("theft_nights", THEFT_NIGHTS))
    lines.append(asp.fact("compensation_min", COMPENSATION_MIN))
    for crop_id in CROPS:
        lines.append(asp.fact("crop", crop_id))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        for crop_id in sorted(culprit.diets):
            lines.append(asp.fact("diet", culprit_id, crop_id))
        for payment_id in sorted(culprit.compensation_ids):
            lines.append(asp.fact("offers", culprit_id, payment_id))
    for payment_id, payment in COMPENSATIONS.items():
        lines.append(asp.fact("payment", payment_id))
        lines.append(asp.fact("power", payment_id, payment.power))
        for helper in sorted(payment.helpers):
            lines.append(asp.fact("helper", payment_id, helper))
        for crop_id in sorted(payment.good_for):
            lines.append(asp.fact("good_for", payment_id, crop_id))
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
            asp.fact("chosen", params.crop, params.culprit, params.compensation),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    crop = CROPS[params.crop]
    culprit = CULPRITS[params.culprit]
    payment = COMPENSATIONS[params.compensation]
    return "restored" if can_steal(crop, culprit) and can_compensate(crop, culprit, payment) else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos() matches ASP ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_params = CURATED[0]
        sample = generate(smoke_params)
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test generated an incomplete sample")
        emit(sample, trace=False, qa=False)
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a repeating garden mystery, a surprise talking culprit, and a fair way to compensate."
    )
    ap.add_argument("--crop", choices=sorted(CROPS))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--compensation", choices=sorted(COMPENSATIONS))
    ap.add_argument("--keeper-name")
    ap.add_argument("--keeper-type", choices=["grandmother", "grandfather"], default=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against the Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.crop and args.culprit:
        crop = CROPS[args.crop]
        culprit = CULPRITS[args.culprit]
        if not can_steal(crop, culprit):
            raise StoryError(explain_rejection(crop, culprit))
    if args.crop and args.culprit and args.compensation:
        crop = CROPS[args.crop]
        culprit = CULPRITS[args.culprit]
        payment = COMPENSATIONS[args.compensation]
        if not can_compensate(crop, culprit, payment):
            raise StoryError(explain_rejection(crop, culprit, payment))
    if args.compensation and COMPENSATIONS[args.compensation].power < COMPENSATION_MIN:
        if args.crop and args.culprit:
            raise StoryError(explain_rejection(CROPS[args.crop], CULPRITS[args.culprit], COMPENSATIONS[args.compensation]))
        raise StoryError(
            f"(No story: '{args.compensation}' does not truly compensate for the repeated loss in this world.)"
        )

    combos = [
        combo
        for combo in valid_combos()
        if (args.crop is None or combo[0] == args.crop)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.compensation is None or combo[2] == args.compensation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    crop_id, culprit_id, compensation_id = rng.choice(combos)
    keeper_name = args.keeper_name or rng.choice(KEEPER_NAMES)
    keeper_type = args.keeper_type or "grandmother"
    return StoryParams(
        crop=crop_id,
        culprit=culprit_id,
        compensation=compensation_id,
        keeper_name=keeper_name,
        keeper_type=keeper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.crop not in CROPS:
        raise StoryError(f"(Unknown crop '{params.crop}')")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit '{params.culprit}')")
    if params.compensation not in COMPENSATIONS:
        raise StoryError(f"(Unknown compensation '{params.compensation}')")

    crop = CROPS[params.crop]
    culprit = CULPRITS[params.culprit]
    payment = COMPENSATIONS[params.compensation]
    if not can_steal(crop, culprit):
        raise StoryError(explain_rejection(crop, culprit))
    if not can_compensate(crop, culprit, payment):
        raise StoryError(explain_rejection(crop, culprit, payment))

    world = tell(
        crop=crop,
        culprit_cfg=culprit,
        payment=payment,
        keeper_name=params.keeper_name,
        keeper_type=params.keeper_type,
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
        print(f"{len(combos)} compatible (crop, culprit, compensation) combos:\n")
        for crop_id, culprit_id, compensation_id in combos:
            print(f"  {crop_id:10} {culprit_id:10} {compensation_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.keeper_name}: {p.culprit} taking {p.crop} ({p.compensation})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
