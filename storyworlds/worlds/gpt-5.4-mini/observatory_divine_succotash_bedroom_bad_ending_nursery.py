#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/observatory_divine_succotash_bedroom_bad_ending_nursery.py
===========================================================================================

A standalone storyworld for a tiny nursery-rhyme-like bedroom tale:
two children turn a bedroom into a pretend observatory, a bowl of divine
succotash becomes part of the game, and a forbidden flame choice leads to a
bad ending when the quilt catches fire.

The world is intentionally small:
- one room: a bedroom
- one pretend-play goal: build an observatory
- one unsafe choice: use a candle for light
- one risky object: a quilt/curtain/bedspread near the candle
- one bad ending: the fire grows faster than the family can fix it, so they
  escape and lose the room's cozy game

The story is written in a nursery-rhyme cadence, but the underlying state
drives the prose. Physical meters and emotional memes accumulate through
simulation, and the Q&A is generated from the world state rather than by parsing
the rendered text.
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    makes_flame: bool = False
    edible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    scene: str
    dark_spot: str
    afford: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class PlayThing:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class UnsafeChoice:
    id: str
    label: str
    phrase: str
    where: str
    makes_flame: bool
    cry: str
    lesson: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    near: str
    flammable: bool = True
    spread: int = 3
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["fear"] += 1
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spread)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def hazard_at_risk(choice: UnsafeChoice, hazard: Hazard) -> bool:
    return choice.makes_flame and hazard.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(hazard: Hazard, delay: int) -> int:
    return hazard.spread + delay


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= fire_severity(hazard, delay)


def _do_forbidden(world: World, hazard_ent: Entity, narrate: bool = True) -> None:
    hazard_ent.meters["burning"] += 1
    propagate(world, narrate=narrate)


def predict_fire(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(hazard_id), narrate=False)
    return {
        "ignites": sim.get(hazard_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"] if "room" in sim.entities else 0,
    }


def build_scene(world: World, child: Entity, buddy: Entity, setting: Setting, play: PlayThing) -> None:
    child.memes["joy"] += 1
    buddy.memes["joy"] += 1
    world.say(
        f"On a moon-pale night in the bedroom, {child.id} and {buddy.id} turned "
        f"{setting.place} into {setting.scene}. {setting.dark_spot} waited in a hush, "
        f"and the blanket made a soft white wall."
    )
    world.say(
        f'"Oh, look," sang {child.id}, "an observatory fine! And a bowl of '
        f"{play.phrase} divine!"
    )


def want_light(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} climbed on the bed and peered at the window glass. "
        f'"We need a little light," {child.pronoun()} said, "for stars that shine."'
    )


def tempt(world: World, child: Entity, unsafe: UnsafeChoice) -> None:
    child.memes["boldness"] += 1
    world.say(
        f'"I know a way," {child.id} cried sweet and bright. "A {unsafe.label} '
        f"will help us see tonight."
    )
    world.say("For a tick of the clock, the idea seemed clever and spry.")


def warn(world: World, buddy: Entity, child: Entity, unsafe: UnsafeChoice, hazard: Hazard) -> None:
    pred = predict_fire(world, "hazard")
    buddy.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f"{buddy.id} shook {buddy.pronoun('possessive')} head. "
        f'"No, no, {child.id}. We must not touch {unsafe.label}. '
        f"It makes a real flame, and {hazard.the} can catch all alight."
    )


def defy(world: World, child: Entity, buddy: Entity, unsafe: UnsafeChoice) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Pish-posh," said {child.id}. "{unsafe.cry}" And {child.id} reached '
        f"for the {unsafe.label} without delay."
    )


def ignite(world: World, hazard_ent: Entity, unsafe: UnsafeChoice, hazard: Hazard) -> None:
    _do_forbidden(world, hazard_ent)
    world.say(
        f"{unsafe.label.capitalize()} flashed to life, a little orange spark. "
        f"For one blink it was merry and light, then it leaned to {hazard.near} "
        f"and kissed the quilt goodnight."
    )


def alarm(world: World, buddy: Entity, child: Entity, hazard: Hazard, parent: Entity) -> None:
    world.say(f'"{child.id}! Fire! The {hazard.label}!" {buddy.id} cried.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, hazard_ent: Entity, hazard: Hazard) -> None:
    hazard_ent.meters["burning"] = 0.0
    if "room" in world.entities:
        world.get("room").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} ran in a hurry and {response.text.replace('{target}', hazard.label)}."
    )
    world.say(
        f"The flame went hiss and hush, and the observatory was saved from smoke."
    )


def rescue_fail(world: World, parent: Entity, response: Response, hazard_ent: Entity, hazard: Hazard) -> None:
    hazard_ent.meters["burning"] += 1
    if "room" in world.entities:
        world.get("room").meters["burning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} ran in a hurry and {response.fail.replace('{target}', hazard.label)}."
    )
    world.say(
        f"But the little flame grew tall and fat, and it leapt from quilt to bedspread like a dancing cat."
    )


def escape_and_loss(world: World, parent: Entity, child: Entity, buddy: Entity) -> None:
    for e in (child, buddy):
        e.memes["fear"] += 1
    world.say(
        f"There was no time to tarry. {parent.label_word.capitalize()} grabbed "
        f"{child.id} and {buddy.id} by the hands and hurried them out."
    )
    world.say(
        "They watched the room turn smoky gray, and their cosy bedroom game was lost that day."
    )


def lesson(world: World, parent: Entity, child: Entity, buddy: Entity, unsafe: UnsafeChoice) -> None:
    for e in (child, buddy):
        e.memes["lesson"] += 1
        e.memes["relief"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} held them close and said, "
        f'"You did the brave thing by calling for me. But remember, remember, '
        f'{unsafe.lesson}."'
    )
    world.say("And the moon kept watching through the smoky pane.")


def tell(setting: Setting, play: PlayThing, unsafe: UnsafeChoice, hazard: Hazard,
         response: Response, child_name: str = "Milo", child_gender: str = "boy",
         buddy_name: str = "Luna", buddy_gender: str = "girl",
         parent_type: str = "mother", delay: int = 1,
         child_age: int = 6, buddy_age: int = 5, relation: str = "friends") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="instigator", age=child_age,
                             attrs={"relation": relation}))
    buddy = world.add(Entity(id=buddy_name, kind="character", type=buddy_gender,
                             role="cautioner", age=buddy_age,
                             attrs={"relation": relation}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    hazard_ent = world.add(Entity(id="hazard", type="hazard", label=hazard.label, flammable=hazard.flammable))
    child.memes["bravery"] = 6.0
    buddy.memes["caution"] = 5.0

    build_scene(world, child, buddy, setting, play)
    world.para()
    want_light(world, child)
    tempt(world, child, unsafe)
    warn(world, buddy, child, unsafe, hazard)

    world.para()
    child.memes["defiance"] += 0.5
    defy(world, child, buddy, unsafe)

    world.para()
    ignite(world, hazard_ent, unsafe, hazard)
    alarm(world, buddy, child, hazard, parent)

    contained = is_contained(response, hazard, delay)
    if contained:
        world.para()
        rescue(world, parent, response, hazard_ent, hazard)
    else:
        world.para()
        rescue_fail(world, parent, response, hazard_ent, hazard)
        escape_and_loss(world, parent, child, buddy)
        lesson(world, parent, child, buddy, unsafe)

    world.facts.update(
        child=child, buddy=buddy, parent=parent, room=room,
        play=play, unsafe=unsafe, hazard_cfg=hazard, hazard=hazard_ent,
        response=response, delay=delay, outcome="contained" if contained else "burned",
        ignited=True, rescued=contained, relation=relation
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        "bedroom",
        "the bedroom",
        "a tiny observatory",
        "the little space under the window",
        {"observatory"},
    )
}

PLAYTHINGS = {
    "succotash": PlayThing(
        "succotash",
        "succotash",
        "a bowl of divine succotash",
        "shone in a silver spoon",
        {"succotash", "food"},
    )
}

UNSAFE_CHOICES = {
    "candle": UnsafeChoice(
        "candle",
        "candle",
        "a candle",
        "on the bedside table",
        True,
        "Light the candle!",
        "never, ever, ever play with candles in a bedroom",
        {"candle", "fire"},
    )
}

HAZARDS = {
    "quilt": Hazard(
        "quilt",
        "quilt",
        "the quilt",
        "the quilt edge",
        True,
        4,
        {"quilt", "cloth"},
    )
}

RESPONSES = {
    "smother": Response(
        "smother",
        3,
        1,
        "snatched the quilt and smothered the spark beneath a heavy blanket",
        "snatched at the quilt, but the spark was already too big to smother",
        "snatched the quilt and smothered the spark beneath a heavy blanket",
        {"blanket", "fire"},
    ),
    "stomp": Response(
        "stomp",
        2,
        2,
        "stamped the spark out with quick, brave feet",
        "stamped at the spark, but the flame only hopped higher",
        "stamped the spark out with quick, brave feet",
        {"feet", "fire"},
    ),
    "water_bowl": Response(
        "water_bowl",
        1,
        1,
        "fetched a tiny bowl of water and splashed it over the spark",
        "fetched a tiny bowl of water, but it was far too little",
        "fetched a tiny bowl of water and splashed it over the spark",
        {"water", "fire"},
    ),
}

GIRL_NAMES = ["Luna", "Mina", "Ivy", "Nora", "Mabel", "Ruby", "Poppy"]
BOY_NAMES = ["Milo", "Finn", "Otto", "Theo", "Benny", "Eli", "Jasper"]
TRAITS = ["curious", "merry", "dreamy", "gentle", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for u in UNSAFE_CHOICES:
            for h in HAZARDS:
                if hazard_at_risk(UNSAFE_CHOICES[u], HAZARDS[h]):
                    combos.append((s, u, h))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    unsafe: str
    hazard: str
    response: str
    child_name: str
    child_gender: str
    buddy_name: str
    buddy_gender: str
    parent_type: str
    trait: str
    delay: int = 1
    child_age: int = 6
    buddy_age: int = 5
    relation: str = "friends"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "observatory": [("What is an observatory?",
                    "An observatory is a place where people look at the sky and stars. It often has a telescope or a special window for watching faraway things.")],
    "succotash": [("What is succotash?",
                  "Succotash is a dish made with corn and beans, and sometimes other soft vegetables. It is a food that should stay in a bowl, not on the floor.")],
    "candle": [("Why can a candle be dangerous in a bedroom?",
                "A candle has a real flame, and bedclothes can catch fire if the flame gets too close. Bedrooms have soft things that can burn quickly.")],
    "quilt": [("What is a quilt?",
               "A quilt is a thick blanket made of cloth. Because it is cloth, it can catch fire if a flame touches it.")],
    "fire": [("Why is fire dangerous?",
              "Fire is hot and can spread fast. It can burn things and make smoke, so children should call a grown-up right away.")],
    "call_adult": [("What should you do if something starts burning?",
                    "Move away from the fire and call a grown-up right away. Getting help fast is the safest choice.")],
    "smother": [("How can you smother a tiny spark?",
                 "You can cover a tiny spark so it does not get air. Without air, a small flame may go out.")],
    "stomp": [("Can you stomp out a tiny flame?",
               "Sometimes a grown-up can stomp out a tiny flame very quickly, but only if it is small and safe to reach.")],
    "water_bowl": [("Is a small bowl of water always enough for fire?",
                     "No. A tiny bowl of water is often not enough for a growing fire, so a grown-up may need a better tool or to call firefighters.")],
}
KNOWLEDGE_ORDER = ["observatory", "succotash", "candle", "quilt", "fire", "call_adult", "smother", "stomp", "water_bowl"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story that includes the words "observatory" and "divine succotash" in a bedroom setting.',
        f"Tell a small bedroom tale where {f['child'].id} and {f['buddy'].id} build an observatory, but a candle makes trouble and the ending goes badly.",
        f'Write a sad little story for a child that uses the word "{f["play"].label}" and ends with a smoky bedroom after a fire.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, buddy, parent = f["child"], f["buddy"], f["parent"]
    play, unsafe, hazard, resp = f["play"], f["unsafe"], f["hazard_cfg"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {buddy.id}, two little friends in the bedroom. {parent.label_word.capitalize()} comes in when the trouble starts."),
        ("What were they building?",
         f"They were turning the bedroom into an observatory, a pretend place for looking at the stars. The bed and blanket became part of the game."),
        ("What was in the bowl?",
         f"There was a bowl of divine succotash. It was part of the play scene, but it did not keep the flame safe."),
        ("What did {0} want to use for light?".format(child.id),
         f"{child.id} wanted to use {unsafe.label}. That choice was dangerous because a real flame can catch {hazard.the}."),
        ("How did the story end?",
         "It ended badly. The fire grew too fast, the family had to get out, and the bedroom game was lost in smoke."),
    ]
    if f.get("outcome") == "burned":
        qa.append((
            f"Could {parent.label_word} stop the fire with the chosen response?",
            f"No. {parent.label_word.capitalize()} tried to {resp.qa_text}, but it was not enough for this fire. The spark became a bigger blaze before the room could be saved."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["play"].tags) | set(world.facts["unsafe"].tags) | set(world.facts["hazard_cfg"].tags)
    tags |= set(world.facts["response"].tags)
    out = []
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.flammable:
            bits.append("flammable=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(unsafe: UnsafeChoice, hazard: Hazard) -> str:
    return f"(No story: {unsafe.label} can make a flame, and {hazard.the} is flammable, but the fixed bad-ending world only allows the one reasonable hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
hazard(F, H) :- makes_flame(F), flammable(H).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, U, H) :- setting(S), unsafe(U), hazard(H), hazard(U, H).
severity(HV) :- hazard_cfg(H), spread(H, HV).
contained :- chosen_response(R), severity(V), power(R, P), P >= V.
outcome(burned) :- not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for uid, u in UNSAFE_CHOICES.items():
        lines.append(asp.fact("unsafe", uid))
        if u.makes_flame:
            lines.append(asp.fact("makes_flame", uid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.flammable:
            lines.append(asp.fact("flammable", hid))
        lines.append(asp.fact("spread", hid, h.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("hazard_cfg", params.hazard),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "burned"


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        print("MISMATCH: sensible responses differ.")
        rc = 1

    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: valid-combo gate matches ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: valid combos differ.")
        rc = 1

    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: generate() produced empty story.")
        rc = 1
    else:
        print("OK: generate() smoke test produced a story.")
    return rc


CURATED = [
    StoryParams("bedroom", "candle", "quilt", "smother", "Milo", "boy", "Luna", "girl", "mother", "dreamy", delay=2),
    StoryParams("bedroom", "candle", "quilt", "stomp", "Nora", "girl", "Theo", "boy", "father", "curious", delay=2),
    StoryParams("bedroom", "candle", "quilt", "water_bowl", "Ivy", "girl", "Benny", "boy", "mother", "gentle", delay=3),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.unsafe and args.hazard:
        if not hazard_at_risk(UNSAFE_CHOICES[args.unsafe], HAZARDS[args.hazard]):
            raise StoryError(explain_rejection(UNSAFE_CHOICES[args.unsafe], HAZARDS[args.hazard]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    buddy_gender = "girl" if child_gender == "boy" else "boy"
    buddy_name = rng.choice(GIRL_NAMES if buddy_gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=args.setting or "bedroom",
        unsafe=args.unsafe or "candle",
        hazard=args.hazard or "quilt",
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        buddy_name=buddy_name,
        buddy_gender=buddy_gender,
        parent_type=args.parent or "mother",
        trait=trait,
        delay=args.delay if args.delay is not None else 2,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PLAYTHINGS["succotash"],
        UNSAFE_CHOICES[params.unsafe],
        HAZARDS[params.hazard],
        RESPONSES[params.response],
        params.child_name,
        params.child_gender,
        params.buddy_name,
        params.buddy_gender,
        params.parent_type,
        params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedroom observatory nursery-rhyme storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--unsafe", choices=UNSAFE_CHOICES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--delay", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, u, h in asp_valid_combos():
            print(f"  {s:8} {u:8} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.child_name}: {p.unsafe} near {p.hazard} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
