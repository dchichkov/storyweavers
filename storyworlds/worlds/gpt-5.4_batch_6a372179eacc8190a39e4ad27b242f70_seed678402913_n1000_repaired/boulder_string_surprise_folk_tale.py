#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/boulder_string_surprise_folk_tale.py
===============================================================

A small storyworld for a folk-tale-shaped surprise: a child faces a blocking
boulder, a bit of string seems too small to matter, and a wise helper reveals
that the string is not for strength at all but for cleverness.

The world is built around one compact common-sense gate:
a plan is only valid when the chosen lever and the chosen use of the string
could truly move the chosen boulder in the chosen place. The story then plays
out as a short simulation: worry, failed effort, surprising advice, a grounded
method, and an ending image that proves the path changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/boulder_string_surprise_folk_tale.py
    python storyworlds/worlds/gpt-5.4/boulder_string_surprise_folk_tale.py --place spring --boulder cracked --plan loop
    python storyworlds/worlds/gpt-5.4/boulder_string_surprise_folk_tale.py --lever reed
    python storyworlds/worlds/gpt-5.4/boulder_string_surprise_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/boulder_string_surprise_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/boulder_string_surprise_folk_tale.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "weaver", "mother"}
        male = {"boy", "man", "ferryman", "gardener", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    place: str
    blocked_thing: str
    reward: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BoulderCfg:
    id: str
    label: str
    phrase: str
    shape: str
    heft: int
    can_loop: bool = False
    roundish: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class LeverCfg:
    id: str
    label: str
    phrase: str
    power: int
    sturdy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class PlanCfg:
    id: str
    surprise_line: str
    prep_line: str
    action_line: str
    explain: str
    needs_loop: bool = False
    needs_round: bool = False
    bonus: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    type: str
    title: str
    manner: str
    wisdom: str
    tags: set[str] = field(default_factory=set)


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
    apply: Callable[[World], list[str]]


def _r_blocked_worry(world: World) -> list[str]:
    boulder = world.entities.get("boulder")
    path = world.entities.get("path")
    hero = world.entities.get("hero")
    if not boulder or not path or not hero:
        return []
    sig = ("blocked_worry",)
    if sig in world.fired:
        return []
    if boulder.meters["blocking"] >= THRESHOLD:
        world.fired.add(sig)
        hero.memes["worry"] += 1
        path.meters["closed"] += 1
    return []


def _r_failed_push(world: World) -> list[str]:
    hero = world.entities.get("hero")
    boulder = world.entities.get("boulder")
    if not hero or not boulder:
        return []
    sig = ("failed_push",)
    if sig in world.fired:
        return []
    if hero.meters["push"] >= THRESHOLD and boulder.meters["moved"] < THRESHOLD:
        world.fired.add(sig)
        hero.meters["tired"] += 1
        hero.memes["frustration"] += 1
    return []


def _r_plan_loosen(world: World) -> list[str]:
    boulder = world.entities.get("boulder")
    if not boulder:
        return []
    sig = ("plan_loosen",)
    if sig in world.fired:
        return []
    if boulder.meters["guided"] >= THRESHOLD and boulder.meters["wedged"] >= THRESHOLD:
        world.fired.add(sig)
        boulder.meters["loosened"] += 1
    return []


def _r_move(world: World) -> list[str]:
    boulder = world.entities.get("boulder")
    path = world.entities.get("path")
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if not boulder or not path or not hero or not helper:
        return []
    sig = ("move",)
    if sig in world.fired:
        return []
    if boulder.meters["loosened"] >= THRESHOLD and hero.meters["final_shove"] >= THRESHOLD:
        world.fired.add(sig)
        boulder.meters["moved"] += 1
        boulder.meters["blocking"] = 0.0
        path.meters["closed"] = 0.0
        path.meters["open"] += 1
        hero.memes["surprise"] += 1
        hero.memes["gratitude"] += 1
        helper.memes["calm"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blocked_worry", apply=_r_blocked_worry),
    Rule(name="failed_push", apply=_r_failed_push),
    Rule(name="plan_loosen", apply=_r_plan_loosen),
    Rule(name="move", apply=_r_move),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = (
                sum(sum(ent.meters.values()) for ent in world.entities.values()),
                sum(sum(ent.memes.values()) for ent in world.entities.values()),
            )
            rule.apply(world)
            after = (
                sum(sum(ent.meters.values()) for ent in world.entities.values()),
                sum(sum(ent.memes.values()) for ent in world.entities.values()),
            )
            if after != before:
                changed = True


PLACES = {
    "spring": Place(
        id="spring",
        place="the mountain spring path",
        blocked_thing="the path to the spring",
        reward="fresh water for the village jars",
        ending="the jars rang softly as clear water splashed into them",
        tags={"spring", "water"},
    ),
    "mill": Place(
        id="mill",
        place="the lane to the little mill",
        blocked_thing="the mill lane",
        reward="sacks of grain to be ground before sunset",
        ending="the mill wheel sang again while flour dust floated in the light",
        tags={"mill", "grain"},
    ),
    "orchard": Place(
        id="orchard",
        place="the gate path to the orchard",
        blocked_thing="the orchard gate path",
        reward="ripe pears waiting on the far side",
        ending="the pears glowed like yellow lamps among the leaves",
        tags={"orchard", "fruit"},
    ),
}

BOULDERS = {
    "round": BoulderCfg(
        id="round",
        label="boulder",
        phrase="a round gray boulder",
        shape="round",
        heft=2,
        can_loop=False,
        roundish=True,
        tags={"boulder", "round"},
    ),
    "cracked": BoulderCfg(
        id="cracked",
        label="boulder",
        phrase="a broad cracked boulder",
        shape="cracked",
        heft=3,
        can_loop=True,
        roundish=False,
        tags={"boulder", "crack"},
    ),
    "flat": BoulderCfg(
        id="flat",
        label="boulder",
        phrase="a flat-backed boulder",
        shape="flat",
        heft=4,
        can_loop=False,
        roundish=False,
        tags={"boulder", "heavy"},
    ),
}

LEVERS = {
    "hazel": LeverCfg(
        id="hazel",
        label="hazel pole",
        phrase="a long hazel pole",
        power=3,
        sturdy=True,
        tags={"pole", "wood"},
    ),
    "shaft": LeverCfg(
        id="shaft",
        label="cart shaft",
        phrase="an old cart shaft",
        power=4,
        sturdy=True,
        tags={"shaft", "wood"},
    ),
    "reed": LeverCfg(
        id="reed",
        label="reed stalk",
        phrase="a thin reed stalk",
        power=1,
        sturdy=False,
        tags={"reed"},
    ),
}

PLANS = {
    "marker": PlanCfg(
        id="marker",
        surprise_line='Then the helper lifted the string and smiled. "The string will not drag the boulder," the helper said. "It will show us where the stone likes to rock."',
        prep_line="The helper wrapped the string around the stone and marked the quiet middle where it tipped most easily.",
        action_line="Then the pole went under that marked place, and what had felt stubborn a moment before suddenly gave a small, startled sigh.",
        explain="The string marked the best place to pry, so the lever could bite where the stone would truly rock.",
        needs_loop=False,
        needs_round=False,
        bonus=0,
        tags={"string", "surprise", "lever"},
    ),
    "loop": PlanCfg(
        id="loop",
        surprise_line='The helper took up the string and said, "A string is not always for pulling. Sometimes it is for teaching wood where to stay."',
        prep_line="The helper threaded the string through the boulder's crack and tied the pole fast so it would not slip away.",
        action_line="With the pole held true by the string, the buried edge of the stone lifted little by little until the whole boulder began to roll.",
        explain="The string held the lever in the crack, so the pole did not skid away when they pressed.",
        needs_loop=True,
        needs_round=False,
        bonus=1,
        tags={"string", "surprise", "crack"},
    ),
    "rollers": PlanCfg(
        id="rollers",
        surprise_line='The helper laid the string on the ground and said, "The string is too small to pull the stone. But it is just big enough to keep little things from wandering."',
        prep_line="The helper tied two short branches together with the string and set them like a cradle before the boulder.",
        action_line="The boulder climbed onto the tied branches and rolled as if the earth had decided to help.",
        explain="The string held the little rollers together, so the round stone could roll instead of scraping.",
        needs_loop=False,
        needs_round=True,
        bonus=1,
        tags={"string", "surprise", "rollers"},
    ),
}

HELPERS = {
    "grandmother": HelperCfg(
        id="grandmother",
        type="grandmother",
        title="Old Grandmother Sana",
        manner="walked with a willow basket on her arm",
        wisdom="She was known for seeing the answer hidden inside small things.",
        tags={"elder"},
    ),
    "ferryman": HelperCfg(
        id="ferryman",
        type="ferryman",
        title="the ferryman Doro",
        manner="came up the lane with river water still shining on his boots",
        wisdom="He had learned that heavy things often obeyed patience before strength.",
        tags={"elder"},
    ),
    "weaver": HelperCfg(
        id="weaver",
        type="weaver",
        title="Auntie Mara the weaver",
        manner="appeared with bright thread tucked into her sleeve",
        wisdom="Everyone said her hands understood knots the way birds understand wind.",
        tags={"elder", "string"},
    ),
}

GIRL_NAMES = ["Lina", "Tali", "Mira", "Nessa", "Pia", "Rina"]
BOY_NAMES = ["Ivo", "Niko", "Pavel", "Toma", "Jori", "Milan"]
TRAITS = ["patient", "quick", "earnest", "hopeful", "stubborn", "kind"]


def plan_works(boulder: BoulderCfg, lever: LeverCfg, plan: PlanCfg) -> bool:
    if not lever.sturdy:
        return False
    if plan.needs_loop and not boulder.can_loop:
        return False
    if plan.needs_round and not boulder.roundish:
        return False
    return lever.power + plan.bonus >= boulder.heft


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for boulder_id, boulder in BOULDERS.items():
            for lever_id, lever in LEVERS.items():
                for plan_id, plan in PLANS.items():
                    if plan_works(boulder, lever, plan):
                        combos.append((place_id, boulder_id, lever_id, plan_id))
    return combos


def predict_success(world: World, boulder_id: str, lever_id: str, plan_id: str) -> dict:
    sim = world.copy()
    boulder_cfg = BOULDERS[boulder_id]
    lever_cfg = LEVERS[lever_id]
    plan_cfg = PLANS[plan_id]
    if plan_works(boulder_cfg, lever_cfg, plan_cfg):
        sim.get("boulder").meters["guided"] += 1
        sim.get("boulder").meters["wedged"] += 1
        sim.get("hero").meters["final_shove"] += 1
        propagate(sim)
    return {
        "moved": sim.get("boulder").meters["moved"] >= THRESHOLD,
        "open": sim.get("path").meters["open"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"In a valley where people still listened to crows and wind, {hero.id} set out along {place.place}. "
        f"{hero.pronoun().capitalize()} hoped to bring back {place.reward}."
    )


def problem(world: World, hero: Entity, boulder: Entity, place: Place, boulder_cfg: BoulderCfg) -> None:
    boulder.meters["blocking"] += 1
    propagate(world)
    world.say(
        f"But in the middle of {place.blocked_thing} lay {boulder_cfg.phrase}. "
        f"It was so large that the morning seemed to stop around it."
    )
    world.say(
        f"{hero.id} put both hands on the boulder and pushed. The stone did not move, and only dust answered."
    )
    hero.meters["push"] += 1
    propagate(world)


def lament(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f'"If the stone stays here," {hero.id} said, "then {place.reward} must wait for another day."'
    )


def arrival(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    helper.memes["calm"] += 1
    world.say(
        f"Just then {helper_cfg.title} {helper_cfg.manner}. {helper_cfg.wisdom}"
    )


def notice_string(world: World, hero: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"{hero.id} had only {world.get('string').phrase} and {world.get('lever').phrase}. "
        f"They looked far too small beside the stone."
    )


def helper_plan(world: World, hero: Entity, helper: Entity, boulder: Entity, plan: PlanCfg) -> None:
    pred = predict_success(world, world.facts["boulder_cfg"].id, world.facts["lever_cfg"].id, plan.id)
    helper.memes["confidence"] += 1
    world.facts["predicted_success"] = pred["moved"]
    world.say(plan.surprise_line)
    world.say(plan.prep_line)
    boulder.meters["guided"] += 1
    boulder.meters["wedged"] += 1
    propagate(world)


def final_move(world: World, hero: Entity, helper: Entity, boulder: Entity, plan: PlanCfg) -> None:
    hero.meters["final_shove"] += 1
    propagate(world)
    world.say(plan.action_line)
    if boulder.meters["moved"] >= THRESHOLD:
        world.say(
            f'{hero.id} stared, then laughed. "{world.get("string").label.capitalize()}!" {hero.pronoun()} cried. '
            f'"I thought it was the smallest thing here."'
        )


def ending(world: World, hero: Entity, helper: Entity, place: Place, plan: PlanCfg) -> None:
    world.say(
        f'"Small does not mean useless," {helper.id} said. "{plan.explain}"'
    )
    world.say(
        f"So {place.blocked_thing} opened again, and {place.ending}. "
        f"From that day on, {hero.id} never mocked a little coil of string."
    )


def tell(
    place: Place,
    boulder_cfg: BoulderCfg,
    lever_cfg: LeverCfg,
    plan_cfg: PlanCfg,
    helper_cfg: HelperCfg,
    hero_name: str = "Lina",
    hero_type: str = "girl",
    trait: str = "earnest",
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        role="hero",
        label=hero_name,
        phrase=hero_name,
        traits=[trait],
    ))
    helper = world.add(Entity(
        id=helper_cfg.title,
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.title,
        phrase=helper_cfg.title,
        tags=set(helper_cfg.tags),
    ))
    boulder = world.add(Entity(
        id="boulder",
        type="boulder",
        label="boulder",
        phrase=boulder_cfg.phrase,
        tags=set(boulder_cfg.tags),
    ))
    path = world.add(Entity(
        id="path",
        type="path",
        label=place.blocked_thing,
        phrase=place.blocked_thing,
        tags=set(place.tags),
    ))
    string = world.add(Entity(
        id="string",
        type="string",
        label="string",
        phrase="a coil of string",
        tags={"string"},
    ))
    lever = world.add(Entity(
        id="lever",
        type="lever",
        label=lever_cfg.label,
        phrase=lever_cfg.phrase,
        tags=set(lever_cfg.tags),
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        boulder_cfg=boulder_cfg,
        lever_cfg=lever_cfg,
        plan_cfg=plan_cfg,
        helper_cfg=helper_cfg,
    )

    introduce(world, hero, place)
    problem(world, hero, boulder, place, boulder_cfg)
    lament(world, hero, place)

    world.para()
    arrival(world, helper, helper_cfg)
    notice_string(world, hero)
    helper_plan(world, hero, helper, boulder, plan_cfg)

    world.para()
    final_move(world, hero, helper, boulder, plan_cfg)
    ending(world, hero, helper, place, plan_cfg)

    world.facts.update(
        moved=boulder.meters["moved"] >= THRESHOLD,
        open=path.meters["open"] >= THRESHOLD,
        tired=hero.meters["tired"] >= THRESHOLD,
        surprised=hero.memes["surprise"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    boulder: str
    lever: str
    plan: str
    helper: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "boulder": [
        (
            "What is a boulder?",
            "A boulder is a very large stone. It is much bigger and heavier than the rocks you can pick up in your hand.",
        )
    ],
    "string": [
        (
            "What is string used for?",
            "String is a thin cord you can tie around things. It is not strong enough for every heavy job, but it can hold, guide, or bundle smaller things.",
        )
    ],
    "lever": [
        (
            "What is a lever?",
            "A lever is a stiff bar or pole that helps you lift or move something heavy. It lets a small push do a bigger job.",
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is a place where water comes up from the ground. People and animals often go there for fresh water.",
        )
    ],
    "mill": [
        (
            "What does a mill do?",
            "A mill grinds grain into flour. In old tales, people brought sacks of grain there to be made into meal.",
        )
    ],
    "orchard": [
        (
            "What is an orchard?",
            "An orchard is a place where fruit trees grow in rows. People go there to gather fruit like pears or apples.",
        )
    ],
    "surprise": [
        (
            "Why can a surprise be part of solving a problem?",
            "Sometimes the answer is not the one people expect. A surprising idea can work because it uses the right trick, not just more force.",
        )
    ],
}
KNOWLEDGE_ORDER = ["boulder", "string", "lever", "spring", "mill", "orchard", "surprise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    plan = f["plan_cfg"]
    helper = f["helper_cfg"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "boulder" and "string" and has a surprise in the middle.',
        f"Tell a folk-tale story where {hero.id} finds a boulder blocking {place.blocked_thing}, and {helper.title} shows that a bit of string can help in an unexpected way.",
        f"Write a gentle tale where the surprising trick is this: {plan.explain}",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    plan = f["plan_cfg"]
    boulder_cfg = f["boulder_cfg"]
    lever_cfg = f["lever_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who came to {place.place}, and {helper.id}, who helped with a clever idea.",
        ),
        (
            "What problem did the hero find?",
            f"{hero.id} found {boulder_cfg.phrase} blocking {place.blocked_thing}. Because of that, {place.reward} could not be reached the usual way.",
        ),
        (
            f"Why was the string a surprise?",
            f"The string looked much too small to matter beside the boulder. The surprise was that it was not used for raw pulling at all, but to help the {lever_cfg.label} work in the right way.",
        ),
        (
            "How did they move the boulder?",
            f"They used {lever_cfg.phrase} together with the string, and the plan worked because {plan.explain} That turned a hopeless push into a real movement.",
        ),
        (
            "How did the story end?",
            f"The boulder moved aside and {place.blocked_thing} opened again. In the end, {place.ending}.",
        ),
    ]
    if f.get("tired"):
        qa.append(
            (
                f"Why could {hero.id} not move the boulder alone?",
                f"{hero.id} pushed with both hands, but the stone was too heavy to answer brute force alone. The failed pushing left {hero.pronoun('object')} tired before the clever plan began.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"boulder", "string", "lever", "surprise"}
    place = world.facts["place"]
    if place.id in {"spring", "mill", "orchard"}:
        tags.add(place.id)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:16} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="spring",
        boulder="cracked",
        lever="hazel",
        plan="loop",
        helper="weaver",
        hero_name="Lina",
        hero_type="girl",
        trait="earnest",
    ),
    StoryParams(
        place="mill",
        boulder="round",
        lever="hazel",
        plan="rollers",
        helper="ferryman",
        hero_name="Ivo",
        hero_type="boy",
        trait="hopeful",
    ),
    StoryParams(
        place="orchard",
        boulder="flat",
        lever="shaft",
        plan="marker",
        helper="grandmother",
        hero_name="Mira",
        hero_type="girl",
        trait="patient",
    ),
]


def explain_rejection(boulder: BoulderCfg, lever: LeverCfg, plan: PlanCfg) -> str:
    if not lever.sturdy:
        return (
            f"(No story: {lever.phrase} is too weak to act as a lever for {boulder.phrase}. "
            f"A reed may bend, but it will not move a boulder.)"
        )
    if plan.needs_loop and not boulder.can_loop:
        return (
            f"(No story: the {plan.id} plan needs a crack or notch where the string can hold, "
            f"but {boulder.phrase} offers no such place.)"
        )
    if plan.needs_round and not boulder.roundish:
        return (
            f"(No story: the {plan.id} plan only makes sense for a round stone that can roll. "
            f"{boulder.phrase} would scrape instead of rolling.)"
        )
    return (
        f"(No story: {lever.phrase} with the {plan.id} plan is not enough to move {boulder.phrase}. "
        f"The world only tells versions where the method can truly work.)"
    )


ASP_RULES = r"""
works(B, L, P) :-
    sturdy(L),
    heft(B, H),
    power(L, Pow),
    bonus(P, Bon),
    Pow + Bon >= H,
    not needs_loop(P).
works(B, L, P) :-
    sturdy(L),
    heft(B, H),
    power(L, Pow),
    bonus(P, Bon),
    Pow + Bon >= H,
    needs_loop(P),
    can_loop(B).
works(B, L, P) :-
    sturdy(L),
    heft(B, H),
    power(L, Pow),
    bonus(P, Bon),
    Pow + Bon >= H,
    not needs_loop(P),
    needs_round(P),
    roundish(B).
works(B, L, P) :-
    sturdy(L),
    heft(B, H),
    power(L, Pow),
    bonus(P, Bon),
    Pow + Bon >= H,
    needs_loop(P),
    needs_round(P),
    can_loop(B),
    roundish(B).

invalid_loop(B, P) :- needs_loop(P), not can_loop(B).
invalid_round(B, P) :- needs_round(P), not roundish(B).

valid(Place, B, L, P) :- place(Place), boulder(B), lever(L), plan(P), works(B, L, P),
                         not invalid_loop(B, P), not invalid_round(B, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for boulder_id, boulder in BOULDERS.items():
        lines.append(asp.fact("boulder", boulder_id))
        lines.append(asp.fact("heft", boulder_id, boulder.heft))
        if boulder.can_loop:
            lines.append(asp.fact("can_loop", boulder_id))
        if boulder.roundish:
            lines.append(asp.fact("roundish", boulder_id))
    for lever_id, lever in LEVERS.items():
        lines.append(asp.fact("lever", lever_id))
        lines.append(asp.fact("power", lever_id, lever.power))
        if lever.sturdy:
            lines.append(asp.fact("sturdy", lever_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("bonus", plan_id, plan.bonus))
        if plan.needs_loop:
            lines.append(asp.fact("needs_loop", plan_id))
        if plan.needs_round:
            lines.append(asp.fact("needs_round", plan_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    rng = random.Random(123)
    parser = build_parser()
    defaults = parser.parse_args([])
    try:
        params = resolve_params(defaults, rng)
        sample = generate(params)
        if "boulder" not in sample.story or "string" not in sample.story:
            raise StoryError("story omitted required seed words")
        print("OK: default resolve/generate smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a boulder blocks the way, and a surprising use of string helps move it."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--boulder", choices=BOULDERS)
    ap.add_argument("--lever", choices=LEVERS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid scenario set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.boulder and args.lever and args.plan:
        if not plan_works(BOULDERS[args.boulder], LEVERS[args.lever], PLANS[args.plan]):
            raise StoryError(explain_rejection(BOULDERS[args.boulder], LEVERS[args.lever], PLANS[args.plan]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.boulder is None or combo[1] == args.boulder)
        and (args.lever is None or combo[2] == args.lever)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        if args.boulder and args.lever and args.plan:
            raise StoryError(explain_rejection(BOULDERS[args.boulder], LEVERS[args.lever], PLANS[args.plan]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, boulder_id, lever_id, plan_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        boulder=boulder_id,
        lever=lever_id,
        plan=plan_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_type=hero_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.boulder not in BOULDERS:
        raise StoryError(f"(Unknown boulder: {params.boulder})")
    if params.lever not in LEVERS:
        raise StoryError(f"(Unknown lever: {params.lever})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    boulder_cfg = BOULDERS[params.boulder]
    lever_cfg = LEVERS[params.lever]
    plan_cfg = PLANS[params.plan]
    if not plan_works(boulder_cfg, lever_cfg, plan_cfg):
        raise StoryError(explain_rejection(boulder_cfg, lever_cfg, plan_cfg))

    world = tell(
        place=PLACES[params.place],
        boulder_cfg=boulder_cfg,
        lever_cfg=lever_cfg,
        plan_cfg=plan_cfg,
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, boulder, lever, plan) combos:\n")
        for place_id, boulder_id, lever_id, plan_id in combos:
            print(f"  {place_id:8} {boulder_id:8} {lever_id:8} {plan_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.hero_name}: {p.place}, {p.boulder}, {p.lever}, {p.plan}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
