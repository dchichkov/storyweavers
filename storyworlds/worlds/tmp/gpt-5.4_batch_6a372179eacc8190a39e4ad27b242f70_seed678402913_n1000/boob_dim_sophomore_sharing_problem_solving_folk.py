#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/boob_dim_sophomore_sharing_problem_solving_folk.py
==============================================================================

A standalone storyworld for a small folk-tale-like domain about sharing food and
solving a path problem together.

Seed constraints carried into the world:
- includes the words "boob-dim" and "sophomore"
- centers Sharing and Problem Solving
- keeps a gentle folk-tale tone

Premise
-------
At the boob-dim hour, two village children carry food to an elder. On the way
they meet a hungry creature. If they share, the creature later helps when the
road is blocked. A small share earns a clue; a generous share earns direct aid.
The children still have to think and work together, so the resolution is always
about both kindness and practical problem solving.

Run it
------
    python storyworlds/worlds/gpt-5.4/boob_dim_sophomore_sharing_problem_solving_folk.py
    python storyworlds/worlds/gpt-5.4/boob_dim_sophomore_sharing_problem_solving_folk.py --helper crow --obstacle stream
    python storyworlds/worlds/gpt-5.4/boob_dim_sophomore_sharing_problem_solving_folk.py --helper goat --obstacle gate
    python storyworlds/worlds/gpt-5.4/boob_dim_sophomore_sharing_problem_solving_folk.py --all
    python storyworlds/worlds/gpt-5.4/boob_dim_sophomore_sharing_problem_solving_folk.py --qa
    python storyworlds/worlds/gpt-5.4/boob_dim_sophomore_sharing_problem_solving_folk.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    road_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    plural: bool = True
    portions: int = 4
    offer_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    type: str
    likes: set[str] = field(default_factory=set)
    solves: set[str] = field(default_factory=set)
    need: int = 2
    clue_tags: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    threat: str
    solve_text: str
    clue_text: str
    child_finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareChoice:
    id: str
    label: str
    amount: int
    offer_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    food: str
    helper: str
    obstacle: str
    share: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    elder_type: str
    hero_trait: str
    friend_trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_generosity(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    helper = world.entities.get("helper")
    basket = world.entities.get("basket")
    if hero is None or friend is None or helper is None or basket is None:
        return out
    if basket.meters["shared"] < THRESHOLD:
        return out
    sig = ("generosity", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    helper.memes["gratitude"] += basket.meters["shared"]
    out.append("__shared__")
    return out


def _r_direct_aid(world: World) -> list[str]:
    out: list[str] = []
    path = world.entities.get("path")
    helper = world.entities.get("helper")
    if path is None or helper is None:
        return out
    if path.meters["blocked"] < THRESHOLD:
        return out
    if helper.memes["gratitude"] < helper.attrs.get("need", 2):
        return out
    sig = ("aid", helper.id, path.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path.meters["solved"] += 1
    path.attrs["outcome"] = "aid"
    out.append("__aid__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    path = world.entities.get("path")
    helper = world.entities.get("helper")
    if path is None or helper is None:
        return out
    if path.meters["blocked"] < THRESHOLD or path.meters["solved"] >= THRESHOLD:
        return out
    if helper.memes["gratitude"] < THRESHOLD:
        return out
    sig = ("clue", helper.id, path.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path.meters["hinted"] += 1
    path.attrs["outcome"] = "clue"
    out.append("__clue__")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    friend = world.entities.get("friend")
    elder = world.entities.get("elder")
    basket = world.entities.get("basket")
    path = world.entities.get("path")
    if hero is None or friend is None or elder is None or basket is None or path is None:
        return out
    if basket.meters["delivered"] < THRESHOLD:
        return out
    sig = ("finish", basket.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    elder.memes["gratitude"] += 1
    out.append("__done__")
    return out


CAUSAL_RULES = [
    Rule(name="generosity", tag="social", apply=_r_generosity),
    Rule(name="direct_aid", tag="social", apply=_r_direct_aid),
    Rule(name="clue", tag="social", apply=_r_clue),
    Rule(name="finish", tag="social", apply=_r_finish),
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
        for _ in produced:
            pass
    return produced


SETTINGS = {
    "ford": Setting(
        id="ford",
        place="the willow ford",
        opening="At the boob-dim hour, when the last light lay soft and gray on the thatched roofs",
        road_phrase="the path that bent past the willow ford",
        tags={"village", "ford"},
    ),
    "mill": Setting(
        id="mill",
        place="the old mill lane",
        opening="At the boob-dim hour, when the wind turned the mill sails into dark hands against the sky",
        road_phrase="the lane that curled toward the old mill",
        tags={"village", "mill"},
    ),
    "hill": Setting(
        id="hill",
        place="the lantern hill path",
        opening="At the boob-dim hour, when even the hill path seemed to whisper old songs",
        road_phrase="the narrow path up Lantern Hill",
        tags={"village", "hill"},
    ),
}

FOODS = {
    "sesame_cakes": Food(
        id="sesame_cakes",
        label="sesame cakes",
        phrase="a basket of warm sesame cakes",
        plural=True,
        portions=4,
        offer_text="a warm sesame cake",
        tags={"cakes", "sharing"},
    ),
    "plum_buns": Food(
        id="plum_buns",
        label="plum buns",
        phrase="a basket of sweet plum buns",
        plural=True,
        portions=4,
        offer_text="a soft plum bun",
        tags={"buns", "sharing"},
    ),
    "cheese_pies": Food(
        id="cheese_pies",
        label="cheese pies",
        phrase="a basket of little cheese pies",
        plural=True,
        portions=4,
        offer_text="a buttery cheese pie",
        tags={"pies", "sharing"},
    ),
}

HELPERS = {
    "crow": Helper(
        id="crow",
        label="crow",
        phrase="a black crow with bright button eyes",
        type="bird",
        likes={"sesame_cakes", "plum_buns"},
        solves={"stream"},
        need=2,
        clue_tags={"bird", "crow"},
        tags={"crow", "sharing"},
    ),
    "mouse": Helper(
        id="mouse",
        label="mouse",
        phrase="a small brown mouse with whiskers like thread",
        type="mouse",
        likes={"plum_buns", "cheese_pies"},
        solves={"gate"},
        need=2,
        clue_tags={"mouse", "gate"},
        tags={"mouse", "sharing"},
    ),
    "goat": Helper(
        id="goat",
        label="goat",
        phrase="a sure-footed white goat with a bell under its chin",
        type="goat",
        likes={"sesame_cakes", "cheese_pies"},
        solves={"hill"},
        need=2,
        clue_tags={"goat", "hill"},
        tags={"goat", "sharing"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        id="stream",
        label="stream",
        phrase="a stream that had swollen over the stepping stones",
        threat="The water licked over the stones, and one careless step would send the basket into the cold rush.",
        solve_text="The crow flew to a drooping willow, tugged a green vine loose, and dropped it across the narrowest place. With one hand on the vine and one hand under the basket, the children crossed steady as cats on a wall.",
        clue_text="The crow did not carry anything at all. Instead it flew low above a line of half-hidden stones where the water ran shallowest.",
        child_finish="So the children held the basket between them, stepped where the crow had shown, and crossed one careful foot at a time.",
        tags={"stream", "water", "problem_solving"},
    ),
    "gate": Obstacle(
        id="gate",
        label="gate",
        phrase="a gate tied shut with a wet knot of rope",
        threat="The knot had swollen hard as wood, and the longer they tugged, the tighter it bit.",
        solve_text="The mouse scampered up the post, nibbled the rope where it crossed itself, and loosened the knot just enough. Then the children pulled together, and the gate sighed open.",
        clue_text="The mouse did not bite the rope open. Instead it scratched at a little wooden latch hidden behind a curl of ivy.",
        child_finish="So the children lifted the latch together, pushed with both shoulders, and slipped through before the gate could swing back.",
        tags={"gate", "rope", "problem_solving"},
    ),
    "hill": Obstacle(
        id="hill",
        label="mud hill",
        phrase="a steep hill made slick with new mud",
        threat="The basket was not terribly heavy, but the mud wanted every shoe and every wheel to slide backward.",
        solve_text="The goat planted its hooves, leaned against the load with its sturdy chest, and helped nudge the basket-cart up the steepest part. Then the children steadied the sides and guided it to the top.",
        clue_text="The goat did not push at all. Instead it climbed in a slow zigzag, showing a path where the ground held firm under the grass.",
        child_finish="So the children changed their plan, took the hill sideways as the goat had shown, and shared the basket's weight between them until they reached the top.",
        tags={"hill", "mud", "problem_solving"},
    ),
}

SHARES = {
    "crumb": ShareChoice(
        id="crumb",
        label="a crumb",
        amount=1,
        offer_line="Only a little. We still have a road to finish.",
        tags={"small_share"},
    ),
    "piece": ShareChoice(
        id="piece",
        label="a fair piece",
        amount=2,
        offer_line="Take a fair piece. A hungry traveler should not go on hungry.",
        tags={"fair_share"},
    ),
    "half": ShareChoice(
        id="half",
        label="half the basket's top layer",
        amount=3,
        offer_line="Take half the top layer. Food tastes better when it is shared.",
        tags={"big_share"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Tessa", "Wren", "Elsa", "Mila", "Pia"]
BOY_NAMES = ["Tobin", "Marek", "Ivo", "Pavel", "Nico", "Bram", "Soren", "Eli"]
TRAITS = ["careful", "brave", "thoughtful", "steady", "quick", "gentle"]


def valid_combo(food_id: str, helper_id: str, obstacle_id: str) -> bool:
    food = FOODS[food_id]
    helper = HELPERS[helper_id]
    obstacle = OBSTACLES[obstacle_id]
    return food.id in helper.likes and obstacle.id in helper.solves


def valid_share(food_id: str, share_id: str) -> bool:
    return SHARES[share_id].amount <= FOODS[food_id].portions


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for food_id in FOODS:
        for helper_id in HELPERS:
            for obstacle_id in OBSTACLES:
                if valid_combo(food_id, helper_id, obstacle_id):
                    combos.append((food_id, helper_id, obstacle_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if not valid_combo(params.food, params.helper, params.obstacle):
        raise StoryError("(No story: that helper would neither welcome that food nor solve that road problem.)")
    if not valid_share(params.food, params.share):
        raise StoryError("(No story: the chosen share is larger than the basket can spare.)")
    return "aid" if SHARES[params.share].amount >= HELPERS[params.helper].need else "clue"


def explain_rejection(food: Food, helper: Helper, obstacle: Obstacle) -> str:
    if food.id not in helper.likes:
        return (
            f"(No story: {helper.label} would not come close for {food.label}. "
            f"In this little world, help begins with a creature being drawn by the food that is shared.)"
        )
    if obstacle.id not in helper.solves:
        return (
            f"(No story: {helper.label} cannot reasonably solve the {obstacle.label} problem. "
            f"Choose a helper whose natural skill fits the obstacle.)"
        )
    return "(No story: this combination is not part of the world's folk logic.)"


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
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def helper_arrival_line(helper: Helper) -> str:
    if helper.id == "crow":
        return "a black crow hopped down from a fence post and tipped its head as if listening to the basket"
    if helper.id == "mouse":
        return "a small brown mouse peeped from the hedge, nose twitching at the smell from the basket"
    return "a sure-footed white goat came tinkling along the lane, its bell giving one soft note"


def share_scene(world: World, hero: Entity, friend: Entity, basket: Entity,
                food: Food, helper_cfg: Helper, share_cfg: ShareChoice) -> None:
    helper = world.get("helper")
    hero.memes["concern"] += 1
    friend.memes["concern"] += 1
    world.say(
        f"Along {world.setting.road_phrase}, {helper_arrival_line(helper_cfg)}."
    )
    world.say(
        f'"It looks hungry," {friend.id} said.'
    )
    world.say(
        f'{hero.id} looked at {food.label}, then at the small waiting creature. '
        f'"{share_cfg.offer_line}"'
    )
    basket.meters["shared"] += share_cfg.amount
    basket.meters["portions_left"] = max(0.0, float(food.portions - share_cfg.amount))
    world.facts["shared_amount"] = share_cfg.amount
    world.facts["shared_label"] = share_cfg.label
    world.say(
        f"So they broke off {share_cfg.label} of the {food.label} and set it down. "
        f"The {helper_cfg.label} ate, blinked once, and seemed to remember their kindness."
    )
    propagate(world, narrate=False)


def block_path(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    path = world.get("path")
    path.meters["blocked"] += 1
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f"But before long they came to {obstacle.phrase}. {obstacle.threat}"
    )
    world.say(
        f'"We cannot turn back," {friend.id} said. "{world.get("elder").label.capitalize()} is waiting."'
    )
    propagate(world, narrate=False)


def resolve_obstacle(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    path = world.get("path")
    helper = world.get("helper")
    basket = world.get("basket")
    if path.attrs.get("outcome") == "aid":
        helper.memes["repay"] += 1
        world.say(
            f"Then the {helper.label} returned. {obstacle.solve_text}"
        )
    else:
        world.say(
            f"Then the {helper.label} returned. {obstacle.clue_text}"
        )
        world.say(obstacle.child_finish)
        path.meters["solved"] += 1
    hero.memes["cleverness"] += 1
    friend.memes["cleverness"] += 1
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    basket.meters["delivered"] += 1
    world.say(
        f"Step by step, they kept the basket level and went on together."
    )
    propagate(world, narrate=False)


def tell(setting: Setting, food: Food, helper_cfg: Helper, obstacle: Obstacle,
         share_cfg: ShareChoice, hero_name: str, hero_gender: str,
         friend_name: str, friend_gender: str, elder_type: str,
         hero_trait: str, friend_trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[hero_trait, "sophomore"],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[friend_trait],
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label="old Nan" if elder_type == "mother" else "old Bran",
        role="elder",
    ))
    basket = world.add(Entity(
        id="basket",
        type="basket",
        label="basket",
        phrase=food.phrase,
        role="food",
    ))
    basket.meters["portions_left"] = float(food.portions)
    helper = world.add(Entity(
        id="helper",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={"need": helper_cfg.need},
        tags=set(helper_cfg.tags),
    ))
    path = world.add(Entity(
        id="path",
        type="path",
        label=obstacle.label,
        phrase=obstacle.phrase,
        role="path",
    ))

    world.facts.update(
        setting=setting,
        food=food,
        helper_cfg=helper_cfg,
        obstacle=obstacle,
        share_cfg=share_cfg,
        hero=hero,
        friend=friend,
        elder=elder,
        basket=basket,
        helper=helper,
        path=path,
    )

    world.say(
        f"{setting.opening}, {hero_name}, a {hero_trait} sophomore from the little hill school, "
        f"walked beside {friend_name} with {food.phrase} balanced between them."
    )
    world.say(
        f"They were carrying supper to {elder.label}, who told the best winter tales in the village."
    )
    world.say(
        f"Each child had two hands on the basket handle now and then, for even a small gift feels larger when the road is long."
    )

    world.para()
    share_scene(world, hero, friend, basket, food, helper_cfg, share_cfg)

    world.para()
    block_path(world, hero, friend, obstacle)

    world.para()
    resolve_obstacle(world, hero, friend, obstacle)

    world.para()
    world.say(
        f"When they reached {elder.label}'s door, not one cake or bun or pie had been lost."
    )
    world.say(
        f'{elder.label.capitalize()} looked into the basket, then into their faces. '
        f'"You kept the food safe because you shared first and thought together after," {elder.pronoun()} said.'
    )
    world.say(
        f"So in that village people later said that a kind hand often clears the road before clever feet can see how."
    )

    world.facts["outcome"] = path.attrs.get("outcome", "clue")
    world.facts["delivered"] = basket.meters["delivered"] >= THRESHOLD
    world.facts["shared_enough"] = share_cfg.amount >= helper_cfg.need
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    food = world.facts["food"]
    helper_cfg = world.facts["helper_cfg"]
    obstacle = world.facts["obstacle"]
    outcome = world.facts["outcome"]
    variant = "direct help" if outcome == "aid" else "a helpful clue"
    return [
        f'Write a short folk tale for a 3-to-5-year-old that includes the words "boob-dim" and "sophomore", and centers sharing food on a road.',
        f"Tell a gentle village tale where {hero.label} and {friend.label} share {food.label} with a {helper_cfg.label}, then solve a {obstacle.label} problem together.",
        f"Write a story in a folk-tale voice where kindness brings {variant}, and the children still have to think carefully to finish their errand.",
    ]


KNOWLEDGE = {
    "crow": [
        ("Why do crows notice food quickly?",
         "Crows are clever birds with sharp eyes, so they notice little things on the ground and in people's hands very quickly.")
    ],
    "mouse": [
        ("Why can a mouse help with a rope knot?",
         "A mouse has tiny sharp teeth and a small body, so it can reach tight places and nibble what bigger animals cannot.")
    ],
    "goat": [
        ("Why are goats good on steep hills?",
         "Goats have strong legs and careful hooves, so they can keep their balance on rough or sloping ground.")
    ],
    "stream": [
        ("How can people cross a shallow stream safely?",
         "They go slowly, test each step, and look for the firmest stones or the narrowest place. Holding onto something steady can help too.")
    ],
    "gate": [
        ("Why do knots get harder to untie when rope is wet?",
         "Wet rope swells and tightens, so the strands press harder against each other and the knot grips more strongly.")
    ],
    "hill": [
        ("Why is a muddy hill slippery?",
         "Mud is soft and slick, so shoes can slide instead of gripping the ground well.")
    ],
    "sharing": [
        ("Why does sharing help in a hard moment?",
         "Sharing makes others feel cared for, and cared-for friends or helpers are more likely to help back. It also helps everyone think in a calmer way.")
    ],
    "problem_solving": [
        ("What does problem solving mean?",
         "Problem solving means looking at what is wrong, thinking of a plan, and trying the safest useful idea until the problem is fixed.")
    ],
}
KNOWLEDGE_ORDER = ["sharing", "problem_solving", "crow", "mouse", "goat", "stream", "gate", "hill"]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    food = world.facts["food"]
    helper_cfg = world.facts["helper_cfg"]
    obstacle = world.facts["obstacle"]
    share_cfg = world.facts["share_cfg"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a sophomore from the little hill school, and {friend.label}, who were carrying {food.phrase} to {elder.label}. They had to be kind and careful on the road."
        ),
        (
            "What did the children share?",
            f"They shared {share_cfg.label} of the {food.label} with the hungry {helper_cfg.label}. That act of sharing is what made the helper remember them later."
        ),
        (
            "What problem did they meet on the road?",
            f"They came to {obstacle.phrase}. That blocked the way and made them worry they might spill the basket or arrive too late."
        ),
    ]
    if outcome == "aid":
        qa.append(
            (
                f"How did the {helper_cfg.label} help them?",
                f"The {helper_cfg.label} helped directly when the road was blocked. It did so because the children had shared enough food to earn warm gratitude, and then the children still worked carefully to keep the basket level."
            )
        )
    else:
        qa.append(
            (
                f"How did the {helper_cfg.label} help even without doing the whole job?",
                f"The {helper_cfg.label} gave them a clue instead of solving the whole problem alone. That happened because the children had shared kindly, and the clue let them make a smart plan together."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They reached {elder.label}'s door with the food still safe in the basket. The ending shows that sharing opened the way, and thinking together finished the work."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sharing", "problem_solving", world.facts["helper_cfg"].id, world.facts["obstacle"].id}
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


ASP_RULES = r"""
acceptable(F, H, O) :- food(F), helper(H), obstacle(O), likes(H, F), solves(H, O).
share_ok(F, S) :- food(F), share(S), portions(F, P), amount(S, A), A <= P.
enough(H, S) :- helper(H), share(S), need(H, N), amount(S, A), A >= N.

outcome(aid)  :- chosen_helper(H), chosen_share(S), enough(H, S).
outcome(clue) :- chosen_helper(H), chosen_share(S), not enough(H, S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("portions", fid, food.portions))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("need", hid, helper.need))
        for food_id in sorted(helper.likes):
            lines.append(asp.fact("likes", hid, food_id))
        for obstacle_id in sorted(helper.solves):
            lines.append(asp.fact("solves", hid, obstacle_id))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for sid, share in SHARES.items():
        lines.append(asp.fact("share", sid))
        lines.append(asp.fact("amount", sid, share.amount))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show acceptable/3."))
    return sorted(set(asp.atoms(model, "acceptable")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_share", params.share),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="ford",
        food="plum_buns",
        helper="crow",
        obstacle="stream",
        share="piece",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Tobin",
        friend_gender="boy",
        elder_type="mother",
        hero_trait="thoughtful",
        friend_trait="steady",
    ),
    StoryParams(
        setting="mill",
        food="cheese_pies",
        helper="mouse",
        obstacle="gate",
        share="crumb",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Bram",
        friend_gender="boy",
        elder_type="father",
        hero_trait="careful",
        friend_trait="quick",
    ),
    StoryParams(
        setting="hill",
        food="sesame_cakes",
        helper="goat",
        obstacle="hill",
        share="half",
        hero_name="Marek",
        hero_gender="boy",
        friend_name="Lina",
        friend_gender="girl",
        elder_type="mother",
        hero_trait="brave",
        friend_trait="gentle",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale storyworld about sharing food and solving a road problem together."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (food, helper, obstacle) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.food and args.helper and args.obstacle:
        food = FOODS[args.food]
        helper = HELPERS[args.helper]
        obstacle = OBSTACLES[args.obstacle]
        if not valid_combo(args.food, args.helper, args.obstacle):
            raise StoryError(explain_rejection(food, helper, obstacle))
    if args.food and args.share and not valid_share(args.food, args.share):
        raise StoryError("(No story: the chosen share is larger than the basket can spare.)")

    combos = [
        combo for combo in valid_combos()
        if (args.food is None or combo[0] == args.food)
        and (args.helper is None or combo[1] == args.helper)
        and (args.obstacle is None or combo[2] == args.obstacle)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    food_id, helper_id, obstacle_id = rng.choice(sorted(combos))
    share_options = [sid for sid in SHARES if valid_share(food_id, sid) and (args.share is None or sid == args.share)]
    if not share_options:
        raise StoryError("(No valid share option matches the given options.)")
    setting_id = args.setting or rng.choice(sorted(SETTINGS))
    share_id = rng.choice(sorted(share_options))
    hero_name, hero_gender = _pick_child(rng)
    friend_name, friend_gender = _pick_child(rng, avoid=hero_name)
    elder_type = args.elder or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != hero_trait] or TRAITS)

    return StoryParams(
        setting=setting_id,
        food=food_id,
        helper=helper_id,
        obstacle=obstacle_id,
        share=share_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        elder_type=elder_type,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.share not in SHARES:
        raise StoryError(f"(Unknown share: {params.share})")
    if not valid_combo(params.food, params.helper, params.obstacle):
        raise StoryError(explain_rejection(FOODS[params.food], HELPERS[params.helper], OBSTACLES[params.obstacle]))
    if not valid_share(params.food, params.share):
        raise StoryError("(No story: the chosen share is larger than the basket can spare.)")

    world = tell(
        setting=SETTINGS[params.setting],
        food=FOODS[params.food],
        helper_cfg=HELPERS[params.helper],
        obstacle=OBSTACLES[params.obstacle],
        share_cfg=SHARES[params.share],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        elder_type=params.elder_type,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
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
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    mismatches = 0
    for p in cases:
        py_out = outcome_of(p)
        asp_out = asp_outcome(p)
        if py_out != asp_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show acceptable/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (food, helper, obstacle) combos:\n")
        for food_id, helper_id, obstacle_id in combos:
            print(f"  {food_id:13} {helper_id:8} {obstacle_id}")
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
                f"### {p.hero_name} and {p.friend_name}: {p.food} / {p.helper} / "
                f"{p.obstacle} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
