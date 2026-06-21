#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mower_trooper_develop_curiosity_rhyming_story.py
============================================================================

A standalone story world about a child's curiosity during yard work.

This tiny domain models a child who hears a loud mower, grows curious, and wants
to go closer or copy the grown-up's job. The world enforces a simple safety
constraint: curiosity is welcome, but the child must have a safe way to explore
it from the right distance or with the right helper tool. The turn is not
"curiosity is bad"; the turn is that good curiosity can develop into careful
learning.

Every generated story is told in a gentle rhyming style.

Run it
------
    python storyworlds/worlds/gpt-5.4/mower_trooper_develop_curiosity_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/mower_trooper_develop_curiosity_rhyming_story.py --yard garden --question engine --guide earmuffs
    python storyworlds/worlds/gpt-5.4/mower_trooper_develop_curiosity_rhyming_story.py --question blade
    python storyworlds/worlds/gpt-5.4/mower_trooper_develop_curiosity_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/mower_trooper_develop_curiosity_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mower_trooper_develop_curiosity_rhyming_story.py --verify
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
SAFE_NOISE = 1
SAFE_DISTANCE = 2


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
class Yard:
    id: str
    place: str
    ground: str
    smell: str
    afford_noise: int
    safe_spot: str
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
class Question:
    id: str
    wonder: str
    danger_focus: str
    safe_action: str
    explain: str
    needs_noise_help: bool
    needs_distance: bool
    observation: str
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
class Guide:
    id: str
    label: str
    phrase: str
    lowers_noise: int
    keeps_distance: bool
    method: str
    ending: str
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


class World:
    def __init__(self, yard: Yard) -> None:
        self.yard = yard
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
        clone = World(self.yard)
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


def _r_noise_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mower = world.get("mower")
    if mower.meters["running"] < THRESHOLD:
        return out
    if child.meters["near_mower"] < THRESHOLD:
        return out
    sig = ("noise_worry", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    exposure = mower.meters["noise"] - child.meters["ear_protection"]
    if exposure > SAFE_NOISE:
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_learning(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    grown = world.get("grown")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    if child.meters["safe_view"] < THRESHOLD:
        return out
    sig = ("learning", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["understanding"] += 1
    child.memes["confidence"] += 1
    grown.memes["pride"] += 1
    out.append("__learning__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_worry", tag="physical", apply=_r_noise_worry),
    Rule(name="learning", tag="emotional", apply=_r_learning),
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


def safe_combo(question: Question, guide: Guide) -> bool:
    if question.needs_noise_help and guide.lowers_noise <= 0:
        return False
    if question.needs_distance and not guide.keeps_distance:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for yard_id in YARDS:
        for qid, question in QUESTIONS.items():
            for gid, guide in GUIDES.items():
                if safe_combo(question, guide):
                    combos.append((yard_id, qid, gid))
    return combos


def predict_explore(world: World, question: Question, guide: Guide) -> dict:
    sim = world.copy()
    child = sim.get("child")
    mower = sim.get("mower")
    if guide.lowers_noise:
        child.meters["ear_protection"] = float(guide.lowers_noise)
    if guide.keeps_distance:
        child.meters["safe_view"] += 1
        child.meters["near_mower"] = 0.0
        mower.meters["distance_steps"] = float(SAFE_DISTANCE)
    else:
        child.meters["near_mower"] += 1
        mower.meters["distance_steps"] = 0.0
    propagate(sim, narrate=False)
    return {
        "safe": child.memes["worry"] < THRESHOLD,
        "understanding": child.memes["understanding"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, grown: Entity, toy: Entity, yard: Yard) -> None:
    world.say(
        f"In {yard.place}, where {yard.ground} lay low, "
        f"{child.id} marched with {toy.label}, all set for a show."
    )
    world.say(
        f"{grown.label_word.capitalize()} wheeled out the mower, steady and slow, "
        f"and {yard.smell} drifted up in the warm afternoon glow."
    )


def hear_mower(world: World, child: Entity, mower: Entity) -> None:
    mower.meters["running"] += 1
    mower.meters["noise"] = float(world.yard.afford_noise)
    child.memes["curiosity"] += 1
    world.say(
        f'The mower went "brrrr," with a rumbling roar, '
        f'and {child.id} blinked twice, then inched to the door.'
    )


def wonder(world: World, child: Entity, question: Question) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f'"{question.wonder}" asked {child.id}, eyes shiny and bright. '
        f'Curiosity twinkled like stars in the light.'
    )


def step_too_close(world: World, child: Entity, mower: Entity, question: Question) -> None:
    child.meters["near_mower"] += 1
    mower.meters["distance_steps"] = 0.0
    propagate(world, narrate=False)
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id} took one more step for a nearer explorer's view, "
            f"but the loud clattery thunder felt much bigger than {child.pronoun('object')} knew."
        )
    else:
        world.say(
            f"{child.id} shuffled nearer to see something new, "
            f"though {question.danger_focus} still called for a careful clue."
        )


def guide_safely(world: World, child: Entity, grown: Entity, guide: Guide, question: Question) -> None:
    if guide.lowers_noise:
        child.meters["ear_protection"] = float(guide.lowers_noise)
    if guide.keeps_distance:
        child.meters["safe_view"] += 1
        child.meters["near_mower"] = 0.0
        world.get("mower").meters["distance_steps"] = float(SAFE_DISTANCE)
    else:
        child.meters["safe_view"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{grown.label_word.capitalize()} smiled. "{guide.method}" '
        f'{grown.pronoun()} said in a voice soft and warm instead.'
    )
    world.say(
        f"They used {guide.phrase}, not a rush and not a dive, "
        f"so {child.id} could explore and still stay safe and alive."
    )
    world.say(
        f"Soon {child.id} could {question.safe_action}, and that helped a new idea develop. "
        f"Small careful questions can climb their own gentle level."
    )


def explain(world: World, child: Entity, grown: Entity, question: Question) -> None:
    child.memes["understanding"] += 1
    world.say(
        f'{grown.label_word.capitalize()} pointed and answered: "{question.explain}" '
        f'The words were simple, kind, and clear.'
    )
    world.say(
        f"{question.observation.capitalize()}, and {child.id} listened near "
        f"from the safe little place {grown.pronoun()} had chosen here."
    )


def resolve(world: World, child: Entity, toy: Entity, guide: Guide, question: Question) -> None:
    child.memes["joy"] += 1
    child.memes["curiosity"] = 0.0
    child.memes["worry"] = 0.0
    world.say(
        f"Back marched the toy trooper with {child.id} in a row, "
        f"practicing {guide.ending} where daisies might grow."
    )
    world.say(
        f"{child.id} did not grab the mower or dash too close to see. "
        f"Instead {child.pronoun()} learned that careful curiosity can be brave as can be."
    )


def tell(
    yard: Yard,
    question: Question,
    guide: Guide,
    child_name: str = "Nora",
    child_type: str = "girl",
    grown_type: str = "mother",
    trait: str = "curious",
    toy_name: str = "the tin trooper",
) -> World:
    world = World(yard)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        traits=[trait],
        role="child",
    ))
    grown = world.add(Entity(
        id="grown",
        kind="character",
        type=grown_type,
        label="the grown-up",
        role="grown",
    ))
    toy = world.add(Entity(
        id="toy",
        kind="thing",
        type="toy",
        label=toy_name,
        role="toy",
    ))
    mower = world.add(Entity(
        id="mower",
        kind="thing",
        type="mower",
        label="the mower",
        role="machine",
    ))

    child.meters["ear_protection"] = 0.0
    child.meters["near_mower"] = 0.0
    child.meters["safe_view"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["understanding"] = 0.0
    child.memes["confidence"] = 0.0
    child.memes["joy"] = 0.0
    mower.meters["running"] = 0.0
    mower.meters["noise"] = 0.0
    mower.meters["distance_steps"] = float(SAFE_DISTANCE)
    grown.memes["pride"] = 0.0

    world.facts["yard"] = yard
    world.facts["question_cfg"] = question
    world.facts["guide_cfg"] = guide
    world.facts["child"] = child
    world.facts["grown"] = grown
    world.facts["toy"] = toy
    world.facts["mower"] = mower

    opening(world, child, grown, toy, yard)
    hear_mower(world, child, mower)

    world.para()
    wonder(world, child, question)
    step_too_close(world, child, mower, question)

    world.para()
    guide_safely(world, child, grown, guide, question)
    explain(world, child, grown, question)

    world.para()
    resolve(world, child, toy, guide, question)

    world.facts.update(
        safe=child.memes["worry"] < THRESHOLD,
        learned=child.memes["understanding"] >= THRESHOLD,
        used_noise_help=guide.lowers_noise > 0,
        used_distance=guide.keeps_distance,
    )
    return world


YARDS = {
    "garden": Yard(
        id="garden",
        place="the garden",
        ground="little clover patches and soft green lines",
        smell="the smell of cut grass",
        afford_noise=2,
        safe_spot="the stone step",
        tags={"garden", "grass"},
    ),
    "backyard": Yard(
        id="backyard",
        place="the backyard",
        ground="apple shadows and dandelion strings",
        smell="the smell of sunny grass",
        afford_noise=2,
        safe_spot="the porch rail",
        tags={"yard", "grass"},
    ),
    "orchard_lane": Yard(
        id="orchard_lane",
        place="the side yard by the orchard lane",
        ground="pear leaves and bright green rows",
        smell="the smell of fresh stems",
        afford_noise=2,
        safe_spot="the wooden gate",
        tags={"orchard", "yard"},
    ),
}

QUESTIONS = {
    "engine": Question(
        id="engine",
        wonder="How does the mower keep making that humming sound",
        danger_focus="the noisy engine",
        safe_action="watch the engine from far away while a grown-up explains",
        explain="Inside is an engine that gives the mower power, but it is for grown-up hands only.",
        needs_noise_help=True,
        needs_distance=True,
        observation="the engine cover shook while the wheels rolled over the grass",
        tags={"engine", "mower"},
    ),
    "blade": Question(
        id="blade",
        wonder="Does the mower have teeth under there",
        danger_focus="the hidden blade",
        safe_action="look at the bottom only after the mower is off and far from the grass",
        explain="Underneath is a blade that cuts the grass, so we never go close while it is running.",
        needs_noise_help=False,
        needs_distance=True,
        observation="the grass trimmings flicked out in tiny green sprays",
        tags={"blade", "safety"},
    ),
    "tracks": Question(
        id="tracks",
        wonder="Why does the mower leave neat stripes in the grass",
        danger_focus="the path close behind the wheels",
        safe_action="stand back and follow the stripes with a finger in the air",
        explain="The wheels press one way and the cut grass bends another, which makes the stripes show.",
        needs_noise_help=False,
        needs_distance=False,
        observation="one row looked light and the next row looked deep green",
        tags={"grass", "pattern"},
    ),
}

GUIDES = {
    "earmuffs": Guide(
        id="earmuffs",
        label="earmuffs",
        phrase="a pair of soft earmuffs beside the porch rail",
        lowers_noise=2,
        keeps_distance=True,
        method="Let's wear these earmuffs and watch from the stone step while I tell you what each part does.",
        ending="straight trooper stripes with a toy wagon on the path",
        tags={"earmuffs", "hearing"},
    ),
    "chalk_map": Guide(
        id="chalk_map",
        label="chalk map",
        phrase="a chalk map on the patio showing the mower's path",
        lowers_noise=0,
        keeps_distance=True,
        method="Let's stay by the gate and draw where the mower goes, then we can talk about each turn.",
        ending="tiny trooper paths in chalk, loop by loop",
        tags={"chalk", "distance"},
    ),
    "toy_mower": Guide(
        id="toy_mower",
        label="toy mower",
        phrase="a toy mower with clicking wheels on the porch",
        lowers_noise=0,
        keeps_distance=False,
        method="Let's use your toy mower here while you watch me, and we will compare what each wheel does.",
        ending="small trooper marches behind the toy mower, clickity-clack",
        tags={"toy", "pretend"},
    ),
}


KNOWLEDGE = {
    "mower": [(
        "What is a mower?",
        "A mower is a machine grown-ups use to cut grass shorter. It has moving parts, so children should watch from a safe place instead of touching it."
    )],
    "engine": [(
        "What does an engine do?",
        "An engine gives power to a machine so it can move or work. Some engines are loud, which is why people sometimes protect their ears nearby."
    )],
    "blade": [(
        "Why should children stay away from mower blades?",
        "A mower blade spins fast and can hurt someone badly. That is why a grown-up should keep children far away while the mower is running."
    )],
    "hearing": [(
        "Why can loud sounds make you uncomfortable?",
        "Very loud sounds can make ears feel tired or upset. Ear protection helps soften the noise so listening feels safer and calmer."
    )],
    "distance": [(
        "Why is standing back safer around a machine?",
        "Standing back gives your body room away from moving parts. It also helps you watch carefully without getting in the machine's path."
    )],
    "grass": [(
        "Why does cut grass sometimes look striped?",
        "Grass can bend in different directions after the mower passes. Light hits each row a little differently, so some rows look brighter than others."
    )],
    "curiosity": [(
        "Is curiosity a good thing?",
        "Yes, curiosity is a good thing when it leads you to ask careful questions. It helps children develop new understanding while still listening to safety rules."
    )],
}
KNOWLEDGE_ORDER = ["mower", "engine", "blade", "hearing", "distance", "grass", "curiosity"]


@dataclass
class StoryParams:
    yard: str
    question: str
    guide: str
    name: str
    gender: str
    grown: str
    trait: str
    toy_name: str
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


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    question = world.facts["question_cfg"]
    guide = world.facts["guide_cfg"]
    yard = world.facts["yard"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "mower," "trooper," and "develop." Let a curious child ask about a mower in {yard.place}.',
        f"Tell a gentle story in rhyme where {child.id} feels curiosity about a mower, starts to move too close, and a grown-up helps {child.pronoun('object')} explore the question about {question.id} safely with {guide.label}.",
        "Write a child-facing poem-story where curiosity becomes careful learning instead of trouble, and end with the child playing in a new safer way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    grown = world.facts["grown"]
    question = world.facts["question_cfg"]
    guide = world.facts["guide_cfg"]
    yard = world.facts["yard"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and {child.pronoun('possessive')} {grown.label_word}, who is using the mower in {yard.place}. A little toy trooper goes along as part of the play."
        ),
        (
            f"What made {child.id} curious?",
            f"The loud mower sound and the neat work it was doing made {child.id} want to know more. {child.pronoun().capitalize()} asked about {question.danger_focus} because the machine seemed interesting and new."
        ),
        (
            f"Why did {child.id} need help instead of going closer alone?",
            f"{child.id} started edging too close to a running mower, which was not safe. The machine was loud or had moving parts, so a grown-up needed to guide the wondering in a safer way."
        ),
        (
            f"How did the grown-up help {child.id} explore the question safely?",
            f"{grown.label_word.capitalize()} used {guide.label} and a careful plan instead of letting {child.id} rush in. That way, {child.id} could keep being curious while staying back from the mower."
        ),
        (
            "What did the child learn by the end?",
            f"{child.id} learned that careful curiosity can develop into understanding. Instead of touching the mower, {child.pronoun()} listened, watched from a safe place, and then played with a safer idea afterward."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    question = world.facts["question_cfg"]
    guide = world.facts["guide_cfg"]
    tags = {"mower", "curiosity"}
    tags |= set(question.tags)
    if guide.lowers_noise:
        tags.add("hearing")
    if guide.keeps_distance:
        tags.add("distance")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        yard="garden",
        question="engine",
        guide="earmuffs",
        name="Nora",
        gender="girl",
        grown="mother",
        trait="curious",
        toy_name="the tin trooper",
    ),
    StoryParams(
        yard="backyard",
        question="blade",
        guide="chalk_map",
        name="Max",
        gender="boy",
        grown="father",
        trait="careful",
        toy_name="the brave toy trooper",
    ),
    StoryParams(
        yard="orchard_lane",
        question="tracks",
        guide="toy_mower",
        name="Lila",
        gender="girl",
        grown="mother",
        trait="wondering",
        toy_name="the pocket trooper",
    ),
]


def explain_rejection(question: Question, guide: Guide) -> str:
    if question.needs_noise_help and guide.lowers_noise <= 0:
        return (
            f"(No story: the question about {question.danger_focus} needs ear protection, "
            f"but {guide.label} does not reduce noise. Pick a guide like earmuffs.)"
        )
    if question.needs_distance and not guide.keeps_distance:
        return (
            f"(No story: the question about {question.danger_focus} needs the child kept back, "
            f"but {guide.label} does not enforce distance. Pick a guide like chalk_map or earmuffs.)"
        )
    return "(No story: this combination does not support a safe curious ending.)"


ASP_RULES = r"""
safe_combo(Q,G) :- question(Q), guide(G), not needs_noise(Q), not needs_distance(Q).
safe_combo(Q,G) :- question(Q), guide(G), needs_noise(Q), lowers_noise(G,N), N > 0, not needs_distance(Q).
safe_combo(Q,G) :- question(Q), guide(G), not needs_noise(Q), needs_distance(Q), keeps_distance(G).
safe_combo(Q,G) :- question(Q), guide(G), needs_noise(Q), lowers_noise(G,N), N > 0, needs_distance(Q), keeps_distance(G).

valid(Y,Q,G) :- yard(Y), safe_combo(Q,G).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for yard_id in YARDS:
        lines.append(asp.fact("yard", yard_id))
    for qid, question in QUESTIONS.items():
        lines.append(asp.fact("question", qid))
        if question.needs_noise_help:
            lines.append(asp.fact("needs_noise", qid))
        if question.needs_distance:
            lines.append(asp.fact("needs_distance", qid))
    for gid, guide in GUIDES.items():
        lines.append(asp.fact("guide", gid))
        lines.append(asp.fact("lowers_noise", gid, guide.lowers_noise))
        if guide.keeps_distance:
            lines.append(asp.fact("keeps_distance", gid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a child develops curiosity about a mower in a safe way."
    )
    ap.add_argument("--yard", choices=YARDS)
    ap.add_argument("--question", choices=QUESTIONS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grown", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nora", "Lila", "Mia", "Zoe", "Ava", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Max", "Leo", "Ben", "Sam", "Finn", "Theo", "Eli", "Jack"]
TRAITS = ["curious", "careful", "wondering", "bright", "thoughtful"]
TOYS = ["the tin trooper", "the brave toy trooper", "the pocket trooper", "the red trooper"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.question and args.guide:
        question = QUESTIONS[args.question]
        guide = GUIDES[args.guide]
        if not safe_combo(question, guide):
            raise StoryError(explain_rejection(question, guide))

    combos = [
        combo for combo in valid_combos()
        if (args.yard is None or combo[0] == args.yard)
        and (args.question is None or combo[1] == args.question)
        and (args.guide is None or combo[2] == args.guide)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    yard, question, guide = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grown = args.grown or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    toy_name = rng.choice(TOYS)
    return StoryParams(
        yard=yard,
        question=question,
        guide=guide,
        name=name,
        gender=gender,
        grown=grown,
        trait=trait,
        toy_name=toy_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.yard not in YARDS:
        raise StoryError(f"(Unknown yard: {params.yard})")
    if params.question not in QUESTIONS:
        raise StoryError(f"(Unknown question: {params.question})")
    if params.guide not in GUIDES:
        raise StoryError(f"(Unknown guide: {params.guide})")

    yard = YARDS[params.yard]
    question = QUESTIONS[params.question]
    guide = GUIDES[params.guide]
    if not safe_combo(question, guide):
        raise StoryError(explain_rejection(question, guide))

    world = tell(
        yard=yard,
        question=question,
        guide=guide,
        child_name=params.name,
        child_type=params.gender,
        grown_type=params.grown,
        trait=params.trait,
        toy_name=params.toy_name,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    smoke_cases = list(CURATED)
    try:
        parser = build_parser()
        default_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"FAILED: default resolve_params crashed: {err}")
        return rc

    try:
        for params in smoke_cases:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            emit(sample, trace=False, qa=False, header="")
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    except Exception as err:
        rc = 1
        print(f"FAILED: ordinary story generation crashed: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (yard, question, guide) combos:\n")
        for yard, question, guide in combos:
            print(f"  {yard:12} {question:8} {guide}")
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
            header = f"### {p.name}: {p.question} in {p.yard} with {p.guide}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
