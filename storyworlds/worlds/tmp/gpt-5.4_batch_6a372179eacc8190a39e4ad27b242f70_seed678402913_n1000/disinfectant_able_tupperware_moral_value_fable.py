#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/disinfectant_able_tupperware_moral_value_fable.py
==============================================================================

A small fable-shaped storyworld about choosing the right way to clean a food
container before sharing a meal. The seed words "disinfectant", "able", and
"tupperware" are built into the domain.

Premise
-------
A young animal wants to use a container for a shared snack. The container is
dirty or smelly. A stronger cleaner can make it look ready fast, but if the
container will hold food, the world insists on a proper rinse before it is safe.
A patient helper teaches that being eager and able is not enough; wisdom means
using the right method and finishing the job.

Run it
------
    python storyworlds/worlds/gpt-5.4/disinfectant_able_tupperware_moral_value_fable.py
    python storyworlds/worlds/gpt-5.4/disinfectant_able_tupperware_moral_value_fable.py --all
    python storyworlds/worlds/gpt-5.4/disinfectant_able_tupperware_moral_value_fable.py --container tupperware --cleaner disinfectant --rinse no
    python storyworlds/worlds/gpt-5.4/disinfectant_able_tupperware_moral_value_fable.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    food_safe: bool = False
    can_hold_food: bool = False
    can_help: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "girl", "mother", "aunt"}
        male = {"fox", "bear", "boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class AnimalSpec:
    id: str
    kind: str
    virtue: str
    opening: str
    voice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ContainerSpec:
    id: str
    label: str
    phrase: str
    lid_word: str
    food_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ResidueSpec:
    id: str
    label: str
    look: str
    smell: str
    stain_level: int
    tags: set[str] = field(default_factory=set)


@dataclass
class CleanerSpec:
    id: str
    label: str
    phrase: str
    strength: int
    harsh: bool
    needs_rinse: bool
    safe_on_food_container: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class FoodSpec:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


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


def _r_clean_strength(world: World) -> list[str]:
    out: list[str] = []
    container = world.get("container")
    cleaner = world.get("cleaner")
    residue = world.get("residue")
    if container.meters["washed"] < THRESHOLD:
        return out
    sig = ("clean_strength", cleaner.id, residue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    reduction = min(cleaner.attrs["strength"], residue.attrs["stain_level"])
    container.meters["dirty"] = max(0.0, container.meters["dirty"] - reduction)
    if cleaner.attrs["harsh"]:
        container.meters["chemical_smell"] += 1
    return out


def _r_rinse_finishes(world: World) -> list[str]:
    out: list[str] = []
    container = world.get("container")
    cleaner = world.get("cleaner")
    if container.meters["rinsed"] < THRESHOLD:
        return out
    sig = ("rinse_finishes", cleaner.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if cleaner.attrs["needs_rinse"]:
        container.meters["chemical_smell"] = 0.0
    container.meters["wet"] += 1
    return out


def _r_ready_for_food(world: World) -> list[str]:
    out: list[str] = []
    container = world.get("container")
    if container.meters["dirty"] > 0:
        return out
    if container.meters["chemical_smell"] > 0:
        return out
    sig = ("ready", container.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    container.food_safe = True
    return out


CAUSAL_RULES = [
    Rule(name="clean_strength", tag="physical", apply=_r_clean_strength),
    Rule(name="rinse_finishes", tag="physical", apply=_r_rinse_finishes),
    Rule(name="ready_for_food", tag="physical", apply=_r_ready_for_food),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ANIMALS = {
    "fox": AnimalSpec(
        id="fox",
        kind="fox",
        virtue="quick paws",
        opening="loved to hurry through every chore",
        voice="bright",
        tags={"fox"},
    ),
    "beaver": AnimalSpec(
        id="beaver",
        kind="beaver",
        virtue="busy paws",
        opening="liked to build neat plans",
        voice="steady",
        tags={"beaver"},
    ),
    "rabbit": AnimalSpec(
        id="rabbit",
        kind="rabbit",
        virtue="nimble feet",
        opening="was always first to volunteer",
        voice="soft",
        tags={"rabbit"},
    ),
    "goose": AnimalSpec(
        id="goose",
        kind="goose",
        virtue="strong wings",
        opening="was proud to keep things tidy",
        voice="clear",
        tags={"goose"},
    ),
}

HELPERS = {
    "owl": AnimalSpec(
        id="owl",
        kind="owl",
        virtue="patient eyes",
        opening="watched the little valley quietly",
        voice="calm",
        tags={"owl", "wisdom"},
    ),
    "tortoise": AnimalSpec(
        id="tortoise",
        kind="tortoise",
        virtue="slow certainty",
        opening="believed that careful work saves time later",
        voice="gentle",
        tags={"tortoise", "wisdom"},
    ),
}

CONTAINERS = {
    "tupperware": ContainerSpec(
        id="tupperware",
        label="tupperware",
        phrase="a clear tupperware tub",
        lid_word="snap-on lid",
        food_use="hold the afternoon snack",
        tags={"tupperware", "container", "food"},
    ),
    "jar": ContainerSpec(
        id="jar",
        label="jar",
        phrase="a little glass jar",
        lid_word="round lid",
        food_use="carry a sweet treat",
        tags={"jar", "container", "food"},
    ),
    "lunchbox": ContainerSpec(
        id="lunchbox",
        label="lunch box",
        phrase="a small lunch box",
        lid_word="clicking lid",
        food_use="bring supper to the hill",
        tags={"lunchbox", "container", "food"},
    ),
}

RESIDUES = {
    "jam": ResidueSpec(
        id="jam",
        label="berry jam",
        look="sticky purple streaks",
        smell="sweet and old",
        stain_level=1,
        tags={"jam", "sticky"},
    ),
    "soup": ResidueSpec(
        id="soup",
        label="bean soup",
        look="a cloudy ring",
        smell="savory and sour",
        stain_level=1,
        tags={"soup", "smell"},
    ),
    "fish": ResidueSpec(
        id="fish",
        label="fish mash",
        look="greasy gray smears",
        smell="sharp and lingering",
        stain_level=2,
        tags={"fish", "smell"},
    ),
}

CLEANERS = {
    "soap": CleanerSpec(
        id="soap",
        label="soap",
        phrase="warm water and soap",
        strength=1,
        harsh=False,
        needs_rinse=False,
        safe_on_food_container=True,
        tags={"soap", "cleaning"},
    ),
    "disinfectant": CleanerSpec(
        id="disinfectant",
        label="disinfectant",
        phrase="a bright bottle of disinfectant",
        strength=2,
        harsh=True,
        needs_rinse=True,
        safe_on_food_container=True,
        tags={"disinfectant", "cleaning"},
    ),
    "vinegar": CleanerSpec(
        id="vinegar",
        label="vinegar",
        phrase="a splash of vinegar and warm water",
        strength=1,
        harsh=False,
        needs_rinse=False,
        safe_on_food_container=True,
        tags={"vinegar", "cleaning"},
    ),
}

FOODS = {
    "berries": FoodSpec(
        id="berries",
        label="berries",
        phrase="red berries and apple slices",
        tags={"berries", "food"},
    ),
    "seeds": FoodSpec(
        id="seeds",
        label="seeds",
        phrase="sunflower seeds and pear cubes",
        tags={"seeds", "food"},
    ),
    "cakes": FoodSpec(
        id="cakes",
        label="cakes",
        phrase="two small oat cakes",
        tags={"cakes", "food"},
    ),
}


def cleaner_works(cleaner: CleanerSpec, residue: ResidueSpec) -> bool:
    return cleaner.strength >= residue.stain_level


def food_safe_plan(cleaner: CleanerSpec, rinse: str) -> bool:
    if cleaner.needs_rinse:
        return rinse == "yes"
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for hero_id in ANIMALS:
        for helper_id in HELPERS:
            for container_id in CONTAINERS:
                for residue_id, residue in RESIDUES.items():
                    for cleaner_id, cleaner in CLEANERS.items():
                        if not cleaner_works(cleaner, residue):
                            continue
                        for rinse in ("yes", "no"):
                            if food_safe_plan(cleaner, rinse):
                                combos.append((hero_id, helper_id, container_id, residue_id, cleaner_id, rinse))
    return combos


@dataclass
class StoryParams:
    hero: str
    helper: str
    container: str
    residue: str
    cleaner: str
    rinse: str
    food: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        hero="fox",
        helper="owl",
        container="tupperware",
        residue="jam",
        cleaner="soap",
        rinse="yes",
        food="berries",
        hero_name="Fenn",
        helper_name="Old Owl",
        seed=101,
    ),
    StoryParams(
        hero="rabbit",
        helper="tortoise",
        container="tupperware",
        residue="fish",
        cleaner="disinfectant",
        rinse="yes",
        food="cakes",
        hero_name="Pip",
        helper_name="Grand Tortoise",
        seed=102,
    ),
    StoryParams(
        hero="beaver",
        helper="owl",
        container="jar",
        residue="soup",
        cleaner="vinegar",
        rinse="yes",
        food="seeds",
        hero_name="Moss",
        helper_name="Old Owl",
        seed=103,
    ),
]


HERO_NAMES = {
    "fox": ["Fenn", "Ash", "Reed"],
    "beaver": ["Moss", "Birch", "Dap"],
    "rabbit": ["Pip", "Fern", "Hopper"],
    "goose": ["Nell", "Brisk", "Wisp"],
}

HELPER_NAMES = {
    "owl": ["Old Owl", "Aunt Owl"],
    "tortoise": ["Grand Tortoise", "Mossback Tortoise"],
}

FOOD_ORDER = ["berries", "seeds", "cakes"]


def explain_rejection(cleaner: CleanerSpec, residue: ResidueSpec, rinse: str) -> str:
    if not cleaner_works(cleaner, residue):
        return (
            f"(No story: {cleaner.label} is too weak for {residue.label}. "
            f"The container would still be dirty, so there is no honest happy ending.)"
        )
    if not food_safe_plan(cleaner, rinse):
        return (
            f"(No story: {cleaner.label} can clean a food container only if it is rinsed well afterward. "
            f"Without the rinse, the container still smells sharp and is not safe for the shared snack.)"
        )
    return "(No story: this cleaning plan is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "safe_share"


def predict_plan(cleaner: CleanerSpec, residue: ResidueSpec, rinse: str) -> dict[str, bool]:
    world = World()
    container = world.add(
        Entity(
            id="container",
            kind="thing",
            type="container",
            label="container",
            can_hold_food=True,
            food_safe=False,
        )
    )
    world.add(
        Entity(
            id="cleaner",
            kind="thing",
            type="cleaner",
            label=cleaner.label,
            attrs={
                "strength": cleaner.strength,
                "harsh": cleaner.harsh,
                "needs_rinse": cleaner.needs_rinse,
            },
        )
    )
    world.add(
        Entity(
            id="residue",
            kind="thing",
            type="residue",
            label=residue.label,
            attrs={"stain_level": residue.stain_level},
        )
    )
    container.meters["dirty"] = float(residue.stain_level)
    container.meters["washed"] += 1
    if rinse == "yes":
        container.meters["rinsed"] += 1
    propagate(world, narrate=False)
    return {
        "clean": container.meters["dirty"] <= 0,
        "sharp_smell": container.meters["chemical_smell"] >= THRESHOLD,
        "food_safe": container.food_safe,
    }


def opening(world: World, hero: Entity, hero_spec: AnimalSpec, container: Entity, residue: ResidueSpec) -> None:
    world.say(
        f"In the ferny hollow, {hero.id} the {hero.type} {hero_spec.opening}. "
        f"One morning {hero.pronoun()} found {container.phrase} with {residue.look} inside "
        f"and a smell that was {residue.smell}."
    )
    world.say(
        f'"If I can clean it, I will be able to {world.facts["container_cfg"].food_use}," '
        f'{hero.pronoun()} said.'
    )


def plan_feast(world: World, hero: Entity, food: FoodSpec) -> None:
    hero.memes["generosity"] += 1
    world.say(
        f"{hero.id} wanted to fill it with {food.phrase} and share them under the willow tree."
    )


def hurry(world: World, hero: Entity, cleaner: CleanerSpec) -> None:
    hero.memes["pride"] += 1
    if cleaner.id == "disinfectant":
        world.say(
            f"{hero.pronoun().capitalize()} reached for {cleaner.phrase}. "
            f'"This is strong. It will make the job quick," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f"{hero.pronoun().capitalize()} reached for {cleaner.phrase} and set to work at once."
        )


def warn(world: World, helper: Entity, hero: Entity, cleaner: CleanerSpec, container: Entity, residue: ResidueSpec, rinse: str) -> None:
    pred = predict_plan(cleaner, residue, rinse)
    world.facts["pred_food_safe"] = pred["food_safe"]
    world.facts["pred_sharp_smell"] = pred["sharp_smell"]
    helper.memes["care"] += 1
    if cleaner.id == "disinfectant":
        if rinse == "no":
            world.say(
                f'Just then {helper.id} the {helper.type} came by and lifted {helper.pronoun("possessive")} head. '
                f'"You are able to scrub hard," {helper.pronoun()} said, '
                f'"but a food tub cleaned with disinfectant must be rinsed well. '
                f'If you hurry past the rinse, the smell will stay in the {container.label_word}."'
            )
        else:
            world.say(
                f'Just then {helper.id} the {helper.type} came by and nodded. '
                f'"Disinfectant can help with a stubborn smell," {helper.pronoun()} said, '
                f'"but only if you finish the job with a full rinse. Strength without care leaves work half-done."'
            )
    else:
        world.say(
            f'{helper.id} the {helper.type} watched a moment and said, '
            f'"A clean meal begins with a careful bowl. Do not merely look clean; make the {container.label_word} truly ready."'
        )


def wash(world: World, hero: Entity, cleaner: CleanerSpec, residue: ResidueSpec, container: Entity) -> None:
    world.get("container").meters["washed"] += 1
    propagate(world, narrate=False)
    container.meters["scrubbed_with_" + cleaner.id] += 1
    if cleaner.id == "disinfectant":
        world.say(
            f"{hero.id} rubbed the {container.label_word} with {cleaner.label} until the {residue.look} disappeared."
        )
    else:
        world.say(
            f"{hero.id} washed the {container.label_word} until the {residue.look} loosened and slid away."
        )


def rinse(world: World, hero: Entity, cleaner: CleanerSpec, container: Entity) -> None:
    world.get("container").meters["rinsed"] += 1
    propagate(world, narrate=False)
    if cleaner.needs_rinse:
        world.say(
            f"Then {hero.id} carried the {container.label_word} to the brook and rinsed it and its {world.facts['container_cfg'].lid_word} again and again."
        )
    else:
        world.say(
            f"Then {hero.id} gave the {container.label_word} one last bright rinse in the brook."
        )


def skip_rinse(world: World, hero: Entity, cleaner: CleanerSpec, container: Entity) -> None:
    if cleaner.needs_rinse:
        world.say(
            f"But {hero.id} almost snapped the {world.facts['container_cfg'].lid_word} shut at once. "
            f"The {container.label_word} looked ready, yet a sharp smell still clung to it."
        )


def change_heart(world: World, helper: Entity, hero: Entity, cleaner: CleanerSpec, container: Entity) -> None:
    hero.memes["humility"] += 1
    if cleaner.needs_rinse:
        world.say(
            f'{hero.id} stopped and sniffed. "{helper.id} is right," {hero.pronoun()} murmured. '
            f'"Being able to start a task is not the same as being wise enough to finish it."'
        )
    else:
        world.say(
            f'{hero.id} slowed down and smiled. "{helper.id} is right," {hero.pronoun()} said. '
            f'"Careful work makes sharing easy."'
        )


def pack_food(world: World, hero: Entity, helper: Entity, container: Entity, food: FoodSpec) -> None:
    container.food_safe = True
    hero.memes["joy"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"Soon the {container.label_word} smelled only of clean water. "
        f"{hero.id} tucked in {food.phrase}, pressed on the lid, and carried the treat to the willow tree."
    )
    world.say(
        f"There {hero.id} shared the food with {helper.id}, and the meal tasted of berries and friendship, not of hurry."
    )
    world.say(
        "From then on, the young folk of the hollow said that good hands should walk beside good sense."
    )


def moral(world: World) -> None:
    world.say("Moral: It is good to be able, but better to be careful enough to finish a job the right way.")


def tell(
    hero_spec: AnimalSpec,
    helper_spec: AnimalSpec,
    container_cfg: ContainerSpec,
    residue_cfg: ResidueSpec,
    cleaner_cfg: CleanerSpec,
    food_cfg: FoodSpec,
    hero_name: str,
    helper_name: str,
    rinse_choice: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_spec.kind,
            label=hero_name,
            role="hero",
            traits=[hero_spec.virtue],
            tags=set(hero_spec.tags),
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_spec.kind,
            label=helper_name,
            role="helper",
            traits=[helper_spec.virtue],
            tags=set(helper_spec.tags),
            can_help=True,
        )
    )
    container = world.add(
        Entity(
            id="container",
            kind="thing",
            type="container",
            label=container_cfg.label,
            phrase=container_cfg.phrase,
            role="container",
            can_hold_food=True,
            tags=set(container_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="cleaner",
            kind="thing",
            type="cleaner",
            label=cleaner_cfg.label,
            phrase=cleaner_cfg.phrase,
            attrs={
                "strength": cleaner_cfg.strength,
                "harsh": cleaner_cfg.harsh,
                "needs_rinse": cleaner_cfg.needs_rinse,
            },
            tags=set(cleaner_cfg.tags),
        )
    )
    world.add(
        Entity(
            id="residue",
            kind="thing",
            type="residue",
            label=residue_cfg.label,
            attrs={"stain_level": residue_cfg.stain_level},
            tags=set(residue_cfg.tags),
        )
    )
    container.meters["dirty"] = float(residue_cfg.stain_level)

    world.facts.update(
        hero=hero,
        helper=helper,
        container=container,
        hero_spec=hero_spec,
        helper_spec=helper_spec,
        container_cfg=container_cfg,
        residue_cfg=residue_cfg,
        cleaner_cfg=cleaner_cfg,
        food_cfg=food_cfg,
        rinse_choice=rinse_choice,
    )

    opening(world, hero, hero_spec, container, residue_cfg)
    plan_feast(world, hero, food_cfg)

    world.para()
    hurry(world, hero, cleaner_cfg)
    warn(world, helper, hero, cleaner_cfg, container, residue_cfg, rinse_choice)
    wash(world, hero, cleaner_cfg, residue_cfg, container)

    world.para()
    if cleaner_cfg.needs_rinse and rinse_choice == "no":
        skip_rinse(world, hero, cleaner_cfg, container)
        change_heart(world, helper, hero, cleaner_cfg, container)
        rinse(world, hero, cleaner_cfg, container)
        repaired = True
    else:
        change_heart(world, helper, hero, cleaner_cfg, container)
        rinse(world, hero, cleaner_cfg, container)
        repaired = False

    world.para()
    pack_food(world, hero, helper, container, food_cfg)
    moral(world)

    world.facts.update(
        repaired_after_warning=repaired,
        used_disinfectant=cleaner_cfg.id == "disinfectant",
        food_safe=container.food_safe,
        moral="It is good to be able, but better to be careful enough to finish a job the right way.",
    )
    return world


KNOWLEDGE = {
    "disinfectant": [
        (
            "What is disinfectant?",
            "Disinfectant is a cleaner that kills many germs on hard surfaces. It must be used the right way and kept away from food unless a grown-up says the surface is rinsed and ready."
        )
    ],
    "tupperware": [
        (
            "What is tupperware?",
            "Tupperware is a reusable food container with a lid. People use it to store snacks or leftovers."
        )
    ],
    "soap": [
        (
            "Why do people wash food containers with soap and water?",
            "Soap and water help lift grease, old food, and dirt away from a container. When the container is rinsed well, it is ready to hold food again."
        )
    ],
    "rinse": [
        (
            "Why does rinsing matter after cleaning?",
            "Rinsing washes away leftover cleaner and loosened dirt. It helps a bowl or tub smell clean instead of sharp."
        )
    ],
    "sharing": [
        (
            "Why is careful cleaning part of sharing food kindly?",
            "When you share food, you should make the container clean and safe for everyone. Care shows respect for the people eating with you."
        )
    ],
    "moral": [
        (
            "What does it mean to be able but not yet wise?",
            "It means you may have the strength or skill to begin a task, but you still need judgment to do it properly. Wisdom finishes what eagerness starts."
        )
    ],
}

KNOWLEDGE_ORDER = ["disinfectant", "tupperware", "soap", "rinse", "sharing", "moral"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cleaner = f["cleaner_cfg"]
    container = f["container_cfg"]
    return [
        f'Write a short fable for young children that includes the words "disinfectant", "able", and "{container.label}".',
        f"Tell a moral-value story where {hero.id} the {hero.type} wants to clean {container.phrase} for food, and {helper.id} the {helper.type} teaches that careful work matters more than hurry.",
        f"Write a gentle animal fable in which {cleaner.label} is mentioned, a shared snack depends on proper cleaning, and the ending states a clear moral.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    container_cfg = f["container_cfg"]
    residue_cfg = f["residue_cfg"]
    cleaner_cfg = f["cleaner_cfg"]
    food_cfg = f["food_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, who wanted to clean {container_cfg.phrase} for a shared meal, and {helper.id} the {helper.type}, who gave wise advice."
        ),
        (
            f"Why did {hero.id} want to clean the {container_cfg.label}?",
            f"{hero.pronoun().capitalize()} wanted to use it to {container_cfg.food_use}. {hero.pronoun().capitalize()} planned to pack {food_cfg.phrase} and share them kindly."
        ),
        (
            f"What was wrong with the {container_cfg.label} at first?",
            f"It had {residue_cfg.look} inside and smelled {residue_cfg.smell}. That meant it was not yet ready to hold fresh food."
        ),
    ]
    if cleaner_cfg.id == "disinfectant":
        qa.append(
            (
                f"Why did {helper.id} warn {hero.id} about the disinfectant?",
                f"{helper.id} warned that disinfectant was strong but had to be rinsed away before the container could hold food safely. The lesson was that speed alone does not make a job truly finished."
            )
        )
    else:
        qa.append(
            (
                f"What lesson did {helper.id} give while {hero.id} was cleaning?",
                f"{helper.id} said the container should be truly ready, not just look clean. That reminder pushed {hero.id} to slow down and finish the work carefully."
            )
        )
    if f.get("repaired_after_warning"):
        qa.append(
            (
                f"What change did {hero.id} make after the warning?",
                f"{hero.id} first almost stopped too soon, then listened and rinsed the container well. Because of that second careful step, the sharp cleaner smell was gone before the food was packed."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The {container_cfg.label} became clean and ready, and {hero.id} shared {food_cfg.phrase} with {helper.id} under the willow tree. The ending proves the lesson because the meal is safe only after the careful final step."
        )
    )
    qa.append(
        (
            "What is the moral of the fable?",
            "The moral is that it is good to be able, but better to finish a job the right way. Skill matters most when it is guided by care."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"sharing", "moral", "rinse", "tupperware"}
    if world.facts["cleaner_cfg"].id == "disinfectant":
        tags.add("disinfectant")
    else:
        tags.add("soap")
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if ent.food_safe:
            flags.append("food_safe")
        if ent.can_hold_food:
            flags.append("can_hold_food")
        if ent.can_help:
            flags.append("can_help")
        if flags:
            bits.append(f"flags={flags}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
works(C, R) :- cleaner(C), residue(R), strength(C, S), stain_level(R, T), S >= T.
safe_plan(C, yes) :- cleaner(C), needs_rinse(C).
safe_plan(C, no)  :- cleaner(C), not needs_rinse(C).
safe_plan(C, yes) :- cleaner(C), not needs_rinse(C).

valid(H, Hp, Ct, R, C, Ri) :-
    hero(H), helper(Hp), container(Ct), residue(R), cleaner(C), rinse(Ri),
    works(C, R), safe_plan(C, Ri).

outcome(safe_share) :- chosen_cleaner(C), chosen_residue(R), chosen_rinse(Ri), works(C, R), safe_plan(C, Ri).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hero_id in ANIMALS:
        lines.append(asp.fact("hero", hero_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for container_id in CONTAINERS:
        lines.append(asp.fact("container", container_id))
    for residue_id, residue in RESIDUES.items():
        lines.append(asp.fact("residue", residue_id))
        lines.append(asp.fact("stain_level", residue_id, residue.stain_level))
    for cleaner_id, cleaner in CLEANERS.items():
        lines.append(asp.fact("cleaner", cleaner_id))
        lines.append(asp.fact("strength", cleaner_id, cleaner.strength))
        if cleaner.needs_rinse:
            lines.append(asp.fact("needs_rinse", cleaner_id))
    lines.append(asp.fact("rinse", "yes"))
    lines.append(asp.fact("rinse", "no"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_cleaner", params.cleaner),
            asp.fact("chosen_residue", params.residue),
            asp.fact("chosen_rinse", params.rinse),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit() -> None:
    sample = generate(CURATED[0])
    emit(sample, trace=False, qa=False, header="")


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

    cases = list(CURATED)
    for idx in range(20):
        rng = random.Random(900 + idx)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp_value = asp_outcome(params)
        if py != asp_value:
            mismatches.append((params, py, asp_value))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcome model on {len(mismatches)} scenarios.")
        for params, py, asp_value in mismatches[:5]:
            print(f"  {params} python={py} asp={asp_value}")

    try:
        _smoke_emit()
        print("OK: smoke generation/emit passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fable about cleaning a food container the right way."
    )
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--residue", choices=RESIDUES)
    ap.add_argument("--cleaner", choices=CLEANERS)
    ap.add_argument("--rinse", choices=["yes", "no"])
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cleaner and args.residue:
        cleaner = CLEANERS[args.cleaner]
        residue = RESIDUES[args.residue]
        rinse = args.rinse if args.rinse is not None else "yes"
        if not (cleaner_works(cleaner, residue) and food_safe_plan(cleaner, rinse)):
            raise StoryError(explain_rejection(cleaner, residue, rinse))
    if args.cleaner and args.rinse:
        cleaner = CLEANERS[args.cleaner]
        if not food_safe_plan(cleaner, args.rinse):
            residue = RESIDUES[args.residue] if args.residue else next(iter(RESIDUES.values()))
            raise StoryError(explain_rejection(cleaner, residue, args.rinse))

    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.helper is None or combo[1] == args.helper)
        and (args.container is None or combo[2] == args.container)
        and (args.residue is None or combo[3] == args.residue)
        and (args.cleaner is None or combo[4] == args.cleaner)
        and (args.rinse is None or combo[5] == args.rinse)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, helper_id, container_id, residue_id, cleaner_id, rinse_choice = rng.choice(sorted(combos))
    food_id = args.food or rng.choice(FOOD_ORDER)
    hero_name = rng.choice(HERO_NAMES[hero_id])
    helper_name = rng.choice(HELPER_NAMES[helper_id])

    return StoryParams(
        hero=hero_id,
        helper=helper_id,
        container=container_id,
        residue=residue_id,
        cleaner=cleaner_id,
        rinse=rinse_choice,
        food=food_id,
        hero_name=hero_name,
        helper_name=helper_name,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        hero_spec = ANIMALS[params.hero]
        helper_spec = HELPERS[params.helper]
        container_cfg = CONTAINERS[params.container]
        residue_cfg = RESIDUES[params.residue]
        cleaner_cfg = CLEANERS[params.cleaner]
        food_cfg = FOODS[params.food]
    except KeyError as exc:
        raise StoryError(f"(Invalid option: {exc.args[0]})") from exc

    if not cleaner_works(cleaner_cfg, residue_cfg):
        raise StoryError(explain_rejection(cleaner_cfg, residue_cfg, params.rinse))
    if not food_safe_plan(cleaner_cfg, params.rinse):
        raise StoryError(explain_rejection(cleaner_cfg, residue_cfg, params.rinse))

    world = tell(
        hero_spec=hero_spec,
        helper_spec=helper_spec,
        container_cfg=container_cfg,
        residue_cfg=residue_cfg,
        cleaner_cfg=cleaner_cfg,
        food_cfg=food_cfg,
        hero_name=params.hero_name,
        helper_name=params.helper_name,
        rinse_choice=params.rinse,
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
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, helper, container, residue, cleaner, rinse) combos:\n")
        for hero, helper, container, residue, cleaner, rinse in combos:
            print(f"  {hero:7} {helper:9} {container:10} {residue:6} {cleaner:12} rinse={rinse}")
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
                f"### {p.hero_name} the {p.hero}: {p.cleaner} on {p.container} "
                f"after {p.residue} (rinse={p.rinse})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
