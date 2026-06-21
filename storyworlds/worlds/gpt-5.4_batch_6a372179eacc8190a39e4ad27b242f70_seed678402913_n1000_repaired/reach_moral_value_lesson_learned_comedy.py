#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reach_moral_value_lesson_learned_comedy.py
=====================================================================

A standalone storyworld about a child trying to reach something set too high,
with a comic wobble, a better plan, and a clear lesson about asking for help.

The tiny domain is built around one practical question:

    "Can the child honestly reach the high thing with this object,
    and if they try the silly way, what happens next?"

The world keeps a few physical meters (wobble, danger, reached, spilled) and
emotional memes (desire, caution, embarrassment, relief, lesson). The prose is
driven by simulated state, not by filling slots in one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/reach_moral_value_lesson_learned_comedy.py
    python storyworlds/worlds/gpt-5.4/reach_moral_value_lesson_learned_comedy.py --place kitchen --goal cookie_jar --tool rolling_chair
    python storyworlds/worlds/gpt-5.4/reach_moral_value_lesson_learned_comedy.py --tool cushion_pile
    python storyworlds/worlds/gpt-5.4/reach_moral_value_lesson_learned_comedy.py --all
    python storyworlds/worlds/gpt-5.4/reach_moral_value_lesson_learned_comedy.py --qa --json
    python storyworlds/worlds/gpt-5.4/reach_moral_value_lesson_learned_comedy.py --verify
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
BASE_REACH = 1
CAUTIOUS_TRAITS = {"careful", "patient", "sensible", "steady"}


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
    reach_bonus: int = 0
    stable: bool = False
    rolling: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "teacher": "teacher",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    afford_goals: set[str] = field(default_factory=set)
    helper_type: str = "mother"
    helper_label: str = "the grown-up"
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    label: str
    phrase: str
    location: str
    height: int
    crave_text: str
    tumble_text: str
    safe_finish: str
    plural_bits: bool = False
    fragile: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    reach_bonus: int
    stable: bool
    rolling: bool = False
    silly: bool = False
    sense: int = 3
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    goal: str
    tool: str
    hero_name: str
    hero_gender: str
    buddy_name: str
    buddy_gender: str
    helper: str
    trait: str
    relation: str = "friends"
    hero_age: int = 5
    buddy_age: int = 5
    seed: Optional[int] = None


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


def can_reach(goal: Goal, tool: Tool) -> bool:
    return BASE_REACH + tool.reach_bonus >= goal.height


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def should_stop_before_climb(relation: str, hero_age: int, buddy_age: int, trait: str, tool: Tool) -> bool:
    if tool.stable:
        return False
    older = relation == "siblings" and buddy_age > hero_age
    very_cautious = trait in CAUTIOUS_TRAITS
    return older and very_cautious


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    if should_stop_before_climb(params.relation, params.hero_age, params.buddy_age, params.trait, tool):
        return "averted"
    return "clean" if tool.stable else "wobble"


def _r_wobble(world: World) -> list[str]:
    hero = world.get("hero")
    tool = world.get("tool")
    if hero.meters["on_tool"] < THRESHOLD or tool.stable:
        return []
    sig = ("wobble", hero.id, tool.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    tool.meters["wobble"] += 1
    hero.memes["fear"] += 1
    hero.memes["embarrassment"] += 1
    world.get("room").meters["danger"] += 1
    return ["__wobble__"]


def _r_spill(world: World) -> list[str]:
    tool = world.get("tool")
    goal = world.get("goal")
    if tool.meters["wobble"] < THRESHOLD or goal.meters["touched"] < THRESHOLD:
        return []
    sig = ("spill", goal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    goal.meters["spilled"] += 1
    goal.meters["reached"] += 1
    return ["__spill__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
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
        for sent in produced:
            world.say(sent)
    return produced


def predict_try(world: World, goal_id: str, tool_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    goal = sim.get(goal_id)
    tool = sim.get(tool_id)
    hero.meters["on_tool"] += 1
    if can_reach(GOALS[goal_id], TOOLS[tool_id]):
        goal.meters["touched"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "spilled": goal.meters["spilled"] >= THRESHOLD,
        "wobble": tool.meters["wobble"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, buddy: Entity, goal: Goal) -> None:
    world.say(
        f"In {world.place.label}, {hero.id} spotted {goal.phrase} {goal.location} "
        f"and made a face like a puppy spotting a biscuit."
    )
    world.say(
        f'{hero.pronoun().capitalize()} stretched as tall as {hero.pronoun("subject")} could. '
        f'"If I just reach a tiny bit more," {hero.pronoun()} said, '
        f'"I can get it."'
    )
    hero.memes["desire"] += 1
    buddy.memes["joy"] += 1


def craving(world: World, hero: Entity, goal: Goal) -> None:
    world.say(
        f"{goal.crave_text} The trouble was that the shelf seemed to have "
        f"grown taller just to be funny."
    )


def notice_tool(world: World, hero: Entity, tool: Tool) -> None:
    silly = "very" if tool.silly else "almost"
    world.say(
        f"Then {hero.id} noticed {tool.phrase}. To {hero.pronoun('object')}, it looked "
        f"{silly} like the perfect ladder."
    )


def warn(world: World, buddy: Entity, hero: Entity, goal: Goal, tool: Tool) -> None:
    pred = predict_try(world, "goal", "tool")
    buddy.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    if pred["wobble"]:
        extra = f" {tool.label.capitalize()}s are for sitting, not for surprise dancing."
    else:
        extra = " Still, a grown-up should stay close."
    world.say(
        f'{buddy.id} squinted at {tool.phrase}. "{hero.id}, that is a bad idea," '
        f'{buddy.pronoun()} said. "You may reach it, but you might wobble."{extra}'
    )


def stop_before_climb(world: World, hero: Entity, buddy: Entity, helper: Entity, goal: Goal, tool: Tool) -> None:
    hero.memes["relief"] += 1
    buddy.memes["pride"] += 1
    world.say(
        f'{hero.id} put one foot toward {tool.phrase}, then looked at {buddy.id} '
        f"and stopped. Being told the truth by an older {('brother' if buddy.type == 'boy' else 'sister')} "
        f"had a way of making the silly plan suddenly look very silly."
    )
    world.say(
        f'Together they called for {helper.label_word}. "{helper.label_word.capitalize()}, can you help us '
        f'reach it the right way?" {hero.id} asked.'
    )
    world.say(
        f"{helper.label_word.capitalize()} came over smiling, because asking for help "
        f"before a wobble is much nicer than asking during one."
    )
    goal_reached(world, hero, helper, goal, safe=True)


def climb(world: World, hero: Entity, goal_ent: Entity) -> None:
    hero.meters["on_tool"] += 1
    if can_reach(world.facts["goal_cfg"], world.facts["tool_cfg"]):
        goal_ent.meters["touched"] += 1
    propagate(world, narrate=False)


def comic_wobble(world: World, hero: Entity, buddy: Entity, goal: Goal, tool: Tool) -> None:
    goal_ent = world.get("goal")
    climb(world, hero, goal_ent)
    world.say(
        f"{hero.id} climbed onto {tool.phrase} and lifted one hand, then another, "
        f"then made the careful face people make right before being not careful at all."
    )
    if world.get("tool").meters["wobble"] >= THRESHOLD:
        motion = "rolled a tiny bit" if tool.rolling else "gave a squeaky wobble"
        world.say(
            f"The {tool.label} {motion}. {hero.id}'s eyes went round. {buddy.id}'s mouth "
            f"went round. Even the spoon in the cup seemed shocked."
        )
    if goal_ent.meters["spilled"] >= THRESHOLD:
        world.say(goal.tumble_text)
    hero.memes["embarrassment"] += 1
    buddy.memes["fear"] += 1


def goal_reached(world: World, hero: Entity, helper: Entity, goal: Goal, safe: bool) -> None:
    goal_ent = world.get("goal")
    goal_ent.meters["reached"] += 1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    helper.memes["care"] += 1
    if safe:
        world.say(
            f"{helper.label_word.capitalize()} brought over a sturdy stool, kept one hand on it, "
            f"and let {hero.id} reach {goal.phrase} at last."
        )
        world.say(goal.safe_finish)
    else:
        world.say(
            f"{helper.label_word.capitalize()} hurried over, steadied {hero.id}, and rescued both "
            f"child and treasure before the scene could become any sillier."
        )
        world.say(
            f"Then {helper.pronoun()} brought a sturdy stool, because comedy is funnier when everyone "
            f"uses the proper furniture in the second half."
        )
        world.say(goal.safe_finish)


def lesson(world: World, helper: Entity, hero: Entity, buddy: Entity, tool: Tool) -> None:
    for child in (hero, buddy):
        child.memes["lesson"] += 1
        child.memes["fear"] = 0.0
    world.say(
        f'{helper.label_word.capitalize()} knelt down and brushed the excitement out of the air. '
        f'"If something is too high to reach, you do not have to turn the room into a circus," '
        f'{helper.pronoun()} said.'
    )
    world.say(
        f'"Ask for help, use a steady stool, and keep your feet off {tool.label if tool.silly or tool.rolling else "silly ideas"}."'
    )
    world.say(
        f"{hero.id} nodded so hard that {hero.pronoun('possessive')} hair bounced. "
        f"{buddy.id} nodded too, just a little more smugly."
    )


def ending(world: World, hero: Entity, goal: Goal) -> None:
    tag = "laughing" if world.facts["outcome"] != "clean" else "grinning"
    world.say(
        f"After that, whenever something sat too high to reach, {hero.id} called for help first. "
        f"The room stayed calm, the shelf stayed ordinary, and {hero.pronoun()} enjoyed {goal.label} while {tag} at the memory."
    )


def tell(
    place: Place,
    goal: Goal,
    tool: Tool,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    buddy_name: str = "Ben",
    buddy_gender: str = "boy",
    helper_type: str = "mother",
    trait: str = "careful",
    relation: str = "friends",
    hero_age: int = 5,
    buddy_age: int = 5,
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["eager"],
        attrs={"relation": relation},
    ))
    buddy = world.add(Entity(
        id=buddy_name,
        kind="character",
        type=buddy_gender,
        role="buddy",
        traits=[trait],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label=place.helper_label,
    ))
    room = world.add(Entity(id="room", type="room", label=place.label))
    goal_ent = world.add(Entity(
        id="goal",
        type="goal",
        label=goal.label,
        phrase=goal.phrase,
        attrs={"height": goal.height, "location": goal.location},
        tags=set(goal.tags),
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        reach_bonus=tool.reach_bonus,
        stable=tool.stable,
        rolling=tool.rolling,
        attrs={"silly": tool.silly},
        tags=set(tool.tags),
    ))
    world.facts.update(
        hero=hero,
        buddy=buddy,
        helper=helper,
        room=room,
        goal=goal_ent,
        goal_cfg=goal,
        tool=tool_ent,
        tool_cfg=tool,
        place=place,
        relation=relation,
        hero_age=hero_age,
        buddy_age=buddy_age,
        trait=trait,
    )

    introduce(world, hero, buddy, goal)
    craving(world, hero, goal)

    world.para()
    notice_tool(world, hero, tool)
    warn(world, buddy, hero, goal, tool)

    world.para()
    outcome = "clean"
    if should_stop_before_climb(relation, hero_age, buddy_age, trait, tool):
        outcome = "averted"
        stop_before_climb(world, hero, buddy, helper, goal, tool)
    elif tool.stable:
        outcome = "clean"
        world.say(
            f"{hero.id} still looked at {helper.label_word} before climbing, because even brave children can have one smart thought in time."
        )
        goal_reached(world, hero, helper, goal, safe=True)
    else:
        outcome = "wobble"
        comic_wobble(world, hero, buddy, goal, tool)
        goal_reached(world, hero, helper, goal, safe=False)

    world.facts["outcome"] = outcome

    world.para()
    lesson(world, helper, hero, buddy, tool)
    ending(world, hero, goal)
    return world


PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        scene="a bright kitchen with a very bossy top shelf",
        afford_goals={"cookie_jar", "mixing_bowl"},
        helper_type="mother",
        helper_label="mom",
        tags={"kitchen"},
    ),
    "classroom": Place(
        id="classroom",
        label="the classroom",
        scene="a classroom with a tall cubby and a little bell",
        afford_goals={"sticker_box", "party_hat"},
        helper_type="teacher",
        helper_label="teacher",
        tags={"school"},
    ),
    "hall": Place(
        id="hall",
        label="the front hall",
        scene="a narrow hall with hooks much too pleased with themselves",
        afford_goals={"party_hat", "cookie_jar"},
        helper_type="father",
        helper_label="dad",
        tags={"home"},
    ),
}

GOALS = {
    "cookie_jar": Goal(
        id="cookie_jar",
        label="the cookie jar",
        phrase="the cookie jar",
        location="on the top shelf",
        height=3,
        crave_text="The lid had blue polka dots, and somehow that made the cookies inside seem even more important.",
        tumble_text="The jar tipped, the lid popped, and three cookies bounced out like surprised little moons. Nobody was hurt, but one cookie did a full somersault onto the table.",
        safe_finish="A cookie was handed down at last, and somehow it tasted even better for having waited.",
        fragile=True,
        tags={"cookie", "kitchen"},
    ),
    "mixing_bowl": Goal(
        id="mixing_bowl",
        label="the shiny bowl",
        phrase="the shiny mixing bowl",
        location="above the fridge",
        height=3,
        crave_text="It shone like treasure, and that was enough to make it irresistible.",
        tumble_text="The bowl came down with a cheerful clang and spun in a circle on the floor, humming to itself like a silver top.",
        safe_finish="When the bowl was reached the proper way, it gleamed in {hero}'s hands like a prize that preferred good manners.",
        fragile=False,
        tags={"kitchen"},
    ),
    "sticker_box": Goal(
        id="sticker_box",
        label="the sticker box",
        phrase="the sticker box",
        location="on the highest classroom shelf",
        height=2,
        crave_text="Inside were glitter stars, puffy frogs, and one gold crown sticker that looked far too grand to wait.",
        tumble_text="The box flopped open and stickers fluttered through the air like a tiny parade of confused butterflies.",
        safe_finish="The sticker box came down safely, and the gold crown sticker waited on top as if it had been patient on purpose.",
        fragile=False,
        tags={"sticker", "school"},
    ),
    "party_hat": Goal(
        id="party_hat",
        label="the striped party hat",
        phrase="the striped party hat",
        location="on a very high hook",
        height=2,
        crave_text="It leaned there with its pom-pom cocked to one side, looking far too funny to leave alone.",
        tumble_text="The hat slipped free, bounced off a coat, and landed on {hero}'s head by accident, which only made everybody laugh harder.",
        safe_finish="Soon the hat was reached safely, and it sat proudly on {hero}'s head as if it approved of sensible plans.",
        fragile=False,
        tags={"hat", "dress_up"},
    ),
}

TOOLS = {
    "stool": Tool(
        id="stool",
        label="stool",
        phrase="a sturdy stool",
        reach_bonus=2,
        stable=True,
        rolling=False,
        silly=False,
        sense=3,
        tags={"stool", "safe"},
    ),
    "rolling_chair": Tool(
        id="rolling_chair",
        label="rolling chair",
        phrase="a rolling chair",
        reach_bonus=2,
        stable=False,
        rolling=True,
        silly=True,
        sense=2,
        tags={"chair", "unsafe"},
    ),
    "toy_drum": Tool(
        id="toy_drum",
        label="toy drum",
        phrase="a toy drum",
        reach_bonus=1,
        stable=False,
        rolling=False,
        silly=True,
        sense=2,
        tags={"drum", "unsafe"},
    ),
    "cushion_pile": Tool(
        id="cushion_pile",
        label="cushion pile",
        phrase="a wobbly pile of sofa cushions",
        reach_bonus=2,
        stable=False,
        rolling=False,
        silly=True,
        sense=1,
        tags={"cushion", "unsafe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Theo", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "patient", "sensible", "steady", "cheerful", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for goal_id in sorted(place.afford_goals):
            goal = GOALS[goal_id]
            for tool_id, tool in TOOLS.items():
                if tool.sense < SENSE_MIN:
                    continue
                if can_reach(goal, tool):
                    combos.append((place_id, goal_id, tool_id))
    return combos


KNOWLEDGE = {
    "reach": [
        (
            "What does reach mean?",
            "Reach means to stretch your arm or body toward something so you can touch or get it."
        )
    ],
    "stool": [
        (
            "Why is a stool better than a rolling chair for getting something high?",
            "A stool is made for standing still, so your feet have a steadier place to stand. A rolling chair can move under you and make you wobble."
        )
    ],
    "chair": [
        (
            "Why can a rolling chair be unsafe to climb on?",
            "A rolling chair has wheels, so it can slide when you do not expect it. That sudden movement can make someone fall or drop things."
        )
    ],
    "ask_help": [
        (
            "Why should children ask a grown-up for help with high shelves?",
            "A grown-up can lift the item down safely or hold a steady stool. Asking first keeps small problems from turning into big silly ones."
        )
    ],
    "cookie": [
        (
            "Why do jars and lids sometimes tip when you pull at them from far away?",
            "If you tug a jar from the side instead of holding it firmly, its balance can shift. Then the jar or lid may tip and spill."
        )
    ],
    "sticker": [
        (
            "Why do stickers flutter when a box opens in the air?",
            "Stickers are light, so moving air can carry them as they fall. That is why they drift instead of dropping straight down."
        )
    ],
    "hat": [
        (
            "Why can a hat bounce in a funny way when it falls?",
            "A light hat is soft and springy, so it can boop off things instead of landing flat. That makes its fall look funny."
        )
    ],
}
KNOWLEDGE_ORDER = ["reach", "ask_help", "stool", "chair", "cookie", "sticker", "hat"]


def _safe_finish_text(goal: Goal, hero: Entity) -> str:
    return goal.safe_finish.replace("{hero}", hero.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    goal = f["goal_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a funny story for a 3-to-5-year-old that includes the word "reach" '
        f"and teaches a lesson about asking for help."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a light comedy where {hero.id} wants to reach {goal.phrase}, "
            f"but {buddy.id} warns {hero.pronoun('object')} in time and they ask a grown-up instead.",
            f"Write a gentle story with a moral value about listening to a wiser child before climbing on {tool.phrase}.",
        ]
    if outcome == "wobble":
        return [
            base,
            f"Tell a comedy where {hero.id} tries to reach {goal.phrase} using {tool.phrase}, "
            f"there is a silly wobble, and a grown-up helps everyone end safely.",
            f"Write a humorous lesson-learned story where a child nearly turns the room into a circus while trying to reach something high.",
        ]
    return [
        base,
        f"Tell a gentle comedy where {hero.id} wants to reach {goal.phrase}, pauses to be sensible, and uses a proper stool with help.",
        f"Write a story with a clear moral value: if something is too high to reach, ask first and climb only on steady things.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    buddy = f["buddy"]
    helper = f["helper"]
    goal = f["goal_cfg"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who wanted to reach {goal.phrase}, {buddy.id}, who spoke up, and {helper.label_word} who helped solve the problem."
        ),
        (
            f"What did {hero.id} want?",
            f"{hero.id} wanted to reach {goal.phrase} {goal.location}. It looked tempting enough to make a silly plan seem clever for a moment."
        ),
        (
            f"Why did {buddy.id} warn {hero.id}?",
            f"{buddy.id} could see that {tool.phrase} was not a steady way to reach something high. The warning mattered because wobbling would make the room unsafe and could spill the thing on the shelf."
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What happened after {buddy.id} warned {hero.id}?",
                f"{hero.id} stopped before climbing and asked {helper.label_word} for help instead. That choice prevented the wobble before it even started."
            )
        )
    elif outcome == "wobble":
        qa.append(
            (
                f"What happened when {hero.id} climbed on {tool.phrase}?",
                f"{hero.id} did reach up, but the plan turned wobbly and silly at once. Then {helper.label_word} hurried over, steadied things, and switched everyone to a proper stool."
            )
        )
        qa.append(
            (
                "Why is the story funny but still a lesson?",
                f"It is funny because the wobble and the tumbling {goal.label} make the moment feel surprising instead of scary. But the ending still teaches that asking for help is smarter than climbing on something shaky."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.id} finally reach {goal.phrase}?",
                f"{hero.label or hero.id} reached it with {helper.label_word}'s help and a sturdy stool. The proper tool turned the problem into an easy, safe success."
            )
        )
    qa.append(
        (
            "What was the lesson learned?",
            f"The lesson was to ask for help when something is too high to reach and to use steady furniture, not silly substitutes. That moral value kept everyone safe and made the ending happy."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"reach", "ask_help"} | set(world.facts["goal_cfg"].tags)
    tool = world.facts["tool_cfg"]
    if tool.id == "stool":
        tags.add("stool")
    if tool.id == "rolling_chair":
        tags.add("chair")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.reach_bonus:
            bits.append(f"reach_bonus={ent.reach_bonus}")
        if ent.stable:
            bits.append("stable=True")
        if ent.rolling:
            bits.append("rolling=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None, False)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        goal="cookie_jar",
        tool="rolling_chair",
        hero_name="Mia",
        hero_gender="girl",
        buddy_name="Ben",
        buddy_gender="boy",
        helper="mother",
        trait="careful",
        relation="friends",
        hero_age=5,
        buddy_age=5,
    ),
    StoryParams(
        place="classroom",
        goal="sticker_box",
        tool="stool",
        hero_name="Leo",
        hero_gender="boy",
        buddy_name="Zoe",
        buddy_gender="girl",
        helper="teacher",
        trait="patient",
        relation="friends",
        hero_age=5,
        buddy_age=5,
    ),
    StoryParams(
        place="hall",
        goal="party_hat",
        tool="toy_drum",
        hero_name="Ava",
        hero_gender="girl",
        buddy_name="Nora",
        buddy_gender="girl",
        helper="father",
        trait="sensible",
        relation="siblings",
        hero_age=4,
        buddy_age=7,
    ),
    StoryParams(
        place="kitchen",
        goal="mixing_bowl",
        tool="stool",
        hero_name="Finn",
        hero_gender="boy",
        buddy_name="Ruby",
        buddy_gender="girl",
        helper="mother",
        trait="steady",
        relation="friends",
        hero_age=6,
        buddy_age=6,
    ),
]


def explain_tool_rejection(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(No story: '{tool_id}' is too silly for this world's reasonableness gate "
        f"(sense={tool.sense} < {SENSE_MIN}). Try a steadier choice such as {better}.)"
    )


def explain_reach_rejection(place: Place, goal: Goal, tool: Tool) -> str:
    if goal.id not in place.afford_goals:
        return (
            f"(No story: {goal.phrase} does not belong in {place.label} here. "
            f"Pick a goal that fits this place.)"
        )
    return (
        f"(No story: {tool.phrase} is not tall enough to let a child reach {goal.phrase}. "
        f"The problem would never really happen, so the story is refused.)"
    )


ASP_RULES = r"""
% reasonableness gate
valid(P, G, T) :- place(P), goal(G), tool(T), affords(P, G), sensible(T), can_reach(G, T).

sensible(T) :- tool(T), sense(T, S), sense_min(M), S >= M.
can_reach(G, T) :- height(G, H), reach_bonus(T, R), base_reach(B), B + R >= H.

% outcome model
older_buddy :- relation(siblings), buddy_age(BA), hero_age(HA), BA > HA.
very_cautious :- trait(T), cautious_trait(T).
averted :- chosen_tool(T), unstable(T), older_buddy, very_cautious.
clean   :- chosen_tool(T), stable(T), not averted.
wobble  :- chosen_tool(T), unstable(T), not averted.

outcome(averted) :- averted.
outcome(clean) :- clean.
outcome(wobble) :- wobble.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("base_reach", BASE_REACH))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for goal_id in sorted(place.afford_goals):
            lines.append(asp.fact("affords", place_id, goal_id))
    for goal_id, goal in GOALS.items():
        lines.append(asp.fact("goal", goal_id))
        lines.append(asp.fact("height", goal_id, goal.height))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("reach_bonus", tool_id, tool.reach_bonus))
        if tool.stable:
            lines.append(asp.fact("stable", tool_id))
        else:
            lines.append(asp.fact("unstable", tool_id))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
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
        asp.fact("chosen_tool", params.tool),
        asp.fact("relation", params.relation),
        asp.fact("hero_age", params.hero_age),
        asp.fact("buddy_age", params.buddy_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for case in cases if asp_outcome(case) != outcome_of(case))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld: trying to reach something high, then learning the steady, helpful way."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=["mother", "father", "teacher"])
    ap.add_argument("--hero-name")
    ap.add_argument("--buddy-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--buddy-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, goal, tool) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(args.tool))
    if args.place and args.goal:
        place = PLACES[args.place]
        goal = GOALS[args.goal]
        tool_for_check = TOOLS[args.tool] if args.tool else next(iter(TOOLS.values()))
        if goal.id not in place.afford_goals:
            raise StoryError(explain_reach_rejection(place, goal, tool_for_check))
    if args.goal and args.tool and args.place:
        place = PLACES[args.place]
        goal = GOALS[args.goal]
        tool = TOOLS[args.tool]
        if goal.id not in place.afford_goals or not can_reach(goal, tool):
            raise StoryError(explain_reach_rejection(place, goal, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.goal is None or combo[1] == args.goal)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, goal_id, tool_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    buddy_gender = args.buddy_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    buddy_name = args.buddy_name or _pick_name(rng, buddy_gender, avoid=hero_name)
    helper = args.helper or PLACES[place_id].helper_type
    trait = rng.choice(TRAITS)
    relation = rng.choice(["friends", "siblings"])
    hero_age, buddy_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        place=place_id,
        goal=goal_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        helper=helper,
        trait=trait,
        relation=relation,
        hero_age=hero_age,
        buddy_age=buddy_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        goal = GOALS[params.goal]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool_rejection(params.tool))
    if goal.id not in place.afford_goals or not can_reach(goal, tool):
        raise StoryError(explain_reach_rejection(place, goal, tool))

    world = tell(
        place=place,
        goal=goal,
        tool=tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        buddy_name=params.buddy_name,
        buddy_gender=params.buddy_gender,
        helper_type=params.helper,
        trait=params.trait,
        relation=params.relation,
        hero_age=params.hero_age,
        buddy_age=params.buddy_age,
    )

    safe_goal = copy.deepcopy(goal)
    safe_goal.safe_finish = _safe_finish_text(goal, world.facts["hero"])
    if world.facts["goal_cfg"].safe_finish != safe_goal.safe_finish:
        story = world.render().replace(goal.safe_finish, safe_goal.safe_finish)
    else:
        story = world.render()

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, goal, tool) combos:\n")
        for place, goal, tool in combos:
            print(f"  {place:10} {goal:12} {tool}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.goal} with {p.tool} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
