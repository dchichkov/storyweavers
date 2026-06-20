#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/meadow_humor_flashback_transformation_heartwarming.py
================================================================================

A standalone story world about a child in a meadow, a caterpillar, an impatient
wish to hurry a miracle, a gentle flashback, and a warm transformation.

This world rebuilds a TinyStories-style premise with explicit state:

- A child visits a meadow with a loving grown-up.
- They find a plump caterpillar near the plant it needs.
- The child makes a funny, silly plan to help it become a butterfly "right now."
- The grown-up answers with a flashback about how small and hungry it used to be.
- They choose a reasonable safe place to wait.
- The caterpillar forms a chrysalis and later transforms into a butterfly.

Reasonableness matters. A caterpillar must be paired with the right host plant,
and the waiting perch must actually support a chrysalis. The world refuses weak
combinations instead of stretching them into vague prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/meadow_humor_flashback_transformation_heartwarming.py
    python storyworlds/worlds/gpt-5.4/meadow_humor_flashback_transformation_heartwarming.py --caterpillar monarch --plant milkweed --perch milkweed_stem
    python storyworlds/worlds/gpt-5.4/meadow_humor_flashback_transformation_heartwarming.py --caterpillar monarch --plant thistle
    python storyworlds/worlds/gpt-5.4/meadow_humor_flashback_transformation_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/meadow_humor_flashback_transformation_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/meadow_humor_flashback_transformation_heartwarming.py --verify
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
# This file lives one level deeper than most worlds, under storyworlds/worlds/gpt-5.4/,
# so we add storyworlds/ itself to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"              # "character" | "thing"
    type: str = "thing"              # girl, boy, grandmother, caterpillar, plant...
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    host_for: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
    # physical meters and emotional memes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class Meadow:
    id: str
    label: str
    opening: str
    detail: str
    tags: set[str] = field(default_factory=lambda: {"meadow"})


@dataclass
class CaterpillarKind:
    id: str
    label: str
    butterfly_label: str
    butterfly_phrase: str
    colors: str
    host_plant: str
    flashback: str
    joke_title: str
    tags: set[str] = field(default_factory=lambda: {"caterpillar", "butterfly", "transformation"})


@dataclass
class Plant:
    id: str
    label: str
    phrase: str
    host_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=lambda: {"plant"})


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    supports: set[str] = field(default_factory=set)
    steady: int = 1
    tags: set[str] = field(default_factory=lambda: {"chrysalis"})


@dataclass
class Helper:
    id: str
    type: str
    label: str
    memory_verb: str
    comfort_style: str
    tags: set[str] = field(default_factory=lambda: {"family"})


# ---------------------------------------------------------------------------
# World and rule engine
# ---------------------------------------------------------------------------
class World:
    def __init__(self, meadow: Meadow) -> None:
        self.meadow = meadow
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
        clone = World(self.meadow)
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


def _r_grow(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    plant = world.get("plant")
    if creature.meters["hungry"] < THRESHOLD:
        return out
    if plant.host_for and creature.id not in plant.host_for:
        return out
    sig = ("grow", creature.id, plant.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters["fed"] += 1
    creature.meters["size"] += 1
    creature.meters["hungry"] = 0.0
    out.append("__grew__")
    return out


def _r_chrysalis(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    perch = world.get("perch")
    if creature.meters["size"] < THRESHOLD:
        return out
    if creature.meters["safe"] < THRESHOLD:
        return out
    if creature.meters["chrysalis"] >= THRESHOLD:
        return out
    if creature.id not in perch.supports:
        return out
    sig = ("chrysalis", creature.id, perch.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters["hanging"] += 1
    creature.meters["chrysalis"] += 1
    creature.meters["wiggly"] = 0.0
    out.append("__chrysalis__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    creature = world.get("creature")
    if creature.meters["chrysalis"] < THRESHOLD:
        return out
    if creature.meters["waited"] < THRESHOLD:
        return out
    if creature.meters["butterfly"] >= THRESHOLD:
        return out
    sig = ("transform", creature.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    creature.meters["butterfly"] += 1
    creature.meters["flutter"] += 1
    out.append("__transformed__")
    return out


CAUSAL_RULES = [
    Rule("grow", "physical", _r_grow),
    Rule("chrysalis", "physical", _r_chrysalis),
    Rule("transform", "physical", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def host_match(caterpillar: CaterpillarKind, plant: Plant) -> bool:
    return caterpillar.id in plant.host_for and plant.id == caterpillar.host_plant


def perch_match(caterpillar: CaterpillarKind, perch: Perch) -> bool:
    return caterpillar.id in perch.supports and perch.steady >= 1


def valid_combo(caterpillar: CaterpillarKind, plant: Plant, perch: Perch) -> bool:
    return host_match(caterpillar, plant) and perch_match(caterpillar, perch)


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for meadow_id in MEADOWS:
        for cat_id, cat in CATERPILLARS.items():
            for plant_id, plant in PLANTS.items():
                for perch_id, perch in PERCHES.items():
                    if valid_combo(cat, plant, perch):
                        out.append((meadow_id, cat_id, plant_id, perch_id))
    return out


def explain_rejection(caterpillar: CaterpillarKind, plant: Plant, perch: Optional[Perch] = None) -> str:
    if not host_match(caterpillar, plant):
        return (
            f"(No story: a {caterpillar.label} belongs on {PLANTS[caterpillar.host_plant].phrase}, "
            f"not {plant.phrase}. Without the right plant, the meadow visit has no honest, safe path "
            f"to the transformation.)"
        )
    if perch is not None and not perch_match(caterpillar, perch):
        return (
            f"(No story: {perch.phrase} is not a good place for a {caterpillar.label} to hang safely. "
            f"Pick a steadier perch that can hold a chrysalis.)"
        )
    return "(No story: this combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Simulation verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity, meadow: Meadow) -> None:
    child.memes["wonder"] += 1
    helper.memes["care"] += 1
    world.say(
        f"One soft afternoon, {child.id} walked into {meadow.label} with {child.pronoun('possessive')} "
        f"{helper.label_word}. {meadow.opening} {meadow.detail}"
    )


def find_caterpillar(world: World, child: Entity, creature: Entity, plant: Plant, cat: CaterpillarKind) -> None:
    creature.meters["hungry"] += 1
    creature.meters["wiggly"] += 1
    world.say(
        f"Near {plant.phrase}, {child.id} spotted a {cat.label}. It was plump and stripy and so busy chewing "
        f"that it looked, {child.id} said, like a tiny green train that had forgotten where the station was."
    )
    child.memes["delight"] += 1


def silly_plan(world: World, child: Entity, cat: CaterpillarKind) -> None:
    child.memes["humor"] += 1
    child.memes["impatience"] += 1
    world.say(
        f'"Maybe {cat.joke_title} just needs a joke and a countdown," {child.id} whispered. '
        f'"One, two, three -- poof! Butterfly!"'
    )
    world.say(
        f"{child.id} cupped both hands beside {child.pronoun('possessive')} mouth and added, "
        f'"If that does not work, I can flap for it."'
    )


def flashback(world: World, helper: Entity, child: Entity, cat: CaterpillarKind, plant: Plant) -> None:
    helper.memes["memory"] += 1
    world.say(
        f"{helper.label_word.capitalize()} laughed so warmly that even the grass seemed to listen. "
        f'"Do you remember last week?" {helper.pronoun()} asked.'
    )
    world.say(
        f"{helper.memory_verb.capitalize()} the same patch of {plant.label}, when {cat.flashback}. "
        f'"It was not ready then," {helper.pronoun()} said, "and it cannot be hurried now. '
        f"Growing has its own quiet kind of funny." + '"'
    )
    world.facts["flashback_happened"] = True


def place_safely(world: World, child: Entity, helper: Entity, perch: Perch, cat: CaterpillarKind) -> None:
    creature = world.get("creature")
    creature.meters["safe"] += 1
    world.say(
        f"Together they chose {perch.phrase} beside the flowers. {helper.label_word.capitalize()} showed "
        f"{child.id} how to be gentle, and {child.id} held {child.pronoun('possessive')} breath as the "
        f"{cat.label} curled itself into place."
    )


def wait_and_watch(world: World, child: Entity, helper: Entity, cat: CaterpillarKind) -> None:
    creature = world.get("creature")
    creature.meters["waited"] += 1
    child.memes["patience"] += 1
    helper.memes["care"] += 1
    world.say(
        f"They came back to the meadow every day. First there was a quiet hanging shape, then a smooth green "
        f"chrysalis that looked like a tiny sleeping lantern."
    )
    world.say(
        f"Each time, {child.id} tried not to bounce too hard, although once {child.pronoun()} whispered, "
        f'"I am bouncing on the inside." {helper.label_word.capitalize()} said that counted as patience.'
    )


def ending(world: World, child: Entity, helper: Entity, cat: CaterpillarKind, meadow: Meadow) -> None:
    creature = world.get("creature")
    child.memes["joy"] += 1
    child.memes["love"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then one bright morning, the chrysalis split, and out came {cat.butterfly_phrase}. "
        f"Its {cat.colors} wings opened in the sun like a secret finally telling the truth."
    )
    world.say(
        f"{child.id} did flap after all -- not to help, but because {child.pronoun()} could not keep the gladness "
        f"still. The butterfly lifted over {meadow.label}, and {helper.label_word.capitalize()} put an arm around "
        f"{child.id} while they watched it go."
    )
    world.say(
        f'"So it was a butterfly all along," {child.id} said softly. '
        f'"Yes," {helper.pronoun()} answered, "{helper.comfort_style} and now you got to see it become itself."'
    )
    world.facts["butterfly_seen"] = creature.meters["butterfly"] >= THRESHOLD


def predict_transformation(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    sim.get("creature").meters["safe"] += 1
    propagate(sim, narrate=False)
    sim.get("creature").meters["waited"] += 1
    propagate(sim, narrate=False)
    creature = sim.get("creature")
    return {
        "chrysalis": creature.meters["chrysalis"] >= THRESHOLD,
        "butterfly": creature.meters["butterfly"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------
def tell(meadow: Meadow, caterpillar: CaterpillarKind, plant: Plant, perch: Perch,
         child_name: str = "Mila", child_type: str = "girl",
         helper_kind: Helper | None = None) -> World:
    world = World(meadow)
    helper_kind = helper_kind or HELPERS["grandmother"]

    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind.type, role="helper", label=helper_kind.label))
    creature = world.add(Entity(id="creature", kind="thing", type="caterpillar", label=caterpillar.label))
    world.add(Entity(id="plant", kind="thing", type="plant", label=plant.label, host_for=set(plant.host_for)))
    world.add(Entity(id="perch", kind="thing", type="perch", label=perch.label, supports=set(perch.supports)))

    introduce(world, child, helper, meadow)
    find_caterpillar(world, child, creature, plant, caterpillar)

    world.para()
    silly_plan(world, child, caterpillar)
    flashback(world, helper, child, caterpillar, plant)

    pred = predict_transformation(world)
    world.facts["predicted_chrysalis"] = pred["chrysalis"]
    world.facts["predicted_butterfly"] = pred["butterfly"]

    world.para()
    propagate(world, narrate=False)  # hungry + right plant -> grows
    place_safely(world, child, helper, perch, caterpillar)
    propagate(world, narrate=False)  # safe + grown + right perch -> chrysalis
    wait_and_watch(world, child, helper, caterpillar)
    propagate(world, narrate=False)  # waited + chrysalis -> butterfly
    ending(world, child, helper, caterpillar, meadow)

    world.facts.update(
        child=child,
        helper=helper,
        helper_kind=helper_kind,
        meadow=meadow,
        caterpillar_cfg=caterpillar,
        plant_cfg=plant,
        perch_cfg=perch,
        transformed=world.get("creature").meters["butterfly"] >= THRESHOLD,
        chrysalis=world.get("creature").meters["chrysalis"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
MEADOWS = {
    "wildflower": Meadow(
        "wildflower",
        "the wildflower meadow",
        "The meadow rolled wide and bright under the sky.",
        "Purple clover nodded beside daisies, and the breeze kept making little laughing waves in the grass.",
    ),
    "sunny": Meadow(
        "sunny",
        "the sunny meadow",
        "The meadow looked as if morning had forgotten to stop smiling there.",
        "Buttercups shone low to the ground, and bees stitched soft loops through the warm air.",
    ),
    "clover": Meadow(
        "clover",
        "the clover meadow",
        "The meadow smelled sweet and green after a small rain.",
        "White clover blossoms bobbed like tiny flags, and each step made the hidden crickets start up again.",
    ),
}

CATERPILLARS = {
    "monarch": CaterpillarKind(
        "monarch",
        "monarch caterpillar",
        "monarch butterfly",
        "a monarch butterfly",
        "orange-and-black",
        "milkweed",
        "it was no bigger than a comma and had been chewing so seriously that its whole body wobbled with each bite",
        "Captain Nibble",
        tags={"caterpillar", "butterfly", "transformation", "milkweed"},
    ),
    "swallowtail": CaterpillarKind(
        "swallowtail",
        "swallowtail caterpillar",
        "swallowtail butterfly",
        "a swallowtail butterfly",
        "yellow-and-black",
        "fennel",
        "it looked like a tiny green question mark on a fennel leaf, as if it had not yet decided what kind of magic it wanted to become",
        "Professor Wiggle",
        tags={"caterpillar", "butterfly", "transformation", "fennel"},
    ),
    "painted_lady": CaterpillarKind(
        "painted_lady",
        "painted lady caterpillar",
        "painted lady butterfly",
        "a painted lady butterfly",
        "orange-and-brown",
        "thistle",
        "it was a fuzzy little muncher tucked among the thistle leaves, and you had to look twice to tell where the leaf ended and the caterpillar began",
        "Sir Crumblepants",
        tags={"caterpillar", "butterfly", "transformation", "thistle"},
    ),
}

PLANTS = {
    "milkweed": Plant("milkweed", "milkweed", "a tall patch of milkweed", host_for={"monarch"}, tags={"plant", "milkweed"}),
    "fennel": Plant("fennel", "fennel", "a feathery stand of fennel", host_for={"swallowtail"}, tags={"plant", "fennel"}),
    "thistle": Plant("thistle", "thistle", "a silver-green thistle clump", host_for={"painted_lady"}, tags={"plant", "thistle"}),
}

PERCHES = {
    "milkweed_stem": Perch("milkweed_stem", "milkweed stem", "a steady milkweed stem", supports={"monarch"}, steady=2, tags={"chrysalis", "stem"}),
    "fennel_stake": Perch("fennel_stake", "garden stake", "a thin garden stake tucked by the fennel", supports={"swallowtail"}, steady=2, tags={"chrysalis", "stake"}),
    "thistle_stem": Perch("thistle_stem", "thistle stem", "a sturdy thistle stem", supports={"painted_lady"}, steady=2, tags={"chrysalis", "stem"}),
    "twig_ring": Perch("twig_ring", "twig ring", "a loose ring of twigs in the grass", supports=set(), steady=0, tags={"chrysalis"}),
}

HELPERS = {
    "grandmother": Helper("grandmother", "grandmother", "the grandmother", "she remembered", "sometimes waiting is the softest way to love a living thing"),
    "grandfather": Helper("grandfather", "grandfather", "the grandfather", "he remembered", "sometimes waiting is the kindest part of helping"),
    "mother": Helper("mother", "mother", "the mother", "she remembered", "sometimes love is quiet hands and patient eyes"),
    "father": Helper("father", "father", "the father", "he remembered", "sometimes the best help is giving wonder a little room"),
}

GIRL_NAMES = ["Mila", "Lily", "Ava", "Nora", "Zoe", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Sam", "Eli", "Theo", "Max", "Finn", "Noah"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    meadow: str
    caterpillar: str
    plant: str
    perch: str
    helper: str
    child_name: str
    child_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "meadow": [
        ("What is a meadow?",
         "A meadow is an open field full of grasses and flowers. Many insects and birds live there because it offers food and shelter.")
    ],
    "caterpillar": [
        ("What is a caterpillar?",
         "A caterpillar is the larva of a butterfly or moth. It eats and grows before changing into a new form.")
    ],
    "transformation": [
        ("How does a caterpillar become a butterfly?",
         "A caterpillar grows, makes a chrysalis, and then changes inside it. After that, a butterfly comes out and opens its wings.")
    ],
    "chrysalis": [
        ("What is a chrysalis?",
         "A chrysalis is the case around a butterfly pupa. It protects the insect while its body changes.")
    ],
    "milkweed": [
        ("Why do monarch caterpillars need milkweed?",
         "Monarch caterpillars eat milkweed, and that plant is their special food. Without it, they cannot grow the normal way.")
    ],
    "fennel": [
        ("Why might a swallowtail caterpillar be found on fennel?",
         "Some swallowtail caterpillars eat fennel leaves. That is why gardeners often spot them there.")
    ],
    "thistle": [
        ("Why would a caterpillar stay on thistle?",
         "Some caterpillars use thistle as food and shelter. Staying near the right plant helps them grow safely.")
    ],
    "family": [
        ("Why can waiting with a grown-up feel easier?",
         "A calm grown-up can help you watch carefully and stay gentle. Their patience can make a hard wait feel safer and warmer.")
    ],
}

KNOWLEDGE_ORDER = ["meadow", "caterpillar", "transformation", "chrysalis",
                   "milkweed", "fennel", "thistle", "family"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    cat = f["caterpillar_cfg"]
    meadow = f["meadow"]
    helper = f["helper"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old set in {meadow.label} that includes humor, a flashback, and a transformation.',
        f"Tell a gentle meadow story where {child.id} meets a {cat.label}, makes a funny plan to hurry it, and {child.pronoun('possessive')} {helper.label_word} shares a loving memory before the creature becomes a butterfly.",
        f'Write a child-friendly story using the word "meadow" that begins with laughter, includes a memory from last week, and ends with a butterfly flying away.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    cat = f["caterpillar_cfg"]
    plant = f["plant_cfg"]
    perch = f["perch_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {helper.label_word}, and a {cat.label} they found in the meadow."
        ),
        (
            f"What funny thing did {child.id} say?",
            f"{child.id} joked that the caterpillar could turn into a butterfly after a countdown. Then {child.pronoun()} said {child.pronoun()} might flap for it if the joke did not work."
        ),
        (
            "What was the flashback about?",
            f"{helper.label_word.capitalize()} remembered the same patch of {plant.label} from last week, when the caterpillar was much smaller and still busy eating. The memory showed that the change had been happening little by little all along."
        ),
        (
            f"Why did they keep the caterpillar near {plant.label} and put it on {perch.label}?",
            f"They chose the right plant because that caterpillar kind belongs there, and they chose a steady perch so it could hang safely. Those careful choices let the transformation happen naturally instead of forcing it."
        ),
    ]
    if f.get("chrysalis"):
        qa.append(
            (
                "What happened before the butterfly came out?",
                "The caterpillar made a chrysalis and stayed still while it changed. The quiet middle part mattered because butterflies do not appear all at once."
            )
        )
    if f.get("transformed"):
        qa.append(
            (
                "How did the story end?",
                f"It ended with {cat.butterfly_phrase} opening its wings and flying over the meadow. {child.id} felt so happy that {child.pronoun()} flapped too, which turned the earlier joke into a loving ending."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["meadow"].tags) | set(f["caterpillar_cfg"].tags) | set(f["helper_kind"].tags)
    tags |= set(f["plant_cfg"].tags) | set(f["perch_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.host_for:
            bits.append(f"host_for={sorted(e.host_for)}")
        if e.supports:
            bits.append(f"supports={sorted(e.supports)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
host_match(C, P) :- caterpillar(C), plant(P), requires(C, P).
perch_match(C, R) :- caterpillar(C), perch(R), supports(R, C), steady(R, S), S >= 1.
valid(M, C, P, R) :- meadow(M), host_match(C, P), perch_match(C, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for meadow_id in MEADOWS:
        lines.append(asp.fact("meadow", meadow_id))
    for cat_id, cat in CATERPILLARS.items():
        lines.append(asp.fact("caterpillar", cat_id))
        lines.append(asp.fact("requires", cat_id, cat.host_plant))
    for plant_id in PLANTS:
        lines.append(asp.fact("plant", plant_id))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("steady", perch_id, perch.steady))
        for cat_id in sorted(perch.supports):
            lines.append(asp.fact("supports", perch_id, cat_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in asp:", sorted(clingo_set - python_set))

    smoke_params = list(CURATED)
    for seed in range(6):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_params.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed during smoke seed {seed}.")
            continue

    for params in smoke_params:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if "meadow" not in sample.story.lower():
                raise StoryError("story did not mention meadow")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"ERROR: smoke generation failed for {params}: {err}")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_params)} generated stories.")
    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams("wildflower", "monarch", "milkweed", "milkweed_stem", "grandmother", "Mila", "girl"),
    StoryParams("sunny", "swallowtail", "fennel", "fennel_stake", "grandfather", "Leo", "boy"),
    StoryParams("clover", "painted_lady", "thistle", "thistle_stem", "mother", "Nora", "girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a meadow child, a funny impatience, a flashback, and a butterfly transformation."
    )
    ap.add_argument("--meadow", choices=MEADOWS)
    ap.add_argument("--caterpillar", choices=CATERPILLARS)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.caterpillar and args.plant:
        cat = CATERPILLARS[args.caterpillar]
        plant = PLANTS[args.plant]
        if not host_match(cat, plant):
            raise StoryError(explain_rejection(cat, plant))
    if args.caterpillar and args.perch:
        cat = CATERPILLARS[args.caterpillar]
        perch = PERCHES[args.perch]
        if not perch_match(cat, perch):
            plant = PLANTS[cat.host_plant]
            raise StoryError(explain_rejection(cat, plant, perch))

    combos = [
        c for c in valid_combos()
        if (args.meadow is None or c[0] == args.meadow)
        and (args.caterpillar is None or c[1] == args.caterpillar)
        and (args.plant is None or c[2] == args.plant)
        and (args.perch is None or c[3] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    meadow_id, caterpillar_id, plant_id, perch_id = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    return StoryParams(meadow_id, caterpillar_id, plant_id, perch_id, helper, child_name, child_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        MEADOWS[params.meadow],
        CATERPILLARS[params.caterpillar],
        PLANTS[params.plant],
        PERCHES[params.perch],
        params.child_name,
        params.child_type,
        HELPERS[params.helper],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (meadow, caterpillar, plant, perch) combos:\n")
        for meadow_id, cat_id, plant_id, perch_id in combos:
            print(f"  {meadow_id:10} {cat_id:14} {plant_id:10} {perch_id}")
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
            header = f"### {p.child_name}: {p.caterpillar} in {p.meadow} meadow"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
