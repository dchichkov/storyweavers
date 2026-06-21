#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py
============================================================================

A standalone story world for a small folk-tale domain: a child sets out on an
errand, the way is blocked, and a thrush gives a surprising clue that helps the
child solve the problem sensibly.

The world is intentionally narrow and constraint-driven. A story is only made
when the obstacle, the thrush's clue, and the solution truly fit one another.
The prose is driven from simulated state: worry rises when the way is blocked,
hope returns when the clue is understood, and the ending image shows how the
traveler has changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py
    python storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py --obstacle stream
    python storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py --solution hidden_gate
    python storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py --trace
    python storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py --asp
    python storyworlds/worlds/gpt-5.4/way_thrush_surprise_problem_solving_folk_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        bird = {"bird", "thrush"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in bird:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
class Errand:
    id: str
    gift: str
    vessel: str
    elder_place: str
    opening: str
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
    article: str
    scene: str
    failed_try: str
    risk: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
class Clue:
    id: str
    action: str
    line: str
    reveals: str
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
    tool: str
    action: str
    success: str
    qa_text: str
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

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
    traveler = world.entities.get("traveler")
    obstacle = world.entities.get("obstacle")
    if traveler is None or obstacle is None:
        return []
    if obstacle.meters["blocking"] < THRESHOLD:
        return []
    if traveler.meters["stopped"] < THRESHOLD:
        return []
    sig = ("blocked_worry", traveler.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    traveler.memes["worry"] += 1
    traveler.memes["patience"] += 1
    world.get("way").meters["blocked"] += 1
    return ["__blocked__"]


def _r_clue_hope(world: World) -> list[str]:
    traveler = world.entities.get("traveler")
    thrush = world.entities.get("thrush")
    if traveler is None or thrush is None:
        return []
    if thrush.meters["clue_given"] < THRESHOLD:
        return []
    sig = ("clue_hope", traveler.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    traveler.memes["wonder"] += 1
    traveler.memes["hope"] += 1
    return ["__clue__"]


def _r_solved_relief(world: World) -> list[str]:
    traveler = world.entities.get("traveler")
    obstacle = world.entities.get("obstacle")
    if traveler is None or obstacle is None:
        return []
    if obstacle.meters["cleared"] < THRESHOLD and traveler.meters["crossed"] < THRESHOLD:
        return []
    sig = ("solved_relief", traveler.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    traveler.memes["relief"] += 1
    traveler.memes["gratitude"] += 1
    world.get("way").meters["open"] += 1
    return ["__solved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="blocked_worry", tag="emotion", apply=_r_blocked_worry),
    Rule(name="clue_hope", tag="emotion", apply=_r_clue_hope),
    Rule(name="solved_relief", tag="emotion", apply=_r_solved_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def compatible(obstacle: Obstacle, clue: Clue, solution: Solution) -> bool:
    return obstacle.id == clue.reveals == solution.id


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for errand_id in ERRANDS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for clue_id, clue in CLUES.items():
                for solution_id, solution in SOLUTIONS.items():
                    if compatible(obstacle, clue, solution):
                        combos.append((errand_id, obstacle_id, clue_id, solution_id))
    return combos


@dataclass
class StoryParams:
    errand: str
    obstacle: str
    clue: str
    solution: str
    traveler_name: str
    traveler_gender: str
    elder: str
    trait: str
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


ERRANDS = {
    "bread": Errand(
        id="bread",
        gift="a round loaf of brown bread",
        vessel="a willow basket",
        elder_place="her grandmother's cottage beyond the birches",
        opening="Before the dew had left the grass,",
        ending="At supper, they broke the brown loaf and left a warm crust on the sill for the bird.",
        tags={"bread", "cottage"},
    ),
    "soup": Errand(
        id="soup",
        gift="a little pot of onion soup wrapped in cloth",
        vessel="a clay pot hugged in both arms",
        elder_place="his grandfather's cottage at the edge of the pine wood",
        opening="On a pale morning,",
        ending="That evening, they set the empty pot by the door and scattered crumbs beneath the rowan tree for the bird.",
        tags={"soup", "cottage"},
    ),
    "seeds": Errand(
        id="seeds",
        gift="a pouch of barley seed",
        vessel="a small linen sack",
        elder_place="their aunt's garden house past the meadow",
        opening="When the first light lay on the field,",
        ending="Later, they poured a few barley seeds on the step, and the bird came hopping back like a small brown thank-you.",
        tags={"seed", "garden"},
    ),
}

OBSTACLES = {
    "stream": Obstacle(
        id="stream",
        label="stream",
        article="a",
        scene="a cold stream had run over the way, silver and quick between the roots",
        failed_try="The traveler thought of jumping it in one leap, but the bank was slick and the water snapped at the shoes",
        risk="getting wet and being swept into the cold water",
        tags={"stream", "water"},
    ),
    "thorn_hedge": Obstacle(
        id="thorn_hedge",
        label="thorn hedge",
        article="a",
        scene="a thorn hedge had grown across the way, woven so tightly that even sunlight had trouble slipping through",
        failed_try="The traveler pushed at the branches, but the thorns caught at sleeves and pricked the fingers",
        risk="being scratched by the thorns",
        tags={"thorns", "hedge"},
    ),
    "fallen_tree": Obstacle(
        id="fallen_tree",
        label="fallen tree",
        article="a",
        scene="a fallen tree lay across the way, broad as a gate and heavy as sleep",
        failed_try="The traveler braced both hands against the trunk, but it would not roll even a finger-width",
        risk="straining too hard against something too heavy",
        tags={"tree", "wood"},
    ),
}

CLUES = {
    "stone_song": Clue(
        id="stone_song",
        action="hopped onto three flat stones and pecked them one by one",
        line='Then a thrush flew down and sang from the middle of the water, as if saying, "Look where the river forgets to be deep."',
        reveals="stream",
        tags={"thrush", "stones"},
    ),
    "vine_latch": Clue(
        id="vine_latch",
        action="tugged at a hanging vine until a little wooden latch showed beneath the leaves",
        line='Just then a thrush landed on the hedge and gave a bright quick call, as if saying, "Not every wall is truly a wall."',
        reveals="thorn_hedge",
        tags={"thrush", "gate"},
    ),
    "pole_tap": Clue(
        id="pole_tap",
        action="struck a long fence pole with its beak until the pole tipped down from the grass",
        line='A thrush burst from the ditch-side grass and chirred so sharply that the sound felt like a thought becoming clear.',
        reveals="fallen_tree",
        tags={"thrush", "pole"},
    ),
}

SOLUTIONS = {
    "stream": Solution(
        id="stream",
        tool="flat stepping stones",
        action="cross",
        success="used the flat stones like a tiny bridge and crossed dry-footed",
        qa_text="crossed on flat stepping stones",
        tags={"stones", "crossing"},
    ),
    "thorn_hedge": Solution(
        id="thorn_hedge",
        tool="a hidden wicket gate",
        action="open",
        success="lifted the little latch, opened the hidden gate, and slipped through without a single tear in the cloth",
        qa_text="opened the hidden gate in the hedge",
        tags={"gate", "hedge"},
    ),
    "fallen_tree": Solution(
        id="fallen_tree",
        tool="a long fence pole",
        action="lever",
        success="set the long pole under the trunk and levered it just far enough to make a narrow safe passage",
        qa_text="used a long pole as a lever to shift the trunk",
        tags={"lever", "wood"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Anya", "Tessa", "Nell", "Ivy", "Rosa", "Bela"]
BOY_NAMES = ["Tarin", "Milo", "Pavel", "Ilan", "Sorin", "Nico", "Bram", "Oren"]
TRAITS = ["patient", "careful", "kind", "steady", "curious", "thoughtful"]


def introduce(world: World, traveler: Entity, elder: Entity, errand: Errand) -> None:
    world.say(
        f"{errand.opening} {traveler.id} set out with {errand.gift} in {errand.vessel}, "
        f"walking toward {elder.label}. In the old stories of that valley, every kind heart "
        f"kept to the way and every errand mattered."
    )
    world.say(
        f"{traveler.id} was {traveler.attrs['trait']}, and so {traveler.pronoun()} walked carefully, "
        f"for what was being carried was meant for an elder who was waiting."
    )


def meet_obstacle(world: World, traveler: Entity, obstacle_cfg: Obstacle) -> None:
    obstacle = world.get("obstacle")
    obstacle.meters["blocking"] = 1.0
    traveler.meters["stopped"] = 1.0
    propagate(world, narrate=False)
    worry = ""
    if traveler.memes["worry"] >= THRESHOLD:
        worry = f" {traveler.id}'s heart gave one small worried thump."
    world.say(
        f"But halfway there, {obstacle_cfg.scene}. {obstacle_cfg.failed_try}.{worry}"
    )
    world.facts["risk"] = obstacle_cfg.risk


def puzzle_over(world: World, traveler: Entity, errand: Errand) -> None:
    traveler.memes["duty"] += 1
    world.say(
        f'"If I turn back, {traveler.pronoun("possessive")} errand will fail," '
        f"{traveler.id} said softly. {traveler.pronoun().capitalize()} stood still instead of rushing, "
        f"because hurrying at a hard problem often makes the hard part harder."
    )


def thrush_appears(world: World, thrush: Entity, clue: Clue) -> None:
    thrush.meters["clue_given"] = 1.0
    propagate(world, narrate=False)
    world.say(clue.line)
    world.say(
        f"The little thrush {clue.action}. It was a surprising thing to see, "
        f"and suddenly the bird's fuss no longer seemed like noise at all."
    )


def understand_clue(world: World, traveler: Entity, obstacle_cfg: Obstacle, solution: Solution) -> None:
    traveler.memes["insight"] += 1
    if obstacle_cfg.id == "stream":
        insight = "The traveler saw that the bird was not singing to the water, but to the stones hidden in it."
    elif obstacle_cfg.id == "thorn_hedge":
        insight = "The traveler saw that the hedge was guarding a door, not merely blocking the road."
    else:
        insight = "The traveler saw that what was too heavy for bare hands might still yield to a wiser tool."
    world.say(
        f"{insight} That was the way through: not magic, only careful looking."
    )


def solve(world: World, traveler: Entity, obstacle_cfg: Obstacle, solution: Solution) -> None:
    obstacle = world.get("obstacle")
    obstacle.meters["cleared"] = 1.0
    traveler.meters["crossed"] = 1.0
    if obstacle_cfg.id == "stream":
        traveler.meters["dry"] = 1.0
    if obstacle_cfg.id == "thorn_hedge":
        traveler.meters["unhurt"] = 1.0
    if obstacle_cfg.id == "fallen_tree":
        traveler.meters["safe_passage"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"So {traveler.id} {solution.success}."
    )


def arrive(world: World, traveler: Entity, elder: Entity, errand: Errand) -> None:
    traveler.meters["arrived"] = 1.0
    world.say(
        f"By and by, {traveler.id} came to {elder.label}, and the gift was delivered warm and whole. "
        f"{elder.label.split()[0].capitalize()} listened to the tale, smiled, and said that a quiet eye can be wiser than a quick foot."
    )


def thanks(world: World, traveler: Entity, thrush: Entity, errand: Errand) -> None:
    traveler.memes["gratitude"] += 1
    traveler.memes["wonder"] += 1
    world.say(
        f"Before going in, {traveler.id} looked back along the way. The thrush was there for one blink of an eye upon a branch, "
        f"and then it was gone, as if the wood itself had borrowed a voice for a moment."
    )
    world.say(errand.ending)


def tell(
    errand: Errand,
    obstacle_cfg: Obstacle,
    clue: Clue,
    solution: Solution,
    traveler_name: str = "Mira",
    traveler_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "patient",
) -> World:
    world = World()
    traveler = world.add(
        Entity(
            id="traveler",
            kind="character",
            type=traveler_gender,
            label=traveler_name,
            role="traveler",
            attrs={"trait": trait},
        )
    )
    elder_word = "grandmother" if elder_type == "grandmother" else "grandfather"
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type="woman" if elder_type == "grandmother" else "man",
            label=f"{traveler.pronoun('possessive')} {elder_word}'s cottage",
            role="elder",
            attrs={"kin": elder_word},
        )
    )
    thrush = world.add(
        Entity(
            id="thrush",
            kind="character",
            type="thrush",
            label="the thrush",
            role="helper",
            attrs={"birdsong": "bright"},
        )
    )
    world.add(Entity(id="way", type="path", label="the way", role="path"))
    obstacle = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle_cfg.label,
            role="obstacle",
        )
    )

    traveler.memes["worry"] = 0.0
    traveler.memes["hope"] = 0.0
    traveler.memes["wonder"] = 0.0
    traveler.memes["gratitude"] = 0.0
    traveler.memes["insight"] = 0.0
    traveler.memes["patience"] = 0.0
    traveler.meters["stopped"] = 0.0
    traveler.meters["crossed"] = 0.0
    obstacle.meters["blocking"] = 0.0
    obstacle.meters["cleared"] = 0.0
    thrush.meters["clue_given"] = 0.0
    world.get("way").meters["blocked"] = 0.0
    world.get("way").meters["open"] = 0.0

    world.facts.update(
        errand=errand,
        obstacle_cfg=obstacle_cfg,
        clue=clue,
        solution=solution,
        traveler=traveler,
        traveler_name=traveler_name,
        elder=elder,
        thrush=thrush,
        risk=obstacle_cfg.risk,
    )

    introduce(world, traveler, elder, errand)
    world.para()
    meet_obstacle(world, traveler, obstacle_cfg)
    puzzle_over(world, traveler, errand)
    world.para()
    thrush_appears(world, thrush, clue)
    understand_clue(world, traveler, obstacle_cfg, solution)
    world.para()
    solve(world, traveler, obstacle_cfg, solution)
    arrive(world, traveler, elder, errand)
    world.para()
    thanks(world, traveler, thrush, errand)

    world.facts.update(
        solved=traveler.meters["crossed"] >= THRESHOLD,
        surprise=thrush.meters["clue_given"] >= THRESHOLD,
        arrived=traveler.meters["arrived"] >= THRESHOLD,
    )
    return world


def explain_rejection(obstacle_id: str, clue_id: str, solution_id: str) -> str:
    obstacle = OBSTACLES.get(obstacle_id)
    clue = CLUES.get(clue_id)
    solution = SOLUTIONS.get(solution_id)
    if obstacle is None or clue is None or solution is None:
        return "(No story: one of the requested options is unknown.)"
    return (
        f"(No story: {obstacle.the} is not honestly solved by clue '{clue_id}' and solution "
        f"'{solution_id}'. The thrush's surprise must point to a real way through the problem.)"
    )


KNOWLEDGE = {
    "thrush": [
        (
            "What is a thrush?",
            "A thrush is a small brown songbird. It is known for bright clear singing and for hopping along the ground to look for food.",
        )
    ],
    "stream": [
        (
            "Why can a stream be hard to cross?",
            "A stream can be slippery, cold, and fast. Even a small one can make you fall if you rush.",
        )
    ],
    "stones": [
        (
            "What are stepping stones for?",
            "Stepping stones make a dry path across shallow water. You place your feet on the firm stones instead of in the stream.",
        )
    ],
    "thorns": [
        (
            "Why should you be careful around thorns?",
            "Thorns are sharp parts of some plants. They can scratch your skin or catch on your clothes.",
        )
    ],
    "gate": [
        (
            "What is a wicket gate?",
            "A wicket gate is a small door in a fence or hedge. It gives people a neat safe way through.",
        )
    ],
    "tree": [
        (
            "Why is a fallen tree hard to move?",
            "A fallen tree is heavy and awkward. Pushing with bare hands may not work because the weight is spread along the whole trunk.",
        )
    ],
    "lever": [
        (
            "What does a lever do?",
            "A lever helps you move something heavy by using a long sturdy stick. It lets careful force do more than bare hands alone.",
        )
    ],
    "problem_solving": [
        (
            "How can stopping to look help solve a problem?",
            "When you stop and look, you notice useful details you might miss while hurrying. A good idea often comes from seeing the problem in a new way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["thrush", "stream", "stones", "thorns", "gate", "tree", "lever", "problem_solving"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obstacle = f["obstacle_cfg"]
    return [
        'Write a short folk tale for a young child that includes the words "way" and "thrush".',
        f"Tell a folk-style story where a child on an errand finds {obstacle.article} {obstacle.label} across the way, and a thrush gives a surprising clue that helps solve the problem.",
        "Write a gentle surprise-and-problem-solving tale in which careful looking matters more than rushing, and end with a thankful image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    traveler = f["traveler"]
    errand = f["errand"]
    obstacle = f["obstacle_cfg"]
    solution = f["solution"]
    elder = f["elder"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {traveler.label}, who was carrying {errand.gift} along the way to {errand.elder_place}. The story is also about the thrush whose clue helped at the hardest moment.",
        ),
        (
            "What problem did the traveler meet on the way?",
            f"The traveler found {obstacle.article} {obstacle.label} blocking the way. That mattered because it could stop the errand and also carried the risk of {f['risk']}.",
        ),
        (
            "Why did the traveler not simply rush ahead?",
            f"The traveler first saw that hurrying would be unsafe and might spoil the errand. So {traveler.pronoun()} stopped to think instead of turning worry into a bigger problem.",
        ),
        (
            "What surprising thing did the thrush do?",
            f"The thrush gave a surprising clue by the way it moved and sang. The bird's fuss looked ordinary at first, but it was really pointing out the answer hidden in plain sight.",
        ),
        (
            "How was the problem solved?",
            f"The traveler {solution.qa_text}. The clue worked because it matched the obstacle instead of offering random help.",
        ),
        (
            "How did the story end?",
            f"The traveler reached {elder.label} with the gift still safe. At the end, gratitude replaced worry, and a small kindness was left for the thrush.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["obstacle_cfg"].tags) | set(f["solution"].tags) | {"problem_solving"}
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(O,C,S) :- obstacle(O), clue(C), solution(S),
                     reveals(C,O), solves(S,O).

valid(E,O,C,S) :- errand(E), compatible(O,C,S).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for errand_id in ERRANDS:
        lines.append(asp.fact("errand", errand_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("reveals", clue_id, clue.reveals))
    for solution_id in SOLUTIONS:
        lines.append(asp.fact("solution", solution_id))
        lines.append(asp.fact("solves", solution_id, solution_id))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        errand="bread",
        obstacle="stream",
        clue="stone_song",
        solution="stream",
        traveler_name="Mira",
        traveler_gender="girl",
        elder="grandmother",
        trait="patient",
    ),
    StoryParams(
        errand="soup",
        obstacle="thorn_hedge",
        clue="vine_latch",
        solution="thorn_hedge",
        traveler_name="Milo",
        traveler_gender="boy",
        elder="grandfather",
        trait="careful",
    ),
    StoryParams(
        errand="seeds",
        obstacle="fallen_tree",
        clue="pole_tap",
        solution="fallen_tree",
        traveler_name="Anya",
        traveler_gender="girl",
        elder="grandmother",
        trait="thoughtful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: a blocked way, a thrush's surprising clue, and a child who solves the problem."
    )
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--traveler-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible stories derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.clue and args.solution:
        if not compatible(OBSTACLES[args.obstacle], CLUES[args.clue], SOLUTIONS[args.solution]):
            raise StoryError(explain_rejection(args.obstacle, args.clue, args.solution))

    combos = [
        combo
        for combo in valid_combos()
        if (args.errand is None or combo[0] == args.errand)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.clue is None or combo[2] == args.clue)
        and (args.solution is None or combo[3] == args.solution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    errand_id, obstacle_id, clue_id, solution_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    traveler_name = args.traveler_name or rng.choice(name_pool)
    elder = args.elder or ("grandmother" if rng.random() < 0.5 else "grandfather")
    trait = rng.choice(TRAITS)
    return StoryParams(
        errand=errand_id,
        obstacle=obstacle_id,
        clue=clue_id,
        solution=solution_id,
        traveler_name=traveler_name,
        traveler_gender=gender,
        elder=elder,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.errand not in ERRANDS:
        raise StoryError(f"(No story: unknown errand '{params.errand}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(No story: unknown solution '{params.solution}'.)")
    errand = ERRANDS[params.errand]
    obstacle = OBSTACLES[params.obstacle]
    clue = CLUES[params.clue]
    solution = SOLUTIONS[params.solution]
    if not compatible(obstacle, clue, solution):
        raise StoryError(explain_rejection(params.obstacle, params.clue, params.solution))

    world = tell(
        errand=errand,
        obstacle_cfg=obstacle,
        clue=clue,
        solution=solution,
        traveler_name=params.traveler_name,
        traveler_gender=params.traveler_gender,
        elder_type=params.elder,
        trait=params.trait,
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
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: clingo gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "thrush" not in sample.story.lower() or "way" not in sample.story.lower():
            raise StoryError("smoke test story missing required story content")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story:
            raise StoryError("default resolved generation produced empty story")
        print("OK: default resolve/generate smoke test succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (errand, obstacle, clue, solution) combos:\n")
        for errand_id, obstacle_id, clue_id, solution_id in combos:
            print(f"  {errand_id:6} {obstacle_id:12} {clue_id:11} {solution_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.traveler_name}: {p.errand}, {p.obstacle}, {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
