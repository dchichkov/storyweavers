#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/climate_twenty_torch_bravery_kindness_ghost_story.py
================================================================================

A standalone story world for a gentle ghost story about a child carrying a torch
into a spooky old place while preparing a climate-club display. The child must
use bravery to stay, and kindness to understand what the ghost needs.

Every story includes the words "climate", "twenty", and "torch". The world model
drives the turn: the ghost is not solved by random niceness, but by the right
kind of help for the ghost's actual trouble.

Run it
------
    python storyworlds/worlds/gpt-5.4/climate_twenty_torch_bravery_kindness_ghost_story.py
    python storyworlds/worlds/gpt-5.4/climate_twenty_torch_bravery_kindness_ghost_story.py --place greenhouse
    python storyworlds/worlds/gpt-5.4/climate_twenty_torch_bravery_kindness_ghost_story.py --disturbance dark
    python storyworlds/worlds/gpt-5.4/climate_twenty_torch_bravery_kindness_ghost_story.py --comfort scarf
    python storyworlds/worlds/gpt-5.4/climate_twenty_torch_bravery_kindness_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/climate_twenty_torch_bravery_kindness_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/climate_twenty_torch_bravery_kindness_ghost_story.py --verify
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
    spooky: str
    project: str
    missing_item: str
    ending_image: str
    affords: set[str] = field(default_factory=set)
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
class Disturbance:
    id: str
    need: str
    sound: str
    clue: str
    reveal: str
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
class Comfort:
    id: str
    kind: str
    label: str
    phrase: str
    action: str
    qa_text: str
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
class StoryParams:
    place: str
    disturbance: str
    comfort: str
    name: str
    gender: str
    caretaker: str
    trait: str
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


def _r_draft_chill(world: World) -> list[str]:
    ghost = world.get("ghost")
    room = world.get("room")
    if room.meters["draft"] < THRESHOLD or ghost.meters["present"] < THRESHOLD:
        return []
    sig = ("draft_chill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["cold"] += 1
    ghost.memes["uneasy"] += 1
    return ["__chill__"]


def _r_dark_fear(world: World) -> list[str]:
    ghost = world.get("ghost")
    room = world.get("room")
    if room.meters["dark"] < THRESHOLD or ghost.meters["present"] < THRESHOLD:
        return []
    sig = ("dark_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["afraid"] += 1
    return ["__dark__"]


def _r_lonely_sad(world: World) -> list[str]:
    ghost = world.get("ghost")
    if ghost.meters["lonely"] < THRESHOLD or ghost.meters["present"] < THRESHOLD:
        return []
    sig = ("lonely_sad",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["sad"] += 1
    return ["__lonely__"]


def _r_warmth_helps(world: World) -> list[str]:
    ghost = world.get("ghost")
    if ghost.meters["comfort_warmth"] < THRESHOLD or ghost.meters["cold"] < THRESHOLD:
        return []
    sig = ("warmth_helps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["cold"] = 0.0
    ghost.memes["trust"] += 1
    ghost.memes["calm"] += 1
    return ["__better__"]


def _r_light_helps(world: World) -> list[str]:
    ghost = world.get("ghost")
    if ghost.meters["comfort_light"] < THRESHOLD or ghost.memes["afraid"] < THRESHOLD:
        return []
    sig = ("light_helps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.memes["afraid"] = 0.0
    ghost.memes["trust"] += 1
    ghost.memes["calm"] += 1
    return ["__better__"]


def _r_company_helps(world: World) -> list[str]:
    ghost = world.get("ghost")
    if ghost.meters["comfort_company"] < THRESHOLD or ghost.memes["sad"] < THRESHOLD:
        return []
    sig = ("company_helps",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ghost.meters["lonely"] = 0.0
    ghost.memes["sad"] = 0.0
    ghost.memes["trust"] += 1
    ghost.memes["calm"] += 1
    return ["__better__"]


RULES: list[Rule] = [
    Rule(name="draft_chill", tag="physical", apply=_r_draft_chill),
    Rule(name="dark_fear", tag="emotional", apply=_r_dark_fear),
    Rule(name="lonely_sad", tag="emotional", apply=_r_lonely_sad),
    Rule(name="warmth_helps", tag="repair", apply=_r_warmth_helps),
    Rule(name="light_helps", tag="repair", apply=_r_light_helps),
    Rule(name="company_helps", tag="repair", apply=_r_company_helps),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        label="the old greenhouse",
        spooky="Glass ribs clicked above the vines, and the moon made pale squares on the floor.",
        project="the climate club display",
        missing_item="a painted wind-wheel",
        ending_image="all twenty wind-wheels turned softly in the window",
        affords={"cold"},
        tags={"greenhouse", "climate"},
    ),
    "weather_shed": Place(
        id="weather_shed",
        label="the weather shed behind the school",
        spooky="Rain taps whispered on the roof, and the shelves of jars looked like sleeping eyes.",
        project="the climate club corner",
        missing_item="the last blue cloud card",
        ending_image="all twenty cloud cards hung in a neat shining row",
        affords={"dark"},
        tags={"weather", "climate"},
    ),
    "bell_tower": Place(
        id="bell_tower",
        label="the old bell tower room",
        spooky="The rope swayed by itself, and every creak seemed to come from one step higher.",
        project="the climate club wall",
        missing_item="the silver moon for the center",
        ending_image="all twenty paper moons glimmered above the stairs",
        affords={"lonely"},
        tags={"tower", "climate"},
    ),
}

DISTURBANCES = {
    "cold": Disturbance(
        id="cold",
        need="warmth",
        sound="a thin chattering sound",
        clue="a breath of icy air slipped through a cracked pane",
        reveal="The ghost was not angry at all. It was small, pale, and shivering like mist near a winter window.",
        tags={"cold", "ghost"},
    ),
    "dark": Disturbance(
        id="dark",
        need="light",
        sound="a soft whimper from the dark",
        clue="the bulb above the shelf had gone dead",
        reveal="The ghost was huddled in the black corner, blinking as if the dark itself had grown too deep.",
        tags={"dark", "ghost"},
    ),
    "lonely": Disturbance(
        id="lonely",
        need="company",
        sound="a long sigh that seemed to float down the stairs",
        clue="nobody had visited this room for a very long time",
        reveal="The ghost was not trying to scare anyone. It was only waiting, thin as moon-smoke, for somebody to stay and speak.",
        tags={"lonely", "ghost"},
    ),
}

COMFORTS = {
    "scarf": Comfort(
        id="scarf",
        kind="warmth",
        label="a wool scarf",
        phrase="a wool scarf from the hook by the door",
        action="wrapped the soft scarf around the shivering little ghost",
        qa_text="shared a warm scarf",
        tags={"warmth", "scarf"},
    ),
    "torch": Comfort(
        id="torch",
        kind="light",
        label="the torch",
        phrase="the bright torch in a steady hand",
        action="lifted the torch so the beam spread gently through the room",
        qa_text="used the torch to make a warm circle of light",
        tags={"light", "torch"},
    ),
    "song": Comfort(
        id="song",
        kind="company",
        label="a soft song",
        phrase="a soft song and a brave hello",
        action='sang a small song and said, "You do not have to be alone tonight"',
        qa_text="stayed and sang so the ghost was not alone",
        tags={"company", "song"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "gentle", "steady", "kind", "curious", "thoughtful"]


def disturbance_fits(place_id: str, disturbance_id: str) -> bool:
    return disturbance_id in PLACES[place_id].affords


def comfort_fits(disturbance_id: str, comfort_id: str) -> bool:
    return DISTURBANCES[disturbance_id].need == COMFORTS[comfort_id].kind


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id in sorted(PLACES):
        for disturbance_id in sorted(DISTURBANCES):
            if not disturbance_fits(place_id, disturbance_id):
                continue
            for comfort_id in sorted(COMFORTS):
                if comfort_fits(disturbance_id, comfort_id):
                    out.append((place_id, disturbance_id, comfort_id))
    return out


def explain_rejection(place_id: str, disturbance_id: str, comfort_id: str) -> str:
    place = PLACES[place_id]
    disturbance = DISTURBANCES[disturbance_id]
    comfort = COMFORTS[comfort_id]
    if not disturbance_fits(place_id, disturbance_id):
        return (
            f"(No story: {place.label} does not produce the '{disturbance_id}' trouble in this world. "
            f"That place supports {', '.join(sorted(place.affords))} instead.)"
        )
    return (
        f"(No story: {comfort.label} does not solve a ghost troubled by {disturbance_id}. "
        f"This ghost needs {disturbance.need}, so pick a comfort that offers {disturbance.need}.)"
    )


def predict_need(world: World, disturbance: Disturbance) -> dict:
    sim = world.copy()
    room = sim.get("room")
    ghost = sim.get("ghost")
    room.meters["draft"] = 1.0 if disturbance.id == "cold" else 0.0
    room.meters["dark"] = 1.0 if disturbance.id == "dark" else 0.0
    ghost.meters["lonely"] = 1.0 if disturbance.id == "lonely" else 0.0
    propagate(sim, narrate=False)
    return {
        "cold": ghost.meters["cold"],
        "afraid": ghost.memes["afraid"],
        "sad": ghost.memes["sad"],
    }


def introduce(world: World, child: Entity, caretaker: Entity, place: Place) -> None:
    world.say(
        f"After supper, {child.id} came back to school with {child.pronoun('possessive')} "
        f"{caretaker.label_word} to finish {place.project}. They had made nineteen paper pieces already, "
        f"and one more would make twenty."
    )
    world.say(
        f"The display was about climate, so every piece showed weather in a bright little way. "
        f"Tonight they still needed {place.missing_item}."
    )


def setup_loss(world: World, child: Entity, caretaker: Entity, place: Place) -> None:
    child.memes["care"] += 1
    world.say(
        f'When the classroom door opened, a draft nipped at the table and whisked {place.missing_item} away. '
        f'It skittered toward {place.label}.'
    )
    world.say(
        f'"I can get it," said {child.id}. {caretaker.label_word.capitalize()} handed over a torch, '
        f'but the dark beyond the doorway still looked deep and strange.'
    )


def enter_spooky_place(world: World, child: Entity, place: Place, disturbance: Disturbance) -> None:
    child.memes["bravery"] += 1
    ghost = world.get("ghost")
    ghost.meters["present"] = 1.0
    room = world.get("room")
    room.meters["draft"] = 1.0 if disturbance.id == "cold" else 0.0
    room.meters["dark"] = 1.0 if disturbance.id == "dark" else 0.0
    ghost.meters["lonely"] = 1.0 if disturbance.id == "lonely" else 0.0
    world.say(
        f"{child.id} stepped inside {place.label} with the torch held out in front. "
        f"{place.spooky}"
    )
    world.say(
        f"Then {child.pronoun()} heard {disturbance.sound}, and {disturbance.clue}."
    )
    propagate(world, narrate=False)


def fear_then_pause(world: World, child: Entity) -> None:
    child.memes["fear"] += 1
    world.say(
        f"For one jumpy moment, {child.id} wanted to run. Then {child.pronoun()} took a slow breath, "
        f"remembered the torch in {child.pronoun('possessive')} hand, and stayed."
    )


def understand_ghost(world: World, child: Entity, disturbance: Disturbance) -> None:
    pred = predict_need(world, disturbance)
    world.facts["predicted_need"] = pred
    world.say(disturbance.reveal)
    if pred["cold"] >= THRESHOLD:
        world.say(
            f"{child.id} saw right away that the poor thing was cold, not cruel."
        )
    elif pred["afraid"] >= THRESHOLD:
        world.say(
            f"{child.id} saw that the poor thing was frightened by the thick dark."
        )
    else:
        world.say(
            f"{child.id} understood that the poor thing had been lonely for a long, long time."
        )


def help_ghost(world: World, child: Entity, comfort: Comfort) -> None:
    child.memes["kindness"] += 1
    ghost = world.get("ghost")
    ghost.meters[f"comfort_{comfort.kind}"] += 1
    world.say(
        f"So {child.id} chose kindness. {child.pronoun().capitalize()} {comfort.action}."
    )
    propagate(world, narrate=False)


def ghost_returns_item(world: World, child: Entity, place: Place, comfort: Comfort) -> None:
    ghost = world.get("ghost")
    ghost.memes["grateful"] += 1
    world.facts["resolved"] = True
    world.say(
        f"The little ghost gave a shimmer that looked almost like a smile. From behind an old box it floated up with {place.missing_item}."
    )
    world.say(
        f'"For the twenty," it whispered. Its voice sounded lighter now, because {child.id} had {comfort.qa_text}.'
    )


def ending(world: World, child: Entity, caretaker: Entity, place: Place) -> None:
    child.memes["joy"] += 1
    child.memes["bravery"] += 1
    child.memes["kindness"] += 1
    world.say(
        f"Back in the classroom, {child.id} and {caretaker.label_word} set the last piece in place. "
        f"Soon {place.ending_image}."
    )
    world.say(
        f"Whenever the window rattled after that, {child.id} did not think first of fright. "
        f"{child.pronoun().capitalize()} thought of a ghost who had needed bravery to face and kindness to help."
    )


def tell(
    place: Place,
    disturbance: Disturbance,
    comfort: Comfort,
    name: str = "Lily",
    gender: str = "girl",
    caretaker_type: str = "mother",
    trait: str = "brave",
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="child",
            traits=[trait],
            attrs={},
        )
    )
    caretaker = world.add(
        Entity(
            id="Caretaker",
            kind="character",
            type=caretaker_type,
            role="caretaker",
            label="the grown-up",
            attrs={},
        )
    )
    ghost = world.add(
        Entity(
            id="ghost",
            kind="character",
            type="ghost",
            role="ghost",
            label="the ghost",
            attrs={},
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=place.label,
            attrs={},
        )
    )

    child.memes["bravery"] = 1.0 if trait in {"brave", "steady"} else 0.5
    child.memes["kindness"] = 1.0 if trait in {"kind", "gentle", "thoughtful"} else 0.5
    ghost.meters["present"] = 0.0
    ghost.meters["lonely"] = 0.0
    room.meters["draft"] = 0.0
    room.meters["dark"] = 0.0
    world.facts["resolved"] = False

    introduce(world, child, caretaker, place)
    setup_loss(world, child, caretaker, place)

    world.para()
    enter_spooky_place(world, child, place, disturbance)
    fear_then_pause(world, child)
    understand_ghost(world, child, disturbance)

    world.para()
    help_ghost(world, child, comfort)
    ghost_returns_item(world, child, place, comfort)
    ending(world, child, caretaker, place)

    world.facts.update(
        child=child,
        caretaker=caretaker,
        ghost=ghost,
        room=room,
        place=place,
        disturbance=disturbance,
        comfort=comfort,
        item=place.missing_item,
    )
    return world


KNOWLEDGE = {
    "climate": [
        (
            "What does climate mean?",
            "Climate is the usual kind of weather a place has over a long time. It includes things like how warm, cold, wet, or windy a place often is."
        )
    ],
    "torch": [
        (
            "What is a torch?",
            "A torch is a hand light you carry in the dark. It helps you see without using any flame."
        )
    ],
    "ghost": [
        (
            "What is a ghost in a story?",
            "In a story, a ghost is a spirit-like character that can seem spooky. In gentle ghost stories, the ghost is often sad, lost, or in need of help."
        )
    ],
    "warmth": [
        (
            "Why does warmth help someone who is shivering?",
            "Warmth helps a shivering body feel safe and steady again. A scarf or blanket can stop the cold from biting so hard."
        )
    ],
    "light": [
        (
            "Why can light make a dark place feel less scary?",
            "Light lets you see what is really there. When you can see clearly, your mind has less room to imagine dangers."
        )
    ],
    "company": [
        (
            "Why does company help when someone feels lonely?",
            "Company reminds someone that they are not by themselves. Even a small kind voice can make a lonely heart feel warmer."
        )
    ],
}
KNOWLEDGE_ORDER = ["climate", "torch", "ghost", "warmth", "light", "company"]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    child = world.facts["child"]
    disturbance = world.facts["disturbance"]
    comfort = world.facts["comfort"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "climate", "twenty", and "torch".',
        f"Tell a spooky-but-kind story where a {child.type} named {child.id} goes into {place.label} to find a missing piece for a climate-club display of twenty items.",
        f"Write a story where bravery keeps a child from running away, and kindness helps a ghost troubled by {disturbance.id}, using {comfort.label} to make things right.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    caretaker = world.facts["caretaker"]
    place = world.facts["place"]
    disturbance = world.facts["disturbance"]
    comfort = world.facts["comfort"]
    pred = world.facts.get("predicted_need", {})
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child carrying a torch, and a little ghost in {place.label}. The grown-up is {child.id}'s {caretaker.label_word}, who is helping finish the school display."
        ),
        (
            "Why did the child go into the spooky place?",
            f"{child.id} went in to look for {place.missing_item}, the last piece needed to make twenty for the climate-club display. That simple errand is what led {child.pronoun('object')} to the ghost."
        ),
        (
            "What made the place feel spooky?",
            f"{place.spooky} Then {child.id} heard {disturbance.sound}. The strange sound and the dark old room made the moment feel like the start of a ghost story."
        ),
        (
            f"How did {child.id} show bravery?",
            f"{child.id} wanted to run for one moment, but stayed instead. {child.pronoun().capitalize()} took a slow breath and kept holding the torch, which let {child.pronoun('object')} face the fear instead of obeying it."
        ),
    ]
    if pred.get("cold", 0) >= THRESHOLD:
        qa.append(
            (
                "What was really wrong with the ghost?",
                f"The ghost was cold because icy air was slipping through a cracked pane. {child.id} understood that the ghost was shivering, not trying to be mean."
            )
        )
    elif pred.get("afraid", 0) >= THRESHOLD:
        qa.append(
            (
                "What was really wrong with the ghost?",
                f"The ghost was afraid of the deep dark in the room. Once {child.id} saw that, the problem stopped feeling like a monster problem and started feeling like one that kindness could solve."
            )
        )
    else:
        qa.append(
            (
                "What was really wrong with the ghost?",
                f"The ghost was lonely and had been waiting a long time for someone to stay. {child.id} learned that the sighing sound came from sadness, not anger."
            )
        )
    qa.append(
        (
            f"How did {child.id} show kindness?",
            f"{child.pronoun().capitalize()} {comfort.action}. That helped because the ghost needed {DISTURBANCES[disturbance.id].need}, and {comfort.label} gave exactly that."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The ghost returned {place.missing_item}, and the classroom display reached twenty at last. The ending image shows what changed: {place.ending_image}."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"climate", "ghost", "torch"}
    tags.add(COMFORTS[world.facts["comfort"].id].kind)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="greenhouse",
        disturbance="cold",
        comfort="scarf",
        name="Lily",
        gender="girl",
        caretaker="mother",
        trait="kind",
    ),
    StoryParams(
        place="weather_shed",
        disturbance="dark",
        comfort="torch",
        name="Tom",
        gender="boy",
        caretaker="father",
        trait="steady",
    ),
    StoryParams(
        place="bell_tower",
        disturbance="lonely",
        comfort="song",
        name="Maya",
        gender="girl",
        caretaker="aunt",
        trait="brave",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a child uses bravery and kindness to help a ghost while finishing a climate-club display."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--disturbance", choices=sorted(DISTURBANCES))
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="verify Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.disturbance and not disturbance_fits(args.place, args.disturbance):
        comfort_id = args.comfort or next(iter(COMFORTS))
        raise StoryError(explain_rejection(args.place, args.disturbance, comfort_id))
    if args.disturbance and args.comfort and not comfort_fits(args.disturbance, args.comfort):
        place_id = args.place or next(iter(PLACES))
        if args.place and disturbance_fits(args.place, args.disturbance):
            place_id = args.place
        elif args.disturbance == "cold":
            place_id = "greenhouse"
        elif args.disturbance == "dark":
            place_id = "weather_shed"
        else:
            place_id = "bell_tower"
        raise StoryError(explain_rejection(place_id, args.disturbance, args.comfort))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.disturbance is None or combo[1] == args.disturbance)
        and (args.comfort is None or combo[2] == args.comfort)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, disturbance_id, comfort_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(pool)
    caretaker = args.caretaker or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        disturbance=disturbance_id,
        comfort=comfort_id,
        name=name,
        gender=gender,
        caretaker=caretaker,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.disturbance not in DISTURBANCES:
        raise StoryError(f"(Unknown disturbance: {params.disturbance})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort: {params.comfort})")
    if not disturbance_fits(params.place, params.disturbance):
        raise StoryError(explain_rejection(params.place, params.disturbance, params.comfort))
    if not comfort_fits(params.disturbance, params.comfort):
        raise StoryError(explain_rejection(params.place, params.disturbance, params.comfort))

    world = tell(
        place=PLACES[params.place],
        disturbance=DISTURBANCES[params.disturbance],
        comfort=COMFORTS[params.comfort],
        name=params.name,
        gender=params.gender,
        caretaker_type=params.caretaker,
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


ASP_RULES = r"""
fits_place(P,D) :- place(P), disturbance(D), affords(P,D).
fits_comfort(D,C) :- disturbance(D), comfort(C), need_of(D,N), kind_of(C,N).
valid(P,D,C) :- fits_place(P,D), fits_comfort(D,C).

resolved(P,D,C) :- valid(P,D,C).
#show valid/3.
#show resolved/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for disturbance_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, disturbance_id))
    for disturbance_id, disturbance in DISTURBANCES.items():
        lines.append(asp.fact("disturbance", disturbance_id))
        lines.append(asp.fact("need_of", disturbance_id, disturbance.need))
    for comfort_id, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", comfort_id))
        lines.append(asp.fact("kind_of", comfort_id, comfort.kind))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP valid combos.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in asp:", sorted(cl - py))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            sample = generate(params)
            if "climate" not in sample.story or "twenty" not in sample.story or "torch" not in sample.story:
                raise StoryError("(Generated story missed a required seed word.)")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke test passed for seeds 0-9.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, disturbance, comfort) combos:\n")
        for place_id, disturbance_id, comfort_id in combos:
            print(f"  {place_id:13} {disturbance_id:10} {comfort_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.name}: {p.place} / {p.disturbance} / {p.comfort}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
