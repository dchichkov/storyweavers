#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bubble_speed_manicotti_humor_quest_repetition_whodunit.py
=====================================================================================

A standalone story world about a child detective solving the mystery of a missing
tray of manicotti at a funny bubble-filled family supper. The world models a
small whodunit: someone took the manicotti, clues are left behind, a child goes
on a quest around the house, repeats a question to the suspects, and discovers
that the "thief" was a bubble machine carrying the tray on a rolling cart during
a hurried cleanup.

The domain is intentionally small and constraint-checked:
- only combinations where the clue pattern uniquely identifies the mover are valid
- the mystery has a real middle turn driven by simulated clues and motion
- the ending proves the change: the family eats together, laughs, and slows down

Run it
------
    python storyworlds/worlds/gpt-5.4/bubble_speed_manicotti_humor_quest_repetition_whodunit.py
    python storyworlds/worlds/gpt-5.4/bubble_speed_manicotti_humor_quest_repetition_whodunit.py --room kitchen --helper aunt --vehicle cart
    python storyworlds/worlds/gpt-5.4/bubble_speed_manicotti_humor_quest_repetition_whodunit.py --vehicle wagon
    python storyworlds/worlds/gpt-5.4/bubble_speed_manicotti_humor_quest_repetition_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bubble_speed_manicotti_humor_quest_repetition_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/bubble_speed_manicotti_humor_quest_repetition_whodunit.py --verify
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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Room:
    id: str
    label: str
    phrase: str
    hiding_spot: str
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
class Helper:
    id: str
    type: str
    label: str
    title: str
    hurry_text: str
    safe_text: str
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
class Vehicle:
    id: str
    label: str
    phrase: str
    motion: str
    silly_sound: str
    speed: int
    leaves_wheels: bool = True
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
class BubbleMaker:
    id: str
    label: str
    phrase: str
    burst_text: str
    leaves_bubbles: bool = True
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
class Food:
    id: str
    label: str
    phrase: str
    smell: str
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


def _r_bubble_clue(world: World) -> list[str]:
    out: list[str] = []
    tray = world.get("tray")
    if tray.attrs.get("moved_by") != "bubble_machine":
        return out
    if tray.meters["moved"] < THRESHOLD:
        return out
    sig = ("bubble_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("hall").meters["bubble_clue"] += 1
    world.get("detective").memes["curious"] += 1
    out.append("__bubble__")
    return out


def _r_speed_clue(world: World) -> list[str]:
    out: list[str] = []
    tray = world.get("tray")
    vehicle = world.get("vehicle")
    if tray.meters["moved"] < THRESHOLD or vehicle.meters["rolling"] < THRESHOLD:
        return out
    sig = ("speed_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hall = world.get("hall")
    hall.meters["wheel_clue"] += 1
    hall.meters["speed"] += vehicle.attrs.get("speed", 0)
    out.append("__speed__")
    return out


def _r_quest_ready(world: World) -> list[str]:
    out: list[str] = []
    hall = world.get("hall")
    detective = world.get("detective")
    if hall.meters["bubble_clue"] < THRESHOLD or hall.meters["wheel_clue"] < THRESHOLD:
        return out
    sig = ("quest_ready",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["determined"] += 1
    out.append("__quest__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="bubble_clue", tag="physical", apply=_r_bubble_clue),
    Rule(name="speed_clue", tag="physical", apply=_r_speed_clue),
    Rule(name="quest_ready", tag="social", apply=_r_quest_ready),
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


def valid_move(vehicle: Vehicle, bubble_maker: BubbleMaker) -> bool:
    return vehicle.leaves_wheels and bubble_maker.leaves_bubbles


def sensible_speed(vehicle: Vehicle) -> bool:
    return vehicle.speed >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for room_id in ROOMS:
        for helper_id in HELPERS:
            for vehicle_id, vehicle in VEHICLES.items():
                for bubble_id, bubble in BUBBLE_MAKERS.items():
                    if valid_move(vehicle, bubble) and sensible_speed(vehicle):
                        combos.append((room_id, helper_id, vehicle_id, bubble_id))
    return combos


def explain_vehicle(vehicle: Vehicle) -> str:
    return (
        f"(Refusing vehicle '{vehicle.id}': it is too slow or clumsy for this little "
        f"mystery, so it would not make a funny speed clue. Pick one of: "
        f"{', '.join(sorted(v.id for v in VEHICLES.values() if sensible_speed(v)))}.)"
    )


def explain_combo(vehicle: Vehicle, bubble_maker: BubbleMaker) -> str:
    return (
        f"(No story: {vehicle.label} and {bubble_maker.label} do not leave both the "
        f"wheel clue and the bubble clue, so the detective would not have a fair mystery.)"
    )


@dataclass
class StoryParams:
    room: str
    helper: str
    vehicle: str
    bubble_maker: str
    food: str
    detective_name: str
    detective_type: str
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


def setup_scene(world: World, detective: Entity, helper: Entity, room: Room, food: Food) -> None:
    detective.memes["joy"] += 1
    world.say(
        f"On family supper night, {detective.id} hurried into {room.phrase} and stopped short. "
        f"The big dish of {food.label} that had been steaming on the table was gone."
    )
    world.say(
        f"The room still smelled like {food.smell}, and that made the mystery feel even bigger."
    )
    world.say(
        f'"A supper whodunit!" {detective.id} whispered, standing as straight as a tiny detective.'
    )
    world.say(
        f'{helper.title} was nearby, looking busy but kind. "{helper.hurry_text}"'
    )


def disappearance(world: World, detective: Entity, helper: Entity, vehicle: Vehicle, bubble_maker: BubbleMaker) -> None:
    tray = world.get("tray")
    tray.meters["moved"] += 1
    tray.attrs["moved_by"] = "bubble_machine"
    world.get("vehicle").meters["rolling"] += 1
    world.get("bubble_machine").meters["blowing"] += 1
    helper.memes["flustered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, from the hall, came {vehicle.silly_sound} and a string of shiny bubble trails."
    )
    world.say(
        f"{detective.id} blinked. Something had gone by at great speed."
    )


def repeated_question(world: World, detective: Entity, suspects: list[Entity]) -> None:
    detective.memes["methodical"] += 1
    line = '"Who took the manicotti?"'
    world.say(
        f"{detective.id} asked the same question again and again, because good detectives like to listen for what stays the same."
    )
    for suspect in suspects:
        suspect.memes["asked"] += 1
        world.say(f"{line} {detective.pronoun()} asked {suspect.id}.")
        reply = suspect.attrs.get("reply", "I do not know.")
        world.say(f'"{reply}"')
    world.facts["repeated_line"] = "Who took the manicotti?"


def investigate(world: World, detective: Entity, room: Room, vehicle: Vehicle, bubble_maker: BubbleMaker) -> None:
    detective.memes["quest"] += 1
    hall = world.get("hall")
    speed = int(hall.meters["speed"])
    world.say(
        f"Then {detective.id} noticed two clues in the hall: round wet bubble marks and quick little wheel tracks."
    )
    world.say(
        f"The wheel marks zipped toward {room.hiding_spot} with such speed that even the dust looked surprised."
    )
    if speed >= 3:
        world.say(
            f'"Too fast for sleepy feet," {detective.id} said. "That means wheels, and bubbles too."'
        )
    world.say(
        f"So the quest began. {detective.id} followed the bubble, followed the bubble, followed the bubble all the way down the hall."
    )
    world.facts["found_clues"] = ["bubble", "wheel tracks"]


def reveal(world: World, detective: Entity, helper: Entity, room: Room, vehicle: Vehicle, bubble_maker: BubbleMaker, food: Food) -> None:
    tray = world.get("tray")
    tray.attrs["location"] = room.hiding_spot
    detective.memes["triumph"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"Behind {room.hiding_spot}, {detective.id} found the missing tray of {food.label} riding on {vehicle.phrase} beside {bubble_maker.phrase}."
    )
    world.say(
        f'"Aha!" {detective.id} cried. "The bubbles did not eat the manicotti. They pointed at it."'
    )
    world.say(
        f"{helper.title} laughed and covered {helper.pronoun('possessive')} mouth. "
        f'"I moved it in a hurry so the bubbles would not splash supper, and then I forgot where I parked it."'
    )
    world.say(
        f"{bubble_maker.burst_text} One last bubble popped on the handle as if it had been trying to confess."
    )


def ending(world: World, detective: Entity, helper: Entity, food: Food) -> None:
    detective.memes["safe"] += 1
    helper.memes["love"] += 1
    world.say(
        f"Everyone carried the tray back together, much more slowly this time."
    )
    world.say(
        f'Soon the family was eating warm {food.label}, and every time a new bubble floated by, {detective.id} grinned and said, "Case closed."'
    )
    world.say(
        f"They all laughed, because the mystery had been solved, supper had been saved, and nobody hurried quite so wildly again."
    )


def tell(
    room: Room,
    helper_cfg: Helper,
    vehicle_cfg: Vehicle,
    bubble_cfg: BubbleMaker,
    food_cfg: Food,
    detective_name: str = "Mina",
    detective_type: str = "girl",
    trait: str = "nosy",
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        label=detective_name,
        role="detective",
        traits=[trait, "small"],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_cfg.title,
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        traits=["busy"],
        attrs={},
    ))
    suspect1 = world.add(Entity(
        id="Grandpa",
        kind="character",
        type="man",
        label="grandpa",
        role="suspect",
        attrs={"reply": "Not me. I only heard a tiny zoom and saw a bubble on my shoe."},
    ))
    suspect2 = world.add(Entity(
        id="Cousin Jo",
        kind="character",
        type="girl",
        label="cousin",
        role="suspect",
        attrs={"reply": "Not me. I saw wheels scoot by, and I laughed too hard to chase them."},
    ))
    world.add(Entity(
        id="tray",
        kind="thing",
        type="tray",
        label="tray of manicotti",
        attrs={"location": "table", "moved_by": ""},
    ))
    world.add(Entity(
        id="vehicle",
        kind="thing",
        type="vehicle",
        label=vehicle_cfg.label,
        attrs={"speed": vehicle_cfg.speed},
    ))
    world.add(Entity(
        id="bubble_machine",
        kind="thing",
        type="machine",
        label=bubble_cfg.label,
        attrs={},
    ))
    world.add(Entity(id="hall", kind="thing", type="hall", label="hall", attrs={}))

    setup_scene(world, detective, helper, room, food_cfg)
    world.para()
    disappearance(world, detective, helper, vehicle_cfg, bubble_cfg)
    repeated_question(world, detective, [suspect1, suspect2, helper])
    world.para()
    investigate(world, detective, room, vehicle_cfg, bubble_cfg)
    world.para()
    reveal(world, detective, helper, room, vehicle_cfg, bubble_cfg, food_cfg)
    ending(world, detective, helper, food_cfg)

    world.facts.update(
        detective=detective,
        helper=helper,
        room=room,
        vehicle=vehicle_cfg,
        bubble_maker=bubble_cfg,
        food=food_cfg,
        suspects=[suspect1, suspect2, helper],
        culprit="bubble_machine",
        culprit_kind="a hurried cleanup with the bubble machine and rolling cart",
        found_location=room.hiding_spot,
        repeated_line=world.facts.get("repeated_line", "Who took the manicotti?"),
        found_clues=world.facts.get("found_clues", []),
        solved=detective.memes["triumph"] >= THRESHOLD,
    )
    return world


ROOMS = {
    "kitchen": Room(
        id="kitchen",
        label="kitchen",
        phrase="the bright kitchen",
        hiding_spot="the pantry door",
        tags={"kitchen"},
    ),
    "dining_room": Room(
        id="dining_room",
        label="dining room",
        phrase="the cheerful dining room",
        hiding_spot="the sideboard",
        tags={"dining_room"},
    ),
    "sunroom": Room(
        id="sunroom",
        label="sunroom",
        phrase="the sunny little supper room",
        hiding_spot="the curtain by the plant stand",
        tags={"sunroom"},
    ),
}

HELPERS = {
    "aunt": Helper(
        id="aunt",
        type="aunt",
        label="the aunt",
        title="Aunt Poppy",
        hurry_text="I only turned around for one second.",
        safe_text="next time we will slow down",
        tags={"adult"},
    ),
    "mom": Helper(
        id="mom",
        type="mother",
        label="the mother",
        title="Mom",
        hurry_text="I was setting spoons and lost track of the tray.",
        safe_text="next time we will slow down",
        tags={"adult"},
    ),
    "uncle": Helper(
        id="uncle",
        type="uncle",
        label="the uncle",
        title="Uncle Ben",
        hurry_text="I heard a funny zoom and then the table was empty.",
        safe_text="next time we will slow down",
        tags={"adult"},
    ),
}

VEHICLES = {
    "cart": Vehicle(
        id="cart",
        label="rolling cart",
        phrase="a little rolling cart",
        motion="rolled",
        silly_sound="whirr-whirr",
        speed=3,
        leaves_wheels=True,
        tags={"wheels", "speed"},
    ),
    "stool": Vehicle(
        id="stool",
        label="wheeled stool",
        phrase="a wheeled stool",
        motion="scooted",
        silly_sound="zip-zip",
        speed=2,
        leaves_wheels=True,
        tags={"wheels", "speed"},
    ),
    "wagon": Vehicle(
        id="wagon",
        label="red wagon",
        phrase="a red wagon",
        motion="clattered",
        silly_sound="clack-clack",
        speed=1,
        leaves_wheels=True,
        tags={"wheels"},
    ),
}

BUBBLE_MAKERS = {
    "machine": BubbleMaker(
        id="machine",
        label="bubble machine",
        phrase="a humming bubble machine",
        burst_text="A silvery bubble wobbled above the tray",
        leaves_bubbles=True,
        tags={"bubble"},
    ),
    "wand": BubbleMaker(
        id="wand",
        label="bubble wand fan",
        phrase="a blinking bubble wand fan",
        burst_text="A fat bubble drifted in a loop",
        leaves_bubbles=True,
        tags={"bubble"},
    ),
}

FOODS = {
    "manicotti": Food(
        id="manicotti",
        label="manicotti",
        phrase="a tray of manicotti",
        smell="warm cheese and tomato sauce",
        tags={"manicotti", "food"},
    ),
}

GIRL_NAMES = ["Mina", "Ruby", "Lila", "Nora", "Tess", "Ivy"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Finn", "Eli", "Max"]
TRAITS = ["nosy", "careful", "funny", "quick", "bright"]

KNOWLEDGE = {
    "bubble": [
        ("What is a bubble?", "A bubble is a tiny ball of soapy water filled with air. It can float for a moment and then pop.")
    ],
    "speed": [
        ("What does speed mean?", "Speed means how fast something moves. Wheels can make a cart move with more speed than walking feet.")
    ],
    "manicotti": [
        ("What is manicotti?", "Manicotti is a kind of pasta tube that is usually filled and baked with sauce and cheese. People often serve it warm for supper.")
    ],
    "wheels": [
        ("Why do wheels leave tracks?", "Wheels press on dust or crumbs as they roll. That can leave little lines behind for sharp eyes to notice.")
    ],
    "mystery": [
        ("What does a detective do?", "A detective looks for clues and asks careful questions. Then the detective uses those clues to figure out what happened.")
    ],
}
KNOWLEDGE_ORDER = ["bubble", "speed", "manicotti", "wheels", "mystery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    room = f["room"]
    return [
        'Write a funny little whodunit for a 3-to-5-year-old that includes the words "bubble", "speed", and "manicotti".',
        f"Tell a child-facing mystery where {detective.id} asks the same question more than once, follows silly clues through {room.label}, and solves the case of the missing manicotti.",
        f"Write a gentle quest story with repetition and humor where {helper.id} is part of the confusion, but the ending is warm and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    room = f["room"]
    food = f["food"]
    vehicle = f["vehicle"]
    bubble_maker = f["bubble_maker"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a tiny detective, and {helper.id}, who was hurrying at supper time. They are trying to solve the mystery of the missing {food.label}."
        ),
        (
            f"What was missing?",
            f"A tray of {food.label} was missing from the supper table. The smell was still in the room, which made the mystery feel real and funny at the same time."
        ),
        (
            f"What question did {detective.id} keep asking?",
            f'{detective.id} kept asking, "{f["repeated_line"]}" {detective.pronoun().capitalize()} repeated it to each suspect so the answers could be compared.'
        ),
        (
            "What clues helped solve the case?",
            f"{detective.id} found bubble marks and wheel tracks in the hall. Those two clues pointed to {bubble_maker.label} and {vehicle.label}, not to a hungry person."
        ),
        (
            "Who really took the manicotti?",
            f"No one stole it to eat it. {helper.id} had moved it in a hurry with {vehicle.phrase} beside {bubble_maker.phrase}, then forgot where it was parked."
        ),
        (
            "How did the story end?",
            f"{detective.id} found the tray behind {room.hiding_spot}, and the family carried it back slowly together. They ate warm {food.label} and laughed about the silly mystery."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bubble", "speed", "manicotti", "mystery"}
    tags |= set(world.facts["vehicle"].tags)
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="kitchen",
        helper="aunt",
        vehicle="cart",
        bubble_maker="machine",
        food="manicotti",
        detective_name="Mina",
        detective_type="girl",
        trait="bright",
    ),
    StoryParams(
        room="dining_room",
        helper="mom",
        vehicle="stool",
        bubble_maker="wand",
        food="manicotti",
        detective_name="Theo",
        detective_type="boy",
        trait="careful",
    ),
    StoryParams(
        room="sunroom",
        helper="uncle",
        vehicle="cart",
        bubble_maker="wand",
        food="manicotti",
        detective_name="Ruby",
        detective_type="girl",
        trait="funny",
    ),
]


ASP_RULES = r"""
valid(Room, Helper, Vehicle, Bubble) :-
    room(Room), helper(Helper), vehicle(Vehicle), bubble_maker(Bubble),
    leaves_wheels(Vehicle), leaves_bubbles(Bubble),
    speed(Vehicle, S), sense_min(M), S >= M.

sensible_vehicle(Vehicle) :- vehicle(Vehicle), speed(Vehicle, S), sense_min(M), S >= M.

culprit(bubble_machine) :- chosen_vehicle(V), chosen_bubble(B),
                           leaves_wheels(V), leaves_bubbles(B),
                           speed(V, S), sense_min(M), S >= M.

solvable :- culprit(bubble_machine).
outcome(solved) :- solvable.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for vid, v in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        lines.append(asp.fact("speed", vid, v.speed))
        if v.leaves_wheels:
            lines.append(asp.fact("leaves_wheels", vid))
    for bid, b in BUBBLE_MAKERS.items():
        lines.append(asp.fact("bubble_maker", bid))
        if b.leaves_bubbles:
            lines.append(asp.fact("leaves_bubbles", bid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_vehicles() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_vehicle/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible_vehicle"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_vehicle", params.vehicle),
        asp.fact("chosen_bubble", params.bubble_maker),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    vehicle = VEHICLES[params.vehicle]
    bubble = BUBBLE_MAKERS[params.bubble_maker]
    return "solved" if valid_move(vehicle, bubble) and sensible_speed(vehicle) else "?"


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

    c_sens = set(asp_sensible_vehicles())
    p_sens = {v.id for v in VEHICLES.values() if sensible_speed(v)}
    if c_sens == p_sens:
        print(f"OK: sensible vehicles match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible vehicles: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a bubble-filled manicotti whodunit with a little quest."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--bubble-maker", dest="bubble_maker", choices=BUBBLE_MAKERS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vehicle:
        vehicle = VEHICLES[args.vehicle]
        if not sensible_speed(vehicle):
            raise StoryError(explain_vehicle(vehicle))
    if args.vehicle and args.bubble_maker:
        vehicle = VEHICLES[args.vehicle]
        bubble = BUBBLE_MAKERS[args.bubble_maker]
        if not valid_move(vehicle, bubble):
            raise StoryError(explain_combo(vehicle, bubble))

    combos = [
        c for c in valid_combos()
        if (args.room is None or c[0] == args.room)
        and (args.helper is None or c[1] == args.helper)
        and (args.vehicle is None or c[2] == args.vehicle)
        and (args.bubble_maker is None or c[3] == args.bubble_maker)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room, helper, vehicle, bubble_maker = rng.choice(sorted(combos))
    detective_type = args.gender or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    food = args.food or "manicotti"
    if food not in FOODS:
        raise StoryError(f"(Unknown food '{food}'.)")
    return StoryParams(
        room=room,
        helper=helper,
        vehicle=vehicle,
        bubble_maker=bubble_maker,
        food=food,
        detective_name=detective_name,
        detective_type=detective_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room '{params.room}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.vehicle not in VEHICLES:
        raise StoryError(f"(Unknown vehicle '{params.vehicle}'.)")
    if params.bubble_maker not in BUBBLE_MAKERS:
        raise StoryError(f"(Unknown bubble maker '{params.bubble_maker}'.)")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food '{params.food}'.)")
    if not valid_move(VEHICLES[params.vehicle], BUBBLE_MAKERS[params.bubble_maker]):
        raise StoryError(explain_combo(VEHICLES[params.vehicle], BUBBLE_MAKERS[params.bubble_maker]))
    if not sensible_speed(VEHICLES[params.vehicle]):
        raise StoryError(explain_vehicle(VEHICLES[params.vehicle]))

    world = tell(
        room=ROOMS[params.room],
        helper_cfg=HELPERS[params.helper],
        vehicle_cfg=VEHICLES[params.vehicle],
        bubble_cfg=BUBBLE_MAKERS[params.bubble_maker],
        food_cfg=FOODS[params.food],
        detective_name=params.detective_name,
        detective_type=params.detective_type,
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
        print(asp_program("", "#show valid/4.\n#show sensible_vehicle/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible vehicles: {', '.join(asp_sensible_vehicles())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, helper, vehicle, bubble_maker) combos:\n")
        for room, helper, vehicle, bubble_maker in combos:
            print(f"  {room:12} {helper:8} {vehicle:8} {bubble_maker}")
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
                f"### {p.detective_name}: {p.food} mystery in {p.room} "
                f"({p.helper}, {p.vehicle}, {p.bubble_maker})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
