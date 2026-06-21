#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stain_twist_ghost_story.py
=====================================================

A standalone story world for a child-facing ghost story with a twist:
something in the dark looks haunting, but the world model reveals that the
"ghost" is only a stain with an ordinary cause.

This world is built around a small set of compatible triples:

    cause + location + inspection tool

The reasonableness gate refuses mismatches. A foggy soap handprint belongs on a
mirror, not a curtain. Old glow-paint stars belong on a wall, not a mirror. The
inspection tool must also make sense: a damp cloth can clear soap or berry
smears, while morning light can reveal old glow paint or tiny paw tracks.

The story itself is state-driven:
- a child arrives in a creaky room
- a strange stain is noticed in the dark
- fear rises
- the child asks for help or peers closer
- the chosen inspection produces a clue
- the twist lands: there was no ghost after all
- the ending image proves the room has changed from scary to safe

Run it
------
    python storyworlds/worlds/gpt-5.4/stain_twist_ghost_story.py
    python storyworlds/worlds/gpt-5.4/stain_twist_ghost_story.py --cause soap_fog --location mirror --tool cloth
    python storyworlds/worlds/gpt-5.4/stain_twist_ghost_story.py --cause glow_paint --location mirror
    python storyworlds/worlds/gpt-5.4/stain_twist_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/stain_twist_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/stain_twist_ghost_story.py --asp
    python storyworlds/worlds/gpt-5.4/stain_twist_ghost_story.py --verify
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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
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
class RoomStyle:
    id: str
    place: str
    opening: str
    hush: str
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
class Cause:
    id: str
    label: str
    material: str
    color: str
    source: str
    ghost_shape: str
    fear_line: str
    reveal_line: str
    allowed_locations: set[str] = field(default_factory=set)
    tools: set[str] = field(default_factory=set)
    wipeable: bool = False
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
class Location:
    id: str
    label: str
    phrase: str
    night_image: str
    clue_phrase: str
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    night_proof: bool = False
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


def _r_eerie(world: World) -> list[str]:
    room = world.get("room")
    stain = world.get("stain")
    child = world.get("child")
    if stain.meters["visible"] < THRESHOLD:
        return []
    sig = ("eerie",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.memes["eerie"] += 1
    child.memes["fear"] += 1
    return []


def _r_understood(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    stain = world.get("stain")
    if stain.meters["explained"] < THRESHOLD:
        return []
    sig = ("understood",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["bravery"] += 1
    helper.memes["calm"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="eerie", tag="mood", apply=_r_eerie),
    Rule(name="understood", tag="mood", apply=_r_understood),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(cause_id: str, location_id: str, tool_id: str) -> bool:
    if cause_id not in CAUSES or location_id not in LOCATIONS or tool_id not in TOOLS:
        return False
    cause = CAUSES[cause_id]
    return location_id in cause.allowed_locations and tool_id in cause.tools


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for cause_id, cause in CAUSES.items():
        for location_id in sorted(cause.allowed_locations):
            for tool_id in sorted(cause.tools):
                out.append((cause_id, location_id, tool_id))
    return sorted(out)


def outcome_of(params: "StoryParams") -> str:
    tool = TOOLS[params.tool]
    return "night_twist" if tool.night_proof else "morning_twist"


def explain_rejection(cause_id: Optional[str], location_id: Optional[str], tool_id: Optional[str]) -> str:
    if cause_id and location_id and cause_id in CAUSES and location_id in LOCATIONS:
        cause = CAUSES[cause_id]
        location = LOCATIONS[location_id]
        if location_id not in cause.allowed_locations:
            places = ", ".join(sorted(cause.allowed_locations))
            return (
                f"(No story: {cause.label} does not belong on the {location.label}. "
                f"In this world it plausibly appears on: {places}.)"
            )
    if cause_id and tool_id and cause_id in CAUSES and tool_id in TOOLS:
        cause = CAUSES[cause_id]
        tool = TOOLS[tool_id]
        if tool_id not in cause.tools:
            options = ", ".join(sorted(cause.tools))
            return (
                f"(No story: {tool.label} would not honestly reveal {cause.label}. "
                f"Try one of: {options}.)"
            )
    return "(No valid combination matches the given options.)"


def predict_reveal(cause: Cause, tool: Tool) -> dict:
    return {
        "night_proof": tool.night_proof,
        "wipeable": cause.wipeable and tool.id == "cloth",
    }


def introduce(world: World, child: Entity, helper: Entity, room_style: RoomStyle) -> None:
    world.say(
        f"That night, {child.id} slept in {room_style.place}. {room_style.opening} "
        f"{room_style.hush}"
    )
    world.say(
        f"{helper.id}, {child.pronoun('possessive')} {helper.label_word}, tucked the blanket under "
        f"{child.pronoun('possessive')} chin and left a small bell on the table just in case."
    )


def settle_in(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"For a while, {child.id} listened to the house breathe and watched moonlight slide across the room."
    )


def spot_stain(world: World, child: Entity, cause: Cause, location: Location) -> None:
    stain = world.get("stain")
    stain.meters["visible"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {child.pronoun('subject')} saw it: a {cause.color} stain on {location.phrase}. "
        f"In the dark it looked like {cause.ghost_shape}."
    )
    world.say(cause.fear_line)


def call_for_help(world: World, child: Entity, helper: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f'"{helper.label_word.capitalize()}?" {child.id} whispered. "{child.pronoun().capitalize()} think there is a ghost."'
    )
    world.say(
        f"{helper.id} came back in soft slippers and did not laugh. "
        f"{helper.pronoun().capitalize()} sat beside {child.pronoun('object')} and listened."
    )


def inspect(world: World, child: Entity, helper: Entity, cause: Cause, location: Location, tool: Tool) -> None:
    world.say(
        f'Together they used {tool.phrase}. {helper.id} {tool.action} near {location.phrase}, and both of them leaned close.'
    )
    pred = predict_reveal(cause, tool)
    world.facts["night_proof"] = pred["night_proof"]
    world.facts["wipeable"] = pred["wipeable"]
    stain = world.get("stain")
    if pred["wipeable"]:
        stain.meters["smeared"] += 1
        world.say(
            f"The mark softened at once. A little {cause.color} smear came away on the cloth."
        )
    elif pred["night_proof"]:
        stain.meters["clue_seen"] += 1
        world.say(cause.reveal_line.format(location=location.clue_phrase))
    else:
        world.say(
            f"The room stayed hushy and gray. They could tell the stain was real, but not yet what had made it."
        )


def reveal_twist(world: World, child: Entity, helper: Entity, cause: Cause, tool: Tool) -> None:
    stain = world.get("stain")
    outcome = "night_twist" if tool.night_proof else "morning_twist"
    if outcome == "night_twist":
        stain.meters["explained"] += 1
        propagate(world, narrate=False)
        world.say(
            f'"Not a ghost," {helper.id} said gently. "{cause.source}."'
        )
        if cause.id == "berry_paws":
            world.say(
                "Right then a small cat stepped from under the chair, holding up one guilty purple paw. "
                f"{child.id} stared for a beat, and then the whole mystery tipped over into a laugh."
            )
        elif cause.id == "soap_fog":
            world.say(
                "The white shape was only dried soap left after a steamy bath. "
                f"Once they knew that, the handprint stopped feeling spooky at all."
            )
        else:
            world.say(
                "In the light, the pale blotches turned into old star paint that had soaked into the wall years ago. "
                "They had glowed just enough to pretend to be a face."
            )
    else:
        world.say(
            f'"We will let morning help us," {helper.id} said. "{helper.pronoun().capitalize()} do not have to solve every shadow tonight."'
        )
        world.para()
        world.say(
            "When dawn finally thinned the dark, the room looked smaller and kinder."
        )
        stain.meters["explained"] += 1
        propagate(world, narrate=False)
        if cause.id == "glow_paint":
            world.say(
                "Sunlight showed the old outlines of tiny star stickers around the stain. "
                "It was not a ghost face at all, only leftover glow paint from someone else's bedtime sky."
            )
        else:
            world.say(
                f"In the clear morning light, they saw what the dark had hidden: {cause.source}. "
                "The night shape had only been a trick of shadow."
            )


def close_story(world: World, child: Entity, helper: Entity, room_style: RoomStyle, cause: Cause) -> None:
    if cause.id == "berry_paws":
        world.say(
            f"{helper.id} washed the little stain away, then set a saucer of water on the floor for the cat."
        )
    elif cause.id == "soap_fog":
        world.say(
            f"{helper.id} polished the last of the stain off the glass until the mirror held only lamplight and sleepy faces."
        )
    else:
        world.say(
            f"{helper.id} traced the old star shapes with one finger and promised they could paint a fresh moon there another day."
        )
    world.say(
        f"Soon {child.id} lay down again. {room_style.ending}"
    )
def tell(
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_type: HelperType,
    trait: Trait,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={},
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=room_style.place,
        attrs={},
    ))
    stain = world.add(Entity(
        id="stain",
        type="stain",
        label="the stain",
        attrs={"cause": cause.id, "location": location.id, "tool": tool.id},
    ))

    world.facts.update(
        room_style=room_style,
        cause=cause,
        location=location,
        tool=tool,
        child=child,
        helper=helper,
        outcome=outcome_of(StoryParams(
            room=room_style.id,
            cause=cause.id,
            location=location.id,
            tool=tool.id,
            child_name=child_name,
            child_gender=child_gender,
            helper_name=helper_name,
            helper_type=helper_type,
            trait=trait,
            seed=None,
        )),
        night_proof=False,
        wipeable=False,
    )

    introduce(world, child, helper, room_style)
    settle_in(world, child)

    world.para()
    spot_stain(world, child, cause, location)
    call_for_help(world, child, helper)

    world.para()
    inspect(world, child, helper, cause, location, tool)
    reveal_twist(world, child, helper, cause, tool)

    world.para()
    close_story(world, child, helper, room_style, cause)

    world.facts.update(
        explained=stain.meters["explained"] >= THRESHOLD,
        smeared=stain.meters["smeared"] >= THRESHOLD,
        child_fear=child.memes["fear"],
        child_relief=child.memes["relief"],
    )
    return world
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


ROOMS = {
    "guest_room": RoomStyle(
        id="guest_room",
        place="her great-aunt's guest room",
        opening="The ceiling beams were dark as tree branches, and the wallpaper had tiny silver moons.",
        hush="Every floorboard gave one soft creak, as if the room were trying not to wake anybody.",
        ending="The shadows still reached long across the floor, but now they looked like ordinary shadows doing their ordinary job.",
        tags={"room", "night"},
    ),
    "attic_room": RoomStyle(
        id="attic_room",
        place="the little attic room",
        opening="The slanted ceiling made the bed feel tucked inside a secret.",
        hush="Wind rubbed the roof with a whisper like a broom on paper.",
        ending="The attic still hummed with old-house sounds, yet none of them felt lonely anymore.",
        tags={"room", "night"},
    ),
    "hall_nook": RoomStyle(
        id="hall_nook",
        place="the narrow hall nook beside the stairs",
        opening="A round window poured in moonlight, and the coat hooks looked taller than they did in daytime.",
        hush="Somewhere below, the old clock gave careful little ticks.",
        ending="Even the clock seemed friendlier, as if it had been keeping watch all along.",
        tags={"room", "night"},
    ),
}

LOCATIONS = {
    "mirror": Location(
        id="mirror",
        label="mirror",
        phrase="the old mirror",
        night_image="the glass held a milky blur",
        clue_phrase="the glass",
        tags={"mirror"},
    ),
    "curtain": Location(
        id="curtain",
        label="curtain",
        phrase="the lace curtain",
        night_image="the lace moved like a sleeve",
        clue_phrase="the curtain hem",
        tags={"curtain"},
    ),
    "wall": Location(
        id="wall",
        label="wall",
        phrase="the pale wall above the bed",
        night_image="the wall kept a greenish blotch",
        clue_phrase="the wall",
        tags={"wall"},
    ),
}

CAUSES = {
    "berry_paws": Cause(
        id="berry_paws",
        label="berry paw marks",
        material="berry juice",
        color="violet",
        source="the cat's berry-stained paws after stealing a taste of pie",
        ghost_shape="a waving little ghost with two ears",
        fear_line="The stain wobbled when the curtain stirred, and for one chilly moment it seemed to raise an arm at her.",
        reveal_line="A chain of tiny paw marks showed up along {location}, each one no bigger than a coin.",
        allowed_locations={"curtain"},
        tools={"cloth", "morning"},
        wipeable=True,
        tags={"stain", "cat", "berry"},
    ),
    "soap_fog": Cause(
        id="soap_fog",
        label="soap fog handprint",
        material="dried soap",
        color="chalky white",
        source="a handprint of dried soap from the steamy mirror after bath time",
        ghost_shape="a pale hand pressed from the other side of the glass",
        fear_line="It looked so much like fingers that her heart gave one hard thump.",
        reveal_line="Under the closer look, the white lines turned bubbly and streaky instead of ghostly.",
        allowed_locations={"mirror"},
        tools={"cloth"},
        wipeable=True,
        tags={"stain", "soap", "mirror"},
    ),
    "glow_paint": Cause(
        id="glow_paint",
        label="old glow-paint stain",
        material="glow paint",
        color="pale green",
        source="old glow paint left from star stickers that used to shine there",
        ghost_shape="a floating face with two round eyes",
        fear_line="Because the stain held its own faint green light, it truly did seem to be looking back.",
        reveal_line="The brighter beam woke more tiny green specks nearby, until the one face broke apart into a scatter of stars on {location}.",
        allowed_locations={"wall"},
        tools={"lantern", "morning"},
        wipeable=False,
        tags={"stain", "glow", "stars"},
    ),
}

TOOLS = {
    "cloth": Tool(
        id="cloth",
        label="a damp cloth",
        phrase="a damp cloth",
        action="pressed the cloth",
        night_proof=True,
        tags={"cloth", "cleaning"},
    ),
    "lantern": Tool(
        id="lantern",
        label="a lantern",
        phrase="a small brass lantern",
        action="lifted the lantern",
        night_proof=True,
        tags={"lantern", "light"},
    ),
    "morning": Tool(
        id="morning",
        label="morning light",
        phrase="the promise of morning light",
        action="waited for light",
        night_proof=False,
        tags={"morning", "light"},
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lucy", "Ada", "Rose", "June", "Willa"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Finn", "Eli", "Jude", "Noah", "Leo"]
HELPERS = [
    ("Grandma June", "grandmother"),
    ("Grandpa Ash", "grandfather"),
    ("Aunt May", "aunt"),
    ("Uncle Ben", "uncle"),
]
TRAITS = ["careful", "curious", "quiet", "brave", "thoughtful"]


KNOWLEDGE = {
    "stain": [
        (
            "What is a stain?",
            "A stain is a mark left on something by paint, juice, mud, soap, or another material. Some stains wipe away easily, and some stay longer.",
        )
    ],
    "mirror": [
        (
            "Why can a mirror look strange at night?",
            "A mirror only shows the light it gets. At night, a little moonlight or a blurry mark can make a shape look much stranger than it really is.",
        )
    ],
    "curtain": [
        (
            "Why do curtains look spooky when they move?",
            "Curtains are thin and light, so air can make them sway and change shape. In dim light, that movement can trick your eyes.",
        )
    ],
    "glow": [
        (
            "Why does glow paint shine in the dark?",
            "Glow paint saves up light and lets it out slowly later. That is why it can look bright after the lamp is turned off.",
        )
    ],
    "soap": [
        (
            "Why does soap leave marks on glass?",
            "When soapy water dries, it can leave pale streaks or prints behind. Those marks are only dried soap, not anything alive.",
        )
    ],
    "cat": [
        (
            "Why do cat paw prints show up in strange places?",
            "Cats step lightly and wander everywhere. If their paws get wet or sticky, they can leave tiny prints on floors, curtains, or chairs.",
        )
    ],
    "lantern": [
        (
            "Why is it easier to solve a mystery with light?",
            "Light shows colors, edges, and little clues that darkness hides. When you can see clearly, scary guesses often turn into ordinary answers.",
        )
    ],
    "cleaning": [
        (
            "What can a damp cloth do to a stain?",
            "A damp cloth can loosen some stains and wipe them away. If the mark smears onto the cloth, that is a clue that it is only a material mark.",
        )
    ],
    "morning": [
        (
            "Why do things look less scary in the morning?",
            "Morning light fills in shadows and makes shapes easier to see. When your eyes get more information, your brain has less room to imagine a monster.",
        )
    ],
}
KNOWLEDGE_ORDER = ["stain", "mirror", "curtain", "glow", "soap", "cat", "lantern", "cleaning", "morning"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    cause = f["cause"]
    location = f["location"]
    tool = f["tool"]
    outcome = f["outcome"]
    base = (
        f'Write a short ghost story for a 3-to-5-year-old that includes the word "stain" '
        f"and ends with a gentle twist."
    )
    if outcome == "night_twist":
        return [
            base,
            f"Tell a spooky-but-safe story where {child.id} sees a stain on the {location.label}, thinks it is a ghost, and {helper.id} helps solve the mystery that same night with {tool.phrase}.",
            f"Write a bedtime ghost story with a twist: the ghostly shape is really {cause.label}, and the ending should leave the room feeling safe again.",
        ]
    return [
        base,
        f"Tell a gentle ghost story where {child.id} sees a stain on the {location.label}, worries all night, and discovers in the morning that it was really {cause.label}.",
        "Write a story with a quiet, eerie beginning and a warm morning twist that explains the haunting shape in an ordinary way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    cause = f["cause"]
    location = f["location"]
    tool = f["tool"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who noticed something strange in the dark, and {helper.id}, who helped with the mystery. The story stays close to their room and to what they discover there.",
        ),
        (
            "What frightened the child at first?",
            f"{child.id} saw a {cause.color} stain on the {location.label}, and in the dark it looked like {cause.ghost_shape}. The dim light made an ordinary mark feel like a ghost.",
        ),
        (
            f"Why did {child.id} call for {helper.id}?",
            f"{child.id} felt scared and did not want to guess alone. Calling {helper.id} brought calm help into the room, which made it possible to check the stain instead of only fearing it.",
        ),
        (
            f"How did they investigate the stain?",
            f"They used {tool.phrase} and looked closely at the mark. The way they checked it mattered, because this tool was the honest way to find out what the stain really was.",
        ),
    ]
    if outcome == "night_twist":
        answer = f"It turned out to be {cause.source}. The clue came that same night, so the ghost idea broke apart as soon as they could really see what the stain was doing."
        qa.append(
            (
                "What was the twist in the story?",
                answer,
            )
        )
    else:
        answer = f"The twist was that the stain was ordinary all along: {cause.source}. They had to wait for morning light, because the dark room hid the clue they needed."
        qa.append(
            (
                "What was the twist in the story?",
                answer,
            )
        )
    if f.get("wipeable"):
        qa.append(
            (
                "How did the cloth help them know the truth?",
                f"When the cloth touched the stain, some of it smeared away at once. That showed it was only a real material mark and not any kind of ghost.",
            )
        )
    else:
        qa.append(
            (
                "How did the clue change the room at the end?",
                f"Once they understood the stain, the room stopped feeling haunted. The same shadows were still there, but now they belonged to an ordinary room with an ordinary story.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"stain"}
    tags |= set(f["location"].tags)
    tags |= set(f["cause"].tags)
    tags |= set(f["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)
@dataclass
class StoryParams:
    room: str
    cause: str
    location: str
    tool: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None




CURATED = [
    StoryParams(
        room="guest_room",
        cause="soap_fog",
        location="mirror",
        tool="cloth",
        child_name="Mina",
        child_gender="girl",
        helper_name="Grandma June",
        helper_type="grandmother",
        trait="careful",
        seed=None,
    ),
    StoryParams(
        room="attic_room",
        cause="glow_paint",
        location="wall",
        tool="lantern",
        child_name="Theo",
        child_gender="boy",
        helper_name="Aunt May",
        helper_type="aunt",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        room="hall_nook",
        cause="berry_paws",
        location="curtain",
        tool="morning",
        child_name="Lucy",
        child_gender="girl",
        helper_name="Grandpa Ash",
        helper_type="grandfather",
        trait="quiet",
        seed=None,
    ),
    StoryParams(
        room="guest_room",
        cause="glow_paint",
        location="wall",
        tool="morning",
        child_name="Owen",
        child_gender="boy",
        helper_name="Uncle Ben",
        helper_type="uncle",
        trait="thoughtful",
        seed=None,
    ),
    StoryParams(
        room="attic_room",
        cause="berry_paws",
        location="curtain",
        tool="cloth",
        child_name="Ivy",
        child_gender="girl",
        helper_name="Grandma June",
        helper_type="grandmother",
        trait="brave",
        seed=None,
    ),
]


ASP_RULES = r"""
valid(C,L,T) :- cause(C), location(L), tool(T), allowed(C,L), works_with(C,T).

night_twist :- chosen_tool(T), night_proof(T).
morning_twist :- chosen_tool(T), not night_proof(T).

outcome(night_twist) :- night_twist.
outcome(morning_twist) :- morning_twist.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for lid in LOCATIONS:
        lines.append(asp.fact("location", lid))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for lid in sorted(cause.allowed_locations):
            lines.append(asp.fact("allowed", cid, lid))
        for tid in sorted(cause.tools):
            lines.append(asp.fact("works_with", cid, tid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if tool.night_proof:
            lines.append(asp.fact("night_proof", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_tool", params.tool)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(100):
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

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a ghostly stain with a gentle twist. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[name for name, _ in HELPERS])
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
    if args.cause and args.location and args.tool:
        if not valid_combo(args.cause, args.location, args.tool):
            raise StoryError(explain_rejection(args.cause, args.location, args.tool))
    elif args.cause and args.location:
        if args.cause in CAUSES and args.location not in CAUSES[args.cause].allowed_locations:
            raise StoryError(explain_rejection(args.cause, args.location, args.tool))
    elif args.cause and args.tool:
        if args.cause in CAUSES and args.tool not in CAUSES[args.cause].tools:
            raise StoryError(explain_rejection(args.cause, args.location, args.tool))

    combos = [
        combo for combo in valid_combos()
        if (args.cause is None or combo[0] == args.cause)
        and (args.location is None or combo[1] == args.location)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError(explain_rejection(args.cause, args.location, args.tool))

    cause_id, location_id, tool_id = rng.choice(sorted(combos))
    room_id = args.room or rng.choice(sorted(ROOMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    if args.helper:
        helper_name = args.helper
        helper_type = next(ht for name, ht in HELPERS if name == helper_name)
    else:
        helper_name, helper_type = rng.choice(HELPERS)
    trait = rng.choice(TRAITS)

    return StoryParams(
        room=room_id,
        cause=cause_id,
        location=location_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.location not in LOCATIONS:
        raise StoryError(f"(Unknown location: {params.location})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if not valid_combo(params.cause, params.location, params.tool):
        raise StoryError(explain_rejection(params.cause, params.location, params.tool))

    world = tell(
        ROOMS[params.room],
        CAUSES[params.cause],
        LOCATIONS[params.location],
        TOOLS[params.tool],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (cause, location, tool) combos:\n")
        for cause_id, location_id, tool_id in combos:
            print(f"  {cause_id:12} {location_id:8} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.cause} on {p.location} ({p.tool}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
