#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gimmick_sound_effects_suspense_friendship_mystery.py
================================================================================

A standalone story world about two friends in a small mystery: a strange sound in
a familiar place seems spooky at first, but turns out to have a simple physical
cause. The engine models fear, trust, clues, and a sensible check that only some
(sound, source, fix) combinations make a plausible mystery.

The world keeps the required child-facing shape:
- a beginning with a shared plan
- a suspenseful middle driven by state and clues
- a friendship turn where the children stay together and investigate safely
- an ending image that proves what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/gimmick_sound_effects_suspense_friendship_mystery.py
    python storyworlds/worlds/gpt-5.4/gimmick_sound_effects_suspense_friendship_mystery.py --place attic --sound thump
    python storyworlds/worlds/gpt-5.4/gimmick_sound_effects_suspense_friendship_mystery.py --source ghost
    python storyworlds/worlds/gpt-5.4/gimmick_sound_effects_suspense_friendship_mystery.py --all
    python storyworlds/worlds/gpt-5.4/gimmick_sound_effects_suspense_friendship_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gimmick_sound_effects_suspense_friendship_mystery.py --verify
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
BRAVE_ENOUGH = 6.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    makes_sound: bool = False
    needs_light: bool = False
    safe_tool: bool = False
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
    phrase: str
    dark_phrase: str
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
class Sound:
    id: str
    noise: str
    line: str
    suspense: str
    needs_movement: bool
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
    type: str
    movable: bool
    can_make: set[str]
    cause_text: str
    reveal_text: str
    friendly_fix: str
    spooky: bool = False
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
    beam: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]

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


def _r_sound_raises_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["sound"] < THRESHOLD:
        return out
    sig = ("fear",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__fear__")
    return out


def _r_friendship_steadies(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("leader")
    b = world.get("friend")
    if a.memes["fear"] < THRESHOLD and b.memes["fear"] < THRESHOLD:
        return out
    if a.memes["together"] < THRESHOLD or b.memes["together"] < THRESHOLD:
        return out
    sig = ("steady",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in (a, b):
        kid.memes["courage"] += 1
        kid.memes["panic"] = 0.0
    out.append("__steady__")
    return out


def _r_light_reveals_clue(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    tool = world.get("tool")
    if room.meters["dark"] < THRESHOLD or tool.meters["on"] < THRESHOLD:
        return out
    sig = ("clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["visible"] += 1
    world.get("source").meters["noticed"] += 1
    out.append("__clue__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sound_raises_fear", tag="emotional", apply=_r_sound_raises_fear),
    Rule(name="friendship_steadies", tag="social", apply=_r_friendship_steadies),
    Rule(name="light_reveals_clue", tag="physical", apply=_r_light_reveals_clue),
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


def mystery_possible(sound: Sound, source: Source) -> bool:
    if source.id == "ghost":
        return False
    if sound.id not in source.can_make:
        return False
    if sound.needs_movement and not source.movable:
        return False
    return True


def sensible_tools() -> list[Tool]:
    return list(TOOLS.values())


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for sound_id, sound in SOUNDS.items():
            for source_id, source in SOURCES.items():
                if mystery_possible(sound, source):
                    combos.append((place_id, sound_id, source_id))
    return combos


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("leader").memes["together"] = 1
    sim.get("friend").memes["together"] = 1
    sim.get("tool").meters["on"] = 1
    propagate(sim, narrate=False)
    return {
        "visible": sim.get("room").meters["visible"] >= THRESHOLD,
        "noticed": sim.get("source").meters["noticed"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, place: Place) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"After supper, {a.id} and {b.id} made up a tiny mystery club and tiptoed toward {place.phrase}."
    )
    world.say(
        f"They had a little notebook, a pencil, and one silly gimmick: whenever they found a clue, "
        f"they whispered, \"Mystery detectives, ready!\" and tapped the notebook twice."
    )


def enter_place(world: World, a: Entity, b: Entity, place: Place) -> None:
    room = world.get("room")
    room.meters["dark"] = 1
    world.say(
        f"{place.label.capitalize()} felt still and shadowy. {place.dark_phrase}"
    )
    world.say(
        f"{a.id} squeezed the notebook. {b.id} listened so hard that even the quiet seemed to be waiting."
    )


def sound_happens(world: World, sound: Sound) -> None:
    world.get("room").meters["sound"] = 1
    world.facts["heard_sound"] = sound.id
    propagate(world, narrate=False)
    world.say(f"{sound.noise} {sound.line}")
    world.say(sound.suspense)


def hold_together(world: World, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["together"] = 1
    propagate(world, narrate=False)
    world.say(
        f"{b.id} slid a little closer to {a.id}. \"Let's stay together,\" {b.pronoun()} whispered."
    )
    world.say(
        f'"Together," {a.id} whispered back. Saying it made the dark feel smaller.'
    )


def use_light(world: World, a: Entity, tool: Tool, place: Place) -> None:
    world.get("tool").meters["on"] = 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} clicked on {tool.phrase}. {tool.beam} swept over {place.hiding_spot}."
    )


def inspect(world: World, a: Entity, b: Entity, source: Source) -> None:
    source_ent = world.get("source")
    source_ent.meters["checked"] += 1
    source_ent.memes["mystery"] = 0.0
    world.say(source.reveal_text)
    world.say(
        f"{a.id} and {b.id} let out the breath they had been holding. The mystery was not a monster at all."
    )


def fix_problem(world: World, a: Entity, b: Entity, source: Source) -> None:
    room = world.get("room")
    source_ent = world.get("source")
    source_ent.meters["secured"] += 1
    room.meters["sound"] = 0.0
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["friendship"] += 1
    world.say(source.friendly_fix)
    world.say(
        f"Then {a.id} grinned at {b.id}, and {b.id} grinned back. Their club felt less like a game and more like real friendship."
    )


def end_scene(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    world.say(
        f'On the way back downstairs, they did their notebook tap again and whispered, "Mystery detectives, ready!"'
    )
    world.say(
        f"This time they were laughing softly, with {tool.label} shining ahead of them and no spooky sound following behind."
    )


PLACES = {
    "attic": Place(
        id="attic",
        label="the attic",
        phrase="the attic stairs",
        dark_phrase="The slanted ceiling made the corners look deeper than they really were.",
        hiding_spot="an old trunk and a stack of boxes",
        tags={"attic", "dark"},
    ),
    "hallway": Place(
        id="hallway",
        label="the hallway closet",
        phrase="the hallway closet",
        dark_phrase="Coats hung in a row like sleepy people standing very still.",
        hiding_spot="the shoe shelf and the umbrella stand",
        tags={"closet", "dark"},
    ),
    "shed": Place(
        id="shed",
        label="the garden shed",
        phrase="the garden shed",
        dark_phrase="Rainy-smelling wood and hanging tools made every little shadow look important.",
        hiding_spot="the back wall near the rake and seed bags",
        tags={"shed", "dark"},
    ),
}

SOUNDS = {
    "thump": Sound(
        id="thump",
        noise="THUMP! THUMP!",
        line="Something bumped from the dark, then all was quiet again.",
        suspense="For a second, neither friend moved.",
        needs_movement=True,
        tags={"thump", "sound"},
    ),
    "scritch": Sound(
        id="scritch",
        noise="Scritch-scritch!",
        line="A small scratchy sound came from behind the clutter.",
        suspense="It was the sort of sound that made imaginations run faster than feet.",
        needs_movement=True,
        tags={"scratch", "sound"},
    ),
    "clink": Sound(
        id="clink",
        noise="Clink... clink...",
        line="A faint tapping sound came and stopped, came and stopped.",
        suspense="The waiting between the little sounds felt longer than the sounds themselves.",
        needs_movement=True,
        tags={"clink", "sound"},
    ),
}

SOURCES = {
    "loose_window": Source(
        id="loose_window",
        label="loose window latch",
        phrase="a loose window latch",
        type="thing",
        movable=True,
        can_make={"clink"},
        cause_text="the wind nudged a loose latch",
        reveal_text="There, near the frame, a loose window latch was tapping gently whenever the wind pushed it.",
        friendly_fix="They called for a grown-up, who turned the latch tight and showed them how the wind had made the clinking sound.",
        tags={"window", "wind", "call_adult"},
    ),
    "toy_wagon": Source(
        id="toy_wagon",
        label="toy wagon",
        phrase="a toy wagon with one wiggly wheel",
        type="thing",
        movable=True,
        can_make={"thump"},
        cause_text="a wheel bumped against a box",
        reveal_text="Behind the boxes sat a toy wagon. One wiggly wheel had rolled just enough to bump the side of a trunk.",
        friendly_fix="Together they pulled the wagon away from the boxes and set a folded cloth behind its wheel so it would stay still.",
        tags={"toy", "wheel"},
    ),
    "tree_branch": Source(
        id="tree_branch",
        label="tree branch",
        phrase="a tree branch brushing the wall",
        type="thing",
        movable=True,
        can_make={"scritch"},
        cause_text="a branch brushed and scratched outside",
        reveal_text="At the wall they found the answer: a tree branch outside was brushing the boards and making the scratchy sound.",
        friendly_fix="They fetched a grown-up, who tied the branch back with garden string so it would stop scraping in the wind.",
        tags={"tree", "wind", "call_adult"},
    ),
    "ghost": Source(
        id="ghost",
        label="ghost",
        phrase="a ghost",
        type="thing",
        movable=True,
        can_make=set(),
        cause_text="nothing sensible",
        reveal_text="",
        friendly_fix="",
        spooky=True,
        tags={"ghost"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="the flashlight",
        beam="A bright circle of light",
        tags={"flashlight", "light"},
    ),
    "lantern": Tool(
        id="lantern",
        label="camp lantern",
        phrase="the little camp lantern",
        beam="A warm yellow glow",
        tags={"lantern", "light"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "curious", "steady", "thoughtful", "kind", "brave"]


@dataclass
class StoryParams:
    place: str
    sound: str
    source: str
    tool: str
    leader: str
    leader_gender: str
    friend: str
    friend_gender: str
    parent: str
    leader_trait: str
    friend_trait: str
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
    "sound": [
        (
            "Why can a strange sound feel scary in the dark?",
            "In the dark, you cannot see what made the sound, so your mind may imagine something bigger or stranger than the real cause. Seeing the place clearly often makes the fear shrink."
        )
    ],
    "flashlight": [
        (
            "What does a flashlight help you do?",
            "A flashlight helps you see into dark places safely. It lets you look for the real cause instead of guessing."
        )
    ],
    "lantern": [
        (
            "What is a lantern good for?",
            "A lantern gives steady light so people can see around them. Light can turn a spooky mystery into an ordinary problem."
        )
    ],
    "wind": [
        (
            "How can wind make sounds?",
            "Wind can push, tap, or rub things together. That can make clinks, thumps, or scratchy noises."
        )
    ],
    "friendship": [
        (
            "How can a friend help when something feels scary?",
            "A friend can stay close, speak calmly, and help you think. Being together can make it easier to act bravely."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something you do not understand yet, like a strange sound or a missing clue. You solve it by looking carefully and finding the real answer."
        )
    ],
    "call_adult": [
        (
            "When should children call a grown-up during a mystery?",
            "Children should call a grown-up when something needs fixing or feels unsafe. Asking for help is a smart part of solving problems."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "sound", "friendship", "flashlight", "lantern", "wind", "call_adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["leader"]
    b = f["friend"]
    sound = f["sound_cfg"]
    place = f["place_cfg"]
    source = f["source_cfg"]
    return [
        'Write a short child-friendly mystery story that includes the word "gimmick", uses sound effects, and ends with friendship making the dark less scary.',
        f"Tell a suspenseful story where {a.id} and {b.id} hear {sound.noise.lower()} in {place.label} and work together to discover the real cause.",
        f"Write a simple mystery in which two friends think something spooky is hiding, but they find out it was really {source.phrase}."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["leader"]
    b = f["friend"]
    place = f["place_cfg"]
    sound = f["sound_cfg"]
    source = f["source_cfg"]
    tool = f["tool_cfg"]
    parent = f["parent"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, who made a tiny mystery club together. Their friendship matters because they stay together when the place feels spooky."
        ),
        (
            "What was their gimmick?",
            'Their gimmick was tapping their notebook twice and whispering, "Mystery detectives, ready!" whenever they found a clue. It started as a playful club habit, but later it helped them feel brave together.'
        ),
        (
            f"What made the mystery begin in {place.label}?",
            f"The mystery began when they heard {sound.noise} in the dark. Because they could hear the sound before they could see its cause, the place suddenly felt much more suspenseful."
        ),
        (
            f"Why did {a.id} and {b.id} stay together instead of running away?",
            f"They stayed together because each friend helped the other feel steadier. Saying \"together\" out loud made the dark feel smaller and gave them courage to look carefully."
        ),
        (
            f"How did they solve the mystery?",
            f"They used {tool.phrase} to see into the dark and inspect the hiding spot. Once the light showed the clue, they could tell that the sound came from {source.phrase} instead of anything spooky."
        ),
    ]
    if source.id in {"loose_window", "tree_branch"}:
        qa.append(
            (
                "Why did they get a grown-up at the end?",
                f"They asked {parent.label_word} for help because the real cause needed fixing, not just finding. That was the sensible next step after they solved the mystery."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the sound fixed and the two friends laughing softly instead of feeling afraid. The shining light and their shared grin showed that the mystery was over."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"mystery", "sound", "friendship"}
    tool = f["tool_cfg"]
    if tool.id == "flashlight":
        tags.add("flashlight")
    if tool.id == "lantern":
        tags.add("lantern")
    if "wind" in f["source_cfg"].tags:
        tags.add("wind")
    if "call_adult" in f["source_cfg"].tags:
        tags.add("call_adult")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, value in (
            ("movable", ent.movable),
            ("makes_sound", ent.makes_sound),
            ("needs_light", ent.needs_light),
            ("safe_tool", ent.safe_tool),
        ) if value]
        if flags:
            bits.append(f"flags={flags}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def explain_rejection(sound: Sound, source: Source) -> str:
    if source.id == "ghost":
        return "(No story: this world refuses truly supernatural answers. The mystery must resolve to an ordinary cause a child could understand.)"
    if sound.id not in source.can_make:
        return f"(No story: {source.phrase} does not make a plausible {sound.id} sound here.)"
    if sound.needs_movement and not source.movable:
        return f"(No story: {sound.id} needs something that can move or tap, but {source.phrase} would stay still.)"
    return "(No story: this mystery does not have a sensible solution.)"


def tell(
    place: Place,
    sound: Sound,
    source: Source,
    tool: Tool,
    leader_name: str = "Lily",
    leader_gender: str = "girl",
    friend_name: str = "Tom",
    friend_gender: str = "boy",
    parent_type: str = "mother",
    leader_trait: str = "curious",
    friend_trait: str = "kind",
) -> World:
    world = World()
    leader = world.add(Entity(
        id="leader",
        kind="character",
        type=leader_gender,
        label=leader_name,
        traits=[leader_trait],
        role="leader",
        attrs={"name": leader_name},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        traits=[friend_trait],
        role="friend",
        attrs={"name": friend_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=place.label,
        needs_light=True,
    ))
    source_ent = world.add(Entity(
        id="source",
        type=source.type,
        label=source.label,
        movable=source.movable,
        makes_sound=True,
    ))
    tool_ent = world.add(Entity(
        id="tool",
        type="tool",
        label=tool.label,
        safe_tool=True,
    ))

    for ent in (leader, friend, parent, room, source_ent, tool_ent):
        ent.meters["dummy"] = 0.0
        ent.memes["dummy"] = 0.0
    room.meters["sound"] = 0.0
    room.meters["dark"] = 0.0
    room.meters["visible"] = 0.0
    source_ent.meters["noticed"] = 0.0
    source_ent.meters["checked"] = 0.0
    source_ent.meters["secured"] = 0.0
    tool_ent.meters["on"] = 0.0
    leader.memes["fear"] = 0.0
    friend.memes["fear"] = 0.0
    leader.memes["together"] = 0.0
    friend.memes["together"] = 0.0
    leader.memes["courage"] = 0.0
    friend.memes["courage"] = 0.0
    leader.memes["panic"] = 0.0
    friend.memes["panic"] = 0.0

    introduce(world, leader, friend, place)
    enter_place(world, leader, friend, place)

    world.para()
    sound_happens(world, sound)
    hold_together(world, leader, friend)

    prediction = predict_reveal(world)
    world.facts["prediction_visible"] = prediction["visible"]

    world.say(
        f'{leader.label} swallowed and whispered, "Maybe it only sounds spooky because we cannot see yet."'
    )
    use_light(world, leader, tool, place)

    world.para()
    inspect(world, leader, friend, source)
    fix_problem(world, leader, friend, source)
    end_scene(world, leader, friend, tool)

    world.facts.update(
        leader=leader,
        friend=friend,
        parent=parent,
        place_cfg=place,
        sound_cfg=sound,
        source_cfg=source,
        tool_cfg=tool,
        solved=source_ent.meters["checked"] >= THRESHOLD,
        secured=source_ent.meters["secured"] >= THRESHOLD,
        friendship_helped=leader.memes["friendship"] >= THRESHOLD and friend.memes["friendship"] >= THRESHOLD,
    )
    return world


CURATED = [
    StoryParams(
        place="attic",
        sound="thump",
        source="toy_wagon",
        tool="flashlight",
        leader="Lily",
        leader_gender="girl",
        friend="Ben",
        friend_gender="boy",
        parent="mother",
        leader_trait="curious",
        friend_trait="kind",
    ),
    StoryParams(
        place="hallway",
        sound="clink",
        source="loose_window",
        tool="lantern",
        leader="Sam",
        leader_gender="boy",
        friend="Mia",
        friend_gender="girl",
        parent="father",
        leader_trait="steady",
        friend_trait="thoughtful",
    ),
    StoryParams(
        place="shed",
        sound="scritch",
        source="tree_branch",
        tool="flashlight",
        leader="Nora",
        leader_gender="girl",
        friend="Theo",
        friend_gender="boy",
        parent="mother",
        leader_trait="careful",
        friend_trait="brave",
    ),
]


ASP_RULES = r"""
mystery_possible(S, Src) :- sound(S), source(Src), can_make(Src, S), not ghost(Src).
mystery_possible(S, Src) :- sound(S), source(Src), can_make(Src, S), needs_movement(S), movable(Src), not ghost(Src).

valid(P, S, Src) :- place(P), sound(S), source(Src), mystery_possible(S, Src).

shown_outcome(solved) :- chosen_place(_), chosen_sound(S), chosen_source(Src), valid(_, S, Src).
#show valid/3.
#show shown_outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for sound_id, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sound_id))
        if sound.needs_movement:
            lines.append(asp.fact("needs_movement", sound_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        if source.spooky:
            lines.append(asp.fact("ghost", source_id))
        if source.movable:
            lines.append(asp.fact("movable", source_id))
        for sound_id in sorted(source.can_make):
            lines.append(asp.fact("can_make", source_id, sound_id))
    for tool_id in TOOLS:
        lines.append(asp.fact("tool", tool_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    checked = 0
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            generate(params)
            checked += 1
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    if rc == 0:
        print(f"OK: random generation smoke-tested on {checked} seeds.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a spooky sound, a sensible mystery, and friendship."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mysteries from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source:
        src = SOURCES[args.source]
        snd = SOUNDS[args.sound] if args.sound else next(iter(SOUNDS.values()))
        if args.sound and not mystery_possible(snd, src):
            raise StoryError(explain_rejection(snd, src))
        if src.id == "ghost":
            raise StoryError(explain_rejection(snd, src))

    if args.sound and args.source:
        snd = SOUNDS[args.sound]
        src = SOURCES[args.source]
        if not mystery_possible(snd, src):
            raise StoryError(explain_rejection(snd, src))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sound is None or combo[1] == args.sound)
        and (args.source is None or combo[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, sound, source = rng.choice(sorted(combos))
    tool = args.tool or rng.choice(sorted(TOOLS))
    leader, leader_gender = _pick_name(rng)
    friend, friend_gender = _pick_name(rng, avoid=leader)
    parent = args.parent or rng.choice(["mother", "father"])
    leader_trait = rng.choice(TRAITS)
    friend_trait = rng.choice([t for t in TRAITS if t != leader_trait] or TRAITS)
    return StoryParams(
        place=place,
        sound=sound,
        source=source,
        tool=tool,
        leader=leader,
        leader_gender=leader_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        leader_trait=leader_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        sound = SOUNDS[params.sound]
        source = SOURCES[params.source]
        tool = TOOLS[params.tool]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not mystery_possible(sound, source):
        raise StoryError(explain_rejection(sound, source))

    world = tell(
        place=place,
        sound=sound,
        source=source,
        tool=tool,
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        leader_trait=params.leader_trait,
        friend_trait=params.friend_trait,
    )

    story = world.render().replace("leader", params.leader).replace("friend", params.friend)
    story = story.replace(world.get("leader").label, params.leader).replace(world.get("friend").label, params.friend)

    # tell() stores names in labels, but dialogue lines use the stored labels directly.
    story = story.replace("parent", world.get("parent").label_word)

    # Clean substitution from internal entity labels to chosen names.
    story = story.replace("Lily", params.leader) if params.leader != "Lily" else story

    # Safer final story from direct world text with explicit names.
    story = (
        world.render()
        .replace(world.get("leader").label, params.leader)
        .replace(world.get("friend").label, params.friend)
    )

    # Rebuild from paragraphs with explicit names already present in entity labels.
    # Since labels carry names, the render above is usually already correct.
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sound, source) combos:\n")
        for place, sound, source in combos:
            print(f"  {place:8} {sound:8} {source}")
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
            header = f"### {p.leader} & {p.friend}: {p.sound} in {p.place} ({p.source})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
