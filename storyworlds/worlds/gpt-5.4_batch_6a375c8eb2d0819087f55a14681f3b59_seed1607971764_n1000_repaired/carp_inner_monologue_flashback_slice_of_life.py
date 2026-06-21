#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py
===========================================================================

A standalone story world for a small, slice-of-life tale about a child feeding
carp with a grown-up beside them. The world centers on one gentle lesson:
carp do not come close for noise and hurry, but they will rise through the
water for patient hands and suitable food.

This world uses:
- inner monologue: the child privately notices, worries, and understands
- flashback: the child remembers an earlier moment that explains the turn

Run it
------
    python storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py --place garden_pond --offering pellets --approach rush
    python storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py --offering crackers
    python storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py --trace
    python storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py --json
    python storyworlds/worlds/gpt-5.4/carp_inner_monologue_flashback_slice_of_life.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    edible_for_carp: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "sister", "grandmother"}
        male = {"boy", "man", "father", "uncle", "brother", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "father": "dad",
            "mother": "mom",
            "aunt": "aunt",
            "uncle": "uncle",
            "sister": "sister",
            "brother": "brother",
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
class Place:
    id: str
    label: str
    image: str
    edge: str
    sound: str
    sold_foods: set[str] = field(default_factory=set)
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
class Offering:
    id: str
    label: str
    phrase: str
    sprinkle: str
    suitable: bool = False
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
class Approach:
    id: str
    label: str
    noise: int
    patient: bool
    opening: str
    correction: str
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
class Memory:
    id: str
    cue: str
    flashback: str
    lesson: str
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
class StoryParams:
    place: str
    offering: str
    approach: str
    helper: str
    child_name: str
    child_gender: str
    child_trait: str
    memory: str
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


def _r_noise_scares(world: World) -> list[str]:
    carp = world.get("carp")
    pond = world.get("pond")
    if pond.meters["noise"] < THRESHOLD:
        return []
    sig = ("noise_scares",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    carp.meters["distance"] += 1
    carp.memes["fear"] += 1
    world.get("child").memes["worry"] += 1
    return ["__carp_hid__"]


def _r_food_invites(world: World) -> list[str]:
    food = world.get("food")
    carp = world.get("carp")
    pond = world.get("pond")
    if not food.edible_for_carp:
        return []
    if food.meters["offered"] < THRESHOLD:
        return []
    if pond.meters["noise"] >= THRESHOLD:
        return []
    sig = ("food_invites",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    carp.meters["interest"] += 1
    carp.meters["distance"] = 0.0
    world.get("child").memes["hope"] += 1
    return ["__carp_gather__"]


def _r_patience_feeds(world: World) -> list[str]:
    child = world.get("child")
    carp = world.get("carp")
    if child.memes["patience"] < THRESHOLD:
        return []
    if carp.meters["interest"] < THRESHOLD:
        return []
    sig = ("patience_feeds",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    carp.meters["fed"] += 1
    child.memes["pride"] += 1
    child.memes["calm"] += 1
    return ["__carp_ate__"]


CAUSAL_RULES = [
    Rule(name="noise_scares", tag="physical", apply=_r_noise_scares),
    Rule(name="food_invites", tag="physical", apply=_r_food_invites),
    Rule(name="patience_feeds", tag="social", apply=_r_patience_feeds),
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


def suitable_offering(place: Place, offering: Offering) -> bool:
    return offering.suitable and offering.id in place.sold_foods


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for offering_id, offering in OFFERINGS.items():
            if suitable_offering(place, offering):
                combos.append((place_id, offering_id))
    return combos


def predict_nearby(world: World, offering_id: str, approach_id: str) -> dict:
    sim = world.copy()
    food = sim.get("food")
    pond = sim.get("pond")
    child = sim.get("child")
    offering = OFFERINGS[offering_id]
    approach = APPROACHES[approach_id]
    food.edible_for_carp = offering.suitable
    if approach.noise:
        pond.meters["noise"] += float(approach.noise)
    food.meters["offered"] += 1
    if approach.patient:
        child.memes["patience"] += 1
    propagate(sim, narrate=False)
    carp = sim.get("carp")
    return {
        "near": carp.meters["interest"] >= THRESHOLD and carp.meters["distance"] < THRESHOLD,
        "fear": carp.memes["fear"],
        "fed": carp.meters["fed"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"After school, {child.id} walked with {helper.label_word} to {place.label}. "
        f"{place.image} {place.sound}"
    )
    world.say(
        f"{child.id} held a paper cup in both hands and thought, "
        f'"I hope the carp come close today."'
    )


def notice_food(world: World, child: Entity, offering: Offering) -> None:
    child.memes["eagerness"] += 1
    world.say(
        f"Inside the cup were {offering.phrase}. {child.id} looked down at them and thought, "
        f'"These are so small. Maybe that means the fish will trust me."'
    )


def reach_edge(world: World, child: Entity, approach: Approach, place: Place) -> None:
    if approach.noise:
        world.get("pond").meters["noise"] += float(approach.noise)
    else:
        child.memes["calm"] += 1
    world.say(
        f"{approach.opening} at {place.edge}. "
        f'{child.id} thought, "{approach.correction}"'
    )


def startle_or_wait(world: World, child: Entity, helper: Entity, memory: Memory) -> None:
    carp = world.get("carp")
    if carp.memes["fear"] >= THRESHOLD:
        child.memes["embarrassment"] += 1
        world.say(
            f"The dark backs vanished at once. {child.id}'s chest gave a small pinch. "
            f'"Oh no," {child.id} thought. "I was too fast."'
        )
        world.say(
            f"{memory.flashback}"
        )
        child.memes["reflection"] += 1
        child.memes["patience"] += 1
        world.get("pond").meters["noise"] = 0.0
        world.say(
            f'{helper.label_word.capitalize()} did not scold. "{memory.lesson}," '
            f'{helper.pronoun()} said softly.'
        )
    else:
        child.memes["patience"] += 1
        world.say(
            f"The water only shivered in rings. A few orange mouths opened near the surface, "
            f"and {child.id} thought, \"They're waiting. I should stay quiet a little longer.\""
        )


def offer_food(world: World, child: Entity, offering: Offering) -> None:
    food = world.get("food")
    food.meters["offered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} tipped a few {offering.sprinkle} into the pond instead of throwing the whole cup. "
        f'{child.id} thought, "Little bits. Little hands. Little ripples."'
    )


def feed_scene(world: World, child: Entity) -> None:
    propagate(world, narrate=False)
    carp = world.get("carp")
    if carp.meters["fed"] >= THRESHOLD:
        world.say(
            f"Soon the carp gathered under the light, moving like slow ribbons of gold and cream. "
            f"They nibbled where the food touched the water, and {child.id} felt the tight knot inside "
            f"{child.pronoun('object')} loosen."
        )
    else:
        world.say(
            f"The pond stayed still for another breath, then one curious carp rose first, then another. "
            f"{child.id} kept waiting, and the water began to trust {child.pronoun('object')} back."
        )
        carp.meters["fed"] += 1
        child.memes["pride"] += 1
        child.memes["calm"] += 1


def close(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["warmth"] += 1
    world.say(
        f"When the cup was nearly empty, {helper.label_word} and {child.id} sat for a moment without talking. "
        f"The last circles on the pond widened and faded."
    )
    if world.facts["outcome"] == "learned":
        world.say(
            f"{child.id} leaned against {helper.label_word} and thought, "
            f'"Next time I will come to the carp the quiet way first."'
        )
    else:
        world.say(
            f"{child.id} smiled at the water and thought, "
            f'"This is my favorite part, when everything gets still and close."'
        )
    world.say(
        f"They walked home from {place.label} a little slower than they had come, "
        f"with the empty cup swinging lightly between them."
    )


def tell(
    place: Place,
    offering: Offering,
    approach: Approach,
    memory: Memory,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_type: str = "grandfather",
    child_trait: str = "thoughtful",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["little", child_trait],
        attrs={},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={},
    ))
    pond = world.add(Entity(
        id="pond",
        type="pond",
        label="pond",
        attrs={},
    ))
    carp = world.add(Entity(
        id="carp",
        type="carp",
        label="carp",
        attrs={},
    ))
    food = world.add(Entity(
        id="food",
        type="food",
        label=offering.label,
        edible_for_carp=offering.suitable,
        attrs={},
    ))

    pond.meters["noise"] = 0.0
    carp.meters["distance"] = 0.0
    carp.meters["interest"] = 0.0
    carp.meters["fed"] = 0.0
    carp.memes["fear"] = 0.0
    child.memes["eagerness"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["patience"] = 0.0
    child.memes["pride"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["embarrassment"] = 0.0
    child.memes["reflection"] = 0.0
    child.memes["warmth"] = 0.0
    food.meters["offered"] = 0.0

    predicted = predict_nearby(world, offering.id, approach.id)
    world.facts["predicted_near"] = predicted["near"]
    world.facts["predicted_fear"] = predicted["fear"]

    introduce(world, child, helper, place)
    notice_food(world, child, offering)

    world.para()
    reach_edge(world, child, approach, place)
    propagate(world, narrate=False)
    startle_or_wait(world, child, helper, memory)

    world.para()
    offer_food(world, child, offering)
    feed_scene(world, child)

    world.para()
    outcome = "learned" if approach.noise > 0 else "smooth"
    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        offering=offering,
        approach=approach,
        memory=memory,
        outcome=outcome,
        carp_fed=world.get("carp").meters["fed"] >= THRESHOLD,
    )
    close(world, child, helper, place)
    return world


PLACES = {
    "garden_pond": Place(
        id="garden_pond",
        label="the garden pond behind the tea shop",
        image="Flat stones were warm from the afternoon sun, and willow leaves touched the water.",
        edge="the mossy edge",
        sound="Somewhere behind them, cups clicked softly in the tea shop.",
        sold_foods={"pellets", "peas"},
        tags={"pond", "garden"},
    ),
    "park_pond": Place(
        id="park_pond",
        label="the little park pond",
        image="The path smelled like wet dirt, and a bench faced the water.",
        edge="the low rail by the pond",
        sound="A bicycle bell rang far away, then the whole place settled down again.",
        sold_foods={"pellets", "lettuce"},
        tags={"pond", "park"},
    ),
    "courtyard_pond": Place(
        id="courtyard_pond",
        label="the quiet courtyard pond",
        image="Square stones held the day's heat, and shadows from the maple tree lay on the water.",
        edge="the smooth stone lip",
        sound="From an upstairs window came the faint sound of someone watering plants.",
        sold_foods={"peas", "lettuce"},
        tags={"pond", "courtyard"},
    ),
}

OFFERINGS = {
    "pellets": Offering(
        id="pellets",
        label="pellets",
        phrase="brown carp pellets",
        sprinkle="pellets",
        suitable=True,
        tags={"pellets", "carp_food"},
    ),
    "peas": Offering(
        id="peas",
        label="peas",
        phrase="soft green peas",
        sprinkle="peas",
        suitable=True,
        tags={"peas", "carp_food"},
    ),
    "lettuce": Offering(
        id="lettuce",
        label="lettuce",
        phrase="torn pieces of lettuce",
        sprinkle="green pieces",
        suitable=True,
        tags={"lettuce", "carp_food"},
    ),
    "crackers": Offering(
        id="crackers",
        label="crackers",
        phrase="crumbled crackers",
        sprinkle="crumbs",
        suitable=False,
        tags={"bread"},
    ),
}

APPROACHES = {
    "crouch": Approach(
        id="crouch",
        label="crouch quietly",
        noise=0,
        patient=True,
        opening="They crouched carefully",
        correction="If I stay small and still, maybe the carp will think I belong here.",
        tags={"quiet", "patient"},
    ),
    "sit": Approach(
        id="sit",
        label="sit and wait",
        noise=0,
        patient=True,
        opening="They sat side by side",
        correction="I can wait. Waiting is part of feeding, not the boring part after it.",
        tags={"quiet", "patient"},
    ),
    "rush": Approach(
        id="rush",
        label="rush to the edge",
        noise=1,
        patient=False,
        opening="They hurried too quickly",
        correction="Maybe if I get there first, the carp will come first too.",
        tags={"noise", "impulse"},
    ),
}

MEMORIES = {
    "boot_splash": Memory(
        id="boot_splash",
        cue="a quick splash",
        flashback=(
            "At once, {name} remembered another afternoon: one careless boot had slapped the edge of the pond, "
            "and every bright shape below had slipped away like dropped silk. The memory came back whole, "
            "not loud, just clear."
        ),
        lesson="The carp need a quiet hello before they will believe in your hands",
        tags={"flashback"},
    ),
    "big_handful": Memory(
        id="big_handful",
        cue="too much food at once",
        flashback=(
            "A memory rose up in {name}'s mind: last month, a big handful had hit the water all at once, "
            "and the surface had jumped and broken apart. Even the bravest carp had kept their distance after that."
        ),
        lesson="Small bits and slow hands make the pond feel safe",
        tags={"flashback"},
    ),
}

HELPERS = {
    "grandfather": {"type": "grandfather", "tags": {"family", "grandpa"}},
    "grandmother": {"type": "grandmother", "tags": {"family", "grandma"}},
    "aunt": {"type": "aunt", "tags": {"family", "aunt"}},
}

GIRL_NAMES = ["Mina", "Aiko", "Lena", "Nora", "Sumi", "Ella", "Maya", "Rin"]
BOY_NAMES = ["Ken", "Leo", "Milo", "Taro", "Eli", "Noah", "Ben", "Sora"]
TRAITS = ["thoughtful", "curious", "gentle", "eager", "quiet"]


KNOWLEDGE = {
    "carp_food": [
        (
            "What do carp do when they feel safe near the water's edge?",
            "Carp rise slowly toward the surface when the place feels calm and safe. Sudden noise can make them turn and swim away."
        )
    ],
    "pond": [
        (
            "Why do ripples spread across a pond?",
            "Ripples spread because moving water pushes the water beside it. A small touch can make circles travel a long way."
        )
    ],
    "quiet": [
        (
            "Why does being quiet help around fish?",
            "Fish notice vibration and movement through the water. When people are quiet and gentle, the water feels less alarming to them."
        )
    ],
    "peas": [
        (
            "What is a pea?",
            "A pea is a small green vegetable seed. It is round, soft when cooked, and easy to hold in your fingers."
        )
    ],
    "pellets": [
        (
            "What are fish pellets?",
            "Fish pellets are small bits of food made for fish. They are easier and safer for pond fish than random human snacks."
        )
    ],
    "lettuce": [
        (
            "What is lettuce?",
            "Lettuce is a leafy green vegetable. Torn into small pieces, it is soft and light."
        )
    ],
}
KNOWLEDGE_ORDER = ["pond", "quiet", "carp_food", "pellets", "peas", "lettuce"]


def helper_noun(helper: Entity) -> str:
    return helper.label_word


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    offering = f["offering"]
    helper = f["helper"]
    outcome = f["outcome"]
    if outcome == "learned":
        return [
            f'Write a gentle slice-of-life story about a child feeding carp at {place.label}, using inner monologue and a short flashback.',
            f"Tell a quiet family story where {child.id} hurries, startles the carp, remembers an earlier mistake, and learns to move slowly beside {helper_noun(helper)}.",
            f'Write a story that includes the word "carp" and ends with a child understanding that patience can change the whole feeling of a small afternoon.',
        ]
    return [
        f'Write a small slice-of-life story about a child and {helper_noun(helper)} feeding carp at {place.label}, with inner monologue and a warm ending.',
        f"Tell a calm story where {child.id} waits quietly with {offering.label} and notices how the pond changes when someone is patient.",
        f'Write a story that includes the word "carp" and uses a child\'s private thoughts to make an ordinary moment feel important.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    offering = f["offering"]
    approach = f["approach"]
    outcome = f["outcome"]
    memory = f["memory"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child visiting {place.label} with {helper_noun(helper)}. Together they spend a quiet afternoon feeding carp."
        ),
        (
            "What did the child bring to the pond?",
            f"{child.id} brought {offering.phrase} in a small paper cup. The cup made the feeding feel careful and small, not wild or messy."
        ),
        (
            "What was the child thinking at the start?",
            f"{child.id} hoped the carp would come close. That inner wish made every ripple feel important."
        ),
    ]
    if outcome == "learned":
        qa.append((
            "Why did the carp hide at first?",
            f"They hid because {child.id} rushed to the edge and made the pond feel noisy. Fish pull away when sudden movement makes the water feel unsafe."
        ))
        qa.append((
            "What happened in the flashback, and why did it matter?",
            f"{child.id} remembered an earlier moment when being too quick near the pond had scared the fish away. The memory explained the problem clearly, so {child.pronoun('subject')} understood how to change."
        ))
        qa.append((
            "How did the child fix the moment?",
            f"{child.id} slowed down, stayed quiet, and offered only a few small pieces at a time. Because the water settled and the hands above it became gentle, the carp came back."
        ))
    else:
        qa.append((
            "Why did the carp come near?",
            f"They came near because {child.id} was patient and quiet from the beginning. The pond stayed calm, so the carp had no reason to hide."
        ))
        qa.append((
            "How did the child act while feeding the fish?",
            f"{child.id} waited, watched, and dropped in only a few small bits at a time. That slow rhythm helped the whole scene stay peaceful."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the cup nearly empty, the pond growing still again, and {child.id} walking home more quietly than before. The ending shows that a small afternoon changed {child.pronoun('object')} on the inside."
    ))
    if "flashback" in memory.tags:
        qa.append((
            "How did the inner monologue change during the story?",
            f"At first, {child.id}'s thoughts were full of hope and hurry. By the end, the thoughts had become calm and certain, because {child.pronoun('subject')} had learned what the carp needed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["offering"].tags) | set(f["approach"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.edible_for_carp:
            bits.append("edible_for_carp=True")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden_pond",
        offering="pellets",
        approach="rush",
        helper="grandfather",
        child_name="Mina",
        child_gender="girl",
        child_trait="eager",
        memory="boot_splash",
    ),
    StoryParams(
        place="park_pond",
        offering="lettuce",
        approach="sit",
        helper="grandmother",
        child_name="Leo",
        child_gender="boy",
        child_trait="thoughtful",
        memory="big_handful",
    ),
    StoryParams(
        place="courtyard_pond",
        offering="peas",
        approach="crouch",
        helper="aunt",
        child_name="Sumi",
        child_gender="girl",
        child_trait="gentle",
        memory="boot_splash",
    ),
]


def explain_rejection(place: Place, offering: Offering) -> str:
    if not offering.suitable:
        return (
            f"(No story: {offering.label} are not a sensible food for carp here. "
            f"Pick food meant for pond fish, like pellets, peas, or lettuce.)"
        )
    return (
        f"(No story: {place.label} does not offer {offering.label} for feeding the carp. "
        f"Choose one of the foods that belongs at this pond.)"
    )


def explain_helper(helper: str) -> str:
    return f"(No story: unknown helper '{helper}'. Choose one of: {', '.join(sorted(HELPERS))}.)"


def outcome_of(params: StoryParams) -> str:
    return "learned" if APPROACHES[params.approach].noise > 0 else "smooth"


ASP_RULES = r"""
suitable_pair(P, O) :- place(P), offering(O), suitable(O), sold_at(P, O).
valid(P, O) :- suitable_pair(P, O).

noisy(A) :- approach(A), noise(A, N), N > 0.
patient(A) :- approach(A), quiet(A).

outcome(learned) :- chosen_approach(A), noisy(A).
outcome(smooth) :- chosen_approach(A), not noisy(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, place in PLACES.items():
        for food in sorted(place.sold_foods):
            lines.append(asp.fact("sold_at", pid, food))
    for oid, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", oid))
        if offering.suitable:
            lines.append(asp.fact("suitable", oid))
    for aid, approach in APPROACHES.items():
        lines.append(asp.fact("approach", aid))
        lines.append(asp.fact("noise", aid, approach.noise))
        if approach.patient:
            lines.append(asp.fact("quiet", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_approach", params.approach)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  clingo:", sorted(set(asp_valid_combos()) - set(valid_combos())))
        print("  python:", sorted(set(valid_combos()) - set(asp_valid_combos())))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story from smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, some carp, and the small lesson of moving gently."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible place/offering pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.helper not in HELPERS:
        raise StoryError(explain_helper(args.helper))
    if args.place and args.offering:
        place = PLACES[args.place]
        offering = OFFERINGS[args.offering]
        if not suitable_offering(place, offering):
            raise StoryError(explain_rejection(place, offering))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.offering is None or c[1] == args.offering)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, offering_id = rng.choice(sorted(combos))
    approach_id = args.approach or rng.choice(sorted(APPROACHES))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    trait = rng.choice(TRAITS)
    memory_id = rng.choice(sorted(MEMORIES))
    return StoryParams(
        place=place_id,
        offering=offering_id,
        approach=approach_id,
        helper=helper_id,
        child_name=name,
        child_gender=gender,
        child_trait=trait,
        memory=memory_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(No story: unknown offering '{params.offering}'.)")
    if params.approach not in APPROACHES:
        raise StoryError(f"(No story: unknown approach '{params.approach}'.)")
    if params.helper not in HELPERS:
        raise StoryError(explain_helper(params.helper))
    if params.memory not in MEMORIES:
        raise StoryError(f"(No story: unknown memory '{params.memory}'.)")

    place = PLACES[params.place]
    offering = OFFERINGS[params.offering]
    if not suitable_offering(place, offering):
        raise StoryError(explain_rejection(place, offering))

    helper_type = HELPERS[params.helper]["type"]
    memory = MEMORIES[params.memory]
    memory = Memory(
        id=memory.id,
        cue=memory.cue,
        flashback=memory.flashback.format(name=params.child_name),
        lesson=memory.lesson,
        tags=set(memory.tags),
    )

    world = tell(
        place=place,
        offering=offering,
        approach=APPROACHES[params.approach],
        memory=memory,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=helper_type,
        child_trait=params.child_trait,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, offering) pairs:\n")
        for place, offering in combos:
            print(f"  {place:15} {offering}")
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
            header = (
                f"### {p.child_name}: {p.offering} at {p.place} "
                f"({p.approach}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
