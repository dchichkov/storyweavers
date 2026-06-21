#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py
==================================================================

A standalone storyworld for a tiny pirate-tale domain where children pretend to
be pirates, run into a problem, and are tempted to use violence to solve it.
The world model refuses weak pairings and prefers calm, concrete problem
solving.

Run it
------
python storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py
python storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py --obstacle high_hook --solution stool_reach
python storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py --violent-idea kick_chest
python storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py --all
python storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py --trace
python storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py --json
python storyworlds/worlds/gpt-5.4/violence_problem_solving_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
CAUTIOUS_TRAITS = {"careful", "gentle", "thoughtful", "patient"}


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
class Obstacle:
    id: str
    label: str
    phrase: str
    scene: str
    problem_line: str
    risk: str
    needs: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ViolentIdea:
    id: str
    label: str
    phrase: str
    kind: str
    works_on: set[str] = field(default_factory=set)
    effect_line: str = ""
    lesson_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Solution:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    sense: int = 3
    setup_line: str = ""
    solve_line: str = ""
    qa_line: str = ""
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_violence_spreads_fear(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["violence"] < THRESHOLD:
            continue
        sig = ("fear_from_violence", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.kids():
            other.memes["fear"] += 1
        if "treasure" in world.entities:
            world.get("treasure").meters["trouble"] += 1
        out.append("__fear__")
    return out


def _r_apology_repairs(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["apology"] < THRESHOLD:
            continue
        sig = ("repair_trust", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.kids():
            other.memes["trust"] += 1
        out.append("__trust__")
    return out


CAUSAL_RULES = [
    Rule(name="violence_spreads_fear", tag="social", apply=_r_violence_spreads_fear),
    Rule(name="apology_repairs", tag="social", apply=_r_apology_repairs),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit.startswith("__"):
                continue
            world.say(bit)
    return produced


def violent_idea_fits(violent_idea: ViolentIdea, obstacle: Obstacle) -> bool:
    return obstacle.id in violent_idea.works_on


def solution_fits(solution: Solution, obstacle: Obstacle) -> bool:
    return obstacle.id in solution.solves and solution.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for obstacle_id, obstacle in OBSTACLES.items():
        for violent_id, violent_idea in VIOLENT_IDEAS.items():
            if not violent_idea_fits(violent_idea, obstacle):
                continue
            for solution_id, solution in SOLUTIONS.items():
                if solution_fits(solution, obstacle):
                    combos.append((obstacle_id, violent_id, solution_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > BRAVERY_INIT


def outcome_of(params: "StoryParams") -> str:
    return "averted" if would_avert(
        params.relation, params.instigator_age, params.cautioner_age, params.trait
    ) else "repaired"


def play_setup(world: World, a: Entity, b: Entity, obstacle: Obstacle) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a breezy afternoon, {a.id} and {b.id} turned the living room into a pirate ship. "
        f"A blanket was the sea, two chairs were the mast, and a striped box held their treasure."
    )
    world.say(
        f'"Captain {a.id} and Mate {b.id}!" {a.id} cried. "Today we find the moon-gold!"'
    )
    world.say(obstacle.scene)


def discover_problem(world: World, a: Entity, b: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"But there was a problem. {obstacle.problem_line}"
    )
    world.say(
        f'{b.id} stared at it. "Now what do we do?" {b.pronoun()} asked.'
    )


def tempt_violence(world: World, a: Entity, violent_idea: ViolentIdea) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} gripped a toy cutlass. "I know," {a.pronoun()} said. '
        f'"We can {violent_idea.phrase}."'
    )
    world.say(
        "For one hot second, the pirate game stopped feeling silly and started feeling sharp."
    )


def predict_hurt(world: World, violent_idea: ViolentIdea) -> dict:
    sim = world.copy()
    actor = sim.get("instigator")
    actor.memes["violence"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sum(k.memes["fear"] for k in sim.kids()),
        "trouble": sim.get("treasure").meters["trouble"],
        "kind": violent_idea.kind,
    }


def warn(world: World, b: Entity, a: Entity, violent_idea: ViolentIdea, obstacle: Obstacle, helper: Entity) -> None:
    pred = predict_hurt(world, violent_idea)
    b.memes["caution"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    extra = ""
    if pred["fear"] >= 2:
        extra = " and make everybody feel scared"
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. {violent_idea.lesson_line}. '
        f'It could {obstacle.risk}{extra}. We need a pirate plan, not violence."'
    )
    world.say(
        f'{helper.label_word.capitalize()} was folding laundry nearby and looked up at the word "violence" as if it had left a bad smell in the room.'
    )


def back_down(world: World, a: Entity, b: Entity, violent_idea: ViolentIdea) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the toy cutlass, then at {b.id}, and lowered it. '
        f'"You\'re right," {a.pronoun()} said. "That would not be brave. That would just be mean."'
    )


def try_violence(world: World, a: Entity, b: Entity, violent_idea: ViolentIdea) -> None:
    a.memes["violence"] += 1
    propagate(world, narrate=False)
    world.say(
        violent_idea.effect_line.format(a=a.id, b=b.id)
    )
    if any(k.memes["fear"] >= THRESHOLD for k in world.kids()):
        world.say(
            f"The game went quiet at once. {b.id}'s eyes grew wide, and even {a.id} looked sorry."
        )


def helper_stops(world: World, helper: Entity, a: Entity, violent_idea: ViolentIdea) -> None:
    a.memes["shame"] += 1
    world.say(
        f'{helper.label_word.capitalize()} came over fast, put a calm hand on the toy cutlass, and said, '
        f'"Pirates in stories may shout, but in this house we do not solve problems with violence."'
    )


def apologize(world: World, a: Entity, b: Entity) -> None:
    a.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I\'m sorry," {a.id} said to {b.id}. "I wanted the treasure so much that I forgot to be gentle."'
    )


def solve_problem(world: World, helper: Entity, a: Entity, b: Entity, obstacle: Obstacle, solution: Solution) -> None:
    for kid in (a, b):
        kid.memes["hope"] += 1
    world.say(
        solution.setup_line
    )
    world.say(
        solution.solve_line.format(a=a.id, b=b.id, helper=helper.label_word, obstacle=obstacle.label)
    )
    world.get("treasure").meters["opened"] += 1
    world.say(
        "Inside the box they found shiny buttons, a crayon map, and a round yellow stone that looked like a coin from the moon."
    )


def ending(world: World, helper: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{helper.label_word.capitalize()} smiled. "Strong hands are for helping, not hurting," {helper.pronoun()} said.'
    )
    world.say(
        f'{a.id} handed the moon-gold to {b.id} first. Then the two pirates tucked the treasure between them and sailed their blanket ship on, noisy again, but kind.'
    )


def tell(
    obstacle: Obstacle,
    violent_idea: ViolentIdea,
    solution: Solution,
    *,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 4,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        phrase=instigator,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        phrase=cautioner,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"name": cautioner, "relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label="the parent",
        phrase="the parent",
        role="helper",
    ))
    world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label="treasure chest",
        phrase="the striped treasure chest",
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = 5.0

    play_setup(world, a, b, obstacle)
    discover_problem(world, a, b, obstacle)

    world.para()
    tempt_violence(world, a, violent_idea)
    warn(world, b, a, violent_idea, obstacle, helper)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, violent_idea)
    else:
        world.say(
            f'"Maybe just one quick pirate move," {a.label} muttered.'
        )
        try_violence(world, a, b, violent_idea)
        helper_stops(world, helper, a, violent_idea)
        apologize(world, a, b)

    world.para()
    solve_problem(world, helper, a, b, obstacle, solution)
    ending(world, helper, a, b)

    world.facts.update(
        obstacle=obstacle,
        violent_idea=violent_idea,
        solution=solution,
        instigator=a,
        cautioner=b,
        helper=helper,
        relation=relation,
        outcome="averted" if averted else "repaired",
        violence_happened=not averted,
        solved=True,
    )
    return world


OBSTACLES = {
    "high_hook": Obstacle(
        id="high_hook",
        label="high hook",
        phrase="the brass key on the high hook",
        scene="Above the sofa, a brass key for the chest hung from a high wall hook, far above their pirate hats.",
        problem_line="The key was too high for little pirate hands.",
        risk="knock the key farther away",
        needs="reach",
        tags={"high", "reach", "key"},
    ),
    "jammed_lid": Obstacle(
        id="jammed_lid",
        label="jammed lid",
        phrase="the jammed treasure chest lid",
        scene="The striped treasure chest sat between them, but its lid would not budge a tiny bit.",
        problem_line="The lid was jammed tight and squeaked each time they pulled.",
        risk="crack the box or pinch somebody's fingers",
        needs="grip",
        tags={"jammed", "lid", "chest"},
    ),
    "snagged_flag": Obstacle(
        id="snagged_flag",
        label="snagged flag",
        phrase="the pirate flag tangled in yarn rigging",
        scene="Their pirate flag was caught in the yarn rigging over the chair-mast, and the treasure clue was tied to the end of it.",
        problem_line="The clue could not come down because the flag was badly tangled.",
        risk="tear the clue and make the tangle worse",
        needs="untangle",
        tags={"tangle", "flag", "clue"},
    ),
}

VIOLENT_IDEAS = {
    "shove_past": ViolentIdea(
        id="shove_past",
        label="shove past",
        phrase="shove past you and grab it first",
        kind="push",
        works_on={"high_hook"},
        effect_line="{a} lunged forward and bumped {b} with a shoulder, reaching up wildly for the key. The key only swung farther away.",
        lesson_line="Shoving is not a clever pirate trick",
        tags={"violence", "pushing"},
    ),
    "kick_chest": ViolentIdea(
        id="kick_chest",
        label="kick chest",
        phrase="kick the chest until it pops open",
        kind="kick",
        works_on={"jammed_lid"},
        effect_line="{a} thumped the chest with a socked foot. The box skidded, and {b} jumped back from it.",
        lesson_line="Kicking things when you are frustrated is still violence",
        tags={"violence", "kicking"},
    ),
    "slash_flag": ViolentIdea(
        id="slash_flag",
        label="slash flag",
        phrase="hack the yarn with the toy cutlass",
        kind="swing",
        works_on={"snagged_flag"},
        effect_line="{a} swung the toy cutlass at the yarn. The clue fluttered, but the knot pulled tighter and the paper almost tore.",
        lesson_line="Swinging at a problem can hurt things instead of helping",
        tags={"violence", "swinging"},
    ),
}

SOLUTIONS = {
    "stool_reach": Solution(
        id="stool_reach",
        label="stool reach",
        phrase="a sturdy step stool and careful hands",
        solves={"high_hook"},
        sense=3,
        setup_line='Instead, the parent rolled over a sturdy step stool and held it steady against the wall.',
        solve_line='{a} climbed one step, {b} pointed, and {helper} kept the stool from wobbling. In one careful reach, they lifted down the key from the {obstacle}.',
        qa_line="used a steady stool so one child could reach the key safely",
        tags={"stool", "teamwork", "reach"},
    ),
    "cloth_twist": Solution(
        id="cloth_twist",
        label="cloth twist",
        phrase="a dishcloth for grip and two patient hands",
        solves={"jammed_lid"},
        sense=3,
        setup_line='The parent fetched a dishcloth and wrapped it around the shiny latch so it would not slip.',
        solve_line='{helper.capitalize()} showed them how to hold the box still while {a} and {b} turned the latch together. With one slow twist, the {obstacle} gave a happy click.',
        qa_line="wrapped the latch in a cloth and twisted it slowly together",
        tags={"cloth", "grip", "teamwork"},
    ),
    "untangle_together": Solution(
        id="untangle_together",
        label="untangle together",
        phrase="slow fingers and patient untangling",
        solves={"snagged_flag"},
        sense=3,
        setup_line='The parent knelt beside the chair-mast and spread the yarn out so every knot could be seen.',
        solve_line='{b} held one loop, {a} lifted another, and {helper} showed them which strand to pull next. Little by little, the {obstacle} came free without tearing.',
        qa_line="spread the knot out and untangled one loop at a time",
        tags={"untangle", "patience", "teamwork"},
    ),
    "water_bucket": Solution(
        id="water_bucket",
        label="water bucket",
        phrase="a bucket of water for no good reason",
        solves=set(),
        sense=1,
        setup_line='Someone suggested a bucket of water.',
        solve_line='But water was no help at all for this pirate problem.',
        qa_line="tried an unhelpful idea",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "gentle", "thoughtful", "patient", "curious", "bold"]


@dataclass
class StoryParams:
    obstacle: str
    violent_idea: str
    solution: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    helper: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        obstacle="high_hook",
        violent_idea="shove_past",
        solution="stool_reach",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        helper="mother",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        obstacle="jammed_lid",
        violent_idea="kick_chest",
        solution="cloth_twist",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        helper="father",
        trait="gentle",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        obstacle="snagged_flag",
        violent_idea="slash_flag",
        solution="untangle_together",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        helper="mother",
        trait="patient",
        relation="siblings",
        instigator_age=7,
        cautioner_age=5,
    ),
    StoryParams(
        obstacle="jammed_lid",
        violent_idea="kick_chest",
        solution="cloth_twist",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Nora",
        cautioner_gender="girl",
        helper="father",
        trait="thoughtful",
        relation="siblings",
        instigator_age=4,
        cautioner_age=6,
    ),
]


KNOWLEDGE = {
    "violence": [(
        "What is violence?",
        "Violence is when someone uses hitting, kicking, shoving, or hurting to try to control a problem. It can scare people and make the problem worse."
    )],
    "problem_solving": [(
        "What is problem solving?",
        "Problem solving means stopping to think about what is wrong and choosing a safe way to fix it. Good problem solving uses calm hands and helpful tools."
    )],
    "stool": [(
        "Why is a step stool better than grabbing wildly for something high?",
        "A steady step stool helps you reach safely while someone keeps it from wobbling. Wild grabbing can make you fall or knock the thing farther away."
    )],
    "cloth": [(
        "Why can a cloth help with a slippery latch?",
        "A cloth gives your hand more grip, so the latch is easier to turn. That means you do not need to kick or yank."
    )],
    "untangle": [(
        "How do you untangle a knot?",
        "You look at the loops one at a time and pull gently in the right order. Going slowly keeps the knot from getting tighter."
    )],
    "teamwork": [(
        "Why is teamwork useful when something is hard?",
        "Teamwork lets one person steady, one person point, and another person pull carefully. Sharing jobs can solve a problem without anyone getting hurt."
    )],
}
KNOWLEDGE_ORDER = ["violence", "problem_solving", "stool", "cloth", "untangle", "teamwork"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    obstacle = f["obstacle"]
    violent_idea = f["violent_idea"]
    solution = f["solution"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short pirate tale for a 3-to-5-year-old that includes the word "violence" and teaches problem solving instead of hurting.',
            f"Tell a pirate-game story where {a.label} wants to {violent_idea.phrase}, but {b.label} stops the idea before anyone gets hurt and the children solve the {obstacle.label} another way.",
            f"Write a gentle story about pretend pirates learning that violence is not brave, and that {solution.phrase} works better.",
        ]
    return [
        'Write a short pirate tale for a 3-to-5-year-old that includes the word "violence" and ends with calm problem solving.',
        f"Tell a pirate-game story where {a.label} is tempted to {violent_idea.phrase}, a grown-up stops it, and the children solve the {obstacle.label} safely.",
        f"Write a child-facing story where a sharp pirate mood turns soft again because the children choose {solution.phrase} instead of violence.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    helper = f["helper"]
    obstacle = f["obstacle"]
    violent_idea = f["violent_idea"]
    solution = f["solution"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, who were pretending to be pirates. {helper.label_word.capitalize()} helped them when their game turned into a real problem."
        ),
        (
            "What was the problem in the pirate game?",
            f"The problem was {obstacle.phrase}. They wanted the treasure, but the obstacle kept the game from moving forward."
        ),
        (
            f"What violent idea did {a.label} suggest?",
            f"{a.label} wanted to {violent_idea.phrase}. {b.label} knew that was a hurtful idea and said they needed a smarter plan."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"Did any violence happen?",
            f"No. {a.label} listened before acting, lowered the toy cutlass, and backed away from the idea. The danger stayed only an idea because {b.label} spoke up in time."
        ))
    else:
        qa.append((
            "What happened when the violent idea was tried?",
            f"It made the game feel scary instead of fun. {violent_idea.effect_line.format(a=a.label, b=b.label)} That is why the grown-up stopped it right away."
        ))
    qa.append((
        "How did they solve the problem?",
        f"They {solution.qa_line}. That worked because it matched the real problem instead of fighting with it."
    ))
    qa.append((
        "What did the children learn at the end?",
        f"They learned that violence is not brave and does not fix pirate problems. Calm hands, teamwork, and the right tool helped them get the treasure safely."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"violence", "problem_solving", "teamwork"}
    solution = world.facts["solution"]
    if solution.id == "stool_reach":
        tags.add("stool")
    elif solution.id == "cloth_twist":
        tags.add("cloth")
    elif solution.id == "untangle_together":
        tags.add("untangle")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_obstacle_mismatch(violent_idea: ViolentIdea, obstacle: Obstacle) -> str:
    return (
        f"(No story: '{violent_idea.id}' does not fit the obstacle '{obstacle.id}'. "
        f"The violent impulse must be a plausible bad idea for that problem.)"
    )


def explain_solution_mismatch(solution: Solution, obstacle: Obstacle) -> str:
    if solution.sense < SENSE_MIN:
        return (
            f"(No story: refusing solution '{solution.id}' because it scores too low on common sense "
            f"(sense={solution.sense} < {SENSE_MIN}). Pick a calmer, more useful fix.)"
        )
    return (
        f"(No story: '{solution.id}' does not actually solve '{obstacle.id}'. "
        f"The ending fix must match the real pirate problem.)"
    )


ASP_RULES = r"""
fits_vi(V, O) :- violent_idea(V), obstacle(O), works_on(V, O).
fits_sol(S, O) :- solution(S), obstacle(O), solves(S, O), sense(S, N), sense_min(M), N >= M.
valid(O, V, S) :- obstacle(O), violent_idea(V), solution(S), fits_vi(V, O), fits_sol(S, O).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

outcome(averted) :- averted.
outcome(repaired) :- not averted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for violent_id, violent_idea in VIOLENT_IDEAS.items():
        lines.append(asp.fact("violent_idea", violent_id))
        for obstacle_id in sorted(violent_idea.works_on):
            lines.append(asp.fact("works_on", violent_id, obstacle_id))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        lines.append(asp.fact("sense", solution_id, solution.sense))
        for obstacle_id in sorted(solution.solves):
            lines.append(asp.fact("solves", solution_id, obstacle_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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
        print("MISMATCH in combo gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
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
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale storyworld: a tempting violent idea, a real problem, and a better solution."
    )
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--violent-idea", dest="violent_idea", choices=VIOLENT_IDEAS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.violent_idea:
        if not violent_idea_fits(VIOLENT_IDEAS[args.violent_idea], OBSTACLES[args.obstacle]):
            raise StoryError(explain_obstacle_mismatch(VIOLENT_IDEAS[args.violent_idea], OBSTACLES[args.obstacle]))
    if args.obstacle and args.solution:
        if not solution_fits(SOLUTIONS[args.solution], OBSTACLES[args.obstacle]):
            raise StoryError(explain_solution_mismatch(SOLUTIONS[args.solution], OBSTACLES[args.obstacle]))

    combos = [
        combo for combo in valid_combos()
        if (args.obstacle is None or combo[0] == args.obstacle)
        and (args.violent_idea is None or combo[1] == args.violent_idea)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    obstacle, violent_idea, solution = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        obstacle=obstacle,
        violent_idea=violent_idea,
        solution=solution,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        helper=helper,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.violent_idea not in VIOLENT_IDEAS:
        raise StoryError(f"(Unknown violent idea: {params.violent_idea})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")

    obstacle = OBSTACLES[params.obstacle]
    violent_idea = VIOLENT_IDEAS[params.violent_idea]
    solution = SOLUTIONS[params.solution]

    if not violent_idea_fits(violent_idea, obstacle):
        raise StoryError(explain_obstacle_mismatch(violent_idea, obstacle))
    if not solution_fits(solution, obstacle):
        raise StoryError(explain_solution_mismatch(solution, obstacle))

    world = tell(
        obstacle=obstacle,
        violent_idea=violent_idea,
        solution=solution,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        helper_type=params.helper,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
    )
    world.get("instigator").label = params.instigator
    world.get("cautioner").label = params.cautioner
    sample = StorySample(
        params=params,
        story=world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )
    return sample


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
        print(f"{len(combos)} compatible (obstacle, violent_idea, solution) combos:\n")
        for obstacle, violent_idea, solution in combos:
            print(f"  {obstacle:12} {violent_idea:12} {solution}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.obstacle} / {p.violent_idea} / {p.solution} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
