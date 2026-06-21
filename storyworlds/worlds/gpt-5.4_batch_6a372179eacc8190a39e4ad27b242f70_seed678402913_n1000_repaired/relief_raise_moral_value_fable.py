#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/relief_raise_moral_value_fable.py
============================================================

A small fable-like story world about a little animal who must raise a fallen
branch to reopen a path before rain. The world prefers reasonable tools and
help, and it uses simulated state to tell either a humble, cooperative success
or a cautionary lesson about pride.

Seed requirements
-----------------
Words: relief, raise
Features: Moral Value
Style: Fable

Run it
------
    python storyworlds/worlds/gpt-5.4/relief_raise_moral_value_fable.py
    python storyworlds/worlds/gpt-5.4/relief_raise_moral_value_fable.py --hero rabbit --obstacle branch --method lever
    python storyworlds/worlds/gpt-5.4/relief_raise_moral_value_fable.py --method twig
    python storyworlds/worlds/gpt-5.4/relief_raise_moral_value_fable.py --all
    python storyworlds/worlds/gpt-5.4/relief_raise_moral_value_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/relief_raise_moral_value_fable.py --verify
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class HeroKind:
    id: str
    noun: str
    home: str
    voice: str
    trait: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    blocks: str
    weight: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    power: int
    sense: int
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    noun: str
    style: str
    strength: int
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
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        new.facts = copy.deepcopy(self.facts)
        return new


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clear_path(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    if obstacle.meters["raised"] < THRESHOLD:
        return []
    sig = ("clear", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    path = world.get("path")
    path.meters["open"] += 1
    hero = world.get("hero")
    hero.memes["relief"] += 1
    helper = world.get("helper")
    if helper.kind == "character":
        helper.memes["glad"] += 1
    return []


def _r_stuck_worry(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    hero = world.get("hero")
    if obstacle.meters["raised"] >= THRESHOLD:
        return []
    if hero.memes["strain"] < THRESHOLD:
        return []
    sig = ("worry", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="clear_path", tag="physical", apply=_r_clear_path),
    Rule(name="stuck_worry", tag="emotional", apply=_r_stuck_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


HEROES = {
    "rabbit": HeroKind(
        id="rabbit",
        noun="rabbit",
        home="a warm burrow under the hill",
        voice="quick",
        trait="eager",
        tags={"rabbit", "burrow"},
    ),
    "mouse": HeroKind(
        id="mouse",
        noun="mouse",
        home="a neat nest under the roots",
        voice="small",
        trait="busy",
        tags={"mouse", "nest"},
    ),
    "hedgehog": HeroKind(
        id="hedgehog",
        noun="hedgehog",
        home="a leaf house by the blackberry bush",
        voice="soft",
        trait="careful",
        tags={"hedgehog", "leaf_house"},
    ),
}

OBSTACLES = {
    "branch": Obstacle(
        id="branch",
        label="branch",
        phrase="a storm-fallen branch",
        blocks="the little path home",
        weight=2,
        tags={"branch", "storm"},
    ),
    "stone": Obstacle(
        id="stone",
        label="stone",
        phrase="a round gray stone",
        blocks="the narrow bridge path",
        weight=3,
        tags={"stone", "bridge"},
    ),
    "cart": Obstacle(
        id="cart",
        label="cart",
        phrase="an overturned berry cart",
        blocks="the lane to the hollow tree",
        weight=2,
        tags={"cart", "berries"},
    ),
}

METHODS = {
    "lever": Method(
        id="lever",
        label="lever",
        phrase="a stout stick used as a lever",
        power=2,
        sense=3,
        success_text="set {phrase} under the {obstacle} and leaned until it began to rise",
        fail_text="pressed with {phrase}, but the {obstacle} barely rocked",
        qa_text="used a stout lever to raise the obstacle",
        tags={"lever", "tool"},
    ),
    "rope": Method(
        id="rope",
        label="rope",
        phrase="a vine rope looped tight",
        power=2,
        sense=3,
        success_text="looped {phrase} around the {obstacle} and pulled at the right angle until it slid up",
        fail_text="pulled and pulled with {phrase}, but the {obstacle} would not lift enough",
        qa_text="used a rope to pull the obstacle up",
        tags={"rope", "tool"},
    ),
    "twig": Method(
        id="twig",
        label="twig",
        phrase="a little twig",
        power=1,
        sense=1,
        success_text="poked at the {obstacle} with {phrase} until, by luck, it shifted",
        fail_text="poked at the {obstacle} with {phrase}, which snapped at once",
        qa_text="tried to move the obstacle with a twig",
        tags={"twig", "tool"},
    ),
}

HELPERS = {
    "tortoise": HelperKind(
        id="tortoise",
        noun="tortoise",
        style="slow and steady",
        strength=1,
        tags={"tortoise", "steady"},
    ),
    "beaver": HelperKind(
        id="beaver",
        noun="beaver",
        style="patient and practical",
        strength=2,
        tags={"beaver", "practical"},
    ),
    "goat": HelperKind(
        id="goat",
        noun="goat",
        style="sure-footed and strong",
        strength=2,
        tags={"goat", "strong"},
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for hero_id in HEROES:
        for obstacle_id, obstacle in OBSTACLES.items():
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and method.power <= obstacle.weight:
                    combos.append((hero_id, obstacle_id, method_id))
    return sorted(combos)


def sensible_methods() -> list[str]:
    return sorted(mid for mid, m in METHODS.items() if m.sense >= SENSE_MIN)


def can_raise_alone(method: Method, obstacle: Obstacle) -> bool:
    return method.power >= obstacle.weight


def can_raise_with_help(method: Method, obstacle: Obstacle, helper: HelperKind) -> bool:
    return method.power + helper.strength >= obstacle.weight


def resolve_outcome(params: "StoryParams") -> str:
    method = METHODS[params.method]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    if params.moral_value == "humility":
        return "helped" if can_raise_with_help(method, obstacle, helper) else "stuck"
    if can_raise_alone(method, obstacle):
        return "alone"
    return "stuck"


@dataclass
class StoryParams:
    hero: str
    obstacle: str
    method: str
    helper: str
    moral_value: str
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, hero_cfg: HeroKind, obstacle_cfg: Obstacle) -> None:
    world.say(
        f"In a green wood lived a little {hero_cfg.noun} named Pip. "
        f"Pip was {hero_cfg.trait} and liked to hurry back to {hero_cfg.home} before dusk."
    )
    world.say(
        f"One windy evening, Pip found {obstacle_cfg.phrase} lying across {obstacle_cfg.blocks}."
    )


def need(world: World, hero_cfg: HeroKind, obstacle_cfg: Obstacle) -> None:
    world.say(
        f"Dark clouds were gathering, and the blocked way made the small traveler stop short. "
        f"If the path stayed shut, supper and shelter would be far away."
    )
    world.say(
        f'"I must raise this {obstacle_cfg.label}," Pip said in a {hero_cfg.voice} voice.'
    )


def boast_or_pause(world: World, moral_value: str, helper_cfg: HelperKind) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    if moral_value == "pride":
        hero.memes["pride"] += 1
        world.say(
            f"Just then, a {helper_cfg.noun} came by. "
            f'"I can do it myself," Pip said, lifting {hero.pronoun("possessive")} nose and refusing help.'
        )
        helper.memes["rebuffed"] += 1
    else:
        hero.memes["humility"] += 1
        world.say(
            f"Just then, a {helper_cfg.noun} came by, {helper_cfg.style}. "
            f'Pip bowed and said, "Friend, will you help me raise it the safe way?"'
        )
        helper.memes["asked"] += 1


def attempt_alone(world: World, method_cfg: Method, obstacle_cfg: Obstacle) -> None:
    hero = world.get("hero")
    hero.memes["strain"] += 1
    if can_raise_alone(method_cfg, obstacle_cfg):
        world.say(
            f"Pip {method_cfg.success_text.format(phrase=method_cfg.phrase, obstacle=obstacle_cfg.label)}."
        )
        world.get("obstacle").meters["raised"] += 1
        propagate(world, narrate=False)
    else:
        world.say(
            f"Pip {method_cfg.fail_text.format(phrase=method_cfg.phrase, obstacle=obstacle_cfg.label)}."
        )
        propagate(world, narrate=False)


def ask_again(world: World, helper_cfg: HelperKind) -> None:
    hero = world.get("hero")
    world.say(
        f"Pip tugged once more and felt fear nibble at {hero.pronoun('possessive')} heart. "
        f"At last came a small sigh of honesty: Pip could not do it alone."
    )
    world.say(
        f'"Please come back, good {helper_cfg.noun}," Pip called. "Pride is lighter than a branch, but it can still pin one down."'
    )


def attempt_together(world: World, method_cfg: Method, obstacle_cfg: Obstacle, helper_cfg: HelperKind) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["cooperation"] += 1
    helper.memes["cooperation"] += 1
    if can_raise_with_help(method_cfg, obstacle_cfg, helper_cfg):
        world.say(
            f"Together they {method_cfg.success_text.format(phrase=method_cfg.phrase, obstacle=obstacle_cfg.label)}, "
            f"and the path opened inch by inch."
        )
        world.get("obstacle").meters["raised"] += 1
        propagate(world, narrate=False)
    else:
        hero.memes["sadness"] += 1
        world.say(
            f"Together they tried, but even with {helper_cfg.noun} strength, the {obstacle_cfg.label} would not rise."
        )
        propagate(world, narrate=False)


def resolution_success(world: World, helper_cfg: HelperKind, moral_value: str, obstacle_cfg: Obstacle) -> None:
    hero = world.get("hero")
    relief_word = "relief"
    if moral_value == "pride":
        world.say(
            f"Warm {relief_word} washed over Pip when the way finally cleared. "
            f"The little {hero.type} thanked the {helper_cfg.noun} and kept no proud words left."
        )
    else:
        world.say(
            f"Warm {relief_word} washed over Pip as the clear path shone ahead. "
            f"The little {hero.type} thanked the {helper_cfg.noun}, glad that a humble voice had opened what stubborn paws could not."
        )
    world.say(
        f"Soon Pip was hurrying home beneath the first raindrops, looking back only once at the lifted {obstacle_cfg.label}."
    )
    world.say(
        "Moral: The one who asks for help raises more than a burden; such a heart raises wisdom too."
    )


def resolution_stuck(world: World, helper_cfg: HelperKind, moral_value: str, obstacle_cfg: Obstacle) -> None:
    hero = world.get("hero")
    if moral_value == "pride":
        world.say(
            f"The rain came before the path was clear, and Pip had to spend the night beneath a cold fern. "
            f"Only then did the little {hero.type} understand that pride had weighed more than the {obstacle_cfg.label}."
        )
        world.say(
            "Moral: He who will not ask for help may stay longer in trouble than in labor."
        )
    else:
        world.say(
            f"Though Pip and the {helper_cfg.noun} could not clear the path that night, they sheltered together and made a wiser plan for morning. "
            f"Pip still felt relief in not being alone, for courage shared is lighter to carry."
        )
        world.say(
            "Moral: Even when work is hard, humility turns fear into fellowship."
        )


def tell(
    hero_cfg: HeroKind,
    obstacle_cfg: Obstacle,
    method_cfg: Method,
    helper_cfg: HelperKind,
    moral_value: str,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg.noun, label="Pip", role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.noun, label=f"the {helper_cfg.noun}", role="helper"))
    obstacle = world.add(Entity(id="obstacle", kind="thing", type=obstacle_cfg.label, label=obstacle_cfg.label))
    world.add(Entity(id="path", kind="thing", type="path", label="path"))
    world.facts["hero_cfg"] = hero_cfg
    world.facts["obstacle_cfg"] = obstacle_cfg
    world.facts["method_cfg"] = method_cfg
    world.facts["helper_cfg"] = helper_cfg
    world.facts["moral_value"] = moral_value

    introduce(world, hero, hero_cfg, obstacle_cfg)
    need(world, hero_cfg, obstacle_cfg)

    world.para()
    boast_or_pause(world, moral_value, helper_cfg)

    outcome = resolve_outcome(
        StoryParams(
            hero=hero_cfg.id,
            obstacle=obstacle_cfg.id,
            method=method_cfg.id,
            helper=helper_cfg.id,
            moral_value=moral_value,
        )
    )

    if outcome == "alone":
        attempt_alone(world, method_cfg, obstacle_cfg)
        world.para()
        resolution_success(world, helper_cfg, moral_value, obstacle_cfg)
    elif outcome == "helped":
        world.say(
            f"The {helper_cfg.noun} nodded and took hold beside Pip."
        )
        attempt_together(world, method_cfg, obstacle_cfg, helper_cfg)
        world.para()
        if world.get("obstacle").meters["raised"] >= THRESHOLD:
            resolution_success(world, helper_cfg, moral_value, obstacle_cfg)
        else:
            resolution_stuck(world, helper_cfg, moral_value, obstacle_cfg)
    else:
        attempt_alone(world, method_cfg, obstacle_cfg)
        world.para()
        ask_again(world, helper_cfg)
        world.say(f"The {helper_cfg.noun} returned without scolding.")
        attempt_together(world, method_cfg, obstacle_cfg, helper_cfg)
        world.para()
        if world.get("obstacle").meters["raised"] >= THRESHOLD:
            resolution_success(world, helper_cfg, moral_value, obstacle_cfg)
        else:
            resolution_stuck(world, helper_cfg, moral_value, obstacle_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        obstacle=obstacle,
        opened=world.get("path").meters["open"] >= THRESHOLD,
        outcome="cleared" if world.get("path").meters["open"] >= THRESHOLD else "blocked",
        asked_for_help=moral_value == "humility" or hero.memes["cooperation"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "lever": [
        (
            "What does a lever do?",
            "A lever helps lift something heavy by using a strong bar and a good place to push. It lets small strength do bigger work."
        )
    ],
    "rope": [
        (
            "How can a rope help move something heavy?",
            "A rope lets you pull from a safer place and share the work with someone else. It is better than poking at a heavy thing with a tiny stick."
        )
    ],
    "twig": [
        (
            "Why is a twig a poor tool for heavy work?",
            "A twig is thin and weak, so it can snap instead of moving the heavy thing. Choosing the right tool matters."
        )
    ],
    "cooperation": [
        (
            "Why is cooperation useful?",
            "Cooperation means working together. When each friend adds a little strength and sense, hard jobs become possible."
        )
    ],
    "humility": [
        (
            "What is humility?",
            "Humility is knowing you do not have to pretend to do everything alone. It helps you listen, ask, and learn."
        )
    ],
    "pride": [
        (
            "Why can pride cause trouble?",
            "Pride can make someone refuse good advice or help. Then a small problem may last longer than it should."
        )
    ],
    "storm": [
        (
            "Why hurry home before a storm?",
            "A storm can bring cold rain, wind, and darkness. It is safer to reach shelter before it arrives."
        )
    ],
}
KNOWLEDGE_ORDER = ["storm", "lever", "rope", "twig", "cooperation", "humility", "pride"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero_cfg = f["hero_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    method_cfg = f["method_cfg"]
    moral_value = f["moral_value"]
    base = (
        f'Write a short fable for a young child about a {hero_cfg.noun} who must raise a '
        f'{obstacle_cfg.label} from a path before rain comes. Include the word "relief".'
    )
    if moral_value == "humility":
        return [
            base,
            f"Tell a fable where a little {hero_cfg.noun} asks for help, uses {method_cfg.phrase}, and learns that humility makes heavy work lighter.",
            "Write a moral story in a gentle animal-fable voice where cooperation clears the danger and the ending states the lesson plainly.",
        ]
    return [
        base,
        f"Tell a fable where a little {hero_cfg.noun} is too proud to ask for help at first, struggles to raise the obstacle, and learns a lesson about pride.",
        "Write a child-facing moral tale with talking animals, a blocked path, a turn toward honesty, and a clear ending image that proves what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero_cfg = f["hero_cfg"]
    helper_cfg = f["helper_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    method_cfg = f["method_cfg"]
    outcome = f["outcome"]
    moral_value = f["moral_value"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Pip, a little {hero_cfg.noun}, and a {helper_cfg.noun} who comes by on the path. The trouble begins when {obstacle_cfg.phrase} blocks Pip's way home."
        ),
        (
            "What problem did Pip face?",
            f"Pip found {obstacle_cfg.phrase} across {obstacle_cfg.blocks}, just as dark clouds were gathering. If the path stayed blocked, Pip would be far from supper and shelter."
        ),
        (
            "Why did Pip want to raise the obstacle?",
            f"Pip needed the path to open before the rain came. Raising the obstacle was the only way to get home safely by that road."
        ),
    ]
    if moral_value == "pride":
        qa.append(
            (
                "What mistake did Pip make at first?",
                f"Pip let pride speak first and refused the {helper_cfg.noun}'s help. That choice mattered because {method_cfg.phrase} was not enough for the job alone."
            )
        )
    else:
        qa.append(
            (
                "What good choice did Pip make?",
                f"Pip asked the {helper_cfg.noun} for help instead of pretending to manage alone. That humble choice brought extra strength and better sense to the work."
            )
        )
    if outcome == "cleared":
        qa.append(
            (
                "How was the problem solved?",
                f"They used {method_cfg.phrase} and worked together until the {obstacle_cfg.label} rose and the path opened. Pip felt relief because the danger of being stranded before the storm was gone."
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                "The story teaches that humility and cooperation can lift what pride cannot. Asking for help is not weakness when the job is truly heavy."
            )
        )
    else:
        qa.append(
            (
                "Did Pip clear the path that night?",
                f"No. The {obstacle_cfg.label} stayed in the way, so Pip had to stop and wait out the storm safely. Even so, the story shows that shared courage is wiser than lonely pride."
            )
        )
        qa.append(
            (
                "What lesson did Pip learn?",
                "Pip learned that refusing help can make trouble last longer. A humble heart finds safer company, even before the whole problem is fixed."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    method_cfg = f["method_cfg"]
    tags = {"storm", method_cfg.id, "cooperation", f["moral_value"]}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="rabbit",
        obstacle="branch",
        method="lever",
        helper="beaver",
        moral_value="humility",
    ),
    StoryParams(
        hero="mouse",
        obstacle="stone",
        method="rope",
        helper="goat",
        moral_value="humility",
    ),
    StoryParams(
        hero="hedgehog",
        obstacle="cart",
        method="lever",
        helper="tortoise",
        moral_value="pride",
    ),
    StoryParams(
        hero="rabbit",
        obstacle="stone",
        method="rope",
        helper="beaver",
        moral_value="pride",
    ),
]


def explain_rejection(method_id: str, obstacle_id: str) -> str:
    method = METHODS[method_id]
    obstacle = OBSTACLES[obstacle_id]
    if method.sense < SENSE_MIN:
        return (
            f"(No story: {method.phrase} is too flimsy and unwise for lifting a {obstacle.label}. "
            f"Choose a sturdier method such as lever or rope.)"
        )
    if method.power > obstacle.weight:
        return (
            f"(No story: this world only tells honest lifting tales where the chosen method is just barely fit or needs help. "
            f"{method.label} is too strong for the delicate tension in this setup.)"
        )
    return "(No story: this combination is not part of the reasonable story set.)"


ASP_RULES = r"""
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
valid(H, O, M) :- hero(H), obstacle(O), method(M), sensible(M), power(M, P), weight(O, W), P <= W.

outcome(alone)   :- chosen_method(M), chosen_obstacle(O), chosen_moral(pride), power(M, P), weight(O, W), P >= W.
outcome(stuck)   :- chosen_method(M), chosen_obstacle(O), chosen_moral(pride), power(M, P), weight(O, W), P < W.
outcome(helped)  :- chosen_method(M), chosen_obstacle(O), chosen_helper(Hp), chosen_moral(humility),
                    power(M, P), weight(O, W), helper_strength(Hp, HS), P + HS >= W.
outcome(stuck)   :- chosen_method(M), chosen_obstacle(O), chosen_helper(Hp), chosen_moral(humility),
                    power(M, P), weight(O, W), helper_strength(Hp, HS), P + HS < W.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("weight", obstacle_id, obstacle.weight))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_strength", helper_id, helper.strength))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_moral", params.moral_value),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story is empty.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = set(sensible_methods())
    asp_sense = set(asp_sensible())
    if py_sensible == asp_sense:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(asp_sense)} python={sorted(py_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatches = 0
    for params in cases:
        a = asp_outcome(params)
        b = resolve_outcome(params)
        if a != b:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small fable world about raising a blocked path and learning a moral."
    )
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--moral-value", dest="moral_value", choices=["humility", "pride"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        obstacle_id = args.obstacle or next(iter(OBSTACLES))
        raise StoryError(explain_rejection(args.method, obstacle_id))

    if args.method and args.obstacle:
        method = METHODS[args.method]
        obstacle = OBSTACLES[args.obstacle]
        if not (method.sense >= SENSE_MIN and method.power <= obstacle.weight):
            raise StoryError(explain_rejection(args.method, args.obstacle))

    combos = [
        combo for combo in valid_combos()
        if (args.hero is None or combo[0] == args.hero)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    hero_id, obstacle_id, method_id = rng.choice(combos)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    moral_value = args.moral_value or rng.choice(["humility", "pride"])
    return StoryParams(
        hero=hero_id,
        obstacle=obstacle_id,
        method=method_id,
        helper=helper_id,
        moral_value=moral_value,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        hero_cfg = HEROES[params.hero]
        obstacle_cfg = OBSTACLES[params.obstacle]
        method_cfg = METHODS[params.method]
        helper_cfg = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter choice: {err.args[0]}.)") from None

    if method_cfg.sense < SENSE_MIN:
        raise StoryError(explain_rejection(params.method, params.obstacle))
    if method_cfg.power > obstacle_cfg.weight:
        raise StoryError(explain_rejection(params.method, params.obstacle))
    if params.moral_value not in {"humility", "pride"}:
        raise StoryError("(Invalid moral value. Choose humility or pride.)")

    world = tell(hero_cfg, obstacle_cfg, method_cfg, helper_cfg, params.moral_value)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (hero, obstacle, method) combos:\n")
        for hero_id, obstacle_id, method_id in combos:
            print(f"  {hero_id:10} {obstacle_id:8} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = (
                f"### {p.hero}: {p.obstacle} with {p.method} "
                f"({p.moral_value}, helper: {p.helper}, {resolve_outcome(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
