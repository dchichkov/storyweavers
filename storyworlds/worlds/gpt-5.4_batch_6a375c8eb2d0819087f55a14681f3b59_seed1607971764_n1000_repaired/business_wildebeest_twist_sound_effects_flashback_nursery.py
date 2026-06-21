#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/business_wildebeest_twist_sound_effects_flashback_nursery.py
=======================================================================================

A standalone story world about a child and a kindly wildebeest running a tiny
market business in a nursery-rhyme style. The central choice is how they try to
call customers: with a signal that fits the place, or with one that is a little
too boomy for the morning. A flashback remembers an earlier noisy mistake, and a
twist reveals that the best sound was never the bought signal at all, but the
wildebeest's own neat clip-clop rhythm.

Run it
------
    python storyworlds/worlds/gpt-5.4/business_wildebeest_twist_sound_effects_flashback_nursery.py
    python storyworlds/worlds/gpt-5.4/business_wildebeest_twist_sound_effects_flashback_nursery.py --place market_square --signal horn
    python storyworlds/worlds/gpt-5.4/business_wildebeest_twist_sound_effects_flashback_nursery.py --place dawn_lane --signal drum
    python storyworlds/worlds/gpt-5.4/business_wildebeest_twist_sound_effects_flashback_nursery.py --all --qa
    python storyworlds/worlds/gpt-5.4/business_wildebeest_twist_sound_effects_flashback_nursery.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Place:
    id: str
    label: str
    neighbor: str
    calm_max: int
    allow_max: int
    ending_image: str
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
class Business:
    id: str
    label: str
    wares: str
    tray: str
    ending_good: str
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
class Signal:
    id: str
    label: str
    volume: int
    sound: str
    lead: str
    gentle: bool
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
class Memory:
    id: str
    signal_text: str
    sound: str
    mishap: str
    lesson: str
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
class World:
    place: Place
    business: Business

    def __post_init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "used_signal": False,
            "signal_volume": 0,
            "hoof_rhythm": 0.0,
            "market_open": True,
            "crowd_before": 0.0,
            "crowd_after": 0.0,
        }

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
        clone = World(self.place, self.business)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_loud_disturbance(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("used_signal"):
        return out
    vol = int(world.facts.get("signal_volume", 0))
    if vol <= world.place.calm_max:
        return out
    sig = ("loud_disturbance", vol, world.place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stall = world.get("stall")
    helper = world.get("helper")
    child = world.get("child")
    stall.meters["wobble"] += 1
    stall.meters["crowd"] -= 1
    helper.memes["surprise"] += 1
    child.memes["worry"] += 1
    out.append("__wobble__")
    return out


def _r_hoof_charm(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("hoof_rhythm", 0.0) < THRESHOLD:
        return out
    sig = ("hoof_charm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stall = world.get("stall")
    child = world.get("child")
    helper = world.get("helper")
    stall.meters["crowd"] += 2
    stall.meters["sales"] += 2
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["pride"] += 1
    out.append("__sales__")
    return out


CAUSAL_RULES = [
    Rule(name="loud_disturbance", tag="physical", apply=_r_loud_disturbance),
    Rule(name="hoof_charm", tag="social", apply=_r_hoof_charm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def valid_combo(place: Place, signal: Signal) -> bool:
    return signal.volume <= place.allow_max


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for business_id in BUSINESSES:
            for signal_id, signal in SIGNALS.items():
                if valid_combo(place, signal):
                    combos.append((place_id, business_id, signal_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    signal = SIGNALS[params.signal]
    if not valid_combo(place, signal):
        return "invalid"
    if signal.volume > place.calm_max:
        return "noisy_twist"
    return "gentle_twist"


def predict_call(world: World, signal: Signal) -> dict:
    sim = world.copy()
    sim.facts["used_signal"] = True
    sim.facts["signal_volume"] = signal.volume
    propagate(sim, narrate=False)
    stall = sim.get("stall")
    child = sim.get("child")
    return {
        "wobble": stall.meters["wobble"] >= THRESHOLD,
        "crowd": stall.meters["crowd"],
        "worry": child.memes["worry"],
    }


def opening(world: World, child: Entity, helper: Entity) -> None:
    child.memes["hope"] += 1
    helper.memes["helpfulness"] += 1
    world.say(
        f"Clip-clop, tip-top, morning in the square: {child.id} opened a tiny "
        f"{world.business.label} business with {helper.id}, a gentle wildebeest with a tidy blue bow."
    )
    world.say(
        f"They set out {world.business.wares} on {world.business.tray}, and the day looked sweet enough to sing to."
    )


def slow_start(world: World, child: Entity) -> None:
    stall = world.get("stall")
    stall.meters["crowd"] = 0.0
    world.say(
        f"But hush went the lane, and no one stopped. {child.id} tapped the counter and whispered, "
        f'"If no one hears us, who will visit our little business?"'
    )


def flashback(world: World, child: Entity, memory: Memory) -> None:
    child.memes["memory"] += 1
    world.say(
        f"Then back came a yesterday, soft as a picture in a puddle: {memory.sound}! {memory.signal_text}! "
        f"{memory.mishap} {memory.lesson}"
    )


def choose_signal(world: World, child: Entity, helper: Entity, signal: Signal) -> None:
    pred = predict_call(world, signal)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_worry"] = pred["worry"]
    world.facts["signal_cfg"] = signal
    helper.attrs["chosen_signal"] = signal.id
    world.say(
        f'{helper.id} lifted the {signal.label}. "{signal.lead}," {child.id} said, listening hard.'
    )
    if pred["wobble"]:
        world.say(
            f"The thought of it made {child.id}'s shoulders go still. This place liked gentle mornings, and a loud call might make the stall shake."
        )
    else:
        world.say(
            f"It sounded just right for the place, bright enough to notice and soft enough to keep the morning smiling."
        )


def sound_call(world: World, child: Entity, helper: Entity, signal: Signal) -> None:
    world.facts["used_signal"] = True
    world.facts["signal_volume"] = signal.volume
    child.memes["trying"] += 1
    helper.memes["trying"] += 1
    world.say(
        f"So {helper.id} gave the call: {signal.sound}! {signal.sound}! The little sound hopped over baskets and boots."
    )
    propagate(world, narrate=False)
    stall = world.get("stall")
    if stall.meters["wobble"] >= THRESHOLD:
        world.say(
            f"But wobble-wobble went the stall, and {world.business.wares} gave a tiny shiver. "
            f"{child.id} put out both hands and hushed the air."
        )
    else:
        world.say(
            f"No cups rattled, no ribbons flew; the sound sat neatly in the morning like a button on a shoe."
        )
    world.facts["crowd_before"] = stall.meters["crowd"]


def discover_twist(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f"Then came the twist. Not the {world.facts['signal_cfg'].label}, not the bought-up noise, "
        f"but {helper.id}'s own feet saved the day."
    )
    world.say(
        f"Clip-clop, clip-clop went the wildebeest as {helper.pronoun()} stepped back from the stall. "
        f"{child.id} heard the beat, matched it with a rhyme, and grinned."
    )
    world.facts["hoof_rhythm"] = 1.0
    propagate(world, narrate=False)


def sales_and_end(world: World, child: Entity, helper: Entity, signal: Signal) -> None:
    stall = world.get("stall")
    world.facts["crowd_after"] = stall.meters["crowd"]
    if stall.meters["sales"] >= THRESHOLD:
        world.say(
            f'"{world.business.ending_good}," sang {child.id}, and {helper.id} clip-clopped the beat again.'
        )
        world.say(
            f"Folks turned, smiled, and came to buy. Soon the tiny business was busy for the best reason of all: it sounded like itself."
        )
    if signal.volume > world.place.calm_max:
        world.say(
            f"{child.id} set the {signal.label} down for later and kept the kinder rhythm instead."
        )
    else:
        world.say(
            f"The {signal.label} rested by the till, but the truest music was the hoofbeat under the rhyme."
        )
    world.say(
        f"When the sun climbed higher, {world.place.ending_image} and {helper.id} stood proud beside the stall, "
        f"soft-sound wise and smiling."
    )


def tell(
    place: Place,
    business: Business,
    signal: Signal,
    memory: Memory,
    child_name: str = "Mabel",
    child_gender: str = "girl",
    helper_name: str = "Mop",
    parent_type: str = "mother",
) -> World:
    world = World(place=place, business=business)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type="wildebeest",
            role="helper",
            attrs={"bow_color": "blue", "chosen_signal": ""},
        )
    )
    world.add(Entity(id="stall", type="stall", label=business.label, role="stall"))
    world.add(Entity(id="parent", kind="character", type=parent_type, role="parent", label="the parent"))

    opening(world, child, helper)
    slow_start(world, child)

    world.para()
    flashback(world, child, memory)
    choose_signal(world, child, helper, signal)

    world.para()
    sound_call(world, child, helper, signal)
    discover_twist(world, child, helper)

    world.para()
    sales_and_end(world, child, helper, signal)

    world.facts.update(
        child=child,
        helper=helper,
        place_cfg=place,
        business_cfg=business,
        memory_cfg=memory,
        signal_cfg=signal,
        stall=world.get("stall"),
        outcome="noisy_twist" if signal.volume > place.calm_max else "gentle_twist",
        wobble=world.get("stall").meters["wobble"] >= THRESHOLD,
        sold=world.get("stall").meters["sales"] >= THRESHOLD,
        twist_source="hoofbeat",
    )
    return world


PLACES = {
    "dawn_lane": Place(
        id="dawn_lane",
        label="Dawn Lane",
        neighbor="sleepy windows",
        calm_max=1,
        allow_max=1,
        ending_image="the sleepy windows stayed sleepy while the customers lined up in a happy row",
        tags={"quiet_place"},
    ),
    "pond_path": Place(
        id="pond_path",
        label="Pond Path",
        neighbor="duck nests",
        calm_max=1,
        allow_max=2,
        ending_image="the duck nests stayed calm while coins clinked gently in the jar",
        tags={"pond", "quiet_place"},
    ),
    "market_square": Place(
        id="market_square",
        label="Market Square",
        neighbor="busy carts",
        calm_max=2,
        allow_max=3,
        ending_image="busy carts rolled by while the stall glowed bright as a rhyme book picture",
        tags={"market"},
    ),
}

BUSINESSES = {
    "bun_barrow": Business(
        id="bun_barrow",
        label="bun barrow",
        wares="round honey buns",
        tray="a red-striped cloth",
        ending_good="Buns for lunch, not for crunch",
        tags={"buns", "business"},
    ),
    "berry_basket": Business(
        id="berry_basket",
        label="berry basket stand",
        wares="shiny berries in little cups",
        tray="a white tray with painted dots",
        ending_good="Berries bright, morning delight",
        tags={"berries", "business"},
    ),
    "ribbon_cart": Business(
        id="ribbon_cart",
        label="ribbon cart",
        wares="loops of ribbon in sunny colors",
        tray="a tiny cart with brass hooks",
        ending_good="Ribbons sway for a bright new day",
        tags={"ribbons", "business"},
    ),
}

SIGNALS = {
    "bell": Signal(
        id="bell",
        label="bell",
        volume=1,
        sound="ting-ting",
        lead="A bell may ring, but not too strong",
        gentle=True,
        tags={"bell", "sound"},
    ),
    "rhyme": Signal(
        id="rhyme",
        label="market rhyme",
        volume=1,
        sound="la-la-lilt",
        lead="A rhyme may skip where feet belong",
        gentle=True,
        tags={"rhyme", "sound"},
    ),
    "clapper": Signal(
        id="clapper",
        label="wooden clapper",
        volume=2,
        sound="clack-clack",
        lead="A clapper talks in tidy knocks",
        gentle=False,
        tags={"clapper", "sound"},
    ),
    "drum": Signal(
        id="drum",
        label="drum",
        volume=3,
        sound="boom-boom",
        lead="A drum can boom from box to box",
        gentle=False,
        tags={"drum", "sound"},
    ),
    "horn": Signal(
        id="horn",
        label="horn",
        volume=3,
        sound="toot-toooot",
        lead="A horn can toot from curb to curb",
        gentle=False,
        tags={"horn", "sound"},
    ),
}

MEMORIES = {
    "drum_day": Memory(
        id="drum_day",
        signal_text="the old drum",
        sound="Boom-boom",
        mishap="One bun bounced, one berry cup tipped, and even the ribbons wriggled",
        lesson="Since then, Mabel had known that not every sound helps a stall.",
        tags={"flashback", "drum"},
    ),
    "horn_day": Memory(
        id="horn_day",
        signal_text="the brass horn",
        sound="Toot-toooot",
        mishap="The ducklings tucked their heads, and a row of cups trembled at the edge",
        lesson="Since then, Mabel had known that a business needs a sound that fits the place.",
        tags={"flashback", "horn"},
    ),
    "clapper_day": Memory(
        id="clapper_day",
        signal_text="the wooden clapper",
        sound="Clack-clack",
        mishap="The cloth on the stall jumped, and the morning lost its easy hum",
        lesson="Since then, Mabel had known that louder is not always wiser.",
        tags={"flashback", "clapper"},
    ),
}

GIRL_NAMES = ["Mabel", "Tilly", "Nora", "Daisy", "Poppy", "Mina"]
BOY_NAMES = ["Toby", "Benji", "Ollie", "Milo", "Ned", "Finn"]
WILDEBEEST_NAMES = ["Mop", "Clip", "Clover", "Bramble", "Tumble", "Pip"]


@dataclass
class StoryParams:
    place: str
    business: str
    signal: str
    memory: str
    child_name: str
    child_gender: str
    helper_name: str
    parent: str
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


KNOWLEDGE = {
    "business": [
        (
            "What is a business?",
            "A business is a little place where people make or sell something for others. It works best when people can find it and feel welcome there.",
        )
    ],
    "wildebeest": [
        (
            "What is a wildebeest?",
            "A wildebeest is a big hoofed animal with a shaggy mane and strong legs. In real life it is wild, but in this story it is a gentle helper.",
        )
    ],
    "bell": [
        (
            "Why is a bell a gentle way to call people?",
            "A bell makes a clear little sound that people can notice without feeling startled. That is useful when a place is calm and quiet.",
        )
    ],
    "rhyme": [
        (
            "Why do rhymes help people remember things?",
            "Rhymes have a beat and matching sounds, so they are easy to hear and easy to repeat. That is why a short rhyme can make a shop or stall feel friendly.",
        )
    ],
    "drum": [
        (
            "Why can a drum be too loud in a quiet place?",
            "A drum can make a big booming sound that jumps into the air all at once. In a quiet place, that can feel startling instead of cheerful.",
        )
    ],
    "horn": [
        (
            "What does a horn sound like?",
            "A horn makes a bright, strong toot that carries far away. That can help in a busy place, but it may be too much in a gentle one.",
        )
    ],
    "clapper": [
        (
            "What is a clapper?",
            "A clapper is a little noisemaker that clicks or clacks when it is struck. It is sharper than a bell and softer than a great big drum.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when the story briefly looks back at something that happened earlier. It helps explain why a character feels careful or brave now.",
        )
    ],
    "twist": [
        (
            "What is a twist in a story?",
            "A twist is a surprise turn. It happens when the answer is different from what the characters first expected.",
        )
    ],
    "hoofbeat": [
        (
            "Why can a hoofbeat sound musical?",
            "Hooves can make a repeating clip-clop rhythm on the ground. A steady rhythm can feel like a beat for a song or rhyme.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "business",
    "wildebeest",
    "bell",
    "rhyme",
    "clapper",
    "drum",
    "horn",
    "flashback",
    "twist",
    "hoofbeat",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    business = f["business_cfg"]
    place = f["place_cfg"]
    signal = f["signal_cfg"]
    return [
        f'Write a nursery-rhyme-style story that includes the words "business" and "wildebeest", set at {place.label}, where a child and a gentle wildebeest run a tiny {business.label}.',
        f"Tell a short rhyming story where {child.id} and {helper.id} try to call customers with a {signal.label}, include sound effects, include a flashback, and end with a twist.",
        f"Write a child-facing market tale in a singsong voice where the best sound for a little business turns out not to be the first sound the characters expected.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    business = f["business_cfg"]
    place = f["place_cfg"]
    signal = f["signal_cfg"]
    memory = f["memory_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {helper.id}, a gentle wildebeest, running a tiny {business.label} business together. They are trying to make their stall cheerful enough for customers to notice.",
        ),
        (
            "What problem did they have at the start?",
            f"The morning was quiet, and no one was stopping at their stall. That made {child.id} worry that their little business would be missed.",
        ),
        (
            "What happened in the flashback?",
            f"In the flashback, {memory.signal_text} made too much commotion and the stall goods jumped about. That old memory is why {child.id} listened so carefully before trying a new sound.",
        ),
        (
            f"Why was {child.id} careful about using the {signal.label}?",
            (
                f"{child.id} was careful because this place, {place.label}, likes softer sounds than some busier places do. "
                + (
                    "The world of the story predicts that the call could make the stall wobble, so the worry comes from a real risk."
                    if f.get("wobble")
                    else "The call fit the place, so it could help without startling the morning."
                )
            ),
        ),
        (
            "What was the twist?",
            f"The twist was that the best sound was not the tool they chose at first. The real winner was {helper.id}'s clip-clop hoofbeat, which turned into a rhythm for the rhyme and brought customers over.",
        ),
        (
            "How did the story end?",
            (
                f"The stall ended busy and happy, with people coming to buy from the little business. "
                + (
                    f"{child.id} put the {signal.label} aside and kept the kinder clip-clop rhythm instead."
                    if signal.volume > place.calm_max
                    else f"The {signal.label} was fine, but the ending showed that the hoofbeat-and-rhyme was even better."
                )
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"business", "wildebeest", "flashback", "twist", "hoofbeat"}
    tags |= set(world.facts["signal_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    lines.append(f"  place={world.place.id} calm_max={world.place.calm_max} allow_max={world.place.allow_max}")
    lines.append(f"  business={world.business.id}")
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts.get('outcome')} crowd_before={world.facts.get('crowd_before')} crowd_after={world.facts.get('crowd_after')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="dawn_lane",
        business="bun_barrow",
        signal="bell",
        memory="drum_day",
        child_name="Mabel",
        child_gender="girl",
        helper_name="Mop",
        parent="mother",
    ),
    StoryParams(
        place="pond_path",
        business="berry_basket",
        signal="clapper",
        memory="horn_day",
        child_name="Toby",
        child_gender="boy",
        helper_name="Clip",
        parent="father",
    ),
    StoryParams(
        place="market_square",
        business="ribbon_cart",
        signal="horn",
        memory="clapper_day",
        child_name="Poppy",
        child_gender="girl",
        helper_name="Bramble",
        parent="mother",
    ),
    StoryParams(
        place="market_square",
        business="bun_barrow",
        signal="drum",
        memory="drum_day",
        child_name="Milo",
        child_gender="boy",
        helper_name="Tumble",
        parent="father",
    ),
]


def explain_rejection(place: Place, signal: Signal) -> str:
    return (
        f"(No story: {signal.label} is too loud for {place.label}. "
        f"This place only allows sounds up to {place.allow_max}, but {signal.label} has volume {signal.volume}. "
        f"Pick a gentler signal, or choose a busier place.)"
    )


ASP_RULES = r"""
valid(P,B,S) :- place(P), business(B), signal(S), volume(S,V), allow_max(P,A), V <= A.

noisy(P,S) :- volume(S,V), calm_max(P,C), V > C.
gentle(P,S) :- volume(S,V), calm_max(P,C), V <= C.

outcome(gentle_twist) :- chosen_place(P), chosen_business(B), chosen_signal(S),
                         valid(P,B,S), gentle(P,S).
outcome(noisy_twist) :- chosen_place(P), chosen_business(B), chosen_signal(S),
                        valid(P,B,S), noisy(P,S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("calm_max", place_id, place.calm_max))
        lines.append(asp.fact("allow_max", place_id, place.allow_max))
    for business_id in BUSINESSES:
        lines.append(asp.fact("business", business_id))
    for signal_id, signal in SIGNALS.items():
        lines.append(asp.fact("signal", signal_id))
        lines.append(asp.fact("volume", signal_id, signal.volume))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_business", params.business),
            asp.fact("chosen_signal", params.signal),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: a tiny business, a gentle wildebeest, a remembered noise, and a surprising better sound."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--business", choices=BUSINESSES)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.signal:
        place = PLACES[args.place]
        signal = SIGNALS[args.signal]
        if not valid_combo(place, signal):
            raise StoryError(explain_rejection(place, signal))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.business is None or combo[1] == args.business)
        and (args.signal is None or combo[2] == args.signal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, business_id, signal_id = rng.choice(sorted(combos))
    memory_id = args.memory or rng.choice(sorted(MEMORIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    helper_name = args.helper or rng.choice(WILDEBEEST_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        business=business_id,
        signal=signal_id,
        memory=memory_id,
        child_name=child_name,
        child_gender=gender,
        helper_name=helper_name,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.business not in BUSINESSES:
        raise StoryError(f"(Unknown business: {params.business})")
    if params.signal not in SIGNALS:
        raise StoryError(f"(Unknown signal: {params.signal})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")

    place = PLACES[params.place]
    signal = SIGNALS[params.signal]
    if not valid_combo(place, signal):
        raise StoryError(explain_rejection(place, signal))

    world = tell(
        place=place,
        business=BUSINESSES[params.business],
        signal=signal,
        memory=MEMORIES[params.memory],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        parent_type=params.parent,
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
        print(f"OK: valid combinations match ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, business, signal) combos:\n")
        for place, business, signal in combos:
            print(f"  {place:13} {business:13} {signal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.child_name}: {p.business} at {p.place} with {p.signal} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
