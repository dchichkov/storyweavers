#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py
================================================================================

A standalone story world about a small animal writer in a toy library who needs a
bundle of story things for sharing time, but a concrete problem gets in the way.
The story is driven by simulated state: an obstacle blocks the bundle, the
characters talk, they inspect the problem, and they choose a sensible fix.

The world prefers a small set of plausible combinations over broad coverage:
each bundle only has certain reasonable problems, and each problem only has a
few sensible fixes. Explicit unreasonable choices are rejected with StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py
    python storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py --bundle puppet_bundle --problem tight_knot
    python storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py --fix jump
    python storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py --trace
    python storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py --json
    python storyworlds/worlds/gpt-5.4/writer_bundle_toy_library_dialogue_problem_solving.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose", "cat", "rabbit"}
        male = {"boy", "father", "bear", "fox", "mouse", "beaver"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "owl":
            return "owl"
        return self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Bundle:
    id: str
    label: str
    phrase: str
    use_for: str
    texture: str
    problems: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Problem:
    id: str
    label: str
    place: str
    clue: str
    block_text: str
    solve_goal: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    solves: set[str] = field(default_factory=set)
    tool_phrase: str = ""
    inspect_text: str = ""
    action_text: str = ""
    result_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_blocked_worry(world: World) -> list[str]:
    bundle = world.get("bundle")
    hero = world.get("hero")
    if bundle.meters["blocked"] < THRESHOLD:
        return []
    sig = ("blocked_worry", bundle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["need_help"] += 1
    return []


def _r_ready_relief(world: World) -> list[str]:
    bundle = world.get("bundle")
    hero = world.get("hero")
    friend = world.get("friend")
    if bundle.meters["ready"] < THRESHOLD:
        return []
    sig = ("ready_relief", bundle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    friend.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="blocked_worry", tag="emotional", apply=_r_blocked_worry),
    Rule(name="ready_relief", tag="emotional", apply=_r_ready_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def bundle_problem_ok(bundle: Bundle, problem: Problem) -> bool:
    return problem.id in bundle.problems


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def fix_works(problem: Problem, fix: Fix) -> bool:
    return problem.id in fix.solves and fix.sense >= SENSE_MIN


def explain_bundle_problem(bundle: Bundle, problem: Problem) -> str:
    return (
        f"(No story: {bundle.phrase} is not the kind of toy-library bundle that is "
        f"usually blocked by {problem.label}. Pick a problem that fits this bundle.)"
    )


def explain_fix(problem: Problem, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        better = ", ".join(sorted(f.id for f in sensible_fixes()))
        return (
            f"(Refusing fix '{fix.id}': it is too flimsy for a careful toy-library "
            f"story (sense={fix.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {fix.label} does not honestly solve {problem.label}. "
        f"Choose a fix that matches the problem.)"
    )


def predict_solved(world: World, fix: Fix) -> dict:
    sim = world.copy()
    problem = sim.facts["problem"]
    bundle = sim.get("bundle")
    _apply_fix_state(sim, problem, fix)
    return {
        "ready": bundle.meters["ready"] >= THRESHOLD,
        "blocked": bundle.meters["blocked"] >= THRESHOLD,
    }


def _apply_problem_state(world: World, problem: Problem) -> None:
    bundle = world.get("bundle")
    bundle.meters["blocked"] = 1.0
    bundle.attrs["problem"] = problem.id
    if problem.id == "high_shelf":
        bundle.meters["high"] = 1.0
    elif problem.id == "tight_knot":
        bundle.meters["knotted"] = 1.0
    elif problem.id == "mixed_bin":
        bundle.meters["buried"] = 1.0
    propagate(world, narrate=False)


def _apply_fix_state(world: World, problem: Problem, fix: Fix) -> None:
    bundle = world.get("bundle")
    if not fix_works(problem, fix):
        return
    bundle.meters["blocked"] = 0.0
    bundle.meters["high"] = 0.0
    bundle.meters["knotted"] = 0.0
    bundle.meters["buried"] = 0.0
    bundle.meters["ready"] = 1.0
    propagate(world, narrate=False)


def introduce(world: World, hero: Entity, friend: Entity, bundle_cfg: Bundle) -> None:
    hero.memes["hope"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"In the toy library, {hero.id} the {hero.type} was a tiny writer with a very big plan. "
        f"He wanted to use {bundle_cfg.phrase} for {bundle_cfg.use_for}."
    )
    world.say(
        f"{friend.id} the {friend.type} padded beside him between the low shelves. "
        f'"What kind of story are you making today?" {friend.id} asked.'
    )
    world.say(
        f'"One with whispers, giggles, and a brave ending," said {hero.id}. '
        f'"But first I need my {bundle_cfg.label}."'
    )


def discover(world: World, hero: Entity, friend: Entity, bundle_cfg: Bundle, problem: Problem) -> None:
    bundle = world.get("bundle")
    _apply_problem_state(world, problem)
    world.say(
        f"They hurried to {problem.place}, where {bundle_cfg.phrase} waited. "
        f"But {problem.block_text}"
    )
    world.say(
        f'{hero.id} stopped short. "{problem.clue}" he said.'
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{friend.id} saw {hero.id}'s ears dip. "
            f'"It is all right," {friend.id} said. "We can look first and think next."'
        )


def inspect(world: World, hero: Entity, friend: Entity, fix: Fix, problem: Problem) -> None:
    hero.memes["focus"] += 1
    friend.memes["focus"] += 1
    world.say(
        f'Together they looked closely. "{fix.inspect_text}" said {friend.id}.'
    )
    pred = predict_solved(world, fix)
    world.facts["predicted_ready"] = pred["ready"]
    if pred["ready"]:
        world.say(
            f'"Then {fix.tool_phrase} can help," said {hero.id}. '
            f'"Let\'s try the careful way."'
        )
    else:
        world.say(
            f'"That still will not {problem.solve_goal}," said {hero.id}. '
            f'"We need a better plan."'
        )


def solve(world: World, hero: Entity, friend: Entity, librarian: Entity, problem: Problem, fix: Fix, bundle_cfg: Bundle) -> None:
    bundle = world.get("bundle")
    hero.memes["courage"] += 1
    friend.memes["care"] += 1
    librarian.memes["warmth"] += 1
    world.say(
        f'{librarian.id} the owl heard their quiet voices and fluttered down. '
        f'"Tell me your plan," she said.'
    )
    world.say(
        f'"We think {fix.tool_phrase} will work," said {hero.id}.'
    )
    world.say(
        f'"A thoughtful plan," said {librarian.id}. "Go on together."'
    )
    _apply_fix_state(world, problem, fix)
    world.say(fix.action_text)
    if bundle.meters["ready"] >= THRESHOLD:
        world.say(fix.result_text.replace("{bundle}", bundle_cfg.label))
        world.say(
            f"{hero.id} hugged the {bundle_cfg.label} close. "
            f'"Now the story can begin," he said.'
        )


def ending(world: World, hero: Entity, friend: Entity, librarian: Entity, bundle_cfg: Bundle) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Soon they were on the round rug in the middle of the toy library. "
        f"{friend.id} passed out cushions, and {librarian.id} set a lamp on the little table."
    )
    world.say(
        f'{hero.id} opened the {bundle_cfg.label}, smoothed the {bundle_cfg.texture}, and began to read in his soft writer voice.'
    )
    world.say(
        f"The toy library grew still to listen. At the end, {friend.id} clapped first, "
        f"and {librarian.id}'s eyes shone like moon-buttons."
    )
    world.say(
        f"{hero.id} no longer looked worried at all. He looked like a writer who had learned that a bundle and a problem could both open with patient talk and a good plan."
    )


def tell(
    bundle_cfg: Bundle,
    problem: Problem,
    fix: Fix,
    hero_name: str = "Pip",
    hero_type: str = "mouse",
    friend_name: str = "Moss",
    friend_type: str = "rabbit",
    librarian_name: str = "Oona",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="writer", traits=["small", "thoughtful"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", traits=["steady", "kind"]))
    librarian = world.add(Entity(id=librarian_name, kind="character", type="owl", role="librarian", label="the librarian", traits=["calm", "watchful"]))
    bundle = world.add(Entity(id="bundle", kind="thing", type="bundle", label=bundle_cfg.label, attrs={"texture": bundle_cfg.texture}))
    world.facts.update(
        hero=hero,
        friend=friend,
        librarian=librarian,
        bundle_cfg=bundle_cfg,
        problem=problem,
        fix=fix,
    )

    introduce(world, hero, friend, bundle_cfg)
    world.para()
    discover(world, hero, friend, bundle_cfg, problem)
    world.para()
    inspect(world, hero, friend, fix, problem)
    world.para()
    solve(world, hero, friend, librarian, problem, fix, bundle_cfg)
    world.para()
    ending(world, hero, friend, librarian, bundle_cfg)

    world.facts.update(
        solved=bundle.meters["ready"] >= THRESHOLD,
        blocked=bundle.meters["blocked"] >= THRESHOLD,
        bundle=bundle,
    )
    return world


BUNDLES = {
    "card_bundle": Bundle(
        id="card_bundle",
        label="bundle of story cards",
        phrase="a bundle of story cards tied in soft cloth",
        use_for="the afternoon sharing circle",
        texture="painted cards",
        problems={"high_shelf", "mixed_bin"},
        tags={"cards", "bundle", "story"},
    ),
    "puppet_bundle": Bundle(
        id="puppet_bundle",
        label="bundle of finger puppets",
        phrase="a bundle of finger puppets wrapped in a ribbon",
        use_for="a tiny puppet story",
        texture="felt puppets",
        problems={"tight_knot", "high_shelf"},
        tags={"puppets", "bundle", "story"},
    ),
    "block_bundle": Bundle(
        id="block_bundle",
        label="bundle of rhyme blocks",
        phrase="a bundle of rhyme blocks in a canvas strap",
        use_for="making a click-clack rhyme tale",
        texture="wooden blocks",
        problems={"mixed_bin", "tight_knot"},
        tags={"blocks", "bundle", "rhyme"},
    ),
}

PROBLEMS = {
    "high_shelf": Problem(
        id="high_shelf",
        label="a shelf that is too high",
        place="the tallest moon shelf",
        clue="Oh dear. It is up where my paws cannot reach",
        block_text="the bundle sat on the highest shelf, just above {hero}'s reach.".replace("{hero}", "the little writer"),
        solve_goal="bring the bundle down safely",
        tags={"high", "shelf"},
    ),
    "tight_knot": Problem(
        id="tight_knot",
        label="a knot tied too tight",
        place="the ribbon basket by the reading rug",
        clue="The ribbon is pinched into a hard little knot",
        block_text="the ribbon around it had pulled into such a tight knot that not even one puppet nose could peek out.",
        solve_goal="loosen the knot without tearing the bundle",
        tags={"knot", "ribbon"},
    ),
    "mixed_bin": Problem(
        id="mixed_bin",
        label="a bundle buried in the wrong bin",
        place="the sorting corner beside the block tubs",
        clue="This is the wrong bin, and everything is mixed together",
        block_text="the bundle had slid into a bin full of toy blocks and beanbags, so only one corner showed.",
        solve_goal="find the bundle without making a bigger mess",
        tags={"sorting", "bin"},
    ),
}

FIXES = {
    "stool": Fix(
        id="stool",
        label="a rolling stool",
        sense=3,
        solves={"high_shelf"},
        tool_phrase="the little rolling stool",
        inspect_text="If the bundle is high, our paws do not need to grow; we need to grow taller for one minute",
        action_text="Moss rolled over the little stool, held it steady, and Pip climbed up one careful step at a time.",
        result_text="From the top, he could reach the {bundle} at last, and he carried it down with both paws.",
        qa_text="They used the little rolling stool so Pip could reach the bundle safely.",
        tags={"stool", "problem_solving"},
    ),
    "unwind": Fix(
        id="unwind",
        label="patient unwinding",
        sense=3,
        solves={"tight_knot"},
        tool_phrase="patient paws and one loose ribbon end",
        inspect_text="A knot often has one sleepy end hiding under the other loop",
        action_text="Pip held the ribbon still while Moss found the sleepy end and teased it loose, bit by bit, until the knot gave a tiny sigh.",
        result_text="The ribbon relaxed, and the {bundle} opened without a rip.",
        qa_text="They solved it by finding the loose ribbon end and unwinding the knot slowly together.",
        tags={"knot", "problem_solving"},
    ),
    "sort": Fix(
        id="sort",
        label="sorting by color",
        sense=3,
        solves={"mixed_bin"},
        tool_phrase="a slow color sort on the floor mat",
        inspect_text="If everything is mixed, we can make small groups and let the right shape show itself",
        action_text="They spread a floor mat beside the bin and sorted the loose toys into gentle color rows: blue, red, yellow, green.",
        result_text="When the rows were neat, the hidden {bundle} was easy to spot and lift out.",
        qa_text="They spread the toys onto a floor mat and sorted them into small groups until the bundle was easy to see.",
        tags={"sorting", "problem_solving"},
    ),
    "jump": Fix(
        id="jump",
        label="jumping for it",
        sense=1,
        solves={"high_shelf"},
        tool_phrase="a big jump",
        inspect_text="Maybe I can spring high enough",
        action_text="Pip bent his knees for a wild jump.",
        result_text="But the bundle wobbled and did not come down safely.",
        qa_text="They tried jumping, but it was not a careful plan.",
        tags={"high"},
    ),
    "pull_hard": Fix(
        id="pull_hard",
        label="pulling hard",
        sense=1,
        solves={"tight_knot"},
        tool_phrase="a hard tug",
        inspect_text="Maybe the knot will just pop",
        action_text="They both gave the ribbon a rough pull.",
        result_text="But the knot only tightened more.",
        qa_text="They pulled hard, but that only made the knot tighter.",
        tags={"knot"},
    ),
    "dig_fast": Fix(
        id="dig_fast",
        label="digging fast",
        sense=1,
        solves={"mixed_bin"},
        tool_phrase="fast digging paws",
        inspect_text="Maybe we can toss everything aside until we find it",
        action_text="The toys flew every which way across the floor.",
        result_text="But the bundle was even harder to see in the bigger mess.",
        qa_text="They dug too fast and made the mess worse.",
        tags={"sorting"},
    ),
}

ANIMALS = {
    "mouse": ["Pip", "Nib", "Tumble"],
    "rabbit": ["Moss", "Fern", "Hopper"],
    "fox": ["Rill", "Soot", "Maple"],
    "beaver": ["Tup", "Clover", "Bramble"],
    "cat": ["Mira", "Tansy", "Dot"],
    "hen": ["Poppy", "Rue", "Lark"],
}

KNOWLEDGE = {
    "toy_library": [
        (
            "What is a toy library?",
            "A toy library is a place where children and families can borrow toys, games, and story things to use and then bring back later."
        )
    ],
    "writer": [
        (
            "What does a writer do?",
            "A writer makes stories with words. A writer thinks about what happens first, next, and last."
        )
    ],
    "bundle": [
        (
            "What is a bundle?",
            "A bundle is a group of things tied or held together. Bundles are easier to carry, but sometimes they can also be tricky to open."
        )
    ],
    "stool": [
        (
            "What is a stool for?",
            "A stool is a small seat or step you can stand on to reach something higher. A careful stool helps you reach without jumping."
        )
    ],
    "knot": [
        (
            "Why is it better to loosen a knot slowly?",
            "A knot often has one little end holding it together. If you work slowly, you can find that end instead of pulling the knot tighter."
        )
    ],
    "sorting": [
        (
            "Why does sorting help when things are mixed up?",
            "Sorting puts similar things together, so your eyes can find what is different. It turns one big mess into small, easy groups."
        )
    ],
    "dialogue": [
        (
            "How can talking help solve a problem?",
            "Talking helps people share clues and ideas. When everyone says what they notice, the best plan becomes easier to see."
        )
    ],
}
KNOWLEDGE_ORDER = ["toy_library", "writer", "bundle", "stool", "knot", "sorting", "dialogue"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for bundle_id, bundle in BUNDLES.items():
        for problem_id, problem in PROBLEMS.items():
            if not bundle_problem_ok(bundle, problem):
                continue
            for fix_id, fix in FIXES.items():
                if fix_works(problem, fix):
                    combos.append((bundle_id, problem_id, fix_id))
    return combos


@dataclass
class StoryParams:
    bundle: str
    problem: str
    fix: str
    hero_type: str
    hero_name: str
    friend_type: str
    friend_name: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    bundle_cfg = f["bundle_cfg"]
    problem = f["problem"]
    return [
        f'Write an animal story set in a toy library that includes the words "writer" and "bundle".',
        f"Tell a gentle dialogue-and-problem-solving story where {hero.id} the {hero.type} needs {bundle_cfg.phrase}, but {problem.label} gets in the way and {friend.id} helps talk through a careful plan.",
        f"Write a child-facing story about a tiny writer in a toy library who solves one concrete problem by looking closely, speaking kindly, and choosing the right tool.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    librarian = f["librarian"]
    bundle_cfg = f["bundle_cfg"]
    problem = f["problem"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type}, a little writer in the toy library, and {friend.id} the {friend.type} who helps him."
        ),
        (
            f"Why did {hero.id} need the {bundle_cfg.label}?",
            f"He wanted it for {bundle_cfg.use_for}. The bundle held the story things he needed to begin."
        ),
        (
            "What was the problem?",
            f"The problem was {problem.label}. Because of that, the bundle was blocked and {hero.id} could not start his story right away."
        ),
        (
            f"How did talking help {hero.id} and {friend.id}?",
            f"They did not grab or guess first. They talked about what they noticed, which helped them choose a careful plan instead of making the problem worse."
        ),
    ]
    if f.get("solved"):
        qa.append(
            (
                f"How did they solve the problem?",
                f"{fix.qa_text} That worked because it matched the real problem instead of fighting the bundle the wrong way."
            )
        )
        qa.append(
            (
                f"How did {hero.id} feel at the end?",
                f"He felt relieved and proud. At the end he could open the {bundle_cfg.label} and read in his soft writer voice."
            )
        )
        qa.append(
            (
                "What changed from the beginning to the end?",
                f"At first the bundle was blocked, so the story could not start. By the end the bundle was ready, the friends were calm again, and the toy library was listening to {hero.id}'s story."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"toy_library", "writer", "bundle", "dialogue"}
    problem = f["problem"]
    fix = f["fix"]
    if "high" in problem.tags or "stool" in fix.tags:
        tags.add("stool")
    if "knot" in problem.tags or "knot" in fix.tags:
        tags.add("knot")
    if "sorting" in problem.tags or "sorting" in fix.tags:
        tags.add("sorting")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
bundle_problem_ok(B, P) :- bundle_problem(B, P).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
works(P, F) :- solves(F, P), sensible(F).
valid(B, P, F) :- bundle(B), problem(P), fix(F), bundle_problem_ok(B, P), works(P, F).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bundle_id, bundle in BUNDLES.items():
        lines.append(asp.fact("bundle", bundle_id))
        for problem_id in sorted(bundle.problems):
            lines.append(asp.fact("bundle_problem", bundle_id, problem_id))
    for problem_id in PROBLEMS:
        lines.append(asp.fact("problem", problem_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for problem_id in sorted(fix.solves):
            lines.append(asp.fact("solves", fix_id, problem_id))
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
    return sorted(item for (item,) in asp.atoms(model, "sensible"))


CURATED = [
    StoryParams(
        bundle="card_bundle",
        problem="high_shelf",
        fix="stool",
        hero_type="mouse",
        hero_name="Pip",
        friend_type="rabbit",
        friend_name="Moss",
    ),
    StoryParams(
        bundle="puppet_bundle",
        problem="tight_knot",
        fix="unwind",
        hero_type="fox",
        hero_name="Maple",
        friend_type="cat",
        friend_name="Dot",
    ),
    StoryParams(
        bundle="block_bundle",
        problem="mixed_bin",
        fix="sort",
        hero_type="beaver",
        hero_name="Bramble",
        friend_type="hen",
        friend_name="Poppy",
    ),
    StoryParams(
        bundle="block_bundle",
        problem="tight_knot",
        fix="unwind",
        hero_type="mouse",
        hero_name="Nib",
        friend_type="rabbit",
        friend_name="Fern",
    ),
    StoryParams(
        bundle="puppet_bundle",
        problem="high_shelf",
        fix="stool",
        hero_type="cat",
        hero_name="Mira",
        friend_type="fox",
        friend_name="Rill",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal-story world: a tiny writer, a bundle in a toy library, and a gentle problem-solving dialogue."
    )
    ap.add_argument("--bundle", choices=sorted(BUNDLES))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--fix", choices=sorted(FIXES))
    ap.add_argument("--hero-type", choices=sorted(ANIMALS))
    ap.add_argument("--friend-type", choices=sorted(ANIMALS))
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, animal_type: str, avoid: str = "") -> str:
    names = [n for n in ANIMALS[animal_type] if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bundle and args.problem:
        bundle = BUNDLES[args.bundle]
        problem = PROBLEMS[args.problem]
        if not bundle_problem_ok(bundle, problem):
            raise StoryError(explain_bundle_problem(bundle, problem))
    if args.problem and args.fix:
        problem = PROBLEMS[args.problem]
        fix = FIXES[args.fix]
        if not fix_works(problem, fix):
            raise StoryError(explain_fix(problem, fix))
    elif args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(next(iter(PROBLEMS.values())), FIXES[args.fix]))

    combos = [
        combo for combo in valid_combos()
        if (args.bundle is None or combo[0] == args.bundle)
        and (args.problem is None or combo[1] == args.problem)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bundle_id, problem_id, fix_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(sorted(ANIMALS))
    friend_choices = [a for a in sorted(ANIMALS) if a != hero_type] or [hero_type]
    friend_type = args.friend_type or rng.choice(friend_choices)
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type, avoid=hero_name)

    return StoryParams(
        bundle=bundle_id,
        problem=problem_id,
        fix=fix_id,
        hero_type=hero_type,
        hero_name=hero_name,
        friend_type=friend_type,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.bundle not in BUNDLES:
        raise StoryError(f"(Unknown bundle '{params.bundle}').")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem '{params.problem}').")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix '{params.fix}').")
    if params.hero_type not in ANIMALS:
        raise StoryError(f"(Unknown hero type '{params.hero_type}').")
    if params.friend_type not in ANIMALS:
        raise StoryError(f"(Unknown friend type '{params.friend_type}').")

    bundle_cfg = BUNDLES[params.bundle]
    problem = PROBLEMS[params.problem]
    fix = FIXES[params.fix]

    if not bundle_problem_ok(bundle_cfg, problem):
        raise StoryError(explain_bundle_problem(bundle_cfg, problem))
    if not fix_works(problem, fix):
        raise StoryError(explain_fix(problem, fix))

    world = tell(
        bundle_cfg=bundle_cfg,
        problem=problem,
        fix=fix,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    python_sens = {fix.id for fix in sensible_fixes()}
    clingo_sens = set(asp_sensible())
    if python_sens == clingo_sens:
        print(f"OK: sensible fixes match ({sorted(python_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sens)} python={sorted(python_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        text = buf.getvalue()
        if "smoke" not in text or "toy library" not in sample.story:
            raise StoryError("(Smoke test failed: emit() did not produce expected output.)")
        print("OK: smoke test passed for generate() and emit().")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Random smoke test generated an empty story.)")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke test passed for 10 seeds.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (bundle, problem, fix) combos:\n")
        for bundle_id, problem_id, fix_id in combos:
            print(f"  {bundle_id:14} {problem_id:12} {fix_id}")
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
            header = f"### {p.hero_name}: {p.bundle} with {p.problem} -> {p.fix}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
