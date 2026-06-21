#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tip_transformation_kindness_suspense_slice_of_life.py
================================================================================

A standalone storyworld for a small slice-of-life tale about kindness, suspense,
and transformation. A child plans a gentle surprise for a neighbor, discovers
that a little plant is in trouble, gets one good tip from a helpful grown-up,
and waits anxiously to see whether the plant will change in time.

The world model keeps both physical meters (thirst, droop, support, sunlight,
uprightness) and emotional memes (worry, hope, relief, kindness). The story is
rendered from state transitions rather than from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/tip_transformation_kindness_suspense_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/tip_transformation_kindness_suspense_slice_of_life.py --plant basil --problem thirsty
    python storyworlds/worlds/gpt-5.4/tip_transformation_kindness_suspense_slice_of_life.py --problem bent --tip water
    python storyworlds/worlds/gpt-5.4/tip_transformation_kindness_suspense_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/tip_transformation_kindness_suspense_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tip_transformation_kindness_suspense_slice_of_life.py --verify
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
        female = {"girl", "woman", "mother", "grandmother", "florist_woman"}
        male = {"boy", "man", "father", "grandfather", "florist_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    child_trip: str
    helper_name: str
    helper_type: str
    helper_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PlantSpec:
    id: str
    label: str
    phrase: str
    color: str
    gift_line: str
    responds_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemSpec:
    id: str
    label: str
    visible: str
    child_worry: str
    wait_line: str
    needs: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TipSpec:
    id: str
    label: str
    quote: str
    act_text: str
    qa_text: str
    fixes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_thirst_droop(world: World) -> list[str]:
    out: list[str] = []
    plant = world.entities.get("plant")
    if plant is None:
        return out
    if plant.meters["thirst"] >= THRESHOLD and ("thirst_droop", plant.id) not in world.fired:
        world.fired.add(("thirst_droop", plant.id))
        plant.meters["droop"] += 1
        out.append("__droop__")
    return out


def _r_dark_pale(world: World) -> list[str]:
    out: list[str] = []
    plant = world.entities.get("plant")
    if plant is None:
        return out
    if plant.meters["dimness"] >= THRESHOLD and ("dark_pale", plant.id) not in world.fired:
        world.fired.add(("dark_pale", plant.id))
        plant.meters["droop"] += 1
        plant.meters["pale"] += 1
        out.append("__pale__")
    return out


def _r_bent_slump(world: World) -> list[str]:
    out: list[str] = []
    plant = world.entities.get("plant")
    if plant is None:
        return out
    if plant.meters["bend"] >= THRESHOLD and ("bend_slump", plant.id) not in world.fired:
        world.fired.add(("bend_slump", plant.id))
        plant.meters["droop"] += 1
        out.append("__bent__")
    return out


def _r_recover(world: World) -> list[str]:
    out: list[str] = []
    plant = world.entities.get("plant")
    if plant is None:
        return out
    supported = plant.meters["support"] >= THRESHOLD
    watered = plant.meters["water"] >= THRESHOLD
    sunlit = plant.meters["sunlight"] >= THRESHOLD
    if watered and plant.meters["thirst"] >= THRESHOLD and ("recover_water", plant.id) not in world.fired:
        world.fired.add(("recover_water", plant.id))
        plant.meters["thirst"] = 0.0
        plant.meters["droop"] = 0.0
        plant.meters["upright"] += 1
        out.append("__recover__")
    if sunlit and plant.meters["dimness"] >= THRESHOLD and ("recover_sun", plant.id) not in world.fired:
        world.fired.add(("recover_sun", plant.id))
        plant.meters["dimness"] = 0.0
        plant.meters["pale"] = 0.0
        plant.meters["droop"] = 0.0
        plant.meters["upright"] += 1
        out.append("__recover__")
    if supported and plant.meters["bend"] >= THRESHOLD and ("recover_support", plant.id) not in world.fired:
        world.fired.add(("recover_support", plant.id))
        plant.meters["bend"] = 0.0
        plant.meters["droop"] = 0.0
        plant.meters["upright"] += 1
        out.append("__recover__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="thirst_droop", tag="physical", apply=_r_thirst_droop),
    Rule(name="dark_pale", tag="physical", apply=_r_dark_pale),
    Rule(name="bend_slump", tag="physical", apply=_r_bent_slump),
    Rule(name="recover", tag="physical", apply=_r_recover),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


PLACES = {
    "apartment": Place(
        id="apartment",
        label="the apartment building hall",
        child_trip="crossed the hall in soft socks with both hands around the little pot",
        helper_name="Mrs. Rami",
        helper_type="woman",
        helper_line="from her doorway with a warm, low voice",
        ending_image="The hall felt brighter when the door opened and the little plant stood tall between them.",
        tags={"home", "neighbor"},
    ),
    "corner_shop": Place(
        id="corner_shop",
        label="the corner flower shop",
        child_trip="walked slowly past the bread shelf and the bucket of tulips by the door",
        helper_name="Mr. Vega",
        helper_type="man",
        helper_line="while tying paper around a bunch of flowers",
        ending_image="The bell over the shop door gave a happy little ring as the plant lifted its leaves.",
        tags={"shop", "neighbor"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the small courtyard downstairs",
        child_trip="hurried through the courtyard where laundry lines moved in the breeze",
        helper_name="Auntie Jo",
        helper_type="woman",
        helper_line="from beside the watering can and the bicycle rack",
        ending_image="By the time the shadows stretched long across the courtyard, the plant looked ready to smile back.",
        tags={"home", "outdoors"},
    ),
}

PLANTS = {
    "basil": PlantSpec(
        id="basil",
        label="basil plant",
        phrase="a little basil plant that smelled fresh and peppery",
        color="green",
        gift_line="It would make the kitchen windowsill smell lively again.",
        responds_to={"thirsty", "dark"},
        tags={"plant", "basil"},
    ),
    "violet": PlantSpec(
        id="violet",
        label="violet",
        phrase="a small violet in a blue pot",
        color="purple",
        gift_line="Its tiny purple flowers looked like folded-up smiles.",
        responds_to={"thirsty", "dark"},
        tags={"plant", "violet"},
    ),
    "daisy": PlantSpec(
        id="daisy",
        label="daisy",
        phrase="a round white daisy in a striped paper sleeve",
        color="white",
        gift_line="Its bright face seemed made for cheering up a quiet room.",
        responds_to={"thirsty", "bent"},
        tags={"plant", "daisy"},
    ),
}

PROBLEMS = {
    "thirsty": ProblemSpec(
        id="thirsty",
        label="thirsty",
        visible="the soil looked pale and crumbly, and the leaves hung down at the edges",
        child_worry="What if it stayed tired-looking all evening?",
        wait_line="For a while nothing happened, and the wait felt longer than the whole afternoon.",
        needs="a slow drink of water",
        tags={"water", "plant"},
    ),
    "dark": ProblemSpec(
        id="dark",
        label="kept in the dark",
        visible="the leaves leaned to one side, searching for the light",
        child_worry="What if it never lifted its face again before the visit?",
        wait_line="The plant stayed still in the dim room, and the child kept checking every few minutes.",
        needs="a bright window and a little time",
        tags={"sunlight", "plant"},
    ),
    "bent": ProblemSpec(
        id="bent",
        label="bent",
        visible="one soft stem had folded sideways after the pot gave a tiny tip",
        child_worry="What if the stem stayed crooked and sad?",
        wait_line="The new tie looked neat, but for a little while the flower still leaned weakly.",
        needs="gentle support",
        tags={"support", "tip"},
    ),
}

TIPS = {
    "water": TipSpec(
        id="water",
        label="water",
        quote='"Here is a tip," the helper said. "Set the pot in a dish, give it a slow drink, and let the roots wake up."',
        act_text="set the pot in a shallow dish and poured in water a little at a time",
        qa_text="gave the plant a slow drink of water",
        fixes={"thirsty"},
        tags={"water", "kindness"},
    ),
    "window": TipSpec(
        id="window",
        label="sunny window",
        quote='"Here is a tip," the helper said. "Turn it toward the light and leave it on a bright sill for a while."',
        act_text="turned the pot toward the brightest window and moved it onto the sunny sill",
        qa_text="moved the plant to a bright window",
        fixes={"dark"},
        tags={"sunlight", "kindness"},
    ),
    "stake": TipSpec(
        id="stake",
        label="little stake",
        quote='"Here is a tip," the helper said. "Tie the bent stem to a little stick, soft and loose, so it can stand again."',
        act_text="slid in a clean little stick and tied the bent stem with a soft loop of string",
        qa_text="gave the bent stem gentle support with a little stake",
        fixes={"bent"},
        tags={"support", "kindness", "tip"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Ruby", "Tessa", "June", "Ava"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Sam", "Eli", "Noah", "Finn"]
NEIGHBOR_NAMES = ["Mrs. Chen", "Mr. Ortiz", "Ms. Bell", "Mrs. Green"]
TRAITS = ["careful", "gentle", "quiet", "thoughtful", "hopeful", "steady"]


def problem_fits(plant_id: str, problem_id: str) -> bool:
    return problem_id in PLANTS[plant_id].responds_to


def tip_fixes(problem_id: str, tip_id: str) -> bool:
    return problem_id in TIPS[tip_id].fixes


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for plant_id in PLANTS:
            for problem_id in PROBLEMS:
                for tip_id in TIPS:
                    if problem_fits(plant_id, problem_id) and tip_fixes(problem_id, tip_id):
                        combos.append((place_id, plant_id, problem_id, tip_id))
    return combos


def predict_recovery(world: World, problem_id: str, tip_id: str) -> dict:
    sim = world.copy()
    plant = sim.get("plant")
    apply_problem(sim, plant, problem_id, narrate=False)
    do_tip(sim, plant, tip_id, narrate=False)
    return {
        "upright": plant.meters["upright"] >= THRESHOLD,
        "droop": plant.meters["droop"],
    }


def apply_problem(world: World, plant: Entity, problem_id: str, narrate: bool = True) -> None:
    if problem_id == "thirsty":
        plant.meters["thirst"] += 1
    elif problem_id == "dark":
        plant.meters["dimness"] += 1
    elif problem_id == "bent":
        plant.meters["bend"] += 1
    propagate(world, narrate=narrate)


def do_tip(world: World, plant: Entity, tip_id: str, narrate: bool = True) -> None:
    if tip_id == "water":
        plant.meters["water"] += 1
    elif tip_id == "window":
        plant.meters["sunlight"] += 1
    elif tip_id == "stake":
        plant.meters["support"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, neighbor: Entity, plant_spec: PlantSpec) -> None:
    world.say(
        f"After school, {child.id} carried {plant_spec.phrase} home. "
        f"{plant_spec.gift_line}"
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} wanted to bring it to {neighbor.id}, "
        f"who had been resting at home all week."
    )
    child.memes["kindness"] += 1
    neighbor.memes["care_received"] += 1


def walk_to_place(world: World, child: Entity) -> None:
    world.say(
        f"In {world.place.label}, {child.id} {world.place.child_trip}."
    )


def discover_problem(world: World, child: Entity, plant: Entity, problem: ProblemSpec) -> None:
    plant.meters["noticed_bad"] += 1
    child.memes["worry"] += 1
    world.say(
        f"Then {child.pronoun('subject')} stopped. {problem.visible}."
    )
    world.say(
        f"{child.id}'s heart gave a small jump. {problem.child_worry}"
    )


def ask_for_help(world: World, child: Entity, helper: Entity) -> None:
    child.memes["hope"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{child.id} looked up at {helper.id}, who was nearby {world.place.helper_line}, "
        f"and whispered, \"Do you know what to do?\""
    )


def give_tip(world: World, helper: Entity, tip: TipSpec) -> None:
    world.say(tip.quote)


def follow_tip(world: World, child: Entity, plant: Entity, tip: TipSpec) -> None:
    child.memes["care"] += 1
    world.say(
        f"{child.id} nodded and {tip.act_text}."
    )
    do_tip(world, plant, tip.id, narrate=False)


def suspense_wait(world: World, child: Entity, problem: ProblemSpec) -> None:
    child.memes["worry"] += 1
    world.say(problem.wait_line)
    world.say(
        f"{child.id} sat close by and watched without bumping the table once."
    )


def transform(world: World, child: Entity, plant: Entity, plant_spec: PlantSpec) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"At last, the change came slowly and then all at once. The {plant_spec.label} lifted itself upright again."
    )
    if plant.meters["sunlight"] >= THRESHOLD:
        world.say(
            f"The {plant_spec.color} leaves turned toward the window as if they had remembered where morning lived."
        )
    elif plant.meters["water"] >= THRESHOLD:
        world.say(
            f"The leaves looked plumper, and the whole little plant no longer seemed thirsty."
        )
    elif plant.meters["support"] >= THRESHOLD:
        world.say(
            "The stem rested against its small support and stopped trembling."
        )


def gift_scene(world: World, child: Entity, neighbor: Entity, plant_spec: PlantSpec) -> None:
    child.memes["kindness"] += 1
    neighbor.memes["comfort"] += 1
    world.say(
        f"By evening, {child.id} knocked on {neighbor.id}'s door and held out the {plant_spec.label} with both hands."
    )
    world.say(
        f"\"This is for you,\" {child.pronoun('subject')} said. {neighbor.id} smiled so softly that the whole doorway changed."
    )
    world.say(
        world.place.ending_image
    )


def tell(
    place: Place,
    plant_spec: PlantSpec,
    problem: ProblemSpec,
    tip: TipSpec,
    child_name: str = "Maya",
    child_type: str = "girl",
    neighbor_name: str = "Mrs. Chen",
    neighbor_type: str = "woman",
    trait: str = "gentle",
) -> World:
    world = World(place)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[trait],
    ))
    neighbor = world.add(Entity(
        id=neighbor_name,
        kind="character",
        type=neighbor_type,
        label=neighbor_name,
        role="neighbor",
    ))
    helper = world.add(Entity(
        id=place.helper_name,
        kind="character",
        type=place.helper_type,
        label=place.helper_name,
        role="helper",
    ))
    plant = world.add(Entity(
        id="plant",
        kind="thing",
        type="plant",
        label=plant_spec.label,
        phrase=plant_spec.phrase,
        tags=set(plant_spec.tags),
    ))

    introduce(world, child, neighbor, plant_spec)
    walk_to_place(world, child)

    world.para()
    apply_problem(world, plant, problem.id, narrate=False)
    discover_problem(world, child, plant, problem)
    ask_for_help(world, child, helper)
    give_tip(world, helper, tip)

    world.para()
    follow_tip(world, child, plant, tip)
    suspense_wait(world, child, problem)
    transform(world, child, plant, plant_spec)

    world.para()
    gift_scene(world, child, neighbor, plant_spec)

    world.facts.update(
        child=child,
        neighbor=neighbor,
        helper=helper,
        plant=plant,
        place=place,
        plant_spec=plant_spec,
        problem=problem,
        tip=tip,
        transformed=plant.meters["upright"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    plant: str
    problem: str
    tip: str
    child_name: str
    child_gender: str
    neighbor_name: str
    neighbor_gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    neighbor = f["neighbor"]
    plant_spec = f["plant_spec"]
    problem = f["problem"]
    tip = f["tip"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "tip" and shows kindness, suspense, and transformation.',
        f"Tell a gentle story where {child.id} wants to cheer up {neighbor.id} with {plant_spec.phrase}, but notices that it is {problem.label} and needs help first.",
        f"Write a quiet neighborhood story where one good tip helps a child care for a struggling plant, and end with a small but visible change.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    neighbor = f["neighbor"]
    helper = f["helper"]
    plant_spec = f["plant_spec"]
    problem = f["problem"]
    tip = f["tip"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted to do something kind for {neighbor.id}. It also includes {helper.id}, who shared a helpful tip.",
        ),
        (
            f"Why was {child.id} carrying the {plant_spec.label}?",
            f"{child.id} wanted to cheer up {neighbor.id}, who had been resting at home. The plant was meant to be a small, gentle gift.",
        ),
        (
            f"What was wrong with the plant?",
            f"The plant was {problem.label}. {child.id} could see that because {problem.visible}.",
        ),
        (
            f"What tip did {helper.id} give?",
            f"{helper.id} told {child.id} how to help the plant: {tip.qa_text}. The advice matched what the plant needed.",
        ),
        (
            "Why did the middle of the story feel suspenseful?",
            f"{child.id} had to wait and watch to see whether the plant would recover in time. {problem.wait_line}",
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                "How did the plant transform by the end?",
                f"It changed from looking weak and droopy to standing upright again. That visible change showed that the careful help had worked.",
            )
        )
    qa.append(
        (
            f"How did the story end?",
            f"It ended with {child.id} bringing the healthy-looking plant to {neighbor.id}. The gift felt even kinder because {child.pronoun('subject')} had worked to save it first.",
        )
    )
    return qa


KNOWLEDGE = {
    "plant": [
        (
            "What does a plant need to stay healthy?",
            "Plants need the right things, like water, light, and gentle care. Different problems need different kinds of help."
        )
    ],
    "water": [
        (
            "Why do droopy plants sometimes need water?",
            "A thirsty plant can droop because its leaves and stems are low on water. When it drinks enough, it can stand up better again."
        )
    ],
    "sunlight": [
        (
            "Why does sunlight help many plants?",
            "Sunlight gives plants energy to grow. When a plant is kept too dark, it may lean and look weak as it searches for light."
        )
    ],
    "support": [
        (
            "Why would someone tie a bent stem to a little stick?",
            "A small stick can hold the stem steady while it rests. Gentle support helps the plant stand instead of falling over."
        )
    ],
    "tip": [
        (
            "What is a tip?",
            "A tip is a small piece of helpful advice. It can show you an easier or better way to do something."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means noticing what someone or something needs and trying to help. Small caring actions can make a big difference."
        )
    ],
    "neighbor": [
        (
            "What is a neighbor?",
            "A neighbor is someone who lives near you, like next door or in the same building. Neighbors can help and care for each other."
        )
    ],
}
KNOWLEDGE_ORDER = ["tip", "plant", "water", "sunlight", "support", "kindness", "neighbor"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["plant_spec"].tags) | set(f["problem"].tags) | set(f["tip"].tags)
    tags.add("tip")
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
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="apartment",
        plant="daisy",
        problem="bent",
        tip="stake",
        child_name="Nora",
        child_gender="girl",
        neighbor_name="Mrs. Chen",
        neighbor_gender="woman",
        trait="careful",
    ),
    StoryParams(
        place="corner_shop",
        plant="basil",
        problem="thirsty",
        tip="water",
        child_name="Owen",
        child_gender="boy",
        neighbor_name="Mr. Ortiz",
        neighbor_gender="man",
        trait="thoughtful",
    ),
    StoryParams(
        place="courtyard",
        plant="violet",
        problem="dark",
        tip="window",
        child_name="Maya",
        child_gender="girl",
        neighbor_name="Ms. Bell",
        neighbor_gender="woman",
        trait="gentle",
    ),
]


def explain_rejection(plant_id: str, problem_id: str, tip_id: str) -> str:
    if not problem_fits(plant_id, problem_id):
        plant = PLANTS[plant_id]
        problem = PROBLEMS[problem_id]
        return (
            f"(No story: a {plant.label} is not set up here to suffer from being {problem.label}. "
            f"Pick a problem that fits that plant.)"
        )
    if not tip_fixes(problem_id, tip_id):
        problem = PROBLEMS[problem_id]
        tip = TIPS[tip_id]
        return (
            f"(No story: the tip '{tip.label}' does not solve a plant that is {problem.label}. "
            f"Use the kind of help that matches the problem.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
fits(Plant, Problem) :- plant_problem(Plant, Problem).
fixes(Tip, Problem)  :- tip_fixes(Tip, Problem).

valid(Place, Plant, Problem, Tip) :-
    place(Place), plant(Plant), problem(Problem), tip(Tip),
    fits(Plant, Problem), fixes(Tip, Problem).

ready :- chosen_plant(P), chosen_problem(Pr), chosen_tip(T),
         fits(P, Pr), fixes(T, Pr).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        for problem_id in sorted(plant.responds_to):
            lines.append(asp.fact("plant_problem", plant_id, problem_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for tip_id, tip in TIPS.items():
        lines.append(asp.fact("tip", tip_id))
        for problem_id in sorted(tip.fixes):
            lines.append(asp.fact("tip_fixes", tip_id, problem_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ready(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_plant", params.plant),
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_tip", params.tip),
    ])
    model = asp.one_model(asp_program(extra, "#show ready/0."))
    return bool(asp.atoms(model, "ready"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: one helpful tip, one struggling plant, one kind surprise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tip", choices=TIPS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--neighbor-gender", choices=["woman", "man"])
    ap.add_argument("--child-name")
    ap.add_argument("--neighbor-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plant and args.problem and not problem_fits(args.plant, args.problem):
        bad_tip = args.tip or next(iter(TIPS))
        raise StoryError(explain_rejection(args.plant, args.problem, bad_tip))
    if args.problem and args.tip and not tip_fixes(args.problem, args.tip):
        bad_plant = args.plant or next(iter(PLANTS))
        raise StoryError(explain_rejection(bad_plant, args.problem, args.tip))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.plant is None or combo[1] == args.plant)
        and (args.problem is None or combo[2] == args.problem)
        and (args.tip is None or combo[3] == args.tip)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, plant_id, problem_id, tip_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    neighbor_gender = args.neighbor_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    neighbor_name = args.neighbor_name or rng.choice(NEIGHBOR_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        plant=plant_id,
        problem=problem_id,
        tip=tip_id,
        child_name=child_name,
        child_gender=child_gender,
        neighbor_name=neighbor_name,
        neighbor_gender=neighbor_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.plant not in PLANTS:
        raise StoryError(f"(Unknown plant: {params.plant})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.tip not in TIPS:
        raise StoryError(f"(Unknown tip: {params.tip})")
    if not problem_fits(params.plant, params.problem) or not tip_fixes(params.problem, params.tip):
        raise StoryError(explain_rejection(params.plant, params.problem, params.tip))

    world = tell(
        place=PLACES[params.place],
        plant_spec=PLANTS[params.plant],
        problem=PROBLEMS[params.problem],
        tip=TIPS[params.tip],
        child_name=params.child_name,
        child_type=params.child_gender,
        neighbor_name=params.neighbor_name,
        neighbor_type=params.neighbor_gender,
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

    for params in CURATED:
        ready_py = problem_fits(params.plant, params.problem) and tip_fixes(params.problem, params.tip)
        ready_asp = asp_ready(params)
        if ready_py != ready_asp:
            rc = 1
            print(f"MISMATCH in ready check for curated params: {params}")
            break
    else:
        print(f"OK: ASP ready check matches Python on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke-tested normal story generation.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show ready/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, plant, problem, tip) combos:\n")
        for place_id, plant_id, problem_id, tip_id in combos:
            print(f"  {place_id:12} {plant_id:8} {problem_id:8} {tip_id}")
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
            header = f"### {p.child_name}: {p.plant} / {p.problem} / {p.tip} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
