#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/power_surprise_repetition_animal_story.py
====================================================================

A standalone storyworld about small animals meeting a big obstacle and learning
that clever teamwork can make surprising power.

The core tale shape is:

- two little animals head toward a treat or home path
- a heavy thing blocks the way
- the eager hero tries again and again with a repeated push-push-push rhythm
- the obstacle does not move, so worry and tiredness rise
- a surprising tiny helper appears with a simple tool idea
- team power plus the tool finally moves the obstacle
- the ending image proves what changed: the path is open and the friends keep going

The reasonableness gate is physical: an obstacle has a weight, each animal has
strength, and a tool adds leverage. A story is only valid when the combined
strength plus tool bonus can honestly move the obstacle. Invalid explicit choices
raise StoryError with a clear explanation.

Run it
------
python storyworlds/worlds/gpt-5.4/power_surprise_repetition_animal_story.py
python storyworlds/worlds/gpt-5.4/power_surprise_repetition_animal_story.py --hero bunny --obstacle log
python storyworlds/worlds/gpt-5.4/power_surprise_repetition_animal_story.py --tool tug_vine
python storyworlds/worlds/gpt-5.4/power_surprise_repetition_animal_story.py --all
python storyworlds/worlds/gpt-5.4/power_surprise_repetition_animal_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/power_surprise_repetition_animal_story.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man", "male"}
        female = {"girl", "mother", "mom", "woman", "female"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class AnimalSpec:
    id: str
    noun: str
    phrase: str
    strength: int
    gait: str
    voice: str
    home: str
    trait: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObstacleSpec:
    id: str
    label: str
    phrase: str
    place: str
    weight: int
    path_word: str
    moved_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolSpec:
    id: str
    label: str
    phrase: str
    bonus: int
    sense: int
    use_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GoalSpec:
    id: str
    label: str
    phrase: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    hero: str
    friend: str
    helper: str
    obstacle: str
    tool: str
    goal: str
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

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_path_blocked(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    path = world.get("path")
    if obstacle.meters["blocking"] >= THRESHOLD and path.meters["blocked"] < THRESHOLD:
        sig = ("path_blocked", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["blocked"] += 1
    return []


def _r_effort_tired(world: World) -> list[str]:
    out: list[str] = []
    for animal in world.animals():
        if animal.meters["effort"] < 2:
            continue
        sig = ("tired", animal.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        animal.memes["tired"] += 1
        out.append(f"{animal.id}'s paws felt shaky from all that trying.")
    return out


def _r_failure_worry(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    hero = world.get("hero")
    friend = world.get("friend")
    if obstacle.meters["failed_tries"] >= 2:
        sig = ("worry", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            friend.memes["worry"] += 1
            return ["For a moment, the two friends wondered if the path would stay blocked all day."]
    return []


def _r_moved_opens(world: World) -> list[str]:
    obstacle = world.get("obstacle")
    path = world.get("path")
    hero = world.get("hero")
    friend = world.get("friend")
    helper = world.get("helper")
    if obstacle.meters["moved"] >= THRESHOLD:
        sig = ("open", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["blocked"] = 0.0
            path.meters["open"] += 1
            for animal in (hero, friend, helper):
                animal.memes["relief"] += 1
                animal.memes["joy"] += 1
            return ["__opened__"]
    return []


CAUSAL_RULES = [
    Rule(name="path_blocked", tag="physical", apply=_r_path_blocked),
    Rule(name="effort_tired", tag="physical", apply=_r_effort_tired),
    Rule(name="failure_worry", tag="emotional", apply=_r_failure_worry),
    Rule(name="moved_opens", tag="physical", apply=_r_moved_opens),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


ANIMALS = {
    "bunny": AnimalSpec(
        id="bunny",
        noun="bunny",
        phrase="a soft gray bunny",
        strength=2,
        gait="hopped",
        voice="peeped",
        home="a clover hill",
        trait="springy",
        tags={"bunny", "forest"},
    ),
    "beaver": AnimalSpec(
        id="beaver",
        noun="beaver",
        phrase="a busy brown beaver",
        strength=4,
        gait="padded",
        voice="said",
        home="a pond lodge",
        trait="steady",
        tags={"beaver", "forest"},
    ),
    "fox": AnimalSpec(
        id="fox",
        noun="fox",
        phrase="a bright red fox",
        strength=3,
        gait="trotted",
        voice="said",
        home="a ferny den",
        trait="quick",
        tags={"fox", "forest"},
    ),
    "mole": AnimalSpec(
        id="mole",
        noun="mole",
        phrase="a velvety little mole",
        strength=2,
        gait="scurried",
        voice="murmured",
        home="a snug tunnel",
        trait="patient",
        tags={"mole", "forest"},
    ),
    "ant": AnimalSpec(
        id="ant",
        noun="ant",
        phrase="a tiny black ant",
        strength=1,
        gait="marched",
        voice="piped",
        home="a neat anthill",
        trait="clever",
        tags={"ant", "tiny", "forest"},
    ),
    "mouse": AnimalSpec(
        id="mouse",
        noun="mouse",
        phrase="a neat little mouse",
        strength=1,
        gait="skittered",
        voice="whispered",
        home="a root burrow",
        trait="clever",
        tags={"mouse", "tiny", "forest"},
    ),
    "beetle": AnimalSpec(
        id="beetle",
        noun="beetle",
        phrase="a shiny green beetle",
        strength=1,
        gait="trundled",
        voice="buzzed",
        home="a bark nook",
        trait="clever",
        tags={"beetle", "tiny", "forest"},
    ),
}

OBSTACLES = {
    "log": ObstacleSpec(
        id="log",
        label="log",
        phrase="a mossy log",
        place="across the little path",
        weight=6,
        path_word="path",
        moved_text="rolled the log into the ferny grass",
        tags={"log", "wood"},
    ),
    "pumpkin": ObstacleSpec(
        id="pumpkin",
        label="pumpkin",
        phrase="a round runaway pumpkin",
        place="right in the middle of the bridge",
        weight=5,
        path_word="bridge",
        moved_text="nudged the pumpkin to the side of the bridge",
        tags={"pumpkin", "garden"},
    ),
    "stone": ObstacleSpec(
        id="stone",
        label="stone",
        phrase="a smooth gray stone",
        place="in front of the burrow gate",
        weight=4,
        path_word="way",
        moved_text="tipped the stone into a patch of moss",
        tags={"stone", "rock"},
    ),
}

TOOLS = {
    "lever_stick": ToolSpec(
        id="lever_stick",
        label="stick lever",
        phrase="a long stick",
        bonus=3,
        sense=3,
        use_text="slid a long stick under the heavy thing and used it like a lever",
        qa_text="used a long stick like a lever to add more power",
        tags={"lever", "tool", "power"},
    ),
    "reed_rollers": ToolSpec(
        id="reed_rollers",
        label="reed rollers",
        phrase="three smooth reeds",
        bonus=2,
        sense=2,
        use_text="tucked smooth reeds under the heavy thing so it could roll instead of drag",
        qa_text="put smooth reeds under it so rolling took less power",
        tags={"rollers", "tool", "power"},
    ),
    "tug_vine": ToolSpec(
        id="tug_vine",
        label="vine loop",
        phrase="a strong vine",
        bonus=1,
        sense=2,
        use_text="looped a strong vine around the heavy thing so everyone could pull together",
        qa_text="made a vine loop so all three animals could pull at once",
        tags={"vine", "tool", "power"},
    ),
    "feather_fan": ToolSpec(
        id="feather_fan",
        label="feather fan",
        phrase="a large feather",
        bonus=0,
        sense=1,
        use_text="waved a big feather at the obstacle",
        qa_text="waved a feather at it",
        tags={"feather"},
    ),
}

GOALS = {
    "berries": GoalSpec(
        id="berries",
        label="berries",
        phrase="the blackberry patch",
        ending="trotted on to the blackberry patch with smiling faces and clean baskets",
        tags={"berries", "food"},
    ),
    "home": GoalSpec(
        id="home",
        label="home",
        phrase="home before supper",
        ending="hurried home before supper while the sky turned peach and gold",
        tags={"home"},
    ),
    "picnic": GoalSpec(
        id="picnic",
        label="picnic",
        phrase="the picnic stump",
        ending="hurried to the picnic stump where flower cups of seed cake were waiting",
        tags={"picnic", "food"},
    ),
}

NAMES = {
    "bunny": ["Pip", "Mimi", "Thimble"],
    "beaver": ["Brick", "Willow", "Paddle"],
    "fox": ["Fern", "Rory", "Spark"],
    "mole": ["Dot", "Nib", "Pebble"],
    "ant": ["Bit", "Tic", "Tiny"],
    "mouse": ["Nell", "Pipkin", "Crumb"],
    "beetle": ["Shine", "Moss", "Button"],
}


def sensible_tools() -> list[str]:
    return [tid for tid, tool in TOOLS.items() if tool.sense >= SENSE_MIN]


def total_power(hero: AnimalSpec, friend: AnimalSpec, helper: AnimalSpec, tool: ToolSpec) -> int:
    return hero.strength + friend.strength + helper.strength + tool.bonus


def can_move(hero: AnimalSpec, friend: AnimalSpec, helper: AnimalSpec,
             obstacle: ObstacleSpec, tool: ToolSpec) -> bool:
    return total_power(hero, friend, helper, tool) >= obstacle.weight


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for hero_id in sorted(k for k in ANIMALS if k not in {"ant", "mouse", "beetle"}):
        for friend_id in sorted(k for k in ANIMALS if k not in {"ant", "mouse", "beetle"} and k != hero_id):
            for helper_id in sorted(k for k in ANIMALS if k in {"ant", "mouse", "beetle"} and k not in {hero_id, friend_id}):
                for obstacle_id, obstacle in OBSTACLES.items():
                    for tool_id in sensible_tools():
                        tool = TOOLS[tool_id]
                        if can_move(ANIMALS[hero_id], ANIMALS[friend_id], ANIMALS[helper_id], obstacle, tool):
                            for goal_id in GOALS:
                                combos.append((hero_id, friend_id, helper_id, obstacle_id, tool_id, goal_id))
    return combos


def explain_rejection(hero_id: str, friend_id: str, helper_id: str,
                      obstacle_id: str, tool_id: str) -> str:
    hero = ANIMALS[hero_id]
    friend = ANIMALS[friend_id]
    helper = ANIMALS[helper_id]
    obstacle = OBSTACLES[obstacle_id]
    tool = TOOLS[tool_id]
    if tool.sense < SENSE_MIN:
        better = ", ".join(sorted(sensible_tools()))
        return (
            f"(No story: {tool.label} is too silly for this problem "
            f"(sense={tool.sense} < {SENSE_MIN}). Try a tool like {better}.)"
        )
    power_now = total_power(hero, friend, helper, tool)
    return (
        f"(No story: {hero.noun}, {friend.noun}, and {helper.noun} with {tool.label} "
        f"only make power {power_now}, but the {obstacle.label} needs {obstacle.weight}. "
        f"Pick a stronger pair, a lighter obstacle, or a better tool.)"
    )


def obstacle_prediction(hero: AnimalSpec, friend: AnimalSpec, obstacle: ObstacleSpec) -> dict:
    force = hero.strength + friend.strength
    return {
        "alone_power": force,
        "will_fail": force < obstacle.weight,
        "short_by": max(0, obstacle.weight - force),
    }


def setup_story(world: World, hero: Entity, friend: Entity, obstacle: Entity,
                goal: GoalSpec, obstacle_cfg: ObstacleSpec) -> None:
    world.say(
        f"One bright morning, {hero.id} the {hero.type} and {friend.id} the {friend.type} "
        f"set out for {goal.phrase}. They {hero.attrs['gait']} side by side, feeling small and merry under the leaves."
    )
    world.say(
        f"But soon they stopped. {obstacle_cfg.phrase.capitalize()} lay {obstacle_cfg.place}, blocking the {obstacle_cfg.path_word}."
    )


def want_and_predict(world: World, hero: Entity, friend: Entity, obstacle_cfg: ObstacleSpec) -> None:
    pred = obstacle_prediction(ANIMALS[hero.type], ANIMALS[friend.type], obstacle_cfg)
    world.facts["predicted_alone_power"] = pred["alone_power"]
    world.facts["predicted_short_by"] = pred["short_by"]
    hero.memes["confidence"] += 1
    world.say(f'"We can move it," said {hero.id}. "{hero.id} power! {friend.id} power! Push, push, push!"')
    if pred["will_fail"]:
        friend.memes["worry"] += 1
        world.say(
            f"{friend.id} planted {friend.pronoun('possessive')} paws too, but the heavy {obstacle_cfg.label} looked much bigger up close."
        )


def push_once(world: World, hero: Entity, friend: Entity, obstacle: Entity, obstacle_cfg: ObstacleSpec,
              first: bool = False) -> None:
    hero.meters["effort"] += 1
    friend.meters["effort"] += 1
    obstacle.meters["failed_tries"] += 1
    if first:
        world.say(
            f"They leaned in together. Push, push, push! The {obstacle_cfg.label} gave only the tiniest wobble."
        )
    else:
        world.say(
            f"They tried again. Push, push, push! Still the {obstacle_cfg.label} would not budge."
        )
    propagate(world, narrate=True)


def surprise_arrival(world: World, helper: Entity) -> None:
    helper.memes["idea"] += 1
    world.say(
        f"Then came a surprise. Out from the grass popped {helper.id} the {helper.type}, so tiny that {hero_and_friend(world)} almost missed {helper.pronoun('object')}."
    )
    world.say(
        f'"You are using all your paws," {helper.id} {helper.attrs["voice"]}, "but not all your power."'
    )


def hero_and_friend(world: World) -> str:
    return f'{world.get("hero").id} and {world.get("friend").id}'


def offer_tool(world: World, helper: Entity, tool: ToolSpec) -> None:
    world.say(
        f"{helper.id} found {tool.phrase} and {tool.use_text}."
    )
    world.say(
        f'"Now try together," {helper.id} {helper.attrs["voice"]}.'
    )


def move_obstacle(world: World, hero: Entity, friend: Entity, helper: Entity,
                  obstacle: Entity, obstacle_cfg: ObstacleSpec) -> None:
    hero.meters["effort"] += 1
    friend.meters["effort"] += 1
    helper.meters["effort"] += 1
    obstacle.meters["moved"] += 1
    obstacle.meters["blocking"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} pushed. {friend.id} pushed. {helper.id} pulled. Push, push, push!"
    )
    world.say(
        f"This time the ground answered back. The three friends {obstacle_cfg.moved_text}, and the {obstacle_cfg.path_word} opened at last."
    )


def resolution(world: World, hero: Entity, friend: Entity, helper: Entity,
               goal: GoalSpec) -> None:
    hero.memes["gratitude"] += 1
    friend.memes["gratitude"] += 1
    world.say(
        f'{hero.id} blinked in surprise. "You are so small," {hero.pronoun()} said, "but you brought big power."'
    )
    world.say(
        f'"Little ideas can make strong power," said {helper.id}.'
    )
    world.say(
        f"Then {hero.id}, {friend.id}, and {helper.id} {goal.ending}."
    )


def tell(hero_cfg: AnimalSpec, friend_cfg: AnimalSpec, helper_cfg: AnimalSpec,
         obstacle_cfg: ObstacleSpec, tool_cfg: ToolSpec, goal_cfg: GoalSpec) -> World:
    world = World()

    hero_name = NAMES[hero_cfg.id][0]
    friend_name = NAMES[friend_cfg.id][0]
    helper_name = NAMES[helper_cfg.id][0]

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_cfg.id,
        label=hero_cfg.noun,
        phrase=hero_cfg.phrase,
        role="hero",
        attrs={"strength": hero_cfg.strength, "gait": hero_cfg.gait, "voice": hero_cfg.voice},
        tags=set(hero_cfg.tags),
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_cfg.id,
        label=friend_cfg.noun,
        phrase=friend_cfg.phrase,
        role="friend",
        attrs={"strength": friend_cfg.strength, "gait": friend_cfg.gait, "voice": friend_cfg.voice},
        tags=set(friend_cfg.tags),
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg.id,
        label=helper_cfg.noun,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={"strength": helper_cfg.strength, "gait": helper_cfg.gait, "voice": helper_cfg.voice},
        tags=set(helper_cfg.tags),
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        kind="thing",
        type=obstacle_cfg.id,
        label=obstacle_cfg.label,
        phrase=obstacle_cfg.phrase,
        tags=set(obstacle_cfg.tags),
    ))
    path = world.add(Entity(
        id="path",
        kind="thing",
        type="path",
        label=obstacle_cfg.path_word,
        phrase=f"the {obstacle_cfg.path_word}",
    ))
    obstacle.meters["blocking"] += 1
    propagate(world, narrate=False)

    setup_story(world, hero, friend, obstacle, goal_cfg, obstacle_cfg)
    world.para()
    want_and_predict(world, hero, friend, obstacle_cfg)
    push_once(world, hero, friend, obstacle, obstacle_cfg, first=True)
    push_once(world, hero, friend, obstacle, obstacle_cfg, first=False)
    world.para()
    surprise_arrival(world, helper)
    offer_tool(world, helper, tool_cfg)
    move_obstacle(world, hero, friend, helper, obstacle, obstacle_cfg)
    world.para()
    resolution(world, hero, friend, helper, goal_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        obstacle=obstacle,
        path=path,
        hero_cfg=hero_cfg,
        friend_cfg=friend_cfg,
        helper_cfg=helper_cfg,
        obstacle_cfg=obstacle_cfg,
        tool_cfg=tool_cfg,
        goal_cfg=goal_cfg,
        repeated_tries=int(obstacle.meters["failed_tries"]) + 1,
        total_power=total_power(hero_cfg, friend_cfg, helper_cfg, tool_cfg),
        obstacle_weight=obstacle_cfg.weight,
        solved=obstacle.meters["moved"] >= THRESHOLD,
        surprise_helper=helper_cfg.id,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    obstacle = f["obstacle_cfg"]
    goal = f["goal_cfg"]
    tool = f["tool_cfg"]
    return [
        'Write a short animal story for a 3-to-5-year-old that includes the word "power" and uses surprise and repetition.',
        f"Tell a gentle forest story where {hero.id} and {friend.id} cannot move a {obstacle.label}, keep saying 'Push, push, push!', and then a surprising little {helper.type} helps them.",
        f"Write a child-facing story that ends with teamwork and a clever tool giving the friends enough power to reach {goal.phrase}. Include {tool.label}.",
    ]


KNOWLEDGE = {
    "power": [(
        "What does power mean in this kind of story?",
        "Power means the force that helps something move or happen. Sometimes it comes from strong bodies, and sometimes it comes from a smart idea that makes work easier."
    )],
    "lever": [(
        "What does a lever do?",
        "A lever helps you lift or move something heavy by using a long stiff tool and a good pushing point. It gives you more power than your paws or hands alone."
    )],
    "rollers": [(
        "Why do rollers help move heavy things?",
        "Rollers help because rolling is easier than dragging. They let a heavy thing glide along with less rubbing and less power."
    )],
    "vine": [(
        "Why does pulling together help?",
        "Pulling together adds everyone's strength at the same time. Teamwork can make more power than one animal working alone."
    )],
    "log": [(
        "Why is a log hard to move?",
        "A log is hard to move because it is long, heavy, and rubs against the ground. That means a little push may not be enough."
    )],
    "stone": [(
        "Why is a stone heavy?",
        "A stone is made of rock, and rock is dense and hard. Even a smooth stone can take a lot of power to shift."
    )],
    "pumpkin": [(
        "Why can a pumpkin roll?",
        "A round pumpkin can roll because its curved shape lets it turn instead of scraping. That can make moving it easier."
    )],
    "ant": [(
        "Can a tiny ant still be useful?",
        "Yes. A tiny ant can notice a clever way to solve a problem. Being small does not stop an animal from having a smart idea."
    )],
    "mouse": [(
        "Can a mouse help with a big problem?",
        "Yes. A mouse may not be the strongest animal, but it can help by spotting a good tool or joining a team pull."
    )],
    "beetle": [(
        "Why might a beetle surprise someone?",
        "A beetle can surprise someone because it looks tiny and quiet, but it may know exactly how to help. Surprises happen when something works better than expected."
    )],
}


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    helper = f["helper"]
    obstacle_cfg = f["obstacle_cfg"]
    tool = f["tool_cfg"]
    goal = f["goal_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, {friend.id} the {friend.type}, and {helper.id} the {helper.type}. They all meet at the blocked {obstacle_cfg.path_word} and solve the problem together."
        ),
        (
            f"What problem did {hero.id} and {friend.id} find?",
            f"They found {obstacle_cfg.phrase} blocking the {obstacle_cfg.path_word}, so they could not get to {goal.phrase}. The heavy obstacle stopped their easy walk and turned the trip into a problem."
        ),
        (
            f"Why did they keep saying 'Push, push, push'?",
            f"They were trying again and again to move the heavy {obstacle_cfg.label}. The repeated words match their repeated effort and show how hard they worked."
        ),
        (
            f"Why could they not move the {obstacle_cfg.label} at first?",
            f"They had only their own bodies at first, and that was not enough power for such a heavy obstacle. After two failed tries, they were tired and worried because the path was still blocked."
        ),
        (
            f"What was the surprise in the story?",
            f"The surprise was that tiny {helper.id} came out of the grass with a smart idea. The smallest helper changed the whole problem by showing them a better way to use power."
        ),
        (
            f"How did the friends finally move the {obstacle_cfg.label}?",
            f"They used {tool.phrase} and {tool.qa_text}. That gave their teamwork enough power to move the obstacle and open the {obstacle_cfg.path_word}."
        ),
        (
            "How did the story end?",
            f"It ended happily with the obstacle moved aside and the friends reaching {goal.phrase}. The open path proves that the clever plan changed the world."
        ),
    ]
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"power", f["helper_cfg"].id, f["obstacle_cfg"].id}
    tool = f["tool_cfg"]
    if tool.id == "lever_stick":
        tags.add("lever")
    elif tool.id == "reed_rollers":
        tags.add("rollers")
    elif tool.id == "tug_vine":
        tags.add("vine")
    order = ["power", "lever", "rollers", "vine", "log", "stone", "pumpkin", "ant", "mouse", "beetle"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.

main_animal(A) :- animal(A), not tiny(A).
valid(H, F, Hp, O, T, G) :-
    main_animal(H), main_animal(F), H != F,
    animal(Hp), tiny(Hp), Hp != H, Hp != F,
    obstacle(O), goal(G),
    sensible_tool(T),
    strength(H, HS), strength(F, FS), strength(Hp, PS),
    tool_bonus(T, TB), weight(O, W),
    HS + FS + PS + TB >= W.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid, animal in ANIMALS.items():
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("strength", aid, animal.strength))
        if "tiny" in animal.tags:
            lines.append(asp.fact("tiny", aid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("weight", oid, obstacle.weight))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_bonus", tid, tool.bonus))
        lines.append(asp.fact("sense", tid, tool.sense))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


CURATED = [
    StoryParams(
        hero="bunny",
        friend="fox",
        helper="ant",
        obstacle="log",
        tool="lever_stick",
        goal="berries",
    ),
    StoryParams(
        hero="mole",
        friend="beaver",
        helper="mouse",
        obstacle="stone",
        tool="reed_rollers",
        goal="home",
    ),
    StoryParams(
        hero="fox",
        friend="bunny",
        helper="beetle",
        obstacle="pumpkin",
        tool="tug_vine",
        goal="picnic",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: repeated tries, a surprising tiny helper, and enough power to move a heavy obstacle."
    )
    ap.add_argument("--hero", choices=sorted(k for k in ANIMALS if k not in {"ant", "mouse", "beetle"}))
    ap.add_argument("--friend", choices=sorted(k for k in ANIMALS if k not in {"ant", "mouse", "beetle"}))
    ap.add_argument("--helper", choices=sorted(k for k in ANIMALS if k in {"ant", "mouse", "beetle"}))
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--goal", choices=sorted(GOALS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_choices = sorted(k for k in ANIMALS if k not in {"ant", "mouse", "beetle"})
    friend_choices = sorted(k for k in ANIMALS if k not in {"ant", "mouse", "beetle"})
    helper_choices = sorted(k for k in ANIMALS if k in {"ant", "mouse", "beetle"})

    if args.hero and args.friend and args.hero == args.friend:
        raise StoryError("(No story: the hero and friend must be two different animals.)")
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(
            f"(No story: {TOOLS[args.tool].label} is too silly for this world. Pick one of {', '.join(sorted(sensible_tools()))}.)"
        )

    partial_hero = args.hero
    partial_friend = args.friend
    partial_helper = args.helper
    partial_obstacle = args.obstacle
    partial_tool = args.tool
    partial_goal = args.goal

    combos = [
        combo for combo in valid_combos()
        if (partial_hero is None or combo[0] == partial_hero)
        and (partial_friend is None or combo[1] == partial_friend)
        and (partial_helper is None or combo[2] == partial_helper)
        and (partial_obstacle is None or combo[3] == partial_obstacle)
        and (partial_tool is None or combo[4] == partial_tool)
        and (partial_goal is None or combo[5] == partial_goal)
    ]
    if not combos:
        hero_id = partial_hero or hero_choices[0]
        friend_id = partial_friend or next(f for f in friend_choices if f != hero_id)
        helper_id = partial_helper or helper_choices[0]
        obstacle_id = partial_obstacle or sorted(OBSTACLES)[0]
        tool_id = partial_tool or sorted(TOOLS)[0]
        raise StoryError(explain_rejection(hero_id, friend_id, helper_id, obstacle_id, tool_id))

    hero_id, friend_id, helper_id, obstacle_id, tool_id, goal_id = rng.choice(sorted(combos))
    return StoryParams(
        hero=hero_id,
        friend=friend_id,
        helper=helper_id,
        obstacle=obstacle_id,
        tool=tool_id,
        goal=goal_id,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        hero_cfg = ANIMALS[params.hero]
        friend_cfg = ANIMALS[params.friend]
        helper_cfg = ANIMALS[params.helper]
        obstacle_cfg = OBSTACLES[params.obstacle]
        tool_cfg = TOOLS[params.tool]
        goal_cfg = GOALS[params.goal]
    except KeyError as exc:
        raise StoryError(f"(No story: unknown choice {exc.args[0]!r}.)") from exc

    if params.hero == params.friend:
        raise StoryError("(No story: the hero and friend must be different animals.)")
    if params.helper not in {"ant", "mouse", "beetle"}:
        raise StoryError("(No story: the helper must be one of the tiny surprise helpers.)")
    if tool_cfg.sense < SENSE_MIN:
        raise StoryError(
            f"(No story: {tool_cfg.label} is too silly for this world. Pick one of {', '.join(sorted(sensible_tools()))}.)"
        )
    if not can_move(hero_cfg, friend_cfg, helper_cfg, obstacle_cfg, tool_cfg):
        raise StoryError(explain_rejection(params.hero, params.friend, params.helper, params.obstacle, params.tool))

    world = tell(hero_cfg, friend_cfg, helper_cfg, obstacle_cfg, tool_cfg, goal_cfg)
    return StorySample(
        params=params,
        story=world.render(),
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = set(sensible_tools())
    asp_sensible = set(asp_sensible_tools())
    if py_sensible == asp_sensible:
        print(f"OK: sensible tools match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible tools:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sensible))

    smoke_cases = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        args = parser.parse_args([])
        try:
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError:
            rc = 1
            print(f"SMOKE ERROR: resolve_params failed unexpectedly for seed {seed}")
            continue

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated an empty story.")
        except Exception as exc:
            rc = 1
            print(f"SMOKE ERROR: generation crashed for params={params}: {exc}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show sensible_tool/1.\n#show valid/6."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (hero, friend, helper, obstacle, tool, goal) combos:\n")
        for hero, friend, helper, obstacle, tool, goal in combos:
            print(f"  {hero:6} {friend:6} {helper:6} {obstacle:8} {tool:13} {goal}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} + {p.friend} with {p.helper} vs {p.obstacle} using {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
