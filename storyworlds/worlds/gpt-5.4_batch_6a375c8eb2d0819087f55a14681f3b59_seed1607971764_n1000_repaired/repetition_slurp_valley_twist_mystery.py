#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py
===================================================================

A standalone story world for a child-sized mystery tale: two children hear a
strange slurp in an echoing valley, follow a clue trail, and discover a twist.
What sounded like many hidden creatures is really one harmless drinker plus the
valley's echo.

The key constraint in this world is simple common sense:

- a place must plausibly echo
- a source must plausibly be in that place
- the chosen drink must be something that source would really slurp
- the chosen clue must be something that source would really leave behind

That reasonableness gate is implemented twice:
(1) in Python via `compatible(...)` / `valid_combos()`
(2) in an inline ASP twin via `ASP_RULES` / `asp_facts()`

Run it
------
    python storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py
    python storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py --place fern_hollow
    python storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py --source pony --drink berry_juice
    python storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py --all
    python storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py --asp
    python storyworlds/worlds/gpt-5.4/repetition_slurp_valley_twist_mystery.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


# ---------------------------------------------------------------------------
# Domain knobs
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path: str
    echo_text: str
    places_source: set[str] = field(default_factory=set)
    echo: bool = True
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
class Source:
    id: str
    label: str
    phrase: str
    step: str
    drink_ok: set[str] = field(default_factory=set)
    clue_ok: set[str] = field(default_factory=set)
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
class Drink:
    id: str
    label: str
    phrase: str
    color: str
    slurp_text: str
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
    discover: str
    meaning: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        return [e for e in self.entities.values() if e.role in {"lead", "companion"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Rules
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


def _r_echo(world: World) -> list[str]:
    place = world.get("place")
    source = world.get("source")
    if world.place.echo and source.meters["drinking"] >= THRESHOLD:
        sig = ("echo",)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["echo"] += 1
            place.meters["mystery"] += 1
            for kid in world.kids():
                kid.memes["fear"] += 1
                kid.memes["curiosity"] += 1
            world.facts["echo_started"] = True
    return []


def _r_clue(world: World) -> list[str]:
    lead = world.get("lead")
    if world.facts.get("clue_found") and not world.facts.get("revealed"):
        sig = ("clue_meaning", world.facts["clue_cfg"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            lead.memes["theory"] += 1
            lead.memes["confidence"] += 1
    return []


def _r_reveal(world: World) -> list[str]:
    if world.facts.get("revealed"):
        sig = ("relief",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["fear"] = 0.0
                kid.memes["joy"] += 1
                kid.memes["understanding"] += 1
            world.get("place").meters["mystery"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="echo", tag="physical", apply=_r_echo),
    Rule(name="clue", tag="inference", apply=_r_clue),
    Rule(name="reveal", tag="emotional", apply=_r_reveal),
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
# Constraints
# ---------------------------------------------------------------------------
def compatible(place: Place, source: Source, drink: Drink, clue: Clue) -> bool:
    return (
        place.echo
        and source.id in place.places_source
        and drink.id in source.drink_ok
        and clue.id in source.clue_ok
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            for drink_id, drink in DRINKS.items():
                for clue_id, clue in CLUES.items():
                    if compatible(place, source, drink, clue):
                        out.append((place_id, source_id, drink_id, clue_id))
    return sorted(out)


def explain_rejection(place: Place, source: Source, drink: Drink, clue: Clue) -> str:
    if not place.echo:
        return (
            f"(No story: {place.label} does not echo, so one slurp would not turn "
            f"into a proper mystery. Pick an echoing valley place.)"
        )
    if source.id not in place.places_source:
        return (
            f"(No story: a {source.label} does not belong in {place.label} here, "
            f"so the clue trail would feel ungrounded.)"
        )
    if drink.id not in source.drink_ok:
        return (
            f"(No story: a {source.label} would not sensibly be slurping {drink.label}. "
            f"Choose a drink that fits the source.)"
        )
    if clue.id not in source.clue_ok:
        return (
            f"(No story: a {source.label} would not leave {clue.phrase}. "
            f"Choose a clue that matches the source.)"
        )
    return "(No story: this combination does not make a sensible mystery.)"


# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------
def predict_mystery(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["drinking"] += 1
    propagate(sim, narrate=False)
    return {
        "echo": sim.get("place").meters["echo"] >= THRESHOLD,
        "fear": sum(k.memes["fear"] for k in sim.kids()),
        "curiosity": sum(k.memes["curiosity"] for k in sim.kids()),
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, lead: Entity, companion: Entity, place: Place) -> None:
    for kid in (lead, companion):
        kid.memes["calm"] += 1
    world.say(
        f"{lead.id} and {companion.id} were walking the narrow path into {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"They had come to look for the blue cornflowers that grew near {place.path}, "
        f"and they promised to stay together."
    )


def first_sound(world: World, lead: Entity, companion: Entity, drink: Drink) -> None:
    source = world.get("source")
    source.meters["drinking"] += 1
    propagate(world, narrate=False)
    pred = predict_mystery(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_curiosity"] = pred["curiosity"]
    world.say(
        f"Then they heard it: {drink.slurp_text}. The sound came once, and then the "
        f"repetition of it rolled back from the stone sides of the valley, making one "
        f"small noise sound like three."
    )
    world.say(
        f'{companion.id} stopped so fast that the grass brushed {companion.pronoun("possessive")} knees. '
        f'"Did you hear that slurp?" {companion.pronoun()} whispered.'
    )


def worry(world: World, lead: Entity, companion: Entity, place: Place) -> None:
    world.say(
        f"{lead.id} listened again. {place.echo_text} That only made the mystery feel deeper."
    )
    if companion.memes["fear"] >= THRESHOLD:
        world.say(
            f'{companion.id} took one step closer to {lead.id}. "It sounds as if something is hiding," '
            f"{companion.pronoun()} said."
        )


def decide_to_follow(world: World, lead: Entity, companion: Entity) -> None:
    lead.memes["bravery"] += 1
    companion.memes["trust"] += 1
    world.say(
        f'"Maybe it only sounds big because the valley keeps tossing the noise back," '
        f'{lead.id} said. "Let\'s look for a clue before we run away."'
    )


def find_clue(world: World, lead: Entity, companion: Entity, clue: Clue) -> None:
    world.facts["clue_found"] = True
    propagate(world, narrate=False)
    lead.meters["steps"] += 1
    companion.meters["steps"] += 1
    world.say(
        f"They followed the sound around a bend, moving slowly enough to hear the grass breathe. "
        f"Near a flat stone, {lead.id} found {clue.phrase}."
    )
    world.say(
        f"{clue.discover} {lead.id} knelt down and looked carefully. "
        f'"This means {clue.meaning}," {lead.pronoun()} said.'
    )


def false_guess(world: World, companion: Entity) -> None:
    companion.memes["fear"] += 1
    world.say(
        f'{companion.id} widened {companion.pronoun("possessive")} eyes. '
        f'"Then maybe there really are many creatures," {companion.pronoun()} whispered.'
    )


def reveal(world: World, lead: Entity, companion: Entity, source: Source, drink: Drink, clue: Clue) -> None:
    world.facts["revealed"] = True
    propagate(world, narrate=False)
    source.meters["seen"] += 1
    world.say(
        f"But when they peeked past the reeds, the twist was plain at last. There was only "
        f"{source.phrase}, standing by {drink.phrase} and making that soft {source.step} sound."
    )
    world.say(
        f"The clue had told the truth all along: {clue.meaning}. One harmless {source.label} was "
        f"doing the slurping, and the valley had been repeating the noise until it sounded crowded."
    )


def befriend(world: World, lead: Entity, companion: Entity, source: Source, drink: Drink) -> None:
    lead.memes["kindness"] += 1
    companion.memes["kindness"] += 1
    world.say(
        f"{lead.id} laughed first, and then {companion.id} laughed too, the frightened kind of laugh "
        f"that turns warm after the danger is gone."
    )
    world.say(
        f"They stood very still while the {source.label} lifted {source.pronoun('possessive')} head, "
        f"blinked at them, and went back to {drink.label}."
    )


def ending(world: World, lead: Entity, companion: Entity, place: Place) -> None:
    world.say(
        f"On the way home, the valley did not seem hungry or haunted anymore. It seemed clever."
    )
    world.say(
        f"The children could still hear the old repetition of their own footsteps on the stone, "
        f"but now it sounded like a game the hills were playing with them."
    )
    world.say(
        f"When they looked back at {place.label}, they waved instead of hurrying, because they knew "
        f"how the mystery worked."
    )


# ---------------------------------------------------------------------------
# Whole story
# ---------------------------------------------------------------------------
def tell(
    place: Place,
    source_cfg: Source,
    drink_cfg: Drink,
    clue_cfg: Clue,
    lead_name: str = "Mina",
    lead_type: str = "girl",
    companion_name: str = "Owen",
    companion_type: str = "boy",
) -> World:
    world = World(place=place)

    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_type,
        role="lead",
        label=lead_name,
        traits=["careful", "curious"],
        attrs={},
    ))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_type,
        role="companion",
        label=companion_name,
        traits=["gentle", "jumpy"],
        attrs={},
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=place.label,
        attrs={},
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type=source_cfg.id,
        label=source_cfg.label,
        attrs={"cfg": source_cfg.id},
    ))

    world.facts.update(
        place_cfg=place,
        source_cfg=source_cfg,
        drink_cfg=drink_cfg,
        clue_cfg=clue_cfg,
        lead=lead,
        companion=companion,
        clue_found=False,
        revealed=False,
        echo_started=False,
    )

    introduce(world, lead, companion, place)
    world.para()
    first_sound(world, lead, companion, drink_cfg)
    worry(world, lead, companion, place)
    decide_to_follow(world, lead, companion)
    world.para()
    find_clue(world, lead, companion, clue_cfg)
    false_guess(world, companion)
    world.para()
    reveal(world, lead, companion, source_cfg, drink_cfg, clue_cfg)
    befriend(world, lead, companion, source_cfg, drink_cfg)
    ending(world, lead, companion, place)

    world.facts.update(
        solved=True,
        twist=True,
        echo_is_cause=place_ent.meters["echo"] >= THRESHOLD or world.facts["echo_started"],
        fear_before=world.facts.get("predicted_fear", 0),
        curiosity_before=world.facts.get("predicted_curiosity", 0),
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "fern_hollow": Place(
        id="fern_hollow",
        label="Fern Hollow Valley",
        opening="The ferns on the banks were so tall that the path looked like a green hallway.",
        path="the cool stream bend",
        echo_text="A whisper there never stayed a whisper for long; the valley always sent it back in pieces.",
        places_source={"fawn", "hedgehog"},
        echo=True,
        tags={"valley", "echo"},
    ),
    "moon_ridge": Place(
        id="moon_ridge",
        label="Moon Ridge Valley",
        opening="Gray rocks stood on both sides like quiet giants, and the air smelled of mint and wet stone.",
        path="the sheep gate",
        echo_text="Even a pebble click could bounce from wall to wall and come back sounding busier than it was.",
        places_source={"pony", "goat"},
        echo=True,
        tags={"valley", "echo"},
    ),
    "bramble_pass": Place(
        id="bramble_pass",
        label="Bramble Pass Valley",
        opening="Blackberry vines looped over the path, and the late sun made the shadows look deeper than they were.",
        path="the berry patch",
        echo_text="The narrow sides of the valley folded each noise and unfolded it again from somewhere else.",
        places_source={"hedgehog", "goat"},
        echo=True,
        tags={"valley", "echo", "berries"},
    ),
}

SOURCES = {
    "fawn": Source(
        id="fawn",
        label="fawn",
        phrase="a shy fawn",
        step="nose-dipping",
        drink_ok={"water"},
        clue_ok={"small_hoofprints"},
        tags={"deer"},
    ),
    "hedgehog": Source(
        id="hedgehog",
        label="hedgehog",
        phrase="a round hedgehog",
        step="snuffling",
        drink_ok={"berry_juice", "milk"},
        clue_ok={"purple_drips"},
        tags={"hedgehog"},
    ),
    "pony": Source(
        id="pony",
        label="pony",
        phrase="a lost pony",
        step="muzzle-dipping",
        drink_ok={"water", "milk"},
        clue_ok={"large_hoofprints"},
        tags={"pony"},
    ),
    "goat": Source(
        id="goat",
        label="goat",
        phrase="a little hill goat",
        step="beard-swaying",
        drink_ok={"water"},
        clue_ok={"white_hair"},
        tags={"goat"},
    ),
}

DRINKS = {
    "water": Drink(
        id="water",
        label="water",
        phrase="a stone basin full of clear water",
        color="clear",
        slurp_text="slurp... slurp... slurp",
        tags={"water"},
    ),
    "berry_juice": Drink(
        id="berry_juice",
        label="berry juice",
        phrase="a cracked jar with a puddle of berry juice beside it",
        color="purple",
        slurp_text="slurp... slrrp... slurp",
        tags={"berries"},
    ),
    "milk": Drink(
        id="milk",
        label="milk",
        phrase="a tipped pail with a little milk still shining in the bottom",
        color="white",
        slurp_text="slurp... slup... slurp",
        tags={"milk"},
    ),
}

CLUES = {
    "small_hoofprints": Clue(
        id="small_hoofprints",
        label="small hoofprints",
        phrase="a trail of small hoofprints pressed into the damp soil",
        discover="They were neat and light, not wild and stompy.",
        meaning="something with small hooves came this way, and only one set of prints",
        tags={"tracks"},
    ),
    "large_hoofprints": Clue(
        id="large_hoofprints",
        label="large hoofprints",
        phrase="four round hoofprints beside a patch of bent grass",
        discover="The prints were deep, but they were not many.",
        meaning="one bigger animal stopped here for a drink, not a whole herd",
        tags={"tracks"},
    ),
    "purple_drips": Clue(
        id="purple_drips",
        label="purple drips",
        phrase="tiny purple drips on a flat stone and a few berry seeds nearby",
        discover="The stone smelled sweet, not scary.",
        meaning="someone had been sipping berry juice, and the mess was small",
        tags={"berries"},
    ),
    "white_hair": Clue(
        id="white_hair",
        label="white hair",
        phrase="a soft twist of white hair caught on a thorn",
        discover="It fluttered like a ribbon in the breeze.",
        meaning="a goat had squeezed through here alone",
        tags={"hair"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "Ivy", "Wren", "Ada", "June"]
BOY_NAMES = ["Owen", "Ben", "Eli", "Noah", "Theo", "Finn", "Milo", "Sam"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    source: str
    drink: str
    clue: str
    lead_name: str
    lead_gender: str
    companion_name: str
    companion_gender: str
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
    "valley": [
        (
            "What is a valley?",
            "A valley is low land between hills or mountains. Sounds can bounce around there because the sides are close enough to throw noise back."
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces off something hard and comes back to your ears. That can make one noise seem louder or repeated."
        )
    ],
    "tracks": [
        (
            "What can hoofprints tell you?",
            "Hoofprints can tell you that an animal with hooves walked there. Their size and number can also hint at whether one animal passed by or many."
        )
    ],
    "berries": [
        (
            "Why would berry juice leave a clue?",
            "Berry juice can drip and stain things purple. That makes it easy to spot where someone spilled or slurped it."
        )
    ],
    "deer": [
        (
            "What is a fawn?",
            "A fawn is a young deer. It is usually shy and gentle."
        )
    ],
    "hedgehog": [
        (
            "What is a hedgehog?",
            "A hedgehog is a small animal with tiny spikes on its back. It has a little nose for sniffing food and drink."
        )
    ],
    "pony": [
        (
            "What is a pony?",
            "A pony is a small kind of horse. Ponies can leave round hoofprints and make soft drinking sounds."
        )
    ],
    "goat": [
        (
            "What is a goat?",
            "A goat is an animal with hooves that likes to climb and squeeze through narrow places. A goat can leave hair on thorns or bushes."
        )
    ],
    "water": [
        (
            "Why can water make a slurp sound?",
            "When an animal drinks quickly, its mouth pulls the water in with a wet little noise. In a quiet place, that sound is easy to hear."
        )
    ],
    "milk": [
        (
            "Why might milk leave a white clue?",
            "Milk is pale, so drops or foam can stand out on dark ground or on fur. That makes it a useful clue in a story."
        )
    ],
}
KNOWLEDGE_ORDER = ["valley", "echo", "tracks", "berries", "deer", "hedgehog", "pony", "goat", "water", "milk"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place_cfg"]
    source = f["source_cfg"]
    drink = f["drink_cfg"]
    clue = f["clue_cfg"]
    lead = f["lead"]
    companion = f["companion"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the words "repetition", "slurp", and "valley".',
        f"Tell a gentle mystery where {lead.id} and {companion.id} hear a strange slurp in {place.label}, follow {clue.label}, and discover that the twist is only {source.phrase} by {drink.label}.",
        f"Write a child-facing mystery in which an echo makes one small sound seem bigger than it is, and end with the children understanding the valley instead of fearing it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    companion = f["companion"]
    place = f["place_cfg"]
    source = f["source_cfg"]
    drink = f["drink_cfg"]
    clue = f["clue_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {companion.id}, two children walking through {place.label}. They become little detectives when they hear the strange slurp."
        ),
        (
            "Why did the sound seem scary at first?",
            f"It sounded scary because the valley kept repeating the noise, so one slurp seemed like several hidden sounds. That made the children think something bigger might be hiding nearby."
        ),
        (
            "What clue did the children find?",
            f"They found {clue.phrase}. The clue mattered because it showed that the sound came from one real creature, not from many secret ones."
        ),
        (
            "What was the twist in the mystery?",
            f"The twist was that there was only {source.phrase}, not a whole crowd of creatures. The valley's echo had stretched one small drinking sound into a much bigger mystery."
        ),
        (
            "How did the children feel at the end?",
            f"They felt relieved and happy instead of frightened. Once they understood the echo, the valley seemed clever and friendly rather than spooky."
        ),
    ]
    qa.append(
        (
            f"Why did {lead.id} choose to follow the clue instead of running home?",
            f"{lead.id} guessed that the valley might be changing the sound, so a clue would tell the truth better than fear would. Following the clue led them to {source.phrase} by {drink.phrase}."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"valley", "echo"} | set(f["source_cfg"].tags) | set(f["drink_cfg"].tags) | set(f["clue_cfg"].tags)
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible(P,S,D,C) :- place(P), source(S), drink(D), clue(C),
                       echo_place(P),
                       allows(P,S),
                       drinks(S,D),
                       leaves(S,C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.echo:
            lines.append(asp.fact("echo_place", pid))
        for sid in sorted(place.places_source):
            lines.append(asp.fact("allows", pid, sid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        for did in sorted(source.drink_ok):
            lines.append(asp.fact("drinks", sid, did))
        for cid in sorted(source.clue_ok):
            lines.append(asp.fact("leaves", sid, cid))
    for did in DRINKS:
        lines.append(asp.fact("drink", did))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    try:
        params = CURATED[0]
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify smoke test.")
        emit(sample, trace=False, qa=False, header="verify-smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="fern_hollow",
        source="fawn",
        drink="water",
        clue="small_hoofprints",
        lead_name="Mina",
        lead_gender="girl",
        companion_name="Owen",
        companion_gender="boy",
    ),
    StoryParams(
        place="bramble_pass",
        source="hedgehog",
        drink="berry_juice",
        clue="purple_drips",
        lead_name="Lila",
        lead_gender="girl",
        companion_name="Finn",
        companion_gender="boy",
    ),
    StoryParams(
        place="moon_ridge",
        source="pony",
        drink="milk",
        clue="large_hoofprints",
        lead_name="Tess",
        lead_gender="girl",
        companion_name="Sam",
        companion_gender="boy",
    ),
    StoryParams(
        place="moon_ridge",
        source="goat",
        drink="water",
        clue="white_hair",
        lead_name="Ben",
        lead_gender="boy",
        companion_name="Ivy",
        companion_gender="girl",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: an echoing valley mystery with a harmless twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.drink and args.clue:
        place = PLACES[args.place]
        source = SOURCES[args.source]
        drink = DRINKS[args.drink]
        clue = CLUES[args.clue]
        if not compatible(place, source, drink, clue):
            raise StoryError(explain_rejection(place, source, drink, clue))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.drink is None or combo[2] == args.drink)
        and (args.clue is None or combo[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, drink_id, clue_id = rng.choice(combos)
    lead_gender = rng.choice(["girl", "boy"])
    companion_gender = "boy" if lead_gender == "girl" else "girl" if rng.random() < 0.5 else lead_gender
    lead_name = _pick_name(rng, lead_gender)
    companion_name = _pick_name(rng, companion_gender, avoid=lead_name)
    return StoryParams(
        place=place_id,
        source=source_id,
        drink=drink_id,
        clue=clue_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, table in (
        ("place", PLACES),
        ("source", SOURCES),
        ("drink", DRINKS),
        ("clue", CLUES),
    ):
        value = getattr(params, field_name)
        if value not in table:
            raise StoryError(f"(Invalid {field_name}: {value})")

    place = PLACES[params.place]
    source = SOURCES[params.source]
    drink = DRINKS[params.drink]
    clue = CLUES[params.clue]
    if not compatible(place, source, drink, clue):
        raise StoryError(explain_rejection(place, source, drink, clue))

    world = tell(
        place=place,
        source_cfg=source,
        drink_cfg=drink,
        clue_cfg=clue,
        lead_name=params.lead_name,
        lead_type=params.lead_gender,
        companion_name=params.companion_name,
        companion_type=params.companion_gender,
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
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, drink, clue) combos:\n")
        for place, source, drink, clue in combos:
            print(f"  {place:12} {source:10} {drink:12} {clue}")
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
            header = f"### {p.lead_name} & {p.companion_name}: {p.place} ({p.source}, {p.drink}, {p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
