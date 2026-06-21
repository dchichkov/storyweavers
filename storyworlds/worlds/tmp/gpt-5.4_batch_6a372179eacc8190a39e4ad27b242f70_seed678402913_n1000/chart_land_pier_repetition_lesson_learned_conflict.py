#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chart_land_pier_repetition_lesson_learned_conflict.py
================================================================================

A standalone story world for a gentle animal story set on a pier. Two small
animals want to reach a little piece of land across the water by following a
chart. They repeat a mistaken start, fall into a conflict, and then learn that
a chart works best when friends stop arguing and look carefully together.

Run it
------
    python storyworlds/worlds/gpt-5.4/chart_land_pier_repetition_lesson_learned_conflict.py
    python storyworlds/worlds/gpt-5.4/chart_land_pier_repetition_lesson_learned_conflict.py --boat rowboat --water calm --destination islet
    python storyworlds/worlds/gpt-5.4/chart_land_pier_repetition_lesson_learned_conflict.py --boat leaf_tub --water choppy
    python storyworlds/worlds/gpt-5.4/chart_land_pier_repetition_lesson_learned_conflict.py --all --qa
    python storyworlds/worlds/gpt-5.4/chart_land_pier_repetition_lesson_learned_conflict.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "hen"}
        male = {"boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class AnimalPair:
    id: str
    leader_species: str
    helper_species: str
    leader_trait: str
    helper_trait: str
    leader_title: str
    helper_title: str


@dataclass
class Boat:
    id: str
    label: str
    phrase: str
    stability: int
    launch: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Water:
    id: str
    label: str
    push: int
    sky: str
    repeat_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    kind: str
    difficulty: int
    clue: str
    landing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Guidance:
    id: str
    sense: int
    help_text: str
    lesson_text: str
    qa_text: str
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


def _r_bickering(world: World) -> list[str]:
    out: list[str] = []
    leader = world.get("leader")
    helper = world.get("helper")
    if leader.memes["arguing"] >= THRESHOLD or helper.memes["arguing"] >= THRESHOLD:
        sig = ("bickering",)
        if sig not in world.fired:
            world.fired.add(sig)
            leader.memes["cooperation"] -= 1
            helper.memes["cooperation"] -= 1
            out.append("__bickering__")
    return out


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    boat = world.get("boat")
    water = world.get("water")
    chart = world.get("chart")
    if boat.meters["launched"] < THRESHOLD:
        return out
    if chart.meters["read_right"] >= THRESHOLD:
        return out
    sig = ("drift", boat.meters["attempts"])
    if sig in world.fired:
        return out
    world.fired.add(sig)
    boat.meters["off_course"] += 1
    boat.meters["distance"] += float(max(1, water.attrs.get("push", 1)))
    world.get("leader").memes["frustration"] += 1
    world.get("helper").memes["frustration"] += 1
    out.append("__drift__")
    return out


def _r_arrive(world: World) -> list[str]:
    out: list[str] = []
    boat = world.get("boat")
    chart = world.get("chart")
    destination = world.get("destination")
    if boat.meters["launched"] < THRESHOLD:
        return out
    if chart.meters["read_right"] < THRESHOLD:
        return out
    if boat.meters["distance"] < destination.attrs.get("difficulty", 1):
        return out
    sig = ("arrive",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    destination.meters["reached"] += 1
    world.get("leader").memes["joy"] += 1
    world.get("helper").memes["joy"] += 1
    out.append("__arrive__")
    return out


CAUSAL_RULES = [
    Rule(name="bickering", tag="social", apply=_r_bickering),
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="arrive", tag="physical", apply=_r_arrive),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(x for x in got if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def can_travel(boat: Boat, water: Water, destination: Destination) -> bool:
    return boat.stability >= water.push and boat.stability >= destination.difficulty


def sensible_guidance() -> list[Guidance]:
    return [g for g in GUIDANCE.values() if g.sense >= SENSE_MIN]


def predict_wrong_start(world: World) -> dict:
    sim = world.copy()
    boat = sim.get("boat")
    chart = sim.get("chart")
    boat.meters["launched"] += 1
    boat.meters["attempts"] += 1
    chart.meters["read_right"] = 0.0
    propagate(sim, narrate=False)
    return {
        "off_course": boat.meters["off_course"] >= THRESHOLD,
        "distance": boat.meters["distance"],
    }


def introduce(world: World, pair: AnimalPair, boat: Boat, water: Water, destination: Destination) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    leader.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright morning at the pier, {leader.id} the {pair.leader_species} and "
        f"{helper.id} the {pair.helper_species} stood beside {boat.phrase}."
    )
    world.say(
        f"Beyond the posts and ropes, they could see {destination.phrase}, a little bit of land "
        f"waiting across the water. The water was {water.label}, and {water.sky}."
    )


def chart_setup(world: World, destination: Destination) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    world.say(
        f"{leader.id} unrolled a small chart on the pier boards. A red mark on it pointed to "
        f"{destination.phrase}, and a tiny shell was drawn near {destination.clue}."
    )
    world.say(
        f'"If we follow the chart, we will find the shell place," said {leader.id}. '
        f'"And then we can land there for our snack," said {helper.id}.'
    )


def first_warning(world: World, guidance: Guidance) -> None:
    helper = world.get("helper")
    pred = predict_wrong_start(world)
    world.facts["predicted_off_course"] = pred["off_course"]
    world.say(
        f"{helper.id} tilted the chart. \"Wait,\" {helper.pronoun()} said. "
        f"\"The wind can turn us if we rush. {guidance.help_text}\""
    )


def argue(world: World) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    leader.memes["arguing"] += 1
    helper.memes["arguing"] += 1
    leader.memes["stubbornness"] += 1
    helper.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I know where to go," said {leader.id}. "{helper.id}, you are looking too slowly." '
        f'"And you are looking too fast," {helper.id} answered.'
    )


def repeated_wrong_starts(world: World, water: Water) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    boat = world.get("boat")
    chart = world.get("chart")
    attempts = [
        "They pushed away from the pier. The boat nosed left.",
        "They came back, squinted at the chart, and pushed away again. The boat nosed left again.",
        "A third time they tried, and a third time the little boat drifted away from the line of posts.",
    ]
    for line in attempts:
        boat.meters["launched"] = 1.0
        boat.meters["attempts"] += 1
        chart.meters["read_right"] = 0.0
        propagate(world, narrate=False)
        world.say(line)
        world.say(water.repeat_line)
    world.facts["repeats"] = int(boat.meters["attempts"])
    world.say(
        f"By then, {leader.id}'s whiskers were drooping, and {helper.id} had folded the chart so tightly "
        f"that its corners trembled."
    )


def receive_help(world: World, guidance: Guidance, destination: Destination) -> None:
    elder = world.get("elder")
    world.say(
        f"Old {elder.id}, who tied boats at the end of the pier, saw their worried faces and padded closer."
    )
    world.say(
        f'"Friends," {elder.pronoun()} said, "{guidance.help_text} Look for {destination.clue}, '
        f'and keep the top of the chart facing the land."'
    )


def learn(world: World, guidance: Guidance) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    chart = world.get("chart")
    leader.memes["arguing"] = 0.0
    helper.memes["arguing"] = 0.0
    leader.memes["cooperation"] += 2
    helper.memes["cooperation"] += 2
    leader.memes["shame"] += 1
    helper.memes["relief"] += 1
    chart.meters["read_right"] = 1.0
    chart.memes["understood"] += 1
    world.say(
        f'{leader.id} looked at {helper.id}, then at the chart. "I was trying to be first," '
        f'{leader.pronoun()} said softly. "I should have tried to be careful."'
    )
    world.say(
        f'{helper.id} smoothed the chart flat. "I should have used a calm voice," {helper.pronoun()} said. '
        f'"Let us read it together."'
    )
    world.say(guidance.lesson_text)


def right_trip(world: World, destination: Destination) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    boat = world.get("boat")
    boat.meters["distance"] = float(destination.difficulty)
    boat.meters["launched"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"This time, {leader.id} held the bottom of the chart and {helper.id} held the top. "
        f"They matched the drawing to the posts, the buoy, and the strip of land ahead."
    )
    world.say(
        f"The little boat glided straight across the water, and soon {destination.landing}."
    )
    world.say(
        f"They climbed out together, set down their berry basket, and laughed at how steady the world felt "
        f"when neither of them had to win."
    )


def ending_image(world: World, destination: Destination) -> None:
    leader = world.get("leader")
    helper = world.get("helper")
    world.say(
        f"On that small piece of land, {leader.id} rolled up the chart with gentle paws, and {helper.id} tucked "
        f"it safely under the basket."
    )
    world.say(
        f"After that day, whenever they left the pier for {destination.label}, they said the same thing together: "
        f'"Slow paws, kind words, and eyes on the chart."'
    )


def tell(pair: AnimalPair, boat: Boat, water: Water, destination: Destination,
         guidance: Guidance, leader_name: str, helper_name: str, elder_name: str) -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type="animal",
        label=pair.leader_species,
        role="leader",
        traits=[pair.leader_trait],
        tags={pair.leader_species},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="animal",
        label=pair.helper_species,
        role="helper",
        traits=[pair.helper_trait],
        tags={pair.helper_species},
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type="animal",
        label="harbor seal",
        role="elder",
        traits=["patient", "wise"],
        tags={"seal"},
    ))
    world.add(Entity(
        id="boat",
        kind="thing",
        type="boat",
        label=boat.label,
        attrs={"stability": boat.stability},
        tags=set(boat.tags),
    ))
    world.add(Entity(
        id="water",
        kind="thing",
        type="water",
        label=water.label,
        attrs={"push": water.push},
        tags=set(water.tags),
    ))
    world.add(Entity(
        id="destination",
        kind="thing",
        type="land",
        label=destination.label,
        attrs={"difficulty": destination.difficulty, "clue": destination.clue},
        tags=set(destination.tags),
    ))
    world.add(Entity(
        id="chart",
        kind="thing",
        type="chart",
        label="chart",
        tags={"chart"},
    ))

    introduce(world, pair, boat, water, destination)
    chart_setup(world, destination)

    world.para()
    first_warning(world, guidance)
    argue(world)
    repeated_wrong_starts(world, water)

    world.para()
    receive_help(world, guidance, destination)
    learn(world, guidance)

    world.para()
    right_trip(world, destination)
    ending_image(world, destination)

    outcome = "learned"
    world.facts.update(
        pair=pair,
        boat_cfg=boat,
        water_cfg=water,
        destination_cfg=destination,
        guidance_cfg=guidance,
        leader=leader,
        helper=helper,
        elder=elder,
        repeats=int(world.get("boat").meters["attempts"]),
        reached=world.get("destination").meters["reached"] >= THRESHOLD,
        outcome=outcome,
    )
    return world


THEMES = {
    "otter_crab": AnimalPair(
        id="otter_crab",
        leader_species="otter",
        helper_species="crab",
        leader_trait="eager",
        helper_trait="careful",
        leader_title="Captain",
        helper_title="Reader",
    ),
    "duck_mouse": AnimalPair(
        id="duck_mouse",
        leader_species="duck",
        helper_species="mouse",
        leader_trait="bouncy",
        helper_trait="thoughtful",
        leader_title="Captain",
        helper_title="Reader",
    ),
    "fox_frog": AnimalPair(
        id="fox_frog",
        leader_species="fox",
        helper_species="frog",
        leader_trait="proud",
        helper_trait="steady",
        leader_title="Captain",
        helper_title="Reader",
    ),
}

BOATS = {
    "rowboat": Boat(
        id="rowboat",
        label="rowboat",
        phrase="a little blue rowboat",
        stability=3,
        launch="pushed the oars into the locks",
        tags={"rowboat"},
    ),
    "raft": Boat(
        id="raft",
        label="raft",
        phrase="a rope-tied raft",
        stability=2,
        launch="nudged the raft off the piling",
        tags={"raft"},
    ),
    "leaf_tub": Boat(
        id="leaf_tub",
        label="leaf tub",
        phrase="a round leaf tub",
        stability=1,
        launch="set the leaf tub on the water",
        tags={"leaf_tub"},
    ),
}

WATERS = {
    "calm": Water(
        id="calm",
        label="calm",
        push=1,
        sky="the sky wore soft white clouds",
        repeat_line="Again they had to paddle back to the pier, because the chart was turned wrong.",
        tags={"calm"},
    ),
    "breezy": Water(
        id="breezy",
        label="breezy",
        push=2,
        sky="a quick wind skipped over the water",
        repeat_line="Again the breeze tipped their noses off course, and again they had to come back to the pier.",
        tags={"wind"},
    ),
    "choppy": Water(
        id="choppy",
        label="choppy",
        push=3,
        sky="gray ripples slapped the pier posts",
        repeat_line="Again the choppy water spun them away from the line they wanted, and again they bobbed back to the pier.",
        tags={"choppy"},
    ),
}

DESTINATIONS = {
    "sandbar": Destination(
        id="sandbar",
        label="the sandbar",
        phrase="a pale sandbar",
        kind="sand",
        difficulty=1,
        clue="the striped buoy",
        landing="their boat brushed the warm edge of the sandbar",
        tags={"sandbar", "land"},
    ),
    "islet": Destination(
        id="islet",
        label="the grassy islet",
        phrase="a grassy islet",
        kind="grass",
        difficulty=2,
        clue="the crooked post with a white gull on top",
        landing="their boat slid into the reeds beside the grassy islet",
        tags={"islet", "land"},
    ),
    "pebble_bank": Destination(
        id="pebble_bank",
        label="the pebble bank",
        phrase="a low pebble bank",
        kind="stone",
        difficulty=3,
        clue="the red buoy beyond the last piling",
        landing="their boat tapped the round stones of the pebble bank",
        tags={"pebbles", "land"},
    ),
}

GUIDANCE = {
    "turn_chart": Guidance(
        id="turn_chart",
        sense=3,
        help_text="Hold the chart so the top points toward the place you want to reach.",
        lesson_text="They turned the chart toward the land and let each friend notice one clue at a time.",
        qa_text="They solved the problem by turning the chart the right way and reading it together.",
        tags={"chart", "teamwork"},
    ),
    "match_buoy": Guidance(
        id="match_buoy",
        sense=3,
        help_text="Do not guess. Match the marks on the chart to the real buoy and the real posts.",
        lesson_text="They stopped guessing and matched the drawing to the real things around them.",
        qa_text="They solved the problem by matching the chart to the buoy and the pier posts.",
        tags={"chart", "buoy", "teamwork"},
    ),
    "close_eyes": Guidance(
        id="close_eyes",
        sense=1,
        help_text="Close your eyes and feel which way the land might be.",
        lesson_text="",
        qa_text="",
        tags={"bad_idea"},
    ),
}

LEADER_NAMES = ["Ollie", "Pip", "Moss", "Tumble", "Nico", "Sunny"]
HELPER_NAMES = ["Clack", "Mimi", "Reed", "Dot", "Pebble", "Kiki"]
ELDER_NAMES = ["Harbor", "Old Salt", "Ripple", "Barnacle"]

KNOWLEDGE = {
    "chart": [
        (
            "What is a chart?",
            "A chart is a kind of map. It helps you look at places and directions so you can travel the right way."
        )
    ],
    "pier": [
        (
            "What is a pier?",
            "A pier is a long walkway built out over the water. Boats can stop beside it, and people or animals can climb on and off."
        )
    ],
    "buoy": [
        (
            "What is a buoy?",
            "A buoy is something that floats in the water to mark a place or warn travelers. It can help you know where to go."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful?",
            "Teamwork helps friends notice more and make fewer mistakes. When people share calm words and careful eyes, hard jobs get easier."
        )
    ],
    "wind": [
        (
            "Why can wind push a small boat?",
            "Wind presses against a small boat and can nudge it sideways. That is why travelers must steer and pay attention."
        )
    ],
    "land": [
        (
            "What does land mean?",
            "Land is the solid ground that is not water. An island, a sandbar, and a shore are all kinds of land."
        )
    ],
}
KNOWLEDGE_ORDER = ["chart", "pier", "buoy", "teamwork", "wind", "land"]


@dataclass
class StoryParams:
    theme: str
    boat: str
    water: str
    destination: str
    guidance: str
    leader_name: str
    helper_name: str
    elder_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        theme="otter_crab",
        boat="rowboat",
        water="calm",
        destination="sandbar",
        guidance="turn_chart",
        leader_name="Ollie",
        helper_name="Clack",
        elder_name="Harbor",
    ),
    StoryParams(
        theme="duck_mouse",
        boat="raft",
        water="breezy",
        destination="islet",
        guidance="match_buoy",
        leader_name="Sunny",
        helper_name="Mimi",
        elder_name="Ripple",
    ),
    StoryParams(
        theme="fox_frog",
        boat="rowboat",
        water="choppy",
        destination="pebble_bank",
        guidance="turn_chart",
        leader_name="Nico",
        helper_name="Reed",
        elder_name="Barnacle",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for boat_id, boat in BOATS.items():
            for water_id, water in WATERS.items():
                for dest_id, destination in DESTINATIONS.items():
                    if can_travel(boat, water, destination):
                        combos.append((theme_id, boat_id, water_id, dest_id))
    return combos


def explain_rejection(boat: Boat, water: Water, destination: Destination) -> str:
    need = max(water.push, destination.difficulty)
    return (
        f"(No story: {boat.phrase} is too tippy for {water.label} water on the way to {destination.label}. "
        f"It handles strength {boat.stability}, but this trip needs at least {need}.)"
    )


def explain_guidance(guidance_id: str) -> str:
    guidance = GUIDANCE[guidance_id]
    better = ", ".join(sorted(g.id for g in sensible_guidance()))
    return (
        f"(Refusing guidance '{guidance_id}': it scores too low on common sense "
        f"(sense={guidance.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    boat = f["boat_cfg"]
    destination = f["destination_cfg"]
    return [
        'Write a gentle animal story for a 3-to-5-year-old set on a pier that includes the words "chart" and "land".',
        f"Tell a story where {leader.id} and {helper.id} try more than once to reach {destination.label} in {boat.phrase}, but arguing over a chart keeps sending them the wrong way.",
        "Write a repetitive story with a conflict, a lesson learned, and a happy ending where friends stop bickering, read a chart together, and reach land safely.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    elder = f["elder"]
    boat = f["boat_cfg"]
    water = f["water_cfg"]
    destination = f["destination_cfg"]
    guidance = f["guidance_cfg"]
    repeats = f["repeats"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {helper.id}, two small animal friends at the pier. They wanted to use {boat.phrase} to reach {destination.label}."
        ),
        (
            "Why did they keep coming back to the pier at first?",
            f"They kept turning or reading the chart the wrong way, so the boat went off course. The {water.label} water pushed them away each time because they were arguing instead of checking the clues together."
        ),
        (
            "What was the conflict in the story?",
            f"The conflict was that {leader.id} wanted to rush and be first, while {helper.id} wanted to slow down and be careful. Their sharp words made the chart harder to use, so the trip became a problem between friends as well as a problem on the water."
        ),
        (
            "How many times did they make the wrong start?",
            f"They made the wrong start {repeats} times. The repetition shows that the same mistake kept happening until they changed how they worked together."
        ),
        (
            f"How did {elder.id} help them?",
            f"{elder.id} gave them calm guidance instead of taking over the trip. {guidance.qa_text}."
        ),
        (
            "What lesson did they learn?",
            "They learned that being kind and careful matters more than trying to win an argument. Once they shared the chart and listened to each other, the path to land became clear."
        ),
    ]
    if f["reached"]:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the friends reaching {destination.label} safely and setting down their berry basket on the little piece of land. The final image shows that the journey changed because they now spoke gently and checked the chart together."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"chart", "pier", "land", "teamwork"}
    guidance = world.facts["guidance_cfg"]
    water = world.facts["water_cfg"]
    if "buoy" in guidance.tags:
        tags.add("buoy")
    if "wind" in water.tags:
        tags.add("wind")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
trip_need(B, W, D, N) :- boat(B), water(W), destination(D), stability(B, S), push(W, P), difficulty(D, K), N = P, P >= K.
trip_need(B, W, D, N) :- boat(B), water(W), destination(D), stability(B, S), push(W, P), difficulty(D, K), N = K, K > P.
can_travel(B, W, D) :- boat(B), water(W), destination(D), stability(B, S), trip_need(B, W, D, N), S >= N.
valid(T, B, W, D) :- theme(T), can_travel(B, W, D).

sensible(G) :- guidance(G), sense(G, S), sense_min(M), S >= M.
wrong_start_repeats(3).

reached :- chosen_boat(B), chosen_water(W), chosen_destination(D), can_travel(B, W, D), chosen_guidance(G), sensible(G).
lesson_learned :- reached.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for boat_id, boat in BOATS.items():
        lines.append(asp.fact("boat", boat_id))
        lines.append(asp.fact("stability", boat_id, boat.stability))
    for water_id, water in WATERS.items():
        lines.append(asp.fact("water", water_id))
        lines.append(asp.fact("push", water_id, water.push))
    for dest_id, destination in DESTINATIONS.items():
        lines.append(asp.fact("destination", dest_id))
        lines.append(asp.fact("difficulty", dest_id, destination.difficulty))
    for guidance_id, guidance in GUIDANCE.items():
        lines.append(asp.fact("guidance", guidance_id))
        lines.append(asp.fact("sense", guidance_id, guidance.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(g for (g,) in asp.atoms(model, "sensible"))


def asp_reached(params: StoryParams) -> bool:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_boat", params.boat),
            asp.fact("chosen_water", params.water),
            asp.fact("chosen_destination", params.destination),
            asp.fact("chosen_guidance", params.guidance),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show reached/0."))
    return bool(asp.atoms(model, "reached"))


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

    clingo_guidance = set(asp_sensible())
    python_guidance = {g.id for g in sensible_guidance()}
    if clingo_guidance == python_guidance:
        print(f"OK: sensible guidance matches ({sorted(clingo_guidance)}).")
    else:
        rc = 1
        print("MISMATCH in sensible guidance.")
        print("  clingo:", sorted(clingo_guidance))
        print("  python:", sorted(python_guidance))

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        py = can_travel(BOATS[params.boat], WATERS[params.water], DESTINATIONS[params.destination]) and (
            GUIDANCE[params.guidance].sense >= SENSE_MIN
        )
        asp_ok = asp_reached(params)
        if py != asp_ok:
            rc = 1
            print(f"MISMATCH reached parity for {params}. python={py} asp={asp_ok}")
    if rc == 0:
        print("OK: curated parity checks passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: friends on a pier use a chart to reach land, repeating a mistake until they learn to cooperate."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--boat", choices=BOATS)
    ap.add_argument("--water", choices=WATERS)
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--guidance", choices=GUIDANCE)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.guidance and GUIDANCE[args.guidance].sense < SENSE_MIN:
        raise StoryError(explain_guidance(args.guidance))
    if args.boat and args.water and args.destination:
        boat = BOATS[args.boat]
        water = WATERS[args.water]
        destination = DESTINATIONS[args.destination]
        if not can_travel(boat, water, destination):
            raise StoryError(explain_rejection(boat, water, destination))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.boat is None or combo[1] == args.boat)
        and (args.water is None or combo[2] == args.water)
        and (args.destination is None or combo[3] == args.destination)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, boat_id, water_id, destination_id = rng.choice(sorted(combos))
    guidance_id = args.guidance or rng.choice(sorted(g.id for g in sensible_guidance()))
    leader_name = rng.choice(LEADER_NAMES)
    helper_name = rng.choice([n for n in HELPER_NAMES if n != leader_name])
    elder_name = rng.choice(ELDER_NAMES)
    return StoryParams(
        theme=theme_id,
        boat=boat_id,
        water=water_id,
        destination=destination_id,
        guidance=guidance_id,
        leader_name=leader_name,
        helper_name=helper_name,
        elder_name=elder_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.boat not in BOATS:
        raise StoryError(f"(Unknown boat: {params.boat})")
    if params.water not in WATERS:
        raise StoryError(f"(Unknown water: {params.water})")
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.guidance not in GUIDANCE:
        raise StoryError(f"(Unknown guidance: {params.guidance})")
    boat = BOATS[params.boat]
    water = WATERS[params.water]
    destination = DESTINATIONS[params.destination]
    guidance = GUIDANCE[params.guidance]
    if guidance.sense < SENSE_MIN:
        raise StoryError(explain_guidance(params.guidance))
    if not can_travel(boat, water, destination):
        raise StoryError(explain_rejection(boat, water, destination))

    world = tell(
        pair=THEMES[params.theme],
        boat=boat,
        water=water,
        destination=destination,
        guidance=guidance,
        leader_name=params.leader_name,
        helper_name=params.helper_name,
        elder_name=params.elder_name,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show reached/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible guidance: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, boat, water, destination) combos:\n")
        for theme_id, boat_id, water_id, destination_id in combos:
            print(f"  {theme_id:11} {boat_id:8} {water_id:7} {destination_id}")
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.helper_name}: {p.boat} on {p.water} water to {p.destination}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
