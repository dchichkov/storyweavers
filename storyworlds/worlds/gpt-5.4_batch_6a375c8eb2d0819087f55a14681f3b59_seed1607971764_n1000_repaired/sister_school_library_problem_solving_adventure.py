#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sister_school_library_problem_solving_adventure.py
=============================================================================

A standalone storyworld about two siblings in a school library turning a small
problem into an adventure. The older child is always a sister. She and her
younger sibling are following a class reading quest, something goes wrong, and
they solve it in a sensible way.

The world model prefers concrete, reasonable problem-solving moves:
- a missing book is solved by the catalog or the librarian
- a book on a high shelf is solved by a step stool or the librarian
- a needed clue hidden on the return cart is solved by scanning the cart or
  asking the librarian

Unsafe or weak moves are known to the model but refused.

Run it
------
    python storyworlds/worlds/gpt-5.4/sister_school_library_problem_solving_adventure.py
    python storyworlds/worlds/gpt-5.4/sister_school_library_problem_solving_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sister_school_library_problem_solving_adventure.py --all
    python storyworlds/worlds/gpt-5.4/sister_school_library_problem_solving_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/sister_school_library_problem_solving_adventure.py --json
    python storyworlds/worlds/gpt-5.4/sister_school_library_problem_solving_adventure.py --asp
    python storyworlds/worlds/gpt-5.4/sister_school_library_problem_solving_adventure.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "librarian_f"}
        male = {"boy", "man", "father", "librarian_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "librarian_f" or self.type == "librarian_m":
            return "librarian"
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
class Mission:
    id: str
    title: str
    object_label: str
    intro: str
    goal: str
    ending: str
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
class Obstacle:
    id: str
    label: str
    scene: str
    risk: str
    discover: str
    solved_by: set[str] = field(default_factory=set)
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
class Solution:
    id: str
    label: str
    sense: int
    helped: bool
    action: str
    result: str
    qa_text: str
    unsafe: bool = False
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
class StoryParams:
    mission: str
    obstacle: str
    solution: str
    sister_name: str
    sibling_name: str
    sibling_gender: str
    librarian_gender: str
    sister_trait: str
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


def _r_problem_pressure(world: World) -> list[str]:
    mission = world.facts.get("mission_obj")
    obstacle = world.facts.get("obstacle_obj")
    if mission is None or obstacle is None:
        return []
    sig = ("problem_pressure", obstacle.id)
    if sig in world.fired:
        return []
    if world.get("problem").meters["active"] < THRESHOLD:
        return []
    world.fired.add(sig)
    sister = world.get("sister")
    sibling = world.get("sibling")
    sister.memes["worry"] += 1
    sibling.memes["worry"] += 1
    world.get("problem").meters["confusion"] += 1
    return []


def _r_sister_calm(world: World) -> list[str]:
    sister = world.get("sister")
    sibling = world.get("sibling")
    if sister.memes["plan"] < THRESHOLD:
        return []
    sig = ("sister_calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    sibling.memes["bravery"] += 1
    sibling.memes["trust"] += 1
    return []


def _r_solution_success(world: World) -> list[str]:
    problem = world.get("problem")
    clue = world.get("clue")
    if problem.meters["solved"] < THRESHOLD:
        return []
    sig = ("solution_success",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    problem.meters["active"] = 0.0
    problem.meters["confusion"] = 0.0
    clue.meters["found"] += 1
    for kid_id in ("sister", "sibling"):
        kid = world.get(kid_id)
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="problem_pressure", tag="emotional", apply=_r_problem_pressure),
    Rule(name="sister_calm", tag="social", apply=_r_sister_calm),
    Rule(name="solution_success", tag="resolution", apply=_r_solution_success),
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


MISSIONS = {
    "dragon_map": Mission(
        id="dragon_map",
        title="The Dragon Map",
        object_label="the red atlas with the dragon on the cover",
        intro="their class had started a reading quest, and today's clue said the next step was hidden in a red atlas with a dragon on the cover",
        goal="the map stamp for their class adventure chart",
        ending="At the last table, they stamped the dragon map and grinned as if they had crossed a mountain pass.",
        tags={"atlas", "map", "adventure"},
    ),
    "moon_key": Mission(
        id="moon_key",
        title="The Moon Key",
        object_label="the silver astronomy book with the tiny moon key tucked inside",
        intro="their class was hunting pieces of a pretend space mission, and today's hint pointed to a silver astronomy book with a moon key inside",
        goal="the moon key sticker for the class mission board",
        ending="When the moon key sticker clicked onto the board, the whole mission felt bright and brave again.",
        tags={"astronomy", "space", "adventure"},
    ),
    "jungle_riddle": Mission(
        id="jungle_riddle",
        title="The Jungle Riddle",
        object_label="the green animal dictionary holding the jungle riddle card",
        intro="their class adventure trail said the jungle riddle card was waiting in a green animal dictionary",
        goal="the answer card for the jungle trail",
        ending="Soon they were whispering the jungle answer over the page as if they had hacked a path through vines.",
        tags={"dictionary", "animals", "adventure"},
    ),
}

OBSTACLES = {
    "misfiled_book": Obstacle(
        id="misfiled_book",
        label="misfiled book",
        scene="But when they reached the right shelf, there was a gap where the book should have been.",
        risk="The trail could not move on if they kept staring at the wrong place.",
        discover="The book had been shelved in the wrong section after another class used it.",
        solved_by={"catalog_search", "ask_librarian"},
        tags={"catalog", "shelves"},
    ),
    "high_shelf": Obstacle(
        id="high_shelf",
        label="high shelf",
        scene="They spotted the book at once, but it was resting on the very top shelf, far above their fingers.",
        risk="Reaching wildly would only make the problem bigger.",
        discover="The needed book was there all along, only too high to reach safely.",
        solved_by={"step_stool", "ask_librarian"},
        tags={"shelf", "safety"},
    ),
    "return_cart": Obstacle(
        id="return_cart",
        label="return cart",
        scene="The shelf looked tidy, yet the clue was nowhere inside the book they expected.",
        risk="If they guessed too fast, they would miss the real hiding place.",
        discover="The needed book was still waiting on the return cart, not back on the shelf yet.",
        solved_by={"cart_scan", "ask_librarian"},
        tags={"cart", "search"},
    ),
}

SOLUTIONS = {
    "catalog_search": Solution(
        id="catalog_search",
        label="catalog search",
        sense=3,
        helped=False,
        action="used the little library catalog screen to look the title up letter by letter",
        result="The screen pointed them to the correct section, and there the book waited where it did not belong.",
        qa_text="used the catalog screen to find where the book really was",
        tags={"catalog", "computer"},
    ),
    "step_stool": Solution(
        id="step_stool",
        label="step stool",
        sense=3,
        helped=False,
        action="rolled over the small step stool, held it steady, and climbed just high enough",
        result="From the top step, the book slipped safely into her hands.",
        qa_text="used the step stool safely to reach the high shelf",
        tags={"stool", "safety"},
    ),
    "cart_scan": Solution(
        id="cart_scan",
        label="cart scan",
        sense=3,
        helped=False,
        action="checked the return cart shelf by shelf instead of guessing",
        result="Tucked between two returned books, the missing title was waiting for them.",
        qa_text="searched the return cart carefully until they found the right book",
        tags={"cart", "search"},
    ),
    "ask_librarian": Solution(
        id="ask_librarian",
        label="ask librarian",
        sense=3,
        helped=True,
        action="walked to the desk and explained the clue to the librarian",
        result="The librarian smiled, followed the clue with them, and showed them exactly where to look.",
        qa_text="asked the librarian for help and followed the clue together",
        tags={"librarian", "help"},
    ),
    "climb_shelf": Solution(
        id="climb_shelf",
        label="climb shelf",
        sense=1,
        helped=False,
        action="started to climb the bookcase like a ladder",
        result="That would be unsafe in a library.",
        qa_text="tried to climb the shelf",
        unsafe=True,
        tags={"unsafe"},
    ),
    "random_guess": Solution(
        id="random_guess",
        label="random guess",
        sense=1,
        helped=False,
        action="pulled books at random and hoped one would be right",
        result="That would waste time and scatter the shelves.",
        qa_text="guessed without a real plan",
        unsafe=True,
        tags={"guessing"},
    ),
}


def valid_solution(obstacle_id: str, solution_id: str) -> bool:
    if obstacle_id not in OBSTACLES or solution_id not in SOLUTIONS:
        return False
    return solution_id in OBSTACLES[obstacle_id].solved_by and SOLUTIONS[solution_id].sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for solution_id in obstacle.solved_by:
                if valid_solution(obstacle_id, solution_id):
                    combos.append((mission_id, obstacle_id, solution_id))
    return sorted(combos)


def predict_success(world: World, solution_id: str) -> dict:
    sim = world.copy()
    if solution_id not in SOLUTIONS:
        return {"solved": False, "helped": False}
    if valid_solution(sim.facts["obstacle_obj"].id, solution_id):
        sim.get("problem").meters["solved"] += 1
        propagate(sim, narrate=False)
    return {
        "solved": sim.get("problem").meters["solved"] >= THRESHOLD,
        "helped": SOLUTIONS[solution_id].helped,
    }


def introduce(world: World, mission: Mission) -> None:
    sister = world.get("sister")
    sibling = world.get("sibling")
    world.say(
        f"After lunch, {sister.id} and {sibling.id} hurried into the school library. "
        f"{sister.id} was {sibling.id}'s sister, and the two of them felt as if they were stepping into a quiet castle of shelves."
    )
    world.say(
        f"The library smelled like paper and pencil shavings, and sun laid bright squares on the carpet. "
        f"They had not come to be ordinary readers today: {mission.intro}"
    )


def set_goal(world: World, mission: Mission) -> None:
    sister = world.get("sister")
    sibling = world.get("sibling")
    for kid_id in ("sister", "sibling"):
        world.get(kid_id).memes["joy"] += 1
        world.get(kid_id).memes["curiosity"] += 1
    world.say(
        f'"If we find {mission.object_label}," {sister.id} whispered, "we can earn {mission.goal}."'
    )
    world.say(
        f'{sibling.id} hugged the clue slip. "Then let\'s go on."'
    )


def hit_obstacle(world: World, obstacle: Obstacle) -> None:
    world.get("problem").meters["active"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.scene)
    world.say(obstacle.risk)


def sister_plans(world: World, obstacle: Obstacle) -> None:
    sister = world.get("sister")
    sibling = world.get("sibling")
    sister.memes["plan"] += 1
    propagate(world, narrate=False)
    calm_line = " Her voice stayed calm, and that made the puzzle feel smaller."
    if sister.attrs.get("trait") in {"steady", "careful"}:
        calm_line = " She spoke slowly and clearly, like someone laying stones across a stream."
    world.say(
        f'{sibling.id} looked worried, but {sister.id} touched the edge of the clue slip and said, '
        f'"This is still part of the adventure. We just need the next good step."{calm_line}'
    )
    world.facts["obstacle_discovery"] = obstacle.discover


def solve_problem(world: World, solution: Solution) -> None:
    world.facts["used_help"] = solution.helped
    world.say(
        f"So they {solution.action}."
    )
    world.say(solution.result)
    world.get("problem").meters["solved"] += 1
    propagate(world, narrate=False)


def ending(world: World, mission: Mission, solution: Solution) -> None:
    sister = world.get("sister")
    sibling = world.get("sibling")
    librarian = world.get("librarian")
    if solution.helped:
        world.say(
            f'"You solved it by asking a smart question," the {librarian.label_word} said. '
            f'"That is real adventuring too."'
        )
    else:
        world.say(
            f"{sibling.id} beamed at {sister.id}. "
            f'"You were right," {sibling.pronoun()} said. "A puzzle is easier when we think first."'
        )
    world.say(
        f"Inside {mission.object_label}, they found exactly what they needed. "
        f"{mission.ending}"
    )


def tell(
    mission: Mission,
    obstacle: Obstacle,
    solution: Solution,
    *,
    sister_name: str = "Maya",
    sibling_name: str = "Ben",
    sibling_gender: str = "boy",
    librarian_gender: str = "librarian_f",
    sister_trait: str = "steady",
) -> World:
    world = World()
    sister = world.add(Entity(
        id="sister",
        kind="character",
        type="girl",
        label=sister_name,
        role="sister",
        traits=[sister_trait],
        attrs={"trait": sister_trait, "display": sister_name},
    ))
    sibling = world.add(Entity(
        id="sibling",
        kind="character",
        type=sibling_gender,
        label=sibling_name,
        role="sibling",
        attrs={"display": sibling_name},
    ))
    librarian = world.add(Entity(
        id="librarian",
        kind="character",
        type=librarian_gender,
        label="the librarian",
        role="helper",
        attrs={"display": "the librarian"},
    ))
    problem = world.add(Entity(
        id="problem",
        kind="thing",
        type="problem",
        label=obstacle.label,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="clue slip",
    ))

    sister.id = sister_name
    sibling.id = sibling_name
    librarian.id = "Librarian"
    world.entities = {
        sister.id: sister,
        sibling.id: sibling,
        librarian.id: librarian,
        problem.id: problem,
        clue.id: clue,
    }

    world.facts["mission_obj"] = mission
    world.facts["obstacle_obj"] = obstacle
    world.facts["solution_obj"] = solution
    world.facts["used_help"] = False

    introduce(world, mission)
    set_goal(world, mission)

    world.para()
    hit_obstacle(world, obstacle)
    sister_plans(world, obstacle)

    prediction = predict_success(world, solution.id)
    world.facts["predicted_solved"] = prediction["solved"]

    world.para()
    solve_problem(world, solution)
    ending(world, mission, solution)

    world.facts.update(
        mission=mission,
        obstacle=obstacle,
        solution=solution,
        sister=sister,
        sibling=sibling,
        librarian=librarian,
        solved=world.get("problem").meters["solved"] >= THRESHOLD,
        clue_found=world.get("clue").meters["found"] >= THRESHOLD,
        outcome="helped" if solution.helped else "self_solved",
    )
    return world


KNOWLEDGE = {
    "catalog": [
        (
            "What is a library catalog?",
            "A library catalog is a list that helps you find where a book belongs. It can tell you the title, the section, and sometimes the shelf."
        )
    ],
    "librarian": [
        (
            "What does a librarian do?",
            "A librarian helps people find books, take care of the shelves, and keep the library organized. They are good helpers when you have a book problem."
        )
    ],
    "stool": [
        (
            "Why is a step stool safer than climbing a shelf?",
            "A step stool is made to help you reach something safely. A shelf can tip or make books fall, so it is not for climbing."
        )
    ],
    "search": [
        (
            "Why is it smart to search carefully instead of guessing?",
            "Searching carefully helps you notice clues and saves time. Guessing can make a bigger mess and still miss the right answer."
        )
    ],
    "library": [
        (
            "Why are books sorted in a library?",
            "Books are sorted so people can find them again. When books stay in the right place, everyone can share them more easily."
        )
    ],
    "teamwork": [
        (
            "How can teamwork help solve a problem?",
            "When people work together, one person can stay calm while another notices clues. Sharing ideas often makes the answer easier to find."
        )
    ],
}
KNOWLEDGE_ORDER = ["library", "catalog", "librarian", "stool", "search", "teamwork"]

SISTER_NAMES = ["Maya", "Lily", "Anna", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Max", "Finn", "Theo"]
GIRL_NAMES = ["Ava", "Mia", "Rose", "Lucy", "Ivy", "Emma"]
SISTER_TRAITS = ["steady", "careful", "clever", "brave"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sister = f["sister"]
    sibling = f["sibling"]
    mission = f["mission"]
    obstacle = f["obstacle"]
    solution = f["solution"]
    return [
        'Write a short adventure story for a 3-to-5-year-old set in a school library that includes the word "sister".',
        f"Tell a gentle school-library adventure where {sister.id} and {sibling.id} follow a clue for {mission.title}, but a {obstacle.label} blocks them until they solve the problem.",
        f"Write a child-friendly problem-solving story in a school library where a sister helps choose a smart next step, and the solution is {solution.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sister = f["sister"]
    sibling = f["sibling"]
    mission = f["mission"]
    obstacle = f["obstacle"]
    solution = f["solution"]
    librarian = f["librarian"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sister.id}, a sister, and {sibling.id}, her younger sibling. They are in the school library on a class adventure."
        ),
        (
            "What were they trying to find?",
            f"They were trying to find {mission.object_label}. They needed it so they could earn {mission.goal} and move their adventure forward."
        ),
        (
            "What problem stopped them?",
            f"The problem was {obstacle.label}. {obstacle.discover} That is why they could not simply take the next clue right away."
        ),
        (
            f"How did {sister.id} help when things went wrong?",
            f"{sister.id} stayed calm and told {sibling.id} that they needed the next good step. Her calm plan made the puzzle feel smaller, so the two of them could think instead of panic."
        ),
    ]
    if solution.helped:
        qa.append(
            (
                "How did they solve the problem?",
                f"They {solution.qa_text}. The librarian helped them follow the clue in a smart, orderly way, and that led them to the right book."
            )
        )
        qa.append(
            (
                "Why was asking for help a good idea?",
                f"Asking for help was a good idea because the librarian knew how the library was organized. That turned a confusing moment into a clear plan."
            )
        )
    else:
        qa.append(
            (
                "How did they solve the problem?",
                f"They {solution.qa_text}. Because they used a careful method instead of guessing, they found the book without making the library messy or unsafe."
            )
        )
        qa.append(
            (
                "What did they learn at the end?",
                f"They learned that a puzzle feels less scary when they slow down and think. Working together let them finish the adventure with pride."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They found what they needed inside the book and finished their school library adventure. The ending shows they changed from worried searchers into proud problem solvers."
        )
    )
    if solution.helped:
        qa.append(
            (
                f"What did the {librarian.label_word} say about their solving?",
                "The librarian said that asking a smart question is real adventuring too. That means good problem solving can include getting help from the right person."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"library", "teamwork"} | set(f["obstacle"].tags) | set(f["solution"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="dragon_map",
        obstacle="misfiled_book",
        solution="catalog_search",
        sister_name="Maya",
        sibling_name="Ben",
        sibling_gender="boy",
        librarian_gender="librarian_f",
        sister_trait="steady",
    ),
    StoryParams(
        mission="moon_key",
        obstacle="high_shelf",
        solution="step_stool",
        sister_name="Anna",
        sibling_name="Lucy",
        sibling_gender="girl",
        librarian_gender="librarian_m",
        sister_trait="careful",
    ),
    StoryParams(
        mission="jungle_riddle",
        obstacle="return_cart",
        solution="cart_scan",
        sister_name="Nora",
        sibling_name="Theo",
        sibling_gender="boy",
        librarian_gender="librarian_f",
        sister_trait="clever",
    ),
    StoryParams(
        mission="dragon_map",
        obstacle="high_shelf",
        solution="ask_librarian",
        sister_name="Ella",
        sibling_name="Mia",
        sibling_gender="girl",
        librarian_gender="librarian_f",
        sister_trait="brave",
    ),
]


def explain_invalid_solution(obstacle_id: str, solution_id: str) -> str:
    if solution_id not in SOLUTIONS:
        return f"(No story: unknown solution '{solution_id}'.)"
    sol = SOLUTIONS[solution_id]
    if sol.sense < SENSE_MIN:
        good = ", ".join(sorted(s for s in OBSTACLES[obstacle_id].solved_by if SOLUTIONS[s].sense >= SENSE_MIN))
        return (
            f"(No story: '{solution_id}' is not a sensible problem-solving move here. "
            f"Try one of these instead: {good}.)"
        )
    if solution_id not in OBSTACLES[obstacle_id].solved_by:
        return (
            f"(No story: '{solution_id}' does not fit the problem '{obstacle_id}'. "
            f"This world only allows solutions that really solve the library obstacle.)"
        )
    return "(No story: invalid problem and solution pairing.)"


def explain_invalid_combo(args: argparse.Namespace) -> str:
    return "(No valid combination matches the given options.)"


ASP_RULES = r"""
sensible_solution(S) :- solution(S), sense(S,N), sense_min(M), N >= M.
valid(M,O,S) :- mission(M), obstacle(O), allowed(O,S), sensible_solution(S).

helped_outcome(helped) :- chosen_solution(S), helper_solution(S).
helped_outcome(self_solved) :- chosen_solution(S), not helper_solution(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        for solution_id in sorted(obstacle.solved_by):
            lines.append(asp.fact("allowed", obstacle_id, solution_id))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        lines.append(asp.fact("sense", solution_id, solution.sense))
        if solution.helped:
            lines.append(asp.fact("helper_solution", solution_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_solution", params.solution)
    model = asp.one_model(asp_program(extra, "#show helped_outcome/1."))
    atoms = asp.atoms(model, "helped_outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.solution not in SOLUTIONS:
        return "?"
    return "helped" if SOLUTIONS[params.solution].helped else "self_solved"


def smoke_emit(sample: StorySample) -> str:
    parts = [sample.story]
    if sample.world is not None:
        parts.append(dump_trace(sample.world))
    parts.append(format_qa(sample))
    return "\n".join(parts)


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combos match ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random resolve at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        rendered = smoke_emit(sample)
        if not rendered.strip():
            raise StoryError("empty render from smoke test")
        print("OK: smoke test generated story, trace, and QA.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a sister leads a school-library problem-solving adventure."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--sister-name")
    ap.add_argument("--sibling-name")
    ap.add_argument("--sibling-gender", choices=["girl", "boy"])
    ap.add_argument("--librarian-gender", choices=["librarian_f", "librarian_m"])
    ap.add_argument("--sister-trait", choices=SISTER_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify Python/ASP parity and smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.solution:
        if not valid_solution(args.obstacle, args.solution):
            raise StoryError(explain_invalid_solution(args.obstacle, args.solution))
    if args.solution and args.obstacle is None:
        compatible = [oid for oid, ob in OBSTACLES.items() if args.solution in ob.solved_by and SOLUTIONS[args.solution].sense >= SENSE_MIN]
        if not compatible:
            raise StoryError(f"(No story: '{args.solution}' does not belong to any sensible obstacle here.)")

    combos = [
        combo for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        raise StoryError(explain_invalid_combo(args))

    mission_id, obstacle_id, solution_id = rng.choice(combos)
    sibling_gender = args.sibling_gender or rng.choice(["girl", "boy"])
    sister_name = args.sister_name or rng.choice(SISTER_NAMES)
    sibling_name = args.sibling_name or _pick_name(rng, sibling_gender, avoid=sister_name)
    if sibling_name == sister_name:
        choices = [n for n in (GIRL_NAMES if sibling_gender == "girl" else BOY_NAMES) if n != sister_name]
        if not choices:
            raise StoryError("(No story: could not choose distinct sibling names.)")
        sibling_name = rng.choice(choices)

    return StoryParams(
        mission=mission_id,
        obstacle=obstacle_id,
        solution=solution_id,
        sister_name=sister_name,
        sibling_name=sibling_name,
        sibling_gender=sibling_gender,
        librarian_gender=args.librarian_gender or rng.choice(["librarian_f", "librarian_m"]),
        sister_trait=args.sister_trait or rng.choice(SISTER_TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(No story: unknown mission '{params.mission}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(No story: unknown solution '{params.solution}'.)")
    if not valid_solution(params.obstacle, params.solution):
        raise StoryError(explain_invalid_solution(params.obstacle, params.solution))
    if params.sibling_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown sibling gender '{params.sibling_gender}'.)")
    if params.librarian_gender not in {"librarian_f", "librarian_m"}:
        raise StoryError(f"(No story: unknown librarian gender '{params.librarian_gender}'.)")
    if params.sister_trait not in set(SISTER_TRAITS):
        raise StoryError(f"(No story: unknown sister trait '{params.sister_trait}'.)")
    if params.sister_name == params.sibling_name:
        raise StoryError("(No story: the sister and sibling need different names.)")

    world = tell(
        MISSIONS[params.mission],
        OBSTACLES[params.obstacle],
        SOLUTIONS[params.solution],
        sister_name=params.sister_name,
        sibling_name=params.sibling_name,
        sibling_gender=params.sibling_gender,
        librarian_gender=params.librarian_gender,
        sister_trait=params.sister_trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible_solution/1.\n#show helped_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (mission, obstacle, solution) combos:\n")
        for mission_id, obstacle_id, solution_id in combos:
            print(f"  {mission_id:14} {obstacle_id:13} {solution_id}")
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
            header = f"### {p.sister_name} and {p.sibling_name}: {p.mission} / {p.obstacle} / {p.solution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
