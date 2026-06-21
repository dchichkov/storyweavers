#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/contract_surprise_fairy_tale.py
==========================================================

A standalone storyworld for a tiny fairy-tale domain built around a magical
contract and a surprise ending.

Premise
-------
A child meets a fairy beside a thirsty enchanted plant. The fairy offers a
small contract: if the child carries enough water before moonrise, the plant
will bloom and reveal a surprise. The child needs a vessel and, in harder
places, a helpful woodland friend. The world model decides whether the chosen
vessel and helper can honestly satisfy the contract.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of results.py shared containers
- typed entities with physical meters and emotional memes
- Python reasonableness checks plus an inline ASP twin
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  and --show-asp

Run it
------
python storyworlds/worlds/gpt-5.4/contract_surprise_fairy_tale.py
python storyworlds/worlds/gpt-5.4/contract_surprise_fairy_tale.py --place rose_garden --plant moonflower
python storyworlds/worlds/gpt-5.4/contract_surprise_fairy_tale.py --vessel acorn_cap
python storyworlds/worlds/gpt-5.4/contract_surprise_fairy_tale.py --helper robin
python storyworlds/worlds/gpt-5.4/contract_surprise_fairy_tale.py --all --qa
python storyworlds/worlds/gpt-5.4/contract_surprise_fairy_tale.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "fairy_woman"}
        male = {"boy", "father", "king", "man", "fairy_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    source: str
    path: str
    moon_image: str
    challenge: int
    plants: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    thirst: int
    droop: str
    bloom: str
    surprise: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    capacity: int
    carry_text: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    bonus: int
    entrance: str
    aid_text: str
    reveal_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    plant: str
    vessel: str
    helper: str
    child_name: str
    child_gender: str
    fairy_name: str
    fairy_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_bloom(world: World) -> list[str]:
    plant = world.get("plant")
    need = int(world.facts["plant_cfg"].thirst)
    if plant.meters["water"] < need:
        return []
    sig = ("bloom", plant.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    plant.meters["blooming"] += 1
    child = world.get("child")
    fairy = world.get("fairy")
    child.memes["wonder"] += 1
    child.memes["joy"] += 1
    fairy.memes["glad"] += 1
    return ["__bloom__"]


def _r_kept_contract(world: World) -> list[str]:
    child = world.get("child")
    plant = world.get("plant")
    if child.meters["signed_contract"] < THRESHOLD or plant.meters["water"] < THRESHOLD:
        return []
    sig = ("kept", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["kept_contract"] += 1
    child.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="bloom", tag="physical", apply=_r_bloom),
    Rule(name="kept_contract", tag="social", apply=_r_kept_contract),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend([s for s in out if not s.startswith("__")])
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "rose_garden": Place(
        id="rose_garden",
        label="the rose garden behind the old gate",
        source="the marble birdbath",
        path="past the sleeping roses",
        moon_image="the moon laid a white ribbon over the petals",
        challenge=1,
        plants={"moonflower", "silver_bean"},
        tags={"garden"},
    ),
    "mossy_hill": Place(
        id="mossy_hill",
        label="the mossy hill under the bent pine",
        source="the spring at the foot of the hill",
        path="up the slippery green slope",
        moon_image="the moon rested on the hill like a silver coin",
        challenge=2,
        plants={"moonflower", "sleeping_tulip"},
        tags={"hill"},
    ),
    "castle_courtyard": Place(
        id="castle_courtyard",
        label="the quiet castle courtyard",
        source="the lion fountain",
        path="across the windy stones",
        moon_image="the moon shone in every high window",
        challenge=2,
        plants={"silver_bean", "sleeping_tulip"},
        tags={"castle"},
    ),
}

PLANTS = {
    "moonflower": Plant(
        id="moonflower",
        label="moonflower",
        phrase="a pale moonflower with folded petals",
        thirst=2,
        droop="its silver stem bowed as if it were too tired to hold up the moon",
        bloom="the moonflower opened into a round white star",
        surprise="inside the bloom sat a string of pearl-bright seeds that glowed like tiny lanterns",
        gift="a string of glowing moon seeds",
        tags={"flower", "moonflower", "surprise"},
    ),
    "silver_bean": Plant(
        id="silver_bean",
        label="silver bean vine",
        phrase="a silver bean vine curled around a little stake",
        thirst=3,
        droop="its leaves hung limp, and the little stake leaned sadly to one side",
        bloom="the silver bean vine sprang upward in one bright twist",
        surprise="from the new leaves dangled a shining bean pod full of sugared stars",
        gift="a pod of sugared stars",
        tags={"vine", "silver_bean", "surprise"},
    ),
    "sleeping_tulip": Plant(
        id="sleeping_tulip",
        label="sleeping tulip",
        phrase="a sleeping tulip wrapped tight as a secret",
        thirst=3,
        droop="its green cup was closed and heavy with sleep",
        bloom="the sleeping tulip unfolded petal by petal",
        surprise="at its heart lay a gold key no bigger than a thumbnail",
        gift="a tiny gold key",
        tags={"tulip", "sleeping_tulip", "surprise"},
    ),
}

VESSELS = {
    "acorn_cap": Vessel(
        id="acorn_cap",
        label="acorn cap",
        phrase="an acorn cap polished like a cup",
        capacity=1,
        carry_text="carefully balanced the acorn cap in both hands",
        tags={"cup"},
    ),
    "shell_cup": Vessel(
        id="shell_cup",
        label="shell cup",
        phrase="a shell cup with a pearly lip",
        capacity=2,
        carry_text="carried the shell cup as steadily as a little boat",
        tags={"shell"},
    ),
    "silver_pail": Vessel(
        id="silver_pail",
        label="silver pail",
        phrase="a silver pail no bigger than a kettle",
        capacity=3,
        carry_text="lifted the silver pail and walked with brave, slow steps",
        tags={"pail"},
    ),
}

HELPERS = {
    "mouse": Helper(
        id="mouse",
        label="field mouse",
        phrase="a field mouse in a waistcoat of clover",
        bonus=0,
        entrance="A field mouse in a waistcoat of clover peeped from the grass.",
        aid_text="trotted beside the child and squeaked warnings about the bumpiest stones",
        reveal_text="The mouse bowed so deeply that its clover waistcoat almost brushed the ground.",
        tags={"mouse"},
    ),
    "robin": Helper(
        id="robin",
        label="robin",
        phrase="a robin with a bright red breast",
        bonus=1,
        entrance="A robin with a bright red breast fluttered down from the nearest branch.",
        aid_text="flew ahead and showed the smoothest way, so not a drop splashed over the rim",
        reveal_text="The robin shook moon dust from its feathers as if it had always known the secret.",
        tags={"bird"},
    ),
    "hedgehog": Helper(
        id="hedgehog",
        label="hedgehog",
        phrase="a round hedgehog with a mossy ribbon",
        bonus=2,
        entrance="Out from under a fern came a round hedgehog with a mossy ribbon tied behind one ear.",
        aid_text="rolled under the vessel on the steepest part and carried it like a tiny cart",
        reveal_text="The hedgehog smiled, and for one blink each quill shone like a silver pin.",
        tags={"hedgehog"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nora", "Poppy", "Wren"]
BOY_NAMES = ["Oren", "Milo", "Theo", "Finn", "Rowan", "Jules"]
FAIRY_GIRL_NAMES = ["Tansy", "Lark", "Briony", "Dewdrop"]
FAIRY_BOY_NAMES = ["Aster", "Reed", "Thistle", "Clover"]
TRAITS = ["gentle", "brave", "patient", "careful", "kind", "hopeful"]


def supported(place_id: str, plant_id: str) -> bool:
    return plant_id in PLACES[place_id].plants


def delivery_amount(place_id: str, vessel_id: str, helper_id: str) -> int:
    place = PLACES[place_id]
    vessel = VESSELS[vessel_id]
    helper = HELPERS[helper_id]
    return max(0, vessel.capacity + helper.bonus - place.challenge)


def can_bloom(place_id: str, plant_id: str, vessel_id: str, helper_id: str) -> bool:
    if not supported(place_id, plant_id):
        return False
    return delivery_amount(place_id, vessel_id, helper_id) >= PLANTS[plant_id].thirst


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in sorted(PLACES):
        for plant_id in sorted(PLANTS):
            if not supported(place_id, plant_id):
                continue
            for vessel_id in sorted(VESSELS):
                if any(can_bloom(place_id, plant_id, vessel_id, helper_id) for helper_id in HELPERS):
                    combos.append((place_id, plant_id, vessel_id))
    return combos


def explain_place_plant(place_id: str, plant_id: str) -> str:
    place = PLACES[place_id]
    plant = PLANTS[plant_id]
    return (
        f"(No story: {plant.label} does not grow in {place.label}. "
        f"Choose a plant that belongs in that place so the fairy-tale world stays believable.)"
    )


def explain_helper(place_id: str, plant_id: str, vessel_id: str, helper_id: str) -> str:
    place = PLACES[place_id]
    plant = PLANTS[plant_id]
    vessel = VESSELS[vessel_id]
    helper = HELPERS[helper_id]
    delivered = delivery_amount(place_id, vessel_id, helper_id)
    return (
        f"(No story: with {vessel.phrase} and {helper.phrase}, the child could only carry "
        f"{delivered} good drop{'s' if delivered != 1 else ''} through {place.path}, but "
        f"the {plant.label} needs {plant.thirst}. Pick a stronger helper or a larger vessel.)"
    )


def predict_delivery(world: World) -> dict:
    sim = world.copy()
    place = sim.facts["place_cfg"]
    plant_cfg = sim.facts["plant_cfg"]
    vessel = sim.facts["vessel_cfg"]
    helper = sim.facts["helper_cfg"]
    amount = delivery_amount(place.id, vessel.id, helper.id)
    sim.get("plant").meters["water"] += amount
    propagate(sim, narrate=False)
    return {
        "delivered": amount,
        "bloomed": sim.get("plant").meters["blooming"] >= THRESHOLD,
    }


def sign_contract(world: World, child: Entity, fairy: Entity, plant: Entity) -> None:
    child.meters["signed_contract"] += 1
    child.memes["resolve"] += 1
    fairy.memes["hope"] += 1
    world.say(
        f'At the root of the plant lay a curled leaf with tiny silver writing. '
        f'"This is a kindness contract," {fairy.id} said. "Carry enough water to '
        f'{plant.label} before moonrise, and the garden will answer with a surprise."'
    )
    world.say(
        f"{child.id} pressed a thumb to the leaf, and a silver line twined into "
        f"{child.pronoun('possessive')} name."
    )


def introduce(world: World, child: Entity, fairy: Entity, place: Place, plant_cfg: Plant) -> None:
    world.say(
        f"Once, when the evening sky was turning blue as a plum, {child.id} wandered into "
        f"{place.label}. {place.moon_image}."
    )
    world.say(
        f"There {child.pronoun()} found {plant_cfg.phrase}, and {plant_cfg.droop}."
    )
    world.say(
        f"Beside it stood {fairy.id}, a small fairy with wings thin as onion skin and eyes bright with worry."
    )


def warning_and_prediction(world: World, child: Entity) -> None:
    pred = predict_delivery(world)
    world.facts["predicted_delivered"] = pred["delivered"]
    world.say(
        f'{child.id} looked toward the water and back again. The path seemed long, and the moon was already climbing.'
    )


def helper_arrives(world: World, helper_cfg: Helper) -> None:
    world.say(helper_cfg.entrance)


def fetch_water(world: World, child: Entity, helper_cfg: Helper, place: Place, vessel: Vessel) -> None:
    child.memes["effort"] += 1
    world.say(
        f"{child.id} dipped {vessel.phrase} into {place.source} and {vessel.carry_text} {place.path}."
    )
    if helper_cfg.bonus > 0:
        world.say(
            f"The {helper_cfg.label} {helper_cfg.aid_text}."
        )
    else:
        world.say(
            f"The {helper_cfg.label} {helper_cfg.aid_text}, though the journey was still hard."
        )


def pour_and_propagate(world: World) -> None:
    place = world.facts["place_cfg"]
    plant_cfg = world.facts["plant_cfg"]
    vessel_cfg = world.facts["vessel_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    amount = delivery_amount(place.id, vessel_cfg.id, helper_cfg.id)
    plant = world.get("plant")
    plant.meters["water"] += amount
    propagate(world, narrate=False)
    world.facts["delivered"] = amount
    world.facts["bloomed"] = plant.meters["blooming"] >= THRESHOLD
    world.facts["kept_contract"] = world.get("child").meters["kept_contract"] >= THRESHOLD
    world.say(
        f"{child_name(world)} poured {amount} shining drop{'s' if amount != 1 else ''} at the root."
    )
    if world.facts["bloomed"]:
        world.say(plant_cfg.bloom + ".")
    else:
        world.say(
            f"But the {plant_cfg.label} only trembled. It was not enough before the moon reached the wall."
        )


def surprise_ending(world: World, child: Entity, fairy: Entity, helper_cfg: Helper, plant_cfg: Plant) -> None:
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    fairy.memes["glad"] += 1
    world.say(
        f"Then came the surprise: {plant_cfg.surprise}."
    )
    world.say(
        f'"You kept the contract," {fairy.id} said, smiling. "The gift was promised to a faithful heart."'
    )
    world.say(helper_cfg.reveal_text)
    world.say(
        f"{fairy.id} placed {plant_cfg.gift} in {child.pronoun('possessive')} hands, "
        f"and all at once the whole place looked less lonely than before."
    )


def gentle_failure(world: World, child: Entity, fairy: Entity, plant_cfg: Plant) -> None:
    child.memes["sadness"] += 1
    fairy.memes["kindness"] += 1
    world.say(
        f'{fairy.id} touched {child.pronoun("possessive")} sleeve. "The contract was brave, and brave things are not always easy the first time," '
        f'{fairy.pronoun()} said.'
    )
    world.say(
        f"Before {child.id} could answer, the fairy folded the silver leaf into {child.pronoun('possessive')} palm. "
        f'"Keep it," {fairy.pronoun()} whispered. "Tomorrow, we begin again."'
    )
    world.say(
        f"So {child.id} walked home under the moon with the little contract safe in one hand, already planning how to help {plant_cfg.label} at dawn."
    )


def child_name(world: World) -> str:
    return world.get("child").id


def tell(
    place: Place,
    plant_cfg: Plant,
    vessel_cfg: Vessel,
    helper_cfg: Helper,
    child_name_value: str,
    child_gender: str,
    fairy_name_value: str,
    fairy_gender: str,
    trait: str,
    parent_type: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name_value,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            label=child_name_value,
            attrs={"parent": parent_type},
        )
    )
    fairy = world.add(
        Entity(
            id=fairy_name_value,
            kind="character",
            type=fairy_gender,
            role="fairy",
            label=fairy_name_value,
            tags={"fairy"},
        )
    )
    plant = world.add(
        Entity(
            id="plant",
            kind="thing",
            type="plant",
            label=plant_cfg.label,
            phrase=plant_cfg.phrase,
            tags=set(plant_cfg.tags),
        )
    )
    vessel = world.add(
        Entity(
            id="vessel",
            kind="thing",
            type="vessel",
            label=vessel_cfg.label,
            phrase=vessel_cfg.phrase,
            tags=set(vessel_cfg.tags),
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="animal",
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            role="helper",
            tags=set(helper_cfg.tags),
        )
    )

    world.facts.update(
        place_cfg=place,
        plant_cfg=plant_cfg,
        vessel_cfg=vessel_cfg,
        helper_cfg=helper_cfg,
        child=child,
        fairy=fairy,
        plant=plant,
        vessel=vessel,
        helper=helper,
        parent_type=parent_type,
        trait=trait,
    )

    introduce(world, child, fairy, place, plant_cfg)
    world.para()
    sign_contract(world, child, fairy, plant)
    warning_and_prediction(world, child)
    helper_arrives(world, helper_cfg)
    world.para()
    fetch_water(world, child, helper_cfg, place, vessel_cfg)
    pour_and_propagate(world)
    world.para()

    if world.facts["bloomed"]:
        surprise_ending(world, child, fairy, helper_cfg, plant_cfg)
        outcome = "bloomed"
    else:
        gentle_failure(world, child, fairy, plant_cfg)
        outcome = "promise_kept_but_unfinished"

    world.facts["outcome"] = outcome
    return world


KNOWLEDGE = {
    "contract": [
        (
            "What is a contract?",
            "A contract is a promise that people agree to keep. In stories, it can be written down or sealed in a special way so everyone remembers the promise."
        )
    ],
    "fairy": [
        (
            "What is a fairy in a fairy tale?",
            "A fairy is a tiny magical being who can help, test, or guide someone. Fairies in tales often reward kindness and honesty."
        )
    ],
    "moonflower": [
        (
            "Why do some flowers open at night?",
            "Some flowers open when the air grows cooler and the light changes. Night-blooming flowers are part of many fairy tales because moonlight makes them feel magical."
        )
    ],
    "silver_bean": [
        (
            "What is a vine?",
            "A vine is a plant with long stems that twist and climb. It often needs a stick, wall, or fence to help it grow upward."
        )
    ],
    "sleeping_tulip": [
        (
            "Why might a flower stay closed?",
            "A flower may stay closed when it is too cold, too dark, or not ready yet. In a fairy tale, a closed flower can also stand for a secret waiting to be found."
        )
    ],
    "shell": [
        (
            "What is a shell cup?",
            "A shell cup is a small cup made from a shell. It would only hold a little water, so someone would have to carry it very carefully."
        )
    ],
    "pail": [
        (
            "What is a pail?",
            "A pail is a little bucket used for carrying things like water. A larger pail can carry more water than a tiny cup."
        )
    ],
    "bird": [
        (
            "How can a bird help someone find a path?",
            "A bird can fly ahead and show the safest way to go. In stories, that kind of helper keeps a traveler from getting lost or spilling something important."
        )
    ],
    "hedgehog": [
        (
            "What is a hedgehog?",
            "A hedgehog is a small animal with many little spines on its back. In fairy tales, hedgehogs are often shown as quiet helpers who are wiser than they first seem."
        )
    ],
    "mouse": [
        (
            "Why do fairy tales use mice as helpers?",
            "Mice are tiny, quick, and good at slipping through hidden places. A fairy tale likes to show that even a very small helper can matter."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "contract",
    "fairy",
    "moonflower",
    "silver_bean",
    "sleeping_tulip",
    "shell",
    "pail",
    "bird",
    "hedgehog",
    "mouse",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    fairy = world.facts["fairy"]
    plant_cfg = world.facts["plant_cfg"]
    place = world.facts["place_cfg"]
    return [
        (
            f'Write a short fairy tale for a 3-to-5-year-old that includes the word "contract" '
            f"and ends with a surprise gift."
        ),
        (
            f"Tell a fairy-tale story where {child.id} meets {fairy.id} in {place.label}, "
            f"agrees to a kindness contract, and helps a thirsty {plant_cfg.label} before moonrise."
        ),
        (
            f"Write a gentle magical story in which a child keeps a promise, a plant blooms, "
            f"and the ending reveals a surprise."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    fairy = world.facts["fairy"]
    place = world.facts["place_cfg"]
    plant_cfg = world.facts["plant_cfg"]
    vessel_cfg = world.facts["vessel_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    delivered = world.facts.get("delivered", 0)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who meets the fairy {fairy.id} beside a thirsty {plant_cfg.label}. Their meeting turns into a promise that must be kept before moonrise."
        ),
        (
            "What was the contract?",
            f"The contract was a promise to carry enough water to the {plant_cfg.label} before moonrise. If the promise was kept, the garden would answer with a surprise."
        ),
        (
            f"Why did {child.id} need help?",
            f"{child.id} had to carry water from {place.source} along {place.path}. That was hard because the path could make precious drops spill away."
        ),
        (
            f"How did the {helper_cfg.label} help?",
            f"The {helper_cfg.label} helped while {child.id} carried {vessel_cfg.phrase}. Because of that help, {delivered} shining drop{'s' if delivered != 1 else ''} reached the root instead of being lost on the way."
        ),
    ]
    if world.facts["outcome"] == "bloomed":
        qa.append(
            (
                "What was the surprise at the end?",
                f"The surprise was that {plant_cfg.surprise}. It proved that the contract had truly been kept and that kindness changed the place."
            )
        )
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt proud and full of wonder. The blooming plant and the promised gift showed that the hard work had mattered."
            )
        )
    else:
        qa.append(
            (
                "Did the child give up?",
                f"No. The plant had not bloomed yet, but {child.id} kept the contract leaf and planned to try again at dawn. The ending is gentle because the promise still matters even before the reward arrives."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    plant_cfg = world.facts["plant_cfg"]
    vessel_cfg = world.facts["vessel_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    tags = {"contract", "fairy"} | set(plant_cfg.tags) | set(vessel_cfg.tags) | set(helper_cfg.tags)
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
    for ent in world.entities.values():
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="rose_garden",
        plant="moonflower",
        vessel="shell_cup",
        helper="robin",
        child_name="Lina",
        child_gender="girl",
        fairy_name="Tansy",
        fairy_gender="girl",
        parent="mother",
        trait="kind",
    ),
    StoryParams(
        place="mossy_hill",
        plant="sleeping_tulip",
        vessel="shell_cup",
        helper="hedgehog",
        child_name="Theo",
        child_gender="boy",
        fairy_name="Reed",
        fairy_gender="boy",
        parent="father",
        trait="brave",
    ),
    StoryParams(
        place="castle_courtyard",
        plant="silver_bean",
        vessel="silver_pail",
        helper="mouse",
        child_name="Mira",
        child_gender="girl",
        fairy_name="Aster",
        fairy_gender="boy",
        parent="mother",
        trait="patient",
    ),
    StoryParams(
        place="castle_courtyard",
        plant="sleeping_tulip",
        vessel="silver_pail",
        helper="robin",
        child_name="Finn",
        child_gender="boy",
        fairy_name="Lark",
        fairy_gender="girl",
        parent="father",
        trait="careful",
    ),
]


ASP_RULES = r"""
supported(P,L) :- grows(P,L).

deliverable(P,V,H,N) :- place(P), vessel(V), helper(H),
                        capacity(V,C), bonus(H,B), challenge(P,D), N = C + B - D, N >= 0.
deliverable(P,V,H,0) :- place(P), vessel(V), helper(H),
                        capacity(V,C), bonus(H,B), challenge(P,D), C + B - D < 0.

can_bloom(P,L,V,H) :- supported(P,L), deliverable(P,V,H,N), thirst(L,T), N >= T.
valid(P,L,V) :- supported(P,L), vessel(V), helper(H), can_bloom(P,L,V,H).

chosen_outcome(bloomed) :- chosen_place(P), chosen_plant(L), chosen_vessel(V), chosen_helper(H), can_bloom(P,L,V,H).
chosen_outcome(promise_kept_but_unfinished) :- chosen_place(P), chosen_plant(L), chosen_vessel(V), chosen_helper(H), not can_bloom(P,L,V,H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("challenge", place_id, place.challenge))
        for plant_id in sorted(place.plants):
            lines.append(asp.fact("grows", place_id, plant_id))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        lines.append(asp.fact("thirst", plant_id, plant.thirst))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        lines.append(asp.fact("capacity", vessel_id, vessel.capacity))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("bonus", helper_id, helper.bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_can_bloom(place_id: str, plant_id: str, vessel_id: str, helper_id: str) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", place_id),
            asp.fact("chosen_plant", plant_id),
            asp.fact("chosen_vessel", vessel_id),
            asp.fact("chosen_helper", helper_id),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show chosen_outcome/1."))
    atoms = asp.atoms(model, "chosen_outcome")
    if not atoms:
        return False
    return atoms[0][0] == "bloomed"


def outcome_of(params: StoryParams) -> str:
    return "bloomed" if can_bloom(params.place, params.plant, params.vessel, params.helper) else "promise_kept_but_unfinished"


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

    scenarios = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    mismatches = []
    for params in scenarios:
        py_ok = outcome_of(params) == "bloomed"
        asp_ok = asp_can_bloom(params.place, params.plant, params.vessel, params.helper)
        if py_ok != asp_ok:
            mismatches.append(params)
    if not mismatches:
        print(f"OK: outcome model matches on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome disagreements.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a fairy-tale contract, a thirsty enchanted plant, and a surprise ending."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--plant", choices=sorted(PLANTS))
    ap.add_argument("--vessel", choices=sorted(VESSELS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, fairy: bool = False) -> str:
    if fairy:
        pool = FAIRY_GIRL_NAMES if gender == "girl" else FAIRY_BOY_NAMES
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.plant and not supported(args.place, args.plant):
        raise StoryError(explain_place_plant(args.place, args.plant))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.plant is None or combo[1] == args.plant)
        and (args.vessel is None or combo[2] == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, plant_id, vessel_id = rng.choice(sorted(combos))

    if args.helper is not None:
        helper_id = args.helper
        if not can_bloom(place_id, plant_id, vessel_id, helper_id):
            raise StoryError(explain_helper(place_id, plant_id, vessel_id, helper_id))
    else:
        possible_helpers = [hid for hid in sorted(HELPERS) if can_bloom(place_id, plant_id, vessel_id, hid)]
        if not possible_helpers:
            raise StoryError("(No helper can honestly complete the contract for these choices.)")
        helper_id = rng.choice(possible_helpers)

    child_gender = rng.choice(["girl", "boy"])
    fairy_gender = rng.choice(["girl", "boy"])
    child_name_value = _pick_name(rng, child_gender, fairy=False)
    fairy_name_value = _pick_name(rng, fairy_gender, fairy=True)
    if fairy_name_value == child_name_value:
        fairy_name_value = _pick_name(rng, "girl" if fairy_gender == "boy" else "boy", fairy=True)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        plant=plant_id,
        vessel=vessel_id,
        helper=helper_id,
        child_name=child_name_value,
        child_gender=child_gender,
        fairy_name=fairy_name_value,
        fairy_gender=fairy_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if not supported(params.place, params.plant):
        raise StoryError(explain_place_plant(params.place, params.plant))
    if not can_bloom(params.place, params.plant, params.vessel, params.helper):
        raise StoryError(explain_helper(params.place, params.plant, params.vessel, params.helper))

    world = tell(
        place=PLACES[params.place],
        plant_cfg=PLANTS[params.plant],
        vessel_cfg=VESSELS[params.vessel],
        helper_cfg=HELPERS[params.helper],
        child_name_value=params.child_name,
        child_gender=params.child_gender,
        fairy_name_value=params.fairy_name,
        fairy_gender=params.fairy_gender,
        trait=params.trait,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show chosen_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, plant, vessel) combos:\n")
        for place_id, plant_id, vessel_id in combos:
            helpers = [hid for hid in sorted(HELPERS) if can_bloom(place_id, plant_id, vessel_id, hid)]
            print(f"  {place_id:17} {plant_id:15} {vessel_id:12} [{', '.join(helpers)}]")
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
            try:
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
                f"### {p.child_name}: {p.plant} in {p.place} "
                f"({p.vessel}, {p.helper}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
