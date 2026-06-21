#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/store_teamwork_dialogue_sound_effects_superhero_story.py
===================================================================================

A standalone story world for a small superhero-flavored store adventure.

Premise
-------
Two children in a store imagine themselves as a superhero team. One child spots
a wanted item that is hard to reach. The tempting but unsafe move would make a
display wobble and spill. A teammate warns about the risk, and the ending turns
on whether the warning is enough to stop the unsafe move before anything falls.

This world is intentionally narrow and constraint-checked:
- the target must be the kind of display the unsafe move could actually upset
- the safe plan must truly reach the target
- the declarative ASP twin mirrors the Python gate and outcome logic

Run it
------
python storyworlds/worlds/gpt-5.4/store_teamwork_dialogue_sound_effects_superhero_story.py
python storyworlds/worlds/gpt-5.4/store_teamwork_dialogue_sound_effects_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/store_teamwork_dialogue_sound_effects_superhero_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/store_teamwork_dialogue_sound_effects_superhero_story.py --qa
python storyworlds/worlds/gpt-5.4/store_teamwork_dialogue_sound_effects_superhero_story.py --verify
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
BRAVERY_INIT = 5.0
STEADY_TRAITS = {"steady", "careful", "calm", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "clerk_f", "cashier_f"}
        male = {"boy", "father", "man", "clerk_m", "cashier_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class StoreScene:
    id: str
    place: str
    glow: str
    hero_name: str
    mission_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    place_text: str
    level: str
    unstable: bool
    stack_kind: str
    spill_noun: str
    spill_sound: str
    item_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class UnsafeMove:
    id: str
    label: str
    action_text: str
    fits: set[str] = field(default_factory=set)
    sense: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class SafePlan:
    id: str
    label: str
    reaches: set[str] = field(default_factory=set)
    sense: int = 0
    arrival_text: str = ""
    retrieval_text: str = ""
    teamwork_text: str = ""
    qa_text: str = ""
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "sidekick"}]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble_to_spill(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    if not target or target.meters["wobble"] < THRESHOLD:
        return out
    sig = ("spill", target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["spilled"] += 1
    aisle = world.entities.get("aisle")
    if aisle:
        aisle.meters["mess"] += 1
        aisle.meters["blocked"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__spill__")
    return out


def _r_teamwork_relief(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("cleanup_started") and not world.facts.get("cleanup_relief_done"):
        world.facts["cleanup_relief_done"] = True
        for kid in world.kids():
            kid.memes["relief"] += 1
            kid.memes["teamwork"] += 1
        out.append("__cleanup__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble_to_spill", tag="physical", apply=_r_wobble_to_spill),
    Rule(name="teamwork_relief", tag="social", apply=_r_teamwork_relief),
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


def hazard_at_risk(move: UnsafeMove, target: Target) -> bool:
    return target.unstable and target.stack_kind in move.fits


def sensible_plans() -> list[SafePlan]:
    return [plan for plan in SAFE_PLANS.values() if plan.sense >= SENSE_MIN]


def can_reach(plan: SafePlan, target: Target) -> bool:
    return target.level in plan.reaches


def initial_caution(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_avert(relation: str, leader_age: int, sidekick_age: int, trait: str) -> bool:
    sidekick_older = relation == "siblings" and sidekick_age > leader_age
    authority = initial_caution(trait) + 1.0 + (3.0 if sidekick_older else 0.0)
    return sidekick_older and authority > BRAVERY_INIT


def predict_spill(world: World, target_id: str) -> dict:
    sim = world.copy()
    tgt = sim.get(target_id)
    tgt.meters["wobble"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": tgt.meters["spilled"] >= THRESHOLD,
        "blocked": sim.get("aisle").meters["blocked"] if "aisle" in sim.entities else 0.0,
    }


def play_setup(world: World, leader: Entity, sidekick: Entity, scene: StoreScene) -> None:
    leader.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    leader.memes["hero"] += 1
    sidekick.memes["hero"] += 1
    world.say(
        f"On a bright afternoon, {leader.id} and {sidekick.id} walked into the store. "
        f"{scene.glow}"
    )
    world.say(
        f"Right away they whispered their superhero names. "
        f'"{leader.id} was {scene.hero_name} Blaze, and {sidekick.id} was Captain Helper," '
        f"{leader.id} declared."
    )
    world.say(
        f'"This is our {scene.mission_word} mission," {sidekick.id} said, peeking up and down the aisle.'
    )


def spot_goal(world: World, leader: Entity, sidekick: Entity, target: Target) -> None:
    world.say(
        f"Then they saw {target.phrase} {target.place_text}. It looked exactly like the sort of prize a superhero team would need."
    )
    world.say(f'"There it is!" {leader.id} said. "{target.label.capitalize()} for the mission!"')


def temptation(world: World, leader: Entity, move: UnsafeMove, target: Target) -> None:
    leader.memes["bravado"] += 1
    world.say(
        f"{leader.id}'s eyes flashed. "
        f'"I can get it myself," {leader.pronoun()} said. "I will {move.action_text}."'
    )
    world.say("For one tiny second, the plan sounded fast and daring.")


def warn(world: World, sidekick: Entity, leader: Entity, move: UnsafeMove, target: Target, adult: Entity) -> None:
    pred = predict_spill(world, "target")
    sidekick.memes["caution"] += 1
    world.facts["predicted_blocked"] = pred["blocked"]
    extra = ""
    if sidekick.memes["caution"] >= 6:
        extra = f" {sidekick.pronoun().capitalize()} planted both sneakers on the floor like a real superhero guard."
    world.say(
        f'{sidekick.id} shook {sidekick.pronoun("possessive")} head. '
        f'"Wait! If you {move.label}, the stack could wobble."'
        f"{extra}"
    )
    if pred["spill"]:
        world.say(
            f'"Then {target.spill_noun} could tumble into the aisle with a {target.spill_sound.lower()}," '
            f"{sidekick.id} warned. "
            f'"Let\'s ask {adult.label} and use teamwork instead."'
        )


def back_down(world: World, leader: Entity, sidekick: Entity, move: UnsafeMove, adult: Entity) -> None:
    leader.memes["bravery"] = 0.0
    leader.memes["relief"] += 1
    sidekick.memes["relief"] += 1
    world.say(
        f'{leader.id} looked up, then down, then back at {sidekick.id}. '
        f'"Okay," {leader.pronoun()} said. "A real hero does not make a bigger problem just to be fast."'
    )
    world.say(
        f'Together they waved to {adult.label} and called, "Store team, we need help!"'
    )


def defy(world: World, leader: Entity, sidekick: Entity, move: UnsafeMove) -> None:
    leader.memes["defiance"] += 1
    world.say(
        f'"Stand back," {leader.id} said. "I can do it."'
    )
    world.say(
        f"But before {sidekick.id} could stop {leader.pronoun('object')}, {leader.pronoun()} tried to {move.action_text}."
    )


def trigger_spill(world: World, target_ent: Entity, target: Target) -> None:
    target_ent.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{target.item_sound}! The display gave a shaky wiggle. Then came {target.spill_sound}! "
        f"{target.spill_noun.capitalize()} slid and bounced into the aisle."
    )


def alarm(world: World, sidekick: Entity, leader: Entity, adult: Entity) -> None:
    world.say(f'"Uh-oh!" {leader.id} gasped.')
    world.say(f'"Store helper!" {sidekick.id} called. "{adult.label.capitalize()}, please!"')


def arrive_and_help(world: World, adult: Entity, plan: SafePlan, target: Target, leader: Entity, sidekick: Entity) -> None:
    for kid in (leader, sidekick):
        kid.memes["trust"] += 1
    world.say(
        f"{adult.label.capitalize()} hurried over. {adult.pronoun().capitalize()} {plan.arrival_text}"
    )
    world.say(
        f'"Super teams use calm hands," {adult.pronoun()} said. "Now let\'s fix the aisle together."'
    )


def cleanup(world: World, adult: Entity, target_ent: Entity, target: Target, leader: Entity, sidekick: Entity) -> None:
    world.facts["cleanup_started"] = True
    target_ent.meters["spilled"] = 0.0
    target_ent.meters["wobble"] = 0.0
    world.get("aisle").meters["mess"] = 0.0
    world.get("aisle").meters["blocked"] = 0.0
    propagate(world, narrate=False)
    leader.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    world.say(
        f"{leader.id} picked up the nearest {target.spill_noun[:-1] if target.spill_noun.endswith('s') else target.spill_noun} while {sidekick.id} gathered the rest into a neat row."
    )
    world.say(
        f'{adult.label.capitalize()} steadied the display, and in a moment the aisle was clear again.'
    )


def retrieve_safely(world: World, adult: Entity, plan: SafePlan, target: Target, leader: Entity, sidekick: Entity) -> None:
    leader.memes["joy"] += 1
    sidekick.memes["joy"] += 1
    leader.memes["teamwork"] += 1
    sidekick.memes["teamwork"] += 1
    world.say(
        f"Then {adult.label} {plan.retrieval_text}"
    )
    world.say(
        f'"Teamwork power!" {leader.id} and {sidekick.id} cheered together.'
    )
    world.say(plan.teamwork_text)


def ending(world: World, scene: StoreScene, target: Target, leader: Entity, sidekick: Entity, adult: Entity, averted: bool) -> None:
    for kid in (leader, sidekick):
        kid.memes["lesson"] += 1
        kid.memes["hero"] += 1
    if averted:
        world.say(
            f"As they rolled their cart onward, {leader.id} grinned at {sidekick.id}. "
            f'The store still felt like a superhero city, only now their best power was asking for help.'
        )
    else:
        world.say(
            f"As they headed to the next aisle, the floor was clear, the display stood straight, and nobody looked scared anymore."
        )
    world.say(
        f'"Next mission?" {sidekick.id} asked.'
    )
    world.say(
        f'"Next mission," {leader.id} agreed, lifting {leader.pronoun("possessive")} chin. '
        f"In the shining store, the bravest heroes were the ones who worked together."
    )


def tell(
    scene: StoreScene,
    target: Target,
    move: UnsafeMove,
    plan: SafePlan,
    *,
    leader_name: str = "Mia",
    leader_gender: str = "girl",
    sidekick_name: str = "Ben",
    sidekick_gender: str = "boy",
    adult_type: str = "mother",
    trait: str = "steady",
    relation: str = "siblings",
    leader_age: int = 5,
    sidekick_age: int = 7,
) -> World:
    world = World()
    leader = world.add(
        Entity(
            id=leader_name,
            kind="character",
            type=leader_gender,
            role="leader",
            traits=["bold"],
            age=leader_age,
            attrs={"relation": relation},
        )
    )
    sidekick = world.add(
        Entity(
            id=sidekick_name,
            kind="character",
            type=sidekick_gender,
            role="sidekick",
            traits=[trait],
            age=sidekick_age,
            attrs={"relation": relation},
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the store clerk" if adult_type.startswith("clerk") else "the parent",
        )
    )
    world.add(Entity(id="aisle", type="aisle", label="the aisle"))
    target_ent = world.add(Entity(id="target", type="display", label=target.label, phrase=target.phrase))

    leader.memes["bravery"] = BRAVERY_INIT
    sidekick.memes["caution"] = initial_caution(trait)

    play_setup(world, leader, sidekick, scene)
    spot_goal(world, leader, sidekick, target)

    world.para()
    temptation(world, leader, move, target)
    warn(world, sidekick, leader, move, target, adult)

    averted = would_avert(relation, leader_age, sidekick_age, trait)

    if averted:
        back_down(world, leader, sidekick, move, adult)
        world.para()
        arrive_and_help(world, adult, plan, target, leader, sidekick)
        retrieve_safely(world, adult, plan, target, leader, sidekick)
    else:
        defy(world, leader, sidekick, move)
        world.para()
        trigger_spill(world, target_ent, target)
        alarm(world, sidekick, leader, adult)
        world.para()
        arrive_and_help(world, adult, plan, target, leader, sidekick)
        cleanup(world, adult, target_ent, target, leader, sidekick)
        retrieve_safely(world, adult, plan, target, leader, sidekick)

    world.para()
    ending(world, scene, target, leader, sidekick, adult, averted)

    world.facts.update(
        scene=scene,
        target_cfg=target,
        move=move,
        plan=plan,
        leader=leader,
        sidekick=sidekick,
        adult=adult,
        relation=relation,
        averted=averted,
        spilled=not averted,
        resolved=True,
    )
    return world


SCENES = {
    "grocery": StoreScene(
        id="grocery",
        place="the grocery store",
        glow="The lights shone on towers of fruit and bright boxes, and every aisle felt like a secret hero base.",
        hero_name="Captain",
        mission_word="store",
        tags={"store", "grocery"},
    ),
    "toy_store": StoreScene(
        id="toy_store",
        place="the toy store",
        glow="Shelves sparkled with games and shiny packages, and the whole store hummed like superhero headquarters.",
        hero_name="Mega",
        mission_word="store",
        tags={"store", "toy"},
    ),
    "corner_store": StoreScene(
        id="corner_store",
        place="the corner store",
        glow="The little store was cozy and bright, with neat rows that looked like streets in a tiny comic-book city.",
        hero_name="Thunder",
        mission_word="store",
        tags={"store", "market"},
    ),
}

TARGETS = {
    "cereal_stack": Target(
        id="cereal_stack",
        label="sparkle cereal",
        phrase="a bright box of sparkle cereal",
        place_text="on the top shelf of a tall cereal stack",
        level="high",
        unstable=True,
        stack_kind="shelf_stack",
        spill_noun="cereal boxes",
        spill_sound="CLATTER-CLATTER!",
        item_sound="Bump",
        tags={"high_shelf", "boxes"},
    ),
    "apple_pyramid": Target(
        id="apple_pyramid",
        label="red apples",
        phrase="a bag of shiny red apples",
        place_text="behind a neat apple pyramid",
        level="middle",
        unstable=True,
        stack_kind="pyramid",
        spill_noun="apples",
        spill_sound="RUMBLE-ROLL!",
        item_sound="Tap",
        tags={"fruit", "roll"},
    ),
    "plush_bin": Target(
        id="plush_bin",
        label="the star cape plush",
        phrase="the star cape plush",
        place_text="dangling above a deep plush bin",
        level="high",
        unstable=False,
        stack_kind="hanger",
        spill_noun="plush toys",
        spill_sound="FLOMP-FLOMP!",
        item_sound="Swish",
        tags={"toy", "hanging"},
    ),
}

UNSAFE_MOVES = {
    "climb_shelf": UnsafeMove(
        id="climb_shelf",
        label="climb the shelf",
        action_text="climb the bottom shelf and reach up",
        fits={"shelf_stack"},
        sense=0,
        tags={"climb", "unsafe"},
    ),
    "pull_bottom": UnsafeMove(
        id="pull_bottom",
        label="pull the bottom item",
        action_text="pull at the bottom of the display",
        fits={"shelf_stack", "pyramid"},
        sense=0,
        tags={"pull", "unsafe"},
    ),
    "tug_side": UnsafeMove(
        id="tug_side",
        label="tug the side of the display",
        action_text="tug the side of the display to make room",
        fits={"pyramid"},
        sense=0,
        tags={"pull", "unsafe"},
    ),
}

SAFE_PLANS = {
    "step_stool": SafePlan(
        id="step_stool",
        label="step stool",
        reaches={"high", "middle"},
        sense=3,
        arrival_text="brought over a little step stool and held it still with one hand.",
        retrieval_text="stepped up carefully and lifted the wanted item down without shaking anything.",
        teamwork_text="The problem felt smaller the moment everyone had a job to do.",
        qa_text="used a step stool and careful hands to get the item safely",
        tags={"step_stool", "ask_adult", "teamwork"},
    ),
    "long_reacher": SafePlan(
        id="long_reacher",
        label="long reacher",
        reaches={"high"},
        sense=3,
        arrival_text="came back with a long reacher and showed them how calm tools beat wild grabbing.",
        retrieval_text="used the long reacher to bring the item down in one smooth, quiet lift.",
        teamwork_text="Even in superhero missions, the smartest tool was better than a risky leap.",
        qa_text="used a long reacher to bring the item down safely",
        tags={"reacher", "ask_adult", "teamwork"},
    ),
    "parent_lift": SafePlan(
        id="parent_lift",
        label="parent lift",
        reaches={"middle"},
        sense=2,
        arrival_text="knelt beside them and stretched one steady arm toward the display.",
        retrieval_text="reached in from the safe side and lifted the wanted item free.",
        teamwork_text="Because they slowed down and worked together, the aisle stayed neat and the mission stayed fun.",
        qa_text="reached from the safe side and lifted the item out carefully",
        tags={"ask_adult", "teamwork"},
    ),
    "jump_grab": SafePlan(
        id="jump_grab",
        label="jump grab",
        reaches={"high"},
        sense=1,
        arrival_text="said maybe a fast jump could work, though it looked wobbly already.",
        retrieval_text="tried a quick grab anyway.",
        teamwork_text="It was a messy plan.",
        qa_text="tried to jump for the item",
        tags={"unsafe"},
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id in SCENES:
        for target_id, target in TARGETS.items():
            for move_id, move in UNSAFE_MOVES.items():
                if not hazard_at_risk(move, target):
                    continue
                for plan_id, plan in SAFE_PLANS.items():
                    if plan.sense >= SENSE_MIN and can_reach(plan, target):
                        combos.append((scene_id, target_id, move_id, plan_id))
    return combos


@dataclass
class StoryParams:
    scene: str
    target: str
    move: str
    plan: str
    leader_name: str
    leader_gender: str
    sidekick_name: str
    sidekick_gender: str
    adult: str
    trait: str
    relation: str = "siblings"
    leader_age: int = 5
    sidekick_age: int = 7
    seed: Optional[int] = None


KNOWLEDGE = {
    "store": [
        (
            "What does a store clerk do?",
            "A store clerk helps people find things, keeps shelves neat, and makes the store safe and tidy."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another do a job together. Each person can do one part, and the whole job gets easier."
        )
    ],
    "high_shelf": [
        (
            "Why should children not climb store shelves?",
            "Store shelves can tip or wobble, and things can fall. It is safer to ask a grown-up for help."
        )
    ],
    "step_stool": [
        (
            "What is a step stool for?",
            "A step stool is a small, steady stool that helps a grown-up reach something safely."
        )
    ],
    "reacher": [
        (
            "What is a long reacher?",
            "A long reacher is a tool that helps someone grab something far away without climbing or pulling."
        )
    ],
    "fruit": [
        (
            "Why do apples roll when they fall?",
            "Apples are round, so when they drop onto the floor they can roll away quickly."
        )
    ],
    "boxes": [
        (
            "Why can a tall stack of boxes wobble?",
            "A tall stack can wobble if you tug one part the wrong way. When the weight shifts, the whole stack may shake."
        )
    ],
}
KNOWLEDGE_ORDER = ["store", "teamwork", "high_shelf", "step_stool", "reacher", "fruit", "boxes"]


def pair_noun(leader: Entity, sidekick: Entity, relation: str) -> str:
    if relation == "siblings":
        if leader.type == "boy" and sidekick.type == "boy":
            return "two brothers"
        if leader.type == "girl" and sidekick.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    sidekick = f["sidekick"]
    target = f["target_cfg"]
    move = f["move"]
    plan = f["plan"]
    averted = f["averted"]
    if averted:
        return [
            'Write a short superhero story for a 3-to-5-year-old that includes the word "store" and uses dialogue, sound effects, and teamwork.',
            f"Tell a superhero-style story where {leader.id} wants to {move.label}, but {sidekick.id} warns about the danger and the team asks for help instead.",
            f"Write a bright store adventure where a child hero listens, uses {plan.label}, and learns that teamwork is a real superpower.",
        ]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the word "store" and uses dialogue, sound effects, and teamwork.',
        f"Tell a superhero-style story where {leader.id} tries to {move.label}, something tumbles with a loud sound effect, and then everyone works together to fix the aisle.",
        f"Write a gentle cautionary story set in a store where children solve a messy problem through dialogue and teamwork instead of panic.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    sidekick = f["sidekick"]
    adult = f["adult"]
    target = f["target_cfg"]
    move = f["move"]
    plan = f["plan"]
    relation = f["relation"]
    pair = pair_noun(leader, sidekick, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.id} and {sidekick.id}, in a store with {adult.label}. They imagined themselves as a superhero team."
        ),
        (
            "What did they see in the store?",
            f"They saw {target.phrase} {target.place_text}. It felt like a special mission prize, which is why {leader.id} wanted it right away."
        ),
        (
            f"Why did {sidekick.id} tell {leader.id} to stop?",
            f"{sidekick.id} knew that if {leader.id} tried to {move.label}, the display could wobble and spill into the aisle. The warning came from noticing the stack was not safe to yank or climb."
        ),
    ]
    if f["averted"]:
        qa.append(
            (
                f"What did {leader.id} do after the warning?",
                f"{leader.id} listened and stopped before touching the display. That choice kept the aisle neat and let the team solve the problem the calm way."
            )
        )
        qa.append(
            (
                "How did they get the item safely?",
                f"They asked for help, and {adult.label} {plan.qa_text}. Because they used teamwork, nobody had to grab or climb."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {leader.id} tried to {move.label}?",
                f"The display wobbled and things spilled into the aisle with a loud sound. The mess happened because the unsafe move shook an unstable stack."
            )
        )
        qa.append(
            (
                "How was the problem fixed?",
                f"First they worked together to clear the aisle, and then {adult.label} {plan.qa_text}. The cleanup mattered because teamwork made the store safe again before they got the item."
            )
        )
    qa.append(
        (
            "What did the children learn at the end?",
            f"They learned that asking for help and working together can be a superhero kind of brave. The ending shows that real heroes keep people safe, not just fast."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"store", "teamwork"}
    tags |= set(f["target_cfg"].tags)
    tags |= set(f["plan"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="grocery",
        target="cereal_stack",
        move="pull_bottom",
        plan="step_stool",
        leader_name="Mia",
        leader_gender="girl",
        sidekick_name="Theo",
        sidekick_gender="boy",
        adult="clerk_f",
        trait="steady",
        relation="siblings",
        leader_age=5,
        sidekick_age=7,
    ),
    StoryParams(
        scene="corner_store",
        target="apple_pyramid",
        move="tug_side",
        plan="parent_lift",
        leader_name="Ben",
        leader_gender="boy",
        sidekick_name="Nora",
        sidekick_gender="girl",
        adult="mother",
        trait="careful",
        relation="friends",
        leader_age=6,
        sidekick_age=6,
    ),
    StoryParams(
        scene="toy_store",
        target="cereal_stack",
        move="climb_shelf",
        plan="long_reacher",
        leader_name="Zoe",
        leader_gender="girl",
        sidekick_name="Max",
        sidekick_gender="boy",
        adult="clerk_m",
        trait="thoughtful",
        relation="siblings",
        leader_age=4,
        sidekick_age=7,
    ),
]


def explain_rejection(move: UnsafeMove, target: Target) -> str:
    if not target.unstable:
        return (
            f"(No story: {target.phrase} is not on an unstable display, so trying to {move.label} would not create the wobble-and-teamwork problem this world models.)"
        )
    if target.stack_kind not in move.fits:
        return (
            f"(No story: trying to {move.label} does not fit the way {target.phrase} is arranged. Pick a move that could truly upset that kind of display.)"
        )
    return "(No story: this move and target do not make a reasonable spill hazard.)"


def explain_plan(plan_id: str) -> str:
    plan = SAFE_PLANS[plan_id]
    better = ", ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense (sense={plan.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.leader_age, params.sidekick_age, params.trait):
        return "averted"
    return "spill"


ASP_RULES = r"""
hazard(M, T) :- unsafe_move(M), target(T), unstable(T), fits(M, K), stack_kind(T, K).
sensible_plan(P) :- safe_plan(P), sense(P, S), sense_min(Min), S >= Min.
reachable(P, T) :- safe_plan(P), target(T), reaches(P, L), level(T, L).
valid(Scene, T, M, P) :- scene(Scene), target(T), unsafe_move(M), safe_plan(P),
                         hazard(M, T), sensible_plan(P), reachable(P, T).

steady_now(T) :- trait(T), steady_trait(T).
init_caution(5) :- trait(T), steady_now(T).
init_caution(3) :- trait(T), not steady_now(T).
sidekick_older :- relation(siblings), leader_age(LA), sidekick_age(SA), SA > LA.
bonus(3) :- sidekick_older.
bonus(0) :- not sidekick_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- sidekick_older, authority(A), bravery_init(B), A > B.

outcome(averted) :- averted.
outcome(spill) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("level", target_id, target.level))
        lines.append(asp.fact("stack_kind", target_id, target.stack_kind))
        if target.unstable:
            lines.append(asp.fact("unstable", target_id))
    for move_id, move in UNSAFE_MOVES.items():
        lines.append(asp.fact("unsafe_move", move_id))
        for fit in sorted(move.fits):
            lines.append(asp.fact("fits", move_id, fit))
    for plan_id, plan in SAFE_PLANS.items():
        lines.append(asp.fact("safe_plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        for level in sorted(plan.reaches):
            lines.append(asp.fact("reaches", plan_id, level))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_plans() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_plan/1."))
    return sorted(p for (p,) in asp.atoms(model, "sensible_plan"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("leader_age", params.leader_age),
            asp.fact("sidekick_age", params.sidekick_age),
            asp.fact("trait", params.trait),
        ]
    )
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

    clingo_plans = set(asp_sensible_plans())
    python_plans = {plan.id for plan in sensible_plans()}
    if clingo_plans == python_plans:
        print(f"OK: sensible plans match ({sorted(clingo_plans)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible plans: clingo={sorted(clingo_plans)} python={sorted(python_plans)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero store storyworld with teamwork, dialogue, and sound effects."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--move", choices=UNSAFE_MOVES)
    ap.add_argument("--plan", choices=SAFE_PLANS)
    ap.add_argument("--adult", choices=["mother", "father", "clerk_f", "clerk_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mia", "Zoe", "Lily", "Nora", "Ava", "Ella", "Ruby", "Lucy"]
BOY_NAMES = ["Ben", "Max", "Theo", "Eli", "Sam", "Noah", "Jack", "Finn"]
TRAITS = ["steady", "careful", "calm", "thoughtful", "curious"]
RELATIONS = ["siblings", "friends"]


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and SAFE_PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))
    if args.move and args.target:
        move = UNSAFE_MOVES[args.move]
        target = TARGETS[args.target]
        if not hazard_at_risk(move, target):
            raise StoryError(explain_rejection(move, target))
    if args.plan and args.target:
        plan = SAFE_PLANS[args.plan]
        target = TARGETS[args.target]
        if plan.sense >= SENSE_MIN and not can_reach(plan, target):
            raise StoryError(
                f"(No story: the plan '{args.plan}' cannot reach {target.phrase}. Pick a plan that works for a {target.level} target.)"
            )

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.target is None or combo[1] == args.target)
        and (args.move is None or combo[2] == args.move)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, target_id, move_id, plan_id = rng.choice(sorted(combos))
    leader_name, leader_gender = _pick_kid(rng)
    sidekick_name, sidekick_gender = _pick_kid(rng, avoid=leader_name)
    adult = args.adult or rng.choice(["mother", "father", "clerk_f", "clerk_m"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(RELATIONS)
    leader_age, sidekick_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        scene=scene_id,
        target=target_id,
        move=move_id,
        plan=plan_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        adult=adult,
        trait=trait,
        relation=relation,
        leader_age=leader_age,
        sidekick_age=sidekick_age,
    )


def _check_params(params: StoryParams) -> None:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.move not in UNSAFE_MOVES:
        raise StoryError(f"(Unknown move: {params.move})")
    if params.plan not in SAFE_PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.adult not in {"mother", "father", "clerk_f", "clerk_m"}:
        raise StoryError(f"(Unknown adult: {params.adult})")

    move = UNSAFE_MOVES[params.move]
    target = TARGETS[params.target]
    plan = SAFE_PLANS[params.plan]
    if not hazard_at_risk(move, target):
        raise StoryError(explain_rejection(move, target))
    if plan.sense < SENSE_MIN:
        raise StoryError(explain_plan(params.plan))
    if not can_reach(plan, target):
        raise StoryError(
            f"(No story: the plan '{params.plan}' cannot safely reach {target.phrase}.)"
        )


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        SCENES[params.scene],
        TARGETS[params.target],
        UNSAFE_MOVES[params.move],
        SAFE_PLANS[params.plan],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        adult_type=params.adult,
        trait=params.trait,
        relation=params.relation,
        leader_age=params.leader_age,
        sidekick_age=params.sidekick_age,
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
        print(asp_program("", "#show valid/4.\n#show sensible_plan/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        plans = asp_sensible_plans()
        print(f"sensible plans: {', '.join(plans)}\n")
        print(f"{len(combos)} compatible (scene, target, move, plan) combos:\n")
        for scene, target, move, plan in combos:
            print(f"  {scene:12} {target:13} {move:12} {plan}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.leader_name} & {p.sidekick_name}: {p.target} with {p.move} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
