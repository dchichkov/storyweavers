#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/basis_happy_ending_sharing_animal_story.py
=====================================================================

A standalone story world for a gentle animal story about sharing. One young
animal brings a snack for an outing, another arrives hungry, and the first must
decide whether to hold the food close or share it. In this world, sharing is
not a moral pasted onto the end: it changes the simulated state. A shared snack
lowers hunger, restores energy, raises trust, and lets the friends enjoy the
outing together. In the happy resolution, the animals discover that sharing is
the basis of their best day.

The model prefers only combinations where there is honestly enough food to
share. Tiny or single-piece snacks are known to the world but refused as weak
stories: if there is not enough to help the hungry friend and still keep the
outing plausible, the problem has no satisfying resolution.

Run it
------
    python storyworlds/worlds/gpt-5.4/basis_happy_ending_sharing_animal_story.py
    python storyworlds/worlds/gpt-5.4/basis_happy_ending_sharing_animal_story.py --snack mushroom
    python storyworlds/worlds/gpt-5.4/basis_happy_ending_sharing_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/basis_happy_ending_sharing_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/basis_happy_ending_sharing_animal_story.py --trace
    python storyworlds/worlds/gpt-5.4/basis_happy_ending_sharing_animal_story.py --json
    python storyworlds/worlds/gpt-5.4/basis_happy_ending_sharing_animal_story.py --verify
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
        gender = self.attrs.get("gender", "")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    path: str
    goal: str
    discovery: str
    ending: str
    extra_portions: int = 2
    foraging_spot: bool = True
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
class Snack:
    id: str
    label: str
    phrase: str
    pieces: int
    plural: bool = True
    delicious: str = ""
    tags: set[str] = field(default_factory=set)

    def unit_word(self) -> str:
        return "pieces" if self.pieces != 1 else "piece"
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
class Need:
    id: str
    cause: str
    line: str
    share_need: int
    thanks: str
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
class Animal:
    name: str
    species: str
    gender: str
    traits: list[str] = field(default_factory=list)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_relieve_hunger(world: World) -> list[str]:
    receiver = world.get("receiver")
    if receiver.meters["hunger"] < THRESHOLD:
        return []
    if receiver.meters["received_food"] < receiver.attrs.get("need_portions", 0):
        return []
    sig = ("relieve_hunger", receiver.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    receiver.meters["hunger"] = 0.0
    receiver.meters["energy"] += 1.0
    receiver.memes["relief"] += 1.0
    return ["__relief__"]


def _r_bond(world: World) -> list[str]:
    giver = world.get("giver")
    receiver = world.get("receiver")
    if giver.meters["shared_food"] < THRESHOLD or receiver.memes["relief"] < THRESHOLD:
        return []
    sig = ("bond", giver.id, receiver.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    giver.memes["generosity"] += 1.0
    giver.memes["joy"] += 1.0
    receiver.memes["gratitude"] += 1.0
    receiver.memes["trust"] += 1.0
    giver.memes["trust"] += 1.0
    giver.memes["friendship"] += 1.0
    receiver.memes["friendship"] += 1.0
    return ["__bond__"]


def _r_discovery(world: World) -> list[str]:
    giver = world.get("giver")
    receiver = world.get("receiver")
    basket = world.get("basket")
    if receiver.meters["energy"] < THRESHOLD:
        return []
    if giver.memes["friendship"] < THRESHOLD or receiver.memes["friendship"] < THRESHOLD:
        return []
    if not world.setting.foraging_spot:
        return []
    sig = ("discovery", world.setting.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    basket.meters["portions"] += float(world.setting.extra_portions)
    world.facts["found_extra"] = True
    receiver.memes["joy"] += 1.0
    giver.memes["surprise"] += 1.0
    return ["__discovery__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="relieve_hunger", tag="physical", apply=_r_relieve_hunger),
    Rule(name="bond", tag="social", apply=_r_bond),
    Rule(name="discovery", tag="physical", apply=_r_discovery),
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
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def enough_to_share(snack: Snack, need: Need) -> bool:
    return snack.pieces >= (need.share_need + 1)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        if not setting.foraging_spot:
            continue
        for snack_id, snack in SNACKS.items():
            for need_id, need in NEEDS.items():
                if enough_to_share(snack, need):
                    combos.append((setting_id, snack_id, need_id))
    return combos


def explain_rejection(snack: Snack, need: Need) -> str:
    return (
        f"(No story: {snack.phrase} gives only {snack.pieces} {snack.unit_word()}, "
        f"but the hungry friend needs at least {need.share_need} to feel better, "
        f"and the giver still needs a little food too. Pick a snack with enough "
        f"pieces to share honestly.)"
    )


def predict_share(world: World, need: Need) -> dict:
    sim = world.copy()
    basket = sim.get("basket")
    receiver = sim.get("receiver")
    giver = sim.get("giver")
    basket.meters["portions"] -= float(need.share_need)
    receiver.meters["received_food"] += float(need.share_need)
    giver.meters["shared_food"] += float(need.share_need)
    propagate(sim, narrate=False)
    return {
        "relieved": receiver.meters["hunger"] < THRESHOLD,
        "energy": receiver.meters["energy"],
        "friendship": giver.memes["friendship"] + receiver.memes["friendship"],
        "extra": bool(sim.facts.get("found_extra")),
        "remaining": basket.meters["portions"],
    }


def introduce(world: World, giver: Entity, receiver: Entity, snack: Snack) -> None:
    world.say(
        f"In {world.setting.place}, {giver.id} the young {giver.type} trotted along "
        f"{world.setting.path} with {snack.phrase} tucked in a little leaf basket."
    )
    world.say(
        f"Beside {giver.pronoun('object')} walked {receiver.id} the {receiver.type}, "
        f"on the way to {world.setting.goal}."
    )
    if snack.delicious:
        world.say(f"The basket smelled {snack.delicious}, and the morning felt full of promise.")


def show_bond(world: World, giver: Entity, receiver: Entity) -> None:
    world.say(
        f"{giver.id} and {receiver.id} were good friends who liked to do small forest "
        f"things together and make big games out of them."
    )


def problem(world: World, receiver: Entity, need: Need) -> None:
    receiver.meters["hunger"] = 1.0
    receiver.memes["worry"] = 1.0
    world.say(need.cause)
    world.say(
        f"Soon {receiver.id}'s tummy gave a small, sad rumble. {need.line}"
    )


def hesitate(world: World, giver: Entity, snack: Snack, need: Need) -> None:
    giver.memes["possessive"] = 1.0
    basket = world.get("basket")
    world.say(
        f"{giver.id} peeked into the basket and counted {int(basket.meters['portions'])} "
        f"{snack.unit_word()}. For one moment, {giver.pronoun()} hugged the basket close."
    )
    pred = predict_share(world, need)
    world.facts["predicted_share"] = pred
    if pred["relieved"]:
        world.say(
            f"Then {giver.pronoun()} thought about what would happen if {giver.pronoun()} shared: "
            f"{receiver.id} would not feel so hollow, and the walk would be easier for both of them."
        )


def share(world: World, giver: Entity, receiver: Entity, snack: Snack, need: Need) -> None:
    basket = world.get("basket")
    basket.meters["portions"] -= float(need.share_need)
    giver.meters["shared_food"] += float(need.share_need)
    receiver.meters["received_food"] += float(need.share_need)
    giver.memes["possessive"] = 0.0
    giver.memes["kindness"] += 1.0
    propagate(world, narrate=False)
    piece_word = "piece" if need.share_need == 1 else "pieces"
    world.say(
        f'"Here," {giver.id} said at last. "{receiver.id}, you can have '
        f'{need.share_need} {piece_word} of my {snack.label}."'
    )
    world.say(
        f"{giver.pronoun().capitalize()} tipped the basket between them so the sharing looked easy "
        f"and fair."
    )
    if receiver.meters["hunger"] < THRESHOLD:
        world.say(
            f"{receiver.id} ate slowly at first, and then with a bright little smile as the hungry ache went away."
        )
    if receiver.memes["gratitude"] >= THRESHOLD:
        world.say(need.thanks)


def discovery(world: World, giver: Entity, receiver: Entity, snack: Snack) -> None:
    basket = world.get("basket")
    if not world.facts.get("found_extra"):
        return
    world.say(
        world.setting.discovery.format(
            giver=giver.id,
            receiver=receiver.id,
            snack=snack.label,
        )
    )
    world.say(
        f"They added the new find to the basket, and suddenly there was more than enough for two small friends."
    )
    world.say(
        f"{giver.id} laughed then, because sharing had not made the day smaller at all."
    )
    world.facts["basket_after_discovery"] = int(basket.meters["portions"])


def ending(world: World, giver: Entity, receiver: Entity) -> None:
    basis_line = (
        f"By the time they reached {world.setting.ending}, the two friends knew that "
        f"sharing was the basis of their happiest forest days."
    )
    world.say(
        f"Together they {world.setting.ending}, shoulder to shoulder and crumb to crumb."
    )
    world.say(basis_line)


def tell(setting: Setting, snack: Snack, need: Need, giver_cfg: Animal, receiver_cfg: Animal) -> World:
    world = World(setting)

    giver = world.add(Entity(
        id=giver_cfg.name,
        kind="character",
        type=giver_cfg.species,
        label=giver_cfg.species,
        attrs={"gender": giver_cfg.gender, "traits": list(giver_cfg.traits)},
        tags={giver_cfg.species},
    ))
    receiver = world.add(Entity(
        id=receiver_cfg.name,
        kind="character",
        type=receiver_cfg.species,
        label=receiver_cfg.species,
        attrs={"gender": receiver_cfg.gender, "traits": list(receiver_cfg.traits), "need_portions": need.share_need},
        tags={receiver_cfg.species},
    ))
    basket = world.add(Entity(
        id="basket",
        kind="thing",
        type="basket",
        label="leaf basket",
        attrs={"owner": giver.id, "snack": snack.id},
        tags=set(snack.tags),
    ))
    basket.meters["portions"] = float(snack.pieces)
    giver.meters["shared_food"] = 0.0
    receiver.meters["received_food"] = 0.0
    receiver.meters["hunger"] = 0.0
    receiver.meters["energy"] = 0.0
    giver.memes["friendship"] = 0.0
    receiver.memes["friendship"] = 0.0
    giver.memes["trust"] = 0.0
    receiver.memes["trust"] = 0.0
    giver.memes["gratitude"] = 0.0
    receiver.memes["gratitude"] = 0.0
    world.facts["found_extra"] = False

    introduce(world, giver, receiver, snack)
    show_bond(world, giver, receiver)

    world.para()
    problem(world, receiver, need)
    hesitate(world, giver, snack, need)

    world.para()
    share(world, giver, receiver, snack, need)
    discovery(world, giver, receiver, snack)

    world.para()
    ending(world, giver, receiver)

    world.facts.update(
        setting=setting,
        snack=snack,
        need=need,
        giver=giver,
        receiver=receiver,
        basket=basket,
        shared_portions=int(giver.meters["shared_food"]),
        hunger_relieved=receiver.meters["hunger"] < THRESHOLD,
        friendship=giver.memes["friendship"] + receiver.memes["friendship"],
        basket_remaining=int(basket.meters["portions"]),
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="a sunny meadow near the forest edge",
        path="through the buttercups",
        goal="a flat stone where they liked to watch butterflies",
        discovery="{receiver} lifted one paw and pointed under the tall grass, where a patch of wild clover cakes had fallen from a picnic cart long ago and dried sweet in the sun.",
        ending="sat on the flat stone and shared their lunch while butterflies dipped above them",
        extra_portions=2,
        foraging_spot=True,
        tags={"meadow", "sharing"},
    ),
    "pond": Setting(
        id="pond",
        place="the pond path under the willow trees",
        path="along the soft mud beside the water",
        goal="the smooth bank where they floated leaf boats",
        discovery="{receiver} spotted a blackberry bramble leaning over the water, heavy with ripe fruit no one had seen from the path.",
        ending="floated leaf boats and ate beside the shining water",
        extra_portions=3,
        foraging_spot=True,
        tags={"pond", "sharing"},
    ),
    "pine_grove": Setting(
        id="pine_grove",
        place="a cool pine grove beyond the hill",
        path="between roots that smelled of warm sap",
        goal="their secret mossy stump in the shade",
        discovery="{receiver} noticed that the wind had shaken down a fresh scatter of little nuts near the stump, hidden under a fan of pine needles.",
        ending="curled up on the mossy stump and nibbled together in the green shade",
        extra_portions=2,
        foraging_spot=True,
        tags={"grove", "sharing"},
    ),
}

SNACKS = {
    "berries": Snack(
        id="berries",
        label="berries",
        phrase="a basket of red berries",
        pieces=6,
        plural=True,
        delicious="sweet and sunny",
        tags={"berries", "food"},
    ),
    "acorns": Snack(
        id="acorns",
        label="acorns",
        phrase="a little bundle of acorns",
        pieces=5,
        plural=True,
        delicious="nutty and warm",
        tags={"acorns", "food"},
    ),
    "seed_cakes": Snack(
        id="seed_cakes",
        label="seed cakes",
        phrase="four crumbly seed cakes",
        pieces=4,
        plural=True,
        delicious="toasty and rich",
        tags={"seeds", "food"},
    ),
    "mushroom": Snack(
        id="mushroom",
        label="mushroom",
        phrase="one round mushroom cap",
        pieces=1,
        plural=False,
        delicious="earthy and soft",
        tags={"mushroom", "food"},
    ),
}

NEEDS = {
    "missed_breakfast": Need(
        id="missed_breakfast",
        cause="That morning, the little friend had hurried out so quickly to meet the sunrise that breakfast had been forgotten at home.",
        line='"I thought I could wait until later," the small friend admitted, "but later feels far away now."',
        share_need=2,
        thanks='"Thank you," the hungry friend said. "Now my paws feel steady again, and my heart does too."',
        tags={"hunger", "sharing"},
    ),
    "gave_it_away": Need(
        id="gave_it_away",
        cause="Before the walk, the little friend had given breakfast to a younger sibling who had dropped theirs in the dirt.",
        line='"I was glad to help," the small friend said, "but now my tummy is making the loudest sound in the wood."',
        share_need=2,
        thanks='"That was kind," the hungry friend said. "You shared with me after I had shared with someone else."',
        tags={"hunger", "kindness"},
    ),
    "long_walk": Need(
        id="long_walk",
        cause="The little friend had come from the far side of the wood and had used up all the crumbs packed for the walk.",
        line='"I did not know the path would feel so long," the small friend whispered, pressing a paw to a rumbling belly.',
        share_need=3,
        thanks='"Oh, that helps so much," the hungry friend said. "I can think about the day again instead of only my tummy."',
        tags={"hunger", "sharing"},
    ),
}

ANIMALS = {
    "hazel": Animal(name="Hazel", species="squirrel", gender="girl", traits=["quick", "bright"]),
    "pip": Animal(name="Pip", species="rabbit", gender="boy", traits=["gentle", "springy"]),
    "moss": Animal(name="Moss", species="mouse", gender="boy", traits=["small", "careful"]),
    "fern": Animal(name="Fern", species="fox", gender="girl", traits=["soft-footed", "curious"]),
    "reed": Animal(name="Reed", species="otter", gender="boy", traits=["playful", "smooth"]),
    "pearl": Animal(name="Pearl", species="hedgehog", gender="girl", traits=["quiet", "kind"]),
}


@dataclass
class StoryParams:
    setting: str
    snack: str
    need: str
    giver: str
    receiver: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    giver = f["giver"]
    receiver = f["receiver"]
    snack = f["snack"]
    setting = f["setting"]
    return [
        f'Write a short animal story for a 3-to-5-year-old that includes the word "basis" and ends happily after one friend shares food with another.',
        f"Tell a gentle forest story where {giver.id} the {giver.type} shares {snack.label} with {receiver.id} the {receiver.type} on the way to {setting.goal}.",
        f"Write an animal story about hunger, kindness, and sharing, where the friends learn that sharing can be the basis of a happy day together.",
    ]


KNOWLEDGE = {
    "sharing": [
        (
            "Why can sharing food help a friendship?",
            "Sharing shows that you notice what someone else needs. When a friend feels cared for, trust can grow."
        )
    ],
    "hunger": [
        (
            "Why is it hard to play when you are hungry?",
            "A hungry body can feel weak and distracted. Food gives you energy so you can think, walk, and play more comfortably."
        )
    ],
    "berries": [
        (
            "Where do berries grow?",
            "Many berries grow on bushes and brambles. Small animals often find them in sunny places around the woods."
        )
    ],
    "acorns": [
        (
            "What are acorns?",
            "Acorns are nuts that grow on oak trees. Squirrels and other animals like to gather them for food."
        )
    ],
    "seeds": [
        (
            "What is a seed cake?",
            "A seed cake is a little pressed snack made from seeds. It breaks into small pieces that can be shared."
        )
    ],
    "mushroom": [
        (
            "What is a mushroom?",
            "A mushroom is a soft forest fungus that grows from the ground or rotting wood. Some animals sniff them out while exploring."
        )
    ],
    "food": [
        (
            "Why do animals look for food during a walk?",
            "Food helps an animal's body keep moving and stay warm. A snack can make a long walk feel easier."
        )
    ],
}


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    giver = f["giver"]
    receiver = f["receiver"]
    snack = f["snack"]
    need = f["need"]
    setting = f["setting"]
    basket_remaining = f["basket_remaining"]
    shared = f["shared_portions"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {giver.id} the {giver.type} and {receiver.id} the {receiver.type}. They were walking together to {setting.goal}."
        ),
        (
            f"Why was {receiver.id} hungry?",
            f"{need.cause} That is why {receiver.id}'s tummy began to rumble on the path."
        ),
        (
            f"Why did {giver.id} hesitate before sharing?",
            f"{giver.id} counted the food in the basket and worried about having too little later. The hesitation came from wanting the snack and also wanting to help a friend."
        ),
        (
            f"What happened after {giver.id} shared the {snack.label}?",
            f"{receiver.id}'s hunger eased, so the walk felt lighter again. Because the sharing helped right away, the two friends felt closer and enjoyed the outing together."
        ),
    ]
    if world.facts.get("found_extra"):
        qa.append(
            (
                "Did sharing make the basket empty?",
                f"No. After the friends shared, they found extra food on the way. The basket ended with {basket_remaining} pieces, which showed that kindness did not ruin the day."
            )
        )
    qa.append(
        (
            "What does the word basis mean in this story?",
            "Here, basis means the starting support underneath something good. The story says sharing was the basis of their happy day because kindness helped everything else go well after that."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily with the friends together at {setting.goal}. They shared {shared} pieces of {snack.label} first, and that choice led to a peaceful meal and playtime side by side."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sharing", "food"} | set(world.facts["need"].tags) | set(world.facts["snack"].tags)
    out: list[tuple[str, str]] = []
    order = ["sharing", "hunger", "berries", "acorns", "seeds", "mushroom", "food"]
    for tag in order:
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="meadow",
        snack="berries",
        need="missed_breakfast",
        giver="hazel",
        receiver="pip",
    ),
    StoryParams(
        setting="pond",
        snack="seed_cakes",
        need="gave_it_away",
        giver="reed",
        receiver="pearl",
    ),
    StoryParams(
        setting="pine_grove",
        snack="acorns",
        need="long_walk",
        giver="hazel",
        receiver="moss",
    ),
    StoryParams(
        setting="meadow",
        snack="seed_cakes",
        need="gave_it_away",
        giver="fern",
        receiver="pip",
    ),
]


ASP_RULES = r"""
good_snack(S, N) :- snack(S), need(N), snack_pieces(S, P), share_need(N, Req), P >= Req + 1.
valid(St, S, N)  :- setting(St), foraging_spot(St), good_snack(S, N).
happy(St, S, N)  :- valid(St, S, N).

#show valid/3.
#show happy/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.foraging_spot:
            lines.append(asp.fact("foraging_spot", setting_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("snack_pieces", snack_id, snack.pieces))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        lines.append(asp.fact("share_need", need_id, need.share_need))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        parser = build_parser()
        default_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_cases.append(default_params)
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"FAIL: resolve_params() crashed during smoke test: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"FAIL: generation smoke test crashed for {params}: {err}")
            break

    if rc == 0:
        print(f"OK: generation smoke test passed on {len(smoke_cases)} scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: one friend shares a snack, and kindness becomes the basis of a happy ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--giver", choices=ANIMALS)
    ap.add_argument("--receiver", choices=ANIMALS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from the ASP gate")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.giver and args.receiver and args.giver == args.receiver:
        raise StoryError("(No story: the giver and receiver should be different animals.)")
    if args.snack and args.need:
        snack = SNACKS[args.snack]
        need = NEEDS[args.need]
        if not enough_to_share(snack, need):
            raise StoryError(explain_rejection(snack, need))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.snack is None or combo[1] == args.snack)
        and (args.need is None or combo[2] == args.need)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, snack_id, need_id = rng.choice(sorted(combos))

    giver_id = args.giver or rng.choice(sorted(ANIMALS))
    receiver_pool = [aid for aid in sorted(ANIMALS) if aid != giver_id]
    receiver_id = args.receiver or rng.choice(receiver_pool)
    if receiver_id == giver_id:
        raise StoryError("(No story: the giver and receiver should be different animals.)")

    return StoryParams(
        setting=setting_id,
        snack=snack_id,
        need=need_id,
        giver=giver_id,
        receiver=receiver_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.giver not in ANIMALS or params.receiver not in ANIMALS:
        raise StoryError("(Unknown animal choice.)")
    if params.giver == params.receiver:
        raise StoryError("(No story: the giver and receiver should be different animals.)")
    snack = SNACKS[params.snack]
    need = NEEDS[params.need]
    if not enough_to_share(snack, need):
        raise StoryError(explain_rejection(snack, need))

    world = tell(
        setting=SETTINGS[params.setting],
        snack=snack,
        need=need,
        giver_cfg=ANIMALS[params.giver],
        receiver_cfg=ANIMALS[params.receiver],
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
        print(f"{len(combos)} compatible (setting, snack, need) combos:\n")
        for setting_id, snack_id, need_id in combos:
            print(f"  {setting_id:10} {snack_id:10} {need_id}")
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
            header = f"### {p.giver} shares {p.snack} with {p.receiver} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
