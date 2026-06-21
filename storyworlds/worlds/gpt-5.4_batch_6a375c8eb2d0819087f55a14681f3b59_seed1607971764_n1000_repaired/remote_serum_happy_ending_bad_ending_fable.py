#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/remote_serum_happy_ending_bad_ending_fable.py
=========================================================================

A standalone story world for a small fable-shaped domain:

In a remote garden, a young animal finds a bottle of serum that promises
quick growth. The wish is good -- help a hungry plant bear fruit before the
village feast -- but the method may be wise or foolish. Watering the roots and
using only a little serum leads to a happy ending. Pouring strong serum onto a
dry plant leads to a bad ending.

The world is state-driven: physical meters track thirst, growth, scorch, and
fruit; emotional memes track hope, greed, worry, relief, and regret. The same
premise can resolve in two ways, and the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/remote_serum_happy_ending_bad_ending_fable.py
    python storyworlds/worlds/gpt-5.4/remote_serum_happy_ending_bad_ending_fable.py --plant vine --prep water --dose little
    python storyworlds/worlds/gpt-5.4/remote_serum_happy_ending_bad_ending_fable.py --dose flood
    python storyworlds/worlds/gpt-5.4/remote_serum_happy_ending_bad_ending_fable.py --all
    python storyworlds/worlds/gpt-5.4/remote_serum_happy_ending_bad_ending_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/remote_serum_happy_ending_bad_ending_fable.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "hen", "mother", "aunt"}
        male = {"boy", "fox", "mole", "toad", "crow", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
class Setting:
    id: str
    place: str
    opening: str
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
class Plant:
    id: str
    label: str
    phrase: str
    fruit: str
    need: str
    tender: bool
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
class Prep:
    id: str
    label: str
    action: str
    waters: bool
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
class Dose:
    id: str
    label: str
    action: str
    strength: int
    gentle: bool
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
class Helper:
    id: str
    type: str
    name: str
    title: str
    counsel: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World + rules
# ---------------------------------------------------------------------------
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


def _r_gentle_growth(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["serum"] < THRESHOLD:
        return out
    sig = ("gentle_growth",)
    if sig in world.fired:
        return out
    if plant.meters["watered"] >= THRESHOLD and plant.meters["strength"] <= 1:
        world.fired.add(sig)
        plant.meters["growth"] += 2
        plant.meters["fruit_ready"] += 1
        plant.meters["thirst"] = 0.0
        for eid in ("hero", "helper"):
            if eid in world.entities:
                world.get(eid).memes["hope"] += 1
        out.append("__gentle__")
    return out


def _r_burned_roots(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["serum"] < THRESHOLD:
        return out
    sig = ("burned_roots",)
    if sig in world.fired:
        return out
    harsh = plant.meters["strength"] >= 2
    dry = plant.meters["watered"] < THRESHOLD
    tender = plant.attrs.get("tender", False)
    if harsh and dry:
        world.fired.add(sig)
        plant.meters["scorched"] += 2 if tender else 1
        plant.meters["growth"] -= 1
        plant.meters["fruit_lost"] += 1
        plant.meters["thirst"] += 1
        world.get("hero").memes["fear"] += 1
        out.append("__burn__")
    return out


def _r_overgrowth(world: World) -> list[str]:
    out: list[str] = []
    plant = world.get("plant")
    if plant.meters["serum"] < THRESHOLD:
        return out
    sig = ("overgrowth",)
    if sig in world.fired:
        return out
    if plant.meters["watered"] >= THRESHOLD and plant.meters["strength"] >= 2 and plant.attrs.get("tender", False):
        world.fired.add(sig)
        plant.meters["split"] += 1
        plant.meters["fruit_lost"] += 1
        plant.meters["growth"] += 1
        world.get("hero").memes["fear"] += 1
        out.append("__split__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="gentle_growth", tag="physical", apply=_r_gentle_growth),
    Rule(name="burned_roots", tag="physical", apply=_r_burned_roots),
    Rule(name="overgrowth", tag="physical", apply=_r_overgrowth),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints / outcomes
# ---------------------------------------------------------------------------
def can_help_plant(plant: Plant) -> bool:
    return True


def safe_combo(plant: Plant, prep: Prep, dose: Dose) -> bool:
    return prep.waters and dose.gentle


def doomed_combo(plant: Plant, prep: Prep, dose: Dose) -> bool:
    if dose.strength < 2:
        return False
    if not prep.waters:
        return True
    return plant.tender and dose.strength >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for plant_id, plant in PLANTS.items():
            if not can_help_plant(plant):
                continue
            for prep_id in PREPS:
                for dose_id in DOSES:
                    combos.append((setting_id, plant_id, prep_id, dose_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    plant = PLANTS[params.plant]
    prep = PREPS[params.prep]
    dose = DOSES[params.dose]
    if safe_combo(plant, prep, dose):
        return "happy"
    if doomed_combo(plant, prep, dose):
        return "bad"
    return "mixed"


def explain_dose_rejection(dose: Dose) -> str:
    return (
        f"(No story: the dose '{dose.id}' is too wild for this small fable world. "
        f"It would stop feeling like a simple lesson and become chaos instead.)"
    )


# ---------------------------------------------------------------------------
# Screenplay helpers
# ---------------------------------------------------------------------------
def predict_serum(world: World, prep: Prep, dose: Dose) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    if prep.waters:
        plant.meters["watered"] += 1
        plant.meters["thirst"] = 0.0
    plant.meters["serum"] += 1
    plant.meters["strength"] = float(dose.strength)
    propagate(sim, narrate=False)
    return {
        "fruit_ready": plant.meters["fruit_ready"] >= THRESHOLD,
        "scorched": plant.meters["scorched"] >= THRESHOLD,
        "split": plant.meters["split"] >= THRESHOLD,
    }


def introduce(world: World, setting: Setting, hero: Entity, plant: Plant) -> None:
    world.say(
        f"In {setting.place}, there lived {hero.id}, a young {hero.type} who kept a careful eye on {plant.phrase}."
    )
    world.say(setting.opening)
    world.say(
        f"Each morning {hero.pronoun()} visited it and hoped it would someday bear {plant.fruit} for the village table."
    )


def need(world: World, hero: Entity, plant: Plant) -> None:
    hero.memes["care"] += 1
    world.say(
        f"But the days had been dry, and {plant.label} seemed tired. Its leaves drooped as if they had forgotten how to smile."
    )
    world.say(
        f'{hero.id} sighed. "If only this {plant.label} could grow well enough to give us {plant.fruit}," {hero.pronoun()} said.'
    )


def find_serum(world: World, hero: Entity) -> None:
    hero.memes["hope"] += 1
    hero.memes["greed"] += 1
    world.say(
        f"On a stone shelf in the shed, {hero.pronoun()} found a tiny bottle marked serum."
    )
    world.say(
        "On the faded label were these tempting words: A drop may hurry what patience is growing."
    )


def consult(world: World, hero: Entity, helper: Entity, helper_cfg: Helper, plant: Plant, prep: Prep, dose: Dose) -> None:
    pred = predict_serum(world, prep, dose)
    world.facts["predicted_fruit"] = pred["fruit_ready"]
    world.facts["predicted_scorch"] = pred["scorched"]
    world.facts["predicted_split"] = pred["split"]
    helper.memes["care"] += 1
    if pred["scorched"] or pred["split"]:
        extra = f' "{helper_cfg.counsel}"'
    else:
        extra = f' "{helper_cfg.counsel}"'
    world.say(
        f"{hero.id} carried the bottle to {helper_cfg.title} {helper.id}, who lived nearby and understood roots, rain, and waiting."
    )
    world.say(
        f'{helper.id} studied {plant.phrase} and said,{extra}'
    )


def choose(world: World, hero: Entity, prep: Prep, dose: Dose) -> None:
    if prep.waters:
        world.say(
            f"{hero.id} first {prep.action}."
        )
    else:
        world.say(
            f"But haste pulled harder than wisdom, and {hero.id} did not {prep.action}."
        )
    world.say(
        f"Then {hero.pronoun()} {dose.action}."
    )


def apply_serum(world: World, plant_ent: Entity, prep: Prep, dose: Dose) -> None:
    if prep.waters:
        plant_ent.meters["watered"] += 1
        plant_ent.meters["thirst"] = 0.0
    else:
        plant_ent.meters["thirst"] += 1
    plant_ent.meters["serum"] += 1
    plant_ent.meters["strength"] = float(dose.strength)
    propagate(world, narrate=False)


def turn_happy(world: World, hero: Entity, helper: Entity, plant: Plant) -> None:
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"The roots drank calmly. By sunset, {plant.label} stood straighter, and by dawn small signs of {plant.fruit} had begun to show."
    )
    world.say(
        f"{hero.id} danced around the bed of earth, while {helper.id} only smiled the quiet smile of one who had expected patience to win."
    )


def turn_bad(world: World, hero: Entity, helper: Entity, plant: Plant) -> None:
    hero.memes["regret"] += 1
    helper.memes["sorrow"] += 1
    plant_ent = world.get("plant")
    if plant_ent.meters["split"] >= THRESHOLD:
        world.say(
            f"For one foolish moment, {plant.label} lurched upward too fast. Then the tender stem split, and the promise of {plant.fruit} fell limp against the dust."
        )
    else:
        world.say(
            f"The strong serum bit the thirsty roots. A bitter smell rose from the soil, and the leaves curled at their edges like singed paper."
        )
    world.say(
        f"{hero.id} stared at the harm and wished for the slow hour {hero.pronoun()} had tried to skip."
    )


def lesson_happy(world: World, hero: Entity, helper: Entity, plant: Plant) -> None:
    world.say(
        f'{helper.id} said, "Little friend, a wise hand gives help in the measure a living thing can bear."'
    )
    world.say(
        f"And when the village feast came, there was enough {plant.fruit} to share, and {hero.id} shared first with {helper.id}."
    )
    world.say(
        "So in that remote place, the young learned that care grows better than hurry."
    )


def lesson_bad(world: World, hero: Entity, helper: Entity, plant: Plant) -> None:
    world.say(
        f'{helper.id} said, "What is forced beyond its season may break before it blesses."'
    )
    world.say(
        f"No {plant.fruit} graced the feast that week. Yet {hero.id} carried water to the roots each evening, trying at last to serve the plant instead of commanding it."
    )
    world.say(
        "So in that remote place, the young learned that greed asks for miracles and often harvests sorrow."
    )


def tell(
    setting: Setting,
    plant_cfg: Plant,
    prep_cfg: Prep,
    dose_cfg: Dose,
    helper_cfg: Helper,
    hero_name: str = "Nilo",
    hero_type: str = "fox",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper = world.add(Entity(id=helper_cfg.name, kind="character", type=helper_cfg.type, role="helper"))
    plant = world.add(Entity(
        id="plant",
        kind="thing",
        type="plant",
        label=plant_cfg.label,
        role="plant",
        attrs={"tender": plant_cfg.tender},
    ))
    plant.meters["thirst"] = 1.0

    introduce(world, setting, hero, plant_cfg)
    need(world, hero, plant_cfg)

    world.para()
    find_serum(world, hero)
    consult(world, hero, helper, helper_cfg, plant_cfg, prep_cfg, dose_cfg)

    world.para()
    choose(world, hero, prep_cfg, dose_cfg)
    apply_serum(world, plant, prep_cfg, dose_cfg)

    outcome = "mixed"
    if plant.meters["fruit_ready"] >= THRESHOLD:
        outcome = "happy"
    elif plant.meters["scorched"] >= THRESHOLD or plant.meters["split"] >= THRESHOLD or plant.meters["fruit_lost"] >= THRESHOLD:
        outcome = "bad"

    world.para()
    if outcome == "happy":
        turn_happy(world, hero, helper, plant_cfg)
        world.para()
        lesson_happy(world, hero, helper, plant_cfg)
    else:
        turn_bad(world, hero, helper, plant_cfg)
        world.para()
        lesson_bad(world, hero, helper, plant_cfg)

    world.facts.update(
        setting=setting,
        hero=hero,
        helper=helper,
        helper_cfg=helper_cfg,
        plant_cfg=plant_cfg,
        plant=plant,
        prep=prep_cfg,
        dose=dose_cfg,
        outcome=outcome,
        fruit_ready=plant.meters["fruit_ready"] >= THRESHOLD,
        scorched=plant.meters["scorched"] >= THRESHOLD,
        split=plant.meters["split"] >= THRESHOLD,
        moral=("care grows better than hurry" if outcome == "happy" else "greed asks for miracles and often harvests sorrow"),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "glen": Setting(
        id="glen",
        place="a remote glen beyond the last mill",
        opening="There the wind came softly through the reeds, and even the stones looked old enough to give advice.",
        tags={"remote"},
    ),
    "orchard": Setting(
        id="orchard",
        place="a remote orchard on the far side of the hill",
        opening="Few travelers passed that way, and the small paths were known better by sparrows than by carts.",
        tags={"remote", "orchard"},
    ),
    "terrace": Setting(
        id="terrace",
        place="a remote terrace garden above the river",
        opening="It was a quiet patch of earth where the morning sun arrived early and the evening bells sounded far away.",
        tags={"remote", "garden"},
    ),
}

PLANTS = {
    "vine": Plant(
        id="vine",
        label="vine",
        phrase="a thin pumpkin vine",
        fruit="pumpkins",
        need="steady water and slow strength",
        tender=True,
        tags={"plant", "pumpkin"},
    ),
    "pear": Plant(
        id="pear",
        label="pear sapling",
        phrase="a young pear sapling",
        fruit="pears",
        need="water before feeding",
        tender=True,
        tags={"plant", "pear"},
    ),
    "fig": Plant(
        id="fig",
        label="fig shrub",
        phrase="a modest fig shrub",
        fruit="figs",
        need="gentle roots and even care",
        tender=False,
        tags={"plant", "fig"},
    ),
}

PREPS = {
    "water": Prep(
        id="water",
        label="water the roots",
        action="carried two little pails and watered the roots well",
        waters=True,
        tags={"water"},
    ),
    "dry": Prep(
        id="dry",
        label="leave the roots dry",
        action="pause to water the roots first",
        waters=False,
        tags={"dry"},
    ),
}

DOSES = {
    "drop": Dose(
        id="drop",
        label="one drop",
        action="tilted in only one shining drop of the serum",
        strength=1,
        gentle=True,
        tags={"serum", "gentle"},
    ),
    "little": Dose(
        id="little",
        label="a little",
        action="mixed a little serum with water and poured it at the base",
        strength=1,
        gentle=True,
        tags={"serum", "gentle"},
    ),
    "flood": Dose(
        id="flood",
        label="too much",
        action="poured nearly the whole bottle of serum onto the roots",
        strength=2,
        gentle=False,
        tags={"serum", "strong"},
    ),
}

HELPERS = {
    "tortoise": Helper(
        id="tortoise",
        type="toad",
        name="Moro",
        title="Old",
        counsel="Water first, and let the serum be a servant, not a master.",
        tags={"elder"},
    ),
    "crow": Helper(
        id="crow",
        type="crow",
        name="Sable",
        title="Aunt",
        counsel="A hungry root should drink water before it tastes power.",
        tags={"elder"},
    ),
    "mole": Helper(
        id="mole",
        type="mole",
        name="Bram",
        title="Master",
        counsel="Measure helps life; too much help becomes harm.",
        tags={"elder"},
    ),
}

FOX_NAMES = ["Nilo", "Renn", "Pico", "Tarin", "Fenn"]
OTHER_NAMES = ["Luma", "Miri", "Tavi", "Oren", "Suri"]
HERO_TYPES = ["fox", "mole", "toad"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    plant: str
    prep: str
    dose: str
    helper: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "serum": [
        (
            "What is a serum?",
            "A serum is a special liquid meant to change something. Because it is strong, a little can be enough and too much can cause harm."
        )
    ],
    "water": [
        (
            "Why do roots need water?",
            "Roots drink water from the soil so the plant can stay alive and grow. Dry roots are weak, so strong feeding can hurt them."
        )
    ],
    "plant": [
        (
            "Why is patience important when growing plants?",
            "Plants grow a little at a time. Gentle care over many days is safer than trying to force them to hurry."
        )
    ],
    "remote": [
        (
            "What does remote mean?",
            "Remote means far away from busy places. A remote garden is quiet and not near the middle of town."
        )
    ],
}
KNOWLEDGE_ORDER = ["remote", "plant", "water", "serum"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    plant_cfg = f["plant_cfg"]
    outcome = f["outcome"]
    if outcome == "happy":
        return [
            'Write a short fable for a 3-to-5-year-old that uses the words "remote" and "serum" and ends happily.',
            f"Tell a gentle fable about {hero.id}, a young {hero.type}, who finds a serum in a remote garden and learns to use it wisely to help {plant_cfg.phrase}.",
            "Write a simple moral tale where a childlike animal chooses patience over hurry, and the ending shows that careful help is better than greedy haste.",
        ]
    return [
        'Write a short fable for a 3-to-5-year-old that uses the words "remote" and "serum" and has a sad cautionary ending.',
        f"Tell a fable about {hero.id}, a young {hero.type}, who tries to make {plant_cfg.phrase} grow too fast with serum in a remote place and learns a hard lesson.",
        "Write a moral tale where too much power is poured too quickly onto a living thing, and the ending teaches that greed can spoil what care might save.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    plant_cfg = f["plant_cfg"]
    prep = f["prep"]
    dose = f["dose"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {hero.type}, and {helper.id}, an older helper, in a remote garden. The story also centers on {plant_cfg.phrase}, which they hoped would bear {plant_cfg.fruit}."
        ),
        (
            "Why did the hero care about the plant?",
            f"{hero.id} wanted the plant to grow well enough to give {plant_cfg.fruit} for the village table. That wish is why the bottle of serum felt so tempting."
        ),
        (
            "What did the helper warn about?",
            f"{helper.id} warned that roots should be treated gently and not forced. The warning mattered because the plant was thirsty, and strong help on dry roots could do harm."
        ),
    ]
    if outcome == "happy":
        qa.append(
            (
                "Why did the serum help instead of harm the plant?",
                f"It helped because {hero.id} {prep.action} and then used {dose.label} of the serum. The roots were ready, and the small amount gave help without burning or splitting the plant."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The ending was happy: the plant began to bear {plant_cfg.fruit}, and there was enough to share at the feast. That ending proves that patience and measured care changed the day."
            )
        )
    else:
        if f["split"]:
            harm = "the stem split after being forced to grow too fast"
        else:
            harm = "the thirsty roots were scorched by the strong serum"
        qa.append(
            (
                "What went wrong when the hero used the serum?",
                f"What went wrong was that {harm}. The hero tried to skip the slow work of care, and the plant paid the price."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The ending was sad: no {plant_cfg.fruit} came for the feast, and {hero.id} felt regret. Afterward {hero.pronoun()} began carrying water each evening, showing that the lesson had finally reached {hero.pronoun('object')}."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"remote", "plant", "serum"}
    if world.facts["prep"].waters:
        tags.add("water")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *rest in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S, P, Pr, D) :- setting(S), plant(P), prep(Pr), dose(D).

safe(P, Pr, D) :- plant(P), tender(P), prep_waters(Pr), gentle(D).
safe(P, Pr, D) :- plant(P), not tender(P), prep_waters(Pr), gentle(D).

doomed(P, Pr, D) :- strong(D), not prep_waters(Pr).
doomed(P, Pr, D) :- tender(P), strong(D), prep_waters(Pr).

outcome(happy) :- chosen_plant(P), chosen_prep(Pr), chosen_dose(D), safe(P, Pr, D).
outcome(bad) :- chosen_plant(P), chosen_prep(Pr), chosen_dose(D), doomed(P, Pr, D).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        if plant.tender:
            lines.append(asp.fact("tender", plant_id))
    for prep_id, prep in PREPS.items():
        lines.append(asp.fact("prep", prep_id))
        if prep.waters:
            lines.append(asp.fact("prep_waters", prep_id))
    for dose_id, dose in DOSES.items():
        lines.append(asp.fact("dose", dose_id))
        if dose.gentle:
            lines.append(asp.fact("gentle", dose_id))
        if dose.strength >= 2:
            lines.append(asp.fact("strong", dose_id))
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
            asp.fact("chosen_plant", params.plant),
            asp.fact("chosen_prep", params.prep),
            asp.fact("chosen_dose", params.dose),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    if out:
        return out[0][0]
    return "mixed"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue

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
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="glen",
        plant="vine",
        prep="water",
        dose="drop",
        helper="tortoise",
        hero_name="Nilo",
        hero_type="fox",
        seed=1,
    ),
    StoryParams(
        setting="orchard",
        plant="pear",
        prep="water",
        dose="little",
        helper="crow",
        hero_name="Luma",
        hero_type="mole",
        seed=2,
    ),
    StoryParams(
        setting="terrace",
        plant="vine",
        prep="dry",
        dose="flood",
        helper="mole",
        hero_name="Renn",
        hero_type="fox",
        seed=3,
    ),
    StoryParams(
        setting="glen",
        plant="pear",
        prep="water",
        dose="flood",
        helper="tortoise",
        hero_name="Miri",
        hero_type="toad",
        seed=4,
    ),
    StoryParams(
        setting="orchard",
        plant="fig",
        prep="dry",
        dose="flood",
        helper="crow",
        hero_name="Tavi",
        hero_type="fox",
        seed=5,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fable-shaped storyworld about a remote garden, a serum, and the choice between measured care and greedy haste."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--prep", choices=PREPS)
    ap.add_argument("--dose", choices=DOSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--hero-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is not None and args.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {args.setting})")
    if args.plant is not None and args.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {args.plant})")
    if args.prep is not None and args.prep not in PREPS:
        raise StoryError(f"(Unknown prep: {args.prep})")
    if args.dose is not None and args.dose not in DOSES:
        raise StoryError(f"(Unknown dose: {args.dose})")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.plant is None or combo[1] == args.plant)
        and (args.prep is None or combo[2] == args.prep)
        and (args.dose is None or combo[3] == args.dose)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, plant, prep, dose = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    if args.hero_name:
        hero_name = args.hero_name
    else:
        pool = FOX_NAMES if hero_type == "fox" else OTHER_NAMES
        hero_name = rng.choice(pool)
    return StoryParams(
        setting=setting,
        plant=plant,
        prep=prep,
        dose=dose,
        helper=helper,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.prep not in PREPS:
        raise StoryError(f"(Unknown prep: {params.prep})")
    if params.dose not in DOSES:
        raise StoryError(f"(Unknown dose: {params.dose})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.hero_type not in HERO_TYPES:
        raise StoryError(f"(Unknown hero type: {params.hero_type})")

    world = tell(
        setting=SETTINGS[params.setting],
        plant_cfg=PLANTS[params.plant],
        prep_cfg=PREPS[params.prep],
        dose_cfg=DOSES[params.dose],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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
        print(f"{len(asp_valid_combos())} valid (setting, plant, prep, dose) combos:\n")
        for setting, plant, prep, dose in asp_valid_combos():
            probe = StoryParams(
                setting=setting,
                plant=plant,
                prep=prep,
                dose=dose,
                helper="tortoise",
                hero_name="Nilo",
                hero_type="fox",
            )
            print(f"  {setting:8} {plant:5} {prep:5} {dose:5} -> {outcome_of(probe)}")
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
            header = f"### {p.hero_name}: {p.setting}, {p.plant}, {p.prep}, {p.dose} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
