#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rotten_flyer_curiosity_lesson_learned_surprise_animal.py
===================================================================================

A standalone storyworld about a young woodland animal, a bright flyer, a tempting
rotten snack, a lesson learned, and a sweet surprise at the end.

Premise
-------
A little animal finds a flyer for a gathering with fresh treats. On the way there,
a rotten scrap of food on the path sparks curiosity and hunger. A grown-up warns
that old found food is not as safe as the fresh food promised on the flyer. In some
stories the child listens right away; in others the child takes a tiny bite, gets a
tummy ache, and learns the lesson the hard way. Either way, the ending image proves
what changed: the child chooses fresh shared food and wiser curiosity.

Run it
------
python storyworlds/worlds/gpt-5.4/rotten_flyer_curiosity_lesson_learned_surprise_animal.py
python storyworlds/worlds/gpt-5.4/rotten_flyer_curiosity_lesson_learned_surprise_animal.py --animal rabbit --food carrot --event garden_lunch
python storyworlds/worlds/gpt-5.4/rotten_flyer_curiosity_lesson_learned_surprise_animal.py --animal rabbit --food acorn
python storyworlds/worlds/gpt-5.4/rotten_flyer_curiosity_lesson_learned_surprise_animal.py --all
python storyworlds/worlds/gpt-5.4/rotten_flyer_curiosity_lesson_learned_surprise_animal.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/rotten_flyer_curiosity_lesson_learned_surprise_animal.py --verify
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
HUNGER_NIBBLE = 2
CAUTIOUS_TRAITS = {"careful", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "female"}
        male = {"boy", "father", "male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)

    def species_word(self) -> str:
        return str(self.attrs.get("species", "animal"))
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class AnimalSpec:
    id: str
    species: str
    home: str
    stride: str
    little_trait: str
    likes: set[str] = field(default_factory=set)
    names_female: list[str] = field(default_factory=list)
    names_male: list[str] = field(default_factory=list)
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
class Food:
    id: str
    tag: str
    rotten_label: str
    fresh_label: str
    smell: str
    place: str
    spoil: int
    warning: str
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
class Event:
    id: str
    title: str
    place: str
    served_tags: set[str] = field(default_factory=set)
    line: str = ""
    reveal: str = ""
    end_image: str = ""
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def _r_rotten_bite(world: World) -> list[str]:
    child = world.get("child")
    food = world.get("food")
    if food.meters["bitten"] < THRESHOLD:
        return []
    sig = ("rotten_bite", food.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if food.attrs.get("rotten"):
        child.meters["tummyache"] += float(food.attrs.get("spoil", 1))
        child.memes["regret"] += 1
        child.memes["fear"] += 1
        world.get("helper").memes["concern"] += 1
    return []


def _r_tempted(world: World) -> list[str]:
    child = world.get("child")
    food = world.get("food")
    if food.meters["smelled"] < THRESHOLD:
        return []
    sig = ("tempted", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if child.meters["hunger"] >= HUNGER_NIBBLE:
        child.memes["temptation"] += 1
        child.memes["curiosity"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="tempted", tag="emotional", apply=_r_tempted),
    Rule(name="rotten_bite", tag="physical", apply=_r_rotten_bite),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_compatible(animal: AnimalSpec, food: Food, event: Event) -> bool:
    return food.tag in animal.likes and food.tag in event.served_tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal_id, animal in ANIMALS.items():
        for food_id, food in FOODS.items():
            for event_id, event in EVENTS.items():
                if is_compatible(animal, food, event):
                    combos.append((animal_id, food_id, event_id))
    return sorted(combos)


def would_nibble(trait: str, hunger: int) -> bool:
    return hunger >= HUNGER_NIBBLE and trait not in CAUTIOUS_TRAITS


def predict_bite(world: World, hunger: int, trait: str) -> dict:
    sim = world.copy()
    child = sim.get("child")
    food = sim.get("food")
    child.meters["hunger"] = float(hunger)
    food.meters["smelled"] += 1
    propagate(sim, narrate=False)
    if would_nibble(trait, hunger):
        food.meters["bitten"] += 1
        propagate(sim, narrate=False)
    return {
        "tempted": child.memes["temptation"] >= THRESHOLD,
        "tummyache": child.meters["tummyache"],
    }


def introduce(world: World, child: Entity, animal: AnimalSpec) -> None:
    world.say(
        f"In the soft woods near {animal.home}, {child.id} the little {animal.species} "
        f"was known for {animal.little_trait}. {child.pronoun().capitalize()} liked to stop "
        f"for every rustle, sparkle, and fluttering leaf."
    )


def find_flyer(world: World, child: Entity, event: Event) -> None:
    child.memes["curiosity"] += 1
    flyer = world.get("flyer")
    world.say(
        f"One breezy morning, a bright flyer came skimming over the grass and tapped "
        f"{child.id} on the nose. {child.pronoun().capitalize()} caught it between small paws "
        f"and saw swirls of berries, leaves, and tiny stars around the words."
    )
    world.say(
        f'The flyer said, "{event.title} at {event.place}! {event.line}" '
        f"At the bottom was a painted arrow pointing down the ferny path."
    )
    flyer.meters["seen"] += 1


def ask_to_go(world: World, child: Entity, helper: Entity, animal: AnimalSpec, event: Event) -> None:
    child.meters["hunger"] = float(world.facts["hunger"])
    world.say(
        f'"May we go?" asked {child.id}. {helper.label_word.capitalize()} smiled and '
        f"{animal.stride} along beside {child.pronoun('object')}. They followed the path toward {event.place}."
    )


def smell_rotten(world: World, child: Entity, helper: Entity, food: Food) -> None:
    food_ent = world.get("food")
    food_ent.meters["smelled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Halfway there, a strong smell drifted from {food.place}. Under a curl of leaves lay "
        f"{food.rotten_label}. It was soft, brown at the edges, and much too old."
    )
    if child.memes["temptation"] >= THRESHOLD:
        world.say(
            f"{child.id} twitched a whisker and leaned closer. Curiosity tugged at "
            f"{child.pronoun('object')}, and so did a hungry tummy."
        )
    else:
        world.say(
            f"{child.id} wrinkled {child.pronoun('possessive')} nose. The smell was interesting, "
            f"but not lovely."
        )


def warn(world: World, child: Entity, helper: Entity, food: Food, event: Event, trait: str) -> None:
    pred = predict_bite(world, world.facts["hunger"], trait)
    world.facts["predicted_tummyache"] = pred["tummyache"]
    child.memes["caution"] += 1
    world.say(
        f'"Wait," said {helper.label_word} softly. "{food.warning} The flyer is leading us '
        f'to fresh food at {event.place}. Old food on the ground can hurt your tummy."'
    )


def heed(world: World, child: Entity, helper: Entity, food: Food) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.facts["outcome"] = "heeded"
    world.say(
        f"{child.id} stepped back from {food.rotten_label} and tucked the thought away. "
        f"{child.pronoun().capitalize()} decided that not every curious thing needed a nibble."
    )


def nibble(world: World, child: Entity, helper: Entity, food: Food) -> None:
    food_ent = world.get("food")
    food_ent.meters["bitten"] += 1
    propagate(world, narrate=False)
    world.facts["outcome"] = "tummyache"
    world.say(
        f"But {child.id}'s curiosity jumped faster than {child.pronoun('possessive')} good sense. "
        f"{child.pronoun().capitalize()} took one tiny bite of {food.rotten_label}."
    )
    if child.meters["tummyache"] >= THRESHOLD:
        world.say(
            f"Right away, {child.pronoun('possessive')} face fell. A sour little tummyache "
            f"curled inside {child.pronoun('object')}, and {child.pronoun()} wished {child.pronoun()} had listened."
        )


def comfort(world: World, child: Entity, helper: Entity) -> None:
    helper.meters["care_given"] += 1
    if child.meters["tummyache"] >= THRESHOLD:
        child.meters["tummyache"] = max(0.0, child.meters["tummyache"] - 1.0)
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{helper.label_word.capitalize()} led {child.id} to a cool log, gave {child.pronoun('object')} a sip of water, "
        f"and waited until the ache settled down."
    )


def lesson(world: World, child: Entity, helper: Entity, food: Food) -> None:
    if world.facts["outcome"] == "heeded":
        world.say(
            f'"You were wise to stop," said {helper.label_word}. "If food is old and rotten, '
            f'we leave it alone and look for something fresh."'
        )
    else:
        world.say(
            f'"Now you know," said {helper.label_word}, rubbing {child.id}\'s back. '
            f'"If food is old and rotten, we do not taste it. We ask first and wait for something fresh."'
        )


def reveal_surprise(world: World, child: Entity, helper: Entity, animal: AnimalSpec, food: Food, event: Event) -> None:
    child.memes["joy"] += 1
    world.say(
        f"When they finally reached {event.place}, the ferns parted and {event.reveal}"
    )
    world.say(
        f"On a low stump sat bowls of {food.fresh_label}, bright and clean beside cups of cool water. "
        f"The surprise on the flyer had been true all along."
    )
    if world.facts["outcome"] == "heeded":
        world.say(
            f"{child.id} laughed, chose the fresh food, and took the first careful bite only after "
            f"{helper.label_word} nodded."
        )
    else:
        world.say(
            f"{child.id} smiled a small, thankful smile and waited for {helper.label_word} to choose a safe piece. "
            f"This time {child.pronoun()} ate slowly, grateful for fresh food and a gentler tummy."
        )
    world.say(event.end_image)


def tell(
    animal: AnimalSpec,
    food: Food,
    event: Event,
    *,
    child_name: str = "Pip",
    child_type: str = "boy",
    helper_type: str = "mother",
    trait: str = "careful",
    hunger: int = 1,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            label=child_name,
            attrs={"species": animal.species, "trait": trait},
            tags=set(animal.tags),
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label=f"the {helper_type}",
            attrs={"species": animal.species},
            tags={"adult"},
        )
    )
    world.add(
        Entity(
            id="flyer",
            kind="thing",
            type="flyer",
            label="flyer",
            attrs={"event": event.id},
            tags={"flyer"},
        )
    )
    world.add(
        Entity(
            id="food",
            kind="thing",
            type="food",
            label=food.rotten_label,
            attrs={"rotten": True, "spoil": food.spoil, "tag": food.tag},
            tags=set(food.tags),
        )
    )
    world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=event.place,
            attrs={"event": event.id},
            tags=set(event.tags),
        )
    )

    world.facts.update(
        animal=animal,
        food_cfg=food,
        event=event,
        child=child,
        helper=helper,
        hunger=hunger,
        trait=trait,
        outcome="",
    )

    introduce(world, child, animal)
    find_flyer(world, child, event)
    ask_to_go(world, child, helper, animal, event)

    world.para()
    smell_rotten(world, child, helper, food)
    warn(world, child, helper, food, event, trait)

    if would_nibble(trait, hunger):
        nibble(world, child, helper, food)
        world.para()
        comfort(world, child, helper)
    else:
        heed(world, child, helper, food)

    world.para()
    lesson(world, child, helper, food)
    reveal_surprise(world, child, helper, animal, food, event)
    return world


@dataclass
class StoryParams:
    animal: str
    food: str
    event: str
    name: str
    gender: str
    helper: str
    trait: str
    hunger: int = 1
    seed: Optional[int] = None
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


ANIMALS = {
    "rabbit": AnimalSpec(
        id="rabbit",
        species="rabbit",
        home="the clover burrow",
        stride="hopped",
        little_trait="asking questions about everything",
        likes={"carrot", "apple", "berry", "lettuce"},
        names_female=["Clover", "Dot", "Poppy", "Mimi"],
        names_male=["Pip", "Tumble", "Nibbles", "Bramble"],
        tags={"rabbit", "forest_animal"},
    ),
    "squirrel": AnimalSpec(
        id="squirrel",
        species="squirrel",
        home="the big oak tree",
        stride="scampered",
        little_trait="peeking into every hollow and crack",
        likes={"acorn", "apple", "berry"},
        names_female=["Hazel", "Tansy", "Moss", "Pipkin"],
        names_male=["Rusty", "Twig", "Nutmeg", "Skip"],
        tags={"squirrel", "forest_animal"},
    ),
    "hedgehog": AnimalSpec(
        id="hedgehog",
        species="hedgehog",
        home="the fern nest",
        stride="padded",
        little_trait="sniffing at every odd little thing",
        likes={"apple", "berry", "mushroom"},
        names_female=["Bramble", "Fern", "Daisy", "Hush"],
        names_male=["Pebble", "Moss", "Tuck", "Pine"],
        tags={"hedgehog", "forest_animal"},
    ),
}

FOODS = {
    "apple": Food(
        id="apple",
        tag="apple",
        rotten_label="a rotten fallen apple",
        fresh_label="fresh apple slices",
        smell="sweet-sour",
        place="beside a stump",
        spoil=1,
        warning="That apple has been lying there too long",
        tags={"apple", "food"},
    ),
    "carrot": Food(
        id="carrot",
        tag="carrot",
        rotten_label="a rotten carrot top",
        fresh_label="crisp carrot sticks",
        smell="earthy and sharp",
        place="near a wheelbarrow",
        spoil=1,
        warning="That carrot is old and limp",
        tags={"carrot", "food"},
    ),
    "berry": Food(
        id="berry",
        tag="berry",
        rotten_label="a squashed cluster of rotten berries",
        fresh_label="a bowl of fresh berries",
        smell="jammy and sour",
        place="under a bramble patch",
        spoil=2,
        warning="Those berries are squashed and spoiled",
        tags={"berry", "food"},
    ),
    "acorn": Food(
        id="acorn",
        tag="acorn",
        rotten_label="a damp rotten acorn cake crumb",
        fresh_label="toasted acorn crumbs",
        smell="nutty but musty",
        place="by a mossy rock",
        spoil=1,
        warning="That acorn crumb is stale and moldy",
        tags={"acorn", "food"},
    ),
    "mushroom": Food(
        id="mushroom",
        tag="mushroom",
        rotten_label="a rotten mushroom cap",
        fresh_label="fresh mushroom slices",
        smell="mushroomy and stale",
        place="under a bent fern",
        spoil=2,
        warning="That mushroom has gone soft and bad",
        tags={"mushroom", "food"},
    ),
}

EVENTS = {
    "garden_lunch": Event(
        id="garden_lunch",
        title="Garden Lunch",
        place="the sunny garden patch",
        served_tags={"carrot", "apple", "lettuce", "berry"},
        line="Follow the green arrow for a surprise under the bean leaves.",
        reveal="little animal friends popped up from behind the bean poles with tiny napkins tied around their necks.",
        end_image="Soon the little group was munching together in the green shade, and the old path behind them looked much less tempting than it had before.",
        tags={"garden", "picnic"},
    ),
    "stump_picnic": Event(
        id="stump_picnic",
        title="Mossy Stump Picnic",
        place="the mossy stump clearing",
        served_tags={"apple", "berry", "acorn"},
        line="There will be songs, shared snacks, and one bright surprise.",
        reveal="a ring of woodland friends sprang from behind the stump and shouted, \"Surprise!\"",
        end_image="The clearing filled with happy chewing and soft woodland songs, while the bright flyer fluttered on a twig like a little flag.",
        tags={"picnic", "song"},
    ),
    "fern_tea": Event(
        id="fern_tea",
        title="Fern-Leaf Tea",
        place="the fern circle",
        served_tags={"apple", "berry", "mushroom"},
        line="Come gently down the path for a leafy surprise.",
        reveal="a tidy circle of friends waited with leaf cups and warm smiles.",
        end_image="By the end, even the breeze seemed gentler, and the lesson sat warmly in the middle of the little feast.",
        tags={"tea", "forest"},
    ),
}

TRAITS = ["careful", "patient", "thoughtful", "bold", "hasty", "impulsive"]


KNOWLEDGE = {
    "flyer": [
        (
            "What is a flyer?",
            "A flyer is a small paper notice that tells people about something, like a picnic or a party. It is meant to be read, not eaten."
        )
    ],
    "rotten": [
        (
            "What does rotten food mean?",
            "Rotten food is food that has gone old and bad. It can smell strange, feel soft or slimy, and it may make your tummy hurt."
        )
    ],
    "fresh_food": [
        (
            "Why is fresh food safer than old food found on the ground?",
            "Fresh food that a grown-up checks is safer because it has not been sitting out getting dirty or spoiled. Old food on the ground may have gone bad."
        )
    ],
    "rabbit": [
        (
            "What kind of animal is a rabbit?",
            "A rabbit is a small animal with long ears, strong back legs, and a twitchy nose. Rabbits hop and often like crunchy plants."
        )
    ],
    "squirrel": [
        (
            "What kind of animal is a squirrel?",
            "A squirrel is a small tree-climbing animal with a bushy tail. Squirrels like to scamper, gather food, and nibble nuts and seeds."
        )
    ],
    "hedgehog": [
        (
            "What kind of animal is a hedgehog?",
            "A hedgehog is a small animal with prickles on its back. Hedgehogs use their noses a lot and curl up when they need to feel safe."
        )
    ],
    "apple": [
        (
            "What is an apple?",
            "An apple is a round fruit that can be sweet and crunchy when it is fresh. If it gets old and mushy, it can start to rot."
        )
    ],
    "carrot": [
        (
            "What is a carrot?",
            "A carrot is a crunchy orange root vegetable that grows in the ground. Fresh carrots are firm, but old carrots can turn limp and bad."
        )
    ],
    "berry": [
        (
            "What are berries?",
            "Berries are small juicy fruits. Fresh berries can be sweet, but squashed old berries can spoil quickly."
        )
    ],
    "acorn": [
        (
            "What is an acorn?",
            "An acorn is the nut of an oak tree. Animals may eat safe acorn foods, but old damp scraps can still go bad."
        )
    ],
    "mushroom": [
        (
            "What is a mushroom?",
            "A mushroom is a soft fungus that grows in damp places. Some mushrooms are safe and some are not, so a child should always ask a grown-up first."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "flyer",
    "rotten",
    "fresh_food",
    "rabbit",
    "squirrel",
    "hedgehog",
    "apple",
    "carrot",
    "berry",
    "acorn",
    "mushroom",
]


CURATED = [
    StoryParams(
        animal="rabbit",
        food="carrot",
        event="garden_lunch",
        name="Pip",
        gender="boy",
        helper="mother",
        trait="careful",
        hunger=1,
    ),
    StoryParams(
        animal="squirrel",
        food="acorn",
        event="stump_picnic",
        name="Hazel",
        gender="girl",
        helper="father",
        trait="bold",
        hunger=2,
    ),
    StoryParams(
        animal="hedgehog",
        food="mushroom",
        event="fern_tea",
        name="Pebble",
        gender="boy",
        helper="mother",
        trait="patient",
        hunger=2,
    ),
    StoryParams(
        animal="rabbit",
        food="berry",
        event="garden_lunch",
        name="Clover",
        gender="girl",
        helper="father",
        trait="hasty",
        hunger=3,
    ),
    StoryParams(
        animal="squirrel",
        food="apple",
        event="stump_picnic",
        name="Rusty",
        gender="boy",
        helper="mother",
        trait="thoughtful",
        hunger=2,
    ),
]


def explain_rejection(animal: AnimalSpec, food: Food, event: Optional[Event] = None) -> str:
    if food.tag not in animal.likes:
        return (
            f"(No story: a {animal.species} here would not be plausibly tempted by "
            f"{food.rotten_label}. Pick a food this animal actually likes.)"
        )
    if event is not None and food.tag not in event.served_tags:
        return (
            f"(No story: {event.title} does not promise a fresh version of {food.tag}, "
            f"so the flyer would not honestly lead to the safer replacement the story needs.)"
        )
    return "(No story: this combination does not fit the world.)"


def _animal_names(spec: AnimalSpec, gender: str) -> list[str]:
    return spec.names_female if gender == "girl" else spec.names_male


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    animal = f["animal"]
    food = f["food_cfg"]
    event = f["event"]
    outcome = f["outcome"]
    if outcome == "tummyache":
        return [
            f'Write a gentle animal story for a 3-to-5-year-old that includes the words "rotten" and "flyer". A little {animal.species} follows a flyer, tastes something rotten, learns a lesson, and ends with a surprise.',
            f"Tell a woodland story where {child.id} the {animal.species} is curious about a flyer, ignores a warning about {food.rotten_label}, gets a small tummyache, and then finds a safe surprise at {event.place}.",
            f'Write a cozy cautionary animal tale that teaches children not to eat old found food, even if curiosity is strong, and end with fresh shared food and a happy surprise.'
        ]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old that includes the words "rotten" and "flyer". A little {animal.species} follows a flyer, makes a wise choice, learns a lesson, and ends with a surprise.',
        f"Tell a woodland story where {child.id} the {animal.species} finds a flyer, smells {food.rotten_label}, listens to a grown-up, and discovers a surprise gathering at {event.place}.",
        f'Write a small animal story about curiosity becoming wisdom, with a bright flyer, a rotten temptation, and a fresh safe ending.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    animal = f["animal"]
    food = f["food_cfg"]
    event = f["event"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {animal.species}, and {child.pronoun('possessive')} {helper.label_word} walking together through the woods. The story follows {child.id}'s curiosity from the bright flyer to the surprise at the end."
        ),
        (
            "What did the flyer say?",
            f"The flyer invited them to {event.title} at {event.place}. Its arrow is what made {child.id} want to follow the ferny path and find out more."
        ),
        (
            f"Why was {child.id} interested in {food.rotten_label}?",
            f"{child.id} was hungry and curious, so the smell made {child.pronoun('object')} lean closer. The old food sat right in the path before the surprise, which made it feel tempting."
        ),
        (
            f"What warning did {child.pronoun('possessive')} {helper.label_word} give?",
            f"{helper.label_word.capitalize()} said the food was rotten and could hurt {child.id}'s tummy. {helper.pronoun().capitalize()} reminded {child.pronoun('object')} that the flyer was leading them to fresh food instead."
        ),
    ]
    if f["outcome"] == "tummyache":
        qa.append(
            (
                f"What happened when {child.id} took a bite?",
                f"{child.id} got a small tummyache right away and wished {child.pronoun()} had listened. The bite caused trouble because the food was rotten and too old to eat safely."
            )
        )
        qa.append(
            (
                f"How did {helper.label_word} help?",
                f"{helper.label_word.capitalize()} gave {child.id} water and sat with {child.pronoun('object')} until the ache calmed down. The help mattered because it turned a bad choice into a lesson instead of a bigger scare."
            )
        )
    else:
        qa.append(
            (
                f"What wise choice did {child.id} make?",
                f"{child.id} stepped back and did not taste the rotten food. That choice kept the walk safe and showed that curiosity does not have to win over good sense."
            )
        )
    qa.append(
        (
            "What was the surprise at the end?",
            f"When they reached {event.place}, their friends were waiting with fresh food and smiles. The surprise proved that the flyer was pointing toward something kind and safe, not the old food on the path."
        )
    )
    qa.append(
        (
            "What lesson did the child learn?",
            f"{child.id} learned not to eat old food found on the ground just because it seems interesting. The better choice is to ask a grown-up and wait for fresh food that is safe to share."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"flyer", "rotten", "fresh_food", f["animal"].id, f["food_cfg"].tag}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
valid(A, F, E) :- animal(A), food(F), event(E), likes(A, T), food_tag(F, T), serves(E, T).

% --- outcome model ---------------------------------------------------------
cautious(T) :- trait(T), cautious_trait(T).
nibble :- hunger(H), nibble_threshold(M), H >= M, not cautious(chosen_trait).
outcome(heeded) :- not nibble.
outcome(tummyache) :- nibble.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for tag in sorted(animal.likes):
            lines.append(asp.fact("likes", animal_id, tag))
    for food_id, food in FOODS.items():
        lines.append(asp.fact("food", food_id))
        lines.append(asp.fact("food_tag", food_id, food.tag))
    for event_id, event in EVENTS.items():
        lines.append(asp.fact("event", event_id))
        for tag in sorted(event.served_tags):
            lines.append(asp.fact("serves", event_id, tag))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("nibble_threshold", HUNGER_NIBBLE))
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
            asp.fact("hunger", params.hunger),
            asp.fact("trait", params.trait),
            asp.fact("chosen_trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "tummyache" if would_nibble(params.trait, params.hunger) else "heeded"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: compatibility gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatibility gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(60):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params smoke seed {seed}.")
            break

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise AssertionError("empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bright flyer, a rotten temptation, a lesson, and a surprise."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--hunger", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.food:
        animal = ANIMALS[args.animal]
        food = FOODS[args.food]
        if food.tag not in animal.likes:
            raise StoryError(explain_rejection(animal, food))
    if args.animal and args.food and args.event:
        animal = ANIMALS[args.animal]
        food = FOODS[args.food]
        event = EVENTS[args.event]
        if not is_compatible(animal, food, event):
            raise StoryError(explain_rejection(animal, food, event))

    combos = [
        combo
        for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.food is None or combo[1] == args.food)
        and (args.event is None or combo[2] == args.event)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, food_id, event_id = rng.choice(combos)
    animal = ANIMALS[animal_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = [n for n in _animal_names(animal, gender)]
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    hunger = args.hunger if args.hunger is not None else rng.choice([1, 2, 3])

    return StoryParams(
        animal=animal_id,
        food=food_id,
        event=event_id,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
        hunger=hunger,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.helper not in {"mother", "father"}:
        raise StoryError(f"(Unknown helper type: {params.helper})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if params.hunger not in {1, 2, 3}:
        raise StoryError("(Hunger must be 1, 2, or 3.)")

    animal = ANIMALS[params.animal]
    food = FOODS[params.food]
    event = EVENTS[params.event]
    if not is_compatible(animal, food, event):
        raise StoryError(explain_rejection(animal, food, event))

    world = tell(
        animal,
        food,
        event,
        child_name=params.name,
        child_type=params.gender,
        helper_type=params.helper,
        trait=params.trait,
        hunger=params.hunger,
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
        print(f"{len(combos)} compatible (animal, food, event) combos:\n")
        for animal, food, event in combos:
            print(f"  {animal:10} {food:10} {event}")
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
            header = f"### {p.name}: {p.animal}, {p.food}, {p.event} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
