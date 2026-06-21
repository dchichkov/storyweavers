#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fuzz_textured_vanquish_lesson_learned_sharing_folk.py
=================================================================================

A standalone story world for a small folk-tale domain about a child on a forest
errand, a hungry traveler, and the lesson that sharing makes a hard road lighter.

The seed asked for the words "fuzz", "textured", and "vanquish", with the
features "Lesson Learned" and "Sharing", in a folk-tale style. This world turns
that into a compact simulation: a child carries food along a difficult path;
when the child shares with a hungry traveler, gratitude becomes help, and help
changes the journey. If the child clutches the food too tightly at first, the
path itself teaches the lesson before the child chooses to share.

Run it
------
    python storyworlds/worlds/gpt-5.4/fuzz_textured_vanquish_lesson_learned_sharing_folk.py
    python storyworlds/worlds/gpt-5.4/fuzz_textured_vanquish_lesson_learned_sharing_folk.py --food berries --container basket --path stones
    python storyworlds/worlds/gpt-5.4/fuzz_textured_vanquish_lesson_learned_sharing_folk.py --food soup --container bundle
    python storyworlds/worlds/gpt-5.4/fuzz_textured_vanquish_lesson_learned_sharing_folk.py --all
    python storyworlds/worlds/gpt-5.4/fuzz_textured_vanquish_lesson_learned_sharing_folk.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fuzz_textured_vanquish_lesson_learned_sharing_folk.py --verify
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
OPEN_HEARTED = {"kind", "gentle", "generous"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "widow", "daughter"}
        male = {"boy", "man", "woodcutter", "shepherd", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    portion: str
    plural: bool
    weight: int
    warmth: int
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
class Container:
    id: str
    label: str
    phrase: str
    holds: set[str] = field(default_factory=set)
    sturdy: int = 0
    carry_verb: str = "carried"
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
class Path:
    id: str
    label: str
    phrase: str
    textured: str
    difficulty: int
    crossing: str
    rescue: str
    ending: str
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
class Traveler:
    id: str
    type: str
    label: str
    phrase: str
    fuzz_detail: str
    request: str
    help_text: str
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


def _r_need(world: World) -> list[str]:
    hero = world.get("hero")
    traveler = world.get("traveler")
    food = world.get("food")
    if traveler.meters["hunger"] < THRESHOLD or food.meters["amount"] < THRESHOLD:
        return []
    sig = ("need",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    traveler.memes["need"] += 1
    return []


def _r_share_warms(world: World) -> list[str]:
    hero = world.get("hero")
    traveler = world.get("traveler")
    if traveler.meters["fed"] < THRESHOLD:
        return []
    sig = ("share_warms",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    traveler.meters["hunger"] = 0.0
    traveler.memes["gratitude"] += 1
    hero.memes["kindness"] += 1
    hero.memes["greed"] = 0.0
    return []


def _r_gratitude_help(world: World) -> list[str]:
    hero = world.get("hero")
    traveler = world.get("traveler")
    path = world.get("path")
    if traveler.memes["gratitude"] < THRESHOLD:
        return []
    sig = ("gratitude_help",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    traveler.memes["help"] += 1
    hero.meters["burden"] = max(0.0, hero.meters["burden"] - 1.0)
    path.meters["safety"] += 1
    return []


def _r_heavy_path(world: World) -> list[str]:
    hero = world.get("hero")
    traveler = world.get("traveler")
    path = world.get("path")
    if hero.meters["burden"] + path.meters["difficulty"] < 3:
        return []
    if traveler.memes["help"] >= THRESHOLD:
        return []
    sig = ("heavy_path",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    path.meters["risk"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="need", tag="social", apply=_r_need),
    Rule(name="share_warms", tag="social", apply=_r_share_warms),
    Rule(name="gratitude_help", tag="social", apply=_r_gratitude_help),
    Rule(name="heavy_path", tag="physical", apply=_r_heavy_path),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = changed or False
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combo(food: Food, container: Container, path: Path) -> bool:
    return food.id in container.holds and (container.sturdy + 2) >= (food.weight + path.difficulty)


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for food_id, food in FOODS.items():
        for container_id, container in CONTAINERS.items():
            for path_id, path in PATHS.items():
                if valid_combo(food, container, path):
                    out.append((food_id, container_id, path_id))
    return out


@dataclass
class StoryParams:
    food: str
    container: str
    path: str
    traveler: str
    hero: str
    gender: str
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


def outcome_of(params: StoryParams) -> str:
    return "shared_early" if params.trait in OPEN_HEARTED else "learned_after_wobble"


def explain_rejection(food: Food, container: Container, path: Path) -> str:
    if food.id not in container.holds:
        return (
            f"(No story: {container.phrase} does not sensibly carry {food.phrase}. "
            f"A sharing tale needs a believable way to bring the food along the road.)"
        )
    return (
        f"(No story: {container.phrase} is too awkward for {food.phrase} on {path.phrase}. "
        f"The burden would fail before the lesson could unfold, so choose a steadier match.)"
    )


def predict_crossing(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    traveler = sim.get("traveler")
    path = sim.get("path")
    return {
        "risk": path.meters["risk"],
        "help": traveler.memes["help"],
        "burden": hero.meters["burden"],
    }


def folk_opening(hero: Entity) -> str:
    return (
        f"In the old days, when paths still kept secrets and doors were opened by song, "
        f"there lived a little {hero.type} named {hero.id}."
    )


def introduce_errand(world: World, hero: Entity, food: Food, container: Container, path: Path) -> None:
    world.say(folk_opening(hero))
    world.say(
        f"One pale morning, {hero.id} {container.carry_verb} {container.phrase} holding "
        f"{food.phrase} toward the far cottage beyond {path.phrase}."
    )
    world.say(
        f"The road bent through pines and over {path.textured}, and the day was quiet enough "
        f"to hear even small thoughts grow loud."
    )


def meet_traveler(world: World, hero: Entity, traveler: Entity, traveler_cfg: Traveler, food: Food) -> None:
    traveler.meters["hunger"] = 1.0
    world.say(
        f"Near the middle of the wood, {hero.id} met {traveler_cfg.phrase}. "
        f"{traveler_cfg.fuzz_detail}"
    )
    world.say(
        f'"Child," {traveler.pronoun()} said, "{traveler_cfg.request} '
        f'Could you spare {food.portion} so I may vanquish the hunger in my belly?"'
    )
    propagate(world, narrate=False)


def clutch(world: World, hero: Entity, container: Container) -> None:
    hero.memes["greed"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} pulled {container.phrase} close and thought of the warm room ahead. "
        f"For a moment, keeping everything seemed easier than sharing anything."
    )


def share_early(world: World, hero: Entity, traveler: Entity, food: Food, container: Container) -> None:
    traveler.meters["fed"] += 1
    world.get("food").meters["amount"] = max(0.0, world.get("food").meters["amount"] - 1.0)
    propagate(world, narrate=False)
    world.say(
        f"But {hero.id}'s heart softened first. {hero.pronoun().capitalize()} opened {container.phrase} "
        f"and gave {traveler.pronoun('object')} {food.portion}."
    )
    world.say(
        f"The traveler ate slowly, as if the gift were a blessing as much as a meal, "
        f"and gratitude brightened {traveler.pronoun('possessive')} tired face."
    )


def attempt_alone(world: World, hero: Entity, path: Path, food: Food, container: Container) -> None:
    propagate(world, narrate=False)
    wobble = "wobble" if path.difficulty >= 2 else "dip"
    world.say(
        f"{hero.id} stepped onto {path.crossing}. At once the burden made {hero.pronoun('possessive')} arms {wobble}, "
        f"and the {food.label} felt heavier than before."
    )


def wobble_and_learn(world: World, hero: Entity, traveler: Entity, traveler_cfg: Traveler,
                     food: Food, container: Container, path: Path) -> None:
    food_ent = world.get("food")
    if path.difficulty >= 2:
        food_ent.meters["spilled"] += 1
        food_ent.meters["amount"] = max(1.0, food_ent.meters["amount"] - 1.0)
        world.say(
            f"A stone shifted under {hero.pronoun('possessive')} foot. The load tipped, and some of the "
            f"{food.label} nearly tumbled away into the moss."
        )
    else:
        world.say(
            f"The path gave a warning creak under {hero.pronoun('possessive')} steps, and {hero.id} stopped before worse could happen."
        )
    hero.memes["shame"] += 1
    world.say(
        f"Then {traveler_cfg.phrase} reached out and steadied the load instead of scolding. "
        f"{hero.id} felt small in the face of such kindness."
    )
    traveler.meters["fed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Please take {food.portion}," {hero.id} said. "A full basket and a closed hand make a poor companion."'
    )
    world.say(
        f"Only after sharing did the road seem less like an enemy. The gift changed two hungry hearts at once."
    )


def traveler_helps(world: World, traveler: Entity, traveler_cfg: Traveler, path: Path) -> None:
    if traveler.memes["help"] < THRESHOLD:
        return
    world.say(
        f"In return, {traveler_cfg.help_text} Together they crossed {path.ending} without another hard lurch."
    )


def arrival(world: World, hero: Entity, traveler: Entity, food: Food) -> None:
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    traveler.memes["belonging"] += 1
    world.say(
        f"By dusk they reached the cottage. The lamp in the window looked twice as warm because it was waiting for more than one soul."
    )
    world.say(
        f"There, the remaining {food.label} were set upon the table and shared again, and {hero.id} saw that a meal divided can still feel abundant."
    )


def moral(world: World, hero: Entity) -> None:
    world.say(
        f"From that day on, {hero.id} remembered what the old roads teach: what we share does not vanish. "
        f"It returns as help, company, and a lighter heart."
    )


def tell(food: Food, container: Container, path: Path, traveler_cfg: Traveler,
         hero_name: str, gender: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=gender,
        label=hero_name,
        role="hero",
        traits=[trait],
    ))
    traveler = world.add(Entity(
        id="Traveler",
        kind="character",
        type=traveler_cfg.type,
        label=traveler_cfg.label,
        role="traveler",
        traits=["weary"],
    ))
    path_ent = world.add(Entity(
        id="path",
        type="path",
        label=path.label,
        phrase=path.phrase,
    ))
    food_ent = world.add(Entity(
        id="food",
        type="food",
        label=food.label,
        phrase=food.phrase,
    ))
    container_ent = world.add(Entity(
        id="container",
        type="container",
        label=container.label,
        phrase=container.phrase,
    ))

    hero.meters["burden"] = float(food.weight)
    hero.memes["greed"] = 0.0
    hero.memes["kindness"] = 0.0
    hero.memes["lesson"] = 0.0
    traveler.meters["hunger"] = 0.0
    traveler.meters["fed"] = 0.0
    traveler.memes["gratitude"] = 0.0
    traveler.memes["help"] = 0.0
    path_ent.meters["difficulty"] = float(path.difficulty)
    path_ent.meters["risk"] = 0.0
    path_ent.meters["safety"] = 0.0
    food_ent.meters["amount"] = 3.0
    food_ent.meters["spilled"] = 0.0
    world.facts.update(
        food_cfg=food,
        container_cfg=container,
        path_cfg=path,
        traveler_cfg=traveler_cfg,
        hero=hero,
        traveler=traveler,
        food=food_ent,
        container=container_ent,
        path=path_ent,
        trait=trait,
        outcome="",
        shared=False,
        spilled=False,
    )

    introduce_errand(world, hero, food, container, path)
    world.para()
    meet_traveler(world, hero, traveler, traveler_cfg, food)

    if trait in OPEN_HEARTED:
        share_early(world, hero, traveler, food, container)
        world.facts["outcome"] = "shared_early"
        world.facts["shared"] = True
    else:
        clutch(world, hero, container)
        world.para()
        attempt_alone(world, hero, path, food, container)
        wobble_and_learn(world, hero, traveler, traveler_cfg, food, container, path)
        world.facts["outcome"] = "learned_after_wobble"
        world.facts["shared"] = True
        world.facts["spilled"] = food_ent.meters["spilled"] >= THRESHOLD

    world.para()
    traveler_helps(world, traveler, traveler_cfg, path)
    arrival(world, hero, traveler, food)
    moral(world, hero)
    return world


FOODS = {
    "berries": Food(
        id="berries",
        label="berries",
        phrase="a heap of red berries",
        portion="a palmful of berries",
        plural=True,
        weight=1,
        warmth=0,
        tags={"berries", "sharing"},
    ),
    "chestnuts": Food(
        id="chestnuts",
        label="chestnuts",
        phrase="a pile of roasted chestnuts",
        portion="a little handful of chestnuts",
        plural=True,
        weight=2,
        warmth=1,
        tags={"chestnuts", "sharing", "warm_food"},
    ),
    "cakes": Food(
        id="cakes",
        label="seed cakes",
        phrase="three round seed cakes",
        portion="one seed cake",
        plural=True,
        weight=2,
        warmth=1,
        tags={"cakes", "sharing", "warm_food"},
    ),
    "soup": Food(
        id="soup",
        label="soup",
        phrase="a pot of mushroom soup",
        portion="a warm cup of soup",
        plural=False,
        weight=2,
        warmth=2,
        tags={"soup", "sharing", "warm_food"},
    ),
}

CONTAINERS = {
    "basket": Container(
        id="basket",
        label="basket",
        phrase="a willow basket",
        holds={"berries", "chestnuts", "cakes"},
        sturdy=2,
        carry_verb="carried",
        tags={"basket"},
    ),
    "pot": Container(
        id="pot",
        label="clay pot",
        phrase="a clay pot wrapped in cloth",
        holds={"soup", "chestnuts"},
        sturdy=3,
        carry_verb="balanced",
        tags={"pot"},
    ),
    "bundle": Container(
        id="bundle",
        label="linen bundle",
        phrase="a linen bundle",
        holds={"cakes", "berries"},
        sturdy=1,
        carry_verb="carried",
        tags={"bundle"},
    ),
    "tray": Container(
        id="tray",
        label="wooden tray",
        phrase="a flat wooden tray",
        holds={"cakes"},
        sturdy=0,
        carry_verb="held",
        tags={"tray"},
    ),
}

PATHS = {
    "stones": Path(
        id="stones",
        label="river stones",
        phrase="the stream of stepping stones",
        textured="a line of textured stones glazed with damp",
        difficulty=2,
        crossing="the slick stepping stones",
        rescue="showed where the safe stones lay",
        ending="the old stream",
        tags={"path", "stones"},
    ),
    "bridge": Path(
        id="bridge",
        label="log bridge",
        phrase="the narrow log bridge",
        textured="a textured bridge of bark and old knots",
        difficulty=1,
        crossing="the log bridge",
        rescue="walked beside the child and steadied the basket with one hand",
        ending="the bridge above the reeds",
        tags={"path", "bridge"},
    ),
    "hill": Path(
        id="hill",
        label="hill path",
        phrase="the steep hill path",
        textured="a textured path of roots and packed leaves",
        difficulty=1,
        crossing="the rooty hill path",
        rescue="took the heavier side of the load and chose the gentler turns",
        ending="the winding hill path",
        tags={"path", "hill"},
    ),
}

TRAVELERS = {
    "widow": Traveler(
        id="widow",
        type="widow",
        label="widow",
        phrase="an old widow in a patched blue shawl",
        fuzz_detail="At the edge of her hood clung a ring of white sheep's-wool fuzz, damp with mist.",
        request="I have walked since sunrise and smelled your supper long before I saw your face.",
        help_text="the widow shared her sure village feet and showed where the safe stones lay.",
        tags={"widow", "sharing"},
    ),
    "woodcutter": Traveler(
        id="woodcutter",
        type="woodcutter",
        label="woodcutter",
        phrase="a thin woodcutter with an empty pack",
        fuzz_detail="A little brown fuzz from fresh bark clung to his sleeves, and his hands were red from the cold.",
        request="My work was long and my pouch is empty.",
        help_text="the woodcutter took the heavier side of the load and made the crossing seem half as hard.",
        tags={"woodcutter", "sharing"},
    ),
    "shepherd": Traveler(
        id="shepherd",
        type="shepherd",
        label="shepherd",
        phrase="a young shepherd wrapped in a rough cloak",
        fuzz_detail="Soft lamb's-wool fuzz peeped from the seam of the cloak and fluttered in the wind.",
        request="My sheep are home, but I have not yet had my own meal.",
        help_text="the shepherd laughed softly, lifted the burden with the child, and found the firmest ground.",
        tags={"shepherd", "sharing"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Tara", "Nessa", "Rina", "Bela", "Suri"]
BOY_NAMES = ["Tobin", "Marek", "Ivo", "Ren", "Pavel", "Luka", "Sorin", "Milo"]
TRAITS = ["kind", "gentle", "generous", "proud", "hasty", "stingy"]


KNOWLEDGE = {
    "sharing": [
        (
            "Why can sharing help two people at once?",
            "Sharing helps the person who receives food or comfort, and it also changes the sharer's heart. It can bring trust, friendship, and help in return."
        )
    ],
    "berries": [
        (
            "Why are berries easy to share?",
            "Berries come in many small pieces, so one handful can be given away while some still remain. That makes them simple to divide kindly."
        )
    ],
    "chestnuts": [
        (
            "Why do roasted chestnuts feel comforting on a cold day?",
            "Roasted chestnuts are warm in your hands and filling in your stomach. Warm food can make a tired traveler feel stronger."
        )
    ],
    "cakes": [
        (
            "Why is a cake easy to divide fairly?",
            "A cake can be split into clear pieces, so each person can have a share. That makes it a good food for a sharing story."
        )
    ],
    "soup": [
        (
            "Why must soup be carried in a sturdy container?",
            "Soup is liquid, so it sloshes and spills if the container is open or flimsy. A sturdy pot keeps the warm soup from being lost on the road."
        )
    ],
    "basket": [
        (
            "What is a willow basket good for?",
            "A willow basket is woven and airy, so it is good for carrying berries, cakes, or nuts. It holds many small things together while you walk."
        )
    ],
    "pot": [
        (
            "Why does a clay pot keep food safe?",
            "A clay pot has firm sides, so it can hold liquid or hot food without falling apart. It protects soup much better than cloth or a tray."
        )
    ],
    "path": [
        (
            "Why should you walk carefully on a narrow path?",
            "A narrow or slippery path gives less room for your feet and your load. Careful steps help keep both you and what you carry safe."
        )
    ],
}

KNOWLEDGE_ORDER = ["sharing", "berries", "chestnuts", "cakes", "soup", "basket", "pot", "path"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    food = f["food_cfg"]
    path = f["path_cfg"]
    traveler = f["traveler_cfg"]
    hero = f["hero"]
    outcome = f["outcome"]
    if outcome == "shared_early":
        return [
            f'Write a folk tale for a 3-to-5-year-old that includes the words "fuzz", "textured", and "vanquish", where a child shares {food.label} with {traveler.phrase}.',
            f"Tell a gentle old-fashioned forest story where {hero.id} is kind at once, and the gift turns a hard walk over {path.label} into a safe journey.",
            f"Write a lesson-learned story about how sharing a small meal can make the road lighter for everyone."
        ]
    return [
        f'Write a folk tale for a 3-to-5-year-old that includes the words "fuzz", "textured", and "vanquish", where a child first clutches some {food.label} and then learns to share.',
        f"Tell an old forest-path story where {hero.id} almost loses the meal on {path.label}, then learns that a closed hand makes a lonely road.",
        f"Write a lesson-learned story in which a hungry traveler and a difficult crossing teach a child why sharing matters."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    traveler = f["traveler"]
    food = f["food_cfg"]
    container = f["container_cfg"]
    path = f["path_cfg"]
    traveler_cfg = f["traveler_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child carrying {food.phrase}, and {traveler_cfg.phrase} met along the forest road. Their meeting changed the whole journey."
        ),
        (
            f"What was {hero.id} carrying?",
            f"{hero.id} was carrying {food.phrase} in {container.phrase}. The load mattered because it was the very thing the traveler asked to share."
        ),
        (
            "Why did the traveler ask for food?",
            f"The traveler was hungry and hoped for {food.portion}. The request was meant to vanquish hunger, not to take everything away."
        ),
    ]
    if outcome == "shared_early":
        qa.append((
            f"Why did the road grow easier after {hero.id} shared?",
            f"Once {hero.id} shared, the traveler felt grateful and chose to help. That meant the burden felt lighter and the crossing over {path.label} became safer."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{hero.id} learned that sharing does not leave you empty. It can return as help, warmth, and company on the road."
        ))
    else:
        spilled = "Some of the food almost spilled away" if f["spilled"] else "The path warned the child before a worse fall came"
        qa.append((
            f"What changed {hero.id}'s mind?",
            f"{spilled}. When the traveler steadied the load with kindness instead of anger, {hero.id} felt ashamed and then chose to share."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the meal being shared at the cottage and the road no longer feeling lonely. The child learned the lesson after a hard wobble, not before it."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sharing", "path"} | set(f["food_cfg"].tags) | set(f["container_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        food="berries",
        container="basket",
        path="stones",
        traveler="widow",
        hero="Mira",
        gender="girl",
        trait="kind",
    ),
    StoryParams(
        food="chestnuts",
        container="pot",
        path="bridge",
        traveler="woodcutter",
        hero="Tobin",
        gender="boy",
        trait="proud",
    ),
    StoryParams(
        food="cakes",
        container="bundle",
        path="hill",
        traveler="shepherd",
        hero="Anya",
        gender="girl",
        trait="gentle",
    ),
    StoryParams(
        food="soup",
        container="pot",
        path="bridge",
        traveler="widow",
        hero="Milo",
        gender="boy",
        trait="hasty",
    ),
    StoryParams(
        food="cakes",
        container="basket",
        path="stones",
        traveler="woodcutter",
        hero="Lina",
        gender="girl",
        trait="stingy",
    ),
]


ASP_RULES = r"""
valid(F,C,P) :- food(F), container(C), path(P), holds(C,F),
                sturdy(C,S), weight(F,W), difficulty(P,D),
                S + 2 >= W + D.

shared_early :- chosen_trait(T), open_hearted(T).
learned_after_wobble :- chosen_trait(T), not open_hearted(T).

outcome(shared_early) :- shared_early.
outcome(learned_after_wobble) :- learned_after_wobble.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        lines.append(asp.fact("weight", food_id, food.weight))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("sturdy", container_id, container.sturdy))
        for food_id in sorted(container.holds):
            lines.append(asp.fact("holds", container_id, food_id))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        lines.append(asp.fact("difficulty", path_id, path.difficulty))
    for trait in sorted(OPEN_HEARTED):
        lines.append(asp.fact("open_hearted", trait))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_trait", params.trait)
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

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
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folk-tale road, a hungry traveler, and a lesson in sharing."
    )
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--traveler", choices=TRAVELERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.container and args.path:
        if not valid_combo(FOODS[args.food], CONTAINERS[args.container], PATHS[args.path]):
            raise StoryError(explain_rejection(FOODS[args.food], CONTAINERS[args.container], PATHS[args.path]))

    combos = [
        combo for combo in valid_combos()
        if (args.food is None or combo[0] == args.food)
        and (args.container is None or combo[1] == args.container)
        and (args.path is None or combo[2] == args.path)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    food_id, container_id, path_id = rng.choice(sorted(combos))
    traveler_id = args.traveler or rng.choice(sorted(TRAVELERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        food=food_id,
        container=container_id,
        path=path_id,
        traveler=traveler_id,
        hero=hero,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.container not in CONTAINERS:
        raise StoryError(f"(Unknown container: {params.container})")
    if params.path not in PATHS:
        raise StoryError(f"(Unknown path: {params.path})")
    if params.traveler not in TRAVELERS:
        raise StoryError(f"(Unknown traveler: {params.traveler})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    food = FOODS[params.food]
    container = CONTAINERS[params.container]
    path = PATHS[params.path]
    if not valid_combo(food, container, path):
        raise StoryError(explain_rejection(food, container, path))

    world = tell(
        food=food,
        container=container,
        path=path,
        traveler_cfg=TRAVELERS[params.traveler],
        hero_name=params.hero,
        gender=params.gender,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (food, container, path) combos:\n")
        for food_id, container_id, path_id in combos:
            print(f"  {food_id:10} {container_id:10} {path_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero}: {p.food} in {p.container} over {p.path} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
