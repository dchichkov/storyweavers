#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grump_conceive_gather_suspense_twist_bravery_heartwarming.py
========================================================================================

A standalone story world about a child who thinks a local caretaker is a grump,
just as storm clouds gather and a small animal needs help. The child must
conceive a plan, act with bravery, and discover a heartwarming twist: the
supposed grump has already been quietly preparing to help.

Run it
------
    python storyworlds/worlds/gpt-5.4/grump_conceive_gather_suspense_twist_bravery_heartwarming.py
    python storyworlds/worlds/gpt-5.4/grump_conceive_gather_suspense_twist_bravery_heartwarming.py --place park --animal duckling --carrier crate
    python storyworlds/worlds/gpt-5.4/grump_conceive_gather_suspense_twist_bravery_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/grump_conceive_gather_suspense_twist_bravery_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/grump_conceive_gather_suspense_twist_bravery_heartwarming.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
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
class Place:
    id: str
    label: str
    keeper_name: str
    keeper_type: str
    keeper_role: str
    rumor: str
    shed_label: str
    hosts: set[str] = field(default_factory=set)
    spots: dict[str, str] = field(default_factory=dict)
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
class AnimalCfg:
    id: str
    label: str
    phrase: str
    sound: str
    call: str
    move_verb: str
    comfort: str
    vulnerability: int
    twist_line: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    power: int
    fits: set[str] = field(default_factory=set)
    gathered: str = ""
    carry_line: str = ""
    qa_text: str = ""
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_exposure(world: World) -> list[str]:
    out: list[str] = []
    sky = world.get("sky")
    animal = world.get("animal")
    child = world.get("child")
    if sky.meters["storm"] < THRESHOLD:
        return out
    if animal.meters["outside"] < THRESHOLD:
        return out
    sig = ("exposure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["wet"] += 1
    animal.meters["cold"] += max(1, int(world.facts["animal_cfg"].vulnerability))
    animal.meters["risk"] += 1
    child.memes["fear"] += 1
    out.append("__exposure__")
    return out


def _r_shelter(world: World) -> list[str]:
    out: list[str] = []
    animal = world.get("animal")
    shed = world.get("shed")
    if animal.meters["inside"] < THRESHOLD or shed.meters["warmth"] < THRESHOLD:
        return out
    sig = ("shelter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    animal.meters["safe"] += 1
    animal.meters["cold"] = 0.0
    animal.meters["wet"] = 0.0
    animal.meters["risk"] = 0.0
    out.append("__safe__")
    return out


def _r_reveal_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    keeper = world.get("keeper")
    if keeper.memes["kindness_revealed"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["trust"] += 2
    child.memes["fear"] = 0.0
    child.memes["warmth"] += 1
    out.append("__trust__")
    return out


CAUSAL_RULES = [
    Rule(name="exposure", tag="physical", apply=_r_exposure),
    Rule(name="shelter", tag="physical", apply=_r_shelter),
    Rule(name="reveal_kindness", tag="social", apply=_r_reveal_kindness),
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


PLACES = {
    "garden": Place(
        id="garden",
        label="the old rose garden",
        keeper_name="Mr. Reed",
        keeper_type="man",
        keeper_role="gardener",
        rumor="He always spoke in short little grumbles and shooed balls away from his flower beds.",
        shed_label="the potting shed",
        hosts={"kitten"},
        spots={"kitten": "under a tipped wheelbarrow by the beans"},
        tags={"garden"},
    ),
    "park": Place(
        id="park",
        label="the little park by the pond",
        keeper_name="Ms. Hollow",
        keeper_type="woman",
        keeper_role="groundskeeper",
        rumor="She frowned when children left wrappers on the grass and sounded sharp when she asked them to clean up.",
        shed_label="the tool shed by the pond",
        hosts={"duckling", "puppy"},
        spots={
            "duckling": "in the reeds beside the pond path",
            "puppy": "under the long green bench near the gate",
        },
        tags={"park", "pond"},
    ),
    "orchard": Place(
        id="orchard",
        label="the windy apple orchard",
        keeper_name="Mrs. Vale",
        keeper_type="woman",
        keeper_role="orchard keeper",
        rumor="She had a scratchy voice and a face that looked stern even when she was listening.",
        shed_label="the packing shed",
        hosts={"kitten", "puppy"},
        spots={
            "kitten": "beneath a stack of empty apple baskets",
            "puppy": "behind a wobbling crate near the fence",
        },
        tags={"orchard"},
    ),
}

ANIMALS = {
    "kitten": AnimalCfg(
        id="kitten",
        label="kitten",
        phrase="a tiny striped kitten",
        sound="mewing",
        call="mew",
        move_verb="curled",
        comfort="towels",
        vulnerability=1,
        twist_line="I heard this little one before the thunder started, so I put out a saucer of water and dry towels.",
        tags={"kitten", "storm"},
    ),
    "duckling": AnimalCfg(
        id="duckling",
        label="duckling",
        phrase="a soaked yellow duckling",
        sound="peeping",
        call="peep",
        move_verb="tucked",
        comfort="straw",
        vulnerability=2,
        twist_line="I saw the mother duck flying in circles, so I gathered straw and a dry crate in case one of her babies was left behind.",
        tags={"duckling", "storm", "pond"},
    ),
    "puppy": AnimalCfg(
        id="puppy",
        label="puppy",
        phrase="a shivering brown puppy",
        sound="whining",
        call="whine",
        move_verb="nestled",
        comfort="blankets",
        vulnerability=2,
        twist_line="I found paw prints in the mud, so I set out blankets and a warm bowl before the rain grew worse.",
        tags={"puppy", "storm"},
    ),
}

CARRIERS = {
    "basket": Carrier(
        id="basket",
        label="basket",
        phrase="a round basket",
        power=2,
        fits={"kitten", "duckling"},
        gathered="towels",
        carry_line="lifted the little body into the basket with both careful hands",
        qa_text="used a basket to carry the little animal",
        tags={"basket"},
    ),
    "crate": Carrier(
        id="crate",
        label="crate",
        phrase="a wooden crate",
        power=3,
        fits={"duckling", "puppy"},
        gathered="straw",
        carry_line="slid the crate close and coaxed the little one inside",
        qa_text="slid the animal into a crate and hurried it to shelter",
        tags={"crate"},
    ),
    "wagon": Carrier(
        id="wagon",
        label="wagon",
        phrase="a red wagon",
        power=2,
        fits={"puppy", "kitten"},
        gathered="blankets",
        carry_line="settled the trembling animal into the wagon and pulled as fast as was safe",
        qa_text="used a wagon so the animal did not have to walk in the rain",
        tags={"wagon"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Zoe", "Nora", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Eli", "Theo", "Finn", "Noah"]
TRAITS = ["careful", "thoughtful", "steady", "kind", "curious", "brave"]


def animal_in_place(place: Place, animal: AnimalCfg) -> bool:
    return animal.id in place.hosts


def carrier_fits(carrier: Carrier, animal: AnimalCfg) -> bool:
    return animal.id in carrier.fits


def rescue_mode(animal: AnimalCfg, carrier: Carrier, storm_level: int) -> str:
    threat = animal.vulnerability + storm_level
    return "carry" if carrier.power >= threat else "knock"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for animal_id, animal in ANIMALS.items():
            if not animal_in_place(place, animal):
                continue
            for carrier_id, carrier in CARRIERS.items():
                if carrier_fits(carrier, animal):
                    combos.append((place_id, animal_id, carrier_id))
    return combos


@dataclass
class StoryParams:
    place: str
    animal: str
    carrier: str
    child_name: str
    child_gender: str
    child_trait: str
    storm_level: int = 1
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


def explain_rejection(place: Place, animal: AnimalCfg, carrier: Carrier) -> str:
    if not animal_in_place(place, animal):
        return (
            f"(No story: {animal.phrase} is not a good fit for {place.label}. "
            f"Pick an animal that plausibly belongs there.)"
        )
    if not carrier_fits(carrier, animal):
        return (
            f"(No story: {carrier.phrase} is not a sensible way to move {animal.phrase}. "
            f"Pick a carrier that fits the animal safely.)"
        )
    return "(No story: this combination does not make a sensible rescue.)"


def animal_spot(place: Place, animal: AnimalCfg) -> str:
    return place.spots[animal.id]


def introduce(world: World, child: Entity, keeper: Entity, place: Place) -> None:
    child.memes["unease"] += 1
    world.say(
        f"{child.id} loved visiting {place.label}, but everyone in the neighborhood called "
        f"{keeper.id} a grump. {place.rumor}"
    )
    world.say(
        f"So when {keeper.id} passed with muddy boots and a ring of keys, "
        f"{child.id} watched from the path and wondered what kind thoughts might be hiding under all that grumbling."
    )


def gather_clouds(world: World, child: Entity) -> None:
    sky = world.get("sky")
    sky.meters["storm"] = float(world.facts["storm_level"])
    world.say(
        f"That afternoon, dark clouds began to gather over the trees, and the wind pushed the leaves the wrong way. "
        f"{child.id} felt the air go cooler and listened hard."
    )


def hear_animal(world: World, child: Entity, animal: AnimalCfg, place: Place) -> None:
    world.say(
        f"Then {child.id} heard a small {animal.call} from {animal_spot(place, animal)}. "
        f"It was not loud, which made it even more worrying."
    )
    world.say(
        f"When {child.pronoun()} looked closer, {child.pronoun()} found {animal.phrase}, alone while the storm crept nearer."
    )


def feel_suspense(world: World, child: Entity, animal_ent: Entity) -> None:
    animal_ent.meters["outside"] = 1.0
    propagate(world, narrate=False)
    if animal_ent.meters["cold"] >= THRESHOLD:
        world.say(
            f"The tiny creature was already damp and trembling, and {child.id}'s stomach gave a nervous little flip. "
            f"The first drop of rain had not even fallen yet."
        )


def conceive_plan(world: World, child: Entity, carrier: Carrier) -> None:
    child.memes["courage"] += 1
    child.memes["care"] += 1
    world.say(
        f"{child.id} tried to conceive a plan instead of running away. "
        f"{child.pronoun().capitalize()} grabbed {carrier.phrase} and looked toward the shed."
    )


def brave_carry(world: World, child: Entity, animal_ent: Entity, carrier_ent: Entity, carrier: Carrier) -> None:
    child.memes["courage"] += 1
    carrier_ent.meters["used"] += 1
    animal_ent.meters["outside"] = 0.0
    animal_ent.meters["in_carrier"] = 1.0
    world.say(
        f"Even though the path shook with thunder far away, {child.id} did not run home. "
        f"{child.pronoun().capitalize()} {carrier.carry_line}."
    )
    world.say(
        f"Then {child.pronoun()} hurried toward the shed, one brave step after another, trying not to jostle the frightened little passenger."
    )


def brave_knock(world: World, child: Entity, carrier: Carrier, place: Place) -> None:
    child.memes["courage"] += 2
    world.say(
        f"{child.id} looked at {carrier.phrase}, looked at the shaking bushes, and knew {child.pronoun()} could not do the whole job alone. "
        f"So {child.pronoun()} ran to {place.shed_label} and knocked, though the wind made the door sound creaky and mysterious."
    )
    world.say(
        f"For one long second, nobody answered, and the story felt as if it might turn scary."
    )


def reveal_twist(world: World, child: Entity, keeper: Entity, animal: AnimalCfg, carrier: Carrier) -> None:
    keeper.memes["kindness_revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the door opened, and there stood {keeper.id} with {animal.comfort}, a lantern, and a dry corner already waiting. "
        f'"I was hoping I had not come too late," {keeper.pronoun()} said.'
    )
    world.say(
        f"{animal.twist_line} The grump voice was still scratchy, but now it sounded gentle too."
    )
    world.say(
        f"{child.id} blinked in surprise. All that time, {keeper.id} had been preparing to help instead of hiding anything at all."
    )
    world.facts["twist_revealed"] = True
    world.facts["keeper_supplies"] = f"{animal.comfort}, a lantern, and a dry corner"


def move_inside(world: World, child: Entity, keeper: Entity, animal_ent: Entity, carrier_ent: Entity, animal: AnimalCfg, carrier: Carrier, branch: str) -> None:
    animal_ent.meters["inside"] = 1.0
    animal_ent.meters["outside"] = 0.0
    carrier_ent.meters["used"] += 1
    shed = world.get("shed")
    shed.meters["warmth"] = 1.0
    if branch == "carry":
        world.say(
            f"Together they tucked the little {animal.label} into the dry corner, and {keeper.id} spread out the {animal.comfort}. "
            f"{child.id} set down the {carrier.label} with a sigh of relief."
        )
    else:
        world.say(
            f"{keeper.id} and {child.id} hurried back through the gusty air, and soon the little {animal.label} was safe inside the shed. "
            f"{keeper.pronoun().capitalize()} used the {carrier.label} while {child.id} held the door and talked softly."
        )
    propagate(world, narrate=False)


def warm_ending(world: World, child: Entity, keeper: Entity, animal_ent: Entity, place: Place) -> None:
    animal_ent.memes["calm"] += 1
    child.memes["relief"] += 1
    keeper.memes["warmth"] += 1
    world.say(
        f"After a little while, the shivering stopped. The tiny creature {world.facts['animal_cfg'].move_verb} into the warm bedding and closed its eyes."
    )
    world.say(
        f"{child.id} looked at {keeper.id} differently then. The face everyone had called grumpy was just careful and tired, and behind it was a very tender heart."
    )
    world.say(
        f"When the rain finally rattled on the roof, they stood together in {place.shed_label}, listening to it, and no one felt lonely at all."
    )


def tell(
    place: Place,
    animal: AnimalCfg,
    carrier: Carrier,
    child_name: str = "Mina",
    child_gender: str = "girl",
    child_trait: str = "careful",
    storm_level: int = 1,
) -> World:
    world = World(place)
    world.facts["storm_level"] = storm_level
    world.facts["animal_cfg"] = animal
    world.facts["carrier_cfg"] = carrier
    world.facts["place_cfg"] = place
    world.facts["twist_revealed"] = False
    world.facts["keeper_supplies"] = ""

    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[child_trait],
            attrs={},
        )
    )
    keeper = world.add(
        Entity(
            id=place.keeper_name,
            kind="character",
            type=place.keeper_type,
            role="keeper",
            label=place.keeper_role,
            attrs={},
        )
    )
    animal_ent = world.add(
        Entity(
            id="animal",
            kind="thing",
            type="animal",
            label=animal.label,
            role="animal",
            attrs={"spot": animal_spot(place, animal)},
        )
    )
    carrier_ent = world.add(
        Entity(
            id="carrier",
            kind="thing",
            type="carrier",
            label=carrier.label,
            role="carrier",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="sky",
            kind="thing",
            type="weather",
            label="the sky",
            role="sky",
            attrs={},
        )
    )
    world.add(
        Entity(
            id="shed",
            kind="thing",
            type="shelter",
            label=place.shed_label,
            role="shed",
            attrs={},
        )
    )

    child.memes["fear"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["courage"] = 1.0 if child_trait in {"steady", "brave"} else 0.0
    keeper.memes["kindness_revealed"] = 0.0
    animal_ent.meters["outside"] = 0.0
    animal_ent.meters["inside"] = 0.0

    introduce(world, child, keeper, place)
    world.para()
    gather_clouds(world, child)
    hear_animal(world, child, animal, place)
    feel_suspense(world, child, animal_ent)
    conceive_plan(world, child, carrier)

    branch = rescue_mode(animal, carrier, storm_level)
    world.facts["branch"] = branch

    world.para()
    if branch == "carry":
        brave_carry(world, child, animal_ent, carrier_ent, carrier)
        reveal_twist(world, child, keeper, animal, carrier)
        move_inside(world, child, keeper, animal_ent, carrier_ent, animal, carrier, branch)
    else:
        brave_knock(world, child, carrier, place)
        reveal_twist(world, child, keeper, animal, carrier)
        move_inside(world, child, keeper, animal_ent, carrier_ent, animal, carrier, branch)

    world.para()
    warm_ending(world, child, keeper, animal_ent, place)

    world.facts.update(
        child=child,
        keeper=keeper,
        animal_ent=animal_ent,
        carrier_ent=carrier_ent,
        safe=animal_ent.meters["safe"] >= THRESHOLD,
        place=place,
        animal=animal,
        carrier=carrier,
        bravery=child.memes["courage"],
    )
    return world


KNOWLEDGE = {
    "storm": [
        (
            "Why can a storm be dangerous for a very small animal?",
            "A small animal can get cold and weak very fast in wind and rain. It may need dry shelter before it can rest safely."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right thing even when you feel nervous. It does not mean never being scared."
        )
    ],
    "kitten": [
        (
            "What helps a cold kitten warm up?",
            "A cold kitten needs a dry place and gentle warmth. Soft towels can help it stop shivering while a grown-up keeps it safe."
        )
    ],
    "duckling": [
        (
            "Why does a duckling still need help in a storm if ducks like water?",
            "Ducklings can swim, but a storm is different from a calm pond. Wind and cold rain can tire a little duckling out very quickly."
        )
    ],
    "puppy": [
        (
            "Why should you help a lost puppy carefully?",
            "A lost puppy may be frightened and shaky. Moving slowly and bringing it somewhere warm can help it feel safe."
        )
    ],
    "basket": [
        (
            "What is a basket good for in a rescue?",
            "A basket can hold a small animal gently so it does not have to walk through mud or rain. That makes it easier to carry the animal to shelter."
        )
    ],
    "crate": [
        (
            "Why is a crate useful for carrying an animal?",
            "A crate gives an animal a small, steady space. That can help keep the animal safe while someone moves it."
        )
    ],
    "wagon": [
        (
            "Why might a wagon help in a rescue?",
            "A wagon can carry something too tired to walk far. It also helps keep little paws out of deep puddles."
        )
    ],
    "garden": [
        (
            "What does a gardener do?",
            "A gardener takes care of plants, paths, and growing things. Sometimes gardeners sound busy or stern because they are protecting what they care for."
        )
    ],
    "park": [
        (
            "What does a groundskeeper do in a park?",
            "A groundskeeper keeps the park clean and safe. That can include watching the paths, the grass, and the pond."
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees grow in rows. People there care for the trees and gather the fruit when it is ready."
        )
    ],
    "pond": [
        (
            "Why do people need to be careful near a pond in bad weather?",
            "Rain can make the ground slippery, and wind can make the water rough. That is why slow, careful steps matter near a pond."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "storm",
    "bravery",
    "kitten",
    "duckling",
    "puppy",
    "basket",
    "crate",
    "wagon",
    "garden",
    "park",
    "orchard",
    "pond",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    animal = f["animal"]
    place = f["place"]
    branch = f["branch"]
    if branch == "knock":
        return [
            f'Write a heartwarming story for a 3-to-5-year-old that includes the words "grump", "conceive", and "gather". A child hears a {animal.label} in trouble as storm clouds gather near {place.label}.',
            f"Tell a suspenseful but gentle story where {child.id} thinks {keeper.id} is a grump, cannot save a little {animal.label} alone, and bravely knocks on a shed door.",
            f"Write a story with a twist where the stern caretaker turns out to have already gathered supplies to help the animal, and the ending feels warm and safe.",
        ]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "grump", "conceive", and "gather". A child carries a small {animal.label} toward shelter while a storm begins to gather.',
        f"Tell a gentle suspense story where {child.id} is brave enough to help first, then learns that {keeper.id}, the supposed grump, had already prepared a safe place.",
        f"Write a story with a twist ending that changes how a child sees a stern grown-up, and end with the rain on the roof and everyone feeling safer.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    animal = f["animal"]
    place = f["place"]
    carrier = f["carrier"]
    branch = f["branch"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {place.keeper_name}, and a small {animal.label} in trouble. The story begins with {child.id} thinking the caretaker is a grump."
        ),
        (
            f"Why was {child.id} worried?",
            f"{child.id} heard the little {animal.label} alone while storm clouds began to gather. The small cries and the coming rain made the danger feel real."
        ),
        (
            f"What plan did {child.id} conceive?",
            f"{child.id} decided not to run away and tried to help using {carrier.phrase}. That choice matters because {child.pronoun()} turned worry into action."
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the supposed grump had already gathered supplies and a warm place for the animal. {place.keeper_name} sounded stern, but was actually preparing to help all along."
        ),
    ]
    if branch == "knock":
        qa.append(
            (
                f"How did {child.id} show bravery?",
                f"{child.id} realized {child.pronoun()} could not do everything alone, so {child.pronoun()} knocked on the shed door even though it felt scary. That was brave because asking for help was the safest choice."
            )
        )
    else:
        qa.append(
            (
                f"How did {child.id} show bravery?",
                f"{child.id} carefully moved the frightened {animal.label} toward shelter while thunder rumbled in the distance. That was brave because {child.pronoun()} stayed gentle and steady instead of freezing."
            )
        )
    qa.append(
        (
            f"How did the story end?",
            f"The little {animal.label} grew warm and calm inside {place.shed_label}. By the end, {child.id} no longer saw {place.keeper_name} as a grump, but as someone with a tender heart."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"storm", "bravery"} | set(f["animal"].tags) | set(f["carrier"].tags) | set(f["place"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        animal="kitten",
        carrier="basket",
        child_name="Mina",
        child_gender="girl",
        child_trait="careful",
        storm_level=1,
    ),
    StoryParams(
        place="park",
        animal="duckling",
        carrier="crate",
        child_name="Leo",
        child_gender="boy",
        child_trait="steady",
        storm_level=1,
    ),
    StoryParams(
        place="park",
        animal="puppy",
        carrier="wagon",
        child_name="Ava",
        child_gender="girl",
        child_trait="kind",
        storm_level=1,
    ),
    StoryParams(
        place="orchard",
        animal="puppy",
        carrier="crate",
        child_name="Ben",
        child_gender="boy",
        child_trait="brave",
        storm_level=2,
    ),
    StoryParams(
        place="orchard",
        animal="kitten",
        carrier="wagon",
        child_name="Nora",
        child_gender="girl",
        child_trait="thoughtful",
        storm_level=2,
    ),
]


ASP_RULES = r"""
valid(P,A,C) :- place(P), animal(A), carrier(C), hosts(P,A), fits(C,A).

threat(A,S,T) :- vulnerability(A,V), storm_level(S), T = V + S.
carry_branch(A,C,S) :- chosen_animal(A), chosen_carrier(C), storm_level(S),
                       threat(A,S,T), power(C,P), P >= T.
knock_branch(A,C,S) :- chosen_animal(A), chosen_carrier(C), storm_level(S),
                       threat(A,S,T), power(C,P), P < T.

outcome(carry) :- carry_branch(_,_,_).
outcome(knock) :- knock_branch(_,_,_).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for animal_id in sorted(place.hosts):
            lines.append(asp.fact("hosts", place_id, animal_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        lines.append(asp.fact("vulnerability", animal_id, animal.vulnerability))
    for carrier_id, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", carrier_id))
        lines.append(asp.fact("power", carrier_id, carrier.power))
        for animal_id in sorted(carrier.fits):
            lines.append(asp.fact("fits", carrier_id, animal_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_branch(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_animal", params.animal),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("storm_level", params.storm_level),
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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = rescue_mode(ANIMALS[params.animal], CARRIERS[params.carrier], params.storm_level)
        cl = asp_branch(params)
        if py != cl:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches rescue_mode() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} branch predictions differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming suspense story world: a child, a grump, a storm, and a surprising rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--storm-level", type=int, choices=[1, 2], help="higher means the child is more likely to need the keeper's help")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, animal, carrier) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.animal and args.carrier:
        place = PLACES[args.place]
        animal = ANIMALS[args.animal]
        carrier = CARRIERS[args.carrier]
        if not (animal_in_place(place, animal) and carrier_fits(carrier, animal)):
            raise StoryError(explain_rejection(place, animal, carrier))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.animal is None or combo[1] == args.animal)
        and (args.carrier is None or combo[2] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, animal_id, carrier_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    storm_level = args.storm_level if args.storm_level is not None else rng.choice([1, 2])

    return StoryParams(
        place=place_id,
        animal=animal_id,
        carrier=carrier_id,
        child_name=name,
        child_gender=gender,
        child_trait=trait,
        storm_level=storm_level,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")

    place = PLACES[params.place]
    animal = ANIMALS[params.animal]
    carrier = CARRIERS[params.carrier]

    if not (animal_in_place(place, animal) and carrier_fits(carrier, animal)):
        raise StoryError(explain_rejection(place, animal, carrier))

    world = tell(
        place=place,
        animal=animal,
        carrier=carrier,
        child_name=params.child_name,
        child_gender=params.child_gender,
        child_trait=params.child_trait,
        storm_level=params.storm_level,
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
        print(f"{len(combos)} compatible (place, animal, carrier) combos:\n")
        for place, animal, carrier in combos:
            print(f"  {place:8} {animal:8} {carrier}")
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
            header = f"### {p.child_name}: {p.animal} at {p.place} with {p.carrier} ({rescue_mode(ANIMALS[p.animal], CARRIERS[p.carrier], p.storm_level)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
