#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ulterior_happy_ending_friendship_adventure.py
=========================================================================

A standalone story world for a small adventure tale about friendship, a secret
plan, and a happy ending.

Premise
-------
Two friends set out on a tiny adventure trail. Along the way they meet a third
child who asks to join them for an ulterior reason: the child wants the prize
at the end, not friendship. But the trail includes a real obstacle that can
only be crossed with the right tool and with help from other people. As the
children travel, kindness changes the newcomer's motives. By the end, the prize
is shared, the secret plan is confessed, and the children become friends.

This world is intentionally constraint-driven:

* A place only supports certain obstacles.
* An obstacle only makes sense with the right trail tool.
* A story is only valid if the chosen place, obstacle, and tool fit together.
* The "ulterior" motive is represented in state, then softened by invitation,
  shared work, and confession.

Run it
------
    python storyworlds/worlds/gpt-5.4/ulterior_happy_ending_friendship_adventure.py
    python storyworlds/worlds/gpt-5.4/ulterior_happy_ending_friendship_adventure.py --all
    python storyworlds/worlds/gpt-5.4/ulterior_happy_ending_friendship_adventure.py --place woods --obstacle creek
    python storyworlds/worlds/gpt-5.4/ulterior_happy_ending_friendship_adventure.py --obstacle cliff
    python storyworlds/worlds/gpt-5.4/ulterior_happy_ending_friendship_adventure.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we need the package dir.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FRIEND_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    trail_phrase: str
    opening_image: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    danger: str
    need: str
    solved_by: str
    difficulty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_line: str
    power: int
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    ending_image: str
    share_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Motive:
    id: str
    wish: str
    confession: str
    greedy: int
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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character" and e.role in {"leader", "friend", "newcomer"}]

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


def _r_trust_softens_scheme(world: World) -> list[str]:
    out: list[str] = []
    newcomer = world.get("newcomer")
    if newcomer.memes["included"] >= THRESHOLD:
        sig = ("included_softens", newcomer.id)
        if sig not in world.fired:
            world.fired.add(sig)
            newcomer.memes["greed"] = max(0.0, newcomer.memes["greed"] - 1.0)
            newcomer.memes["trust"] += 1.0
            out.append("__softened__")
    if newcomer.meters["helped"] >= THRESHOLD:
        sig = ("helped_softens", newcomer.id)
        if sig not in world.fired:
            world.fired.add(sig)
            newcomer.memes["greed"] = max(0.0, newcomer.memes["greed"] - 1.0)
            newcomer.memes["friendship"] += 1.0
            out.append("__softened__")
    return out


def _r_crossing_builds_friendship(world: World) -> list[str]:
    leader = world.get("leader")
    pal = world.get("pal")
    newcomer = world.get("newcomer")
    if world.facts.get("crossed"):
        for a, b in ((leader, newcomer), (pal, newcomer), (leader, pal)):
            sig = ("bond", a.id, b.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            a.memes["friendship"] += 1.0
            b.memes["friendship"] += 1.0
    return []


CAUSAL_RULES = [
    Rule(name="trust_softens_scheme", tag="social", apply=_r_trust_softens_scheme),
    Rule(name="crossing_builds_friendship", tag="social", apply=_r_crossing_builds_friendship),
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


def obstacle_fits(place: Place, obstacle: Obstacle) -> bool:
    return obstacle.id in place.affords


def tool_fits(obstacle: Obstacle, tool: Tool) -> bool:
    return obstacle.id in tool.solves and tool.power >= obstacle.difficulty


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for obstacle_id in sorted(place.affords):
            obstacle = OBSTACLES[obstacle_id]
            for tool_id, tool in TOOLS.items():
                if tool_fits(obstacle, tool):
                    combos.append((place_id, obstacle_id, tool_id))
    return combos


def predict_crossing(place: Place, obstacle: Obstacle, tool: Tool) -> dict:
    return {
        "possible": obstacle_fits(place, obstacle) and tool_fits(obstacle, tool),
        "difficulty": obstacle.difficulty,
        "power": tool.power,
    }


def introduce(world: World, leader: Entity, pal: Entity, place: Place, prize: Prize) -> None:
    leader.memes["joy"] += 1.0
    pal.memes["joy"] += 1.0
    world.say(
        f"On a bright morning, {leader.id} and {pal.id} hurried to {place.label} "
        f"for a tiny adventure. {place.opening_image}"
    )
    world.say(
        f"They had heard that the trail ended with {prize.phrase}, and the two friends "
        f"wanted to find it together."
    )


def meet_newcomer(world: World, newcomer: Entity, motive: Motive) -> None:
    newcomer.memes["greed"] = float(motive.greedy)
    newcomer.memes["lonely"] += 1.0
    world.say(
        f"At the trail sign they met {newcomer.id}, who watched the map with careful eyes. "
        f'{newcomer.id} asked, "Can I come too?"'
    )
    world.say(
        f"{newcomer.id} had an ulterior plan: {motive.wish}. {newcomer.pronoun().capitalize()} did not say that part out loud."
    )


def invite(world: World, leader: Entity, pal: Entity, newcomer: Entity) -> None:
    newcomer.memes["included"] += 1.0
    leader.memes["kindness"] += 1.0
    pal.memes["kindness"] += 1.0
    world.say(
        f'"Of course," said {leader.id}. "{pal.id} and I are better on adventures with one more friend."'
    )
    world.say(
        f'{pal.id} scooted over and shared the little trail map. That small kindness made {newcomer.id} blink in surprise.'
    )
    propagate(world, narrate=False)


def set_obstacle(world: World, obstacle: Obstacle) -> None:
    for kid in world.kids():
        kid.memes["alert"] += 1.0
    world.say(
        f"Soon the path bent toward {obstacle.phrase}. {obstacle.danger}"
    )
    world.say(
        f"To keep going, they needed {obstacle.need}."
    )


def use_tool(world: World, leader: Entity, pal: Entity, newcomer: Entity, tool: Tool, obstacle: Obstacle) -> None:
    leader.meters["helped"] += 1.0
    pal.meters["helped"] += 1.0
    newcomer.meters["helped"] += 1.0
    world.facts["crossed"] = True
    world.say(
        f"{leader.id} pulled out {tool.phrase}. {tool.use_line}"
    )
    world.say(
        f"{pal.id} held steady, {newcomer.id} followed close, and together they got past {obstacle.label}."
    )
    propagate(world, narrate=False)


def pause_and_change(world: World, newcomer: Entity) -> None:
    if newcomer.memes["greed"] < THRESHOLD:
        world.say(
            f"On the other side, {newcomer.id} looked back at the tricky path and then at the two smiling children. "
            f"The secret plan did not feel shiny anymore."
        )
    else:
        world.say(
            f"On the other side, {newcomer.id} still remembered the prize, but now the trail felt less lonely than before."
        )


def confess(world: World, newcomer: Entity, motive: Motive, prize: Prize) -> None:
    newcomer.memes["honesty"] += 1.0
    newcomer.memes["friendship"] += 1.0
    newcomer.memes["greed"] = 0.0
    world.say(
        f'When they reached the clearing, {newcomer.id} stopped and took a deep breath. "{motive.confession}"'
    )
    world.say(
        f'"I came for {prize.label}, not for company," {newcomer.pronoun()} admitted. "But walking with you felt better than sneaking."'
    )


def share_prize(world: World, leader: Entity, pal: Entity, newcomer: Entity, prize: Prize) -> None:
    leader.memes["friendship"] += 1.0
    pal.memes["friendship"] += 1.0
    newcomer.memes["friendship"] += 1.0
    newcomer.memes["joy"] += 1.0
    leader.memes["joy"] += 1.0
    pal.memes["joy"] += 1.0
    world.say(
        f"Instead of frowning, {pal.id} smiled. {prize.share_line}"
    )
    world.say(
        f"Soon the three children stood shoulder to shoulder with {prize.ending_image}, and the adventure felt bigger because nobody was left out."
    )


def closing_image(world: World, leader: Entity, pal: Entity, newcomer: Entity, place: Place) -> None:
    world.say(
        f"They walked back along {place.trail_phrase} talking all the way, and by the time the sun leaned low, "
        f"{leader.id}, {pal.id}, and {newcomer.id} were not just trail partners. They were friends."
    )


def tell(
    place: Place,
    obstacle: Obstacle,
    tool: Tool,
    prize: Prize,
    motive: Motive,
    leader_name: str,
    leader_gender: str,
    pal_name: str,
    pal_gender: str,
    newcomer_name: str,
    newcomer_gender: str,
) -> World:
    if not obstacle_fits(place, obstacle):
        raise StoryError(explain_rejection(place=place, obstacle=obstacle, tool=tool))
    if not tool_fits(obstacle, tool):
        raise StoryError(explain_rejection(place=place, obstacle=obstacle, tool=tool))

    world = World(place)
    leader = world.add(Entity(id="leader", kind="character", type=leader_gender, label=leader_name, role="leader"))
    pal = world.add(Entity(id="pal", kind="character", type=pal_gender, label=pal_name, role="friend"))
    newcomer = world.add(Entity(id="newcomer", kind="character", type=newcomer_gender, label=newcomer_name, role="newcomer"))
    world.facts["crossed"] = False

    introduce(world, leader, pal, place, prize)
    world.para()
    meet_newcomer(world, newcomer, motive)
    invite(world, leader, pal, newcomer)
    world.para()
    set_obstacle(world, obstacle)
    use_tool(world, leader, pal, newcomer, tool, obstacle)
    pause_and_change(world, newcomer)
    world.para()
    confess(world, newcomer, motive, prize)
    share_prize(world, leader, pal, newcomer, prize)
    closing_image(world, leader, pal, newcomer, place)

    world.facts.update(
        place=place,
        obstacle=obstacle,
        tool=tool,
        prize=prize,
        motive=motive,
        leader=leader,
        pal=pal,
        newcomer=newcomer,
        friendship_ready=newcomer.memes["friendship"] >= FRIEND_MIN,
        shared=True,
    )
    return world


KNOWLEDGE = {
    "creek": [
        (
            "What is a creek?",
            "A creek is a small stream of moving water. It can look gentle, but stones can still be slippery."
        )
    ],
    "brambles": [
        (
            "What are brambles?",
            "Brambles are thorny plants with long, scratchy stems. They can catch on sleeves and skin."
        )
    ],
    "cave": [
        (
            "Why can a dark cave feel scary?",
            "A dark cave can feel scary because you cannot see clearly inside it. Shadows and hidden rocks can make people move more carefully."
        )
    ],
    "rope": [
        (
            "What can a rope help people do on an adventure?",
            "A rope can help people climb, pull, or steady each other. It works best when people use it carefully together."
        )
    ],
    "gloves": [
        (
            "Why do gloves help with thorny plants?",
            "Gloves protect hands from little scratches and pokes. They make it safer to push branches aside."
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern gives light so people can see in dim places. Good light helps people notice safe steps."
        )
    ],
    "friendship": [
        (
            "How can kindness start a friendship?",
            "Kindness shows someone that they are welcome and safe with you. A small helpful act can change how a whole day feels."
        )
    ],
    "honesty": [
        (
            "Why is it good to tell the truth after making a bad plan?",
            "Telling the truth lets people fix the problem together. Honesty can turn a secret mistake into a better choice."
        )
    ],
}
KNOWLEDGE_ORDER = ["creek", "brambles", "cave", "rope", "gloves", "lantern", "friendship", "honesty"]


PLACES = {
    "woods": Place(
        id="woods",
        label="the whispering woods",
        trail_phrase="the pine-smelling path",
        opening_image="Tall trees drew striped shadows across the ground, and a red ribbon on a branch pointed toward the trail.",
        affords={"creek", "brambles"},
        tags={"friendship"},
    ),
    "cliffs": Place(
        id="cliffs",
        label="the windy sea cliffs",
        trail_phrase="the windy cliff path",
        opening_image="Far below, the sea flashed blue, and little gull feathers skipped over the grass.",
        affords={"creek", "cave"},
        tags={"friendship"},
    ),
    "garden": Place(
        id="garden",
        label="the old garden maze",
        trail_phrase="the twisty stone path",
        opening_image="Low hedges made green walls, and little painted arrows peeped from the leaves.",
        affords={"brambles", "cave"},
        tags={"friendship"},
    ),
}

OBSTACLES = {
    "creek": Obstacle(
        id="creek",
        label="the creek",
        phrase="a chattering creek with round wet stones",
        danger="The water was not deep, but it moved fast enough to splash shoes and wobble knees.",
        need="a safe way to steady themselves over the water",
        solved_by="rope",
        difficulty=2,
        tags={"creek"},
    ),
    "brambles": Obstacle(
        id="brambles",
        label="the bramble arch",
        phrase="a bramble arch woven with tiny thorns",
        danger="The opening looked narrow, and the thorns reached out like grabby fingers.",
        need="protected hands and patient teamwork",
        solved_by="gloves",
        difficulty=2,
        tags={"brambles"},
    ),
    "cave": Obstacle(
        id="cave",
        label="the little cave",
        phrase="a little cave under a hill of roots",
        danger="The mouth of the cave was dark, and the ground inside dipped where small feet could stumble.",
        need="a bright light to see each careful step",
        solved_by="lantern",
        difficulty=2,
        tags={"cave"},
    ),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="rope",
        phrase="a coil of soft climbing rope",
        use_line="They looped it around a sturdy stump so each child could hold on while crossing.",
        power=2,
        solves={"creek"},
        tags={"rope"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="a pair of thick gardening gloves",
        use_line="The gloves let them lift thorny branches and make a safe little doorway.",
        power=2,
        solves={"brambles"},
        tags={"gloves"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a bright camping lantern",
        use_line="Its warm light painted the stones gold and showed every place to put a foot.",
        power=2,
        solves={"cave"},
        tags={"lantern"},
    ),
    "mapstick": Tool(
        id="mapstick",
        label="map stick",
        phrase="a pointed walking stick",
        use_line="It was handy for poking leaves, but it could not truly solve the obstacle ahead.",
        power=1,
        solves=set(),
        tags=set(),
    ),
}

PRIZES = {
    "badge": Prize(
        id="badge",
        label="the silver trail badge",
        phrase="a silver trail badge hanging from a blue ribbon",
        ending_image="the silver trail badge swinging from all three hands",
        share_line='"Then we will all find it together," said Pal. "A treasure is better when everyone gets to touch it."',
        tags={"friendship"},
    ),
    "box": Prize(
        id="box",
        label="the painted treasure box",
        phrase="a painted treasure box full of bright paper stars",
        ending_image="the painted treasure box open between them",
        share_line='"Then let us open it together," said Pal. "Paper stars do not need to belong to only one person."',
        tags={"friendship"},
    ),
    "bell": Prize(
        id="bell",
        label="the brass explorer bell",
        phrase="a tiny brass explorer bell tied to a green cord",
        ending_image="the brass bell glinting while each child had a turn to ring it",
        share_line='"Then we can all ring it," said Pal. "A bell sounds happiest when everyone gets a turn."',
        tags={"friendship"},
    ),
}

MOTIVES = {
    "badge": Motive(
        id="badge",
        wish="to reach the prize first and keep the trail treasure alone",
        confession="I only joined because I wanted to get there first.",
        greedy=2,
        tags={"honesty"},
    ),
    "prove": Motive(
        id="prove",
        wish="to prove nobody was kinder or braver than to newcomer",
        confession="I wanted to win by myself so everyone would notice me.",
        greedy=2,
        tags={"honesty"},
    ),
    "lonely": Motive(
        id="lonely",
        wish="to hide how lonely the trail had felt all week",
        confession="I pretended I only cared about the prize, because I did not want anyone to see I was lonely.",
        greedy=1,
        tags={"honesty"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora", "Rose", "Lucy"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]


@dataclass
class StoryParams:
    place: str
    obstacle: str
    tool: str
    prize: str
    motive: str
    leader_name: str
    leader_gender: str
    pal_name: str
    pal_gender: str
    newcomer_name: str
    newcomer_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="woods",
        obstacle="creek",
        tool="rope",
        prize="badge",
        motive="badge",
        leader_name="Lily",
        leader_gender="girl",
        pal_name="Tom",
        pal_gender="boy",
        newcomer_name="Max",
        newcomer_gender="boy",
        seed=1,
    ),
    StoryParams(
        place="garden",
        obstacle="brambles",
        tool="gloves",
        prize="box",
        motive="prove",
        leader_name="Mia",
        leader_gender="girl",
        pal_name="Ella",
        pal_gender="girl",
        newcomer_name="Ben",
        newcomer_gender="boy",
        seed=2,
    ),
    StoryParams(
        place="cliffs",
        obstacle="cave",
        tool="lantern",
        prize="bell",
        motive="lonely",
        leader_name="Sam",
        leader_gender="boy",
        pal_name="Nora",
        pal_gender="girl",
        newcomer_name="Zoe",
        newcomer_gender="girl",
        seed=3,
    ),
]


def explain_rejection(place: Place, obstacle: Obstacle, tool: Tool) -> str:
    if not obstacle_fits(place, obstacle):
        allowed = ", ".join(sorted(place.affords))
        return (
            f"(No story: {obstacle.label} does not fit {place.label}. "
            f"That place supports: {allowed}.)"
        )
    if not tool_fits(obstacle, tool):
        return (
            f"(No story: {tool.label} is not a sensible way past {obstacle.label}. "
            f"Choose a tool that really solves the obstacle.)"
        )
    return "(No story: that combination is not reasonable.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    obstacle = f["obstacle"]
    prize = f["prize"]
    newcomer = f["newcomer"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that uses the word "ulterior" and ends in friendship.',
        f"Tell a gentle adventure where two friends explore {place.label}, meet a newcomer with an ulterior plan, and reach {prize.label} together.",
        f"Write a happy ending trail story where a child named {newcomer.label} starts out selfish, but crossing {obstacle.label} with help changes {newcomer.pronoun('object')}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    pal = f["pal"]
    newcomer = f["newcomer"]
    place = f["place"]
    obstacle = f["obstacle"]
    tool = f["tool"]
    prize = f["prize"]
    motive = f["motive"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.label} and {pal.label}, two friends on a trail adventure, and {newcomer.label}, the child they invited along. The story shows how the three children changed from strangers into friends."
        ),
        (
            f"Why did {newcomer.label} ask to join the adventure?",
            f"{newcomer.label} asked to join because {newcomer.pronoun()} had an ulterior plan: {motive.wish}. At first, {newcomer.pronoun()} cared more about the prize than about being with the others."
        ),
        (
            f"What problem did the children meet on the trail?",
            f"They came to {obstacle.phrase}. It was a problem because {obstacle.need}, so they could not simply rush ahead."
        ),
        (
            f"How did they get past {obstacle.label}?",
            f"They used {tool.phrase} to solve the problem. The tool worked because it fit the obstacle, and the children used it together instead of one child trying to win alone."
        ),
        (
            f"What changed {newcomer.label}'s mind?",
            f"{leader.label} and {pal.label} welcomed {newcomer.pronoun('object')} and helped {newcomer.pronoun('object')} across the trail. That kindness made the secret plan feel less important, so {newcomer.pronoun()} chose honesty over sneaking."
        ),
        (
            "How did the story end?",
            f"The children shared {prize.label} and walked back as friends. The ending proves the adventure changed because the prize was no longer something to keep alone."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["obstacle"].tags) | set(world.facts["tool"].tags) | {"friendship", "honesty"}
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
        bits = [f"name={e.label}", f"role={e.role}"]
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:5}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
place_fits(P, O) :- affords(P, O).
tool_fits(O, T)  :- solves(T, O), power(T, Pw), difficulty(O, D), Pw >= D.
valid(P, O, T)   :- place(P), obstacle(O), tool(T), place_fits(P, O), tool_fits(O, T).

% The newcomer becomes a friend when inclusion and crossing both happen.
included(1).
helped(1).
softened_greed(G2) :- greedy_start(G), included(1), G2 = G - 1.
softened_greed2(G3) :- softened_greed(G2), helped(1), G3 = G2 - 1.
friend_ready :- softened_greed2(G3), G3 <= 0.

outcome(friends) :- valid(_, _, _), friend_ready.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for obstacle_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("difficulty", obstacle_id, obstacle.difficulty))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("power", tool_id, tool.power))
        for obstacle_id in sorted(tool.solves):
            lines.append(asp.fact("solves", tool_id, obstacle_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_friend_outcome(params: StoryParams) -> str:
    import asp

    motive = MOTIVES[params.motive]
    extra = "\n".join([
        asp.fact("greedy_start", motive.greedy),
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    tool = TOOLS[params.tool]
    motive = MOTIVES[params.motive]
    if not obstacle_fits(place, obstacle) or not tool_fits(obstacle, tool):
        return "invalid"
    greed = motive.greedy
    greed -= 1
    greed -= 1
    return "friends" if greed <= 0 else "uncertain"


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
            print("  only in python:", sorted(python_set - python_set))

    cases = list(CURATED)
    for params in cases:
        if asp_friend_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome:", params)
            break
    else:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an adventure trail, an ulterior motive, and a friendship ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--motive", choices=MOTIVES)
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


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle:
        place = PLACES[args.place]
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool] if args.tool else TOOLS["rope"]
        if not obstacle_fits(place, obstacle):
            raise StoryError(explain_rejection(place=place, obstacle=obstacle, tool=tool))
    if args.obstacle and args.tool:
        obstacle = OBSTACLES[args.obstacle]
        tool = TOOLS[args.tool]
        place = PLACES[args.place] if args.place else next(iter(PLACES.values()))
        if not tool_fits(obstacle, tool):
            raise StoryError(explain_rejection(place=place, obstacle=obstacle, tool=tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obstacle_id, tool_id = rng.choice(sorted(combos))
    prize_id = args.prize or rng.choice(sorted(PRIZES.keys()))
    motive_id = args.motive or rng.choice(sorted(MOTIVES.keys()))

    leader_gender = rng.choice(["girl", "boy"])
    leader_name = _pick_name(rng, leader_gender, set())
    pal_gender = rng.choice(["girl", "boy"])
    pal_name = _pick_name(rng, pal_gender, {leader_name})
    newcomer_gender = rng.choice(["girl", "boy"])
    newcomer_name = _pick_name(rng, newcomer_gender, {leader_name, pal_name})

    return StoryParams(
        place=place_id,
        obstacle=obstacle_id,
        tool=tool_id,
        prize=prize_id,
        motive=motive_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        pal_name=pal_name,
        pal_gender=pal_gender,
        newcomer_name=newcomer_name,
        newcomer_gender=newcomer_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in (
        ("place", PLACES),
        ("obstacle", OBSTACLES),
        ("tool", TOOLS),
        ("prize", PRIZES),
        ("motive", MOTIVES),
    ):
        value = getattr(params, key)
        if value not in table:
            raise StoryError(f"(Invalid {key}: {value})")

    world = tell(
        place=PLACES[params.place],
        obstacle=OBSTACLES[params.obstacle],
        tool=TOOLS[params.tool],
        prize=PRIZES[params.prize],
        motive=MOTIVES[params.motive],
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        pal_name=params.pal_name,
        pal_gender=params.pal_gender,
        newcomer_name=params.newcomer_name,
        newcomer_gender=params.newcomer_gender,
    )

    # Replace internal ids in prose-facing fact access by using labels in QA only.
    world.facts["leader"].label = params.leader_name
    world.facts["pal"].label = params.pal_name
    world.facts["newcomer"].label = params.newcomer_name

    story = world.render()
    story = story.replace("leader", params.leader_name)
    story = story.replace("pal", params.pal_name)
    story = story.replace("newcomer", params.newcomer_name)

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
        print(f"{len(combos)} compatible (place, obstacle, tool) combos:\n")
        for place, obstacle, tool in combos:
            print(f"  {place:8} {obstacle:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.leader_name}, {p.pal_name}, and {p.newcomer_name}: {p.place} / {p.obstacle} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
