#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/irritable_spokesman_kindness_animal_story.py
=======================================================================

A standalone storyworld for a gentle Animal Story about an irritable animal,
a chosen spokesman, and a turn driven by kindness.

Seed idea rebuilt as world state
--------------------------------
A little group of animals wants to enjoy something lovely in a shared woodland
place, but the animal already there is snappish and hard to approach. The group
chooses one small animal as their spokesman. Instead of pushing a speech through,
the spokesman notices that the "mean" animal is hurting or uncomfortable, offers
the one kind help that actually fits the problem, and the whole mood changes.

This world models:
- a woodland place with a treat the animals hope to share
- an irritable host animal whose discomfort makes them sharp and guarding
- a spokesman chosen by the waiting animals
- a kindness act that must genuinely relieve the discomfort
- a state-driven resolution where calm and trust lead to sharing

Run it
------
    python storyworlds/worlds/gpt-5.4/irritable_spokesman_kindness_animal_story.py
    python storyworlds/worlds/gpt-5.4/irritable_spokesman_kindness_animal_story.py --place blackberry_hill
    python storyworlds/worlds/gpt-5.4/irritable_spokesman_kindness_animal_story.py --irritant bee_buzz --kindness fern_fan
    python storyworlds/worlds/gpt-5.4/irritable_spokesman_kindness_animal_story.py --irritant thorn_paw --kindness leaf_shade
    python storyworlds/worlds/gpt-5.4/irritable_spokesman_kindness_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/irritable_spokesman_kindness_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/irritable_spokesman_kindness_animal_story.py --verify
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
        female = {"doe", "hen", "mother", "girl"}
        male = {"badger", "porcupine", "turtle", "rabbit", "mouse", "wren", "mole", "otter", "boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    treat: str
    treat_phrase: str
    host_name: str
    host_type: str
    host_title: str
    group_label: str
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
class Irritant:
    id: str
    meter: str
    label: str
    sign: str
    cause_line: str
    question: str
    relief_noun: str
    severity: int
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
class KindnessAct:
    id: str
    label: str
    helps: str
    power: int
    notice: str
    do_line: str
    calm_line: str
    qa_line: str
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
class SpeakerAnimal:
    type: str
    names: list[str]
    voice: str
    walk: str
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
class StoryParams:
    place: str
    irritant: str
    kindness: str
    spokesman_type: str
    spokesman_name: str
    companion_type: str
    companion_name: str
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


def _r_irritable(world: World) -> list[str]:
    host = world.get("host")
    irritant = world.facts["irritant_cfg"]
    if host.meters[irritant.meter] < THRESHOLD:
        return []
    sig = ("irritable", irritant.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    host.memes["irritable"] += 1
    host.memes["guarding"] += 1
    world.history.append("host_became_irritable")
    return []


def _r_fear(world: World) -> list[str]:
    host = world.get("host")
    spokesman = world.get("spokesman")
    companion = world.get("companion")
    waiting = world.get("waiting")
    if host.memes["irritable"] < THRESHOLD or waiting.memes["hope"] < THRESHOLD:
        return []
    sig = ("fear", host.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spokesman.memes["nervous"] += 1
    companion.memes["worry"] += 1
    waiting.memes["worry"] += 1
    world.history.append("crowd_grew_wary")
    return []


def _r_share(world: World) -> list[str]:
    host = world.get("host")
    waiting = world.get("waiting")
    treat = world.get("treat")
    spokesman = world.get("spokesman")
    companion = world.get("companion")
    if host.memes["calm"] < THRESHOLD or host.memes["trust"] < THRESHOLD:
        return []
    sig = ("share", treat.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treat.meters["shared"] += 1
    waiting.memes["joy"] += 1
    spokesman.memes["relief"] += 1
    companion.memes["relief"] += 1
    host.memes["generosity"] += 1
    world.history.append("treat_was_shared")
    return []


CAUSAL_RULES = [
    Rule(name="irritable", tag="emotional", apply=_r_irritable),
    Rule(name="fear", tag="emotional", apply=_r_fear),
    Rule(name="share", tag="social", apply=_r_share),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "blackberry_hill": Place(
        id="blackberry_hill",
        label="Blackberry Hill",
        opening="At the edge of the woods, Blackberry Hill hung low with shiny fruit.",
        treat="blackberries",
        treat_phrase="the plump blackberries",
        host_name="Bramble",
        host_type="porcupine",
        host_title="Porcupine",
        group_label="the little hillside animals",
        affords={"thorn_paw", "bee_buzz"},
        tags={"berries", "hill"},
    ),
    "apple_glade": Place(
        id="apple_glade",
        label="Apple Glade",
        opening="In Apple Glade, sweet red apples thumped softly onto the grass.",
        treat="apples",
        treat_phrase="the fallen apples",
        host_name="Bruno",
        host_type="badger",
        host_title="Badger",
        group_label="the glade animals",
        affords={"bee_buzz", "sun_glare"},
        tags={"apples", "glade"},
    ),
    "pond_bank": Place(
        id="pond_bank",
        label="Pond Bank",
        opening="By the pond bank, cool water shone beside a patch of tender watercress.",
        treat="watercress",
        treat_phrase="the crisp watercress",
        host_name="Moss",
        host_type="turtle",
        host_title="Turtle",
        group_label="the pond-side animals",
        affords={"sun_glare", "thorn_paw"},
        tags={"pond", "greens"},
    ),
}

IRRITANTS = {
    "thorn_paw": Irritant(
        id="thorn_paw",
        meter="pain",
        label="a thorn in his paw",
        sign="kept lifting one sore paw and setting it down again",
        cause_line="A sharp thorn was stuck in his paw, and every step pinched.",
        question="Did something hurt?",
        relief_noun="the thorn",
        severity=2,
        tags={"thorn", "pain"},
    ),
    "bee_buzz": Irritant(
        id="bee_buzz",
        meter="buzz",
        label="bees buzzing around his ears",
        sign="kept twitching his ears and ducking his head",
        cause_line="Two cross bees were circling his ears, and the buzzing made him jumpy.",
        question="Are the bees bothering you?",
        relief_noun="the bees",
        severity=1,
        tags={"bees", "buzzing"},
    ),
    "sun_glare": Irritant(
        id="sun_glare",
        meter="glare",
        label="the bright sun in his eyes",
        sign="kept squinting and blinking at the light",
        cause_line="The noon sun shone straight into his eyes, so everything felt too bright.",
        question="Is the sun too bright for you?",
        relief_noun="the glare",
        severity=1,
        tags={"sun", "bright"},
    ),
}

KINDNESS = {
    "gentle_tug": KindnessAct(
        id="gentle_tug",
        label="a gentle tug",
        helps="thorn_paw",
        power=2,
        notice="looked down instead of speaking at once",
        do_line="With very careful paws, he eased the thorn free and laid a cool leaf over the sore spot.",
        calm_line="The pain stopped pinching at once.",
        qa_line="He gently pulled the thorn out and covered the sore paw with a cool leaf.",
        tags={"thorn_help"},
    ),
    "fern_fan": KindnessAct(
        id="fern_fan",
        label="a fern fan",
        helps="bee_buzz",
        power=1,
        notice="noticed a broad fern growing beside the path",
        do_line="He picked up the fern and waved it slowly until the bees drifted back toward the clover.",
        calm_line="The angry buzzing moved away from his ears.",
        qa_line="He used a broad fern to fan the bees away from the host's ears.",
        tags={"bee_help"},
    ),
    "leaf_shade": KindnessAct(
        id="leaf_shade",
        label="a leaf shade",
        helps="sun_glare",
        power=1,
        notice="spotted a large dock leaf near a stone",
        do_line="He held the wide leaf above the host's face like a tiny umbrella.",
        calm_line="The hard sunlight softened into cool green shade.",
        qa_line="He held up a wide leaf to make gentle shade over the host's eyes.",
        tags={"shade_help"},
    ),
}

SPEAKER_TYPES = {
    "mouse": SpeakerAnimal(
        type="mouse",
        names=["Pip", "Milo", "Nip", "Tumble"],
        voice="small but clear",
        walk="padded forward with whiskers trembling",
        tags={"mouse"},
    ),
    "rabbit": SpeakerAnimal(
        type="rabbit",
        names=["Thimble", "Bram", "Nettle", "Clover"],
        voice="soft and polite",
        walk="hopped forward with long careful steps",
        tags={"rabbit"},
    ),
    "wren": SpeakerAnimal(
        type="wren",
        names=["Wisp", "Feather", "Peep", "Merry"],
        voice="tiny and brave",
        walk="fluttered down to the nearest stone",
        tags={"bird"},
    ),
    "mole": SpeakerAnimal(
        type="mole",
        names=["Mott", "Digby", "Soot", "Velvet"],
        voice="low and gentle",
        walk="trundled forward with neat little paws",
        tags={"mole"},
    ),
}

COMPANION_TYPES = {
    "rabbit": ["Clover", "Reed", "Mallow", "Bun"],
    "mouse": ["Pipkin", "Nib", "Dot", "Bean"],
    "wren": ["Tizzy", "Wing", "Sprig", "Lilt"],
    "otter": ["Ripple", "Drift", "Skim", "Pebble"],
    "hedgehog": ["Burr", "Hazel", "Prickle", "Muffin"],
}


def kindness_fits(irritant: Irritant, kindness: KindnessAct) -> bool:
    return kindness.helps == irritant.id and kindness.power >= irritant.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for irritant_id in sorted(place.affords):
            irritant = IRRITANTS[irritant_id]
            for kindness_id, kindness in KINDNESS.items():
                if kindness_fits(irritant, kindness):
                    combos.append((place_id, irritant_id, kindness_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    irritant = IRRITANTS[params.irritant]
    kindness = KINDNESS[params.kindness]
    return "shared" if kindness_fits(irritant, kindness) else "standoff"


def explain_rejection(place: Place, irritant: Irritant, kindness: KindnessAct) -> str:
    if irritant.id not in place.affords:
        return (
            f"(No story: {place.label} does not support the problem '{irritant.id}', "
            f"so the host would have no honest reason to be irritable there.)"
        )
    if kindness.helps != irritant.id:
        return (
            f"(No story: {kindness.label} does not help with {irritant.label}. "
            f"The kindness turn must really solve the host's problem.)"
        )
    if kindness.power < irritant.severity:
        return (
            f"(No story: {kindness.label} is too weak for {irritant.label}. "
            f"The kind act must actually bring relief.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def setup_world(place: Place, irritant: Irritant, kindness: KindnessAct,
                spokesman_cfg: SpeakerAnimal, spokesman_name: str,
                companion_type: str, companion_name: str) -> World:
    world = World()
    host = world.add(Entity(
        id="host",
        kind="character",
        type=place.host_type,
        label=f"{place.host_name} {place.host_title}",
        role="host",
        attrs={"name": place.host_name, "title": place.host_title},
    ))
    spokesman = world.add(Entity(
        id="spokesman",
        kind="character",
        type=spokesman_cfg.type,
        label=f"{spokesman_name} the {spokesman_cfg.type}",
        role="spokesman",
        attrs={"name": spokesman_name, "voice": spokesman_cfg.voice, "walk": spokesman_cfg.walk},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type=companion_type,
        label=f"{companion_name} the {companion_type}",
        role="companion",
        attrs={"name": companion_name},
    ))
    waiting = world.add(Entity(
        id="waiting",
        kind="group",
        type="animals",
        label=place.group_label,
        role="crowd",
    ))
    treat = world.add(Entity(
        id="treat",
        type="food",
        label=place.treat,
    ))

    host.meters[irritant.meter] = float(irritant.severity)
    host.meters["comfort"] = 0.0
    host.memes["calm"] = 0.0
    host.memes["trust"] = 0.0
    host.memes["gratitude"] = 0.0
    host.memes["irritable"] = 0.0
    host.memes["guarding"] = 0.0
    spokesman.memes["kindness"] = 0.0
    spokesman.memes["nervous"] = 0.0
    spokesman.memes["relief"] = 0.0
    waiting.memes["hope"] = 1.0
    waiting.memes["worry"] = 0.0
    waiting.memes["joy"] = 0.0
    companion.memes["worry"] = 0.0
    companion.memes["trust"] = 1.0
    treat.meters["shared"] = 0.0

    world.facts["place_cfg"] = place
    world.facts["irritant_cfg"] = irritant
    world.facts["kindness_cfg"] = kindness
    world.facts["spokesman_cfg"] = spokesman_cfg
    world.facts["chosen_phrase"] = ""
    world.facts["noticed_problem"] = False
    world.facts["relieved"] = False
    world.facts["outcome"] = "standoff"

    propagate(world)
    return world


def choose_spokesman(world: World) -> None:
    place = world.facts["place_cfg"]
    spokesman = world.get("spokesman")
    companion = world.get("companion")
    world.say(place.opening)
    world.say(
        f"{place.group_label.capitalize()} could smell {place.treat_phrase}, but nobody wanted to crowd close."
    )
    world.say(
        f"{place.host_name} {place.host_title} sat beside them and looked so irritable that even the grasshoppers stayed quiet."
    )
    world.para()
    world.say(
        f'"Someone should ask kindly," whispered {companion.attrs["name"]} the {companion.type}. '
        f'So the others chose {spokesman.attrs["name"]} the {spokesman.type} as their spokesman.'
    )
    world.say(
        f"{spokesman.attrs['name'].capitalize()} was {world.facts['spokesman_cfg'].voice}, but his heart beat fast all the same."
    )
    world.history.append("spokesman_chosen")


def snap_warning(world: World) -> None:
    host = world.get("host")
    place = world.facts["place_cfg"]
    irritant = world.facts["irritant_cfg"]
    world.say(
        f"When the little line of animals edged nearer, {place.host_name} {place.host_title} {irritant.sign}."
    )
    world.say(
        f'"Not now," he grumbled. "Can\'t you see I want to be left alone?"'
    )
    world.history.append("host_snapped")


def approach(world: World) -> None:
    spokesman = world.get("spokesman")
    kindness = world.facts["kindness_cfg"]
    world.para()
    world.say(
        f"{spokesman.attrs['name']} {spokesman.attrs['walk']}. He had prepared a careful spokesman speech, but he {kindness.notice}."
    )
    world.history.append("spokesman_approached")


def notice_need(world: World) -> None:
    host = world.get("host")
    spokesman = world.get("spokesman")
    irritant = world.facts["irritant_cfg"]
    world.facts["noticed_problem"] = True
    spokesman.memes["kindness"] += 1
    world.say(
        f'Instead of blurting out the speech, he asked, "{host.attrs["name"]}, {irritant.question}"'
    )
    world.say(
        f"Then he saw the truth: {irritant.cause_line}"
    )
    world.history.append("problem_noticed")


def perform_kindness(world: World) -> None:
    host = world.get("host")
    spokesman = world.get("spokesman")
    kindness = world.facts["kindness_cfg"]
    irritant = world.facts["irritant_cfg"]
    spokesman.memes["kindness"] += 1
    host.meters[irritant.meter] = 0.0
    host.meters["comfort"] += 1
    host.memes["irritable"] = 0.0
    host.memes["calm"] += 1
    host.memes["trust"] += 1
    host.memes["gratitude"] += 1
    world.facts["relieved"] = True
    propagate(world)
    world.say(kindness.do_line)
    world.say(kindness.calm_line)
    world.history.append("kindness_done")


def soften_and_share(world: World) -> None:
    host = world.get("host")
    spokesman = world.get("spokesman")
    place = world.facts["place_cfg"]
    world.say(
        f'{host.attrs["name"]} blinked, and his sharp face turned gentle. "Oh," he said, '
        f'"I was cross because everything hurt and buzzed and glared at once inside my head."'
    )
    world.say(
        f'"Thank you, little spokesman. You saw what was wrong before you asked for anything."'
    )
    world.para()
    world.say(
        f"Then {host.attrs['name']} moved aside from {place.treat_phrase} and invited everyone closer."
    )
    world.say(
        f"Soon the waiting animals were nibbling together, and {host.attrs['name']} was no longer guarding the place at all."
    )
    spokesman.memes["pride"] += 1
    world.facts["outcome"] = "shared"
    world.history.append("host_shared")


def ending_image(world: World) -> None:
    spokesman = world.get("spokesman")
    companion = world.get("companion")
    place = world.facts["place_cfg"]
    world.say(
        f'{companion.attrs["name"]} the {companion.type} smiled at {spokesman.attrs["name"]} and said, '
        f'"That was the best kind of speech."'
    )
    world.say(
        f"At sunset on {place.label}, the animals ate in a friendly ring, and the tiniest spokesman of all no longer sounded nervous—only kind."
    )
    world.history.append("ending_image")


def tell(place: Place, irritant: Irritant, kindness: KindnessAct,
         spokesman_type: str, spokesman_name: str,
         companion_type: str, companion_name: str) -> World:
    spokesman_cfg = SPEAKER_TYPES[spokesman_type]
    world = setup_world(
        place=place,
        irritant=irritant,
        kindness=kindness,
        spokesman_cfg=spokesman_cfg,
        spokesman_name=spokesman_name,
        companion_type=companion_type,
        companion_name=companion_name,
    )
    choose_spokesman(world)
    snap_warning(world)
    approach(world)
    notice_need(world)
    perform_kindness(world)
    soften_and_share(world)
    ending_image(world)
    return world


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place_cfg"]
    irritant = world.facts["irritant_cfg"]
    spokesman = world.get("spokesman")
    return [
        f'Write an Animal Story for ages 3 to 5 using the words "irritable" and "spokesman". Include kindness as the turning point.',
        f"Tell a woodland story where {spokesman.attrs['name']} the {spokesman.type} is chosen as a spokesman for other animals and discovers that the irritable host is hurting because of {irritant.label}.",
        f"Write a gentle story set at {place.label} where an animal first plans to speak politely, then helps first and asks later, ending in shared food and friendship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    place = world.facts["place_cfg"]
    irritant = world.facts["irritant_cfg"]
    kindness = world.facts["kindness_cfg"]
    spokesman = world.get("spokesman")
    companion = world.get("companion")
    host = world.get("host")
    qa: list[tuple[str, str]] = [
        (
            "Who was chosen as the spokesman?",
            f"{spokesman.attrs['name']} the {spokesman.type} was chosen as the spokesman for the other animals. They hoped he could speak gently to {host.attrs['name']} {place.host_title}.",
        ),
        (
            f"Why did {host.attrs['name']} seem so irritable at first?",
            f"{host.attrs['name']} was not mean for no reason. {irritant.cause_line} That discomfort made him sharp and guarding when the others came near.",
        ),
        (
            f"What did {spokesman.attrs['name']} do instead of giving his speech right away?",
            f"He stopped and looked carefully at the host instead of rushing into his prepared words. Because he noticed the real problem first, he could choose a kind act that truly helped.",
        ),
        (
            f"How did kindness change what happened at {place.label}?",
            f"{spokesman.attrs['name']} used {kindness.label} to help {host.attrs['name']}. Once the pain or bother was gone, the host calmed down, trusted the animals, and shared {place.treat_phrase}.",
        ),
        (
            "How did the story end?",
            f"It ended with the animals eating together in a friendly ring. The ending shows that kindness changed the whole place from tense and guarded to calm and shared.",
        ),
    ]
    if companion.memes["worry"] >= THRESHOLD:
        qa.append(
            (
                f"Why were the other animals quiet before the kindness turn?",
                f"They were worried because the host had already snapped at them, and they did not want to make him feel worse. When {spokesman.attrs['name']} helped instead of arguing, their worry melted into relief.",
            )
        )
    return qa


KNOWLEDGE = {
    "thorn": [
        (
            "Why can a thorn make an animal grumpy?",
            "A thorn pricks with every step, so it keeps hurting again and again. When something hurts, it is harder to feel patient and calm.",
        )
    ],
    "bees": [
        (
            "Why does buzzing near your ears feel upsetting?",
            "A loud buzz near your ears can make you jump and flinch because it is sudden and close. That is why even a gentle animal can feel tense when bees keep circling.",
        )
    ],
    "sun": [
        (
            "Why does shade help on a bright day?",
            "Shade blocks some of the strong light and heat. That gives tired eyes and warm bodies a chance to rest.",
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means noticing what someone else needs and trying to help in a gentle way. Sometimes one small helpful act changes a whole hard moment.",
        )
    ],
    "sharing": [
        (
            "Why is it easier to share after someone feels safe and calm?",
            "When a person or animal feels safe and calm, they do not have to guard everything so tightly. Then they can think about others and welcome them in.",
        )
    ],
    "spokesman": [
        (
            "What is a spokesman?",
            "A spokesman is someone chosen to speak for a group. In a gentle story, a good spokesman listens and notices things too.",
        )
    ],
}
KNOWLEDGE_ORDER = ["spokesman", "kindness", "thorn", "bees", "sun", "sharing"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    irritant = world.facts["irritant_cfg"]
    tags = {"kindness", "sharing", "spokesman"}
    if irritant.id == "thorn_paw":
        tags.add("thorn")
    if irritant.id == "bee_buzz":
        tags.add("bees")
    if irritant.id == "sun_glare":
        tags.add("sun")
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="blackberry_hill",
        irritant="thorn_paw",
        kindness="gentle_tug",
        spokesman_type="mouse",
        spokesman_name="Pip",
        companion_type="rabbit",
        companion_name="Clover",
    ),
    StoryParams(
        place="apple_glade",
        irritant="bee_buzz",
        kindness="fern_fan",
        spokesman_type="wren",
        spokesman_name="Wisp",
        companion_type="otter",
        companion_name="Pebble",
    ),
    StoryParams(
        place="pond_bank",
        irritant="sun_glare",
        kindness="leaf_shade",
        spokesman_type="rabbit",
        spokesman_name="Thimble",
        companion_type="hedgehog",
        companion_name="Hazel",
    ),
    StoryParams(
        place="pond_bank",
        irritant="thorn_paw",
        kindness="gentle_tug",
        spokesman_type="mole",
        spokesman_name="Digby",
        companion_type="wren",
        companion_name="Lilt",
    ),
]


ASP_RULES = r"""
afflicted(P, I) :- place(P), irritant(I), place_affords(P, I).
compatible(I, K) :- irritant(I), kindness(K), helps(K, I), power(K, KP), severity(I, IS), KP >= IS.
valid(P, I, K) :- afflicted(P, I), compatible(I, K).

outcome(shared) :- chosen_irritant(I), chosen_kindness(K), compatible(I, K).
outcome(standoff) :- chosen_irritant(I), chosen_kindness(K), not compatible(I, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for irritant_id in sorted(place.affords):
            lines.append(asp.fact("place_affords", place_id, irritant_id))
    for irritant_id, irritant in IRRITANTS.items():
        lines.append(asp.fact("irritant", irritant_id))
        lines.append(asp.fact("severity", irritant_id, irritant.severity))
    for kindness_id, kindness in KINDNESS.items():
        lines.append(asp.fact("kindness", kindness_id))
        lines.append(asp.fact("helps", kindness_id, kindness.helps))
        lines.append(asp.fact("power", kindness_id, kindness.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_irritant", params.irritant),
        asp.fact("chosen_kindness", params.kindness),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed for seed {seed}")
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story world: an irritable host, a chosen spokesman, and a kind turn."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--irritant", choices=IRRITANTS)
    ap.add_argument("--kindness", choices=KINDNESS)
    ap.add_argument("--spokesman-type", choices=SPEAKER_TYPES)
    ap.add_argument("--spokesman-name")
    ap.add_argument("--companion-type", choices=COMPANION_TYPES)
    ap.add_argument("--companion-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, animal_type: str, avoid: str = "") -> str:
    if animal_type in SPEAKER_TYPES:
        pool = [n for n in SPEAKER_TYPES[animal_type].names if n != avoid]
    else:
        pool = [n for n in COMPANION_TYPES[animal_type] if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.irritant and args.kindness:
        place = PLACES[args.place]
        irritant = IRRITANTS[args.irritant]
        kindness = KINDNESS[args.kindness]
        if (args.place, args.irritant, args.kindness) not in valid_combos():
            raise StoryError(explain_rejection(place, irritant, kindness))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.irritant is None or combo[1] == args.irritant)
        and (args.kindness is None or combo[2] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, irritant_id, kindness_id = rng.choice(combos)
    spokesman_type = args.spokesman_type or rng.choice(sorted(SPEAKER_TYPES))
    spokesman_name = args.spokesman_name or _pick_name(rng, spokesman_type)
    companion_type = args.companion_type or rng.choice(sorted(COMPANION_TYPES))
    companion_name = args.companion_name or _pick_name(rng, companion_type, avoid=spokesman_name)
    return StoryParams(
        place=place_id,
        irritant=irritant_id,
        kindness=kindness_id,
        spokesman_type=spokesman_type,
        spokesman_name=spokesman_name,
        companion_type=companion_type,
        companion_name=companion_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.irritant not in IRRITANTS:
        raise StoryError(f"Unknown irritant: {params.irritant}")
    if params.kindness not in KINDNESS:
        raise StoryError(f"Unknown kindness: {params.kindness}")
    if params.spokesman_type not in SPEAKER_TYPES:
        raise StoryError(f"Unknown spokesman type: {params.spokesman_type}")
    if params.companion_type not in COMPANION_TYPES:
        raise StoryError(f"Unknown companion type: {params.companion_type}")

    place = PLACES[params.place]
    irritant = IRRITANTS[params.irritant]
    kindness = KINDNESS[params.kindness]
    if (params.place, params.irritant, params.kindness) not in valid_combos():
        raise StoryError(explain_rejection(place, irritant, kindness))

    world = tell(
        place=place,
        irritant=irritant,
        kindness=kindness,
        spokesman_type=params.spokesman_type,
        spokesman_name=params.spokesman_name,
        companion_type=params.companion_type,
        companion_name=params.companion_name,
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
        print(f"{len(combos)} compatible (place, irritant, kindness) combos:\n")
        for place, irritant, kindness in combos:
            print(f"  {place:16} {irritant:12} {kindness}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
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
            header = f"### {p.place}: {p.irritant} with {p.kindness}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
