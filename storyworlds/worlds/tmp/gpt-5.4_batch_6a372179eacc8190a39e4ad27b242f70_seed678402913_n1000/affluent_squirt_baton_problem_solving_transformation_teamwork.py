#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/affluent_squirt_baton_problem_solving_transformation_teamwork.py
===========================================================================================

A standalone story world about two children turning a plain wagon into a parade
float with a squirt bottle, a baton, and teamwork.

The seed asked for the words "affluent", "squirt", and "baton", with the story
features Problem Solving, Transformation, and Teamwork, in a style close to a
small adventurous tale. This world rebuilds that premise as a tiny simulation:

    * two children invent a river-parade game in a neat, affluent courtyard
    * their float material is too dry and stiff to shape
    * one child first tries to tug it into place
    * the other child reasons about the problem and suggests a careful squirt
      of water
    * together they lift, tie, and transform the plain wagon into something
      grand enough for the pretend parade

The world prefers only combinations that make common-sense crafting sense:
the chosen material must actually soften under a light squirt of water, and the
chosen baton must be sturdy enough to hold the float shape.

Run it
------
    python storyworlds/worlds/gpt-5.4/affluent_squirt_baton_problem_solving_transformation_teamwork.py
    python storyworlds/worlds/gpt-5.4/affluent_squirt_baton_problem_solving_transformation_teamwork.py --theme harbor --material crepe_paper --baton twirler_baton
    python storyworlds/worlds/gpt-5.4/affluent_squirt_baton_problem_solving_transformation_teamwork.py --material poster_board
    python storyworlds/worlds/gpt-5.4/affluent_squirt_baton_problem_solving_transformation_teamwork.py --baton paper_tube
    python storyworlds/worlds/gpt-5.4/affluent_squirt_baton_problem_solving_transformation_teamwork.py --all
    python storyworlds/worlds/gpt-5.4/affluent_squirt_baton_problem_solving_transformation_teamwork.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/affluent_squirt_baton_problem_solving_transformation_teamwork.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    water_friendly: bool = False
    sturdy: bool = False
    flexible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
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
        }.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    opening: str
    call_a: str
    call_b: str
    mission: str
    parade_name: str
    ending_line: str


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    color: str
    dry_problem: str
    softened: str
    water_friendly: bool = False
    flexible: bool = False
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Baton:
    id: str
    label: str
    phrase: str
    sturdy: bool = False
    sparkle: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    article: str
    plain_name: str
    transformed_name: str
    attach_text: str
    closing_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]

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


def _r_transform(world: World) -> list[str]:
    wagon = world.get("wagon")
    material = world.get("material")
    baton = world.get("baton")
    a = world.get("lead")
    b = world.get("partner")
    if wagon.meters["transformed"] >= THRESHOLD:
        return []
    if material.meters["soft"] >= THRESHOLD and baton.meters["ready"] >= THRESHOLD:
        if a.memes["helping"] >= THRESHOLD and b.memes["helping"] >= THRESHOLD:
            world.fired.add(("transform",))
            wagon.meters["transformed"] += 1
            wagon.meters["plain"] = 0.0
            a.memes["joy"] += 1
            b.memes["joy"] += 1
            a.memes["pride"] += 1
            b.memes["pride"] += 1
            return ["__transform__"]
    return []


def _r_crumple(world: World) -> list[str]:
    material = world.get("material")
    if material.meters["dry"] < THRESHOLD or material.meters["tugged"] < THRESHOLD:
        return []
    sig = ("crumple", material.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    material.meters["crumpled"] += 1
    for kid in world.kids():
        kid.memes["frustration"] += 1
    return ["__crumple__"]


CAUSAL_RULES = [
    Rule(name="transform", tag="physical", apply=_r_transform),
    Rule(name="crumple", tag="physical", apply=_r_crumple),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def workable(material: Material, baton: Baton) -> bool:
    return material.water_friendly and material.flexible and baton.sturdy


def outcome_of(params: "StoryParams") -> str:
    material = MATERIALS[params.material]
    return "patched" if params.approach == "tug_first" and material.fragile else "grand"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in THEMES:
        for material_id, material in MATERIALS.items():
            for baton_id, baton in BATONS.items():
                for target_id in TARGETS:
                    if workable(material, baton):
                        combos.append((theme_id, material_id, baton_id, target_id))
    return combos


def predict_solution(world: World) -> dict:
    sim = world.copy()
    material = sim.get("material")
    baton = sim.get("baton")
    a = sim.get("lead")
    b = sim.get("partner")
    material.meters["soft"] += 1
    material.meters["dry"] = 0.0
    baton.meters["ready"] += 1
    a.memes["helping"] += 1
    b.memes["helping"] += 1
    propagate(sim, narrate=False)
    return {
        "transformed": sim.get("wagon").meters["transformed"] >= THRESHOLD,
        "soft": sim.get("material").meters["soft"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, adult: Entity, theme: Theme, target: Target) -> None:
    wagon = world.get("wagon")
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} played in {theme.scene}, an affluent courtyard with clipped hedges, a splashing fountain, and smooth stone paths."
    )
    world.say(
        f"{theme.opening} A plain wagon waited beside them, and to the children it looked ready to become {target.article} {target.transformed_name}."
    )
    world.say(
        f'"{theme.call_a} {a.id} and {theme.call_b} {b.id}!" {a.id} shouted. "{theme.mission}!"'
    )
    adult_name = adult.label_word.capitalize()
    wagon.meters["plain"] += 1
    world.say(
        f"{adult_name} smiled from the shade and let them borrow the craft basket, as long as they worked gently and together."
    )


def present_problem(world: World, a: Entity, b: Entity, material: Material, baton: Baton, target: Target) -> None:
    world.say(
        f"They had {material.phrase} for the float and {baton.phrase} for the mast, but the {material.label} was so dry that {material.dry_problem}."
    )
    world.say(
        f"{b.id} lifted one end and frowned. \"If it stays like this, our {target.transformed_name} will never stand up for {THEMES[world.facts['theme_id']].parade_name}.\""
    )


def tug_attempt(world: World, a: Entity, material_ent: Entity) -> None:
    material_ent.meters["tugged"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{a.id} tried to pull the {material_ent.label} into shape. It gave a dry little crinkle instead, and the edges buckled the wrong way.'
    )
    if material_ent.meters["crumpled"] >= THRESHOLD:
        world.say(
            f"For one worried breath, the plan looked ready to flop."
        )


def reason_and_plan(world: World, b: Entity, a: Entity, adult: Entity, material: Material) -> None:
    pred = predict_solution(world)
    b.memes["idea"] += 1
    world.facts["predicted_transformed"] = pred["transformed"]
    world.say(
        f'{b.id} touched the {material.label} with careful fingers. "Wait," {b.pronoun()} said. "Dry things snap, but soft things bend. Let\'s solve it instead of yanking it."'
    )
    world.say(
        f'{adult.label_word.capitalize()} had left a little squirt bottle by the fountain, and {b.id} pointed to it. "Just one small squirt," {b.pronoun()} said. "Not a soak."'
    )


def soften(world: World, a: Entity, b: Entity, material_ent: Entity, material: Material) -> None:
    material_ent.meters["soft"] += 1
    material_ent.meters["dry"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} gave the {material.label} a careful squirt of water. The color deepened at once, and the {material.label} {material.softened}."
    )


def teamwork_build(world: World, a: Entity, b: Entity, baton_ent: Entity, target: Target, baton: Baton) -> None:
    baton_ent.meters["ready"] += 1
    a.memes["helping"] += 1
    b.memes["helping"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} held the {baton.label} high while {b.id} wrapped the softened material around it. Then {b.id} steadied the knot while {a.id} tied the ribbon tight."
    )
    world.say(
        f"Together they {target.attach_text}."
    )
    if world.get("wagon").meters["transformed"] >= THRESHOLD:
        world.say(
            f"The plain wagon changed before their eyes. Now it looked like {target.article} {target.transformed_name}, and even the fountain light seemed to clap on its sides."
        )
    if baton.sparkle:
        world.say(
            f"The {baton.label} flashed {baton.sparkle}, as if it had been waiting all day to become part of the game."
        )


def patch_if_needed(world: World, a: Entity, b: Entity, material: Material) -> None:
    if not material.fragile or world.facts.get("approach") != "tug_first":
        return
    world.say(
        f"One corner had wrinkled from the first hard tug, so {a.id} and {b.id} smoothed it together and hid it under a neat bow."
    )
    world.say(
        "That made the float look even more special, because the fix became part of the design."
    )


def parade_finish(world: World, a: Entity, b: Entity, target: Target, theme: Theme, adult: Entity) -> None:
    for kid in (a, b):
        kid.memes["teamwork"] += 1
        kid.memes["confidence"] += 1
    adult_name = adult.label_word.capitalize()
    world.say(
        f'{adult_name} came over and laughed softly. "There," {adult.pronoun()} said. "That is what clever teamwork looks like."'
    )
    world.say(
        f"{a.id} climbed to the front of the wagon, and {b.id} trotted beside it with a hand on the side. They rolled into {theme.parade_name} with their {target.transformed_name} gleaming."
    )
    world.say(
        target.closing_image
    )
    world.say(
        theme.ending_line
    )


def tell(
    theme: Theme,
    material: Material,
    baton: Baton,
    target: Target,
    approach: str,
    lead_name: str,
    lead_gender: str,
    partner_name: str,
    partner_gender: str,
    adult_type: str,
    trait: str,
) -> World:
    world = World()
    a = world.add(Entity(
        id="lead",
        kind="character",
        type=lead_gender,
        label=lead_name,
        role="lead",
        traits=["bold"],
        attrs={"name": lead_name},
    ))
    b = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        traits=[trait],
        attrs={"name": partner_name},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        role="adult",
    ))
    wagon = world.add(Entity(
        id="wagon",
        type="wagon",
        label="wagon",
        phrase="the plain wagon",
    ))
    material_ent = world.add(Entity(
        id="material",
        type="material",
        label=material.label,
        phrase=material.phrase,
        water_friendly=material.water_friendly,
        flexible=material.flexible,
        tags=set(material.tags),
    ))
    baton_ent = world.add(Entity(
        id="baton",
        type="baton",
        label=baton.label,
        phrase=baton.phrase,
        sturdy=baton.sturdy,
        tags=set(baton.tags),
    ))
    material_ent.meters["dry"] += 1
    world.facts.update(
        theme=theme,
        theme_id=theme.id,
        material=material,
        baton=baton,
        target=target,
        approach=approach,
        lead=a,
        partner=b,
        adult=adult,
        wagon=wagon,
    )

    introduce(world, a, b, adult, theme, target)
    present_problem(world, a, b, material, baton, target)

    world.para()
    if approach == "tug_first":
        tug_attempt(world, a, material_ent)
    reason_and_plan(world, b, a, adult, material)
    soften(world, a, b, material_ent, material)

    world.para()
    teamwork_build(world, a, b, baton_ent, target, baton)
    patch_if_needed(world, a, b, material)
    parade_finish(world, a, b, target, theme, adult)

    world.facts["outcome"] = outcome_of(StoryParams(
        theme=theme.id,
        material=material.id,
        baton=baton.id,
        target=target.id,
        approach=approach,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        adult=adult_type,
        trait=trait,
        seed=None,
    ))
    return world


THEMES = {
    "harbor": Theme(
        id="harbor",
        scene="the long back court behind Aunt Mira's house",
        opening="The children had decided the fountain was a silver harbor and the path was a river road.",
        call_a="Captain",
        call_b="Mate",
        mission="Let's build the grandest boat in the whole courtyard parade",
        parade_name="the Harbor Parade",
        ending_line="And off they rolled, not because one child had been strongest, but because both children had been clever together.",
    ),
    "island": Theme(
        id="island",
        scene="the sunny stone yard behind Grandpa's townhouse",
        opening="To them, the hedges were jungle walls and the fountain was the sea around a hidden island.",
        call_a="Skipper",
        call_b="Scout",
        mission="Let's carry our treasure cart to the island festival",
        parade_name="the Island Festival",
        ending_line="The game felt bigger now, because the best part of it was the part they had solved side by side.",
    ),
    "river": Theme(
        id="river",
        scene="the neat garden court by Grandma's bright windows",
        opening="They imagined the smooth path as a moonlit river where tiny parade boats would glide past the roses.",
        call_a="Helm",
        call_b="Guide",
        mission="Let's launch the finest river float before the roses close",
        parade_name="the River March",
        ending_line="From then on, whenever a plan felt stuck and stiff, they remembered that teamwork could change its shape.",
    ),
}

MATERIALS = {
    "crepe_paper": Material(
        id="crepe_paper",
        label="crepe paper",
        phrase="a roll of blue crepe paper",
        color="blue",
        dry_problem="it kept curling into sharp little folds",
        softened="relaxed into soft waves",
        water_friendly=True,
        flexible=True,
        fragile=False,
        tags={"paper", "water", "craft"},
    ),
    "tissue_paper": Material(
        id="tissue_paper",
        label="tissue paper",
        phrase="sheets of bright tissue paper",
        color="bright",
        dry_problem="they crackled and slipped apart in papery whispers",
        softened="settled gently without fighting their hands",
        water_friendly=True,
        flexible=True,
        fragile=True,
        tags={"paper", "water", "craft"},
    ),
    "cloth_streamers": Material(
        id="cloth_streamers",
        label="cloth streamers",
        phrase="a bundle of green cloth streamers",
        color="green",
        dry_problem="the twists were stubborn and would not lie flat",
        softened="fell into easy folds",
        water_friendly=True,
        flexible=True,
        fragile=False,
        tags={"cloth", "water", "craft"},
    ),
    "poster_board": Material(
        id="poster_board",
        label="poster board",
        phrase="a sheet of silver poster board",
        color="silver",
        dry_problem="it bent in stiff corners instead of flowing",
        softened="darkened with spots but stayed hard and awkward",
        water_friendly=False,
        flexible=False,
        fragile=False,
        tags={"board", "craft"},
    ),
}

BATONS = {
    "twirler_baton": Baton(
        id="twirler_baton",
        label="baton",
        phrase="a parade baton with rubber tips",
        sturdy=True,
        sparkle="in the sun",
        tags={"baton", "parade"},
    ),
    "garden_stake": Baton(
        id="garden_stake",
        label="garden stake",
        phrase="a smooth bamboo garden stake",
        sturdy=True,
        sparkle="between the leaves",
        tags={"pole", "garden"},
    ),
    "wooden_dowel": Baton(
        id="wooden_dowel",
        label="wooden dowel",
        phrase="a straight wooden dowel from the tool shelf",
        sturdy=True,
        sparkle="like a polished oar",
        tags={"wood", "craft"},
    ),
    "paper_tube": Baton(
        id="paper_tube",
        label="paper tube",
        phrase="a long paper tube from wrapping paper",
        sturdy=False,
        sparkle="for one floppy second",
        tags={"tube", "craft"},
    ),
}

TARGETS = {
    "swan_boat": Target(
        id="swan_boat",
        label="swan boat",
        article="a",
        plain_name="wagon",
        transformed_name="swan boat",
        attach_text="fitted the new sail and curved neck to the front of the wagon",
        closing_image="The wagon rolled past the roses like a swan on green water, and the children bowed to every tulip as if it were a cheering crowd.",
        tags={"boat", "parade"},
    ),
    "sea_dragon": Target(
        id="sea_dragon",
        label="sea dragon",
        article="a",
        plain_name="wagon",
        transformed_name="sea dragon",
        attach_text="lashed the crest and waving back-fin to the sides of the wagon",
        closing_image="Its streamer scales shivered in the breeze, and the whole sea dragon seemed ready to splash straight out of the fountain.",
        tags={"dragon", "parade"},
    ),
    "treasure_ship": Target(
        id="treasure_ship",
        label="treasure ship",
        article="a",
        plain_name="wagon",
        transformed_name="treasure ship",
        attach_text="raised a tall mast and tied bright streamers all along the wagon rails",
        closing_image="The transformed ship bobbed along the path so proudly that even the fountain drops looked like tiny silver coins.",
        tags={"ship", "parade"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "thoughtful", "steady", "clever", "patient", "calm"]


@dataclass
class StoryParams:
    theme: str
    material: str
    baton: str
    target: str
    approach: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "affluent": [(
        "What does affluent mean?",
        "Affluent means having plenty of money or things. In this story, the affluent courtyard is a neat, comfortable place with pretty extras like hedges and a fountain."
    )],
    "squirt": [(
        "What is a squirt of water?",
        "A squirt is a small quick spray. A careful squirt can dampen something a little without soaking it."
    )],
    "baton": [(
        "What is a baton?",
        "A baton is a light stick used in marching, twirling, or signaling. In this story, it also works like a mast or frame for the float."
    )],
    "paper": [(
        "Why does a little water sometimes help paper bend?",
        "A tiny bit of water can make some paper softer for a moment, so it bends more gently. Too much water can tear it, so you have to be careful."
    )],
    "cloth": [(
        "Why do cloth streamers move nicely in a parade?",
        "Cloth is soft and flexible, so it can fold and wave in the air. That makes it good for flags and streamers."
    )],
    "teamwork": [(
        "What is teamwork?",
        "Teamwork is when people help one another on the same job. One person can hold, another can tie, and together they do what would be hard alone."
    )],
    "problem_solving": [(
        "What does problem solving mean?",
        "Problem solving means noticing what is wrong, thinking about why it is happening, and trying a smart fix. Good problem solving is calm and careful."
    )],
    "transformation": [(
        "What is a transformation?",
        "A transformation is a change from one thing into another kind of thing. In pretend play, a plain wagon can transform into a swan boat or treasure ship."
    )],
}
KNOWLEDGE_ORDER = ["affluent", "squirt", "baton", "paper", "cloth", "teamwork", "problem_solving", "transformation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    material = f["material"]
    target = f["target"]
    theme = f["theme"]
    return [
        'Write a short story for a 3-to-5-year-old that includes the words "affluent", "squirt", and "baton".',
        f"Tell a child-facing adventure where {lead.label} and {partner.label} use teamwork and problem solving to transform a plain wagon into {target.article} {target.transformed_name}.",
        f"Write a gentle pretend-play tale in a neat, affluent courtyard where dry {material.label} will not behave until the children discover a clever use for a small squirt of water during {theme.parade_name}.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["lead"]
    b = f["partner"]
    adult = f["adult"]
    material = f["material"]
    baton = f["baton"]
    target = f["target"]
    theme = f["theme"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.label} and {b.label}, playing an outdoor make-believe game. {adult.label_word.capitalize()} is nearby, but the children are the ones who solve the big craft problem."
        ),
        (
            "What problem did the children have?",
            f"They wanted to turn a plain wagon into {target.article} {target.transformed_name}, but the {material.label} was too dry and stiff to shape. That stopped the parade plan right in the middle."
        ),
        (
            f"Why did {b.label} suggest the squirt bottle?",
            f"{b.label} noticed that dry material was fighting their hands and would bend better if it became softer. The little squirt was a careful fix, not a wild splash, so it solved the real problem."
        ),
        (
            "How did the baton help?",
            f"The {baton.label} gave the float a strong piece to hold the shape up, like a mast or frame. Without that sturdy stick, the new decoration would have drooped instead of standing proudly."
        ),
        (
            "How did teamwork matter in the story?",
            f"One child held the frame while the other wrapped and tied the softened material. They succeeded because the job needed more than one pair of hands at the same time."
        ),
    ]
    if world.get("material").meters["crumpled"] >= THRESHOLD:
        qa.append((
            "Did anything go wrong before the solution worked?",
            f"Yes. {a.label} tugged at the dry {material.label}, and it crinkled the wrong way. That little setback showed why a calmer plan was better than pulling harder."
        ))
    if outcome == "patched":
        qa.append((
            "What kind of ending did the children get?",
            f"They got a happy patched ending. Their float still transformed beautifully, and the wrinkled corner became part of the design because they fixed it together."
        ))
    else:
        qa.append((
            "What kind of ending did the children get?",
            f"They got a smooth, grand ending. Once the material softened and the baton held firm, the wagon transformed neatly and rolled into {theme.parade_name} looking magical."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the children proudly rolling their transformed {target.transformed_name} into the pretend parade. The final image proves the change: the wagon is no longer plain, because their teamwork has turned it into something new."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"affluent", "squirt", "baton", "teamwork", "problem_solving", "transformation"}
    material = world.facts["material"]
    if "paper" in material.tags:
        tags.add("paper")
    if "cloth" in material.tags:
        tags.add("cloth")
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = []
        if e.water_friendly:
            flags.append("water_friendly")
        if e.sturdy:
            flags.append("sturdy")
        if e.flexible:
            flags.append("flexible")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="harbor",
        material="crepe_paper",
        baton="twirler_baton",
        target="treasure_ship",
        approach="tug_first",
        lead_name="Tom",
        lead_gender="boy",
        partner_name="Lily",
        partner_gender="girl",
        adult="aunt",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        theme="river",
        material="cloth_streamers",
        baton="garden_stake",
        target="swan_boat",
        approach="plan_first",
        lead_name="Mia",
        lead_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        adult="grandmother",
        trait="steady",
        seed=None,
    ),
    StoryParams(
        theme="island",
        material="tissue_paper",
        baton="wooden_dowel",
        target="sea_dragon",
        approach="tug_first",
        lead_name="Max",
        lead_gender="boy",
        partner_name="Zoe",
        partner_gender="girl",
        adult="grandfather",
        trait="clever",
        seed=None,
    ),
    StoryParams(
        theme="harbor",
        material="cloth_streamers",
        baton="twirler_baton",
        target="swan_boat",
        approach="plan_first",
        lead_name="Ella",
        lead_gender="girl",
        partner_name="Noah",
        partner_gender="boy",
        adult="mother",
        trait="patient",
        seed=None,
    ),
]


def explain_material(mid: str) -> str:
    material = MATERIALS[mid]
    return (
        f"(No story: {material.label} is too stiff or unhelpful for this fix. "
        f"A careful squirt should make the material shape better, but {material.label} does not respond that way.)"
    )


def explain_baton(bid: str) -> str:
    baton = BATONS[bid]
    return (
        f"(No story: {baton.label} is too floppy to hold the float up. "
        f"The frame needs a sturdier stick, such as a parade baton, garden stake, or wooden dowel.)"
    )


ASP_RULES = r"""
workable(M, B) :- water_friendly(M), flexible(M), sturdy(B).
valid(T, M, B, G) :- theme(T), material(M), baton(B), target(G), workable(M, B).

outcome(patched) :- chosen_approach(tug_first), fragile_material.
outcome(grand)   :- not outcome(patched).

fragile_material :- chosen_material(M), fragile(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for material_id, material in MATERIALS.items():
        lines.append(asp.fact("material", material_id))
        if material.water_friendly:
            lines.append(asp.fact("water_friendly", material_id))
        if material.flexible:
            lines.append(asp.fact("flexible", material_id))
        if material.fragile:
            lines.append(asp.fact("fragile", material_id))
    for baton_id, baton in BATONS.items():
        lines.append(asp.fact("baton", baton_id))
        if baton.sturdy:
            lines.append(asp.fact("sturdy", baton_id))
    for target_id in TARGETS:
        lines.append(asp.fact("target", target_id))
    for approach in ["plan_first", "tug_first"]:
        lines.append(asp.fact("approach", approach))
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
        asp.fact("chosen_material", params.material),
        asp.fact("chosen_approach", params.approach),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for s in range(30):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: two children solve a float-building problem with a squirt bottle, a baton, and teamwork."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--baton", choices=BATONS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--approach", choices=["plan_first", "tug_first"])
    ap.add_argument("--adult", choices=["mother", "father", "grandmother", "grandfather", "aunt"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and not MATERIALS[args.material].water_friendly:
        raise StoryError(explain_material(args.material))
    if args.material and not MATERIALS[args.material].flexible:
        raise StoryError(explain_material(args.material))
    if args.baton and not BATONS[args.baton].sturdy:
        raise StoryError(explain_baton(args.baton))
    if args.material and args.baton and not workable(MATERIALS[args.material], BATONS[args.baton]):
        raise StoryError("(No story: that material and baton do not make a reasonable float-building pair.)")

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.material is None or c[1] == args.material)
        and (args.baton is None or c[2] == args.baton)
        and (args.target is None or c[3] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, material, baton, target = rng.choice(sorted(combos))
    approach = args.approach or rng.choice(["plan_first", "tug_first"])
    lead_name, lead_gender = _pick_kid(rng)
    partner_name, partner_gender = _pick_kid(rng, avoid=lead_name)
    adult = args.adult or rng.choice(["mother", "father", "grandmother", "grandfather", "aunt"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme,
        material=material,
        baton=baton,
        target=target,
        approach=approach,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        adult=adult,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        material = MATERIALS[params.material]
        baton = BATONS[params.baton]
        target = TARGETS[params.target]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not workable(material, baton):
        if not material.water_friendly or not material.flexible:
            raise StoryError(explain_material(params.material))
        raise StoryError(explain_baton(params.baton))

    world = tell(
        theme=theme,
        material=material,
        baton=baton,
        target=target,
        approach=params.approach,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        adult_type=params.adult,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("lead", params.lead_name).replace("partner", params.partner_name),
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, material, baton, target) combos:\n")
        for theme, material, baton, target in combos:
            print(f"  {theme:8} {material:15} {baton:14} {target}")
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
            header = f"### {p.lead_name} & {p.partner_name}: {p.material} + {p.baton} -> {p.target} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
