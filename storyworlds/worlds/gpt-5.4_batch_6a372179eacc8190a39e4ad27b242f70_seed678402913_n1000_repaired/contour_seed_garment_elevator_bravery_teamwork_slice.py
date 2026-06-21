#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/contour_seed_garment_elevator_bravery_teamwork_slice.py
==================================================================================

A small slice-of-life storyworld about two children carrying seeds in an elevator.
When the elevator jolts and stops, one child feels scared. The children and a
helpful grown-up work together: one presses the help button, one steadies the
seed tray, and a soft garment is used to protect it. The story turns on bravery
that grows through teamwork, then ends with the seeds being planted.

The seed words "contour", "seed", and "garment" are built into the prose of each
reasonable story.

Run it
------
    python storyworlds/worlds/gpt-5.4/contour_seed_garment_elevator_bravery_teamwork_slice.py
    python storyworlds/worlds/gpt-5.4/contour_seed_garment_elevator_bravery_teamwork_slice.py --seed-kind sunflower --garment sweater
    python storyworlds/worlds/gpt-5.4/contour_seed_garment_elevator_bravery_teamwork_slice.py --garment sequined_vest
    python storyworlds/worlds/gpt-5.4/contour_seed_garment_elevator_bravery_teamwork_slice.py --all --qa
    python storyworlds/worlds/gpt-5.4/contour_seed_garment_elevator_bravery_teamwork_slice.py --verify
"""

from __future__ import annotations

import argparse
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
SENSE_MIN = 2


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
    soft: bool = False
    absorbent: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class SeedKind:
    id: str
    label: str
    phrase: str
    packet_art: str
    planting_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GarmentCfg:
    id: str
    label: str
    phrase: str
    texture: str
    cushion: int
    absorb: int
    sense: int
    use_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    adult_type: str
    label: str
    entry_text: str
    calm_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    seed_kind: str
    garment: str
    helper: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    parent: str
    brave_child: str
    delay: int = 0
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child_a", "child_b"}]

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


def _r_stuck_fear(world: World) -> list[str]:
    elevator = world.get("elevator")
    if elevator.meters["stuck"] < THRESHOLD:
        return []
    out: list[str] = []
    for kid in world.kids():
        sig = ("fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_garment_stabilizes(world: World) -> list[str]:
    tray = world.get("tray")
    garment = world.get("garment")
    if tray.meters["tilted"] < THRESHOLD or garment.meters["used"] < THRESHOLD:
        return []
    sig = ("stabilize", garment.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tray.meters["stability"] += float(garment.attrs.get("cushion", 0))
    tray.meters["spill_risk"] -= float(garment.attrs.get("cushion", 0))
    tray.meters["spill_risk"] = max(0.0, tray.meters["spill_risk"])
    if garment.attrs.get("absorb", 0) > 0:
        tray.meters["soil_saved"] += 1
    return ["__stable__"]


def _r_teamwork_bravery(world: World) -> list[str]:
    if world.facts.get("jobs_done") != 2:
        return []
    out: list[str] = []
    for kid in world.kids():
        sig = ("team", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["teamwork"] += 1
        if kid.memes["fear"] >= THRESHOLD:
            kid.memes["fear"] = max(0.0, kid.memes["fear"] - 1)
            kid.memes["bravery"] += 1
        out.append("__team__")
    return out


def _r_help_rescue(world: World) -> list[str]:
    elevator = world.get("elevator")
    if elevator.meters["help_called"] < THRESHOLD:
        return []
    if world.facts.get("jobs_done") != 2:
        return []
    sig = ("rescue", "elevator")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elevator.meters["opened"] += 1
    elevator.meters["stuck"] = 0.0
    return ["__open__"]


CAUSAL_RULES = [
    Rule(name="stuck_fear", tag="emotional", apply=_r_stuck_fear),
    Rule(name="garment_stabilizes", tag="physical", apply=_r_garment_stabilizes),
    Rule(name="teamwork_bravery", tag="social", apply=_r_teamwork_bravery),
    Rule(name="help_rescue", tag="physical", apply=_r_help_rescue),
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
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


SEEDS = {
    "sunflower": SeedKind(
        id="sunflower",
        label="sunflower seeds",
        phrase="a tray of sunflower seeds",
        packet_art="a bright flower with dark contour lines around each petal",
        planting_place="the sunny planter boxes",
        tags={"seed", "garden", "sunflower"},
    ),
    "bean": SeedKind(
        id="bean",
        label="bean seeds",
        phrase="a tray of bean seeds",
        packet_art="a little green vine drawn in soft contour lines",
        planting_place="the long wooden planter",
        tags={"seed", "garden", "beans"},
    ),
    "basil": SeedKind(
        id="basil",
        label="basil seeds",
        phrase="a tray of basil seeds",
        packet_art="a leaf sketch with a neat contour around its edge",
        planting_place="the herb box by the railing",
        tags={"seed", "garden", "herb"},
    ),
}

GARMENTS = {
    "sweater": GarmentCfg(
        id="sweater",
        label="sweater",
        phrase="a soft blue sweater",
        texture="soft and thick",
        cushion=2,
        absorb=1,
        sense=3,
        use_text="slid the sweater under one side of the tray so it would stop wobbling",
        qa_text="used the soft sweater to level the seed tray and catch a little loose soil",
        tags={"garment", "soft_clothes"},
    ),
    "scarf": GarmentCfg(
        id="scarf",
        label="scarf",
        phrase="a long yellow scarf",
        texture="soft and folded twice over",
        cushion=2,
        absorb=1,
        sense=3,
        use_text="folded the scarf into a pad and tucked it under the shaky corner of the tray",
        qa_text="folded the scarf into a pad to steady the tray",
        tags={"garment", "soft_clothes"},
    ),
    "raincoat": GarmentCfg(
        id="raincoat",
        label="raincoat",
        phrase="a small green raincoat",
        texture="smooth but sturdy",
        cushion=1,
        absorb=0,
        sense=2,
        use_text="rolled the raincoat and placed it under the tray so the corner would not bump again",
        qa_text="rolled the raincoat into support under the tray",
        tags={"garment", "raincoat"},
    ),
    "sequined_vest": GarmentCfg(
        id="sequined_vest",
        label="sequined vest",
        phrase="a shiny sequined vest",
        texture="stiff and scratchy",
        cushion=0,
        absorb=0,
        sense=1,
        use_text="",
        qa_text="",
        tags={"garment"},
    ),
}

HELPERS = {
    "superintendent": HelperCfg(
        id="superintendent",
        adult_type="man",
        label="Mr. Bell",
        entry_text="The building superintendent was riding with them because he had the roof key.",
        calm_text='Through the speaker, Mr. Bell said, "You are safe. Keep still, press the help button once, and we will be moving again soon."',
        tags={"help_button", "elevator"},
    ),
    "neighbor": HelperCfg(
        id="neighbor",
        adult_type="woman",
        label="Mrs. Rami",
        entry_text="Their upstairs neighbor, Mrs. Rami, had come along to show them the roof garden.",
        calm_text='Through the speaker, Mrs. Rami said, "You are safe in here with me. We will do this one step at a time."',
        tags={"help_button", "elevator"},
    ),
    "janitor": HelperCfg(
        id="janitor",
        adult_type="man",
        label="Mr. Ortiz",
        entry_text="The school janitor, Mr. Ortiz, was with them because the class was planting on the roof.",
        calm_text='Through the speaker, Mr. Ortiz said, "Good teamwork. Stay calm, hold the tray steady, and help is on the way."',
        tags={"help_button", "elevator"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Sana", "Ruby", "Ava", "Mina"]
BOY_NAMES = ["Owen", "Theo", "Eli", "Noah", "Ben", "Sam", "Leo", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for seed_id in SEEDS:
        for garment_id, garment in GARMENTS.items():
            for helper_id in HELPERS:
                if garment.sense >= SENSE_MIN and garment.cushion >= 1:
                    combos.append((seed_id, garment_id, helper_id))
    return combos


def garment_is_reasonable(garment: GarmentCfg) -> bool:
    return garment.sense >= SENSE_MIN and garment.cushion >= 1


def explain_rejection(garment: GarmentCfg) -> str:
    return (
        f"(No story: {garment.phrase} is too stiff to steady a tilting seed tray in an elevator. "
        f"The rescue depends on a garment that can cushion or support the tray, so try "
        f"a sweater, scarf, or raincoat instead.)"
    )


def predict_tray(seed_kind: SeedKind, garment: GarmentCfg, delay: int) -> dict:
    base_risk = 2 + delay
    saved = garment.cushion
    stable = saved >= base_risk - 1
    return {"spill_risk": base_risk, "saved": saved, "stable": stable}


def outcome_of(params: StoryParams) -> str:
    garment = GARMENTS[params.garment]
    if not garment_is_reasonable(garment):
        return "invalid"
    return "steady" if predict_tray(SEEDS[params.seed_kind], garment, params.delay)["stable"] else "messy"


def introduce(world: World, kid_a: Entity, kid_b: Entity, parent: Entity, helper: Entity,
              seed_kind: SeedKind, garment: Entity) -> None:
    world.say(
        f"After school, {kid_a.id} and {kid_b.id} stepped into the apartment elevator with "
        f"{parent.label_word} and {helper.label}. They were carrying {seed_kind.phrase} up to the roof garden."
    )
    world.say(helper.attrs.get("entry_text", ""))
    world.say(
        f"{kid_b.id} held the seed packet on top, and {kid_a.id} traced the {seed_kind.packet_art} with one finger "
        f"while the doors slid shut."
    )
    world.say(
        f"Over one arm, {kid_a.id} carried {garment.phrase}, a garment that smelled faintly of soap and sunshine."
    )


def ride_starts(world: World, kid_a: Entity, kid_b: Entity) -> None:
    for kid in (kid_a, kid_b):
        kid.memes["joy"] += 1
    world.say(
        f"The elevator hummed upward, and the tray of soil and tiny seed cups rocked gently between them."
    )


def elevator_stops(world: World, kid_a: Entity, kid_b: Entity) -> None:
    elevator = world.get("elevator")
    tray = world.get("tray")
    elevator.meters["stuck"] += 1
    tray.meters["tilted"] += 1
    tray.meters["spill_risk"] += 2
    propagate(world, narrate=False)
    world.say(
        "Then the car gave a quick bump and stopped between floors."
    )
    world.say(
        f"The lights stayed on, but the tray tipped to one side, and a little ridge of dark soil slid toward the lip."
    )
    scared = world.facts["scared_child"]
    world.say(
        f'{scared.id} grabbed the rail. "I do not like this," {scared.pronoun()} whispered.'
    )


def assign_jobs(world: World, brave: Entity, scared: Entity, helper: Entity) -> None:
    brave.memes["bravery"] += 1
    world.say(helper.attrs.get("calm_text", ""))
    world.say(
        f"{brave.id} took a slow breath. "
        f'"I can press the help button," {brave.pronoun()} said, "and you can hold the tray with me."'
    )


def press_help(world: World, brave: Entity) -> None:
    elevator = world.get("elevator")
    elevator.meters["help_called"] += 1
    world.facts["jobs_done"] = world.facts.get("jobs_done", 0) + 1
    world.say(
        f"{brave.id} pressed the help button once, just as the grown-up said."
    )


def use_garment(world: World, scared: Entity, garment: Entity) -> None:
    garment.meters["used"] += 1
    world.facts["jobs_done"] = world.facts.get("jobs_done", 0) + 1
    propagate(world, narrate=False)
    world.say(
        f"At the same time, {scared.id} {garment.attrs.get('use_text', 'used the garment to steady the tray')}."
    )


def waiting_beat(world: World, brave: Entity, scared: Entity) -> None:
    propagate(world, narrate=False)
    tray = world.get("tray")
    if tray.meters["stability"] >= 2:
        world.say(
            f"The wobble eased. {scared.id} kept both hands on the tray while {brave.id} counted slowly to five beside {scared.pronoun('object')}."
        )
    else:
        world.say(
            f"The tray still shivered a little, but now both children were holding it together instead of freezing apart."
        )


def doors_open(world: World, helper: Entity) -> None:
    elevator = world.get("elevator")
    propagate(world, narrate=False)
    if elevator.meters["opened"] >= THRESHOLD:
        world.say(
            "A moment later, the elevator gave a gentle click and began to move again."
        )
        world.say(
            "When the doors opened, the hallway felt bright and ordinary in the nicest way."
        )
    else:
        world.say(
            f"{helper.label} kept talking in the calmest voice until the elevator finally started again."
        )
        world.say(
            "The doors opened one floor below the roof, and everyone stepped out carefully."
        )


def plant_seeds(world: World, kid_a: Entity, kid_b: Entity, parent: Entity, seed_kind: SeedKind) -> None:
    tray = world.get("tray")
    for kid in (kid_a, kid_b):
        kid.memes["joy"] += 1
        kid.memes["hope"] += 1
    world.say(
        f"Together they carried the tray the rest of the way and planted the seed cups in {seed_kind.planting_place}."
    )
    if tray.meters["stability"] >= 2:
        world.say(
            f"Not a single cup had tipped over. {kid_b.id} smiled at {kid_a.id}, and {parent.label_word} said they had been brave because they had worked as a team."
        )
    else:
        world.say(
            f"A pinch of soil had spilled, but the seeds were safe. {kid_a.id} and {kid_b.id} brushed the dirt from their hands and smiled anyway."
        )
    world.say(
        f"Before going back downstairs, {kid_a.id} looked at the little rows and thought about how small a seed could be, and how big teamwork could feel."
    )


def tell(seed_kind: SeedKind, garment_cfg: GarmentCfg, helper_cfg: HelperCfg,
         child_a: str, child_a_gender: str, child_b: str, child_b_gender: str,
         parent_type: str, brave_child: str, delay: int) -> World:
    world = World()
    kid_a = world.add(Entity(id=child_a, kind="character", type=child_a_gender, role="child_a", label=child_a))
    kid_b = world.add(Entity(id=child_b, kind="character", type=child_b_gender, role="child_b", label=child_b))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.adult_type,
        role="helper",
        label=helper_cfg.label,
        attrs={"entry_text": helper_cfg.entry_text, "calm_text": helper_cfg.calm_text},
        tags=set(helper_cfg.tags),
    ))
    garment = world.add(Entity(
        id="garment",
        type="garment",
        label=garment_cfg.label,
        phrase=garment_cfg.phrase,
        soft=garment_cfg.cushion > 0,
        absorbent=garment_cfg.absorb > 0,
        attrs={
            "cushion": garment_cfg.cushion,
            "absorb": garment_cfg.absorb,
            "use_text": garment_cfg.use_text,
            "qa_text": garment_cfg.qa_text,
        },
        tags=set(garment_cfg.tags),
    ))
    tray = world.add(Entity(id="tray", type="tray", label="seed tray", phrase=seed_kind.phrase, tags=set(seed_kind.tags)))
    elevator = world.add(Entity(id="elevator", type="elevator", label="elevator", tags={"elevator"}))

    brave = kid_a if brave_child == "child_a" else kid_b
    scared = kid_b if brave is kid_a else kid_a

    introduce(world, kid_a, kid_b, parent, helper, seed_kind, garment)
    ride_starts(world, kid_a, kid_b)

    world.para()
    elevator_stops(world, kid_a, kid_b)
    assign_jobs(world, brave, scared, helper)
    press_help(world, brave)
    use_garment(world, scared, garment)
    waiting_beat(world, brave, scared)

    world.para()
    doors_open(world, helper)
    plant_seeds(world, kid_a, kid_b, parent, seed_kind)

    world.facts.update(
        seed_kind=seed_kind,
        garment_cfg=garment_cfg,
        helper_cfg=helper_cfg,
        child_a=kid_a,
        child_b=kid_b,
        brave=brave,
        scared_child=scared,
        parent=parent,
        helper=helper,
        garment=garment,
        tray=tray,
        delay=delay,
        jobs_done=world.facts.get("jobs_done", 0),
        outcome="steady" if tray.meters["stability"] >= 2 else "messy",
        contour_text=seed_kind.packet_art,
    )
    return world


KNOWLEDGE = {
    "elevator": [
        ("What does an elevator do?",
         "An elevator is a small room that moves up and down inside a building so people can travel between floors.")
    ],
    "help_button": [
        ("What should you do if an elevator stops moving?",
         "Stay calm, stand still, and press the help button or call for a grown-up. It is safest to wait for help instead of trying to force the doors.")
    ],
    "seed": [
        ("What is a seed?",
         "A seed is a tiny part of a plant that can grow into a new plant when it gets soil, water, and light.")
    ],
    "garden": [
        ("Why do people plant seeds in soil?",
         "Seeds need soil to hold them in place and help them get water and nutrients as they begin to grow.")
    ],
    "garment": [
        ("What is a garment?",
         "A garment is a piece of clothing, like a sweater, scarf, or coat.")
    ],
    "soft_clothes": [
        ("Why can a soft sweater or scarf cushion something?",
         "Soft cloth can spread out a bump and make it gentler, so a wobbly object does not knock so hard against a surface.")
    ],
    "raincoat": [
        ("What is a raincoat for?",
         "A raincoat is a coat that helps keep rain off your clothes and skin. It is smooth and can also be rolled up to make a light pad.")
    ],
    "sunflower": [
        ("What do sunflower seeds grow into?",
         "Sunflower seeds grow into tall plants with big yellow flowers that turn toward the light.")
    ],
    "beans": [
        ("How do bean plants grow?",
         "Bean plants sprout from beans, then send up stems and leaves. Many of them like to climb when they get bigger.")
    ],
    "herb": [
        ("What is basil?",
         "Basil is a soft green herb with a sweet smell. People grow it in pots and use the leaves in food.")
    ],
}
KNOWLEDGE_ORDER = [
    "elevator", "help_button", "seed", "garden", "garment", "soft_clothes",
    "raincoat", "sunflower", "beans", "herb",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    brave = f["brave"]
    scared = f["scared_child"]
    seed_kind = f["seed_kind"]
    garment = f["garment"]
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old set in an elevator, and include the words "contour", "seed", and "garment".',
        f"Tell a story where {brave.id} and {scared.id} are carrying {seed_kind.label} in an elevator, the car stops, and they solve the problem through bravery and teamwork.",
        f"Write a calm story where a soft {garment.label} helps protect a seed tray during a small elevator scare, and the ending shows the children planting safely together.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two children"
    if a.type == "boy" and b.type == "boy":
        return "two children"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    brave = f["brave"]
    scared = f["scared_child"]
    parent = f["parent"]
    helper = f["helper"]
    garment = f["garment"]
    seed_kind = f["seed_kind"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, riding an elevator with {parent.label_word} and {helper.label}. They were taking {seed_kind.label} to be planted on the roof."
        ),
        (
            "Why were they in the elevator?",
            f"They were riding up to the roof garden with a tray of seeds. The elevator mattered because the trouble began when it stopped between floors."
        ),
        (
            "Where did the word contour appear in the story?",
            f"It appeared on the seed packet art. {a.id} traced the contour drawing with one finger while the elevator ride began."
        ),
        (
            f"Why did {scared.id} feel afraid?",
            f"{scared.id} felt afraid because the elevator bumped and stopped between floors, and the tray began to tilt. The sudden stop made the small space feel uncertain."
        ),
        (
            f"What jobs did the children do together?",
            f"{brave.id} pressed the help button, and {scared.id} helped steady the tray. Doing two useful jobs at once turned their worry into teamwork."
        ),
        (
            f"How did the garment help the seeds?",
            f"They {garment.attrs.get('qa_text', 'used the garment to help the tray')}. That kept the tray steadier so the seed cups would not slide and spill."
        ),
    ]
    if outcome == "steady":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children planting the seeds safely on the roof. The calm ending shows that they got through the elevator scare by being brave together."
            )
        )
    else:
        qa.append(
            (
                "Did they lose the seeds?",
                f"No. A little soil spilled, but the seeds stayed safe enough to plant. The teamwork mattered because it stopped a bigger mess."
            )
        )
    qa.append(
        (
            f"What made {brave.id} brave?",
            f"{brave.id} was brave by taking a slow breath and doing the next helpful thing instead of pretending not to be scared. The bravery worked because {scared.id}, the grown-ups, and the soft garment all helped too."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"elevator", "seed", "garden", "garment"}
    tags |= set(world.facts["helper"].tags)
    tags |= set(world.facts["garment"].tags)
    tags |= set(world.facts["seed_kind"].tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        seed_kind="sunflower",
        garment="sweater",
        helper="neighbor",
        child_a="Lina",
        child_a_gender="girl",
        child_b="Theo",
        child_b_gender="boy",
        parent="mother",
        brave_child="child_a",
        delay=0,
    ),
    StoryParams(
        seed_kind="bean",
        garment="scarf",
        helper="superintendent",
        child_a="Max",
        child_a_gender="boy",
        child_b="Nora",
        child_b_gender="girl",
        parent="father",
        brave_child="child_b",
        delay=0,
    ),
    StoryParams(
        seed_kind="basil",
        garment="raincoat",
        helper="janitor",
        child_a="Maya",
        child_a_gender="girl",
        child_b="Leo",
        child_b_gender="boy",
        parent="mother",
        brave_child="child_b",
        delay=1,
    ),
]


ASP_RULES = r"""
reasonable_garment(G) :- garment(G), sense(G,S), sense_min(M), S >= M, cushion(G,C), C >= 1.
valid(Sd, G, H) :- seed_kind(Sd), reasonable_garment(G), helper(H).

base_risk(2).
risk(R) :- base_risk(B), delay(D), R = B + D.
saved(C) :- chosen_garment(G), cushion(G, C).
steady :- risk(R), saved(C), C >= R - 1.
outcome(steady) :- steady.
outcome(messy) :- not steady.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for seed_id in SEEDS:
        lines.append(asp.fact("seed_kind", seed_id))
    for garment_id, garment in GARMENTS.items():
        lines.append(asp.fact("garment", garment_id))
        lines.append(asp.fact("sense", garment_id, garment.sense))
        lines.append(asp.fact("cushion", garment_id, garment.cushion))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_garment", params.garment),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: children, seeds, an elevator stop, and teamwork."
    )
    ap.add_argument("--seed-kind", choices=SEEDS)
    ap.add_argument("--garment", choices=GARMENTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP and Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.garment is not None:
        garment = GARMENTS[args.garment]
        if not garment_is_reasonable(garment):
            raise StoryError(explain_rejection(garment))

    combos = [
        c for c in valid_combos()
        if (args.seed_kind is None or c[0] == args.seed_kind)
        and (args.garment is None or c[1] == args.garment)
        and (args.helper is None or c[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    seed_kind, garment, helper = rng.choice(sorted(combos))
    child_a, ga = _pick_child(rng)
    child_b, gb = _pick_child(rng, avoid=child_a)
    parent = args.parent or rng.choice(["mother", "father"])
    brave_child = rng.choice(["child_a", "child_b"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        seed_kind=seed_kind,
        garment=garment,
        helper=helper,
        child_a=child_a,
        child_a_gender=ga,
        child_b=child_b,
        child_b_gender=gb,
        parent=parent,
        brave_child=brave_child,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.seed_kind not in SEEDS:
        raise StoryError(f"(Unknown seed kind: {params.seed_kind})")
    if params.garment not in GARMENTS:
        raise StoryError(f"(Unknown garment: {params.garment})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.brave_child not in {"child_a", "child_b"}:
        raise StoryError("(brave_child must be child_a or child_b)")
    garment_cfg = GARMENTS[params.garment]
    if not garment_is_reasonable(garment_cfg):
        raise StoryError(explain_rejection(garment_cfg))

    world = tell(
        seed_kind=SEEDS[params.seed_kind],
        garment_cfg=garment_cfg,
        helper_cfg=HELPERS[params.helper],
        child_a=params.child_a,
        child_a_gender=params.child_a_gender,
        child_b=params.child_b,
        child_b_gender=params.child_b_gender,
        parent_type=params.parent,
        brave_child=params.brave_child,
        delay=params.delay,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(20):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    mismatch = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        buf = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old_stdout
        sample.to_json()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (seed_kind, garment, helper) combos:\n")
        for seed_kind, garment, helper in combos:
            print(f"  {seed_kind:10} {garment:14} {helper}")
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
            header = f"### {p.child_a} and {p.child_b}: {p.seed_kind}, {p.garment}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
