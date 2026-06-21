#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/saber_dial_bird_surprise_cautionary_slice_of.py
============================================================================

A small slice-of-life storyworld about a child, a toy saber, a frightened bird,
and the calm grown-up steps that make the room safe again.

The seed words are all part of the living world model:

* saber: the child is already playing with a toy saber
* dial: the grown-up turns a fan dial to zero before helping
* bird: a real little bird has flown inside and needs a safe way out

The cautionary logic is simple and explicit:
a toy saber is not a tool for touching a frightened bird, and a whirring fan
makes an indoor bird's panic more dangerous. A safe rescue requires:
(1) an open exit,
(2) the fan turned off,
(3) a helper gentle enough for a bird,
(4) enough reach for the perch where the bird landed.

This file is standalone and stdlib-only. It follows the Storyworld contract:
typed entities, physical meters and emotional memes, a Python reasonableness
gate, an inline ASP twin, state-driven prose, and three QA sets.
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

# Make the shared result containers importable when this script is run directly:
# add the package dir (storyworlds/) to sys.path from this nested folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Room:
    id: str
    label: str
    phrase: str
    exit_word: str
    exit_action: str
    fan_phrase: str
    has_window: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    height: int
    fragile: bool = False
    room_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    reach: int
    gentle: bool
    sense: int
    action: str
    qa_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FanState:
    id: str
    label: str
    dial_value: int
    whirr: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
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
        clone = World(self.room)
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


def _r_fan_risk(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    bird = world.get("bird")
    fan = world.get("fan")
    if bird.meters["indoors"] >= THRESHOLD and fan.meters["on"] >= THRESHOLD:
        sig = ("fan_risk",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["danger"] += 1
            bird.memes["fear"] += 1
            out.append("__fan__")
    return out


def _r_saber_panic(world: World) -> list[str]:
    out: list[str] = []
    bird = world.get("bird")
    child = world.get("child")
    if child.meters["saber_raised"] >= THRESHOLD and bird.meters["indoors"] >= THRESHOLD:
        sig = ("saber_panic",)
        if sig not in world.fired:
            world.fired.add(sig)
            bird.memes["fear"] += 1
            child.memes["worry"] += 1
            out.append("__panic__")
    return out


def _r_safe_exit(world: World) -> list[str]:
    out: list[str] = []
    bird = world.get("bird")
    fan = world.get("fan")
    room = world.get("room")
    helper = world.get("helper")
    if (
        bird.meters["exit_open"] >= THRESHOLD
        and fan.meters["on"] < THRESHOLD
        and helper.meters["used"] >= THRESHOLD
        and helper.attrs.get("gentle", False)
        and helper.attrs.get("reach", 0) >= bird.attrs.get("perch_height", 0)
        and bird.meters["indoors"] >= THRESHOLD
    ):
        sig = ("safe_exit",)
        if sig not in world.fired:
            world.fired.add(sig)
            bird.meters["indoors"] = 0.0
            bird.meters["outside"] += 1
            room.meters["danger"] = 0.0
            bird.memes["fear"] = 0.0
            bird.memes["relief"] += 1
            out.append("__exit__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="fan_risk", tag="physical", apply=_r_fan_risk),
    Rule(name="saber_panic", tag="social", apply=_r_saber_panic),
    Rule(name="safe_exit", tag="physical", apply=_r_safe_exit),
]


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


def perch_allowed(room: Room, perch: Perch) -> bool:
    return room.id in perch.room_ids


def helper_can_reach(helper: Helper, perch: Perch) -> bool:
    return helper.reach >= perch.height


def helper_is_sensible(helper: Helper) -> bool:
    return helper.gentle and helper.sense >= SENSE_MIN


def valid_combo(room: Room, perch: Perch, helper: Helper) -> bool:
    return perch_allowed(room, perch) and helper_can_reach(helper, perch) and helper_is_sensible(helper)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for perch_id, perch in PERCHES.items():
            for helper_id, helper in HELPERS.items():
                if valid_combo(room, perch, helper):
                    combos.append((room_id, perch_id, helper_id))
    return combos


def explain_helper_rejection(helper: Helper) -> str:
    if helper.sense < SENSE_MIN:
        return (
            f"(Refusing helper '{helper.id}': it is not a calm, sensible way to help a frightened bird "
            f"(sense={helper.sense} < {SENSE_MIN}). Pick a gentler helper like "
            f"{', '.join(sorted(h.id for h in HELPERS.values() if helper_is_sensible(h)))}.)"
        )
    if not helper.gentle:
        return (
            f"(Refusing helper '{helper.id}': it is too rough for a frightened bird. "
            f"A storyworld should prefer gentle tools that guide instead of jab.)"
        )
    return "(Refusing helper: this tool is unreasonable here.)"


def explain_combo_rejection(room: Room, perch: Perch, helper: Helper) -> str:
    if not perch_allowed(room, perch):
        return (
            f"(No story: {perch.label} does not belong in {room.label}, so the bird would not land there. "
            f"Pick a perch that fits the room.)"
        )
    if not helper_can_reach(helper, perch):
        return (
            f"(No story: {helper.label} cannot reach the {perch.label}. "
            f"The helper must reach high enough to guide the bird safely.)"
        )
    if not helper_is_sensible(helper):
        return explain_helper_rejection(helper)
    return "(No story: this room, perch, and helper do not make a reasonable rescue.)"


def predict_with_saber(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["saber_raised"] += 1
    propagate(sim, narrate=False)
    return {
        "bird_fear": sim.get("bird").memes["fear"],
        "danger": sim.get("room").meters["danger"],
    }


def introduce(world: World, child: Entity, parent: Entity, room: Room) -> None:
    trait = next((t for t in child.traits if t), "")
    desc = f"little {trait} {child.type}".strip()
    world.say(
        f"After school, {child.id} was a {desc} in {room.phrase}, making soft whooshing sounds with a foam saber while "
        f"{child.pronoun('possessive')} {parent.label_word} finished a small chore nearby."
    )


def setup_room(world: World, room: Room, fan_state: FanState) -> None:
    world.say(
        f"The room felt ordinary and homey: a chair by the wall, afternoon light on the floor, and {room.fan_phrase} "
        f"set to {fan_state.dial_value} on the fan dial."
    )


def surprise_arrival(world: World, child: Entity, room: Room, perch: Perch) -> None:
    bird = world.get("bird")
    bird.meters["indoors"] += 1
    bird.attrs["perch_height"] = perch.height
    bird.attrs["perch_label"] = perch.label
    bird.attrs["perch_fragile"] = perch.fragile
    world.say(
        f"Then came the surprise. A little bird fluttered in through {room.exit_word}, circled once in a blur, and landed on {perch.phrase}."
    )
    propagate(world, narrate=False)
    if world.get("room").meters["danger"] >= THRESHOLD:
        world.say(
            f"For a moment the bird looked very small under the moving fan, and the room no longer felt quite ordinary."
        )


def child_idea(world: World, child: Entity, parent: Entity) -> None:
    pred = predict_with_saber(world)
    world.facts["predicted_fear"] = pred["bird_fear"]
    world.facts["predicted_danger"] = pred["danger"]
    child.memes["impulse"] += 1
    world.say(
        f'"I can help," {child.id} said, lifting the toy saber a little. "{child.pronoun("possessive").capitalize()} beak is up there. I can nudge it down."'
    )
    extra = ""
    if pred["danger"] >= THRESHOLD:
        extra = " The spinning fan made the idea seem even riskier."
    world.say(
        f'{parent.label_word.capitalize()} shook {parent.pronoun("possessive")} head at once. '
        f'"No, sweetie. A saber is for pretend games, not for touching a scared bird."{extra}'
    )


def near_miss(world: World, child: Entity) -> None:
    child.meters["saber_raised"] += 1
    propagate(world, narrate=False)
    bird = world.get("bird")
    if bird.memes["fear"] >= THRESHOLD:
        world.say(
            f"As the foam saber lifted, the bird pressed itself tighter and gave one quick, frightened flutter."
        )


def calm_plan(world: World, parent: Entity, room: Room, helper: Helper) -> None:
    fan = world.get("fan")
    fan.meters["on"] = 0.0
    fan.meters["off"] += 1
    world.get("bird").memos = {} if hasattr(world.get("bird"), "memos") else None
    world.get("bird").meters["exit_open"] += 1
    world.say(
        f'{parent.label_word.capitalize()} reached for the fan and turned the dial down to zero. '
        f'The whir faded away. Then {parent.pronoun()} {room.exit_action} and picked up {helper.phrase}.'
    )
    child.memes["trust"] += 1
    world.say(
        f'"We make the room quiet first," {parent.pronoun()} said. "Then we give the bird a calm way out."'
    )


def rescue(world: World, parent: Entity, child: Entity, helper: Helper, perch: Perch) -> None:
    helper_ent = world.get("helper")
    helper_ent.meters["used"] += 1
    propagate(world, narrate=False)
    bird = world.get("bird")
    if bird.meters["outside"] >= THRESHOLD:
        child.memes["relief"] += 1
        child.memes["awe"] += 1
        parent.memes["relief"] += 1
        world.say(
            f"{parent.label_word.capitalize()} {helper.action}. The bird hopped once, saw the bright opening, and flew outside in a neat, quick streak."
        )
        if perch.fragile:
            world.say(
                f"Only the {perch.label} trembled a little after it left."
            )
        else:
            world.say(
                f"The place where it had been perched looked still again."
            )


def lesson(world: World, parent: Entity, child: Entity) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} put a hand on {child.id}\'s shoulder. '
        f'"You wanted to help, and that was kind," {parent.pronoun()} said. '
        f'"But frightened animals need calm hands, not toys."'
    )
    world.say(
        f'{child.id} looked at the foam saber, then back at the open {world.room.exit_word}. '
        f'"Next time I will call you first," {child.pronoun()} said.'
    )


def ending(world: World, child: Entity, room: Room) -> None:
    bird = world.get("bird")
    if bird.meters["outside"] >= THRESHOLD:
        feather = world.facts.get("feather")
        image = "A tiny feather floated down onto the windowsill." if feather else "Outside, the little bird gave one bright chirp from a branch."
        world.say(
            f"A minute later, {room.phrase} felt like itself again. {image} {child.id} set the saber on the chair and listened with a small, careful smile."
        )


def tell(
    room: Room,
    perch: Perch,
    helper: Helper,
    fan_state: FanState,
    child_name: str = "Mina",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    poke_first: bool = False,
    feather: bool = False,
) -> World:
    world = World(room)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    fan = world.add(Entity(
        id="fan",
        type="fan",
        label="fan",
        phrase="the fan",
        attrs={"dial_value": fan_state.dial_value},
        tags=set(fan_state.tags),
    ))
    if fan_state.dial_value > 0:
        fan.meters["on"] += 1
    else:
        fan.meters["off"] += 1
    room_ent = world.add(Entity(
        id="room",
        type="room",
        label=room.label,
        phrase=room.phrase,
        tags=set(room.tags),
    ))
    bird = world.add(Entity(
        id="bird",
        type="bird",
        label="bird",
        phrase="a little bird",
        attrs={"perch_height": perch.height},
        tags={"bird"},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        type="helper",
        label=helper.label,
        phrase=helper.phrase,
        attrs={"reach": helper.reach, "gentle": helper.gentle, "sense": helper.sense},
        tags=set(helper.tags),
    ))

    introduce(world, child, parent, room)
    setup_room(world, room, fan_state)

    world.para()
    surprise_arrival(world, child, room, perch)
    child_idea(world, child, parent)
    if poke_first:
        near_miss(world, child)

    world.para()
    calm_plan(world, parent, room, helper)
    rescue(world, parent, child, helper, perch)
    lesson(world, parent, child)

    world.para()
    world.facts["feather"] = feather
    ending(world, child, room)

    world.facts.update(
        child=child,
        parent=parent,
        room_cfg=room,
        perch_cfg=perch,
        helper_cfg=helper,
        fan_cfg=fan_state,
        bird=bird,
        fan=fan,
        room=room_ent,
        helper=helper_ent,
        poke_first=poke_first,
        escaped=bird.meters["outside"] >= THRESHOLD,
        danger_seen=room_ent.meters["danger"] <= 0.0,
    )
    return world


ROOMS = {
    "kitchen": Room(
        id="kitchen",
        label="kitchen",
        phrase="the warm kitchen",
        exit_word="the open window over the sink",
        exit_action="pushed the window wider",
        fan_phrase="a small ceiling fan humming above the table",
        has_window=True,
        tags={"home", "kitchen"},
    ),
    "sunroom": Room(
        id="sunroom",
        label="sunroom",
        phrase="the bright sunroom",
        exit_word="the half-open porch door",
        exit_action="opened the porch door all the way",
        fan_phrase="a standing fan in the corner softly whirring",
        has_window=True,
        tags={"home", "sunroom"},
    ),
    "bedroom": Room(
        id="bedroom",
        label="bedroom",
        phrase="the tidy bedroom",
        exit_word="the window beside the dresser",
        exit_action="lifted the window higher",
        fan_phrase="a ceiling fan turning lazy circles overhead",
        has_window=True,
        tags={"home", "bedroom"},
    ),
}

PERCHES = {
    "curtain_rod": Perch(
        id="curtain_rod",
        label="curtain rod",
        phrase="the curtain rod near the light",
        height=3,
        fragile=False,
        room_ids={"sunroom", "bedroom"},
        tags={"high", "window"},
    ),
    "bookshelf": Perch(
        id="bookshelf",
        label="bookshelf",
        phrase="the top edge of the bookshelf",
        height=2,
        fragile=False,
        room_ids={"bedroom"},
        tags={"high", "books"},
    ),
    "chair_back": Perch(
        id="chair_back",
        label="chair back",
        phrase="the back of the wooden chair",
        height=1,
        fragile=False,
        room_ids={"kitchen", "sunroom", "bedroom"},
        tags={"low"},
    ),
    "lamp_shade": Perch(
        id="lamp_shade",
        label="lamp shade",
        phrase="the cloth lamp shade by the sofa",
        height=2,
        fragile=True,
        room_ids={"sunroom"},
        tags={"high", "fragile"},
    ),
}

HELPERS = {
    "tea_towel": Helper(
        id="tea_towel",
        label="tea towel",
        phrase="a clean tea towel",
        reach=2,
        gentle=True,
        sense=3,
        action="held the tea towel up like a soft wall and guided the bird away from the room",
        qa_text="used a clean tea towel as a soft guide",
        fail_text="could not reach the perch with the tea towel",
        tags={"towel"},
    ),
    "laundry_basket": Helper(
        id="laundry_basket",
        label="laundry basket",
        phrase="the light laundry basket",
        reach=1,
        gentle=True,
        sense=2,
        action="tilted the basket slowly so the bird could see the open way and hop toward it",
        qa_text="used a laundry basket to block the wrong direction and guide the bird",
        fail_text="could not lift the basket high enough to help there",
        tags={"basket"},
    ),
    "cardigan": Helper(
        id="cardigan",
        label="cardigan",
        phrase="a soft cardigan",
        reach=3,
        gentle=True,
        sense=3,
        action="raised the cardigan slowly and made a quiet, safe tunnel toward the opening",
        qa_text="used a soft cardigan to make a gentle path to the exit",
        fail_text="did not have enough reach with the cardigan",
        tags={"cloth"},
    ),
    "broom": Helper(
        id="broom",
        label="broom",
        phrase="the broom",
        reach=3,
        gentle=False,
        sense=1,
        action="waved the broom at the bird",
        qa_text="waved a broom at the bird",
        fail_text="only scared the bird more with the broom",
        tags={"rough"},
    ),
}

FAN_STATES = {
    "low": FanState(
        id="low",
        label="low",
        dial_value=1,
        whirr="soft",
        tags={"fan"},
    ),
    "medium": FanState(
        id="medium",
        label="medium",
        dial_value=2,
        whirr="steady",
        tags={"fan"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Ava", "Nora", "Lucy", "Maya", "Ella", "Zoe"]
BOY_NAMES = ["Owen", "Ben", "Theo", "Max", "Sam", "Leo", "Noah", "Eli"]
TRAITS = ["careful", "curious", "gentle", "busy", "eager", "thoughtful"]


@dataclass
class StoryParams:
    room: str
    perch: str
    helper: str
    fan_state: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    poke_first: bool = False
    feather: bool = False
    seed: Optional[int] = None


KNOWLEDGE = {
    "bird": [
        (
            "Why can a bird get scared inside a house?",
            "A house is not where a wild bird expects to be, so strange walls, people, and noises can make it panic. When birds panic, they flap fast and may bump into things.",
        )
    ],
    "fan": [
        (
            "Why should a fan be turned off if a bird is flying inside?",
            "A moving fan is dangerous because a bird can fly into the spinning blades. Turning the fan off makes the room safer right away.",
        )
    ],
    "saber": [
        (
            "Why is a toy saber not a good tool for helping a bird?",
            "A toy saber is made for pretend play, not for touching living animals. Even a soft toy can frighten a bird and make it flap in a dangerous way.",
        )
    ],
    "towel": [
        (
            "How can a towel help guide a bird?",
            "A towel can act like a soft wall that gently shows the bird which way to go. It should be moved slowly so the bird does not panic.",
        )
    ],
    "basket": [
        (
            "How can a basket help with a bird indoors?",
            "A light basket can block the wrong path and leave one safe path open. That works best when the bird is low enough for the basket to reach.",
        )
    ],
    "cloth": [
        (
            "Why can a soft cloth be better than a hard stick near a bird?",
            "A soft cloth looks less sharp and threatening than a stick or broom. Gentle tools help people move slowly and keep the bird calmer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bird", "fan", "saber", "towel", "basket", "cloth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    room = f["room_cfg"]
    perch = f["perch_cfg"]
    helper = f["helper_cfg"]
    parent = f["parent"]
    return [
        'Write a short slice-of-life story for a 3-to-5-year-old that includes the words "saber", "dial", and "bird".',
        f"Tell a gentle cautionary story where {child.id} starts to help a frightened bird with a toy saber in {room.label}, but {child.pronoun('possessive')} {parent.label_word} stops that idea and uses {helper.phrase} instead.",
        f"Write a home story with a small surprise: a bird lands on {perch.label}, someone turns a fan dial to zero, and the ending shows the room feeling calm again.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    room = f["room_cfg"]
    perch = f["perch_cfg"]
    helper = f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child playing at home with a foam saber, and {child.pronoun('possessive')} {parent.label_word} who helps when a bird flies inside.",
        ),
        (
            "What was the surprise in the story?",
            f"The surprise was that a little bird suddenly flew into {room.label} and landed on {perch.label}. That changed an ordinary afternoon into a careful rescue.",
        ),
        (
            f"Why did {child.id}'s {parent.label_word} say not to use the saber?",
            f"{parent.label_word.capitalize()} said a saber is for pretend games, not for touching a scared bird. The bird was already frightened, and waving the toy near it could make it flap harder and get into more danger.",
        ),
        (
            "What did the grown-up do first to make the room safer?",
            f"{parent.label_word.capitalize()} turned the fan dial to zero before helping. That mattered because a moving fan is dangerous for a bird that is already flying around the room.",
        ),
        (
            f"How did {child.id}'s {parent.label_word} help the bird get out?",
            f"{parent.label_word.capitalize()} {helper.qa_text} and opened a clear way outside. The quiet room and the gentle helper gave the bird one safe direction to fly.",
        ),
        (
            "How did the story end?",
            f"The bird got back outside, and the room felt calm again. {child.id} understood that kind ideas still need safe tools.",
        ),
    ]
    if f.get("poke_first"):
        qa.append(
            (
                f"What happened when {child.id} lifted the saber first?",
                f"The bird gave a quick frightened flutter, which showed that the toy was making things worse, not better. That small near-miss is why the grown-up stepped in so quickly.",
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"bird", "fan", "saber"}
    helper = f["helper_cfg"]
    tags |= set(helper.tags)
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="kitchen",
        perch="chair_back",
        helper="laundry_basket",
        fan_state="low",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        trait="curious",
        poke_first=False,
        feather=True,
    ),
    StoryParams(
        room="sunroom",
        perch="lamp_shade",
        helper="cardigan",
        fan_state="medium",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="eager",
        poke_first=True,
        feather=False,
    ),
    StoryParams(
        room="bedroom",
        perch="bookshelf",
        helper="tea_towel",
        fan_state="low",
        child_name="Lucy",
        child_gender="girl",
        parent="grandmother",
        trait="thoughtful",
        poke_first=False,
        feather=True,
    ),
    StoryParams(
        room="sunroom",
        perch="curtain_rod",
        helper="cardigan",
        fan_state="medium",
        child_name="Owen",
        child_gender="boy",
        parent="grandfather",
        trait="gentle",
        poke_first=True,
        feather=True,
    ),
]


ASP_RULES = r"""
room_perch_ok(R, P) :- room(R), perch(P), present_in(P, R).
helper_reaches(H, P) :- helper(H), perch(P), reach(H, RH), height(P, PH), RH >= PH.
sensible(H) :- helper(H), gentle(H), sense(H, S), sense_min(M), S >= M.
valid(R, P, H) :- room(R), perch(P), helper(H), room_perch_ok(R, P), helper_reaches(H, P), sensible(H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for room_id in ROOMS:
        lines.append(asp.fact("room", room_id))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("height", perch_id, perch.height))
        for room_id in sorted(perch.room_ids):
            lines.append(asp.fact("present_in", perch_id, room_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("reach", helper_id, helper.reach))
        lines.append(asp.fact("sense", helper_id, helper.sense))
        if helper.gentle:
            lines.append(asp.fact("gentle", helper_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _validate_params(params: StoryParams) -> None:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room '{params.room}'.)")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch '{params.perch}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.fan_state not in FAN_STATES:
        raise StoryError(f"(Unknown fan state '{params.fan_state}'.)")
    room = ROOMS[params.room]
    perch = PERCHES[params.perch]
    helper = HELPERS[params.helper]
    if not helper_is_sensible(helper):
        raise StoryError(explain_helper_rejection(helper))
    if not valid_combo(room, perch, helper):
        raise StoryError(explain_combo_rejection(room, perch, helper))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        params = resolve_params(default_args, random.Random(123))
        smoke_cases.append(params)
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE FAILURE in resolve_params(): {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story or "bird" not in sample.story.lower():
                raise StoryError("story text missing or malformed")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"SMOKE FAILURE for params {params}: {err}")
            break

    if rc == 0:
        print(f"OK: generated and emitted {len(smoke_cases)} smoke-test stories.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a toy saber, a fan dial, and a frightened bird indoors."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--fan-state", choices=FAN_STATES, dest="fan_state")
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--poke-first", action="store_true", help="child lifts the saber before stopping")
    ap.add_argument("--feather", action="store_true", help="ending image includes a fallen feather")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid room/perch/helper combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper is not None and args.helper in HELPERS and not helper_is_sensible(HELPERS[args.helper]):
        raise StoryError(explain_helper_rejection(HELPERS[args.helper]))

    if args.room and args.perch and args.helper:
        room = ROOMS[args.room]
        perch = PERCHES[args.perch]
        helper = HELPERS[args.helper]
        if not valid_combo(room, perch, helper):
            raise StoryError(explain_combo_rejection(room, perch, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.perch is None or combo[1] == args.perch)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, perch_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    parent = args.parent or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    fan_state = args.fan_state or rng.choice(sorted(FAN_STATES))
    poke_first = bool(args.poke_first) or rng.choice([False, False, True])
    feather = bool(args.feather) or rng.choice([False, True])
    return StoryParams(
        room=room_id,
        perch=perch_id,
        helper=helper_id,
        fan_state=fan_state,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        poke_first=poke_first,
        feather=feather,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        room=ROOMS[params.room],
        perch=PERCHES[params.perch],
        helper=HELPERS[params.helper],
        fan_state=FAN_STATES[params.fan_state],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        poke_first=params.poke_first,
        feather=params.feather,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (room, perch, helper) combos:\n")
        for room_id, perch_id, helper_id in combos:
            print(f"  {room_id:8} {perch_id:12} {helper_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.room}, {p.perch}, {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
