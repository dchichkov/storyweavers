#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/churn_ply_contend_inner_monologue_surprise_bedtime.py
=================================================================================

A standalone bedtime-story world about a child who hears a mysterious bedtime
sound, feels worry churn inside, and must decide whether to contend with the
dark alone or call for help. The surprise is always gentle: the frightening
shape turns out to be something ordinary and safe, and the ending image proves
that the room has changed from scary to snug.

Run it
------
    python storyworlds/worlds/gpt-5.4/churn_ply_contend_inner_monologue_surprise_bedtime.py
    python storyworlds/worlds/gpt-5.4/churn_ply_contend_inner_monologue_surprise_bedtime.py --source branch --worry dragon
    python storyworlds/worlds/gpt-5.4/churn_ply_contend_inner_monologue_surprise_bedtime.py --source laundry --worry ghost
    python storyworlds/worlds/gpt-5.4/churn_ply_contend_inner_monologue_surprise_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/churn_ply_contend_inner_monologue_surprise_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/churn_ply_contend_inner_monologue_surprise_bedtime.py --trace
    python storyworlds/worlds/gpt-5.4/churn_ply_contend_inner_monologue_surprise_bedtime.py --verify
"""

from __future__ import annotations

import argparse
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
CAUTIOUS_TRAITS = {"careful", "gentle", "thoughtful"}
BOLD_TRAITS = {"bold", "curious", "spirited"}


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
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Bedroom:
    id: str
    label: str
    bedtime_image: str
    window_note: str
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
    sound: str
    motion: str
    reveal: str
    location: str
    plausible_worries: set[str] = field(default_factory=set)
    needs_window: bool = False
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
class Worry:
    id: str
    label: str
    think_line: str
    shape: str
    needs_light: bool = True
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
class ComfortAid:
    id: str
    label: str
    phrase: str
    action: str
    glow: str
    power: int
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
    def __init__(self, bedroom: Bedroom) -> None:
        self.bedroom = bedroom
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
        clone = World(self.bedroom)
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


def _r_mystery(world: World) -> list[str]:
    room = world.get("room")
    source = world.get("source")
    if source.meters["active"] < THRESHOLD:
        return []
    sig = ("mystery", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mystery"] += 1
    room.meters["noise"] += 1
    return []


def _r_fear(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    if room.meters["mystery"] < THRESHOLD:
        return []
    sig = ("fear", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    return []


def _r_peek_worsens(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["peeked"] < THRESHOLD or child.memes["fear"] < THRESHOLD:
        return []
    sig = ("peek_worsens", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    return []


def _r_light_reveals(world: World) -> list[str]:
    child = world.get("child")
    room = world.get("room")
    helper = world.get("helper")
    aid = world.get("aid")
    source = world.get("source")
    if helper.meters["arrived"] < THRESHOLD or aid.meters["used"] < THRESHOLD:
        return []
    sig = ("light_reveals", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["mystery"] = 0.0
    room.meters["noise"] = 0.0
    source.meters["seen_clearly"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    child.memes["sleepy"] += 1
    helper.memes["care"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="mystery", tag="physical", apply=_r_mystery),
    Rule(name="fear", tag="emotional", apply=_r_fear),
    Rule(name="peek_worsens", tag="emotional", apply=_r_peek_worsens),
    Rule(name="light_reveals", tag="physical", apply=_r_light_reveals),
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


def worry_fits(source: Source, worry: Worry) -> bool:
    return worry.id in source.plausible_worries


def best_aids() -> list[ComfortAid]:
    return [aid for aid in AIDS.values() if aid.power >= 1]


def outcome_of(params: "StoryParams") -> str:
    return "quick_help" if params.trait in CAUTIOUS_TRAITS else "peek_then_help"


def predict_peek(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["peeked"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": child.memes["fear"],
        "mystery": sim.get("room").meters["mystery"],
    }


def scene_open(world: World, child: Entity, bedroom: Bedroom) -> None:
    child.memes["sleepy"] += 1
    room = world.get("room")
    room.meters["darkness"] += 1
    world.say(
        f"It was bedtime, and {child.id}'s room felt soft and small. "
        f"{bedroom.bedtime_image} {bedroom.window_note}"
    )


def settle_in(world: World, child: Entity, bedtime_friend: str) -> None:
    if bedtime_friend:
        child.attrs["bedtime_friend"] = bedtime_friend
        world.say(
            f"{child.id} tucked {bedtime_friend} under one arm and pulled the blanket to {child.pronoun('possessive')} chin."
        )
    else:
        world.say(
            f"{child.id} pulled the blanket to {child.pronoun('possessive')} chin and listened to the house grow quieter and quieter."
        )


def startle(world: World, child: Entity, source: Source) -> None:
    src = world.get("source")
    src.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {source.sound}. Something seemed to {source.motion} in the dark near {source.location}."
    )


def inner_monologue(world: World, child: Entity, worry: Worry, source: Source) -> None:
    pred = predict_peek(world)
    world.facts["predicted_peek_fear"] = pred["fear"]
    child.memes["imagination"] += 1
    world.say(
        f'{child.id} held very still. Inside {child.pronoun("possessive")} head, thoughts began to churn. '
        f'"{worry.think_line}" {child.pronoun()} wondered.'
    )
    if source.needs_window:
        world.say(
            f"The moonlight seemed to ply silver stripes across the floor, and each stripe made the shape look stranger."
        )
    else:
        world.say(
            f"The dark corners made the shape look stranger every time {child.pronoun()} blinked."
        )


def decide_quick_help(world: World, child: Entity, helper: Entity, worry: Worry) -> None:
    child.memes["caution"] += 1
    child.meters["called"] += 1
    world.say(
        f'"Can I contend with this by myself?" {child.id} thought. Then {child.pronoun()} gave a tiny shake of {child.pronoun("possessive")} head.'
    )
    world.say(
        f'"{helper.label_word.capitalize()}?" {child.pronoun()} whispered. "I think there is {worry.label} in my room."'
    )


def decide_peek_first(world: World, child: Entity, worry: Worry) -> None:
    child.memes["bravery"] += 1
    child.meters["peeked"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Maybe I can be brave for one little peek," {child.id} thought.'
    )
    world.say(
        f"{child.pronoun().capitalize()} lifted the blanket just enough to look, but the {worry.shape} shape only made {child.pronoun('possessive')} heart thump faster."
    )


def call_after_peek(world: World, child: Entity, helper: Entity) -> None:
    child.meters["called"] += 1
    world.say(
        f'"{helper.label_word.capitalize()}!" {child.id} called then, louder this time. "Please come see."'
    )


def helper_arrives(world: World, helper: Entity, aid: ComfortAid) -> None:
    helper.meters["arrived"] += 1
    world.get("aid").meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} came in at once with {aid.phrase}. {helper.pronoun().capitalize()} {aid.action}, and {aid.glow}."
    )


def reveal(world: World, child: Entity, helper: Entity, source: Source, worry: Worry) -> None:
    source_ent = world.get("source")
    source_ent.meters["revealed"] += 1
    world.say(
        f"It was only {source.reveal}. There was no {worry.label} at all."
    )
    if source.id == "kitten":
        world.say(
            f"The surprise made {child.id} blink, and then laugh a little as the tiny visitor blinked back."
        )
    else:
        world.say(
            f"The surprise was so ordinary that {child.id}'s shoulders dropped at once."
        )
    world.say(
        f'"There now," said {helper.label_word}. "Dark can make small things look much bigger than they are."'
    )


def soothe(world: World, child: Entity, helper: Entity, aid: ComfortAid, source: Source) -> None:
    child.memes["love"] += 1
    world.say(
        f"{helper.label_word.capitalize()} sat on the edge of the bed until the room felt familiar again."
    )
    if source.id == "branch":
        world.say(
            f"{helper.pronoun().capitalize()} tied the curtain back so the branch could not tap the window again."
        )
    elif source.id == "laundry":
        world.say(
            f"{helper.pronoun().capitalize()} folded the robe and set it neatly in the basket."
        )
    elif source.id == "mobile":
        world.say(
            f"{helper.pronoun().capitalize()} moved the mobile so it would rest still above the bed."
        )
    else:
        world.say(
            f"{helper.pronoun().capitalize()} lifted the kitten gently into a basket with a towel."
        )
    world.say(
        f"Soon {aid.label} made a warm little pool of light, and the corners of the room looked kind again."
    )


def ending(world: World, child: Entity, bedtime_friend: str) -> None:
    if bedtime_friend:
        world.say(
            f"{child.id} curled up with {bedtime_friend}, let out one long breath, and closed {child.pronoun('possessive')} eyes."
        )
    else:
        world.say(
            f"{child.id} let out one long breath, snuggled deeper under the blanket, and closed {child.pronoun('possessive')} eyes."
        )
    world.say(
        f"This time the room held only bedtime sounds, and sleep came softly at last."
    )


def tell(
    bedroom: Bedroom,
    source: Source,
    worry: Worry,
    aid: ComfortAid,
    child_name: str = "Mina",
    child_type: str = "girl",
    helper_type: str = "mother",
    trait: str = "careful",
    bedtime_friend: str = "",
) -> World:
    world = World(bedroom)
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_type,
            label=child_name,
            traits=[trait],
            role="child",
            attrs={"bedtime_friend": bedtime_friend},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
            attrs={},
        )
    )
    room = world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            label=bedroom.label,
            role="room",
            attrs={},
        )
    )
    source_ent = world.add(
        Entity(
            id="source",
            kind="thing",
            type="source",
            label=source.label,
            role="source",
            attrs={},
        )
    )
    aid_ent = world.add(
        Entity(
            id="aid",
            kind="thing",
            type="aid",
            label=aid.label,
            role="aid",
            attrs={},
        )
    )
    world.facts.update(
        child=child,
        helper=helper,
        bedroom=bedroom,
        source_cfg=source,
        worry_cfg=worry,
        aid_cfg=aid,
        source=source_ent,
        aid=aid_ent,
        bedtime_friend=bedtime_friend,
        trait=trait,
    )

    scene_open(world, child, bedroom)
    settle_in(world, child, bedtime_friend)

    world.para()
    startle(world, child, source)
    inner_monologue(world, child, worry, source)

    world.para()
    if trait in CAUTIOUS_TRAITS:
        decide_quick_help(world, child, helper, worry)
        outcome = "quick_help"
    else:
        decide_peek_first(world, child, worry)
        call_after_peek(world, child, helper)
        outcome = "peek_then_help"

    world.para()
    helper_arrives(world, helper, aid)
    reveal(world, child, helper, source, worry)
    soothe(world, child, helper, aid, source)

    world.para()
    ending(world, child, bedtime_friend)

    world.facts.update(
        outcome=outcome,
        mystery_started=room.meters["darkness"] >= THRESHOLD,
        fear_before_help=(2.0 if outcome == "peek_then_help" else 1.0),
        source_revealed=source_ent.meters["revealed"] >= THRESHOLD,
    )
    return world


BEDROOMS = {
    "moon": Bedroom(
        id="moon",
        label="moon room",
        bedtime_image="A moon quilt lay smooth across the bed, and a row of paper stars glimmered over the shelf.",
        window_note="The curtains were half open to the night.",
        tags={"bedroom", "moon"},
    ),
    "ocean": Bedroom(
        id="ocean",
        label="ocean room",
        bedtime_image="A blue blanket looked like a sleepy sea, and a shell lamp waited on the dresser.",
        window_note="A thin wash of moonlight reached the rug.",
        tags={"bedroom", "ocean"},
    ),
    "forest": Bedroom(
        id="forest",
        label="forest room",
        bedtime_image="Leaf shadows rested on the wall, and a little stack of books sat beside the pillow.",
        window_note="The window was cracked open to the cool air.",
        tags={"bedroom", "forest"},
    ),
}

SOURCES = {
    "branch": Source(
        id="branch",
        label="branch",
        sound="a twiggy tap-tap came at the window",
        motion="ply back and forth",
        reveal="a windy branch brushing the glass",
        location="the window",
        plausible_worries={"dragon", "giant"},
        needs_window=True,
        tags={"window", "wind", "branch"},
    ),
    "laundry": Source(
        id="laundry",
        label="robe",
        sound="a soft shuff-shuff came from the chair",
        motion="sway",
        reveal="a robe slipping from the chair to the floor",
        location="the chair",
        plausible_worries={"ghost", "giant"},
        needs_window=False,
        tags={"chair", "robe"},
    ),
    "mobile": Source(
        id="mobile",
        label="mobile",
        sound="a tiny clink-clink drifted from above",
        motion="turn",
        reveal="a moon-and-boat mobile nudging the wall",
        location="the ceiling",
        plausible_worries={"dragon", "ghost"},
        needs_window=False,
        tags={"mobile", "ceiling"},
    ),
    "kitten": Source(
        id="kitten",
        label="kitten",
        sound="a small rustle and one brave mew came from under the bed",
        motion="shuffle",
        reveal="a lost kitten batting at a dust ruffle",
        location="under the bed",
        plausible_worries={"ghost"},
        needs_window=False,
        tags={"kitten", "under_bed", "surprise"},
    ),
}

WORRIES = {
    "dragon": Worry(
        id="dragon",
        label="a dragon",
        think_line="What if a dragon has folded itself into the dark and is waiting to open one bright eye?",
        shape="long-necked",
        needs_light=True,
        tags={"dragon", "fear"},
    ),
    "ghost": Worry(
        id="ghost",
        label="a ghost",
        think_line="What if a ghost is floating there, quiet as a pillowcase?",
        shape="floating",
        needs_light=True,
        tags={"ghost", "fear"},
    ),
    "giant": Worry(
        id="giant",
        label="a giant",
        think_line="What if a giant has bent down to look through the window?",
        shape="tall",
        needs_light=True,
        tags={"giant", "fear"},
    ),
}

AIDS = {
    "nightlight": ComfortAid(
        id="nightlight",
        label="the night-light",
        phrase="the little night-light",
        action="clicked it on",
        glow="a soft gold circle bloomed near the bed",
        power=1,
        tags={"light", "nightlight"},
    ),
    "lantern": ComfortAid(
        id="lantern",
        label="the lantern",
        phrase="a small lantern",
        action="set it on the dresser and turned the knob",
        glow="honey-colored light slid across the room",
        power=1,
        tags={"light", "lantern"},
    ),
    "flashlight": ComfortAid(
        id="flashlight",
        label="the flashlight",
        phrase="a flashlight",
        action="aimed it gently into the corners",
        glow="a bright beam hopped from bedpost to chair to window",
        power=1,
        tags={"light", "flashlight"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "Ivy", "June", "Ella", "Maya"]
BOY_NAMES = ["Owen", "Leo", "Finn", "Theo", "Milo", "Sam", "Eli", "Noah"]
TRAITS = ["careful", "gentle", "thoughtful", "bold", "curious", "spirited"]
FRIENDS = ["a rabbit doll", "a plush fox", "a small bear", "a knitted whale"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for bedroom_id in BEDROOMS:
        for source_id, source in SOURCES.items():
            for worry_id, worry in WORRIES.items():
                if worry_fits(source, worry) and best_aids():
                    combos.append((bedroom_id, source_id, worry_id))
    return combos


@dataclass
class StoryParams:
    bedroom: str
    source: str
    worry: str
    aid: str
    child_name: str
    child_type: str
    helper_type: str
    trait: str
    bedtime_friend: str = ""
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
    "nightlight": [
        (
            "What does a night-light do?",
            "A night-light makes a small gentle glow in a dark room. It helps you see that familiar things are still where they belong."
        )
    ],
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp with light inside it. It can brighten a room without making loud or scary shadows."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for?",
            "A flashlight helps you shine light exactly where you want to look. Seeing clearly often makes a mystery feel much smaller."
        )
    ],
    "branch": [
        (
            "Why can a branch sound loud at night?",
            "A branch can tap a window when the wind moves it. In a quiet room, small sounds can seem bigger than they really are."
        )
    ],
    "ghost": [
        (
            "Why do shadows sometimes look spooky?",
            "In the dark, your eyes do not get all the details. Your imagination can fill in the rest and make an ordinary shape seem spooky."
        )
    ],
    "dragon": [
        (
            "Can a shadow really be a dragon?",
            "No. A shadow is just light being blocked by something real, like a chair or a curtain or a branch."
        )
    ],
    "giant": [
        (
            "Why can something small look giant in the dark?",
            "When light is dim, sizes are harder to judge. A small thing can throw a big shape that only looks giant."
        )
    ],
    "kitten": [
        (
            "What should you do if you find a lost kitten?",
            "Tell a grown-up right away. A grown-up can make a safe warm place for the kitten and decide how to help it."
        )
    ],
}
KNOWLEDGE_ORDER = ["nightlight", "lantern", "flashlight", "branch", "ghost", "dragon", "giant", "kitten"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    worry = f["worry_cfg"]
    source = f["source_cfg"]
    aid = f["aid_cfg"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "churn", "ply", and "contend".',
        f"Tell a gentle bedtime story where {child.label} hears a mysterious sound, worries it might be {worry.label}, and then {helper.label_word} uses {aid.label} to reveal the harmless truth.",
        f"Write a sleepy story with inner monologue and a surprise ending where {source.label} seems scary in the dark but turns out to be safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    source = f["source_cfg"]
    worry = f["worry_cfg"]
    aid = f["aid_cfg"]
    outcome = f["outcome"]
    bedtime_friend = f.get("bedtime_friend", "")
    qas: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, who was trying to fall asleep, and {helper.label_word}, who came to help. The whole story happens around one small bedtime worry in {child.pronoun('possessive')} room."
        ),
        (
            "What scared the child at bedtime?",
            f"{source.sound.capitalize()}, and in the dark it seemed much stranger than it really was. The mystery sound and shape made {child.label}'s thoughts churn into a scary idea about {worry.label}."
        ),
        (
            "What was the child thinking to themself?",
            f"{child.label} wondered whether the dark shape might be {worry.label}. That inner worry made the room feel bigger and less familiar until help came."
        ),
    ]
    if outcome == "quick_help":
        qas.append(
            (
                f"How did {child.label} handle the scary moment?",
                f"{child.label} decided not to contend with the mystery alone and whispered for {helper.label_word}. Asking for help was the turning point, because it brought light and calm into the room right away."
            )
        )
    else:
        qas.append(
            (
                f"What happened when {child.label} peeked first?",
                f"{child.label} tried one brave peek, but the strange shape only looked scarier. That made {child.pronoun('object')} call for {helper.label_word}, who could actually show what was there."
            )
        )
    qas.append(
        (
            "What was the surprise?",
            f"The surprise was that there was no {worry.label} at all. It was only {source.reveal}, which looked frightening only because the room was dark."
        )
    )
    end_answer = f"{helper.label_word.capitalize()} used {aid.label} and stayed with {child.label} until the room felt kind again."
    if bedtime_friend:
        end_answer += f" At the end, {child.label} cuddled {bedtime_friend} and went back to sleep."
    else:
        end_answer += f" At the end, {child.label} snuggled under the blanket and went back to sleep."
    qas.append(("How did the story end?", end_answer))
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    aid = f["aid_cfg"]
    source = f["source_cfg"]
    worry = f["worry_cfg"]
    for tag in aid.tags:
        if tag in KNOWLEDGE:
            tags.add(tag)
    for tag in source.tags:
        if tag in KNOWLEDGE:
            tags.add(tag)
    for tag in worry.tags:
        if tag in KNOWLEDGE:
            tags.add(tag)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        bedroom="moon",
        source="branch",
        worry="dragon",
        aid="lantern",
        child_name="Mina",
        child_type="girl",
        helper_type="mother",
        trait="careful",
        bedtime_friend="a rabbit doll",
    ),
    StoryParams(
        bedroom="ocean",
        source="mobile",
        worry="ghost",
        aid="nightlight",
        child_name="Owen",
        child_type="boy",
        helper_type="father",
        trait="curious",
        bedtime_friend="a knitted whale",
    ),
    StoryParams(
        bedroom="forest",
        source="laundry",
        worry="giant",
        aid="flashlight",
        child_name="Lila",
        child_type="girl",
        helper_type="grandmother",
        trait="thoughtful",
        bedtime_friend="a plush fox",
    ),
    StoryParams(
        bedroom="moon",
        source="kitten",
        worry="ghost",
        aid="flashlight",
        child_name="Finn",
        child_type="boy",
        helper_type="father",
        trait="bold",
        bedtime_friend="a small bear",
    ),
]


def explain_rejection(source: Source, worry: Worry) -> str:
    return (
        f"(No story: {source.label} is not a good match for the fear of {worry.label}. "
        f"This world only tells bedtime worries that a child might honestly imagine from that sound and shape.)"
    )


ASP_RULES = r"""
good_aid(A) :- aid(A), power(A, P), P >= 1.
valid(B, S, W) :- bedroom(B), source(S), worry(W), plausible(S, W), good_aid(_).

quick_help :- chosen_trait(T), cautious(T).
peek_then_help :- chosen_trait(T), bold(T).
outcome(quick_help) :- quick_help.
outcome(peek_then_help) :- peek_then_help.

#show valid/3.
#show good_aid/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bedroom_id in BEDROOMS:
        lines.append(asp.fact("bedroom", bedroom_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for worry_id in sorted(source.plausible_worries):
            lines.append(asp.fact("plausible", source_id, worry_id))
    for worry_id in WORRIES:
        lines.append(asp.fact("worry", worry_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("power", aid_id, aid.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious", trait))
    for trait in sorted(BOLD_TRAITS):
        lines.append(asp.fact("bold", trait))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_good_aids() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(a for (a,) in asp.atoms(model, "good_aid"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(asp_program(extra=asp.fact("chosen_trait", params.trait)))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_aids = {aid.id for aid in best_aids()}
    clingo_aids = set(asp_good_aids())
    if py_aids == clingo_aids:
        print(f"OK: good aids match ({sorted(py_aids)}).")
    else:
        rc = 1
        print(f"MISMATCH in good aids: clingo={sorted(clingo_aids)} python={sorted(py_aids)}")

    cases = list(CURATED)
    for seed in range(50):
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=False, qa=True)
        finally:
            sys.stdout = old
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a mysterious night sound, an inner worry, and a gentle surprise."
    )
    ap.add_argument("--bedroom", choices=BEDROOMS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.worry:
        source = SOURCES[args.source]
        worry = WORRIES[args.worry]
        if not worry_fits(source, worry):
            raise StoryError(explain_rejection(source, worry))

    combos = [
        c for c in valid_combos()
        if (args.bedroom is None or c[0] == args.bedroom)
        and (args.source is None or c[1] == args.source)
        and (args.worry is None or c[2] == args.worry)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    bedroom, source, worry = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    bedtime_friend = rng.choice(FRIENDS + ["", ""])
    return StoryParams(
        bedroom=bedroom,
        source=source,
        worry=worry,
        aid=aid,
        child_name=child_name,
        child_type=child_type,
        helper_type=helper_type,
        trait=trait,
        bedtime_friend=bedtime_friend,
    )


def generate(params: StoryParams) -> StorySample:
    if params.bedroom not in BEDROOMS:
        raise StoryError(f"(Unknown bedroom: {params.bedroom})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.worry not in WORRIES:
        raise StoryError(f"(Unknown worry: {params.worry})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    source = SOURCES[params.source]
    worry = WORRIES[params.worry]
    if not worry_fits(source, worry):
        raise StoryError(explain_rejection(source, worry))
    if params.trait not in set(TRAITS):
        raise StoryError(f"(Unknown trait: {params.trait})")

    world = tell(
        bedroom=BEDROOMS[params.bedroom],
        source=source,
        worry=worry,
        aid=AIDS[params.aid],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_type=params.helper_type,
        trait=params.trait,
        bedtime_friend=params.bedtime_friend,
    )
    story_text = world.render().replace("child", params.child_name)
    story_text = story_text.replace("helper", world.facts["helper"].label_word.capitalize(), 1)
    story_text = story_text.replace("helper", world.facts["helper"].label_word)
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        aids = asp_good_aids()
        print(f"good aids: {', '.join(aids)}\n")
        print(f"{len(combos)} compatible (bedroom, source, worry) combos:\n")
        for bedroom, source, worry in combos:
            print(f"  {bedroom:8} {source:8} {worry}")
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
            header = f"### {p.child_name}: {p.source} -> {p.worry} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
