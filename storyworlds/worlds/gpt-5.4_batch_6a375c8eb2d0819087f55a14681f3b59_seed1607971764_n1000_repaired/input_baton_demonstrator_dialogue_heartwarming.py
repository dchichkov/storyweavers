#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/input_baton_demonstrator_dialogue_heartwarming.py
============================================================================

A standalone story world about a child demonstrator in a cozy club who learns
how kind, orderly input can help a room feel brave and warm.

Every generated story includes the words "input", "baton", and "demonstrator".
The world model tracks a small social situation:

- a child volunteers to be the demonstrator
- the room grows noisy because everyone wants to help
- a speaking baton organizes turns
- one small piece of input at a time lets the demonstration succeed
- the ending image shows the room changed: calmer, kinder, and proud together

Run it
------
    python storyworlds/worlds/gpt-5.4/input_baton_demonstrator_dialogue_heartwarming.py
    python storyworlds/worlds/gpt-5.4/input_baton_demonstrator_dialogue_heartwarming.py --demo seed_cup --audience circle --baton plush --trait shy
    python storyworlds/worlds/gpt-5.4/input_baton_demonstrator_dialogue_heartwarming.py --demo seed_cup --audience circle --baton ribbon --trait shy
    python storyworlds/worlds/gpt-5.4/input_baton_demonstrator_dialogue_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/input_baton_demonstrator_dialogue_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/input_baton_demonstrator_dialogue_heartwarming.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Domain registries
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
class Demo:
    id: str
    label: str
    article: str
    opening: str
    action: str
    object_phrase: str
    finish_image: str
    clarity_need: int
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
class Audience:
    id: str
    place: str
    size_word: str
    buzz: int
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
class Baton:
    id: str
    label: str
    phrase: str
    texture: str
    order: int
    passing: str
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
class Trait:
    id: str
    adjective: str
    courage: int
    line: str
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
class Helper:
    id: str
    kind: str
    label: str
    opening: str
    reassurance: str
    closing: str
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


DEMOS = {
    "paper_fan": Demo(
        id="paper_fan",
        label="paper fan",
        article="a paper fan",
        opening="show everyone how to fold a paper fan",
        action="creased the paper into little hills and valleys",
        object_phrase="the bright square of paper",
        finish_image="small fans fluttered like tiny wings all around the table",
        clarity_need=1,
        tags={"paper", "demonstration"},
    ),
    "seed_cup": Demo(
        id="seed_cup",
        label="seed cup",
        article="a seed cup",
        opening="show everyone how to plant a seed in a little paper cup",
        action="scooped soil, tucked in the seed, and patted the top smooth",
        object_phrase="the little cup of soil",
        finish_image="three little cups sat by the window, each waiting for a green sprout",
        clarity_need=2,
        tags={"seed", "plant", "demonstration"},
    ),
    "button_bracelet": Demo(
        id="button_bracelet",
        label="button bracelet",
        article="a button bracelet",
        opening="show everyone how to lace buttons onto yarn to make a bracelet",
        action="threaded the yarn through the shiny buttons one by one",
        object_phrase="the soft blue yarn",
        finish_image="round button bracelets circled little wrists and clicked softly together",
        clarity_need=2,
        tags={"bracelet", "craft", "demonstration"},
    ),
}

AUDIENCES = {
    "pair": Audience(
        id="pair",
        place="the sunny reading nook",
        size_word="two children",
        buzz=1,
        opening="Only two children sat close enough to see every finger move.",
        ending="The reading nook felt almost like a secret little team.",
        tags={"small_group"},
    ),
    "table": Audience(
        id="table",
        place="the round art table",
        size_word="four children",
        buzz=2,
        opening="A small table of children leaned forward with bright, ready faces.",
        ending="The round art table glowed with the pleased hush of careful work.",
        tags={"group"},
    ),
    "circle": Audience(
        id="circle",
        place="the rug by the window",
        size_word="six children",
        buzz=3,
        opening="A whole circle of children gathered on the rug, knees tucked under and eyes shining.",
        ending="The rug by the window felt full of soft pride and shared excitement.",
        tags={"large_group"},
    ),
}

BATONS = {
    "ribbon": Baton(
        id="ribbon",
        label="ribbon baton",
        phrase="a ribbon baton",
        texture="with a satin tail that swished when it moved",
        order=1,
        passing="The ribbon baton moved from hand to hand like a quiet little promise.",
        tags={"baton"},
    ),
    "star": Baton(
        id="star",
        label="star baton",
        phrase="a star baton",
        texture="with a yellow paper star on the top",
        order=2,
        passing="The star baton passed slowly around the circle, and each child waited for the sparkle to reach them.",
        tags={"baton"},
    ),
    "plush": Baton(
        id="plush",
        label="plush baton",
        phrase="a plush baton",
        texture="soft as a toy and easy to hold",
        order=3,
        passing="The plush baton went around with such calm little turns that even the busiest hands grew still.",
        tags={"baton"},
    ),
}

TRAITS = {
    "shy": Trait(
        id="shy",
        adjective="shy",
        courage=1,
        line="tucked the words close at first",
        tags={"feelings"},
    ),
    "steady": Trait(
        id="steady",
        adjective="steady",
        courage=2,
        line="took one slow breath and remembered the first step",
        tags={"feelings"},
    ),
    "sunny": Trait(
        id="sunny",
        adjective="sunny",
        courage=3,
        line="smiled even when lots of eyes turned kindly toward them",
        tags={"feelings"},
    ),
}

HELPERS = {
    "teacher": Helper(
        id="teacher",
        kind="teacher",
        label="Ms. June",
        opening="Ms. June had made the room feel gentle all morning.",
        reassurance='"One kind piece of input at a time," Ms. June said. "That helps a demonstrator hear the room."',
        closing="Ms. June's smile made the whole room feel safe enough to try.",
        tags={"teacher", "helper"},
    ),
    "grandpa": Helper(
        id="grandpa",
        kind="man",
        label="Grandpa Lou",
        opening="Grandpa Lou, the visiting demonstrator helper, sat nearby with his warm, crinkly eyes.",
        reassurance='"Slow is strong," Grandpa Lou said. "One kind piece of input at a time, and our demonstrator can shine."',
        closing="Grandpa Lou gave the smallest nod, the kind that said he believed in everybody.",
        tags={"grandparent", "helper"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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
        clone.history = list(self.history)
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


def _r_noise_shakes(world: World) -> list[str]:
    demo_child = world.get("child")
    audience = world.get("audience")
    out: list[str] = []
    if audience.meters["noise"] < THRESHOLD:
        return out
    if demo_child.memes["courage"] >= 2:
        return out
    sig = ("shaken", demo_child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    demo_child.memes["wobble"] += 1
    demo_child.memes["fear"] += 1
    world.history.append("noise_shook_demonstrator")
    out.append("__wobble__")
    return out


def _r_baton_orders(world: World) -> list[str]:
    baton = world.get("baton")
    audience = world.get("audience")
    child = world.get("child")
    out: list[str] = []
    if baton.meters["in_use"] < THRESHOLD:
        return out
    sig = ("baton_order", baton.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    audience.meters["order"] += baton.attrs["order"]
    audience.meters["noise"] = max(0.0, audience.meters["noise"] - baton.attrs["order"])
    child.memes["focus"] += 1
    child.memes["belonging"] += 1
    world.history.append("baton_brought_order")
    out.append("__order__")
    return out


def _r_good_input_progress(world: World) -> list[str]:
    child = world.get("child")
    audience = world.get("audience")
    project = world.get("project")
    need = world.facts["clarity_need"]
    out: list[str] = []
    if audience.meters["order"] < THRESHOLD or child.memes["focus"] < THRESHOLD:
        return out
    sig = ("progress", project.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["progress"] += need
    child.memes["confidence"] += 1
    child.memes["joy"] += 1
    audience.memes["trust"] += 1
    world.history.append("kind_input_helped_progress")
    out.append("__progress__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_shakes", tag="social", apply=_r_noise_shakes),
    Rule(name="baton_orders", tag="social", apply=_r_baton_orders),
    Rule(name="good_input_progress", tag="social", apply=_r_good_input_progress),
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


# ---------------------------------------------------------------------------
# Constraints / ASP mirror
# ---------------------------------------------------------------------------
def support_score(demo_id: str, audience_id: str, baton_id: str, trait_id: str) -> int:
    demo = DEMOS[demo_id]
    audience = AUDIENCES[audience_id]
    baton = BATONS[baton_id]
    trait = TRAITS[trait_id]
    return baton.order + trait.courage - (demo.clarity_need + audience.buzz - 1)


def organized_enough(demo_id: str, audience_id: str, baton_id: str, trait_id: str) -> bool:
    return support_score(demo_id, audience_id, baton_id, trait_id) >= 0


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for demo_id in DEMOS:
        for audience_id in AUDIENCES:
            for baton_id in BATONS:
                for trait_id in TRAITS:
                    if organized_enough(demo_id, audience_id, baton_id, trait_id):
                        combos.append((demo_id, audience_id, baton_id, trait_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    margin = support_score(params.demo, params.audience, params.baton, params.trait)
    return "leads" if margin >= 2 else "grows"


def explain_rejection(demo: Demo, audience: Audience, baton: Baton, trait: Trait) -> str:
    need = demo.clarity_need + audience.buzz - 1
    got = baton.order + trait.courage
    return (
        f"(No story: {demo.article} needs calm, clear turns in {audience.place}. "
        f"A {trait.adjective} demonstrator with {baton.phrase} only has support {got}, "
        f"but this situation needs at least {need}. Try a stronger baton, a calmer setting, "
        f"or a steadier demonstrator.)"
    )


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity, demo: Demo, audience: Audience) -> None:
    world.say(
        f"On a warm afternoon in {audience.place}, {child.id} was chosen to be the demonstrator. "
        f"{helper.attrs['opening']}"
    )
    world.say(
        f"{audience.opening} Today {child.pronoun()} would {demo.opening}."
    )
    world.say(
        f'{helper.label} said, "Our demonstrator today is {child.id}. We will help with kind eyes and kind words."'
    )


def ready_child(world: World, child: Entity, demo: Demo, trait: Trait) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} stood beside {demo.object_phrase} and {trait.line}. "
        f"{child.pronoun().capitalize()} wanted to do well."
    )


def crowd_input(world: World, child: Entity, audience: Entity, demo: Demo) -> None:
    audience.meters["noise"] += audience.attrs["buzz"]
    audience.memes["eagerness"] += 1
    world.history.append("room_burst_with_input")
    propagate(world, narrate=False)
    world.say(
        f'Before {child.id} could begin, hands popped up and voices tumbled together. '
        f'"Use more!" one child said. "No, fold it first!" said another. '
        f'All that input came at once, and the room felt suddenly too full.'
    )
    if child.memes["wobble"] >= THRESHOLD:
        world.say(
            f"{child.id}'s shoulders drew in a little. For a moment, {child.pronoun()} forgot the next step."
        )
    else:
        world.say(
            f"{child.id} blinked, then held still, trying to keep the first step safe in {child.pronoun('possessive')} mind."
        )


def offer_baton(world: World, child: Entity, helper: Entity, baton: Entity) -> None:
    world.say(
        f'{helper.attrs["reassurance"]} Then {helper.label} lifted {baton.attrs["phrase"]} {baton.attrs["texture"]}.'
    )
    world.say(
        f'"Whoever holds the baton may speak," {helper.label} said. "One idea, then we pass it on."'
    )


def child_accepts_plan(world: World, child: Entity, helper: Entity, baton: Entity) -> None:
    child.memes["trust"] += 1
    line = (
        f'"I can try again," {child.id} said softly.'
        if child.memes["wobble"] >= THRESHOLD
        else f'''"That will help me hear," {child.id} said."'''
    )
    world.say(line)
    world.say(
        f"{child.pronoun().capitalize()} took {baton.attrs['phrase']} with both hands and looked around at the waiting faces."
    )


def use_baton(world: World, child: Entity, audience: Entity, baton: Entity) -> None:
    baton.meters["in_use"] += 1
    world.history.append("baton_started")
    propagate(world, narrate=False)
    world.say(baton.attrs["passing"])
    world.say(
        f'One child held it and said, "Maybe tuck that corner in." Another whispered, "Your cup looks just right." '
        f'The input was smaller now, and kinder too.'
    )


def demonstrate(world: World, child: Entity, demo: Demo, helper: Entity) -> None:
    project = world.get("project")
    if project.meters["progress"] < world.facts["clarity_need"]:
        raise StoryError("(Story logic error: the demonstration did not become clear enough to finish.)")
    child.memes["pride"] += 1
    project.meters["finished"] += 1
    world.history.append("demo_finished")
    world.say(
        f"Now {child.id} could speak in a clear little voice. {child.pronoun().capitalize()} {demo.action}, "
        f"and everyone could follow along."
    )
    if world.facts["outcome"] == "leads":
        world.say(
            f'"See?" {child.id} said, smiling this time. "The tiny step comes first."'
        )
    else:
        world.say(
            f'{helper.label} stayed close, but {child.id} did the important showing. '
            f'"I remembered," {child.pronoun()} said, sounding braver than before.'
        )


def ending(world: World, child: Entity, helper: Entity, demo: Demo, audience: Audience) -> None:
    child.memes["belonging"] += 1
    child.memes["love"] += 1
    world.say(
        f"When the demonstration was done, the children did not clap loudly at first. "
        f"They smiled at {child.id} the way people smile when they are proud and careful at the same time."
    )
    world.say(
        f'{helper.label} said, "Thank you, demonstrator. Your calm helped all of us learn."'
    )
    world.say(
        f"{demo.finish_image} {audience.ending}"
    )
    world.say(
        f"{child.id} passed the baton to the next small hand and did not look quite so small anymore."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    demo: str
    audience: str
    baton: str
    trait: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None
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


CURATED = [
    StoryParams(
        demo="paper_fan",
        audience="pair",
        baton="ribbon",
        trait="steady",
        helper="teacher",
        name="Lily",
        gender="girl",
    ),
    StoryParams(
        demo="seed_cup",
        audience="table",
        baton="star",
        trait="shy",
        helper="teacher",
        name="Ben",
        gender="boy",
    ),
    StoryParams(
        demo="button_bracelet",
        audience="circle",
        baton="plush",
        trait="steady",
        helper="grandpa",
        name="Maya",
        gender="girl",
    ),
    StoryParams(
        demo="seed_cup",
        audience="circle",
        baton="plush",
        trait="sunny",
        helper="teacher",
        name="Leo",
        gender="boy",
    ),
    StoryParams(
        demo="paper_fan",
        audience="table",
        baton="star",
        trait="steady",
        helper="grandpa",
        name="Nora",
        gender="girl",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "input": [
        (
            "What does input mean when children are working together?",
            "Input means an idea or suggestion that someone offers to help. Kind input is easier to use when people take turns instead of all talking at once.",
        )
    ],
    "baton": [
        (
            "What is a speaking baton for?",
            "A speaking baton is an object people pass around to help everyone take turns. It reminds the group that one voice speaks at a time and the others listen.",
        )
    ],
    "demonstrator": [
        (
            "What does a demonstrator do?",
            "A demonstrator shows other people how to do something step by step. The job is not only making the thing, but helping others see the order of the steps.",
        )
    ],
    "seed": [
        (
            "What does a seed need after it is planted?",
            "A seed needs soil, water, and time. When it has what it needs, it can begin to sprout and grow.",
        )
    ],
    "paper": [
        (
            "Why does folding paper carefully matter?",
            "Careful folds help the paper hold its shape. When the folds line up, the finished craft works better and looks neat.",
        )
    ],
    "bracelet": [
        (
            "Why do people thread beads or buttons one by one?",
            "Going one by one keeps the string from tangling and helps the pattern stay in order. Slow hands often make stronger little crafts.",
        )
    ],
    "teacher": [
        (
            "How can a teacher help a nervous child speak?",
            "A teacher can slow the room down, give clear turn-taking rules, and use a calm voice. That helps the child feel safe enough to try.",
        )
    ],
    "grandparent": [
        (
            "Why can a grandparent helper feel comforting?",
            "A gentle grandparent often brings patience and warmth. That can make a child feel less rushed and more brave.",
        )
    ],
}
KNOWLEDGE_ORDER = ["input", "baton", "demonstrator", "seed", "paper", "bracelet", "teacher", "grandparent"]


def generation_prompts(world: World) -> list[str]:
    demo = world.facts["demo"]
    child = world.facts["child"]
    helper = world.facts["helper_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the words "input", "baton", and "demonstrator".',
        f"Tell a gentle classroom story where {child.id} is the demonstrator for {demo.article}, the room gets too eager, and a baton helps everyone give kind input one turn at a time.",
        f"Write a dialogue-rich story about a child who almost loses confidence while demonstrating {demo.label}, but a caring {helper.id} helps the whole group slow down and listen.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    demo = world.facts["demo"]
    audience_cfg = world.facts["audience_cfg"]
    baton_cfg = world.facts["baton_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child chosen to be the demonstrator, and {helper_cfg.label}, who helped the room slow down. The other children mattered too because their eagerness created the problem and later helped solve it.",
        ),
        (
            f"What was {child.id} trying to show?",
            f"{child.id} was trying to show everyone how to make {demo.article}. The demonstration mattered because the other children wanted to follow the steps too.",
        ),
        (
            "Why did the room become hard for the demonstrator at first?",
            f"The children were excited and gave input all at once, so the room suddenly felt noisy and crowded. That made it harder for {child.id} to hold onto the next step.",
        ),
        (
            "How did the baton help?",
            f"The {baton_cfg.label} turned many voices into turns, so only one child spoke at a time. That calmer order helped {child.id} focus and continue the demonstration.",
        ),
    ]
    if outcome == "leads":
        qa.append(
            (
                f"How did {child.id} feel by the end?",
                f"{child.id} felt proud and calm by the end. The room's kind turn-taking let {child.pronoun('object')} lead the steps instead of shrinking away from the attention.",
            )
        )
    else:
        qa.append(
            (
                f"What changed for {child.id} during the story?",
                f"At first {child.id} felt small and wobbly when the input came too fast. After the baton slowed the room down, {child.pronoun()} remembered the steps and sounded braver.",
            )
        )
    qa.append(
        (
            "What proves the ending was heartwarming?",
            f"The children listened carefully, learned together, and smiled at the demonstrator with quiet pride. The last image of {child.id} passing the baton on shows that the room had become kinder and more confident together.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    demo = world.facts["demo"]
    helper_cfg = world.facts["helper_cfg"]
    tags = {"input", "baton", "demonstrator"} | set(demo.tags) | set(helper_cfg.tags)
    if "plant" in tags:
        tags.add("seed")
    if "paper" in tags:
        tags.add("paper")
    if "bracelet" in tags or "craft" in tags:
        tags.add("bracelet")
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
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
support(D,A,B,T, BO + CO - (CN + BU - 1)) :-
    demo(D), audience(A), baton(B), trait(T),
    baton_order(B, BO), courage(T, CO),
    clarity_need(D, CN), buzz(A, BU).

valid(D,A,B,T) :- support(D,A,B,T,S), S >= 0.
outcome(D,A,B,T,leads) :- support(D,A,B,T,S), S >= 2.
outcome(D,A,B,T,grows) :- support(D,A,B,T,S), S >= 0, S < 2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for demo_id, demo in DEMOS.items():
        lines.append(asp.fact("demo", demo_id))
        lines.append(asp.fact("clarity_need", demo_id, demo.clarity_need))
    for audience_id, audience in AUDIENCES.items():
        lines.append(asp.fact("audience", audience_id))
        lines.append(asp.fact("buzz", audience_id, audience.buzz))
    for baton_id, baton in BATONS.items():
        lines.append(asp.fact("baton", baton_id))
        lines.append(asp.fact("baton_order", baton_id, baton.order))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("courage", trait_id, trait.courage))
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
            asp.fact("chosen_demo", params.demo),
            asp.fact("chosen_audience", params.audience),
            asp.fact("chosen_baton", params.baton),
            asp.fact("chosen_trait", params.trait),
            "selected_outcome(O) :- chosen_demo(D), chosen_audience(A), chosen_baton(B), chosen_trait(T), outcome(D,A,B,T,O).",
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show selected_outcome/1."))
    outs = asp.atoms(model, "selected_outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(40):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child demonstrator, eager input, and a speaking baton."
    )
    ap.add_argument("--demo", choices=DEMOS)
    ap.add_argument("--audience", choices=AUDIENCES)
    ap.add_argument("--baton", choices=BATONS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.demo and args.audience and args.baton and args.trait:
        if not organized_enough(args.demo, args.audience, args.baton, args.trait):
            raise StoryError(
                explain_rejection(
                    DEMOS[args.demo],
                    AUDIENCES[args.audience],
                    BATONS[args.baton],
                    TRAITS[args.trait],
                )
            )

    combos = [
        c
        for c in valid_combos()
        if (args.demo is None or c[0] == args.demo)
        and (args.audience is None or c[1] == args.audience)
        and (args.baton is None or c[2] == args.baton)
        and (args.trait is None or c[3] == args.trait)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    demo_id, audience_id, baton_id, trait_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    return StoryParams(
        demo=demo_id,
        audience=audience_id,
        baton=baton_id,
        trait=trait_id,
        helper=helper_id,
        name=name,
        gender=gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        demo = DEMOS[params.demo]
        audience = AUDIENCES[params.audience]
        baton = BATONS[params.baton]
        trait = TRAITS[params.trait]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter key: {err})") from err

    if not organized_enough(params.demo, params.audience, params.baton, params.trait):
        raise StoryError(explain_rejection(demo, audience, baton, trait))

    world = tell(
        demo=demo,
        audience_cfg=audience,
        baton_cfg=baton,
        trait=trait,
        helper_cfg=helper,
        child_name=params.name,
        child_gender=params.gender,
    )
    world.facts["outcome"] = outcome_of(params)
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (demo, audience, baton, trait) combos:\n")
        for demo_id, audience_id, baton_id, trait_id in combos:
            print(f"  {demo_id:16} {audience_id:8} {baton_id:7} {trait_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.demo} with {p.baton} in {p.audience} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def tell(
    demo: Demo,
    audience_cfg: Audience,
    baton_cfg: Baton,
    trait: Trait,
    helper_cfg: Helper,
    child_name: str,
    child_gender: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="demonstrator",
            traits=[trait.adjective],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_cfg.kind,
            label=helper_cfg.label,
            role="helper",
            attrs={
                "opening": helper_cfg.opening,
                "reassurance": helper_cfg.reassurance,
                "closing": helper_cfg.closing,
            },
        )
    )
    audience = world.add(
        Entity(
            id="audience",
            kind="thing",
            type="group",
            label="the group",
            role="audience",
            attrs={"buzz": audience_cfg.buzz},
        )
    )
    baton = world.add(
        Entity(
            id="baton",
            kind="thing",
            type="baton",
            label=baton_cfg.label,
            role="baton",
            attrs={
                "order": baton_cfg.order,
                "phrase": baton_cfg.phrase,
                "texture": baton_cfg.texture,
                "passing": baton_cfg.passing,
            },
        )
    )
    project = world.add(
        Entity(
            id="project",
            kind="thing",
            type="project",
            label=demo.label,
            role="project",
        )
    )

    child.memes["courage"] = float(trait.courage)
    child.memes["focus"] = 0.0
    child.memes["wobble"] = 0.0
    child.memes["fear"] = 0.0
    audience.meters["noise"] = 0.0
    audience.meters["order"] = 0.0
    project.meters["progress"] = 0.0
    project.meters["finished"] = 0.0
    baton.meters["in_use"] = 0.0

    world.facts.update(
        demo=demo,
        audience_cfg=audience_cfg,
        baton_cfg=baton_cfg,
        trait=trait,
        helper_cfg=helper_cfg,
        child=child,
        helper=helper,
        audience=audience,
        baton=baton,
        project=project,
        clarity_need=demo.clarity_need,
    )

    introduce(world, child, helper, demo, audience_cfg)
    ready_child(world, child, demo, trait)

    world.para()
    crowd_input(world, child, audience, demo)
    offer_baton(world, child, helper, baton)
    child_accepts_plan(world, child, helper, baton)

    world.para()
    use_baton(world, child, audience, baton)
    demonstrate(world, child, demo, helper)
    ending(world, child, helper, demo, audience_cfg)

    world.facts["outcome"] = "leads" if child.memes["confidence"] >= THRESHOLD and support_score(
        demo.id, audience_cfg.id, baton_cfg.id, trait.id
    ) >= 2 else "grows"
    return world


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
