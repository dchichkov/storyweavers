#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/swarm_construction_ease_mystery_to_solve_misunderstanding.py
=======================================================================================

A standalone storyworld about a child who thinks a tiny swarm is stealing
building supplies, only to discover the little workers are solving a problem of
their own. In this tall-tale flavored world, a mystery grows from missing
materials, a misunderstanding sends the child snooping after clues, and an
inner monologue carries the turn from suspicion to wonder. The resolution comes
when the child copies the swarm's construction trick and makes a bigger crossing
with ease.

Run it
------
python storyworlds/worlds/gpt-5.4/swarm_construction_ease_mystery_to_solve_misunderstanding.py
python storyworlds/worlds/gpt-5.4/swarm_construction_ease_mystery_to_solve_misunderstanding.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/swarm_construction_ease_mystery_to_solve_misunderstanding.py --all
python storyworlds/worlds/gpt-5.4/swarm_construction_ease_mystery_to_solve_misunderstanding.py --qa --json
python storyworlds/worlds/gpt-5.4/swarm_construction_ease_mystery_to_solve_misunderstanding.py --verify
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
        female = {"girl", "woman", "mother", "aunt", "grandmother"}
        male = {"boy", "man", "father", "uncle", "grandfather"}
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
class Place:
    id: str
    label: str
    horizon: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    plural: bool
    action: str
    tiny_work: str
    big_work: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    cause: str
    tiny_need: str
    crossing: str
    pass_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Vehicle:
    id: str
    label: str
    phrase: str
    load: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_mystery(world: World) -> list[str]:
    hero = world.get("hero")
    stash = world.get("stash")
    if stash.meters["missing"] < THRESHOLD:
        return []
    sig = ("mystery", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["suspicion"] += 1
    hero.memes["curiosity"] += 1
    return []


def _r_clue(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["trail_seen"] < THRESHOLD:
        return []
    sig = ("clue", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["certainty"] += 1
    return []


def _r_discovery(world: World) -> list[str]:
    hero = world.get("hero")
    swarm = world.get("swarm")
    obstacle = world.get("obstacle")
    if swarm.meters["building"] < THRESHOLD or obstacle.meters["observed"] < THRESHOLD:
        return []
    sig = ("discovery", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["wonder"] += 2
    hero.memes["suspicion"] = 0.0
    hero.memes["relief"] += 1
    return []


def _r_big_fix(world: World) -> list[str]:
    hero = world.get("hero")
    obstacle = world.get("obstacle")
    if hero.meters["copied_plan"] < THRESHOLD:
        return []
    sig = ("big_fix", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["passable"] += 1
    hero.memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mystery", tag="social", apply=_r_mystery),
    Rule(name="clue", tag="social", apply=_r_clue),
    Rule(name="discovery", tag="social", apply=_r_discovery),
    Rule(name="big_fix", tag="physical", apply=_r_big_fix),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "barnyard": Place(
        id="barnyard",
        label="the barnyard",
        horizon="The red barn stood so tall it looked like it was trying to hold up the sky.",
        tags={"farm"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard",
        horizon="The apple trees leaned in rows like green soldiers guarding the wind.",
        tags={"farm"},
    ),
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        horizon="The river shone and curled like a silver rope dropped by a giant.",
        tags={"water"},
    ),
}

MATERIALS = {
    "pebbles": Material(
        id="pebbles",
        label="pebbles",
        phrase="a neat bucket of smooth pebbles",
        plural=True,
        action="rolled pebbles one by one",
        tiny_work="a tiny stone road",
        big_work="a stout pebble causeway",
        tags={"stones"},
    ),
    "twigs": Material(
        id="twigs",
        label="twigs",
        phrase="a dry stack of straight little twigs",
        plural=True,
        action="dragged twigs longer than their own bodies",
        tiny_work="a tiny twig bridge",
        big_work="a springy twig bridge",
        tags={"wood"},
    ),
}

OBSTACLES = {
    "puddle": Obstacle(
        id="puddle",
        label="puddle",
        phrase="a rain puddle wide as a moon to anything with six legs",
        cause="last night's rain had left a broad puddle across the yard path",
        tiny_need="a raised path over the water",
        crossing="cross the puddle",
        pass_line="rolled across the puddle path with ease",
        tags={"water", "puddle"},
    ),
    "crack": Obstacle(
        id="crack",
        label="crack",
        phrase="a split in the hard ground, black and deep to a tiny traveler",
        cause="the dry ground had opened into a long crack across the footpath",
        tiny_need="a bridge over the gap",
        crossing="cross the crack",
        pass_line="rattled over the bridged crack with ease",
        tags={"crack"},
    ),
    "rut": Obstacle(
        id="rut",
        label="rut",
        phrase="a wagon rut with steep sides and sticky bottoms",
        cause="an old wheel track had sunk into a crooked rut across the lane",
        tiny_need="a firm fill over the dip",
        crossing="cross the rut",
        pass_line="bumped over the filled rut with ease",
        tags={"mud", "rut"},
    ),
}

VEHICLES = {
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="the berry wagon",
        load="baskets of berries",
        tags={"wagon"},
    ),
    "cart": Vehicle(
        id="cart",
        label="cart",
        phrase="the seed cart",
        load="sacks of seed",
        tags={"cart"},
    ),
    "barrow": Vehicle(
        id="barrow",
        label="barrow",
        phrase="the pumpkin barrow",
        load="one round pumpkin almost as big as a chair",
        tags={"barrow"},
    ),
}

COMPATIBLE = {
    ("pebbles", "puddle"),
    ("pebbles", "rut"),
    ("twigs", "crack"),
}

GIRL_NAMES = ["Mira", "Nell", "Tessa", "June", "Clara", "Bess"]
BOY_NAMES = ["Bram", "Jory", "Eli", "Tobin", "Miles", "Cal"]
TRAITS = ["bold", "busy", "curious", "stout-hearted", "quick-eyed"]
ELDERS = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    place: str
    material: str
    obstacle: str
    vehicle: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="barnyard",
        material="pebbles",
        obstacle="puddle",
        vehicle="wagon",
        name="Bram",
        gender="boy",
        elder="grandfather",
        trait="bold",
    ),
    StoryParams(
        place="orchard",
        material="twigs",
        obstacle="crack",
        vehicle="cart",
        name="Mira",
        gender="girl",
        elder="grandmother",
        trait="quick-eyed",
    ),
    StoryParams(
        place="riverbank",
        material="pebbles",
        obstacle="rut",
        vehicle="barrow",
        name="Tobin",
        gender="boy",
        elder="grandfather",
        trait="busy",
    ),
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in PLACES:
        for material in MATERIALS:
            for obstacle in OBSTACLES:
                if (material, obstacle) not in COMPATIBLE:
                    continue
                for vehicle in VEHICLES:
                    combos.append((place, material, obstacle, vehicle))
    return combos


def material_fits(material: str, obstacle: str) -> bool:
    return (material, obstacle) in COMPATIBLE


def explain_rejection(material: Material, obstacle: Obstacle) -> str:
    return (
        f"(No story: {material.label} would not make a sensible way to {obstacle.crossing}. "
        f"This world only allows building methods that really solve the obstacle.)"
    )


def _think(world: World, hero: Entity, text: str) -> None:
    hero.memes["thinking"] += 1
    world.say(f'{hero.id} thought, "{text}"')


def intro(world: World, hero: Entity, elder: Entity, material: Material, obstacle: Obstacle, vehicle: Vehicle) -> None:
    stash = world.get("stash")
    stash.meters["full"] = 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} was a {next(iter([t for t in hero.traits if t != 'little']), 'curious')} {hero.type} "
        f"who believed no ordinary morning should stay ordinary for long."
    )
    world.say(
        f"In {world.place.label}, {world.place.horizon} {hero.id} had been piling up {material.phrase} "
        f"for the grandest patching job in three counties, because {obstacle.cause}."
    )
    world.say(
        f"{elder.label_word.capitalize()} meant to push {vehicle.phrase} loaded with {vehicle.load} that way before supper."
    )


def first_loss(world: World, hero: Entity, material: Material) -> None:
    stash = world.get("stash")
    stash.meters["missing"] += 1
    hero.meters["loss_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the sun climbed over the fence, part of the pile was gone. "
        f"Somebody had {material.action} away in the night."
    )
    _think(world, hero, f"Those are my building bits. Who pinched them?")
    world.facts["missing_once"] = True


def second_loss(world: World, hero: Entity, material: Material) -> None:
    stash = world.get("stash")
    stash.meters["missing"] += 1
    hero.meters["loss_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By the next morning, another little slice had vanished, neat as if measured with a ruler no bigger than a grass blade."
    )
    _think(world, hero, f"A thief is running a whole construction crew out here.")
    world.facts["missing_twice"] = True


def follow_trail(world: World, hero: Entity, material: Material) -> None:
    hero.meters["trail_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} knelt down and followed the clues: a line of dust, a wobbling procession, and one brave crumb of {material.label} shining in the dirt."
    )
    world.say(
        f"Before long {hero.pronoun()} saw them at last: a dark swarm of ants marching in such order they looked like tiny workers after a dinner bell."
    )
    _think(world, hero, "I knew it! A whole army of hard-hat ants!")


def misunderstanding(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["mistaken_blaming"] += 1
    world.say(
        f"For a moment, {hero.id} was sure the swarm had come to rob the pile and ruin the day's work."
    )
    world.say(
        f"{hero.pronoun().capitalize()} puffed up with detective importance and crept closer to catch the little rascals in the act."
    )
    _think(world, hero, f"They must be building a secret road of their own and spoiling mine.")


def discovery(world: World, hero: Entity, material: Material, obstacle: Obstacle) -> None:
    swarm = world.get("swarm")
    obstacle_ent = world.get("obstacle")
    swarm.meters["building"] += 1
    obstacle_ent.meters["observed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} stopped short. The ants were not scattering the load at all. They were laying each piece exactly where the path broke, making {material.tiny_work} so their line could reach a seed on the far side."
    )
    world.say(
        f"The little builders needed {obstacle.tiny_need}, and they had borrowed just enough to make one."
    )
    _think(world, hero, "Well butter my boots. They are not thieves. They are engineers.")
    world.facts["misunderstanding_resolved"] = True


def talk_with_elder(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["trust"] += 1
    world.say(
        f'{hero.id} ran to {elder.label_word} and blurted out the whole mystery. '
        f'"I thought the swarm was stealing, but they were solving a problem," {hero.pronoun()} said.'
    )
    world.say(
        f'{elder.label_word.capitalize()} laughed softly. "Good builders do that," {elder.pronoun()} said. '
        f'"First they notice what is in the way. Then they make a way through."'
    )


def copy_plan(world: World, hero: Entity, material: Material, obstacle: Obstacle, vehicle: Vehicle, elder: Entity) -> None:
    hero.meters["copied_plan"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That was all {hero.id} needed. Down went bigger handfuls of {material.label}, set with care where the wheel would bite and where the ground would hold."
    )
    world.say(
        f"Under {hero.pronoun('possessive')} hands, the little lesson turned into {material.big_work}."
    )
    world.say(
        f"When {elder.label_word} pushed {vehicle.phrase} forward, it {obstacle.pass_line}."
    )
    world.facts["ease_line"] = obstacle.pass_line


def ending(world: World, hero: Entity) -> None:
    swarm = world.get("swarm")
    hero.memes["joy"] += 1
    swarm.memes["order"] += 1
    world.say(
        f"{hero.id} tipped {hero.pronoun('possessive')} hat to the ants. The mystery was solved, the misunderstanding was gone, and the smallest crew in the county had taught the biggest lesson of the day."
    )
    world.say(
        f"After that, whenever {hero.id} saw a swarm at work, {hero.pronoun()} looked twice before calling anybody a thief."
    )


def tell(place: Place, material: Material, obstacle: Obstacle, vehicle: Vehicle,
         name: str, gender: str, elder_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=gender,
        label=name,
        phrase=name,
        role="hero",
        traits=["little", trait],
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=elder_type,
        phrase=f"the {elder_type}",
        role="elder",
    ))
    stash = world.add(Entity(
        id="stash",
        kind="thing",
        type="stash",
        label=material.label,
        phrase=material.phrase,
        role="stash",
        tags=set(material.tags),
    ))
    swarm = world.add(Entity(
        id="swarm",
        kind="thing",
        type="ants",
        label="swarm",
        phrase="a swarm of ants",
        role="builders",
        tags={"swarm", "ants"},
    ))
    obstacle_ent = world.add(Entity(
        id="obstacle",
        kind="thing",
        type=obstacle.id,
        label=obstacle.label,
        phrase=obstacle.phrase,
        role="obstacle",
        tags=set(obstacle.tags),
    ))
    vehicle_ent = world.add(Entity(
        id="vehicle",
        kind="thing",
        type=vehicle.id,
        label=vehicle.label,
        phrase=vehicle.phrase,
        role="vehicle",
        tags=set(vehicle.tags),
    ))

    intro(world, hero, elder, material, obstacle, vehicle)
    world.para()
    first_loss(world, hero, material)
    second_loss(world, hero, material)
    follow_trail(world, hero, material)
    misunderstanding(world, hero, obstacle)
    world.para()
    discovery(world, hero, material, obstacle)
    talk_with_elder(world, hero, elder)
    world.para()
    copy_plan(world, hero, material, obstacle, vehicle, elder)
    ending(world, hero)

    world.facts.update(
        hero=hero,
        elder=elder,
        stash=stash,
        swarm=swarm,
        obstacle=obstacle_ent,
        vehicle=vehicle_ent,
        place=place,
        material=material,
        obstacle_cfg=obstacle,
        vehicle_cfg=vehicle,
        solved=hero.memes["wonder"] >= THRESHOLD and obstacle_ent.meters["passable"] >= THRESHOLD,
        misunderstanding=hero.memes["mistaken_blaming"] >= THRESHOLD,
        passable=obstacle_ent.meters["passable"] >= THRESHOLD,
        missing_count=int(stash.meters["missing"]),
    )
    return world


KNOWLEDGE = {
    "swarm": [
        (
            "What is a swarm?",
            "A swarm is a big group of small creatures moving together. When they work in lines or clusters, they can look busy and powerful."
        )
    ],
    "ants": [
        (
            "Why do ants walk in lines?",
            "Ants often follow scent trails that help them find food and guide each other. That is why they can look like one moving ribbon."
        )
    ],
    "construction": [
        (
            "What does construction mean?",
            "Construction means building something by putting parts together in a planned way. It can be as small as a toy bridge or as big as a real house."
        )
    ],
    "ease": [
        (
            "What does it mean to do something with ease?",
            "Doing something with ease means it feels smooth and not hard anymore. A good tool or a clever plan can make work easier."
        )
    ],
    "puddle": [
        (
            "How can stones help at a puddle?",
            "Stones can make a firmer little path above soft, wet ground. That gives feet or wheels something steadier to press on."
        )
    ],
    "crack": [
        (
            "Why do people put something across a crack?",
            "A crack can catch little feet or wheels. Putting a bridge or cover across it helps travelers get over safely."
        )
    ],
    "rut": [
        (
            "What is a rut?",
            "A rut is a long dip or groove made by wheels or heavy use. It can make a cart bump or stick if the ground is soft."
        )
    ],
}


def pair_name(world: World) -> str:
    hero = world.facts["hero"]
    return hero.label


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    material = f["material"]
    obstacle = f["obstacle_cfg"]
    vehicle = f["vehicle_cfg"]
    return [
        (
            f'Write a tall-tale style story for a 3-to-5-year-old that includes the words '
            f'"swarm," "construction," and "ease," and features a mystery, a misunderstanding, and inner monologue.'
        ),
        (
            f"Tell a story where {hero.label} thinks a swarm is stealing {material.label}, "
            f"but discovers the tiny builders are solving how to {obstacle.crossing}."
        ),
        (
            f"Write a child-facing story in which {hero.label} learns from small builders, "
            f"then helps {elder.label_word} move {vehicle.phrase} with ease."
        ),
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    material = f["material"]
    obstacle = f["obstacle_cfg"]
    vehicle = f["vehicle_cfg"]
    qa = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child who notices that building bits keep disappearing, and {elder.label_word} nearby with work to do. The story also centers on a swarm of ants that seems suspicious at first."
        ),
        (
            f"What was the mystery {hero.label} wanted to solve?",
            f"{hero.label} wanted to know who kept taking {material.label} from the pile. The missing pieces mattered because {hero.pronoun('subject')} needed them to help with the path."
        ),
        (
            f"Why did {hero.label} misunderstand the swarm at first?",
            f"{hero.label} first thought the ants were thieves because the pile kept shrinking and the clues led straight to them. From far away, it looked as if they were hauling away supplies just to spoil the day's work."
        ),
        (
            f"What did {hero.label} discover when {hero.pronoun('subject')} got closer?",
            f"{hero.label} discovered that the swarm was doing careful construction, not stealing. The ants were placing each piece to make a tiny way to {obstacle.crossing}."
        ),
        (
            f"How did the ants' work help {hero.label} solve the bigger problem?",
            f"The ants showed {hero.label} the right idea: build where the path is broken, not just where the pile looks best. After copying their plan on a larger scale, {elder.label_word} could move {vehicle.phrase} with ease."
        ),
        (
            "How did the story end?",
            f"It ended with the obstacle made passable and the mystery solved. {hero.label} stopped blaming the swarm and even tipped {hero.pronoun('possessive')} hat to the tiny builders."
        ),
    ]
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"swarm", "ants", "construction", "ease"}
    tags |= set(f["material"].tags)
    tags |= set(f["obstacle_cfg"].tags)
    ordered = ["swarm", "ants", "construction", "ease", "puddle", "crack", "rut"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(pebbles,puddle).
fits(pebbles,rut).
fits(twigs,crack).

valid(P,M,O,V) :- place(P), material(M), obstacle(O), vehicle(V), fits(M,O).

resolved(M,O) :- fits(M,O).
outcome(solved) :- chosen_material(M), chosen_obstacle(O), resolved(M,O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for material in MATERIALS:
        lines.append(asp.fact("material", material))
    for obstacle in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle))
    for vehicle in VEHICLES:
        lines.append(asp.fact("vehicle", vehicle))
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
        asp.fact("chosen_obstacle", params.obstacle),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if material_fits(params.material, params.obstacle) else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome for curated params:", params)
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a child mistakes a tiny swarm for thieves, then learns from their clever construction."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.material and args.obstacle and not material_fits(args.material, args.obstacle):
        raise StoryError(explain_rejection(MATERIALS[args.material], OBSTACLES[args.obstacle]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.material is None or c[1] == args.material)
        and (args.obstacle is None or c[2] == args.obstacle)
        and (args.vehicle is None or c[3] == args.vehicle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, material, obstacle, vehicle = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        material=material,
        obstacle=obstacle,
        vehicle=vehicle,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.material not in MATERIALS:
        raise StoryError(f"(Unknown material: {params.material})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle: {params.vehicle})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.gender})")
    if params.elder not in set(ELDERS):
        raise StoryError(f"(Unknown elder type: {params.elder})")
    if not material_fits(params.material, params.obstacle):
        raise StoryError(explain_rejection(MATERIALS[params.material], OBSTACLES[params.obstacle]))

    world = tell(
        place=PLACES[params.place],
        material=MATERIALS[params.material],
        obstacle=OBSTACLES[params.obstacle],
        vehicle=VEHICLES[params.vehicle],
        name=params.name,
        gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
    )

    hero = world.get("hero")
    story = world.render().replace("hero", hero.label)
    story = story.replace("elder", world.get("elder").label_word)
    return StorySample(
        params=params,
        story=story.replace("hero", hero.label),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(f"{len(combos)} compatible (place, material, obstacle, vehicle) combos:\n")
        for place, material, obstacle, vehicle in combos:
            print(f"  {place:10} {material:8} {obstacle:8} {vehicle}")
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
            header = f"### {p.name}: {p.material} for {p.obstacle} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
