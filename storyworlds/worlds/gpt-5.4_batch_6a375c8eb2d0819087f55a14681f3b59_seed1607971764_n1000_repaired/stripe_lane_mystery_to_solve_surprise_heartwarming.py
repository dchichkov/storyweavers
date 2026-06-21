#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stripe_lane_mystery_to_solve_surprise_heartwarming.py
=================================================================================

A standalone story world about a child who builds a little play lane, notices a
missing stripe, follows a clue, and discovers a warm surprise.

The domain is intentionally small and constraint-checked: a stripe item must be
the sort of thing a grown-up could honestly borrow for a craft surprise, and the
chosen clue must truly point to the place where that surprise is being made.
The story always forms a complete arc:

- premise: a cheerful lane-making game
- tension: one stripe is missing, so the lane is unfinished
- turn: the child follows a grounded clue instead of blaming someone
- resolution: the mystery is solved, and the missing stripe becomes part of a
  heartwarming surprise

Run it
------
    python storyworlds/worlds/gpt-5.4/stripe_lane_mystery_to_solve_surprise_heartwarming.py
    python storyworlds/worlds/gpt-5.4/stripe_lane_mystery_to_solve_surprise_heartwarming.py --lane scooter --stripe ribbon
    python storyworlds/worlds/gpt-5.4/stripe_lane_mystery_to_solve_surprise_heartwarming.py --surprise cape
    python storyworlds/worlds/gpt-5.4/stripe_lane_mystery_to_solve_surprise_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/stripe_lane_mystery_to_solve_surprise_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/stripe_lane_mystery_to_solve_surprise_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
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
class Lane:
    id: str
    place: str
    play: str
    mover: str
    finish: str
    floor_detail: str
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
class StripeItem:
    id: str
    label: str
    phrase: str
    texture: str
    finish_role: str
    can_make: set[str] = field(default_factory=set)
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
class Clue:
    id: str
    label: str
    phrase: str
    place: str
    detail: str
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
class Surprise:
    id: str
    label: str
    article: str
    place: str
    making: str
    reveal: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_missing_lane(world: World) -> list[str]:
    lane = world.get("lane")
    stripe = world.get("stripe")
    seeker = world.get("seeker")
    helper = world.get("helper")
    if stripe.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_lane",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lane.meters["unfinished"] += 1
    seeker.memes["worry"] += 1
    seeker.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    return []


def _r_clue_guides(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_guides",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("seeker").memes["hope"] += 1
    world.get("helper").memes["focus"] += 1
    world.get("surprise").meters["nearby"] += 1
    return []


def _r_reveal_heals(world: World) -> list[str]:
    surprise = world.get("surprise")
    if surprise.meters["revealed"] < THRESHOLD:
        return []
    sig = ("reveal_heals",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("seeker").memes["joy"] += 1
    world.get("helper").memes["joy"] += 1
    grown = world.get("grownup")
    grown.memes["love"] += 1
    world.get("lane").meters["unfinished"] = 0.0
    world.get("lane").meters["complete"] += 1
    world.get("stripe").meters["missing"] = 0.0
    world.get("stripe").meters["shared"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_lane", tag="physical", apply=_r_missing_lane),
    Rule(name="clue_guides", tag="social", apply=_r_clue_guides),
    Rule(name="reveal_heals", tag="emotional", apply=_r_reveal_heals),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                produced.extend(lines)
                changed = True
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def material_fits(stripe: StripeItem, surprise: Surprise) -> bool:
    return surprise.id in stripe.can_make


def clue_fits(clue: Clue, surprise: Surprise) -> bool:
    return clue.place == surprise.place


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for lane_id in LANES:
        for stripe_id, stripe in STRIPES.items():
            for clue_id, clue in CLUES.items():
                for surprise_id, surprise in SURPRISES.items():
                    if material_fits(stripe, surprise) and clue_fits(clue, surprise):
                        combos.append((lane_id, stripe_id, clue_id, surprise_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "peeked" if params.manner == "rush" else "surprised"


# ---------------------------------------------------------------------------
# Screenplay helpers
# ---------------------------------------------------------------------------
def introduce(world: World, seeker: Entity, helper: Entity, lane_cfg: Lane, stripe_cfg: StripeItem) -> None:
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"One soft afternoon, {seeker.id} and {helper.id} made {lane_cfg.article if 'article' in lane_cfg.__dict__ else 'a'} "
        f"{lane_cfg.label if 'label' in lane_cfg.__dict__ else lane_cfg.play} in {lane_cfg.place}."
    )


def open_scene(world: World, seeker: Entity, helper: Entity, lane_cfg: Lane, stripe_cfg: StripeItem) -> None:
    world.say(
        f"One soft afternoon, {seeker.id} and {helper.id} made {lane_cfg.play} in {lane_cfg.place}. "
        f"{lane_cfg.floor_detail}"
    )
    world.say(
        f"They lined the edges with {stripe_cfg.phrase}, and the last bright stripe marked {lane_cfg.finish}."
    )
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1


def discover_missing(world: World, seeker: Entity, helper: Entity, lane_cfg: Lane, stripe_cfg: StripeItem) -> None:
    stripe = world.get("stripe")
    stripe.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {seeker.id} stepped back to admire the lane, one {stripe_cfg.label} stripe was gone."
    )
    world.say(
        f'"Our {lane_cfg.finish} looks crooked now," {seeker.id} said. {helper.id} looked all around, puzzled.'
    )


def choose_kindness(world: World, seeker: Entity, helper: Entity) -> None:
    helper.memes["care"] += 1
    world.say(
        f'"Let\'s not guess or grumble," {helper.id} said. "Let\'s solve the mystery kindly first."'
    )
    seeker.memes["calm"] += 1


def find_clue(world: World, seeker: Entity, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near the lane, {seeker.id} spotted {clue_cfg.phrase}. {clue_cfg.detail}"
    )


def follow_clue(world: World, seeker: Entity, helper: Entity, clue_cfg: Clue) -> None:
    world.say(
        f"Together they followed the clue toward the {clue_cfg.place}. "
        f"The mystery did not feel scary anymore. It felt like a small puzzle waiting to be understood."
    )


def reveal_scene(world: World, seeker: Entity, helper: Entity, grownup: Entity,
                 stripe_cfg: StripeItem, surprise_cfg: Surprise, lane_cfg: Lane,
                 manner: str) -> None:
    surprise = world.get("surprise")
    if manner == "rush":
        seeker.memes["impatience"] += 1
        world.say(
            f"When they reached the {surprise_cfg.place}, {seeker.id} hurried to peek around the corner."
        )
        world.say(
            f"There was {grownup.label_word} with the missing stripe, busy {surprise_cfg.making}."
        )
        world.say(
            f'{grownup.label_word.capitalize()} looked up and laughed softly. "Well, now you found my surprise a tiny bit early," '
            f'{grownup.pronoun()} said.'
        )
    else:
        world.say(
            f"In the {surprise_cfg.place}, they found {grownup.label_word} very carefully {surprise_cfg.making}."
        )
        world.say(
            f'{grownup.label_word.capitalize()} smiled when {helper.id} pointed at the missing stripe. '
            f'"You solved it," {grownup.pronoun()} said.'
        )
    surprise.meters["revealed"] += 1
    propagate(world, narrate=False)
    world.say(
        surprise_cfg.reveal.format(
            grownup=grownup.label_word.capitalize(),
            stripe=stripe_cfg.label,
            seeker=seeker.id,
            helper=helper.id,
        )
    )
    world.say(
        f'"I borrowed it only for a little while," {grownup.label_word} added. '
        f'"A lane with love in it should have something special at the end."'
    )


def repair_and_end(world: World, seeker: Entity, helper: Entity, grownup: Entity,
                   stripe_cfg: StripeItem, surprise_cfg: Surprise, lane_cfg: Lane) -> None:
    world.say(
        f"Soon the lane was straight again, and it looked even better than before."
    )
    world.say(
        surprise_cfg.ending_image.format(
            seeker=seeker.id,
            helper=helper.id,
            grownup=grownup.label_word,
            mover=lane_cfg.mover,
            finish=lane_cfg.finish,
            stripe=stripe_cfg.label,
        )
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    lane: str
    stripe: str
    clue: str
    surprise: str
    manner: str = "patient"
    seeker: str = "Lily"
    seeker_gender: str = "girl"
    helper: str = "Ben"
    helper_gender: str = "boy"
    grownup: str = "mother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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


def tell(lane_cfg: Lane, stripe_cfg: StripeItem, clue_cfg: Clue, surprise_cfg: Surprise,
         seeker_name: str = "Lily", seeker_type: str = "girl",
         helper_name: str = "Ben", helper_type: str = "boy",
         grownup_type: str = "mother", manner: str = "patient") -> World:
    world = World()
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type, role="seeker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    grownup = world.add(
        Entity(id="Grownup", kind="character", type=grownup_type, role="grownup", label="the grown-up")
    )
    lane = world.add(Entity(id="lane", type="lane", label=lane_cfg.id))
    stripe = world.add(Entity(id="stripe", type="stripe", label=stripe_cfg.label))
    clue = world.add(Entity(id="clue", type="clue", label=clue_cfg.label))
    surprise = world.add(Entity(id="surprise", type="surprise", label=surprise_cfg.label))

    # Initialize any fact/rule inputs before propagation.
    world.facts["lane_cfg"] = lane_cfg
    world.facts["stripe_cfg"] = stripe_cfg
    world.facts["clue_cfg"] = clue_cfg
    world.facts["surprise_cfg"] = surprise_cfg
    world.facts["manner"] = manner

    open_scene(world, seeker, helper, lane_cfg, stripe_cfg)

    world.para()
    discover_missing(world, seeker, helper, lane_cfg, stripe_cfg)
    choose_kindness(world, seeker, helper)
    find_clue(world, seeker, clue_cfg)
    follow_clue(world, seeker, helper, clue_cfg)

    world.para()
    reveal_scene(world, seeker, helper, grownup, stripe_cfg, surprise_cfg, lane_cfg, manner)

    world.para()
    repair_and_end(world, seeker, helper, grownup, stripe_cfg, surprise_cfg, lane_cfg)

    world.facts.update(
        seeker=seeker,
        helper=helper,
        grownup=grownup,
        lane=lane,
        stripe=stripe,
        clue=clue,
        surprise=surprise,
        solved=surprise.meters["revealed"] >= THRESHOLD,
        outcome=outcome_of(
            StoryParams(
                lane=lane_cfg.id,
                stripe=stripe_cfg.id,
                clue=clue_cfg.id,
                surprise=surprise_cfg.id,
                manner=manner,
                seeker=seeker_name,
                seeker_gender=seeker_type,
                helper=helper_name,
                helper_gender=helper_type,
                grownup=grownup_type,
                seed=None,
            )
        ),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
LANES = {
    "toy_car": Lane(
        id="toy_car",
        place="the hallway",
        play="a toy-car lane",
        mover="tiny cars",
        finish="the little finish lane by the bookcase",
        floor_detail="Blue tape made the long lane, and a pillow at the end became the grandstand.",
        tags={"lane", "toy_car"},
    ),
    "marble": Lane(
        id="marble",
        place="the porch",
        play="a marble lane",
        mover="shiny marbles",
        finish="the chalk finish lane by the flowerpot",
        floor_detail="A cardboard ramp leaned against the step, and the boards glowed warm in the sun.",
        tags={"lane", "marble"},
    ),
    "scooter": Lane(
        id="scooter",
        place="the driveway",
        play="a scooter lane",
        mover="small scooters",
        finish="the finish lane near the mailbox",
        floor_detail="Sidewalk chalk curved in bright lines, and a bell on the gate gave tiny happy rings.",
        tags={"lane", "scooter"},
    ),
}

STRIPES = {
    "ribbon": StripeItem(
        id="ribbon",
        label="ribbon",
        phrase="a striped ribbon",
        texture="silky",
        finish_role="a fluttering finish stripe",
        can_make={"medal", "banner"},
        tags={"ribbon", "stripe"},
    ),
    "paper_strip": StripeItem(
        id="paper_strip",
        label="paper strip",
        phrase="a striped paper strip",
        texture="crisp",
        finish_role="a bright paper finish stripe",
        can_make={"banner"},
        tags={"paper", "stripe"},
    ),
    "scarf": StripeItem(
        id="scarf",
        label="scarf",
        phrase="a soft striped scarf",
        texture="soft",
        finish_role="a cozy finish stripe",
        can_make={"medal", "cape"},
        tags={"scarf", "stripe"},
    ),
}

CLUES = {
    "buttons": Clue(
        id="buttons",
        label="buttons",
        phrase="two shiny buttons on the floor",
        place="craft table",
        detail="They were the kind that sometimes rolled out of the sewing tin.",
        tags={"buttons", "clue"},
    ),
    "tape_snips": Clue(
        id="tape_snips",
        label="tape snips",
        phrase="tiny curled snips of tape",
        place="porch bench",
        detail="They looked fresh, as if someone had just trimmed something neat and careful.",
        tags={"tape", "clue"},
    ),
    "thread": Clue(
        id="thread",
        label="thread",
        phrase="a loop of bright thread",
        place="sofa nook",
        detail="It led under the lamp where soft things were often mended.",
        tags={"thread", "clue"},
    ),
}

SURPRISES = {
    "medal": Surprise(
        id="medal",
        label="winner's medal",
        article="a",
        place="craft table",
        making="tying the missing stripe around a shiny cardboard medal",
        reveal="{grownup} had turned the missing {stripe} into a little winner's medal for the end of the race. It was meant for {seeker} and {helper} to share after their game.",
        ending_image="{seeker} sent the {mover} along the lane while {helper} held up the medal, and even {grownup} clapped when they crossed {finish}.",
        tags={"medal"},
    ),
    "banner": Surprise(
        id="banner",
        label="cheering banner",
        article="a",
        place="porch bench",
        making="fastening the missing stripe onto a small cheering banner",
        reveal="{grownup} had tucked the missing {stripe} onto a tiny cheering banner that said Hooray for {seeker} and {helper}. It was waiting to wave over the lane when the game began.",
        ending_image="The banner bobbed above {finish}, the {mover} zipped underneath it, and {seeker} laughed to see the old stripe dancing in the air.",
        tags={"banner"},
    ),
    "cape": Surprise(
        id="cape",
        label="helper cape",
        article="a",
        place="sofa nook",
        making="pinning the missing stripe into a tiny helper cape",
        reveal="{grownup} had folded the missing {stripe} into a little helper cape for a stuffed bear who was going to hand out cheers at the end of the game. The surprise made the whole lane feel like a celebration.",
        ending_image="At the end of the race, a stuffed bear in the cape waited by {finish}, and {helper} hugged it while {seeker} sent the {mover} gliding past.",
        tags={"cape"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Max", "Theo", "Finn", "Eli", "Jack"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "lane": [
        (
            "What is a lane in a game?",
            "A lane is a long path or strip where toys or people are meant to go. It helps everyone know where the race or game should happen."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a long, soft strip of cloth. People use ribbons to tie, decorate, or make something look special."
        )
    ],
    "paper": [
        (
            "What is a paper strip?",
            "A paper strip is a thin piece of paper cut into a long shape. It can be used for signs, crafts, or decorations."
        )
    ],
    "scarf": [
        (
            "What is a scarf?",
            "A scarf is a soft piece of cloth people wear or wrap around things. It can keep you warm or be used in gentle pretend play."
        )
    ],
    "medal": [
        (
            "What is a medal?",
            "A medal is a prize or sign of praise. It shows that someone wants to celebrate your effort or your kindness."
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a sign or strip of cloth or paper that people hold up to cheer. It makes a place feel festive and welcoming."
        )
    ],
    "cape": [
        (
            "What is a cape?",
            "A cape is a piece of cloth that hangs over the back and shoulders. In pretend play, it can make a toy or a person feel brave or special."
        )
    ],
    "buttons": [
        (
            "Why can buttons be a clue in a craft mystery?",
            "Buttons are often used in sewing or making things. If you find them on the floor, they can show that someone was crafting nearby."
        )
    ],
    "tape": [
        (
            "Why can little tape snips be a clue?",
            "Tiny snips of tape can fall when someone is making a sign or decoration. They can point to a place where careful crafting just happened."
        )
    ],
    "thread": [
        (
            "What does thread help people do?",
            "Thread helps people sew, mend, or tie soft things together. Seeing thread can mean someone has been making or fixing something."
        )
    ],
}
KNOWLEDGE_ORDER = ["lane", "ribbon", "paper", "scarf", "medal", "banner", "cape", "buttons", "tape", "thread"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    lane_cfg = f["lane_cfg"]
    stripe_cfg = f["stripe_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "stripe" and "lane" and centers on a small mystery to solve.',
        f"Tell a gentle mystery story where {seeker.id} and {helper.id} build {lane_cfg.play}, notice a missing {stripe_cfg.label}, and discover a loving surprise.",
        f"Write a simple story with a missing clue, a kind investigation, and a happy ending image at the end of a play lane.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    grownup = f["grownup"]
    lane_cfg = f["lane_cfg"]
    stripe_cfg = f["stripe_cfg"]
    clue_cfg = f["clue_cfg"]
    surprise_cfg = f["surprise_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id} and {helper.id}, who were building {lane_cfg.play}, and {grownup.label_word} who had a secret surprise ready for them."
        ),
        (
            "What was the mystery in the story?",
            f"The mystery was that one {stripe_cfg.label} stripe had gone missing from the lane. That made the finish look crooked, so the children had to figure out where it had gone."
        ),
        (
            f"Why did {helper.id} tell {seeker.id} not to grumble?",
            f"{helper.id} wanted them to solve the mystery kindly instead of blaming someone too soon. That choice changed the mood from worry to curiosity and helped them follow the real clue."
        ),
        (
            "What clue did they find, and where did it lead?",
            f"They found {clue_cfg.phrase}. Because that clue belonged near the {clue_cfg.place}, it led them straight to the place where the surprise was being made."
        ),
        (
            f"What had {grownup.label_word} done with the missing stripe?",
            f"{grownup.label_word.capitalize()} had borrowed it to make {surprise_cfg.article} {surprise_cfg.label}. The missing stripe was not lost at all; it had become part of something loving and special."
        ),
    ]
    if outcome == "peeked":
        qa.append(
            (
                "Was the surprise still a surprise?",
                f"Mostly, yes, but {seeker.id} peeked a tiny bit early. Even so, the reveal stayed warm and happy because {grownup.label_word} laughed gently and shared the surprise with love."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the lane straight again and the surprise shining at the finish. The children were not only ready to play; they also knew that the missing stripe had been borrowed for kindness."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"lane"}
    tags |= set(world.facts["stripe_cfg"].tags)
    tags |= set(world.facts["clue_cfg"].tags)
    tags |= set(world.facts["surprise_cfg"].tags)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        lane="toy_car",
        stripe="ribbon",
        clue="buttons",
        surprise="medal",
        manner="patient",
        seeker="Lily",
        seeker_gender="girl",
        helper="Ben",
        helper_gender="boy",
        grownup="mother",
    ),
    StoryParams(
        lane="marble",
        stripe="paper_strip",
        clue="tape_snips",
        surprise="banner",
        manner="patient",
        seeker="Mia",
        seeker_gender="girl",
        helper="Leo",
        helper_gender="boy",
        grownup="father",
    ),
    StoryParams(
        lane="scooter",
        stripe="scarf",
        clue="thread",
        surprise="cape",
        manner="rush",
        seeker="Nora",
        seeker_gender="girl",
        helper="Sam",
        helper_gender="boy",
        grownup="grandmother",
    ),
    StoryParams(
        lane="toy_car",
        stripe="scarf",
        clue="buttons",
        surprise="medal",
        manner="patient",
        seeker="Theo",
        seeker_gender="boy",
        helper="Ava",
        helper_gender="girl",
        grownup="grandfather",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
usable(S, Su) :- stripe_item(S), surprise(Su), decorates(S, Su).
matching_clue(C, Su) :- clue(C), surprise(Su), clue_place(C, P), surprise_place(Su, P).
valid(L, S, C, Su) :- lane(L), usable(S, Su), matching_clue(C, Su).

outcome(peeked) :- manner(rush).
outcome(surprised) :- manner(patient).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for lane_id in LANES:
        lines.append(asp.fact("lane", lane_id))
    for stripe_id, stripe in STRIPES.items():
        lines.append(asp.fact("stripe_item", stripe_id))
        for surprise_id in sorted(stripe.can_make):
            lines.append(asp.fact("decorates", stripe_id, surprise_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_place", clue_id, clue.place))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        lines.append(asp.fact("surprise_place", surprise_id, surprise.place))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("manner", params.manner)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
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
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="")
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a missing stripe, a lane, a clue, and a heartwarming surprise."
    )
    ap.add_argument("--lane", choices=LANES)
    ap.add_argument("--stripe", choices=STRIPES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--manner", choices=["patient", "rush"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def explain_rejection(stripe: StripeItem, clue: Clue, surprise: Surprise) -> str:
    if not material_fits(stripe, surprise):
        options = ", ".join(sorted(stripe.can_make))
        return (
            f"(No story: {stripe.phrase} cannot honestly become {surprise.article} {surprise.label}. "
            f"It only fits surprise kinds like: {options}.)"
        )
    if not clue_fits(clue, surprise):
        return (
            f"(No story: {clue.phrase} points to the {clue.place}, but the {surprise.label} would be made at the "
            f"{surprise.place}. The clue must truly lead to the surprise.)"
        )
    return "(No story: this combination does not make a coherent mystery.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.stripe and args.surprise:
        stripe = STRIPES[args.stripe]
        surprise = SURPRISES[args.surprise]
        clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        if not material_fits(stripe, surprise) or not clue_fits(clue, surprise):
            raise StoryError(explain_rejection(stripe, clue, surprise))
    if args.clue and args.surprise and not clue_fits(CLUES[args.clue], SURPRISES[args.surprise]):
        stripe = STRIPES[args.stripe] if args.stripe else next(iter(STRIPES.values()))
        raise StoryError(explain_rejection(stripe, CLUES[args.clue], SURPRISES[args.surprise]))

    combos = [
        combo for combo in valid_combos()
        if (args.lane is None or combo[0] == args.lane)
        and (args.stripe is None or combo[1] == args.stripe)
        and (args.clue is None or combo[2] == args.clue)
        and (args.surprise is None or combo[3] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lane_id, stripe_id, clue_id, surprise_id = rng.choice(sorted(combos))
    manner = args.manner or rng.choice(["patient", "rush"])
    seeker_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    seeker = _pick_name(rng, seeker_gender)
    helper = _pick_name(rng, helper_gender, avoid=seeker)
    grownup = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather"])

    return StoryParams(
        lane=lane_id,
        stripe=stripe_id,
        clue=clue_id,
        surprise=surprise_id,
        manner=manner,
        seeker=seeker,
        seeker_gender=seeker_gender,
        helper=helper,
        helper_gender=helper_gender,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    if params.lane not in LANES:
        raise StoryError(f"(Unknown lane: {params.lane})")
    if params.stripe not in STRIPES:
        raise StoryError(f"(Unknown stripe: {params.stripe})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")
    if params.manner not in {"patient", "rush"}:
        raise StoryError(f"(Unknown manner: {params.manner})")
    if params.grownup not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown grownup: {params.grownup})")

    lane_cfg = LANES[params.lane]
    stripe_cfg = STRIPES[params.stripe]
    clue_cfg = CLUES[params.clue]
    surprise_cfg = SURPRISES[params.surprise]
    if not material_fits(stripe_cfg, surprise_cfg) or not clue_fits(clue_cfg, surprise_cfg):
        raise StoryError(explain_rejection(stripe_cfg, clue_cfg, surprise_cfg))

    world = tell(
        lane_cfg=lane_cfg,
        stripe_cfg=stripe_cfg,
        clue_cfg=clue_cfg,
        surprise_cfg=surprise_cfg,
        seeker_name=params.seeker,
        seeker_type=params.seeker_gender,
        helper_name=params.helper,
        helper_type=params.helper_gender,
        grownup_type=params.grownup,
        manner=params.manner,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lane, stripe, clue, surprise) combos:\n")
        for lane_id, stripe_id, clue_id, surprise_id in combos:
            print(f"  {lane_id:9} {stripe_id:11} {clue_id:10} {surprise_id}")
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
            header = (
                f"### {p.seeker} & {p.helper}: {p.lane}, {p.stripe}, {p.surprise} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
