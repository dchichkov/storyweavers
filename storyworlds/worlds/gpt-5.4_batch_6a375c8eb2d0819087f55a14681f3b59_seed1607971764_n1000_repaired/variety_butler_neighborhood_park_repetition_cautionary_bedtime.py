#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/variety_butler_neighborhood_park_repetition_cautionary_bedtime.py
================================================================================================

A standalone story world for a gentle bedtime cautionary tale set in a neighborhood
park. A child plays at being a tiny park butler, gathering a variety of small
nature treasures for a pretend tea party. The tempting mistake is to take a quick,
wobbly route across a low stone border near the pond instead of the safe path.

The world model tracks simple physical meters (balance, spill, scrape, danger)
and emotional memes (joy, caution, fear, relief, pride). The prose is driven by
simulated state, including a repeated warning beat: "Slow feet by the pond."

Run it
------
    python storyworlds/worlds/gpt-5.4/variety_butler_neighborhood_park_repetition_cautionary_bedtime.py
    python storyworlds/worlds/gpt-5.4/variety_butler_neighborhood_park_repetition_cautionary_bedtime.py --hazard pond_border --goal bench
    python storyworlds/worlds/gpt-5.4/variety_butler_neighborhood_park_repetition_cautionary_bedtime.py --hazard grass
    python storyworlds/worlds/gpt-5.4/variety_butler_neighborhood_park_repetition_cautionary_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/variety_butler_neighborhood_park_repetition_cautionary_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/variety_butler_neighborhood_park_repetition_cautionary_bedtime.py --verify
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    slippery: bool = False
    near_water: bool = False
    safe_route: bool = False
    carries_load: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
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
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Theme:
    id: str
    opening: str
    collection: str
    party: str
    title: str
    final_line: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    surface: str
    near: str
    safe: bool
    slippery: bool
    near_water: bool
    risk_text: str
    repeated_warning: str
    consequence: str
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
class Goal:
    id: str
    label: str
    phrase: str
    nearby: str
    waiting_image: str
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
class Fix:
    id: str
    sense: int
    power: int
    label: str
    text: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    route = world.get("hazard")
    tray = world.get("tray")
    if child.meters["on_route"] < THRESHOLD:
        return out
    if not route.slippery:
        return out
    sig = ("wobble", route.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["balance_loss"] += 1
    tray.meters["tilt"] += 1
    child.memes["fear"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    tray = world.get("tray")
    if child.meters["balance_loss"] < THRESHOLD or tray.meters["load"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tray.meters["spill"] += 1
    tray.meters["load"] = 0.0
    child.memes["sadness"] += 1
    out.append("__spill__")
    return out


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    route = world.get("hazard")
    if child.meters["balance_loss"] < THRESHOLD or not route.near_water:
        return out
    sig = ("danger", route.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("park").meters["danger"] += 1
    child.memes["fear"] += 1
    out.append("__danger__")
    return out


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.meters["balance_loss"] < THRESHOLD or helper.meters["catch"] >= THRESHOLD:
        return out
    sig = ("scrape",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["scrape"] += 1
    child.memes["fear"] += 1
    out.append("__scrape__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="scrape", tag="physical", apply=_r_scrape),
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
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def hazard_at_risk(hazard: Hazard, goal: Goal) -> bool:
    return (not hazard.safe) and (hazard.slippery or hazard.near_water) and bool(goal.id)


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: (f.sense, f.power))


def rescue_need(hazard: Hazard) -> int:
    need = 1
    if hazard.slippery:
        need += 1
    if hazard.near_water:
        need += 1
    return need


def fix_works(fix: Fix, hazard: Hazard) -> bool:
    return fix.power >= rescue_need(hazard)


def predict_crossing(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["on_route"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": child.meters["balance_loss"] >= THRESHOLD,
        "spill": sim.get("tray").meters["spill"] >= THRESHOLD,
        "danger": sim.get("park").meters["danger"] >= THRESHOLD,
        "scrape": child.meters["scrape"] >= THRESHOLD,
    }


def play_setup(world: World, child: Entity, helper: Entity, theme: Theme, goal: Goal) -> None:
    child.memes["joy"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"In the soft evening light at the neighborhood park, {child.id} and "
        f"{helper.label_word} made {theme.opening}."
    )
    world.say(
        f"{child.id} was the {theme.title}, carrying a little tray and gathering "
        f"{theme.collection} for {goal.phrase}."
    )
    world.say(goal.waiting_image)


def gather(world: World, child: Entity, tray: Entity) -> None:
    tray.meters["load"] += 1
    child.memes["pride"] += 1
    world.say(
        f"Onto the tray went a small variety of treasures: a yellow leaf, two "
        f"round pebbles, a feathery seed, and one bright acorn cup."
    )


def tempt(world: World, child: Entity, hazard: Hazard, goal: Goal) -> None:
    child.memes["urgency"] += 1
    world.say(
        f"When {child.id} saw {goal.nearby}, the short way looked easy: "
        f"{hazard.phrase}."
    )
    world.say(
        f'"I can go this way with my tray," {child.pronoun()} whispered. '
        f'"Just this way. Just this way."'
    )


def warn(world: World, helper: Entity, child: Entity, hazard: Hazard) -> None:
    pred = predict_crossing(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_spill"] = pred["spill"]
    world.facts["predicted_danger"] = pred["danger"]
    child.memes["caution_heard"] += 1
    because = []
    if pred["wobble"]:
        because.append("the stones could make the tray wobble")
    if pred["spill"]:
        because.append("the little treasures could spill")
    if pred["danger"]:
        because.append("the water was too close for quick feet")
    reason = ", and ".join(because) if because else hazard.risk_text
    world.say(
        f'{helper.label_word.capitalize()} touched {child.id}\'s shoulder and said, '
        f'"{hazard.repeated_warning}. {hazard.repeated_warning}. {reason}."'
    )


def step_onto_hazard(world: World, child: Entity) -> None:
    child.meters["on_route"] += 1
    produced = propagate(world, narrate=False)
    wobble = "__wobble__" in produced
    spill = "__spill__" in produced
    world.say(
        f"But the wish to hurry felt bigger than the warning, and {child.id} "
        f"placed one foot on the stones."
    )
    if wobble:
        world.say(
            f"At once the tray tipped, and {child.pronoun('possessive')} shoulders "
            f"gave a tiny frightened jump."
        )
    if spill:
        world.say(
            "The leaf fluttered down, the pebbles clicked together, and the acorn "
            "cup rolled toward the pond."
        )


def rescue(world: World, helper: Entity, child: Entity, fix: Fix, hazard: Hazard) -> None:
    helper.meters["catch"] += 1
    world.get("park").meters["danger"] = 0.0
    child.meters["on_route"] = 0.0
    child.meters["balance_loss"] = 0.0
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    world.say(
        f"{helper.label_word.capitalize()} moved quickly and {fix.text}"
    )
    if hazard.near_water:
        world.say(
            f"{child.id} felt how near the dark water had been, and stood very still "
            f"with {child.pronoun('possessive')} heart knocking."
        )


def comfort_and_lesson(world: World, helper: Entity, child: Entity, hazard: Hazard) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f'"Oh, my little butler," {helper.label_word} said softly, drawing '
        f"{child.pronoun('object')} close. "
        f'"A quick way is not always a kind way. {hazard.repeated_warning}."'
    )
    if child.meters["scrape"] >= THRESHOLD:
        world.say(
            f"{helper.label_word.capitalize()} brushed the dust from {child.id}'s knee "
            f"and kissed the small scrape."
        )
    else:
        world.say(
            f"{child.id} leaned in and listened, no longer trying to be quick."
        )


def safe_route(world: World, child: Entity, helper: Entity, goal: Goal, tray: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    world.say(
        f"Then they took the long path of smooth bricks around the pond, step by "
        f"step, slow feet and steady hands."
    )
    if tray.meters["spill"] >= THRESHOLD:
        world.say(
            f"Together they gathered the little treasures again, and this time "
            f"nothing rolled away."
        )
        tray.meters["load"] += 1
        tray.meters["spill"] = 0.0
    world.say(
        f"At last they reached {goal.phrase}, and {child.id} set down the tray as "
        f"carefully as moonlight settling on a bench."
    )
    world.say(goal.waiting_image)
    world.say(goal_finish_line(world))


def goal_finish_line(world: World) -> str:
    goal = world.facts["goal"]
    theme = world.facts["theme"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    return (
        f'Together they whispered, "{world.facts["hazard_cfg"].repeated_warning}," '
        f"as if it were part of the game now, and the {theme.title} served the "
        f"tiny feast safely beside {helper.label_word}. {theme.final_line}"
    )


THEMES = {
    "tea_party": Theme(
        id="tea_party",
        opening="a hush-hush evening tea party under the sycamore tree",
        collection="tiny park treasures",
        party="a tiny tea party",
        title="park butler",
        final_line="Soon the park looked sleepy too, and the lesson stayed gentle and bright in memory.",
        tags={"bedtime", "play"},
    ),
    "leaf_feast": Theme(
        id="leaf_feast",
        opening="a small supper for stuffed friends on a plaid blanket",
        collection="leaf plates and pebble buns",
        party="a blanket supper",
        title="leaf butler",
        final_line="By the time the first stars showed, quick feet had turned into careful feet.",
        tags={"bedtime", "play"},
    ),
    "owl_picnic": Theme(
        id="owl_picnic",
        opening="a twilight picnic for toy owls near the flower bed",
        collection="soft seeds and little leaves",
        party="an owl picnic",
        title="twilight butler",
        final_line="The evening closed like a book, and the safer path became part of every later game.",
        tags={"bedtime", "play"},
    ),
}

HAZARDS = {
    "pond_border": Hazard(
        id="pond_border",
        label="pond border",
        phrase="the low stone border that curved along the pond",
        surface="low stones",
        near="the pond",
        safe=False,
        slippery=True,
        near_water=True,
        risk_text="it was slippery and far too near the pond",
        repeated_warning="Slow feet by the pond",
        consequence="a wobble by the water",
        tags={"pond", "slippery", "water"},
    ),
    "flower_edging": Hazard(
        id="flower_edging",
        label="flower-bed edging",
        phrase="the narrow brick edging by the flower bed",
        surface="narrow bricks",
        near="the flower bed",
        safe=False,
        slippery=True,
        near_water=False,
        risk_text="the edging was narrow and wobbly for a child with a tray",
        repeated_warning="Slow feet by the edge",
        consequence="a spill onto the path",
        tags={"edge", "slippery", "flowers"},
    ),
    "grass": Hazard(
        id="grass",
        label="wide grass",
        phrase="the wide grass path beside the lamps",
        surface="grass",
        near="the lamps",
        safe=True,
        slippery=False,
        near_water=False,
        risk_text="it was broad and safe",
        repeated_warning="Slow feet on the grass",
        consequence="no real danger",
        tags={"grass", "safe"},
    ),
}

GOALS = {
    "bench": Goal(
        id="bench",
        label="bench",
        phrase="the striped bench under the sycamore",
        nearby="the striped bench under the sycamore tree",
        waiting_image="A toy bear and a folded napkin were waiting there as if guests had come early.",
        tags={"bench"},
    ),
    "blanket": Goal(
        id="blanket",
        label="blanket",
        phrase="the plaid blanket near the daisies",
        nearby="the plaid blanket near the daisies",
        waiting_image="Two stuffed rabbits sat there already, patient as old ladies at supper.",
        tags={"blanket"},
    ),
    "gazebo": Goal(
        id="gazebo",
        label="gazebo",
        phrase="the little gazebo with the painted rail",
        nearby="the little gazebo with the painted rail",
        waiting_image="Inside, a doll's cup and saucer waited on a wooden step.",
        tags={"gazebo"},
    ),
}

FIXES = {
    "hand_hold": Fix(
        id="hand_hold",
        sense=3,
        power=3,
        label="hand hold",
        text="took the tray in one hand and {child}'s hand in the other, guiding {obj} back to the path.",
        qa_text="held the child's hand and guided the tray back to the safe path",
        tags={"hand", "adult_help"},
    ),
    "tray_first": Fix(
        id="tray_first",
        sense=2,
        power=2,
        label="tray first",
        text="lifted the tray away from the edge and turned {child} gently toward the long path.",
        qa_text="lifted the tray away and turned the child back to the long path",
        tags={"tray", "adult_help"},
    ),
    "call_from_bench": Fix(
        id="call_from_bench",
        sense=1,
        power=1,
        label="call from bench",
        text="called for {child} to come back, but the edge was still under {pos} feet.",
        qa_text="only called out from far away",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Maya", "Nora"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Theo", "Finn", "Eli", "Noah"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["careful", "dreamy", "playful", "eager", "gentle", "curious"]
STUFFED = ["toy bear", "striped rabbit", "little owl", "soft fox"]


@dataclass
class StoryParams:
    theme: str
    hazard: str
    goal: str
    fix: str
    child_name: str
    child_gender: str
    helper_type: str
    child_trait: str
    stuffed_friend: str = ""
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for hazard_id, hazard in HAZARDS.items():
            for goal_id, goal in GOALS.items():
                if hazard_at_risk(hazard, goal):
                    combos.append((theme_id, hazard_id, goal_id))
    return combos


KNOWLEDGE = {
    "pond": [
        (
            "Why should children use slow feet near a pond?",
            "A pond has water close by, and wet edges can be slippery. Slow feet help your body stay balanced and give a grown-up time to help.",
        )
    ],
    "slippery": [
        (
            "What does slippery mean?",
            "Slippery means your feet do not grip well, so you can slide or wobble. Stones and bricks can feel slippery when they are smooth or damp.",
        )
    ],
    "water": [
        (
            "Why is water by a path something to notice?",
            "Water can make nearby edges slick, and a stumble there can be more serious. That is why grown-ups tell children to walk carefully near it.",
        )
    ],
    "adult_help": [
        (
            "What should a child do if a path feels wobbly or unsafe?",
            "Stop moving fast and ask a grown-up for help. A safe helper can hold your hand, carry something for you, or show you the better way.",
        )
    ],
    "tray": [
        (
            "Why is it harder to balance while carrying a tray?",
            "A tray gives your hands a job, so they cannot help as much with balance. If the tray tips, the things on it can slide and make you wobble more.",
        )
    ],
    "bench": [
        (
            "What is a park bench for?",
            "A park bench is a place to sit, rest, or set things down. It is a better place for a pretend tea party than a narrow edge by water.",
        )
    ],
    "blanket": [
        (
            "Why do people use a blanket for a picnic?",
            "A blanket makes a soft clean spot to sit and put things on. It helps keep small things together instead of rolling away.",
        )
    ],
    "gazebo": [
        (
            "What is a gazebo?",
            "A gazebo is a small open park shelter with a roof. People rest there, talk there, or pretend it is part of a game.",
        )
    ],
}
KNOWLEDGE_ORDER = ["pond", "slippery", "water", "adult_help", "tray", "bench", "blanket", "gazebo"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    theme = f["theme"]
    hazard = f["hazard_cfg"]
    goal = f["goal"]
    return [
        f'Write a bedtime story set in a neighborhood park about a child pretending to be a "{theme.title}" and carrying a tray of tiny treasures.',
        f"Tell a gentle cautionary story where {child.id} wants to hurry across {hazard.phrase} to reach {goal.phrase}, but {helper.label_word} repeats a warning and teaches a safer way.",
        f'Write a soft, repetitive story for young children that includes the words "variety" and "butler" and ends with careful walking instead of quick walking.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    goal = f["goal"]
    theme = f["theme"]
    hazard = f["hazard_cfg"]
    fix = f["fix"]
    tray = world.get("tray")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child playing as a tiny {theme.title}, and {helper.label_word} at the neighborhood park. They were making a pretend feast with small park treasures.",
        ),
        (
            f"What was on {child.id}'s tray?",
            "There was a small variety of treasures on the tray: a yellow leaf, two pebbles, a feathery seed, and an acorn cup. Those little things mattered because carrying them made balance harder.",
        ),
        (
            f"Why did {helper.label_word} warn {child.id}?",
            f"{helper.label_word.capitalize()} warned {child.id} because {hazard.phrase} was not a safe shortcut. The edge could make the tray wobble, and it was too close to danger for quick feet.",
        ),
        (
            f"What happened when {child.id} stepped onto the shortcut?",
            "The tray tipped and the careful game turned shaky all at once. Some of the treasures spilled, and the scary part began because rushing was bigger than caution for one moment.",
        ),
        (
            f"How did {helper.label_word} help?",
            _story_fix_answer(world),
        ),
        (
            "How did the story end?",
            f"They took the long safe path and reached {goal.phrase} together. The repeated warning became part of the game, and the ending image shows that careful feet had replaced hurrying feet.",
        ),
    ]
    if child.meters["scrape"] >= THRESHOLD:
        qa.append(
            (
                f"Did {child.id} get badly hurt?",
                f"No, only a small scrape happened. It still mattered because the scrape made the warning feel real and helped the lesson stay in {child.pronoun('possessive')} mind.",
            )
        )
    if tray.meters["spill"] == 0.0:
        qa.append(
            (
                "Did the treasures stay spilled forever?",
                "No. They gathered the little treasures again before the pretend supper, which shows the helper did not just stop the danger but also helped mend the game.",
            )
        )
    return qa


def _story_fix_answer(world: World) -> str:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    fix = f["fix"]
    answer = fix.qa_text
    return (
        f"{helper.label_word.capitalize()} {answer}. That changed the story because the quick, wobbly shortcut stopped being the route, and the safe path became the way forward."
    )


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["hazard_cfg"].tags) | set(world.facts["goal"].tags)
    tags |= set(world.facts["fix"].tags)
    tags.add("tray")
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
        flags = []
        if e.slippery:
            flags.append("slippery")
        if e.near_water:
            flags.append("near_water")
        if e.safe_route:
            flags.append("safe_route")
        if e.carries_load:
            flags.append("carries_load")
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(hazard: Hazard, goal: Goal) -> str:
    if hazard.safe:
        return (
            f"(No story: {hazard.phrase} is already a safe route to {goal.phrase}, "
            f"so there is no honest cautionary turn. Pick a slippery edge near the pond or flower bed.)"
        )
    return "(No story: this combination has no meaningful hazard.)"


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = " / ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "rescued" if fix_works(FIXES[params.fix], HAZARDS[params.hazard]) else "scraped"


def tell(
    theme: Theme,
    hazard_cfg: Hazard,
    goal: Goal,
    fix: Fix,
    *,
    child_name: str = "Lily",
    child_gender: str = "girl",
    helper_type: str = "grandmother",
    child_trait: str = "careful",
    stuffed_friend: str = "toy bear",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[child_trait],
            attrs={"stuffed_friend": stuffed_friend},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    park = world.add(Entity(id="park", type="park", label="the neighborhood park"))
    hazard = world.add(
        Entity(
            id="hazard",
            type="route",
            label=hazard_cfg.label,
            slippery=hazard_cfg.slippery,
            near_water=hazard_cfg.near_water,
            safe_route=hazard_cfg.safe,
        )
    )
    tray = world.add(
        Entity(
            id="tray",
            type="tray",
            label="tray",
            carries_load=True,
        )
    )
    safe_path = world.add(Entity(id="safe_path", type="path", label="long path", safe_route=True))

    child.meters["on_route"] = 0.0
    child.meters["balance_loss"] = 0.0
    child.meters["scrape"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["fear"] = 0.0
    helper.meters["catch"] = 0.0
    tray.meters["load"] = 0.0
    tray.meters["tilt"] = 0.0
    tray.meters["spill"] = 0.0
    park.meters["danger"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        goal=goal,
        theme=theme,
        hazard_cfg=hazard_cfg,
        fix=fix,
        stuffed_friend=stuffed_friend,
        predicted_wobble=False,
        predicted_spill=False,
        predicted_danger=False,
    )

    play_setup(world, child, helper, theme, goal)
    gather(world, child, tray)

    world.para()
    tempt(world, child, hazard_cfg, goal)
    warn(world, helper, child, hazard_cfg)

    world.para()
    step_onto_hazard(world, child)

    worked = fix_works(fix, hazard_cfg)
    if worked:
        text = fix.text.format(
            child=child.id,
            obj=child.pronoun("object"),
            pos=child.pronoun("possessive"),
        )
        fix_runtime = Fix(
            id=fix.id,
            sense=fix.sense,
            power=fix.power,
            label=fix.label,
            text=text,
            qa_text=fix.qa_text,
            tags=set(fix.tags),
        )
        world.facts["fix"] = fix_runtime
        world.para()
        rescue(world, helper, child, fix_runtime, hazard_cfg)
        comfort_and_lesson(world, helper, child, hazard_cfg)
        world.para()
        safe_route(world, child, helper, goal, tray)
        outcome = "rescued"
    else:
        text = fix.text.format(
            child=child.id,
            obj=child.pronoun("object"),
            pos=child.pronoun("possessive"),
        )
        fix_runtime = Fix(
            id=fix.id,
            sense=fix.sense,
            power=fix.power,
            label=fix.label,
            text=text,
            qa_text=fix.qa_text,
            tags=set(fix.tags),
        )
        world.facts["fix"] = fix_runtime
        world.say(
            f"{helper.label_word.capitalize()} called from too far away, and {child.id} had to hop down alone."
        )
        child.meters["scrape"] += 1
        child.memes["fear"] += 1
        world.para()
        comfort_and_lesson(world, helper, child, hazard_cfg)
        world.para()
        safe_route(world, child, helper, goal, tray)
        outcome = "scraped"

    world.facts["outcome"] = outcome
    return world


ASP_RULES = r"""
hazard_at_risk(H, G) :- hazard(H), goal(G), not safe(H), (slippery(H); near_water(H)).
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.

need(H, 1) :- hazard(H), not slippery(H), not near_water(H).
need(H, 2) :- hazard(H), slippery(H), not near_water(H).
need(H, 2) :- hazard(H), not slippery(H), near_water(H).
need(H, 3) :- hazard(H), slippery(H), near_water(H).

valid(T, H, G) :- theme(T), hazard(H), goal(G), hazard_at_risk(H, G).

works(F, H) :- chosen_fix(F), chosen_hazard(H), power(F, P), need(H, N), P >= N.
outcome(rescued) :- works(F, H), chosen_fix(F), chosen_hazard(H).
outcome(scraped) :- chosen_fix(F), chosen_hazard(H), not works(F, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if hazard.safe:
            lines.append(asp.fact("safe", hid))
        if hazard.slippery:
            lines.append(asp.fact("slippery", hid))
        if hazard.near_water:
            lines.append(asp.fact("near_water", hid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("power", fid, fix.power))
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
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


CURATED = [
    StoryParams(
        theme="tea_party",
        hazard="pond_border",
        goal="bench",
        fix="hand_hold",
        child_name="Lily",
        child_gender="girl",
        helper_type="grandmother",
        child_trait="eager",
        stuffed_friend="toy bear",
    ),
    StoryParams(
        theme="leaf_feast",
        hazard="flower_edging",
        goal="blanket",
        fix="tray_first",
        child_name="Ben",
        child_gender="boy",
        helper_type="father",
        child_trait="curious",
        stuffed_friend="striped rabbit",
    ),
    StoryParams(
        theme="owl_picnic",
        hazard="pond_border",
        goal="gazebo",
        fix="hand_hold",
        child_name="Maya",
        child_gender="girl",
        helper_type="mother",
        child_trait="dreamy",
        stuffed_friend="little owl",
    ),
]


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {f.id for f in sensible_fixes()}
    if c_sens == p_sens:
        print(f"OK: sensible fixes match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(50):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story in smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny park butler learns that slow feet are safer than quick shortcuts."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard:
        hazard = HAZARDS[args.hazard]
        goal = GOALS[args.goal] if args.goal else next(iter(GOALS.values()))
        if not hazard_at_risk(hazard, goal):
            raise StoryError(explain_rejection(hazard, goal))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c
        for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.hazard is None or c[1] == args.hazard)
        and (args.goal is None or c[2] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, hazard_id, goal_id = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.child_name or rng.choice(pool)
    helper_type = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    stuffed_friend = rng.choice(STUFFED)

    return StoryParams(
        theme=theme_id,
        hazard=hazard_id,
        goal=goal_id,
        fix=fix,
        child_name=name,
        child_gender=gender,
        helper_type=helper_type,
        child_trait=trait,
        stuffed_friend=stuffed_friend,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    hazard = HAZARDS[params.hazard]
    goal = GOALS[params.goal]
    if not hazard_at_risk(hazard, goal):
        raise StoryError(explain_rejection(hazard, goal))
    if FIXES[params.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(params.fix))

    world = tell(
        THEMES[params.theme],
        hazard,
        goal,
        FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        child_trait=params.child_trait,
        stuffed_friend=params.stuffed_friend,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, hazard, goal) combos:\n")
        for theme, hazard, goal in combos:
            print(f"  {theme:10} {hazard:12} {goal}")
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
            header = f"### {p.child_name}: {p.hazard} to {p.goal} ({p.theme}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
