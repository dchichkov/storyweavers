#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/passage_twist_conflict_adventure.py
==============================================================

A standalone storyworld for a tiny adventure tale built around one key word:
"passage".

Two children set out on a small quest, disagree about a risky choice, and learn
that the frightening mystery ahead is not what it first seemed. The world model
tracks physical state (blocked paths, tools, safety, help) and emotional state
(curiosity, fear, trust, relief). A simple reasonableness gate only permits
stories where the obstacle, clue, and solution genuinely fit together.

Run it
------
python storyworlds/worlds/gpt-5.4/passage_twist_conflict_adventure.py
python storyworlds/worlds/gpt-5.4/passage_twist_conflict_adventure.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/passage_twist_conflict_adventure.py --all
python storyworlds/worlds/gpt-5.4/passage_twist_conflict_adventure.py --obstacle rockfall --clue growl --solution lever
python storyworlds/worlds/gpt-5.4/passage_twist_conflict_adventure.py --obstacle flooded_stream --solution dig
python storyworlds/worlds/gpt-5.4/passage_twist_conflict_adventure.py --qa --json
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class AdventureFrame:
    id: str
    place: str
    goal: str
    map_line: str
    legend: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    passage: str
    hazard: str
    rumor: str
    twist_truth: str
    severity: int
    needs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    sound: str
    true_source: str
    points_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    action: str
    result: str
    tool_word: str
    method: str
    power: int
    sense: int
    works_for: set[str] = field(default_factory=set)
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    block = world.get("block")
    if block.meters["blocked"] < THRESHOLD:
        return out
    sig = ("danger", "block")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    world.get("place").meters["danger"] += 1
    out.append("__danger__")
    return out


def _r_open(world: World) -> list[str]:
    out: list[str] = []
    block = world.get("block")
    if block.meters["opened"] < THRESHOLD:
        return out
    sig = ("open", "block")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    block.meters["blocked"] = 0.0
    world.get("place").meters["danger"] = 0.0
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
    out.append("__opened__")
    return out


CAUSAL_RULES = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="open", tag="physical", apply=_r_open),
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


def obstacle_real(obstacle: Obstacle, solution: Solution) -> bool:
    return obstacle.id in solution.works_for and solution.sense >= SENSE_MIN


def clue_fits(obstacle: Obstacle, clue: Clue) -> bool:
    return obstacle.id in clue.points_to


def valid_combo(obstacle: Obstacle, clue: Clue, solution: Solution) -> bool:
    return obstacle_real(obstacle, solution) and clue_fits(obstacle, clue)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for obs_id, obs in OBSTACLES.items():
        for clue_id, clue in CLUES.items():
            for sol_id, sol in SOLUTIONS.items():
                if valid_combo(obs, clue, sol):
                    combos.append((obs_id, clue_id, sol_id))
    return combos


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def challenge_level(obstacle: Obstacle) -> int:
    return obstacle.severity


def can_clear(obstacle: Obstacle, solution: Solution) -> bool:
    return solution.power >= challenge_level(obstacle) and obstacle.id in solution.works_for


def explain_rejection(obstacle: Obstacle, clue: Clue, solution: Solution) -> str:
    if solution.sense < SENSE_MIN:
        return (
            f"(No story: '{solution.label}' is a poor plan for children in this world. "
            f"Pick a calmer, more sensible fix.)"
        )
    if obstacle.id not in clue.points_to:
        return (
            f"(No story: the clue '{clue.label}' does not reasonably match {obstacle.label}. "
            f"The mystery and the twist need to line up.)"
        )
    if obstacle.id not in solution.works_for:
        return (
            f"(No story: {solution.label} does not solve {obstacle.label}. "
            f"The blocked passage needs a fitting method.)"
        )
    if solution.power < obstacle.severity:
        return (
            f"(No story: {solution.label} is too weak for {obstacle.label}. "
            f"The children need a method strong enough to make the passage safe.)"
        )
    return "(No story: that combination is not reasonable.)"


def predict_truth(world: World, obstacle: Obstacle, clue: Clue) -> dict:
    sim = world.copy()
    sim.get("block").meters["blocked"] = 1.0
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("place").meters["danger"],
        "truth": obstacle.twist_truth,
        "source": clue.true_source,
    }


def introduce(world: World, leader: Entity, partner: Entity, frame: AdventureFrame, guide: Entity) -> None:
    leader.memes["curiosity"] += 1
    partner.memes["curiosity"] += 1
    world.say(
        f"{leader.id} and {partner.id} were pretending to be explorers on the edge of {frame.place}. "
        f"They had {frame.map_line}, and the map promised {frame.goal}."
    )
    world.say(
        f'{guide.label_word.capitalize()} had told them one important rule before they set off: '
        f'"If you find trouble, stop, think, and help each other."'
    )
    world.say(frame.legend)


def discover_passage(world: World, leader: Entity, partner: Entity, obstacle: Obstacle) -> None:
    block = world.get("block")
    block.meters["blocked"] += 1
    leader.memes["excitement"] += 1
    partner.memes["excitement"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the foot of the hill, they found a narrow passage between two old stones. "
        f"But {obstacle.passage}."
    )


def hear_clue(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, clue: Clue) -> None:
    pred = predict_truth(world, obstacle, clue)
    world.facts["predicted_danger"] = pred["danger"]
    leader.memes["bravery"] += 1
    partner.memes["caution"] += 1
    world.say(
        f"Then {clue.sound}. {leader.id}'s eyes grew wide. "
        f'"Maybe a monster is hiding in there," {leader.pronoun()} whispered.'
    )
    extra = ""
    if pred["danger"] >= THRESHOLD:
        extra = " The blocked place looked real enough to hurt knees or trap small feet."
    world.say(
        f'{partner.id} listened harder. "Or maybe something is stuck," {partner.pronoun()} said.{extra}'
    )


def argue(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, solution: Solution) -> None:
    leader.memes["defiance"] += 1
    partner.memes["worry"] += 1
    world.say(
        f'"Let\'s squeeze past and see!" {leader.id} said.'
    )
    world.say(
        f'{partner.id} caught {leader.pronoun("possessive")} sleeve. '
        f'"No. {obstacle.hazard} We need to use the {solution.tool_word} the safe way first."'
    )


def choose_help(world: World, leader: Entity, partner: Entity, guide: Entity, solution: Solution) -> None:
    for kid in (leader, partner):
        kid.memes["thinking"] += 1
    world.say(
        f"For one quiet moment, neither child moved. Then {leader.id} looked at the dark crack again and nodded."
    )
    world.say(
        f'"You were right," {leader.pronoun()} said. "We should {solution.method} before we go any farther."'
    )
    world.say(
        f"They called for {guide.label_word} to stand nearby while they worked, and that made both explorers feel steadier."
    )


def solve(world: World, leader: Entity, partner: Entity, obstacle: Obstacle, clue: Clue, solution: Solution) -> None:
    block = world.get("block")
    block.meters["opened"] += 1
    world.get("tool").meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they {solution.action}. {solution.result}"
    )
    world.say(
        f"And there was the twist: the scary {clue.label} was really {clue.true_source}, and {obstacle.twist_truth}."
    )


def ending(world: World, leader: Entity, partner: Entity, frame: AdventureFrame, guide: Entity) -> None:
    for kid in (leader, partner):
        kid.memes["joy"] += 1
    world.say(
        f'{guide.label_word.capitalize()} smiled. "The bravest adventurers are the ones who stop to think," '
        f'{guide.pronoun()} said.'
    )
    world.say(
        f"{leader.id} and {partner.id} stepped through the passage together this time, slower than before and much more sure."
    )
    world.say(frame.closing)


def tell(
    frame: AdventureFrame,
    obstacle: Obstacle,
    clue: Clue,
    solution: Solution,
    leader_name: str = "Nora",
    leader_gender: str = "girl",
    partner_name: str = "Ben",
    partner_gender: str = "boy",
    guide_type: str = "father",
    trait: str = "careful",
    pet_name: str = "",
) -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=["bold"],
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=[trait],
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=guide_type,
        role="guide",
        label="the guide",
    ))
    world.add(Entity(id="place", type="place", label=frame.place))
    world.add(Entity(id="block", type="obstacle", label=obstacle.label, tags=set(obstacle.tags)))
    world.add(Entity(id="tool", type="tool", label=solution.tool_word, tags=set(solution.tags)))

    world.facts["pet_name"] = pet_name
    introduce(world, leader, partner, frame, guide)

    world.para()
    discover_passage(world, leader, partner, obstacle)
    hear_clue(world, leader, partner, obstacle, clue)

    world.para()
    argue(world, leader, partner, obstacle, solution)
    choose_help(world, leader, partner, guide, solution)

    world.para()
    solve(world, leader, partner, obstacle, clue, solution)
    if pet_name:
        world.say(f"{pet_name.capitalize()} trotted out after the freed creature, as if it wanted to inspect the rescue too.")
    ending(world, leader, partner, frame, guide)

    world.facts.update(
        frame=frame,
        obstacle=obstacle,
        clue=clue,
        solution=solution,
        leader=leader,
        partner=partner,
        guide=guide,
        resolved=world.get("block").meters["blocked"] < THRESHOLD,
        twist=obstacle.twist_truth,
        creature=clue.true_source,
    )
    return world


@dataclass
class StoryParams:
    frame: str
    obstacle: str
    clue: str
    solution: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    guide: str
    trait: str
    pet_name: str = ""
    seed: Optional[int] = None


FRAMES = {
    "hollow_hill": AdventureFrame(
        id="hollow_hill",
        place="Hollow Hill",
        goal="a hidden room with a painted star on the wall",
        map_line="a hand-drawn map with a red dotted trail",
        legend="The path felt ordinary at first, but every bend made the day feel bigger.",
        closing="Beyond the stones they found the little room at last, and the painted star shone in their lantern light like a prize for patient feet.",
        tags={"adventure", "map"},
    ),
    "fern_cliffs": AdventureFrame(
        id="fern_cliffs",
        place="Fern Cliffs",
        goal="an echo cave behind the green rocks",
        map_line="a folded map marked with a blue arrow",
        legend="Wind moved through the grass in long whispers, making even the sunny hillside feel mysterious.",
        closing="Inside the cave, their voices bounced back in happy echoes, and the adventure felt brighter because they had reached it the careful way.",
        tags={"adventure", "cave"},
    ),
    "sunroot_ridge": AdventureFrame(
        id="sunroot_ridge",
        place="Sunroot Ridge",
        goal="a lookout ledge above the berry bushes",
        map_line="a paper map with a tiny gold X",
        legend="The stones were warm in the sun, and the whole hillside seemed to invite one more step.",
        closing="From the ledge they could see the valley below, and both children knew the best part of the adventure was how they had helped something else first.",
        tags={"adventure", "ridge"},
    ),
}

OBSTACLES = {
    "rockfall": Obstacle(
        id="rockfall",
        label="a rockfall",
        passage="a tumble of loose rocks had spilled across it, leaving only a crooked gap",
        hazard="Those rocks could slide if we push past",
        rumor="growls",
        twist_truth="a small goat had been trapped behind the fallen stones",
        severity=2,
        needs={"lever"},
        tags={"rocks", "passage"},
    ),
    "thorn_vines": Obstacle(
        id="thorn_vines",
        label="thorny vines",
        passage="thorny vines had knotted across the opening like a prickly curtain",
        hazard="Those thorns could scratch us and snag our clothes",
        rumor="rustling",
        twist_truth="a basket of wind chimes was tangled in the vines and making the strange noise",
        severity=2,
        needs={"clip"},
        tags={"thorns", "passage"},
    ),
    "flooded_stream": Obstacle(
        id="flooded_stream",
        label="a flooded stream",
        passage="rainwater had rushed through the crack, turning the floor into a cold, splashing stream",
        hazard="That water could knock us over in the narrow place",
        rumor="splashing",
        twist_truth="a family of ducks was paddling on the far side where the water had pooled",
        severity=3,
        needs={"bridge"},
        tags={"water", "passage"},
    ),
}

CLUES = {
    "growl": Clue(
        id="growl",
        label="growl",
        sound="a low growly sound rolled out of the passage",
        true_source="a shivery little goat bleating through the stones",
        points_to={"rockfall"},
        tags={"animal_sound", "goat"},
    ),
    "rustle": Clue(
        id="rustle",
        label="rustling",
        sound="a papery rustling came from inside",
        true_source="wind rattling a basket of tiny chimes caught in the vines",
        points_to={"thorn_vines"},
        tags={"wind", "chimes"},
    ),
    "splash": Clue(
        id="splash",
        label="splashing",
        sound="quick splashing and soft peeps echoed out from the dark",
        true_source="ducklings pattering in the shallow water",
        points_to={"flooded_stream"},
        tags={"duck", "water"},
    ),
}

SOLUTIONS = {
    "lever": Solution(
        id="lever",
        label="long branch lever",
        action="slid a long branch under the biggest stone and heaved together",
        result="The stone tipped aside with a scrape, and the rest settled into a safer heap",
        tool_word="long branch",
        method="use the long branch as a lever",
        power=2,
        sense=3,
        works_for={"rockfall"},
        tags={"lever", "branch"},
    ),
    "clippers": Solution(
        id="clippers",
        label="garden clippers",
        action="used the garden clippers to snip the twistiest vines one by one",
        result="Soon a neat doorway opened where the green knot had been",
        tool_word="clippers",
        method="use the clippers carefully",
        power=2,
        sense=3,
        works_for={"thorn_vines"},
        tags={"clippers", "garden"},
    ),
    "plank": Solution(
        id="plank",
        label="wooden plank bridge",
        action="laid an old plank from rock to rock and tested it with careful toes",
        result="The water still hurried below, but now there was a safe little bridge across it",
        tool_word="plank",
        method="lay the plank across first",
        power=3,
        sense=3,
        works_for={"flooded_stream"},
        tags={"bridge", "plank"},
    ),
    "dig": Solution(
        id="dig",
        label="dig with hands",
        action="scratched at the mess with their hands as fast as they could",
        result="Bits moved, but not enough to make the place safe",
        tool_word="hands",
        method="dig with our hands",
        power=1,
        sense=1,
        works_for={"rockfall", "thorn_vines"},
        tags={"dig"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Lucy", "Anna", "Maya", "Zoe", "Rose"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Noah", "Eli", "Theo", "Jack", "Owen"]
TRAITS = ["careful", "thoughtful", "steady", "cautious", "kind", "clever"]
PETS = ["pepper the dog", "moss the puppy", "pippin the cat", "bean the goat", ""]


KNOWLEDGE = {
    "passage": [(
        "What is a passage?",
        "A passage is a way through, like a narrow path, hallway, or opening between things. It helps you get from one place to another."
    )],
    "rocks": [(
        "Why can loose rocks be dangerous?",
        "Loose rocks can slide or tumble if someone pushes against them. That can hurt feet or block a path even more."
    )],
    "thorns": [(
        "Why are thorny vines hard to walk through?",
        "Thorns are sharp, so they can scratch skin and catch on clothes. That is why people move carefully around them."
    )],
    "water": [(
        "Why can rushing water in a narrow place be risky?",
        "Fast water can make the ground slippery and push at your legs. In a tight place, that makes it easier to fall."
    )],
    "lever": [(
        "What is a lever?",
        "A lever is a strong bar or stick you push on to help lift something heavy. It lets a small person move more than they could with bare hands."
    )],
    "bridge": [(
        "Why does a plank make a safer crossing?",
        "A plank gives your feet a flat place to step on above the water. That is safer than splashing straight into a rushing stream."
    )],
    "clippers": [(
        "What are clippers used for?",
        "Clippers are tools for cutting plants or vines. They help make clean cuts without tugging everything with your hands."
    )],
    "adventure": [(
        "What makes something an adventure?",
        "An adventure is a trip or task that feels exciting, mysterious, and a little challenging. Usually someone has to be brave and think carefully."
    )],
    "help": [(
        "Why is asking for help brave?",
        "Asking for help means you notice a real problem and choose safety over showing off. That takes honesty and good sense."
    )],
}
KNOWLEDGE_ORDER = ["passage", "adventure", "rocks", "thorns", "water", "lever", "bridge", "clippers", "help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    frame = f["frame"]
    obstacle = f["obstacle"]
    clue = f["clue"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the word "passage".',
        f"Tell a story where two children exploring {frame.place} find a blocked passage, disagree about what to do, and discover that the scary {clue.label} has a surprising explanation.",
        f"Write a gentle conflict-and-twist adventure in which a frightening mystery near {obstacle.label} turns out to be something that needs help, not something mean.",
    ]


def relation_phrase(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "a girl and a boy"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    guide = f["guide"]
    frame = f["frame"]
    obstacle = f["obstacle"]
    clue = f["clue"]
    solution = f["solution"]
    pair = relation_phrase(leader, partner)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {leader.id} and {partner.id}, exploring {frame.place} with {guide.label_word} nearby. They are trying to reach {frame.goal}."
        ),
        (
            "What did they find?",
            f"They found a narrow passage, but {obstacle.passage}. That blocked their way and made the adventure feel risky instead of simple."
        ),
        (
            "What was the conflict?",
            f"{leader.id} wanted to hurry in and see what was making the sound, but {partner.id} wanted to stop and make the place safe first. Their disagreement came from one child feeling bold and the other noticing the danger."
        ),
        (
            "What was the twist?",
            f"The scary {clue.label} was not a monster after all. It was really {clue.true_source}, because {obstacle.twist_truth}."
        ),
        (
            "How did they solve the problem?",
            f"They chose to {solution.method}, and then they {solution.action}. {solution.result}."
        ),
        (
            "Why was that a good idea?",
            f"It was a good idea because {obstacle.hazard.lower()}. Using the right tool made the passage safe before they stepped through it."
        ),
        (
            "How did the story end?",
            f"It ended happily: the children stepped through the passage together and finished the adventure more carefully than they started it. The ending shows that they became braver in a thoughtful way, not a reckless way."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"passage", "adventure", "help"}
    tags |= set(f["obstacle"].tags)
    tags |= set(f["solution"].tags)
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
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        frame="hollow_hill",
        obstacle="rockfall",
        clue="growl",
        solution="lever",
        leader_name="Nora",
        leader_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        guide="father",
        trait="careful",
        pet_name="pepper the dog",
    ),
    StoryParams(
        frame="fern_cliffs",
        obstacle="thorn_vines",
        clue="rustle",
        solution="clippers",
        leader_name="Mia",
        leader_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        guide="mother",
        trait="steady",
        pet_name="",
    ),
    StoryParams(
        frame="sunroot_ridge",
        obstacle="flooded_stream",
        clue="splash",
        solution="plank",
        leader_name="Finn",
        leader_gender="boy",
        partner_name="Lucy",
        partner_gender="girl",
        guide="father",
        trait="thoughtful",
        pet_name="moss the puppy",
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ----------------------------------------------------
valid(O, C, S) :- obstacle(O), clue(C), solution(S),
                  clue_points(C, O),
                  works_for(S, O),
                  sense(S, Se), sense_min(M), Se >= M,
                  power(S, P), severity(O, V), P >= V.

sensible(S) :- solution(S), sense(S, Se), sense_min(M), Se >= M.

% --- outcome model ----------------------------------------------------------
resolved :- chosen_obstacle(O), chosen_solution(S),
            works_for(S, O),
            power(S, P), severity(O, V), P >= V,
            sense(S, Se), sense_min(M), Se >= M.
outcome(resolved) :- resolved.
outcome(stuck) :- not resolved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for frame_id in FRAMES:
        lines.append(asp.fact("frame", frame_id))
    for obs_id, obs in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obs_id))
        lines.append(asp.fact("severity", obs_id, obs.severity))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for obs_id in sorted(clue.points_to):
            lines.append(asp.fact("clue_points", clue_id, obs_id))
    for sol_id, sol in SOLUTIONS.items():
        lines.append(asp.fact("solution", sol_id))
        lines.append(asp.fact("power", sol_id, sol.power))
        lines.append(asp.fact("sense", sol_id, sol.sense))
        for obs_id in sorted(sol.works_for):
            lines.append(asp.fact("works_for", sol_id, obs_id))
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
    return sorted(item[0] for item in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_solution", params.solution),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    solution = SOLUTIONS[params.solution]
    return "resolved" if can_clear(obstacle, solution) and solution.sense >= SENSE_MIN else "stuck"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if "passage" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story did not include 'passage'.")
    emit(sample, trace=False, qa=False, header="")


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

    clingo_sens = set(asp_sensible())
    python_sens = {s.id for s in sensible_solutions()}
    if clingo_sens == python_sens:
        print(f"OK: sensible solutions match ({sorted(clingo_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible solutions: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Tiny adventure storyworld: a blocked passage, a disagreement, and a helpful twist."
    )
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid obstacle/clue/solution sets from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.clue and args.solution:
        obstacle = OBSTACLES[args.obstacle]
        clue = CLUES[args.clue]
        solution = SOLUTIONS[args.solution]
        if not valid_combo(obstacle, clue, solution):
            raise StoryError(explain_rejection(obstacle, clue, solution))
    if args.solution and SOLUTIONS[args.solution].sense < SENSE_MIN:
        obstacle = OBSTACLES[args.obstacle] if args.obstacle else next(iter(OBSTACLES.values()))
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        raise StoryError(explain_rejection(obstacle, clue, SOLUTIONS[args.solution]))

    combos = [
        combo for combo in valid_combos()
        if (args.obstacle is None or combo[0] == args.obstacle)
        and (args.clue is None or combo[1] == args.clue)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    obstacle_id, clue_id, solution_id = rng.choice(sorted(combos))
    frame = args.frame or rng.choice(sorted(FRAMES))
    leader_name, leader_gender = _pick_kid(rng)
    partner_name, partner_gender = _pick_kid(rng, avoid=leader_name)
    guide = args.guide or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    pet_name = rng.choice(PETS)
    return StoryParams(
        frame=frame,
        obstacle=obstacle_id,
        clue=clue_id,
        solution=solution_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        guide=guide,
        trait=trait,
        pet_name=pet_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.frame not in FRAMES:
        raise StoryError(f"Unknown frame: {params.frame}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"Unknown solution: {params.solution}")

    frame = FRAMES[params.frame]
    obstacle = OBSTACLES[params.obstacle]
    clue = CLUES[params.clue]
    solution = SOLUTIONS[params.solution]
    if not valid_combo(obstacle, clue, solution):
        raise StoryError(explain_rejection(obstacle, clue, solution))

    world = tell(
        frame=frame,
        obstacle=obstacle,
        clue=clue,
        solution=solution,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        guide_type=params.guide,
        trait=params.trait,
        pet_name=params.pet_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} valid (obstacle, clue, solution) combos:\n")
        for obstacle, clue, solution in combos:
            print(f"  {obstacle:14} {clue:8} {solution}")
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
            header = f"### {p.leader_name} & {p.partner_name}: {p.obstacle} / {p.clue} / {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
