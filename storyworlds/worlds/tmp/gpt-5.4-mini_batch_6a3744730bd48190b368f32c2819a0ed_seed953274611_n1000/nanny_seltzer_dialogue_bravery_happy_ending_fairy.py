#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nanny_seltzer_dialogue_bravery_happy_ending_fairy.py
=====================================================================================

A small standalone storyworld for a fairy-tale style tale about a nanny, a
sparkling seltzer wish, a brave choice, dialogue, and a happy ending.

The world is intentionally tiny and classical:
- A child wants a shiny, fizzy thing that is a bit too fancy or risky for a
  quiet moment.
- A nanny uses calm dialogue to guide the child toward courage.
- The child shows bravery by speaking up or trying the safe thing.
- The ending proves a real change in the world state: the child calms down,
  the problem is solved, and the scene ends bright and happy.

This file follows the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- a forward-chained world model
- a Python reasonableness gate plus inline ASP twin
- three Q&A sets grounded in the simulated world
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "nanny"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"nanny": "nanny"}.get(self.type, self.label or self.type)


@dataclass
class Scene:
    id: str
    place: str
    mood: str
    detail: str
    prompt: str
    ending_image: str


@dataclass
class Problem:
    id: str
    label: str
    shiny: str
    sound: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeChoice:
    id: str
    label: str
    action: str
    result: str
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


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    nanny = world.entities.get("nanny")
    if not child or not nanny:
        return out
    if child.memes["bravery"] >= BRAVERY_MIN and nanny.memes["hope"] >= 1:
        sig = ("bravery", "rise")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += 1
            nanny.memes["pride"] += 1
            out.append("The child stood a little taller.")
    return out


def _r_resolution(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["problem_solved"] >= THRESHOLD:
        sig = ("resolution", "glow")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["joy"] += 1
            out.append("The room felt brighter at once.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("bravery", "social", _r_bravery),
    Rule("resolution", "emotional", _r_resolution),
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
            world.say(s)
    return produced


def reasonabler(problem: Problem) -> bool:
    return problem.risky and problem.id in PROBLEMS


def safe_choices() -> list[SafeChoice]:
    return list(SAFE_CHOICES.values())


def would_problem(problem: Problem, choice: SafeChoice) -> bool:
    return problem.risky and choice.id in {"bubble", "cup"} and problem.id == "seltzer"


def predict(world: World, problem_id: str, choice_id: str) -> dict:
    sim = world.copy()
    child = sim.get("child")
    problem = PROBLEMS[problem_id]
    choice = SAFE_CHOICES[choice_id]
    _attempt(sim, child, problem, choice, narrate=False)
    return {
        "solved": bool(sim.get("child").meters["problem_solved"] >= THRESHOLD),
        "joy": sim.get("child").memes["joy"],
    }


def _attempt(world: World, child: Entity, problem: Problem, choice: SafeChoice,
             narrate: bool = True) -> None:
    if choice.id == "bubble":
        child.meters["problem_solved"] += 1
        child.meters["sparkle"] += 1
    elif choice.id == "cup":
        child.meters["problem_solved"] += 1
        child.meters["sparkle"] += 1
    elif choice.id == "shield":
        child.meters["problem_solved"] += 1
        child.meters["sparkle"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, scene: Scene, child: Entity, nanny: Entity, problem: Problem) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Once in a little fairy-tale house near the green lane, {child.id} and "
        f"{nanny.id} sat by a window in {scene.place}. {scene.detail}"
    )
    world.say(
        f'"{problem.label}!" {child.id} whispered. "{problem.sound} {problem.shiny}!"'
    )


def warning(world: World, nanny: Entity, child: Entity, problem: Problem) -> None:
    nanny.memes["hope"] += 1
    world.say(
        f'"Dear child," {nanny.id} said, "that is bright, but we must be careful '
        f'with {problem.label}. It is best to choose the safe way."'
    )


def brave_choice(world: World, child: Entity, choice: SafeChoice) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} took a breath and said, "
        f'"I can be brave if I choose wisely."'
    )
    world.say(f"Then {child.id} reached for {choice.label}.")


def dialogue_turn(world: World, nanny: Entity, child: Entity, choice: SafeChoice) -> None:
    world.say(
        f'"That is the spirit," {nanny.id} smiled. "{choice.action.capitalize()}, '
        f'and we shall still have our fun."'
    )


def resolve(world: World, nanny: Entity, child: Entity, scene: Scene, choice: SafeChoice) -> None:
    child.memes["joy"] += 1
    child.memes["fear"] = 0.0
    child.meters["problem_solved"] = 1.0
    child.meters["sparkle"] += 1
    world.say(
        f"{choice.result.capitalize()}. {nanny.id} laughed softly, and {child.id} "
        f"laughed too."
    )
    world.say(
        f"By the end, {scene.ending_image}. The little house felt safe and warm, "
        f"as if it had been tucked in by a kindly star."
    )


SCENES = {
    "cottage": Scene(
        id="cottage",
        place="a tiny cottage kitchen",
        mood="gentle",
        detail="A blue kettle rested on the stove, and a single candle glowed on the shelf.",
        prompt="a cottage story",
        ending_image="the candle flickered kindly beside two smiling faces",
    ),
    "garden": Scene(
        id="garden",
        place="a flower garden porch",
        mood="bright",
        detail="Roses climbed the fence, and the sun painted gold on the stepping stones.",
        prompt="a garden story",
        ending_image="the roses shone as the child held a safe cup of bubbles",
    ),
    "hall": Scene(
        id="hall",
        place="a castle hall",
        mood="grand",
        detail="A painted shield hung on the wall, and soft drapes moved like clouds.",
        prompt="a castle story",
        ending_image="the drapes swayed while the child grinned beside the nanny",
    ),
}

PROBLEMS = {
    "seltzer": Problem(
        id="seltzer",
        label="seltzer",
        shiny="sparkly",
        sound="It went",
        risky=True,
        tags={"sparkle", "drink"},
    ),
    "glass": Problem(
        id="glass",
        label="a glass slipper",
        shiny="glittery",
        sound="It gleamed",
        risky=True,
        tags={"glitter", "fairy_tale"},
    ),
    "mirror": Problem(
        id="mirror",
        label="a silver mirror",
        shiny="moon-bright",
        sound="It flashed",
        risky=True,
        tags={"mirror", "shine"},
    ),
}

SAFE_CHOICES = {
    "bubble": SafeChoice(
        id="bubble",
        label="a little bubble wand",
        action="blow bubbles with the wand",
        result="The bubbles floated up like tiny moons",
        tags={"bubbles", "safe"},
    ),
    "cup": SafeChoice(
        id="cup":=None,  # type: ignore[misc]
        label="a cup of chilled water",
        action="pour a cup for a small sip",
        result="The child took a neat sip and smiled",
        tags={"water", "safe"},
    ),
    "shield": SafeChoice(
        id="shield",
        label="a painted shield",
        action="hold the shield and dance by the window",
        result="The shield flashed like a brave little sun",
        tags={"dance", "safe"},
    ),
}
