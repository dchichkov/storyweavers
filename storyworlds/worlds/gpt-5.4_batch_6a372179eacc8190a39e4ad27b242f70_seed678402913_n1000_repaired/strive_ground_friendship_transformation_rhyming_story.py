#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/strive_ground_friendship_transformation_rhyming_story.py
===================================================================================

A standalone story world for a rhyming friendship tale about two children who
find a tiny seed on the ground and work together to help it transform into a
flower.

The domain is intentionally small and constraint-checked:

- a seed can only be planted in ground that can really grow it
- the chosen helper must be sensible and strong enough for that ground
- the story's change is simulated as world state:
  seed on ground -> buried -> watered -> rooted -> sprouted -> bloomed
- friendship matters because the two children strive together, and the prose
  changes when the ground is stubborn enough to need a shared effort

Run it
------
    python storyworlds/worlds/gpt-5.4/strive_ground_friendship_transformation_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/strive_ground_friendship_transformation_rhyming_story.py --ground clay_corner --helper hand_spade
    python storyworlds/worlds/gpt-5.4/strive_ground_friendship_transformation_rhyming_story.py --ground stone_path
    python storyworlds/worlds/gpt-5.4/strive_ground_friendship_transformation_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/strive_ground_friendship_transformation_rhyming_story.py --verify
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
SENSE_MIN = 2
FRIEND_BONUS = 1


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
    growable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class SeedKind:
    id: str
    label: str
    phrase: str
    bloom: str
    color: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GroundKind:
    id: str
    label: str
    phrase: str
    hardness: int
    growable: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    dig_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sunshine: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "friend"]

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
        clone.sunshine = self.sunshine
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_root(world: World) -> list[str]:
    seed = world.get("seed")
    ground = world.get("ground")
    if seed.meters["buried"] < THRESHOLD or seed.meters["watered"] < THRESHOLD:
        return []
    if not ground.growable:
        return []
    sig = ("root",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seed.meters["rooted"] += 1
    for child in world.children():
        child.memes["hope"] += 1
    return []


def _r_sprout(world: World) -> list[str]:
    seed = world.get("seed")
    if seed.meters["rooted"] < THRESHOLD or world.sunshine < THRESHOLD:
        return []
    sig = ("sprout",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seed.meters["sprouted"] += 1
    for child in world.children():
        child.memes["wonder"] += 1
    return []


def _r_bloom(world: World) -> list[str]:
    seed = world.get("seed")
    if seed.meters["sprouted"] < THRESHOLD:
        return []
    teamwork = sum(child.memes["care"] for child in world.children())
    if teamwork < 2.0:
        return []
    sig = ("bloom",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seed.meters["bloomed"] += 1
    for child in world.children():
        child.memes["friendship"] += 1
        child.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="root", tag="physical", apply=_r_root),
    Rule(name="sprout", tag="physical", apply=_r_sprout),
    Rule(name="bloom", tag="social", apply=_r_bloom),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
            if out or any(sig[0] == rule.name for sig in world.fired):
                pass
        current = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        if len(world.fired) > current:
            changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SEEDS = {
    "sunflower": SeedKind(
        id="sunflower",
        label="sunflower seed",
        phrase="a striped sunflower seed",
        bloom="sunflower",
        color="golden",
        tags={"seed", "flower", "sunflower"},
    ),
    "bean": SeedKind(
        id="bean",
        label="bean seed",
        phrase="a little bean seed",
        bloom="bean vine blossom",
        color="white",
        tags={"seed", "flower", "bean"},
    ),
    "tulip": SeedKind(
        id="tulip",
        label="tulip bulb",
        phrase="a tiny tulip bulb",
        bloom="tulip",
        color="red",
        tags={"seed", "flower", "tulip"},
    ),
}

GROUNDS = {
    "garden_patch": GroundKind(
        id="garden_patch",
        label="garden patch",
        phrase="a soft garden patch",
        hardness=1,
        growable=True,
        tags={"soil", "garden"},
    ),
    "window_box": GroundKind(
        id="window_box",
        label="window box",
        phrase="a crumbly window box",
        hardness=1,
        growable=True,
        tags={"soil", "garden"},
    ),
    "clay_corner": GroundKind(
        id="clay_corner",
        label="clay corner",
        phrase="a sticky clay corner",
        hardness=2,
        growable=True,
        tags={"soil", "clay"},
    ),
    "root_bank": GroundKind(
        id="root_bank",
        label="root bank",
        phrase="a root-tangled bank by the fence",
        hardness=3,
        growable=True,
        tags={"soil", "roots"},
    ),
    "stone_path": GroundKind(
        id="stone_path",
        label="stone path",
        phrase="a flat stone path",
        hardness=3,
        growable=False,
        tags={"stone"},
    ),
}

HELPERS = {
    "fingers": Helper(
        id="fingers",
        label="fingers",
        phrase="their careful fingers",
        power=0,
        sense=3,
        dig_text="knelt and scooped a little hollow with their careful fingers",
        qa_text="used their careful fingers to make a little hole",
        tags={"digging", "hands"},
    ),
    "wooden_spoon": Helper(
        id="wooden_spoon",
        label="wooden spoon",
        phrase="a wooden spoon",
        power=1,
        sense=2,
        dig_text="borrowed a wooden spoon and scraped a neat little nest in the dirt",
        qa_text="used a wooden spoon to scrape a neat little hole",
        tags={"digging", "spoon"},
    ),
    "hand_spade": Helper(
        id="hand_spade",
        label="hand spade",
        phrase="a hand spade",
        power=2,
        sense=3,
        dig_text="fetched a hand spade and pressed it down together until the earth gave way",
        qa_text="used a hand spade together until the earth gave way",
        tags={"digging", "spade"},
    ),
    "toy_hammer": Helper(
        id="toy_hammer",
        label="toy hammer",
        phrase="a toy hammer",
        power=0,
        sense=1,
        dig_text="tapped at the dirt with a toy hammer",
        qa_text="tapped at the dirt with a toy hammer",
        tags={"toy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Theo"]
TRAITS = ["gentle", "curious", "patient", "bright", "careful", "kind"]


def helper_can_open_ground(helper: Helper, ground: GroundKind) -> bool:
    return helper.power + FRIEND_BONUS >= ground.hardness


def valid_combo(seed_id: str, ground_id: str, helper_id: str) -> bool:
    if seed_id not in SEEDS or ground_id not in GROUNDS or helper_id not in HELPERS:
        return False
    ground = GROUNDS[ground_id]
    helper = HELPERS[helper_id]
    return ground.growable and helper.sense >= SENSE_MIN and helper_can_open_ground(helper, ground)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for seed_id in sorted(SEEDS):
        for ground_id in sorted(GROUNDS):
            for helper_id in sorted(HELPERS):
                if valid_combo(seed_id, ground_id, helper_id):
                    combos.append((seed_id, ground_id, helper_id))
    return combos


@dataclass
class StoryParams:
    seed: str
    ground: str
    helper: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    parent: str
    trait1: str
    trait2: str
    seed_value_word: str = "little"
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        seed="sunflower",
        ground="garden_patch",
        helper="fingers",
        friend1="Lily",
        friend1_gender="girl",
        friend2="Ben",
        friend2_gender="boy",
        parent="mother",
        trait1="gentle",
        trait2="curious",
        seed_value_word="tiny",
    ),
    StoryParams(
        seed="tulip",
        ground="clay_corner",
        helper="wooden_spoon",
        friend1="Mia",
        friend1_gender="girl",
        friend2="Zoe",
        friend2_gender="girl",
        parent="father",
        trait1="patient",
        trait2="kind",
        seed_value_word="sleepy",
    ),
    StoryParams(
        seed="bean",
        ground="root_bank",
        helper="hand_spade",
        friend1="Max",
        friend1_gender="boy",
        friend2="Anna",
        friend2_gender="girl",
        parent="mother",
        trait1="bright",
        trait2="careful",
        seed_value_word="small",
    ),
]


KNOWLEDGE = {
    "seed": [
        (
            "What is a seed?",
            "A seed is a tiny beginning for a plant. With soil, water, and sunlight, it can grow into something bigger.",
        )
    ],
    "soil": [
        (
            "Why do plants need soil or good ground?",
            "Good ground helps hold a plant's roots, water, and food. Hard stone is not a good place for most seeds to grow.",
        )
    ],
    "garden": [
        (
            "What is a garden patch?",
            "A garden patch is a place with soft soil where flowers or vegetables can grow. It is much easier to plant in than stone.",
        )
    ],
    "clay": [
        (
            "Why is clay ground hard to dig?",
            "Clay can feel sticky and packed tight. Sometimes it takes more effort or a better tool to open a little space in it.",
        )
    ],
    "roots": [
        (
            "Why can roots in the ground make digging harder?",
            "Old roots weave through the soil like strings. They can block a small hole and make the earth harder to open.",
        )
    ],
    "digging": [
        (
            "Why do people dig a little hole for a seed?",
            "A seed needs to be tucked into the ground so it can stay safe, drink water, and send roots down. A shallow hole gives it a good start.",
        )
    ],
    "spade": [
        (
            "What is a hand spade?",
            "A hand spade is a small garden tool for digging. Grown-ups and children can use it carefully together in soft dirt.",
        )
    ],
    "flower": [
        (
            "How does a plant transform from a seed to a flower?",
            "First a seed sends out roots, then a sprout rises up, and later buds or petals open. It changes step by step as it grows.",
        )
    ],
    "friendship": [
        (
            "How can friendship help with a hard job?",
            "Friends can share the work, cheer each other on, and keep trying together. A job that feels tough alone can feel possible side by side.",
        )
    ],
}
KNOWLEDGE_ORDER = ["seed", "soil", "garden", "clay", "roots", "digging", "spade", "flower", "friendship"]


def explain_rejection(seed_cfg: SeedKind, ground_cfg: GroundKind, helper_cfg: Helper) -> str:
    if not ground_cfg.growable:
        return (
            f"(No story: {ground_cfg.phrase} is not a place where {seed_cfg.label} can really grow. "
            "The children need real soil, not stone, for the transformation to make sense.)"
        )
    if helper_cfg.sense < SENSE_MIN:
        return (
            f"(Refusing helper '{helper_cfg.id}': {helper_cfg.label} is too weak or silly for careful planting "
            f"(sense={helper_cfg.sense} < {SENSE_MIN}). Pick a more sensible helper.)"
        )
    if not helper_can_open_ground(helper_cfg, ground_cfg):
        return (
            f"(No story: {helper_cfg.label} cannot open {ground_cfg.label} well enough. "
            "The friends need a helper strong enough for that ground.)"
        )
    return "(No valid combination matches the given options.)"


def opening_rhyme(world: World, a: Entity, b: Entity, seed_cfg: SeedKind) -> None:
    for child in (a, b):
        child.memes["friendship"] += 1
        child.memes["care"] += 0.5
    world.say(
        f"{a.id} and {b.id} were friends who liked to wander round; "
        f"one bright morning they found {seed_cfg.phrase} resting on the ground."
    )
    world.say(
        f'"A little life is waiting here," said {a.id} with gentle pride; '
        f'"Let\'s help it strive instead of letting it hide."'
    )


def inspect_seed(world: World, a: Entity, b: Entity, seed_cfg: SeedKind, ground_cfg: GroundKind) -> None:
    world.say(
        f"{b.id} brushed away a pebble and looked with patient eyes; "
        f"\"It cannot bloom on bare old ground, no matter how it tries.\""
    )
    world.say(
        f"So they searched for {ground_cfg.phrase}, a kinder place to grow; "
        f"they wanted roots to tuck in deep and leaves to rise and show."
    )


def stubborn_ground_turn(world: World, a: Entity, b: Entity, ground_cfg: GroundKind) -> None:
    if ground_cfg.hardness < 2:
        return
    world.say(
        f"But {ground_cfg.label} held on tight and would not open fast; "
        f"the first small push made {a.id} sigh, \"This stubborn dirt may last.\""
    )
    world.say(
        f"{b.id} gave a nod and took {a.pronoun('possessive')} hand. "
        f"\"We strive much better side by side; together we will stand.\""
    )
    a.memes["strive"] += 1
    b.memes["strive"] += 1
    a.memes["care"] += 0.5
    b.memes["care"] += 0.5


def dig_and_plant(world: World, a: Entity, b: Entity, helper_cfg: Helper, ground_cfg: GroundKind) -> None:
    ground = world.get("ground")
    seed = world.get("seed")
    ground.meters["opened"] += 1
    world.say(
        f"They {helper_cfg.dig_text}; the earth grew loose and brown. "
        f"They made a tiny bed so the waiting seed could settle down."
    )
    seed.meters["buried"] += 1
    a.memes["care"] += 0.5
    b.memes["care"] += 0.5
    world.facts["planted"] = True


def water_seed(world: World, a: Entity, b: Entity) -> None:
    seed = world.get("seed")
    seed.meters["watered"] += 1
    a.memes["hope"] += 0.5
    b.memes["hope"] += 0.5
    world.say(
        f"{a.id} poured a cup of water light, and {b.id} patted the mound; "
        "a silver sip went slipping in and darkened all the ground."
    )


def shine(world: World) -> None:
    world.sunshine += 1
    world.say(
        "Then sunlight stitched the afternoon with warm and golden thread; "
        "the quiet patch looked still at first, as if the wish had fled."
    )


def transform(world: World, seed_cfg: SeedKind, a: Entity, b: Entity) -> None:
    propagate(world)
    if world.get("seed").meters["rooted"] >= THRESHOLD:
        world.say(
            "Under the soil, fine roots took hold where hidden dreams belong; "
            "the tiny seed was changing there, unseen yet growing strong."
        )
    if world.get("seed").meters["sprouted"] >= THRESHOLD:
        world.say(
            "Soon up there poked a tender sprout, so green and slim and bright; "
            f"{a.id} laughed, and {b.id} clapped twice at such a lovely sight."
        )
    if world.get("seed").meters["bloomed"] >= THRESHOLD:
        world.say(
            f"By evening stood a {seed_cfg.color} {seed_cfg.bloom}, smiling to the sky; "
            "what once had slept upon the ground now lifted petals high."
        )


def closing(world: World, a: Entity, b: Entity, seed_cfg: SeedKind) -> None:
    world.say(
        f'"We helped it change, and we changed too," said {b.id} with happy cheer; '
        "for friendship grows in kindly work when helping hands stay near."
    )
    world.say(
        f"So whenever they passed that blooming place, they grinned and slowed their pace; "
        f"they remembered how a little strive had filled the yard with grace."
    )
    world.facts["ending_image"] = f"a {seed_cfg.color} {seed_cfg.bloom} standing where the seed once lay on the ground"


def tell(
    seed_cfg: SeedKind,
    ground_cfg: GroundKind,
    helper_cfg: Helper,
    *,
    friend1: str,
    friend1_gender: str,
    friend2: str,
    friend2_gender: str,
    parent: str,
    trait1: str,
    trait2: str,
    seed_value_word: str,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=friend1,
            kind="character",
            type=friend1_gender,
            label=friend1,
            role="friend",
            traits=[trait1],
        )
    )
    b = world.add(
        Entity(
            id=friend2,
            kind="character",
            type=friend2_gender,
            label=friend2,
            role="friend",
            traits=[trait2],
        )
    )
    caretaker = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent,
            label="the parent",
            role="adult",
        )
    )
    ground = world.add(
        Entity(
            id="ground",
            type="ground",
            label=ground_cfg.label,
            phrase=ground_cfg.phrase,
            growable=ground_cfg.growable,
            attrs={"hardness": ground_cfg.hardness},
            tags=set(ground_cfg.tags),
        )
    )
    seed = world.add(
        Entity(
            id="seed",
            type="seed",
            label=seed_cfg.label,
            phrase=f"{seed_value_word} {seed_cfg.label}",
            tags=set(seed_cfg.tags),
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            type="tool",
            label=helper_cfg.label,
            phrase=helper_cfg.phrase,
            attrs={"power": helper_cfg.power, "sense": helper_cfg.sense},
            tags=set(helper_cfg.tags),
        )
    )

    world.facts.update(
        seed_cfg=seed_cfg,
        ground_cfg=ground_cfg,
        helper_cfg=helper_cfg,
        friend1=a,
        friend2=b,
        parent=caretaker,
        seed_value_word=seed_value_word,
    )

    opening_rhyme(world, a, b, seed_cfg)
    inspect_seed(world, a, b, seed_cfg, ground_cfg)

    world.para()
    stubborn_ground_turn(world, a, b, ground_cfg)
    dig_and_plant(world, a, b, helper_cfg, ground_cfg)
    water_seed(world, a, b)

    world.para()
    shine(world)
    propagate(world)
    transform(world, seed_cfg, a, b)
    closing(world, a, b, seed_cfg)

    world.facts.update(
        rooted=seed.meters["rooted"] >= THRESHOLD,
        sprouted=seed.meters["sprouted"] >= THRESHOLD,
        bloomed=seed.meters["bloomed"] >= THRESHOLD,
        friendship_grew=a.memes["friendship"] > 1.0 or b.memes["friendship"] > 1.0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    seed_cfg = f["seed_cfg"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that uses the words "strive" and "ground" and ends with a {seed_cfg.bloom}.',
        f"Tell a gentle friendship story where {a.id} and {b.id} find {seed_cfg.phrase} on the ground and help it transform into a flower.",
        "Write a child-facing rhyming tale where two friends work together, keep trying kindly, and prove their friendship through a growing change.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    seed_cfg = f["seed_cfg"]
    ground_cfg = f["ground_cfg"]
    helper_cfg = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, who found {seed_cfg.phrase} on the ground. They decided to care for it together.",
        ),
        (
            "Why did the friends help the seed?",
            f"They could see the seed would not bloom if it stayed on bare ground. So they chose to strive together and give it a real place to grow.",
        ),
        (
            f"How did {a.id} and {b.id} plant the seed?",
            f"They {helper_cfg.qa_text} in {ground_cfg.phrase}. Then they tucked the seed in, watered it, and waited for the change to begin.",
        ),
    ]
    if ground_cfg.hardness >= 2:
        qa.append(
            (
                "What was the hard part in the middle of the story?",
                f"The {ground_cfg.label} was stubborn and did not open easily. The friends kept working side by side, and their teamwork helped them keep going.",
            )
        )
    if f.get("bloomed"):
        qa.append(
            (
                "What transformed in the story?",
                f"The seed transformed step by step into a flower. First it settled under the ground, then it rooted and sprouted, and by evening it bloomed.",
            )
        )
        qa.append(
            (
                "How did friendship matter in the story?",
                f"The flower grew because the friends shared the work with care and patience. Helping together also changed them, because their friendship felt even stronger at the end.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["seed_cfg"].tags) | set(f["ground_cfg"].tags) | set(f["helper_cfg"].tags) | {"friendship"}
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.growable:
            bits.append("growable=True")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  sunshine: {world.sunshine}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
growable_ground(G) :- ground(G), growable(G).
sensible_helper(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
strong_enough(H, G) :- helper(H), ground(G), power(H, P), hardness(G, D), friend_bonus(B), P + B >= D.
valid(S, G, H) :- seed(S), growable_ground(G), sensible_helper(H), strong_enough(H, G).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for seed_id in sorted(SEEDS):
        lines.append(asp.fact("seed", seed_id))
    for ground_id, ground in GROUNDS.items():
        lines.append(asp.fact("ground", ground_id))
        lines.append(asp.fact("hardness", ground_id, ground.hardness))
        if ground.growable:
            lines.append(asp.fact("growable", ground_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
        lines.append(asp.fact("sense", helper_id, helper.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("friend_bonus", FRIEND_BONUS))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming friendship story world: two friends find a seed on the ground and help it transform into a flower."
    )
    ap.add_argument("--seed-kind", dest="seed_kind", choices=SEEDS)
    ap.add_argument("--ground", choices=GROUNDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.seed_kind is not None and args.seed_kind not in SEEDS:
        raise StoryError("(Unknown seed kind.)")
    if args.ground is not None and args.ground not in GROUNDS:
        raise StoryError("(Unknown ground.)")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError("(Unknown helper.)")

    if args.ground is not None and args.helper is not None:
        seed_id = args.seed_kind or next(iter(SEEDS))
        if not valid_combo(seed_id, args.ground, args.helper):
            raise StoryError(explain_rejection(SEEDS[seed_id], GROUNDS[args.ground], HELPERS[args.helper]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.seed_kind is None or combo[0] == args.seed_kind)
        and (args.ground is None or combo[1] == args.ground)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        if args.seed_kind and args.ground and args.helper:
            raise StoryError(explain_rejection(SEEDS[args.seed_kind], GROUNDS[args.ground], HELPERS[args.helper]))
        raise StoryError("(No valid combination matches the given options.)")

    seed_id, ground_id, helper_id = rng.choice(sorted(combos))
    friend1_gender = rng.choice(["girl", "boy"])
    friend2_gender = rng.choice(["girl", "boy"])
    friend1 = _pick_name(rng, friend1_gender)
    friend2 = _pick_name(rng, friend2_gender, avoid=friend1)
    parent = args.parent or rng.choice(["mother", "father"])
    trait1 = rng.choice(TRAITS)
    trait2 = rng.choice([t for t in TRAITS if t != trait1] or TRAITS)
    seed_value_word = rng.choice(["little", "tiny", "small", "sleepy"])
    return StoryParams(
        seed=seed_id,
        ground=ground_id,
        helper=helper_id,
        friend1=friend1,
        friend1_gender=friend1_gender,
        friend2=friend2,
        friend2_gender=friend2_gender,
        parent=parent,
        trait1=trait1,
        trait2=trait2,
        seed_value_word=seed_value_word,
    )


def generate(params: StoryParams) -> StorySample:
    if params.seed not in SEEDS:
        raise StoryError(f"(Unknown seed '{params.seed}'.)")
    if params.ground not in GROUNDS:
        raise StoryError(f"(Unknown ground '{params.ground}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if not valid_combo(params.seed, params.ground, params.helper):
        raise StoryError(explain_rejection(SEEDS[params.seed], GROUNDS[params.ground], HELPERS[params.helper]))

    world = tell(
        SEEDS[params.seed],
        GROUNDS[params.ground],
        HELPERS[params.helper],
        friend1=params.friend1,
        friend1_gender=params.friend1_gender,
        friend2=params.friend2,
        friend2_gender=params.friend2_gender,
        parent=params.parent,
        trait1=params.trait1,
        trait2=params.trait2,
        seed_value_word=params.seed_value_word,
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "ground" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or malformed.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("(Random smoke test failed: missing story or QA content.)")
        print("OK: random generation smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"RANDOM SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (seed, ground, helper) combos:\n")
        for seed_id, ground_id, helper_id in combos:
            print(f"  {seed_id:10} {ground_id:12} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            local_seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(local_seed))
            except StoryError as err:
                print(err)
                return
            params.seed = local_seed
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
            header = f"### {p.friend1} & {p.friend2}: {p.seed} in {p.ground} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
