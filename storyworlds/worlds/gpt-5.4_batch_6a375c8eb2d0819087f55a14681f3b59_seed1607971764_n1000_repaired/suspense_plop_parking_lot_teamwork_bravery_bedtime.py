#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/suspense_plop_parking_lot_teamwork_bravery_bedtime.py
================================================================================

A standalone story world for a soft bedtime-style parking-lot suspense tale:
a child's beloved bedtime item goes *plop* into a puddle and skids under a
parked car, and the children must use teamwork and bravery to solve the problem
safely.

The domain is intentionally small and constraint-checked. A story is only
generated when the chosen recovery plan is genuinely safe and capable for the
kind of darkness, the depth under the vehicle, and the shape of the lost item.

Run it
------
    python storyworlds/worlds/gpt-5.4/suspense_plop_parking_lot_teamwork_bravery_bedtime.py
    python storyworlds/worlds/gpt-5.4/suspense_plop_parking_lot_teamwork_bravery_bedtime.py --item bunny --vehicle minivan --time night --plan flashlight_grabber
    python storyworlds/worlds/gpt-5.4/suspense_plop_parking_lot_teamwork_bravery_bedtime.py --plan crawl_under
    python storyworlds/worlds/gpt-5.4/suspense_plop_parking_lot_teamwork_bravery_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/suspense_plop_parking_lot_teamwork_bravery_bedtime.py --qa --json
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
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
class LostItem:
    id: str
    label: str
    phrase: str
    bedtime_use: str
    hookable: bool
    soft: bool
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
class Vehicle:
    id: str
    label: str
    phrase: str
    depth: int
    shadow: str
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
class TimeOfDay:
    id: str
    label: str
    opening: str
    sky: str
    dark: bool
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
class Plan:
    id: str
    label: str
    sense: int
    reach: int
    gives_light: bool
    works_for_unhookable: bool
    teamwork_text: str
    retrieval_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child", "helper"}]

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


def _r_hidden_suspense(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("hidden_suspense",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["suspense"] += 1
        kid.memes["worry"] += 1
    world.get("parent").memes["focus"] += 1
    return ["__suspense__"]


def _r_teamwork_recover(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["hidden"] < THRESHOLD:
        return []
    if not world.facts.get("plan_safe", False):
        return []
    if not world.facts.get("plan_capable", False):
        return []
    if world.facts.get("team_ready", 0.0) < THRESHOLD:
        return []
    sig = ("recover",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["hidden"] = 0.0
    item.meters["recovered"] += 1
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["bravery"] += 1
        kid.memes["teamwork"] += 1
        kid.memes["worry"] = 0.0
    world.get("parent").memes["relief"] += 1
    return ["__recovered__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hidden_suspense", tag="emotion", apply=_r_hidden_suspense),
    Rule(name="teamwork_recover", tag="physical", apply=_r_teamwork_recover),
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
        for s in produced:
            world.say(s)
    return produced


ITEMS = {
    "bunny": LostItem(
        id="bunny",
        label="bunny",
        phrase="a small sleepy bunny plush",
        bedtime_use="to tuck under one small chin at bedtime",
        hookable=True,
        soft=True,
        tags={"bunny", "bedtime_item"},
    ),
    "storybook": LostItem(
        id="storybook",
        label="storybook",
        phrase="a picture storybook with moonlit pages",
        bedtime_use="to read before the last yawn",
        hookable=False,
        soft=False,
        tags={"storybook", "bedtime_item"},
    ),
    "pajama_bag": LostItem(
        id="pajama_bag",
        label="pajama bag",
        phrase="a little bag with striped pajamas inside",
        bedtime_use="to carry cozy pajamas for getting ready for bed",
        hookable=True,
        soft=True,
        tags={"pajamas", "bedtime_item"},
    ),
}

VEHICLES = {
    "sedan": Vehicle(
        id="sedan",
        label="sedan",
        phrase="a parked sedan",
        depth=1,
        shadow="a short dark strip beneath the car",
        tags={"car"},
    ),
    "minivan": Vehicle(
        id="minivan",
        label="minivan",
        phrase="a parked minivan",
        depth=2,
        shadow="a long dim tunnel beneath the van",
        tags={"car"},
    ),
    "pickup": Vehicle(
        id="pickup",
        label="pickup",
        phrase="a parked pickup truck",
        depth=2,
        shadow="a wide shadow beneath the truck",
        tags={"car"},
    ),
}

TIMES = {
    "dusk": TimeOfDay(
        id="dusk",
        label="dusk",
        opening="At the edge of bedtime, when the shops were closing and the lamps were waking up,",
        sky="The sky was violet and soft.",
        dark=False,
        tags={"dusk"},
    ),
    "night": TimeOfDay(
        id="night",
        label="night",
        opening="Near bedtime, when the parking lot had grown quiet and dark,",
        sky="The sky was deep blue, and the painted lines glimmered under the lamps.",
        dark=True,
        tags={"night"},
    ),
}

PLANS = {
    "flashlight_grabber": Plan(
        id="flashlight_grabber",
        label="flashlight and grabber",
        sense=3,
        reach=3,
        gives_light=True,
        works_for_unhookable=True,
        teamwork_text="One child held the flashlight steady while the other pointed to the right tire, and their grown-up guided the long grabber into the shadow.",
        retrieval_text="The grabber slid in, paused, and then came back with the lost thing safe in its gentle jaws.",
        qa_text="They used a flashlight for light and a long grabber to reach safely under the car.",
        tags={"flashlight", "grabber", "parking_lot_safety"},
    ),
    "umbrella_hook": Plan(
        id="umbrella_hook",
        label="umbrella hook",
        sense=2,
        reach=2,
        gives_light=False,
        works_for_unhookable=False,
        teamwork_text="Their grown-up knelt by the bumper with a closed umbrella while the children stood close together and pointed to the little gleam under the car.",
        retrieval_text="With one careful pull, the umbrella's curved handle coaxed the lost thing back across the pavement.",
        qa_text="They used the curved handle of a closed umbrella to hook the item and pull it back safely.",
        tags={"umbrella", "parking_lot_safety"},
    ),
    "crawl_under": Plan(
        id="crawl_under",
        label="crawl under the car",
        sense=1,
        reach=1,
        gives_light=False,
        works_for_unhookable=True,
        teamwork_text="",
        retrieval_text="",
        qa_text="",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Eli", "Noah", "Finn", "Theo", "Jack", "Owen"]
TRAITS = ["careful", "brave", "gentle", "steady", "thoughtful", "kind"]


def plan_is_capable(item: LostItem, vehicle: Vehicle, when: TimeOfDay, plan: Plan) -> bool:
    if plan.reach < vehicle.depth:
        return False
    if when.dark and not plan.gives_light:
        return False
    if not item.hookable and not plan.works_for_unhookable:
        return False
    return True


def plan_is_safe(plan: Plan) -> bool:
    return plan.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for item_id, item in ITEMS.items():
        for vehicle_id, vehicle in VEHICLES.items():
            for time_id, when in TIMES.items():
                for plan_id, plan in PLANS.items():
                    if plan_is_safe(plan) and plan_is_capable(item, vehicle, when, plan):
                        combos.append((item_id, vehicle_id, time_id, plan_id))
    return combos


@dataclass
class StoryParams:
    item: str
    vehicle: str
    time: str
    plan: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent: str
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


CURATED = [
    StoryParams(
        item="bunny",
        vehicle="sedan",
        time="dusk",
        plan="umbrella_hook",
        child_name="Lily",
        child_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="mother",
        trait="gentle",
    ),
    StoryParams(
        item="storybook",
        vehicle="minivan",
        time="night",
        plan="flashlight_grabber",
        child_name="Max",
        child_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        parent="father",
        trait="steady",
    ),
    StoryParams(
        item="pajama_bag",
        vehicle="pickup",
        time="night",
        plan="flashlight_grabber",
        child_name="Nora",
        child_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        parent="mother",
        trait="brave",
    ),
    StoryParams(
        item="bunny",
        vehicle="minivan",
        time="dusk",
        plan="flashlight_grabber",
        child_name="Theo",
        child_gender="boy",
        helper_name="Ava",
        helper_gender="girl",
        parent="father",
        trait="kind",
    ),
]


def explain_plan_rejection(plan: Plan) -> str:
    return (
        f"(Refusing plan '{plan.id}': it scores too low on common sense "
        f"(sense={plan.sense} < {SENSE_MIN}). In a parking lot, the story only allows safe recovery plans.)"
    )


def explain_combo_rejection(item: LostItem, vehicle: Vehicle, when: TimeOfDay, plan: Plan) -> str:
    reasons: list[str] = []
    if plan.reach < vehicle.depth:
        reasons.append(f"{plan.label} cannot reach far enough under the {vehicle.label}")
    if when.dark and not plan.gives_light:
        reasons.append("the parking lot is too dark for that plan")
    if not item.hookable and not plan.works_for_unhookable:
        reasons.append(f"{item.label} is not a good shape for {plan.label}")
    if not reasons:
        reasons.append("that combination does not make a reasonable story")
    return "(No story: " + "; ".join(reasons) + ".)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    item = f["item_cfg"]
    vehicle = f["vehicle_cfg"]
    when = f["time_cfg"]
    plan = f["plan_cfg"]
    return [
        'Write a bedtime story for a 3-to-5-year-old set in a parking lot that includes the words "suspense" and "plop".',
        f"Tell a gentle suspense story where {child.id}'s {item.label} slips under {vehicle.phrase} at {when.label}, and {child.id}, {helper.id}, and their {f['parent'].label_word} solve it with teamwork and bravery.",
        f"Write a soft nighttime story where a family uses {plan.label} to get a bedtime item back safely, ending with everyone calmer than before.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    parent = f["parent"]
    item = f["item_cfg"]
    vehicle = f["vehicle_cfg"]
    when = f["time_cfg"]
    plan = f["plan_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {helper.id}, and their {parent.label_word} in a parking lot near bedtime. They were trying to get {child.id}'s {item.label} back safely.",
        ),
        (
            f"Why did the story feel full of suspense?",
            f"It felt full of suspense because {item.label} slipped under {vehicle.phrase}, where the children could not easily see or reach it. The quiet parking lot and the dark shadow under the vehicle made the moment feel bigger and more mysterious.",
        ),
        (
            f"What happened with a plop?",
            f"{child.id}'s {item.label} fell into a puddle with a plop and slid away under the parked vehicle. That little sound was the start of the whole problem.",
        ),
        (
            f"How were teamwork and bravery shown in the story?",
            f"{child.id} and {helper.id} were brave because they did not rush into the shadow or crawl under the car. They worked as a team with their {parent.label_word}, each doing a small helpful part until the item came back.",
        ),
        (
            f"How did they get the {item.label} back?",
            f"{plan.qa_text} {helper.id} helped by pointing carefully, and {child.id} stayed close and steady. Because they used a safe plan together, the lost thing was recovered without anyone taking a risky step.",
        ),
        (
            "How did the story end?",
            f"It ended quietly and safely, with the {item.label} back where it belonged and everyone's worry settling down. The ending proves that the brave choice was the careful one.",
        ),
    ]
    if when.dark:
        qa.append(
            (
                "Why did the darkness matter?",
                f"The darkness mattered because it made it harder to see under the vehicle. That is why a plan with light was important for a safe ending."
                if plan.gives_light
                else f"The darkness made the shadow under the vehicle feel harder to judge, which is why the family had to move very carefully.",
            )
        )
    return qa


KNOWLEDGE = {
    "parking_lot_safety": [
        (
            "Why should children stay close to a grown-up in a parking lot?",
            "Parking lots have cars that can move, turn, or back up, so children should stay close to a grown-up who can watch carefully. Safe walking in a parking lot means staying together.",
        )
    ],
    "flashlight": [
        (
            "What does a flashlight help you do?",
            "A flashlight helps you see into dark places without putting your hands there first. Good light makes careful choices easier.",
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool with little jaws on the end that can pick something up from far away. It lets a grown-up reach safely without crawling under things.",
        )
    ],
    "umbrella": [
        (
            "How can a closed umbrella sometimes help pick something up?",
            "A closed umbrella has a curved handle that can sometimes hook a soft or looped item and slide it back. It should be used slowly and only by a grown-up in a safe way.",
        )
    ],
    "bunny": [
        (
            "Why do some children sleep with a stuffed bunny?",
            "A stuffed bunny can feel cozy and familiar at bedtime. Holding something soft can help a child feel calm and ready to rest.",
        )
    ],
    "storybook": [
        (
            "Why do people read storybooks before bed?",
            "Storybooks can help bedtime feel gentle and calm. A quiet story gives the mind a soft place to land before sleep.",
        )
    ],
    "pajamas": [
        (
            "Why do pajamas matter at bedtime?",
            "Pajamas are soft clothes for sleeping, and putting them on can help the body know it is time to settle down. Bedtime routines make the end of the day feel safe and familiar.",
        )
    ],
}

KNOWLEDGE_ORDER = ["parking_lot_safety", "flashlight", "grabber", "umbrella", "bunny", "storybook", "pajamas"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["plan_cfg"].tags) | set(f["item_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  world facts: plan_safe={world.facts.get('plan_safe')} plan_capable={world.facts.get('plan_capable')} team_ready={world.facts.get('team_ready')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def predict_recovery(world: World) -> dict:
    sim = world.copy()
    sim.facts["team_ready"] = 1.0
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "recovered": item.meters["recovered"] >= THRESHOLD,
        "hidden": item.meters["hidden"] >= THRESHOLD,
    }


def open_scene(world: World, child: Entity, helper: Entity, parent: Entity, when: TimeOfDay, item: LostItem) -> None:
    world.say(
        f"{when.opening} {child.id}, {helper.id}, and their {parent.label_word} crossed the parking lot after one last errand."
    )
    world.say(when.sky)
    world.say(
        f"{child.id} carried {item.phrase}, the one {child.pronoun('subject')} liked {item.bedtime_use}."
    )


def lose_item(world: World, child: Entity, item: LostItem, vehicle: Vehicle) -> None:
    obj = world.get("item")
    obj.meters["wet"] += 1
    obj.meters["hidden"] += 1
    propagate(world, narrate=False)
    splash = "softly" if item.soft else "flat and sudden"
    world.say(
        f"Then {child.id}'s fingers loosened for just a blink. Down went the {item.label} with a plop into a rain puddle, {splash}, and it skidded under {vehicle.phrase}."
    )
    world.say(
        f"It disappeared into {vehicle.shadow}. A little ripple of suspense moved through all three of them."
    )


def unsafe_idea(world: World, child: Entity, helper: Entity, vehicle: Vehicle) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"{child.id} took one quick step toward the dark space, ready to crouch and reach. But {helper.id} touched {child.pronoun('possessive')} sleeve and whispered, \"Wait. It's too dark under the {vehicle.label}.\""
    )


def brave_pause(world: World, child: Entity, helper: Entity, parent: Entity) -> None:
    child.memes["bravery"] += 1
    helper.memes["bravery"] += 1
    helper.memes["teamwork"] += 1
    child.memes["teamwork"] += 1
    world.say(
        f"The bravest thing turned out not to be rushing. {child.id} stopped, took a breath, and stayed beside {parent.label_word} while {helper.id} kept watch on the little puddle trail."
    )


def choose_plan(world: World, parent: Entity, plan: Plan, when: TimeOfDay) -> None:
    if when.dark and plan.gives_light:
        world.say(
            f'"We will do this the careful way," their {parent.label_word} said. "First, we need light."'
        )
    else:
        world.say(
            f'"We will do this the careful way," their {parent.label_word} said.'
        )
    world.say(plan.teamwork_text)
    world.facts["team_ready"] = 1.0
    propagate(world, narrate=False)


def recover_item(world: World, child: Entity, helper: Entity, item: LostItem, plan: Plan) -> None:
    if world.get("item").meters["recovered"] < THRESHOLD:
        raise StoryError("(Internal story error: the recovery plan did not recover the item.)")
    world.say(plan.retrieval_text)
    world.say(
        f'"There it is!" {helper.id} breathed. {child.id} held the {item.label} close, and the tight feeling in {child.pronoun("possessive")} chest softened at once.'
    )


def closing(world: World, child: Entity, helper: Entity, parent: Entity, item: LostItem, when: TimeOfDay) -> None:
    child.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f'Their {parent.label_word} dabbed off the little drops and smiled. "That was good teamwork," {parent.pronoun()} said. "And good bravery too."'
    )
    if item.id == "storybook":
        world.say(
            f"Soon they were buckled in, with the storybook safe on {child.id}'s lap, ready to open once they were home."
        )
    elif item.id == "pajama_bag":
        world.say(
            f"Soon they were buckled in, and the pajama bag rested safely by {child.id}'s feet, waiting for warm lights and sleepy clothes."
        )
    else:
        world.say(
            f"Soon they were buckled in, and the bunny rode home in {child.id}'s arms like a small moonlit secret."
        )
    tail = "The parking lot no longer felt full of suspense." if when.dark else "The quiet parking lot felt ordinary again."
    world.say(
        f"{tail} The careful plan had brought everyone back to calm."
    )


def tell(
    item_cfg: LostItem,
    vehicle_cfg: Vehicle,
    time_cfg: TimeOfDay,
    plan_cfg: Plan,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={"careful": trait in {"careful", "steady", "thoughtful"}},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=["watchful"],
            attrs={"watchful": True},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
            attrs={"parking_lot": True},
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="lost_item",
            label=item_cfg.label,
            attrs={"hookable": item_cfg.hookable, "soft": item_cfg.soft},
        )
    )
    world.add(
        Entity(
            id="vehicle",
            kind="thing",
            type="vehicle",
            label=vehicle_cfg.label,
            attrs={"depth": vehicle_cfg.depth},
        )
    )
    world.facts.update(
        child=child,
        helper=helper,
        parent=parent,
        item_cfg=item_cfg,
        vehicle_cfg=vehicle_cfg,
        time_cfg=time_cfg,
        plan_cfg=plan_cfg,
        plan_safe=plan_is_safe(plan_cfg),
        plan_capable=plan_is_capable(item_cfg, vehicle_cfg, time_cfg, plan_cfg),
        team_ready=0.0,
    )

    open_scene(world, child, helper, parent, time_cfg, item_cfg)
    world.para()
    lose_item(world, child, item_cfg, vehicle_cfg)
    unsafe_idea(world, child, helper, vehicle_cfg)
    brave_pause(world, child, helper, parent)

    prediction = predict_recovery(world)
    world.facts["predicted_recovery"] = prediction["recovered"]

    world.para()
    choose_plan(world, parent, plan_cfg, time_cfg)
    recover_item(world, child, helper, item_cfg, plan_cfg)

    world.para()
    closing(world, child, helper, parent, item_cfg, time_cfg)
    world.facts["recovered"] = world.get("item").meters["recovered"] >= THRESHOLD
    world.facts["suspense"] = child.memes["suspense"] >= THRESHOLD or helper.memes["suspense"] >= THRESHOLD
    return world


ASP_RULES = r"""
safe_plan(P) :- plan(P), sense(P,S), sense_min(M), S >= M.

capable(I,V,T,P) :- item(I), vehicle(V), time(T), plan(P),
                    reach(P,R), depth(V,D), R >= D,
                    dark(T), gives_light(P),
                    not_hookable(I), works_for_unhookable(P).
capable(I,V,T,P) :- item(I), vehicle(V), time(T), plan(P),
                    reach(P,R), depth(V,D), R >= D,
                    dark(T), gives_light(P),
                    hookable(I).
capable(I,V,T,P) :- item(I), vehicle(V), time(T), plan(P),
                    reach(P,R), depth(V,D), R >= D,
                    not dark(T),
                    not_hookable(I), works_for_unhookable(P).
capable(I,V,T,P) :- item(I), vehicle(V), time(T), plan(P),
                    reach(P,R), depth(V,D), R >= D,
                    not dark(T),
                    hookable(I).

valid(I,V,T,P) :- item(I), vehicle(V), time(T), plan(P), safe_plan(P), capable(I,V,T,P).

chosen_valid :- chosen_item(I), chosen_vehicle(V), chosen_time(T), chosen_plan(P), valid(I,V,T,P).
outcome(recovered) :- chosen_valid.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.hookable:
            lines.append(asp.fact("hookable", item_id))
        else:
            lines.append(asp.fact("not_hookable", item_id))
    for vehicle_id, vehicle in VEHICLES.items():
        lines.append(asp.fact("vehicle", vehicle_id))
        lines.append(asp.fact("depth", vehicle_id, vehicle.depth))
    for time_id, when in TIMES.items():
        lines.append(asp.fact("time", time_id))
        if when.dark:
            lines.append(asp.fact("dark", time_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("reach", plan_id, plan.reach))
        if plan.gives_light:
            lines.append(asp.fact("gives_light", plan_id))
        if plan.works_for_unhookable:
            lines.append(asp.fact("works_for_unhookable", plan_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_vehicle", params.vehicle),
            asp.fact("chosen_time", params.time),
            asp.fact("chosen_plan", params.plan),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    item = ITEMS[params.item]
    vehicle = VEHICLES[params.vehicle]
    when = TIMES[params.time]
    plan = PLANS[params.plan]
    return "recovered" if plan_is_safe(plan) and plan_is_capable(item, vehicle, when, plan) else "invalid"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    cases = list(CURATED)
    for s in range(40):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: ASP outcomes match Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bedtime item slips under a parked car, and teamwork plus bravery solve the problem safely."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--time", choices=TIMES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan:
        plan = PLANS[args.plan]
        if not plan_is_safe(plan):
            raise StoryError(explain_plan_rejection(plan))
    if args.item and args.vehicle and args.time and args.plan:
        item = ITEMS[args.item]
        vehicle = VEHICLES[args.vehicle]
        when = TIMES[args.time]
        plan = PLANS[args.plan]
        if not (plan_is_safe(plan) and plan_is_capable(item, vehicle, when, plan)):
            raise StoryError(explain_combo_rejection(item, vehicle, when, plan))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.vehicle is None or combo[1] == args.vehicle)
        and (args.time is None or combo[2] == args.time)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, vehicle_id, time_id, plan_id = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=child_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        vehicle=vehicle_id,
        time=time_id,
        plan=plan_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle: {params.vehicle})")
    if params.time not in TIMES:
        raise StoryError(f"(Unknown time: {params.time})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    item = ITEMS[params.item]
    vehicle = VEHICLES[params.vehicle]
    when = TIMES[params.time]
    plan = PLANS[params.plan]
    if not plan_is_safe(plan):
        raise StoryError(explain_plan_rejection(plan))
    if not plan_is_capable(item, vehicle, when, plan):
        raise StoryError(explain_combo_rejection(item, vehicle, when, plan))

    world = tell(
        item_cfg=item,
        vehicle_cfg=vehicle,
        time_cfg=when,
        plan_cfg=plan,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, vehicle, time, plan) combos:\n")
        for item, vehicle, time_id, plan in combos:
            print(f"  {item:10} {vehicle:8} {time_id:5} {plan}")
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
            header = f"### {p.child_name} & {p.helper_name}: {p.item} under {p.vehicle} at {p.time} ({p.plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
