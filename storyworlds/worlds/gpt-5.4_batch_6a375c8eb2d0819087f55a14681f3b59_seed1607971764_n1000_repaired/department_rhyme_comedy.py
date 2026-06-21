#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/department_rhyme_comedy.py
====================================================

A standalone story world about a child in a department store, a silly rhyme,
and a comic little mix-up in one tempting department.

The core tale:
- a child and grown-up visit a department store for an ordinary errand
- one funny department lures the child with a rhyming attraction
- the child slips away and causes a small comic commotion
- a store clerk helps with a sensible, rhyming search
- they reunite, help tidy up, and leave with a new rule: stay close in the store

This world keeps the shape small and child-facing, but it is still a real
simulation:
- typed entities with physical meters and emotional memes
- state-driven prose
- a Python reasonableness gate
- an inline ASP twin for parity checks
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
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | thing | place
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "clerk_f"}
        male = {"boy", "father", "uncle", "man", "clerk_m"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain config
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
class Department:
    id: str
    label: str
    article: str
    scenery: str
    errand: str
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
class Attraction:
    id: str
    department: str
    label: str
    phrase: str
    effect: str
    rhyme_call: str
    rhyme_reply: str
    commotion: int
    noise: int
    clutter: int
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    messy_text: str
    qa_text: str
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


def _r_missing_worry(world: World) -> list[str]:
    child = world.get("child")
    guardian = world.get("guardian")
    clerk = world.get("clerk")
    if child.meters["separated"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guardian.memes["worry"] += 1
    clerk.memes["notice"] += 1
    return []


def _r_commotion_attention(world: World) -> list[str]:
    dept = world.get("department")
    guardian = world.get("guardian")
    clerk = world.get("clerk")
    if dept.meters["commotion"] < THRESHOLD:
        return []
    sig = ("commotion_attention",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guardian.memes["flustered"] += 1
    clerk.memes["helpful"] += 1
    return []


def _r_reunion_relief(world: World) -> list[str]:
    child = world.get("child")
    guardian = world.get("guardian")
    if child.meters["found"] < THRESHOLD:
        return []
    sig = ("reunion_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    guardian.memes["relief"] += 1
    guardian.memes["worry"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="commotion_attention", tag="social", apply=_r_commotion_attention),
    Rule(name="reunion_relief", tag="social", apply=_r_reunion_relief),
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
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_pair(department: Department, attraction: Attraction) -> bool:
    return attraction.department == department.id


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def search_severity(attraction: Attraction, delay: int) -> int:
    return attraction.commotion + delay


def found_neatly(response: Response, attraction: Attraction, delay: int) -> bool:
    return response.power >= search_severity(attraction, delay)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for dept_id, dept in DEPARTMENTS.items():
        for attr_id, attr in ATTRACTIONS.items():
            if valid_pair(dept, attr):
                combos.append((dept_id, attr_id))
    return combos


def explain_pair_rejection(department: Department, attraction: Attraction) -> str:
    return (
        f"(No story: {attraction.phrase} does not belong in the {department.label}. "
        f"It belongs in the {DEPARTMENTS[attraction.department].label}, so that mix-up "
        f"would not make sense in this little world.)"
    )


def explain_response_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of the sensible helpers: {better}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_search(world: World, attraction_id: str) -> dict:
    sim = world.copy()
    attraction = ATTRACTIONS[attraction_id]
    dept = sim.get("department")
    child = sim.get("child")
    dept.meters["commotion"] += attraction.commotion
    dept.meters["noise"] += attraction.noise
    dept.meters["clutter"] += attraction.clutter
    child.meters["separated"] += 1
    propagate(sim, narrate=False)
    return {
        "commotion": dept.meters["commotion"],
        "noise": dept.meters["noise"],
        "clutter": dept.meters["clutter"],
        "worry": sim.get("guardian").memes["worry"],
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, guardian: Entity, department: Department) -> None:
    child.memes["glee"] += 1
    world.say(
        f"On a bright Saturday, {child.id} went with {child.pronoun('possessive')} "
        f"{guardian.label_word} to the big department store."
    )
    world.say(
        f"They were only there for {department.errand}, but the {department.label} "
        f"was glowing nearby. {department.scenery}"
    )


def tempt(world: World, child: Entity, guardian: Entity, attraction: Attraction, department: Department) -> None:
    pred = predict_search(world, attraction.id)
    world.facts["predicted_commotion"] = int(pred["commotion"])
    world.facts["predicted_worry"] = int(pred["worry"])
    world.say(
        f'From the {department.label} came a silly little call: "{attraction.rhyme_call}"'
    )
    world.say(
        f'{child.id} answered without even thinking, "{attraction.rhyme_reply}" '
        f'and giggled so hard {child.pronoun()} had to clap.'
    )
    world.say(
        f'{guardian.label_word.capitalize()} smiled, then said, "Stay beside me, side by side."'
    )


def slip_away(world: World, child: Entity, guardian: Entity, attraction: Attraction) -> None:
    child.meters["separated"] += 1
    child.memes["mischief"] += 1
    child.memes["glee"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the rhyme pulled at {child.id} like a kite string. While "
        f"{guardian.label_word} checked the shopping list, {child.id} tiptoed "
        f"one aisle over to see {attraction.phrase}."
    )


def mishap(world: World, child: Entity, attraction: Attraction) -> None:
    dept = world.get("department")
    dept.meters["commotion"] += attraction.commotion
    dept.meters["noise"] += attraction.noise
    dept.meters["clutter"] += attraction.clutter
    child.memes["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} only meant to peek, but {attraction.effect}. "
        f"In one blink the whole aisle felt funny and busy."
    )


def alarm(world: World, child: Entity, guardian: Entity, attraction: Attraction, department: Department) -> None:
    noise_word = "racket" if attraction.noise >= 2 else "rustle"
    world.say(
        f'{guardian.label_word.capitalize()} looked up at the {noise_word} and said, '
        f'"{child.id}?"'
    )
    if world.get("guardian").memes["worry"] >= THRESHOLD:
        world.say(
            f"When there was no answer right away, {guardian.label_word} hurried to the "
            f"{department.label}, with a worried face and the crinkly shopping list still in hand."
        )


def search_help(world: World, clerk: Entity, response: Response, attraction: Attraction, department: Department) -> None:
    clerk.memes["helpful"] += 1
    world.say(
        f"A kind store clerk in a bright vest heard the commotion and {response.text}."
    )
    world.say(
        f'The rhyme bounced all through the {department.label}: '
        f'"{attraction.rhyme_call}"'
    )


def reunite_neat(
    world: World,
    child: Entity,
    guardian: Entity,
    clerk: Entity,
    response: Response,
    attraction: Attraction,
    department: Department,
) -> None:
    child.meters["found"] += 1
    child.meters["separated"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f'From behind {attraction.phrase}, {child.id} answered, "{attraction.rhyme_reply}"'
    )
    world.say(
        f"{guardian.label_word.capitalize()} followed the sound and scooped {child.id} into a hug "
        f"before the aisle could get any sillier."
    )
    world.say(
        f"Together they straightened the {department.article} things that had tipped, and the clerk "
        f"grinned because the whole rescue had taken less than a minute."
    )


def reunite_messy(
    world: World,
    child: Entity,
    guardian: Entity,
    clerk: Entity,
    response: Response,
    attraction: Attraction,
    department: Department,
) -> None:
    child.meters["found"] += 1
    child.meters["separated"] = 0.0
    world.get("department").meters["extra_mess"] += 1
    child.memes["embarrassed"] += 1
    propagate(world, narrate=False)
    world.say(response.messy_text.format(child=child.id, item=attraction.label))
    world.say(
        f"At last the clerk spotted {child.id} kneeling in the middle of the {department.label}, "
        f"trying very hard to put things back the neat way."
    )
    world.say(
        f"{guardian.label_word.capitalize()} reached {child.id}, hugged {child.pronoun('object')}, "
        f"and then all three of them tidied the aisle together while laughing at the ridiculous little mix-up."
    )


def lesson_and_end(
    world: World,
    child: Entity,
    guardian: Entity,
    clerk: Entity,
    department: Department,
    attraction: Attraction,
    neat: bool,
) -> None:
    child.memes["lesson"] += 1
    child.memes["glee"] += 1
    guardian.memes["love"] += 1
    child.memes["love"] += 1
    if neat:
        world.say(
            f'"Next time," said {guardian.label_word}, tapping the shopping cart gently, '
            f'"store and more, floor and door, stay close in every department store."'
        )
    else:
        world.say(
            f'"Next time," said {guardian.label_word}, brushing a laugh out of {child.id}\'s hair, '
            f'"store and more, floor and door, stay close in every department store."'
        )
    world.say(
        f'{child.id} nodded and made up a new rhyme of {child.pronoun('possessive')} own: '
        f'"Near and dear, I stay right here."'
    )
    if department.id == "hats":
        ending = "The clerk let the child carry one flat hat box to the counter like a grand parade prize."
    elif department.id == "linens":
        ending = "At the end, they rolled away with soft towels stacked neatly again, like sleepy clouds in a cart."
    else:
        ending = "At the end, they rolled away with the robot turned off, the aisle calm again, and everybody smiling."
    world.say(
        f"Then they finished the errand together. {ending}"
    )
    world.facts["ending_image"] = ending


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    department: Department,
    attraction: Attraction,
    response: Response,
    child_name: str = "Mia",
    child_gender: str = "girl",
    guardian_type: str = "mother",
    clerk_type: str = "clerk_f",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        attrs={"likes_rhymes": True},
    ))
    guardian = world.add(Entity(
        id="Guardian",
        kind="character",
        type=guardian_type,
        role="guardian",
        label="the grown-up",
    ))
    clerk = world.add(Entity(
        id="Clerk",
        kind="character",
        type=clerk_type,
        role="clerk",
        label="the clerk",
    ))
    dept_ent = world.add(Entity(
        id="department",
        kind="place",
        type="department",
        label=department.label,
    ))
    attraction_ent = world.add(Entity(
        id="attraction",
        kind="thing",
        type="display",
        label=attraction.label,
    ))

    # Initialize meters/memes that rules read before propagation.
    child.meters["separated"] = 0.0
    child.meters["found"] = 0.0
    child.memes["glee"] = 0.0
    child.memes["mischief"] = 0.0
    child.memes["surprise"] = 0.0
    child.memes["embarrassed"] = 0.0
    child.memes["lesson"] = 0.0
    child.memes["love"] = 0.0

    guardian.memes["worry"] = 0.0
    guardian.memes["flustered"] = 0.0
    guardian.memes["relief"] = 0.0
    guardian.memes["love"] = 0.0

    clerk.memes["notice"] = 0.0
    clerk.memes["helpful"] = 0.0

    dept_ent.meters["commotion"] = 0.0
    dept_ent.meters["noise"] = 0.0
    dept_ent.meters["clutter"] = 0.0
    dept_ent.meters["extra_mess"] = 0.0

    world.facts.update(
        child=child,
        guardian=guardian,
        clerk=clerk,
        department_cfg=department,
        attraction_cfg=attraction,
        response=response,
        delay=delay,
    )

    introduce(world, child, guardian, department)
    world.para()
    tempt(world, child, guardian, attraction, department)
    slip_away(world, child, guardian, attraction)
    mishap(world, child, attraction)
    alarm(world, child, guardian, attraction, department)

    # Delay deepens the comic tangle without changing the underlying departments.
    if delay > 0:
        world.get("department").meters["commotion"] += delay
        world.get("department").meters["clutter"] += delay
        child.memes["surprise"] += delay
        guardian.memes["flustered"] += delay

    neat = found_neatly(response, attraction, delay)
    world.facts["severity"] = search_severity(attraction, delay)
    world.facts["outcome"] = "neat" if neat else "messy"

    world.para()
    search_help(world, clerk, response, attraction, department)
    if neat:
        reunite_neat(world, child, guardian, clerk, response, attraction, department)
    else:
        reunite_messy(world, child, guardian, clerk, response, attraction, department)

    world.para()
    lesson_and_end(world, child, guardian, clerk, department, attraction, neat)
    world.facts["reunited"] = True
    world.facts["commotion"] = int(world.get("department").meters["commotion"])
    world.facts["clutter"] = int(world.get("department").meters["clutter"])
    world.facts["child_helped_tidy"] = True
    world.facts["attraction_ent"] = attraction_ent
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
DEPARTMENTS = {
    "toys": Department(
        id="toys",
        label="toy department",
        article="toy-department",
        scenery="Tin drums winked from one shelf, and a row of robots stood as still as cookies waiting for milk.",
        errand="plain socks and a pack of washcloths",
        tags={"department_store", "toys"},
    ),
    "hats": Department(
        id="hats",
        label="hat department",
        article="hat-department",
        scenery="Round boxes were piled like little moons, and floppy brims leaned over the racks as if they were listening.",
        errand="plain socks and a new dish towel",
        tags={"department_store", "hats"},
    ),
    "linens": Department(
        id="linens",
        label="linen department",
        article="linen-department",
        scenery="Towel towers stood in soft stripes of lemon, mint, and cloud-white.",
        errand="plain socks and a pack of napkins",
        tags={"department_store", "linens"},
    ),
}

ATTRACTIONS = {
    "robot": Attraction(
        id="robot",
        department="toys",
        label="a beeping robot",
        phrase="a beeping robot with shiny red buttons",
        effect="one curious tap woke a robot chorus, and soon three toy robots were peeping, marching, and bumping their cardboard feet",
        rhyme_call="beepy robot, tiny tot",
        rhyme_reply="I can hear your beep-beep bop",
        commotion=2,
        noise=2,
        clutter=1,
        tags={"robot", "intercom", "stay_close"},
    ),
    "feather_hat": Attraction(
        id="feather_hat",
        department="hats",
        label="a feather hat stand",
        phrase="a feather hat stand with a wobbling top shelf",
        effect="the top hat box slid, three feathered hats flopped down, and one purple plume landed right on the child's head",
        rhyme_call="hatty chatter, feather flitter",
        rhyme_reply="Here I am, a giggle-sitter",
        commotion=2,
        noise=1,
        clutter=2,
        tags={"hats", "stay_close"},
    ),
    "towel_tower": Attraction(
        id="towel_tower",
        department="linens",
        label="a towel tower",
        phrase="a towel tower folded into a neat rainbow",
        effect="the bottom towel scooted free and the whole tower went whoof, poof, and floof across the floor",
        rhyme_call="towel tower, floofy flower",
        rhyme_reply="I'm right here this very hour",
        commotion=3,
        noise=1,
        clutter=2,
        tags={"towels", "stay_close"},
    ),
}

RESPONSES = {
    "intercom_rhyme": Response(
        id="intercom_rhyme",
        sense=3,
        power=4,
        text="lifted the intercom microphone and called in a warm sing-song voice",
        messy_text="{child} heard the call but answered from the far end of the aisle, which only made the boxes and {item} wobble some more.",
        qa_text="used the store intercom and a friendly rhyme to guide the child back",
        tags={"intercom", "department_store"},
    ),
    "cart_bell": Response(
        id="cart_bell",
        sense=2,
        power=3,
        text="jingled the service cart bell in a steady little rhythm and added a silly rhyme",
        messy_text="The bell helped a little, but {child} followed the sound in loops and zigzags before peeking out beside {item}.",
        qa_text="rang the service bell and used a rhyme so the child could follow the sound",
        tags={"bell", "department_store"},
    ),
    "shoe_squeak": Response(
        id="shoe_squeak",
        sense=2,
        power=2,
        text="asked everyone to pause and listen for the child's squeaky sneakers, then called the rhyme line softly",
        messy_text="{child} tried to tiptoe back, but each squeak sent {child} in another funny direction around {item}.",
        qa_text="listened for the child's squeaky shoes and followed the sounds",
        tags={"shoes", "stay_close"},
    ),
    "guessing_game": Response(
        id="guessing_game",
        sense=1,
        power=1,
        text="started a guessing game in the middle of the aisle",
        messy_text="{child} guessed and giggled, but the guessing only delayed things.",
        qa_text="played a guessing game",
        tags={"game"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Noah", "Sam", "Eli", "Finn"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    department: str
    attraction: str
    response: str
    child_name: str
    child_gender: str
    guardian: str
    clerk: str
    delay: int = 0
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


KNOWLEDGE = {
    "department_store": [
        (
            "What is a department store?",
            "A department store is a big shop with different sections for different kinds of things, like toys, clothes, or towels. Each section is called a department."
        )
    ],
    "intercom": [
        (
            "What does an intercom do in a store?",
            "An intercom lets a person speak through speakers around the store. It helps everyone hear a message at the same time."
        )
    ],
    "robot": [
        (
            "Why can toy robots make a store aisle noisy?",
            "Toy robots can beep, blink, and move all at once. When several start together, the aisle can sound much louder than one small toy."
        )
    ],
    "hats": [
        (
            "Why do hats fall over easily on a stand?",
            "Hats can tip if the stack gets bumped because they are light and round. A wobbly box or brim can make the whole stand look crooked."
        )
    ],
    "towels": [
        (
            "Why does a towel tower fall when one towel is pulled from the bottom?",
            "The towels on top need the bottom ones to hold them up. If one lower towel slides out, the stack can slump or tumble."
        )
    ],
    "stay_close": [
        (
            "Why should children stay close to a grown-up in a big store?",
            "Big stores have many aisles and corners, so it is easy to get separated. Staying close helps everyone shop safely and find each other quickly."
        )
    ],
    "bell": [
        (
            "Why can a bell help someone find the right direction?",
            "A clear bell sound can be heard from far away. Listening to where it is loudest can help you move toward it."
        )
    ],
    "shoes": [
        (
            "How can squeaky shoes help someone find a person?",
            "Squeaky shoes make a repeating sound each time a person steps. If the room is quiet enough, people can follow the sound."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "department_store",
    "intercom",
    "robot",
    "hats",
    "towels",
    "stay_close",
    "bell",
    "shoes",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    department = f["department_cfg"]
    attraction = f["attraction_cfg"]
    outcome = f["outcome"]
    if outcome == "messy":
        return [
            f'Write a funny rhyming story for a 3-to-5-year-old set in a department store. Include the word "department".',
            f"Tell a comedy where {child.id} slips into the {department.label}, causes a silly little mess around {attraction.label}, and is found with help from {guardian.label_word} and a clerk.",
            f"Write a short story with playful rhyme, a department-store mix-up, and an ending where everyone laughs, tidies up, and learns to stay close.",
        ]
    return [
        f'Write a funny rhyming story for a 3-to-5-year-old set in a department store. Include the word "department".',
        f"Tell a gentle comedy where {child.id} follows a silly rhyme into the {department.label}, and a kind clerk helps {guardian.label_word} find the child quickly.",
        f"Write a short story with rhyme, one comic department-store problem, and a warm ending that shows what the child learned.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    clerk = f["clerk"]
    department = f["department_cfg"]
    attraction = f["attraction_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {guardian.label_word}, and a helpful store clerk. They are all in a big department store together."
        ),
        (
            "What tempted the child to wander into the department?",
            f"{attraction.phrase.capitalize()} and the silly rhyme from the {department.label} tempted {child.id}. The rhyme made the aisle feel like a game instead of an ordinary errand."
        ),
        (
            "Why did the grown-up get worried?",
            f"{guardian.label_word.capitalize()} got worried because {child.id} slipped one aisle away and could not be seen right away. The commotion in the {department.label} made the separation feel bigger and more urgent."
        ),
    ]
    if outcome == "neat":
        qa.extend([
            (
                "How did the clerk help find the child?",
                f"The clerk {response.qa_text}. That worked quickly because the sound or rhyme gave {child.id} a clear way to answer back."
            ),
            (
                "What changed by the end of the story?",
                f"At the end, {child.id} was back beside {guardian.label_word} instead of wandering alone. The child also learned a new rule about staying close in a department store."
            ),
        ])
    else:
        qa.extend([
            (
                "Did the mix-up stay neat or become messy?",
                f"It became a messy little comedy before it was solved. The helper worked, but not fast enough to stop extra wobbling and clutter in the {department.label}."
            ),
            (
                "How was the problem solved in the end?",
                f"{guardian.label_word.capitalize()}, the clerk, and {child.id} found one another and tidied the aisle together. Helping clean up turned the silly mistake into a lesson instead of just a scolding."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = (
        set(world.facts["department_cfg"].tags)
        | set(world.facts["attraction_cfg"].tags)
        | set(world.facts["response"].tags)
    )
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        department="toys",
        attraction="robot",
        response="intercom_rhyme",
        child_name="Mia",
        child_gender="girl",
        guardian="mother",
        clerk="clerk_f",
        delay=0,
    ),
    StoryParams(
        department="hats",
        attraction="feather_hat",
        response="cart_bell",
        child_name="Ben",
        child_gender="boy",
        guardian="father",
        clerk="clerk_m",
        delay=0,
    ),
    StoryParams(
        department="linens",
        attraction="towel_tower",
        response="shoe_squeak",
        child_name="Zoe",
        child_gender="girl",
        guardian="aunt",
        clerk="clerk_f",
        delay=1,
    ),
    StoryParams(
        department="toys",
        attraction="robot",
        response="cart_bell",
        child_name="Leo",
        child_gender="boy",
        guardian="uncle",
        clerk="clerk_m",
        delay=1,
    ),
]


# ---------------------------------------------------------------------------
# Outcome helpers
# ---------------------------------------------------------------------------
def outcome_of(params: StoryParams) -> str:
    return (
        "neat"
        if found_neatly(RESPONSES[params.response], ATTRACTIONS[params.attraction], params.delay)
        else "messy"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Reasonableness: an attraction belongs only in its home department.
valid(D, A) :- department(D), attraction(A), home(A, D).

% Sensible helpers.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% Outcome: neat if the helper power meets the search severity.
severity(C + Delay) :- chosen_attraction(A), commotion(A, C), delay(Delay).
helper_power(P) :- chosen_response(R), power(R, P).
outcome(neat) :- helper_power(P), severity(S), P >= S.
outcome(messy) :- helper_power(P), severity(S), P < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for dept_id in DEPARTMENTS:
        lines.append(asp.fact("department", dept_id))
    for attr_id, attr in ATTRACTIONS.items():
        lines.append(asp.fact("attraction", attr_id))
        lines.append(asp.fact("home", attr_id, attr.department))
        lines.append(asp.fact("commotion", attr_id, attr.commotion))
    for resp_id, resp in RESPONSES.items():
        lines.append(asp.fact("response", resp_id))
        lines.append(asp.fact("sense", resp_id, resp.sense))
        lines.append(asp.fact("power", resp_id, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_attraction", params.attraction),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    clingo_resp = set(asp_sensible())
    python_resp = {r.id for r in sensible_responses()}
    if clingo_resp == python_resp:
        print(f"OK: sensible responses match ({sorted(clingo_resp)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_resp)} python={sorted(python_resp)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke test ordinary generation + emit.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comic rhyming department-store storyworld. Unspecified choices are selected at random (seeded)."
    )
    ap.add_argument("--department", choices=DEPARTMENTS)
    ap.add_argument("--attraction", choices=ATTRACTIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--guardian", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--clerk", choices=["clerk_f", "clerk_m"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how much extra comic delay happens before the child is found")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.department and args.attraction:
        dept = DEPARTMENTS[args.department]
        attr = ATTRACTIONS[args.attraction]
        if not valid_pair(dept, attr):
            raise StoryError(explain_pair_rejection(dept, attr))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(args.response))

    combos = [
        pair
        for pair in valid_combos()
        if (args.department is None or pair[0] == args.department)
        and (args.attraction is None or pair[1] == args.attraction)
    ]
    if not combos:
        raise StoryError("(No valid department/attraction combination matches the given options.)")

    department_id, attraction_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father", "aunt", "uncle"])
    clerk = args.clerk or rng.choice(["clerk_f", "clerk_m"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1, 2])

    return StoryParams(
        department=department_id,
        attraction=attraction_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        guardian=guardian,
        clerk=clerk,
        delay=delay,
    )


def _validated_lookup(mapping: dict, key: str, field_name: str):
    if key not in mapping:
        raise StoryError(f"(No story: unknown {field_name} '{key}'.)")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    department = _validated_lookup(DEPARTMENTS, params.department, "department")
    attraction = _validated_lookup(ATTRACTIONS, params.attraction, "attraction")
    response = _validated_lookup(RESPONSES, params.response, "response")

    if not valid_pair(department, attraction):
        raise StoryError(explain_pair_rejection(department, attraction))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response_rejection(params.response))

    world = tell(
        department=department,
        attraction=attraction,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        guardian_type=params.guardian,
        clerk_type=params.clerk,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (department, attraction) combos:\n")
        for department, attraction in combos:
            print(f"  {department:8} {attraction}")
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
            header = (
                f"### {p.child_name}: {p.attraction} in {p.department} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
