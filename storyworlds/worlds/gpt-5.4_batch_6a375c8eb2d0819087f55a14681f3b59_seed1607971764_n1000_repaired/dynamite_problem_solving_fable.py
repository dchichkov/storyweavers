#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dynamite_problem_solving_fable.py
============================================================

A standalone storyworld for a small fable-like domain about **problem solving**.

Tiny source tale imagined from the seed
---------------------------------------
At the edge of a meadow, a boulder blocks a spring that waters the village
garden. A boastful young fox wants to use dynamite because it seems fast and
dramatic. A patient beaver points out that dynamite is dangerous near homes,
animals, and the water itself. Instead, the animals study the rock, dig a small
side trench to lower the pressure, wedge a branch under one edge, and roll the
stone aside together. The stream runs again, the garden drinks, and the young
fox learns that clever teamwork beats noisy force.

World model summary
-------------------
This world simulates:
- a community problem: a blocked spring / path / burrow gate
- a rash proposed tool: dynamite
- a wise helper's prediction of danger
- either an averted misuse or a repair by sensible tools and teamwork

It uses typed entities with physical ``meters`` and emotional ``memes``.
The rendered prose is driven by state and branch decisions, not noun swapping.

Run it
------
    python storyworlds/worlds/gpt-5.4/dynamite_problem_solving_fable.py
    python storyworlds/worlds/gpt-5.4/dynamite_problem_solving_fable.py --problem spring
    python storyworlds/worlds/gpt-5.4/dynamite_problem_solving_fable.py --approach leverage
    python storyworlds/worlds/gpt-5.4/dynamite_problem_solving_fable.py --site village
    python storyworlds/worlds/gpt-5.4/dynamite_problem_solving_fable.py --all
    python storyworlds/worlds/gpt-5.4/dynamite_problem_solving_fable.py --qa --json
    python storyworlds/worlds/gpt-5.4/dynamite_problem_solving_fable.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "ewe", "doe"}
        male = {"fox", "beaver", "badger", "mole", "crow", "hare"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Problem:
    id: str
    label: str
    opening: str
    blocked_thing: str
    need: str
    risk_if_blasted: str
    solved_image: str
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
class Site:
    id: str
    label: str
    place_phrase: str
    nearby_homes: bool
    near_water: bool
    echo: str
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
class Approach:
    id: str
    label: str
    sense: int
    power: int
    uses: tuple[str, ...]
    action: str
    image: str
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    plan = world.get("plan")
    if plan.meters["blast_planned"] < THRESHOLD:
        return out
    if plan.meters["danger"] >= THRESHOLD:
        return out
    sig = ("danger",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    site = world.get("site")
    obstacle = world.get("obstacle")
    plan.meters["danger"] += 1
    obstacle.meters["at_risk"] += 1
    if site.attrs.get("nearby_homes"):
        world.get("village").meters["at_risk"] += 1
    if site.attrs.get("near_water"):
        world.get("stream").meters["at_risk"] += 1
    for eid in ("solver", "helper"):
        world.get(eid).memes["worry"] += 1
    out.append("__danger__")
    return out


def _r_pressure(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    if obstacle.meters["blocked"] < THRESHOLD:
        return out
    if obstacle.meters["pressure"] >= THRESHOLD:
        return out
    sig = ("pressure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    obstacle.meters["pressure"] += 1
    world.get("village").meters["need"] += 1
    for eid in ("solver", "helper"):
        world.get(eid).memes["concern"] += 1
    out.append("__need__")
    return out


def _r_relieved(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    if obstacle.meters["moved"] < THRESHOLD:
        return out
    sig = ("relieved",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("village").meters["need"] = 0.0
    world.get("stream").meters["flowing"] = 1.0
    for eid in ("solver", "helper"):
        world.get(eid).memes["relief"] += 1
        world.get(eid).memes["pride"] += 1
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="pressure", tag="physical", apply=_r_pressure),
    Rule(name="danger", tag="safety", apply=_r_danger),
    Rule(name="relieved", tag="resolution", apply=_r_relieved),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def blast_is_unreasonable(problem: Problem, site: Site) -> bool:
    return site.nearby_homes or site.near_water or "fragile" in problem.tags


def sensible_approaches() -> list[Approach]:
    return [a for a in APPROACHES.values() if a.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for site_id, site in SITES.items():
        for problem_id, problem in PROBLEMS.items():
            if blast_is_unreasonable(problem, site):
                for approach_id, approach in APPROACHES.items():
                    if approach.sense >= SENSE_MIN:
                        combos.append((site_id, problem_id, approach_id))
    return sorted(combos)


def predict_blast(world: World) -> dict:
    sim = world.copy()
    sim.get("plan").meters["blast_planned"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("plan").meters["danger"] >= THRESHOLD,
        "village_at_risk": sim.get("village").meters["at_risk"] >= THRESHOLD,
        "stream_at_risk": sim.get("stream").meters["at_risk"] >= THRESHOLD,
    }


def introduce(world: World, solver: Entity, helper: Entity, site: Site, problem: Problem) -> None:
    world.say(
        f"In {site.place_phrase}, a young {solver.type} named {solver.id} and a patient "
        f"{helper.type} named {helper.id} watched a great stone trouble their neighbors."
    )
    world.say(problem.opening)
    world.say(
        f"Because of the stone, {problem.need}. Even the air seemed to wait, listening to {site.echo}."
    )


def boast(world: World, solver: Entity, site: Site) -> None:
    solver.memes["boldness"] += 1
    world.say(
        f'"Why push and puzzle over one old stone?" cried {solver.id}. '
        f'"A stick of dynamite would settle it in a blink."'
    )


def wise_warning(world: World, helper: Entity, solver: Entity, problem: Problem, site: Site) -> None:
    pred = predict_blast(world)
    world.facts["predicted_danger"] = pred
    helper.memes["care"] += 1
    extra = []
    if pred["village_at_risk"]:
        extra.append("the little homes nearby might crack or shake")
    if pred["stream_at_risk"]:
        extra.append("the spring itself might be spoiled with dirt and broken stone")
    tail = ""
    if extra:
        tail = " " + " and ".join(extra) + "."
    world.say(
        f'{helper.id} laid a paw on the stone and shook {helper.pronoun("possessive")} head. '
        f'"Dynamite is loud, quick, and wild," {helper.pronoun()} said. '
        f'"But this is {site.label}, not an empty quarry. If we blast here, {problem.risk_if_blasted}.{tail}"'
    )


def inspect(world: World, solver: Entity, helper: Entity, problem: Problem) -> None:
    solver.memes["thought"] += 1
    helper.memes["thought"] += 1
    world.say(
        f"So the two walked around the boulder. They noticed a narrow seam under one edge, "
        f"soft earth beside it, and a place where patient paws might work together."
    )
    if problem.id == "spring":
        world.say(
            "First they scratched a little side channel so the trapped water could sigh out and stop pressing so hard."
        )
        world.get("obstacle").meters["pressure"] = 0.0
    elif problem.id == "path":
        world.say(
            "First they brushed away the loose gravel around the stone, so they could see where it leaned and where it would roll."
        )
    else:
        world.say(
            "First they cleared the packed dirt around the gate rock, so the hidden lip of the stone showed itself."
        )


def solve_problem(world: World, solver: Entity, helper: Entity, approach: Approach, problem: Problem) -> None:
    obstacle = world.get("obstacle")
    obstacle.meters["moved"] += 1
    obstacle.meters["blocked"] = 0.0
    world.get("plan").meters["safe_plan"] += 1
    world.get("plan").attrs["uses"] = list(approach.uses)
    propagate(world, narrate=False)
    world.say(
        f'Then {helper.id} said, "Let us use our heads before our noise."'
    )
    world.say(
        f"Together they {approach.action}. Little by little, the stone answered patient work."
    )
    world.say(approach.image)
    world.say(problem.solved_image)


def learned(world: World, solver: Entity, helper: Entity) -> None:
    solver.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f'{solver.id} looked at the quiet place and said, "I thought the biggest sound would be the biggest wisdom."'
    )
    world.say(
        f'"No," said {helper.id}, smiling. "The best answer is the one that helps without harming."'
    )
    world.say(
        "And from that day on, whenever the meadow folk met a hard knot in life, they first studied it, then solved it together."
    )


def moral(world: World) -> None:
    world.say("Moral: Clever hands and calm minds do better work than reckless force.")


PROBLEMS = {
    "spring": Problem(
        id="spring",
        label="blocked spring",
        opening="A boulder had slid against the spring-mouth, and the water that fed the bean patch could only drip and mutter.",
        blocked_thing="spring-mouth",
        need="the bean patch drooped and the village jars stayed half-empty",
        risk_if_blasted="flying shards could wound the garden and frighten every creature nearby",
        solved_image="Soon the stream sang again, threading silver through the roots, and the thirsty beans lifted their leaves like small green flags.",
        tags={"water", "fragile", "garden"},
    ),
    "path": Problem(
        id="path",
        label="blocked path",
        opening="A fallen boulder lay across the hill path where carts and paws used to pass to market.",
        blocked_thing="hill path",
        need="old Badger could not wheel turnips to market and the smaller animals had to scramble through brambles",
        risk_if_blasted="stones would scatter down the hill and could strike the market road below",
        solved_image="By sunset the path lay open and kind again, and wheel tracks soon drew neat lines through the dust.",
        tags={"road", "fragile"},
    ),
    "burrow": Problem(
        id="burrow",
        label="burrow gate blocked",
        opening="A storm had rolled a heavy stone against the burrow gate where the field mice stored their winter grain.",
        blocked_thing="burrow gate",
        need="the mice could not reach their grain baskets before the next rain",
        risk_if_blasted="the shock could collapse the narrow tunnel and bury the grain deeper",
        solved_image="The burrow door opened wide, and the mice carried out dry golden kernels while the evening smelled of clean earth.",
        tags={"fragile", "home"},
    ),
}

SITES = {
    "village": Site(
        id="village",
        label="the village edge",
        place_phrase="a green meadow by the village edge",
        nearby_homes=True,
        near_water=True,
        echo="the faint clink of pails and the low talk of worried neighbors",
        tags={"village", "water"},
    ),
    "hillside": Site(
        id="hillside",
        label="the market hillside",
        place_phrase="a windy hillside above the market road",
        nearby_homes=False,
        near_water=False,
        echo="cart wheels far below and larks in the grass",
        tags={"road"},
    ),
    "orchard": Site(
        id="orchard",
        label="the old orchard",
        place_phrase="an old orchard with roots like curled fingers",
        nearby_homes=True,
        near_water=False,
        echo="bees at the clover and leaves whispering overhead",
        tags={"village", "orchard"},
    ),
}

APPROACHES = {
    "leverage": Approach(
        id="leverage",
        label="lever and wedge",
        sense=3,
        power=3,
        uses=("branch", "wedge", "teamwork"),
        action="pressed a long ash branch under the seam while the mice shoved flat wedges into the gap",
        image="At last the stone tipped with a deep, sleepy grunt and rolled onto a patch of moss where it could hurt no one.",
        qa_text="used a long branch as a lever and wedged the stone up little by little",
        tags={"lever", "teamwork"},
    ),
    "rollers": Approach(
        id="rollers",
        label="rollers and rope",
        sense=3,
        power=3,
        uses=("rollers", "rope", "teamwork"),
        action="slid round sticks beneath the boulder and pulled together with a braided vine rope",
        image="The boulder crept forward one patient finger-width at a time, then settled safely beside the track.",
        qa_text="put round sticks under the boulder and pulled it with a rope together",
        tags={"rollers", "teamwork"},
    ),
    "dig_and_lift": Approach(
        id="dig_and_lift",
        label="dig and lift",
        sense=2,
        power=2,
        uses=("shovels", "branch", "teamwork"),
        action="dug away the packed earth, packed stones under one side, and lifted in turns with a stout branch",
        image="When the earth finally gave a little, the rock lost its grip and slid aside into the fern bed.",
        qa_text="dug around the stone and lifted it in careful turns",
        tags={"digging", "teamwork"},
    ),
    "dynamite": Approach(
        id="dynamite",
        label="dynamite",
        sense=1,
        power=4,
        uses=("dynamite",),
        action="set dynamite beside the stone and ran for cover",
        image="The blast split the silence, but this world refuses to treat that as a wise answer here.",
        qa_text="tried to blast the stone with dynamite",
        tags={"dynamite", "explosion"},
    ),
}

FOX_NAMES = ["Felix", "Rufus", "Jory", "Pip", "Tarn"]
BEAVER_NAMES = ["Bram", "Hazel", "Moss", "Willow", "Otis"]
SOLVER_TRAITS = ["quick", "bright", "restless", "bold", "eager"]
HELPER_TRAITS = ["patient", "steady", "careful", "thoughtful", "calm"]


@dataclass
class StoryParams:
    site: str
    problem: str
    approach: str
    solver_name: str
    solver_type: str
    helper_name: str
    helper_type: str
    solver_trait: str
    helper_trait: str
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


KNOWLEDGE = {
    "dynamite": [
        (
            "What is dynamite?",
            "Dynamite is an explosive that can break rock with a blast. It is dangerous and must only be handled by trained grown-ups in proper places."
        )
    ],
    "lever": [
        (
            "What is a lever?",
            "A lever is a strong bar, like a branch or pole, that helps lift or move something heavy. It lets a small push do bigger work."
        )
    ],
    "rollers": [
        (
            "Why do round sticks help move a heavy rock?",
            "Round sticks can act like rollers under a heavy object. They help it turn and slide instead of scraping the ground the whole way."
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful for a hard job?",
            "Teamwork lets many helpers share the effort and notice different parts of the problem. That way the job becomes safer and smarter, not just stronger."
        )
    ],
    "digging": [
        (
            "Why would digging around a stone help?",
            "Digging can uncover the stone's edges and loosen the dirt that holds it tight. Once that grip is weaker, the stone is easier to move."
        )
    ],
    "water": [
        (
            "Why is clean spring water important?",
            "Clean spring water helps plants grow and gives animals something safe to drink. If the water is spoiled, the whole place can suffer."
        )
    ],
    "problem_solving": [
        (
            "What does it mean to solve a problem carefully?",
            "It means you look closely at what is wrong, think about what could happen next, and choose a fix that helps without causing new trouble."
        )
    ],
}

KNOWLEDGE_ORDER = ["problem_solving", "dynamite", "lever", "rollers", "digging", "teamwork", "water"]


CURATED = [
    StoryParams(
        site="village",
        problem="spring",
        approach="leverage",
        solver_name="Felix",
        solver_type="fox",
        helper_name="Bram",
        helper_type="beaver",
        solver_trait="bold",
        helper_trait="patient",
        seed=101,
    ),
    StoryParams(
        site="hillside",
        problem="path",
        approach="rollers",
        solver_name="Pip",
        solver_type="fox",
        helper_name="Moss",
        helper_type="beaver",
        solver_trait="quick",
        helper_trait="steady",
        seed=102,
    ),
    StoryParams(
        site="orchard",
        problem="burrow",
        approach="dig_and_lift",
        solver_name="Rufus",
        solver_type="fox",
        helper_name="Hazel",
        helper_type="beaver",
        solver_trait="eager",
        helper_trait="thoughtful",
        seed=103,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    solver = f["solver"]
    helper = f["helper"]
    problem = f["problem_cfg"]
    approach = f["approach_cfg"]
    return [
        'Write a short fable for a 3-to-5-year-old about problem solving that includes the word "dynamite".',
        f"Tell a gentle animal fable where {solver.id} first wants to use dynamite to fix a {problem.label}, but {helper.id} helps solve it another way.",
        f"Write a meadow fable in which a hard problem is solved by {approach.label} and teamwork instead of reckless force.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    solver = f["solver"]
    helper = f["helper"]
    problem = f["problem_cfg"]
    site = f["site_cfg"]
    approach = f["approach_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {solver.id} the {solver.type} and {helper.id} the {helper.type}. They were trying to solve a {problem.label} in {site.label}."
        ),
        (
            "What was the problem?",
            f"The problem was that a great stone blocked the {problem.blocked_thing}. Because of that, {problem.need}."
        ),
        (
            f"Why did {helper.id} say dynamite was a bad idea?",
            f"{helper.id} warned that dynamite was too wild for that place. {problem.risk_if_blasted.capitalize()}, so a quick blast could have caused new harm instead of solving the first problem."
        ),
        (
            "How did they solve the problem in the end?",
            f"They solved it by studying the stone first and then {approach.qa_text}. That careful plan worked because it moved the boulder without hurting the homes, water, or tunnels nearby."
        ),
        (
            f"What did {solver.id} learn?",
            f"{solver.id} learned that the loudest answer is not always the wisest one. Careful thinking and teamwork solved the trouble better than dynamite would have."
        ),
    ]
    if f.get("predicted_danger", {}).get("stream_at_risk"):
        qa.append(
            (
                "Why did the spring matter so much?",
                "The spring mattered because the animals and plants depended on it. If the blast had spoiled the water, the problem would have spread beyond the stone itself."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"problem_solving", "dynamite"} | set(f["approach_cfg"].tags) | set(f["problem_cfg"].tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
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
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, site: Site, approach: Approach) -> str:
    if approach.id == "dynamite":
        return (
            f"(No story: dynamite is not a wise answer for {problem.label} at {site.label}. "
            f"{problem.risk_if_blasted.capitalize()}, so this world requires a safer problem-solving method.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def tell(
    site: Site,
    problem: Problem,
    approach: Approach,
    solver_name: str,
    solver_type: str,
    helper_name: str,
    helper_type: str,
    solver_trait: str,
    helper_trait: str,
) -> World:
    world = World()
    solver = world.add(
        Entity(
            id=solver_name,
            kind="character",
            type=solver_type,
            label=solver_name,
            role="solver",
            traits=[solver_trait],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            label=helper_name,
            role="helper",
            traits=[helper_trait],
        )
    )
    world.add(Entity(id="obstacle", type="boulder", label="boulder"))
    world.add(
        Entity(
            id="site",
            type="place",
            label=site.label,
            attrs={"nearby_homes": site.nearby_homes, "near_water": site.near_water},
        )
    )
    world.add(Entity(id="stream", type="spring", label="spring"))
    world.add(Entity(id="village", type="village", label="village"))
    world.add(Entity(id="plan", type="plan", label="plan", attrs={"uses": []}))

    world.get("obstacle").meters["blocked"] = 1.0
    world.get("stream").meters["flowing"] = 0.0
    propagate(world, narrate=False)

    introduce(world, solver, helper, site, problem)
    world.para()
    boast(world, solver, site)
    world.get("plan").meters["blast_planned"] += 1
    propagate(world, narrate=False)
    wise_warning(world, helper, solver, problem, site)

    world.para()
    inspect(world, solver, helper, problem)
    world.get("plan").meters["blast_planned"] = 0.0
    world.get("plan").meters["danger"] = 0.0
    solve_problem(world, solver, helper, approach, problem)

    world.para()
    learned(world, solver, helper)
    moral(world)

    world.facts.update(
        solver=solver,
        helper=helper,
        site_cfg=site,
        problem_cfg=problem,
        approach_cfg=approach,
        outcome="solved",
        used_dynamite=False,
        solved=world.get("obstacle").meters["moved"] >= THRESHOLD,
    )
    return world


ASP_RULES = r"""
reasonable_site_problem(S, P) :- site(S), problem(P), risky_with_dynamite(S, P).
sensible(A) :- approach(A), sense(A, V), sense_min(M), V >= M.
valid(S, P, A) :- reasonable_site_problem(S, P), sensible(A).

risky_with_dynamite(S, P) :- nearby_homes(S).
risky_with_dynamite(S, P) :- near_water(S).
risky_with_dynamite(S, P) :- fragile_problem(P).

#show valid/3.
#show sensible/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        if site.nearby_homes:
            lines.append(asp.fact("nearby_homes", site_id))
        if site.near_water:
            lines.append(asp.fact("near_water", site_id))
    for problem_id, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", problem_id))
        if "fragile" in problem.tags:
            lines.append(asp.fact("fragile_problem", problem_id))
    for approach_id, approach in APPROACHES.items():
        lines.append(asp.fact("approach", approach_id))
        lines.append(asp.fact("sense", approach_id, approach.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(a for (a,) in asp.atoms(model, "sensible"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fable about problem solving, dynamite, and wiser solutions."
    )
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.problem and args.approach:
        site = SITES[args.site]
        problem = PROBLEMS[args.problem]
        approach = APPROACHES[args.approach]
        if (args.site, args.problem, args.approach) not in valid_combos():
            raise StoryError(explain_rejection(problem, site, approach))

    combos = [
        combo
        for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.problem is None or combo[1] == args.problem)
        and (args.approach is None or combo[2] == args.approach)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, problem_id, approach_id = rng.choice(sorted(combos))
    solver_name = rng.choice(FOX_NAMES)
    helper_name = rng.choice([n for n in BEAVER_NAMES if n != solver_name])
    return StoryParams(
        site=site_id,
        problem=problem_id,
        approach=approach_id,
        solver_name=solver_name,
        solver_type="fox",
        helper_name=helper_name,
        helper_type="beaver",
        solver_trait=rng.choice(SOLVER_TRAITS),
        helper_trait=rng.choice(HELPER_TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES:
        raise StoryError(f"(Unknown site: {params.site})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.approach not in APPROACHES:
        raise StoryError(f"(Unknown approach: {params.approach})")

    site = SITES[params.site]
    problem = PROBLEMS[params.problem]
    approach = APPROACHES[params.approach]
    if (params.site, params.problem, params.approach) not in valid_combos():
        raise StoryError(explain_rejection(problem, site, approach))

    world = tell(
        site=site,
        problem=problem,
        approach=approach,
        solver_name=params.solver_name,
        solver_type=params.solver_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        solver_trait=params.solver_trait,
        helper_trait=params.helper_trait,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {a.id for a in sensible_approaches()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible approaches match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible approaches:")
        print("  python:", sorted(py_sensible))
        print("  clingo:", sorted(asp_sens))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        if "dynamite" not in sample.story.lower():
            raise StoryError("smoke test story omitted required word 'dynamite'")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible approaches: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (site, problem, approach) combos:\n")
        for site, problem, approach in combos:
            print(f"  {site:9} {problem:8} {approach}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.solver_name} and {p.helper_name}: {p.problem} at {p.site} ({p.approach})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
