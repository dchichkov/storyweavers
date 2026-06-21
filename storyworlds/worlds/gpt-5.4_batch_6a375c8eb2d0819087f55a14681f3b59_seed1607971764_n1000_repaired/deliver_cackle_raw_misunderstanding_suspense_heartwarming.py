#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/deliver_cackle_raw_misunderstanding_suspense_heartwarming.py
=======================================================================================

A standalone story world about a child trying to deliver a warm treat next door,
misreading a sudden cackle as a mean laugh, and learning that the noisy animal
was actually warning about a missing basket.

The domain is deliberately small and constraint-checked:

- a parent and child prepare something kind to deliver
- a second bowl of raw ingredients sits in the kitchen, coloring the scene
- the basket is moved by a small cause (puppy, kitten, or breeze)
- a hen or goose gives a loud cackle near the hiding place
- the child misunderstands the cackle as mockery or trouble
- suspense grows while they search
- they discover the animal was pointing them toward the basket
- the gift is still delivered, and the ending image proves the child now hears
  the cackle differently

Run it
------
    python storyworlds/worlds/gpt-5.4/deliver_cackle_raw_misunderstanding_suspense_heartwarming.py
    python storyworlds/worlds/gpt-5.4/deliver_cackle_raw_misunderstanding_suspense_heartwarming.py --delivery pie --mover puppy --spot hedge --animal hen
    python storyworlds/worlds/gpt-5.4/deliver_cackle_raw_misunderstanding_suspense_heartwarming.py --delivery pie --mover breeze
    python storyworlds/worlds/gpt-5.4/deliver_cackle_raw_misunderstanding_suspense_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/deliver_cackle_raw_misunderstanding_suspense_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/deliver_cackle_raw_misunderstanding_suspense_heartwarming.py --verify
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
    kind: str = "thing"            # character | animal | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
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
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parameter registries
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
class Delivery:
    id: str
    phrase: str
    short: str
    container: str
    warmth: str
    pull: int
    ingredient_phrase: str
    raw_phrase: str
    trace_mark: str
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
class Mover:
    id: str
    label: str
    strength: int
    clue: int
    spots: set[str]
    move_text: str
    clue_text: str
    reveal_text: str
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
class Spot:
    id: str
    label: str
    difficulty: int
    shelter_text: str
    discovery_text: str
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
class AlarmAnimal:
    id: str
    label: str
    alert: int
    spots: set[str]
    cackle_text: str
    reveal_text: str
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


DELIVERIES = {
    "rolls": Delivery(
        id="rolls",
        phrase="a basket of honey rolls",
        short="the rolls",
        container="basket",
        warmth="still warm under a checked cloth",
        pull=1,
        ingredient_phrase="a bowl of dough waiting for the second batch",
        raw_phrase="raw dough",
        trace_mark="soft crumbs",
        tags={"deliver", "bread", "raw_dough"},
    ),
    "pie": Delivery(
        id="pie",
        phrase="a blueberry pie in a shallow basket",
        short="the pie",
        container="basket",
        warmth="cooling under a blue cloth",
        pull=2,
        ingredient_phrase="a colander of berries waiting by the sink",
        raw_phrase="raw berries",
        trace_mark="a tiny blue smear",
        tags={"deliver", "pie", "berries"},
    ),
    "soup": Delivery(
        id="soup",
        phrase="a jar of carrot soup wrapped in a towel",
        short="the soup",
        container="basket",
        warmth="sending up a gentle smell of parsley",
        pull=1,
        ingredient_phrase="a neat pile of chopped carrots for tomorrow's pot",
        raw_phrase="raw carrots",
        trace_mark="a pale orange drip",
        tags={"deliver", "soup", "carrots"},
    ),
}

MOVERS = {
    "puppy": Mover(
        id="puppy",
        label="the puppy",
        strength=2,
        clue=2,
        spots={"bench", "hedge", "wagon"},
        move_text="the puppy caught the edge of the cloth and tugged the basket away in a bouncy hurry",
        clue_text="small paw prints dotted the path",
        reveal_text="the puppy was curled beside it, looking pleased with the game",
        tags={"puppy", "pet"},
    ),
    "kitten": Mover(
        id="kitten",
        label="the kitten",
        strength=1,
        clue=1,
        spots={"bench"},
        move_text="the kitten worried a dangling ribbon until the basket slid away a little at a time",
        clue_text="a loose ribbon thread trailed across the stones",
        reveal_text="the kitten sat nearby, blinking at the ribbon as if it had been the finest toy in the world",
        tags={"kitten", "pet"},
    ),
    "breeze": Mover(
        id="breeze",
        label="the breeze",
        strength=1,
        clue=1,
        spots={"hedge"},
        move_text="a playful breeze lifted the cloth and worried the basket along the path",
        clue_text="the cloth corner kept fluttering toward the bushes",
        reveal_text="the cloth was caught in the leaves, and the basket had simply nudged in after it",
        tags={"wind", "weather"},
    ),
}

SPOTS = {
    "bench": Spot(
        id="bench",
        label="the garden bench",
        difficulty=1,
        shelter_text="a shady corner beside the bench",
        discovery_text="tucked under the garden bench where the light turned soft and green",
        tags={"bench"},
    ),
    "hedge": Spot(
        id="hedge",
        label="the lilac hedge",
        difficulty=2,
        shelter_text="the darker side of the lilac hedge",
        discovery_text="nestled behind the lilac hedge among cool leaves",
        tags={"hedge", "bush"},
    ),
    "wagon": Spot(
        id="wagon",
        label="the red wagon",
        difficulty=2,
        shelter_text="the quiet space behind the red wagon",
        discovery_text="resting behind the red wagon by the shed wall",
        tags={"wagon"},
    ),
}

ANIMALS = {
    "hen": AlarmAnimal(
        id="hen",
        label="the hen",
        alert=1,
        spots={"bench", "hedge"},
        cackle_text="A hen burst into a sharp cackle nearby.",
        reveal_text="The hen had only been fussing at the commotion, neck stretched high as if trying to show them where to look.",
        tags={"hen", "cackle"},
    ),
    "goose": AlarmAnimal(
        id="goose",
        label="the goose",
        alert=2,
        spots={"bench", "wagon"},
        cackle_text="A goose let out a great crackly cackle that made the yard ring.",
        reveal_text="The goose was not laughing at all; it was stamping and pointing its beak toward the hiding place.",
        tags={"goose", "cackle"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "hopeful", "earnest", "gentle", "curious", "helpful"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    delivery: str
    mover: str
    spot: str
    animal: str
    child: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_missing(world: World) -> list[str]:
    basket = world.get("basket")
    child = world.get("child")
    if basket.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing", basket.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["suspense"] += 1
    return ["__missing__"]


def _r_found(world: World) -> list[str]:
    basket = world.get("basket")
    child = world.get("child")
    if basket.meters["found"] < THRESHOLD:
        return []
    sig = ("found", basket.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["gratitude"] += 1
    child.memes["misunderstanding"] = 0.0
    basket.meters["missing"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing", tag="emotion", apply=_r_missing),
    Rule(name="found", tag="emotion", apply=_r_found),
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


# ---------------------------------------------------------------------------
# Reasonableness gate and outcome model
# ---------------------------------------------------------------------------
def can_move(delivery: Delivery, mover: Mover) -> bool:
    return mover.strength >= delivery.pull


def valid_combo(delivery: Delivery, mover: Mover, spot: Spot, animal: AlarmAnimal) -> bool:
    return can_move(delivery, mover) and spot.id in mover.spots and spot.id in animal.spots


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for delivery_id, delivery in DELIVERIES.items():
        for mover_id, mover in MOVERS.items():
            for spot_id, spot in SPOTS.items():
                for animal_id, animal in ANIMALS.items():
                    if valid_combo(delivery, mover, spot, animal):
                        combos.append((delivery_id, mover_id, spot_id, animal_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    delivery = DELIVERIES[params.delivery]
    mover = MOVERS[params.mover]
    spot = SPOTS[params.spot]
    animal = ANIMALS[params.animal]
    if not valid_combo(delivery, mover, spot, animal):
        return "invalid"
    return "quick" if mover.clue + animal.alert >= spot.difficulty + 1 else "delayed"


def explain_invalid(delivery: Delivery, mover: Mover, spot: Spot, animal: AlarmAnimal) -> str:
    if not can_move(delivery, mover):
        return (
            f"(No story: {mover.label} is too small to shift {delivery.short}. "
            f"Pick a lighter delivery or a stronger mover.)"
        )
    if spot.id not in mover.spots:
        return (
            f"(No story: {mover.label} would not plausibly take the basket to {spot.label}. "
            f"Choose a different hiding spot.)"
        )
    if spot.id not in animal.spots:
        return (
            f"(No story: {animal.label} would not honestly be cackling from near {spot.label}. "
            f"Choose a place that matches the animal.)"
        )
    return "(No story: this combination does not fit the world.)"


# ---------------------------------------------------------------------------
# Screenplay helpers
# ---------------------------------------------------------------------------
def pick_name(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def introduce(world: World, child: Entity, parent: Entity, delivery: Delivery) -> None:
    child.memes["pride"] += 1
    world.say(
        f"{child.id} was a little {next(iter(child.traits), child.type)} {child.type} "
        f"who loved being trusted with small important jobs."
    )
    world.say(
        f"That afternoon, {child.id}'s {parent.label_word} set out {delivery.phrase}, "
        f"{delivery.warmth}, and said it was time to deliver it to Mrs. Maple next door."
    )
    world.say(
        f"On the kitchen table, {delivery.ingredient_phrase} waited for later, and "
        f"{child.id} sniffed the air and noticed {delivery.raw_phrase} beside the warm good smell."
    )


def set_out(world: World, child: Entity, parent: Entity, delivery: Delivery) -> None:
    basket = world.get("basket")
    basket.meters["warm"] = 1.0
    world.say(
        f'"Carry it with two hands," {parent.label_word.capitalize()} said gently. '
        f'"We only have to cross the garden path to deliver it."'
    )
    world.say(
        f"{child.id} carried {delivery.short} to the little gate and set the basket down "
        f"for one moment so {child.pronoun()} could fix the note tucked under the handle."
    )


def displace(world: World, child: Entity, delivery: Delivery, mover: Mover,
             spot: Spot, animal: AlarmAnimal) -> None:
    basket = world.get("basket")
    basket.meters["missing"] = 1.0
    basket.attrs["spot"] = spot.id
    basket.attrs["mover"] = mover.id
    world.get("animal").meters["alerted"] = 1.0
    child.memes["misunderstanding"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, {mover.move_text}. {animal.cackle_text}"
    )
    world.say(
        f"When {child.id} turned back, the basket was gone from the gate stone, "
        f"and the yard felt suddenly much bigger and quieter than before."
    )


def misunderstand(world: World, child: Entity, parent: Entity, animal: AlarmAnimal) -> None:
    world.say(
        f'{child.id} froze. "{animal.label_word if hasattr(animal, "label_word") else animal.label} '
        f'is laughing at me," {child.pronoun()} whispered.'
    )
    world.say(
        f"{child.pronoun('possessive').capitalize()} {parent.label_word} knelt beside "
        f"{child.pronoun('object')}. \"Maybe not,\" {parent.pronoun()} said softly. "
        f"\"Let us look before we decide what that sound meant.\""
    )


def search(world: World, child: Entity, parent: Entity, delivery: Delivery,
           mover: Mover, spot: Spot, animal: AlarmAnimal, outcome: str) -> None:
    child.memes["courage"] += 1
    world.say(
        f"They walked slowly toward {spot.shelter_text}. {child.id}'s heart thumped, "
        f"because every leaf and wheel-shadow seemed to hide a secret."
    )
    if outcome == "quick":
        world.say(
            f"Then {parent.label_word.capitalize()} pointed. \"Look,\" {parent.pronoun()} said. "
            f"{mover.clue_text}, and the sound of the cackle came from the same direction."
        )
    else:
        world.say(
            f"For a few long breaths they saw nothing at all. Then {parent.label_word.capitalize()} "
            f"noticed one small clue: {mover.clue_text}. It was not much, but it was enough to keep them going."
        )
        world.say(
            f"The cackle came again, not mean now, but urgent, as if the animal wanted them to hurry."
        )


def find_basket(world: World, delivery: Delivery, mover: Mover,
                spot: Spot, animal: AlarmAnimal) -> None:
    basket = world.get("basket")
    basket.meters["found"] = 1.0
    basket.meters["scuffed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There was {delivery.short}, {spot.discovery_text}. {mover.reveal_text}"
    )
    world.say(animal.reveal_text)


def mend_and_deliver(world: World, child: Entity, parent: Entity, delivery: Delivery,
                     outcome: str) -> None:
    basket = world.get("basket")
    basket.meters["delivered"] = 1.0
    world.say(
        f"{child.id} let out the breath {child.pronoun()} had been holding. "
        f"{parent.label_word.capitalize()} straightened the cloth, checked that {delivery.short} was still fine, "
        f"and put the basket back into {child.pronoun('possessive')} hands."
    )
    world.say(
        f'"So that was not a nasty laugh after all," {child.id} said. '
        f'"It was a warning."'
    )
    if outcome == "quick":
        world.say(
            f"A moment later they reached Mrs. Maple's porch and got to deliver the gift while it was still warm."
        )
    else:
        world.say(
            f"A few moments later they reached Mrs. Maple's porch and got to deliver the gift with both of them smiling again."
        )
    world.say(
        f'Mrs. Maple opened the door, thanked {child.id} as if {child.pronoun()} had brought the whole afternoon in a basket, '
        f'and broke off a little piece to share at once. On the walk home, {child.id} heard another cackle from the garden and waved back.'
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    if params.delivery not in DELIVERIES:
        raise StoryError(f"(Unknown delivery '{params.delivery}').")
    if params.mover not in MOVERS:
        raise StoryError(f"(Unknown mover '{params.mover}').")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot '{params.spot}').")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal '{params.animal}').")

    delivery = DELIVERIES[params.delivery]
    mover = MOVERS[params.mover]
    spot = SPOTS[params.spot]
    animal_cfg = ANIMALS[params.animal]
    if not valid_combo(delivery, mover, spot, animal_cfg):
        raise StoryError(explain_invalid(delivery, mover, spot, animal_cfg))

    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_gender,
        label=params.child,
        role="child",
        traits=[params.trait],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label="the parent",
        role="parent",
    ))
    basket = world.add(Entity(
        id="basket",
        kind="thing",
        type="basket",
        label="basket",
        role="delivery",
        attrs={"spot": "", "mover": ""},
    ))
    animal = world.add(Entity(
        id="animal",
        kind="animal",
        type=params.animal,
        label=animal_cfg.label,
        role="animal",
    ))
    world.add(Entity(id="spot", kind="place", type="place", label=spot.label, role="spot"))

    basket.meters["missing"] = 0.0
    basket.meters["found"] = 0.0
    basket.meters["warm"] = 0.0
    basket.meters["scuffed"] = 0.0
    basket.meters["delivered"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["suspense"] = 0.0
    child.memes["misunderstanding"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["gratitude"] = 0.0
    child.memes["courage"] = 0.0
    parent.memes["calm"] = 1.0
    animal.meters["alerted"] = 0.0

    outcome = outcome_of(params)

    introduce(world, child, parent, delivery)
    world.para()
    set_out(world, child, parent, delivery)
    displace(world, child, delivery, mover, spot, animal_cfg)
    misunderstand(world, child, parent, animal_cfg)
    world.para()
    search(world, child, parent, delivery, mover, spot, animal_cfg, outcome)
    find_basket(world, delivery, mover, spot, animal_cfg)
    world.para()
    mend_and_deliver(world, child, parent, delivery, outcome)

    world.facts.update(
        child_name=params.child,
        child=child,
        parent=parent,
        basket=basket,
        delivery=delivery,
        mover=mover,
        spot=spot,
        animal_cfg=animal_cfg,
        outcome=outcome,
        recipient="Mrs. Maple",
        misunderstood=child.memes["misunderstanding"] < THRESHOLD,
        delivered=basket.meters["delivered"] >= THRESHOLD,
        missing=basket.meters["scuffed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "deliver": [(
        "What does deliver mean?",
        "To deliver something means to carry it to the person who is meant to receive it. It is a careful job because you are helping someone."
    )],
    "cackle": [(
        "What is a cackle?",
        "A cackle is a loud crackly bird sound, often made by a hen or a goose. It can sound sharp, even when the animal is only excited or warning about something."
    )],
    "raw_dough": [(
        "What is raw dough?",
        "Raw dough is dough before it is baked. It is soft and unfinished, so it still needs time and heat before it becomes bread or rolls."
    )],
    "berries": [(
        "What are raw berries?",
        "Raw berries are berries just as they come from the bowl or bush, before they are cooked in a pie or jam. They are fresh and juicy."
    )],
    "carrots": [(
        "What are raw carrots?",
        "Raw carrots are carrots before they are cooked. They are crunchy and can later be turned into soup or stew."
    )],
    "puppy": [(
        "Why might a puppy drag something away?",
        "A puppy may drag something because it thinks the cloth or ribbon is a toy. Puppies often play first and understand later."
    )],
    "kitten": [(
        "Why might a kitten pull at a ribbon?",
        "Kittens love chasing and batting little moving things. A ribbon can look like a game to them."
    )],
    "wind": [(
        "How can a breeze move light things?",
        "A breeze can catch a loose cloth or paper and keep nudging it along. If the thing is light enough, it may slide farther than you expect."
    )],
    "hen": [(
        "Why does a hen cackle?",
        "A hen cackles when it is excited, startled, or calling attention to something. The sound is not always angry."
    )],
    "goose": [(
        "Why can a goose sound loud?",
        "Geese make strong noisy calls to warn, complain, or tell everyone something is happening. Their voices can fill a whole yard."
    )],
}
KNOWLEDGE_ORDER = ["deliver", "cackle", "raw_dough", "berries", "carrots",
                   "puppy", "kitten", "wind", "hen", "goose"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    delivery = f["delivery"]
    animal = f["animal_cfg"]
    mover = f["mover"]
    spot = f["spot"]
    child = f["child"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that uses the words "deliver", "cackle", and "raw".',
        f"Tell a gentle misunderstanding story where {child.label} tries to deliver {delivery.phrase}, hears {animal.label} cackle, and wrongly thinks the sound is a mean laugh before discovering the truth.",
        f"Write a suspenseful but cozy story about a missing basket, a {mover.label}, and a search near {spot.label} that ends with relief and kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    delivery = f["delivery"]
    mover = f["mover"]
    spot = f["spot"]
    animal = f["animal_cfg"]
    outcome = f["outcome"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, {child.pronoun('possessive')} {pw}, and a noisy {animal.label}. Together they turn a small garden problem into a kind ending."
        ),
        (
            "What was the child trying to do?",
            f"{child.label} was trying to deliver {delivery.phrase} to Mrs. Maple next door. The job felt important because the gift had been prepared with care."
        ),
        (
            "Where did the word raw fit into the story?",
            f"In the kitchen there was {delivery.raw_phrase} waiting for later. That little detail made the home feel busy and real before the basket went missing."
        ),
        (
            f"Why did {child.label} feel scared when {animal.label} made that cackle?",
            f"{child.label} heard the sharp sound just as the basket disappeared, so {child.pronoun()} thought the noise meant someone was mocking {child.pronoun('object')}. The fear came from the misunderstanding, not from knowing what had really happened."
        ),
        (
            "What had really happened to the basket?",
            f"{mover.label.capitalize()} had moved it to {spot.label}. The cackle was near the hiding place because the animal was fussing about the commotion there."
        ),
    ]
    if outcome == "quick":
        qa.append((
            "How did they find the basket so quickly?",
            f"They followed the first clear clue right away: {mover.clue_text}. Because the clue and the cackle pointed the same way, the search turned before worry could grow too large."
        ))
    else:
        qa.append((
            "Why did the search feel suspenseful?",
            f"For a little while they could not see anything, so every shadow in the yard felt important. Then one small clue, {mover.clue_text}, helped them keep going until the hiding place made sense."
        ))
    qa.append((
        "What did the child learn at the end?",
        f"{child.label} learned not to decide too fast what a scary sound means. At the end, {child.pronoun()} understood that the cackle had been more like a warning than a laugh."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["delivery"].tags) | set(f["mover"].tags) | set(f["animal_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
movable(D, M) :- delivery(D), mover(M), pull(D, P), strength(M, S), S >= P.
valid(D, M, S, A) :- movable(D, M), mover_spot(M, S), animal_spot(A, S).

quick(D, M, S, A) :- valid(D, M, S, A),
                     clue(M, C), alert(A, Al), difficulty(S, Dif),
                     C + Al >= Dif + 1.
delayed(D, M, S, A) :- valid(D, M, S, A), not quick(D, M, S, A).

outcome(quick)   :- chosen(D, M, S, A), quick(D, M, S, A).
outcome(delayed) :- chosen(D, M, S, A), delayed(D, M, S, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for delivery_id, delivery in DELIVERIES.items():
        lines.append(asp.fact("delivery", delivery_id))
        lines.append(asp.fact("pull", delivery_id, delivery.pull))
    for mover_id, mover in MOVERS.items():
        lines.append(asp.fact("mover", mover_id))
        lines.append(asp.fact("strength", mover_id, mover.strength))
        lines.append(asp.fact("clue", mover_id, mover.clue))
        for spot_id in sorted(mover.spots):
            lines.append(asp.fact("mover_spot", mover_id, spot_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        lines.append(asp.fact("difficulty", spot_id, spot.difficulty))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("alert", animal_id, animal.alert))
        for spot_id in sorted(animal.spots):
            lines.append(asp.fact("animal_spot", animal_id, spot_id))
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
        asp.fact("chosen", params.delivery, params.mover, params.spot, params.animal),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatch = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcome checks failed.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - defensive verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        delivery="rolls",
        mover="puppy",
        spot="bench",
        animal="hen",
        child="Lily",
        child_gender="girl",
        parent="mother",
        trait="helpful",
    ),
    StoryParams(
        delivery="pie",
        mover="puppy",
        spot="wagon",
        animal="goose",
        child="Ben",
        child_gender="boy",
        parent="father",
        trait="earnest",
    ),
    StoryParams(
        delivery="soup",
        mover="breeze",
        spot="hedge",
        animal="hen",
        child="Mia",
        child_gender="girl",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        delivery="rolls",
        mover="kitten",
        spot="bench",
        animal="goose",
        child="Theo",
        child_gender="boy",
        parent="father",
        trait="curious",
    ),
    StoryParams(
        delivery="pie",
        mover="puppy",
        spot="bench",
        animal="goose",
        child="Nora",
        child_gender="girl",
        parent="mother",
        trait="hopeful",
    ),
]


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child must deliver a gift, misreads a cackle, and discovers a kinder truth."
    )
    ap.add_argument("--delivery", choices=sorted(DELIVERIES))
    ap.add_argument("--mover", choices=sorted(MOVERS))
    ap.add_argument("--spot", choices=sorted(SPOTS))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.delivery is not None and args.delivery not in DELIVERIES:
        raise StoryError(f"(Unknown delivery '{args.delivery}').")
    if args.mover is not None and args.mover not in MOVERS:
        raise StoryError(f"(Unknown mover '{args.mover}').")
    if args.spot is not None and args.spot not in SPOTS:
        raise StoryError(f"(Unknown spot '{args.spot}').")
    if args.animal is not None and args.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal '{args.animal}').")

    if args.delivery and args.mover and args.spot and args.animal:
        delivery = DELIVERIES[args.delivery]
        mover = MOVERS[args.mover]
        spot = SPOTS[args.spot]
        animal = ANIMALS[args.animal]
        if not valid_combo(delivery, mover, spot, animal):
            raise StoryError(explain_invalid(delivery, mover, spot, animal))

    combos = [
        combo for combo in valid_combos()
        if (args.delivery is None or combo[0] == args.delivery)
        and (args.mover is None or combo[1] == args.mover)
        and (args.spot is None or combo[2] == args.spot)
        and (args.animal is None or combo[3] == args.animal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    delivery_id, mover_id, spot_id, animal_id = rng.choice(sorted(combos))
    if args.gender:
        gender = args.gender
        name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
        child_name = args.child or rng.choice(name_pool)
    else:
        child_name, gender = (args.child, rng.choice(["girl", "boy"])) if args.child else pick_name(rng)
    if args.child and args.gender:
        child_name = args.child
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        delivery=delivery_id,
        mover=mover_id,
        spot=spot_id,
        animal=animal_id,
        child=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.delivery not in DELIVERIES or params.mover not in MOVERS or params.spot not in SPOTS or params.animal not in ANIMALS:
        raise StoryError("(Parameters refer to an unknown registry key.)")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    story = sample.story.replace("child", sample.params.child)
    print(story)
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
        print(f"{len(combos)} compatible (delivery, mover, spot, animal) combos:\n")
        for delivery, mover, spot, animal in combos:
            quick = "quick" if asp_outcome(StoryParams(
                delivery=delivery,
                mover=mover,
                spot=spot,
                animal=animal,
                child="Lily",
                child_gender="girl",
                parent="mother",
                trait="gentle",
            )) == "quick" else "delayed"
            print(f"  {delivery:6} {mover:7} {spot:6} {animal:5}  [{quick}]")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child}: {p.delivery} moved by {p.mover} near {p.spot} "
                f"({p.animal}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
