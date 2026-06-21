#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rile_reconciliation_curiosity_comedy.py
==================================================================

A standalone storyworld about a funny household mystery: two children hear a
strange noise, one child tries to rile the other with silly monster talk, and
their curiosity leads them to the real answer. The turn is comic rather than
dangerous, and the ending is a clear reconciliation.

The world model tracks simple physical meters (noise, wobble, found) and
emotional memes (curiosity, worry, mischief, hurt, apology, trust, joy). The
story text is rendered from those changing states rather than from one frozen
template.

Run it
------
python storyworlds/worlds/gpt-5.4/rile_reconciliation_curiosity_comedy.py
python storyworlds/worlds/gpt-5.4/rile_reconciliation_curiosity_comedy.py --nook toy_chest --source windup_duck
python storyworlds/worlds/gpt-5.4/rile_reconciliation_curiosity_comedy.py --nook pantry_shelf --method lift_lid
python storyworlds/worlds/gpt-5.4/rile_reconciliation_curiosity_comedy.py --all
python storyworlds/worlds/gpt-5.4/rile_reconciliation_curiosity_comedy.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/rile_reconciliation_curiosity_comedy.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Nook:
    id: str
    label: str
    phrase: str
    room: str
    height: str
    openable: bool
    silly_guess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    noise: str
    reveal: str
    ending_image: str
    allowed_nooks: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    reach: int
    mode: str
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"teaser", "worrier"}]

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


def _r_noise_curiosity(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    if source is None or source.meters["noise"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("curiosity", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["curiosity"] += 1
        out.append("__curious__")
    worrier = world.entities.get("worrier")
    if worrier is not None:
        sig = ("worry", worrier.id)
        if sig not in world.fired:
            world.fired.add(sig)
            worrier.memes["worry"] += 1
    return out


def _r_tease_hurt(world: World) -> list[str]:
    teaser = world.entities.get("teaser")
    worrier = world.entities.get("worrier")
    if teaser is None or worrier is None:
        return []
    if teaser.memes["mischief"] < THRESHOLD or worrier.memes["worry"] < THRESHOLD:
        return []
    sig = ("hurt", teaser.id, worrier.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    worrier.memes["hurt"] += 1
    teaser.memes["conflict"] += 1
    worrier.memes["conflict"] += 1
    return ["__hurt__"]


def _r_apology_repair(world: World) -> list[str]:
    teaser = world.entities.get("teaser")
    worrier = world.entities.get("worrier")
    source = world.entities.get("source")
    if teaser is None or worrier is None or source is None:
        return []
    if teaser.memes["apology"] < THRESHOLD or source.meters["found"] < THRESHOLD:
        return []
    sig = ("repair", teaser.id, worrier.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    teaser.memes["trust"] += 1
    worrier.memes["trust"] += 1
    teaser.memes["joy"] += 1
    worrier.memes["joy"] += 1
    teaser.memes["conflict"] = 0.0
    worrier.memes["conflict"] = 0.0
    worrier.memes["hurt"] = 0.0
    worrier.memes["worry"] = 0.0
    return ["__repair__"]


CAUSAL_RULES = [
    Rule(name="noise_curiosity", tag="emotion", apply=_r_noise_curiosity),
    Rule(name="tease_hurt", tag="social", apply=_r_tease_hurt),
    Rule(name="apology_repair", tag="social", apply=_r_apology_repair),
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
        for sent in produced:
            world.say(sent)
    return produced


def source_fits(nook: Nook, source: Source) -> bool:
    return nook.id in source.allowed_nooks


def method_works(nook: Nook, method: Method) -> bool:
    need = 1 if nook.height == "low" else 2
    return method.reach >= need and (nook.openable or method.mode != "open")


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for nook_id, nook in NOOKS.items():
        for source_id, source in SOURCES.items():
            if not source_fits(nook, source):
                continue
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and method_works(nook, method):
                    combos.append((nook_id, source_id, method_id))
    return sorted(combos)


def explain_combo_rejection(nook: Nook, source: Source) -> str:
    return (
        f"(No story: {source.phrase} does not make sense in {nook.phrase}. "
        f"Pick a source that could reasonably be hidden there.)"
    )


def explain_method_rejection(nook: Nook, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). This world prefers steady, safe "
            f"ways to solve a mystery.)"
        )
    if nook.height == "high" and method.reach < 2:
        return (
            f"(No story: {method.label} cannot reach {nook.phrase}. A high hiding place "
            f"needs a grown-up or another high-reach method.)"
        )
    if not nook.openable and method.mode == "open":
        return (
            f"(No story: {nook.phrase} is not something the children can simply open. "
            f"Choose a method that fits the hiding place.)"
        )
    return "(No story: that method does not fit this hiding place.)"


def predict_resolution(world: World, nook: Nook, method: Method) -> dict:
    sim = world.copy()
    source = sim.get("source")
    if method_works(nook, method):
        source.meters["found"] += 1
        source.meters["noise"] = 0.0
    propagate(sim, narrate=False)
    return {
        "found": source.meters["found"] >= THRESHOLD,
        "conflict": sim.get("teaser").memes["conflict"] + sim.get("worrier").memes["conflict"],
    }


def opening(world: World, teaser: Entity, worrier: Entity, nook: Nook) -> None:
    room = nook.room
    world.say(
        f"One cozy afternoon, {teaser.id} and {worrier.id} were supposed to be putting toys away in the {room}."
    )
    world.say(
        f"Then {nook.phrase} made a funny little bump-bump sound, as if the room had cleared its throat."
    )


def hear_noise(world: World, source_ent: Entity, source: Source, teaser: Entity, worrier: Entity) -> None:
    source_ent.meters["noise"] += 1
    source_ent.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They froze and listened. The sound came again: {source.noise}."
    )
    if teaser.memes["curiosity"] >= THRESHOLD and worrier.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"Now both children were curious, though {worrier.id} looked much less pleased about it."
        )


def tease(world: World, teaser: Entity, worrier: Entity, nook: Nook) -> None:
    teaser.memes["mischief"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{teaser.id} grinned. Sometimes {teaser.pronoun()} liked to rile {worrier.id} with ridiculous guesses."
    )
    world.say(
        f'"Maybe," {teaser.pronoun()} whispered, "it is {nook.silly_guess}."'
    )
    if worrier.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{worrier.id} frowned instead of laughing. The joke had landed like a pebble in a shoe."
        )


def snap_back(world: World, worrier: Entity, teaser: Entity) -> None:
    worrier.memes["bravery"] += 1
    world.say(
        f'"That is not funny," {worrier.id} said. "If you know what it is, just say so."'
    )
    if worrier.memes["conflict"] >= THRESHOLD:
        world.say(
            f"For a moment, the mystery was not the only thing making the room feel tight."
        )


def choose_method(world: World, teaser: Entity, worrier: Entity, parent: Entity, nook: Nook, method: Method) -> None:
    pred = predict_resolution(world, nook, method)
    world.facts["predicted_found"] = pred["found"]
    if method.mode == "parent":
        world.say(
            f"That made {teaser.id}'s grin wilt. Instead of making another joke, {teaser.pronoun()} took a breath and called, "
            f'"{parent.label_word.capitalize()}, can you help us check {nook.phrase}?"'
        )
    else:
        world.say(
            f"Curiosity won over the sulks. Together they decided to {method.text}."
        )


def reveal(world: World, teaser: Entity, worrier: Entity, parent: Entity, nook: Nook, source_ent: Entity,
           source: Source, method: Method) -> None:
    if method.mode == "parent":
        world.say(
            f"{parent.label_word.capitalize()} came over, listened once, and helped them check {nook.phrase}."
        )
    source_ent.meters["found"] += 1
    source_ent.meters["noise"] = 0.0
    source_ent.meters["hidden"] = 0.0
    propagate(world, narrate=False)
    world.say(source.reveal)


def apology(world: World, teaser: Entity, worrier: Entity, source: Source) -> None:
    teaser.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{teaser.id} looked at {worrier.id} and rubbed the back of {teaser.pronoun("possessive")} neck. '
        f'"I was trying to be funny," {teaser.pronoun()} said, "but I made it worse. I am sorry."'
    )
    if worrier.memes["trust"] >= THRESHOLD:
        world.say(
            f'{worrier.id} let out a breath that sounded almost like a laugh. "Next time, just be curious with me," {worrier.pronoun()} said.'
        )


def reconcile(world: World, teaser: Entity, worrier: Entity, source: Source, method: Method) -> None:
    if method.mode == "parent":
        world.say(
            f"Even {parent_phrase(world)} smiled, because the whole mystery had turned out to be much smaller than the teasing."
        )
    world.say(
        f"Then both children laughed, this time for the same reason."
    )
    world.say(source.ending_image)


def parent_phrase(world: World) -> str:
    parent = world.facts.get("parent")
    if isinstance(parent, Entity):
        return f"{parent.label_word}"
    return "the grown-up"


def tell(nook: Nook, source: Source, method: Method, teaser_name: str, teaser_gender: str,
         worrier_name: str, worrier_gender: str, parent_type: str, bond: str) -> World:
    world = World()
    teaser = world.add(Entity(
        id=teaser_name,
        kind="character",
        type=teaser_gender,
        role="teaser",
        attrs={"bond": bond},
    ))
    worrier = world.add(Entity(
        id=worrier_name,
        kind="character",
        type=worrier_gender,
        role="worrier",
        attrs={"bond": bond},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    source_ent = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source.label,
        phrase=source.phrase,
        tags=set(source.tags),
    ))
    world.add(Entity(
        id="nook",
        kind="thing",
        type="nook",
        label=nook.label,
        phrase=nook.phrase,
        tags=set(nook.tags),
    ))

    opening(world, teaser, worrier, nook)
    hear_noise(world, source_ent, source, teaser, worrier)

    world.para()
    tease(world, teaser, worrier, nook)
    snap_back(world, worrier, teaser)

    world.para()
    choose_method(world, teaser, worrier, parent, nook, method)
    reveal(world, teaser, worrier, parent, nook, source_ent, source, method)

    world.para()
    apology(world, teaser, worrier, source)
    reconcile(world, teaser, worrier, source, method)

    outcome = "parent_helped" if method.mode == "parent" else "found_together"
    world.facts.update(
        teaser=teaser,
        worrier=worrier,
        parent=parent,
        nook=nook,
        source_cfg=source,
        source=source_ent,
        method=method,
        bond=bond,
        outcome=outcome,
        repaired=teaser.memes["trust"] >= THRESHOLD and worrier.memes["trust"] >= THRESHOLD,
    )
    return world


NOOKS = {
    "toy_chest": Nook(
        id="toy_chest",
        label="toy chest",
        phrase="the old toy chest by the window",
        room="playroom",
        height="low",
        openable=True,
        silly_guess="a pirate captain who got stuck under the blocks",
        tags={"chest", "indoors"},
    ),
    "laundry_basket": Nook(
        id="laundry_basket",
        label="laundry basket",
        phrase="the tall laundry basket in the hall",
        room="hall",
        height="low",
        openable=True,
        silly_guess="a sock dragon learning to roar",
        tags={"laundry", "indoors"},
    ),
    "pantry_shelf": Nook(
        id="pantry_shelf",
        label="pantry shelf",
        phrase="the top pantry shelf above the cereal boxes",
        room="kitchen",
        height="high",
        openable=False,
        silly_guess="a biscuit goblin with crunchy feet",
        tags={"kitchen", "shelf"},
    ),
}

SOURCES = {
    "kitten": Source(
        id="kitten",
        label="kitten",
        phrase="a tiny kitten",
        noise="mew-scritch, mew-scritch",
        reveal="Out popped a tiny kitten, batting at a loose ribbon as if it had planned the whole performance.",
        ending_image="Soon the mystery-maker was purring in their laps, and the children were taking turns tickling the ribbon instead of each other.",
        allowed_nooks={"laundry_basket", "toy_chest"},
        tags={"kitten", "pet", "sound"},
    ),
    "windup_duck": Source(
        id="windup_duck",
        label="wind-up duck",
        phrase="a wind-up duck",
        noise="quack-click, quack-click",
        reveal="Inside was a wind-up duck waddling in stubborn little circles and bumping the wall every few seconds.",
        ending_image="The duck kept quack-clicking across the floor while both children chased it in one giggling zigzag.",
        allowed_nooks={"toy_chest", "pantry_shelf"},
        tags={"toy", "sound", "duck"},
    ),
    "rolling_apple": Source(
        id="rolling_apple",
        label="apple",
        phrase="a runaway apple",
        noise="thup-roll, thup-roll",
        reveal="There, tucked behind a bag of oats, was a shiny apple rolling back and forth whenever the shelf trembled.",
        ending_image="In the end they carried the apple down together, still smiling at how such a round little thing had caused such a grand little mystery.",
        allowed_nooks={"pantry_shelf"},
        tags={"apple", "kitchen", "sound"},
    ),
}

METHODS = {
    "listen_close": Method(
        id="listen_close",
        label="listen close and peek together",
        sense=3,
        reach=1,
        mode="peek",
        text="kneel beside it, listen close, and peek together",
        qa_text="They knelt beside the hiding place, listened carefully, and peeked together",
        tags={"listen", "curiosity"},
    ),
    "lift_lid": Method(
        id="lift_lid",
        label="lift the lid together",
        sense=3,
        reach=1,
        mode="open",
        text="lift the lid together",
        qa_text="They opened the hiding place together",
        tags={"open", "curiosity"},
    ),
    "ask_parent": Method(
        id="ask_parent",
        label="ask a grown-up for help",
        sense=3,
        reach=2,
        mode="parent",
        text="ask a grown-up for help",
        qa_text="They asked their grown-up to help check the hiding place",
        tags={"adult_help", "curiosity"},
    ),
    "wobble_chair": Method(
        id="wobble_chair",
        label="drag over a wobbly chair",
        sense=1,
        reach=2,
        mode="climb",
        text="drag over a wobbly chair and climb up alone",
        qa_text="They climbed on a wobbly chair",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]


@dataclass
class StoryParams:
    nook: str
    source: str
    method: str
    teaser: str
    teaser_gender: str
    worrier: str
    worrier_gender: str
    parent: str
    bond: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "sound": [
        (
            "How can a small thing make a big mystery?",
            "A tiny sound can seem huge when you do not know what is making it. Your brain starts guessing before your eyes can check."
        )
    ],
    "curiosity": [
        (
            "What does curiosity mean?",
            "Curiosity means wanting to find out more about something. It can help you solve a mystery when you slow down and look carefully."
        )
    ],
    "adult_help": [
        (
            "When should children ask a grown-up for help with a mystery?",
            "Children should ask a grown-up when something is too high, too heavy, or feels unsafe. Asking for help is a smart way to stay curious safely."
        )
    ],
    "kitten": [
        (
            "Why do kittens make funny little noises?",
            "Kittens mew and scritch because they are small, lively animals who explore with their paws and voices. Their little sounds can bounce around a room and seem mysterious."
        )
    ],
    "toy": [
        (
            "What is a wind-up toy?",
            "A wind-up toy is a toy that moves after someone turns a little key or knob. It can click, wobble, and bump into things all by itself."
        )
    ],
    "apple": [
        (
            "Why can an apple roll away?",
            "An apple is round, so it can roll if a shelf tips or the surface shakes. Round things like to keep moving."
        )
    ],
    "open": [
        (
            "Why is it helpful to open something slowly when you are curious?",
            "Opening something slowly helps you see clearly and keeps the surprise from getting too wild. Careful looking is better than grabbing in a rush."
        )
    ],
    "listen": [
        (
            "How can listening help solve a mystery?",
            "Listening tells you where a sound is coming from and what kind of thing might be making it. Your ears can give clues before your eyes do."
        )
    ],
}

KNOWLEDGE_ORDER = ["curiosity", "sound", "listen", "open", "adult_help", "kitten", "toy", "apple"]


def pair_noun(teaser: Entity, worrier: Entity, bond: str) -> str:
    if bond == "siblings":
        if teaser.type == "boy" and worrier.type == "boy":
            return "two brothers"
        if teaser.type == "girl" and worrier.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    teaser = f["teaser"]
    worrier = f["worrier"]
    nook = f["nook"]
    source = f["source_cfg"]
    method = f["method"]
    return [
        f'Write a funny story for a 3-to-5-year-old that includes the word "rile" and begins with a strange noise coming from {nook.phrase}.',
        f"Tell a comedy where {teaser.id} teases {worrier.id} about a silly mystery, but curiosity leads them to discover {source.phrase} and make up afterward.",
        f"Write a short reconciliation story in which two children get cross for a moment, then {method.label} and end up laughing together."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    teaser = f["teaser"]
    worrier = f["worrier"]
    parent = f["parent"]
    nook = f["nook"]
    source = f["source_cfg"]
    method = f["method"]
    pair = pair_noun(teaser, worrier, f["bond"])
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {teaser.id} and {worrier.id}. They hear a mysterious noise and have to choose whether to tease or solve it together."
        ),
        (
            f"What was making the strange sound?",
            f"It was {source.phrase}. The funny noise seemed bigger than it really was because the children could hear it before they could see it."
        ),
        (
            f"How did {teaser.id} rile {worrier.id}?",
            f"{teaser.id} tried to rile {worrier.id} by whispering a ridiculous guess about {nook.phrase} instead of helping right away. The teasing made {worrier.id} feel more worried and a little hurt."
        ),
        (
            "Why did the children stop arguing?",
            f"They stopped arguing because curiosity became more useful than the joke. Once they chose to check the hiding place, the mystery started to feel manageable."
        ),
    ]
    if f["outcome"] == "parent_helped":
        out.append(
            (
                f"How did they find out what was really there?",
                f"They asked {parent.label_word} for help, and together they checked {nook.phrase}. That was the sensible choice because the hiding place was too high for the children to reach safely."
            )
        )
    else:
        out.append(
            (
                f"How did they solve the mystery themselves?",
                f"{method.qa_text}. Working side by side turned the moment from a quarrel into a little investigation."
            )
        )
    out.append(
        (
            f"How did {teaser.id} and {worrier.id} reconcile?",
            f"{teaser.id} apologized for trying to be funny in the wrong way, and {worrier.id} accepted it. They ended by laughing together because the real answer was harmless and silly."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"curiosity", "sound"} | set(f["method"].tags) | set(f["source_cfg"].tags)
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
    for e in world.entities.values():
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        nook="toy_chest",
        source="windup_duck",
        method="lift_lid",
        teaser="Noah",
        teaser_gender="boy",
        worrier="Mia",
        worrier_gender="girl",
        parent="mother",
        bond="friends",
    ),
    StoryParams(
        nook="laundry_basket",
        source="kitten",
        method="listen_close",
        teaser="Lily",
        teaser_gender="girl",
        worrier="Ben",
        worrier_gender="boy",
        parent="father",
        bond="siblings",
    ),
    StoryParams(
        nook="pantry_shelf",
        source="rolling_apple",
        method="ask_parent",
        teaser="Sam",
        teaser_gender="boy",
        worrier="Zoe",
        worrier_gender="girl",
        parent="mother",
        bond="siblings",
    ),
    StoryParams(
        nook="pantry_shelf",
        source="windup_duck",
        method="ask_parent",
        teaser="Ella",
        teaser_gender="girl",
        worrier="Tom",
        worrier_gender="boy",
        parent="father",
        bond="friends",
    ),
]


ASP_RULES = r"""
fits(N, S) :- allows(S, N).
sensible(M) :- method(M), sense(M, V), sense_min(Min), V >= Min.

need(N, 1) :- nook(N), height(N, low).
need(N, 2) :- nook(N), height(N, high).

works(N, M) :- method(M), need(N, R), reach(M, RR), RR >= R, mode(M, parent).
works(N, M) :- method(M), need(N, R), reach(M, RR), RR >= R, openable(N), mode(M, open).
works(N, M) :- method(M), need(N, R), reach(M, RR), RR >= R, mode(M, peek).

valid(N, S, M) :- nook(N), source(S), method(M), fits(N, S), sensible(M), works(N, M).

outcome(parent_helped) :- chosen_method(M), mode(M, parent).
outcome(found_together) :- chosen_method(M), not mode(M, parent).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for nook_id, nook in NOOKS.items():
        lines.append(asp.fact("nook", nook_id))
        lines.append(asp.fact("height", nook_id, nook.height))
        if nook.openable:
            lines.append(asp.fact("openable", nook_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for nook_id in sorted(source.allowed_nooks):
            lines.append(asp.fact("allows", source_id, nook_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("reach", method_id, method.reach))
        lines.append(asp.fact("mode", method_id, method.mode))
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
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_method", params.method)
    model = asp.one_model(asp_program(extra, "#show outcome/1.\n#show mode/2."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    method = METHODS[params.method]
    return "parent_helped" if method.mode == "parent" else "found_together"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    with io.StringIO() as buf, redirect_stdout(buf):
        emit(sample, trace=False, qa=True)
        rendered = buf.getvalue()
    if "rile" not in sample.story:
        raise StoryError("Smoke test failed: story missing required seed word.")
    if not rendered.strip():
        raise StoryError("Smoke test failed: emit() produced no output.")


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_sens = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: asp={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a comic mystery, a teasing child, curiosity, and reconciliation."
    )
    ap.add_argument("--nook", choices=NOOKS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--bond", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.nook and args.source:
        nook = NOOKS[args.nook]
        source = SOURCES[args.source]
        if not source_fits(nook, source):
            raise StoryError(explain_combo_rejection(nook, source))
    if args.nook and args.method:
        nook = NOOKS[args.nook]
        method = METHODS[args.method]
        if not method_works(nook, method) or method.sense < SENSE_MIN:
            raise StoryError(explain_method_rejection(nook, method))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(NOOKS[args.nook] if args.nook else next(iter(NOOKS.values())), METHODS[args.method]))

    combos = [
        combo for combo in valid_combos()
        if (args.nook is None or combo[0] == args.nook)
        and (args.source is None or combo[1] == args.source)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    nook_id, source_id, method_id = rng.choice(sorted(combos))
    teaser, teaser_gender = _pick_kid(rng)
    worrier, worrier_gender = _pick_kid(rng, avoid=teaser)
    parent = args.parent or rng.choice(["mother", "father"])
    bond = args.bond or rng.choice(["siblings", "friends"])
    return StoryParams(
        nook=nook_id,
        source=source_id,
        method=method_id,
        teaser=teaser,
        teaser_gender=teaser_gender,
        worrier=worrier,
        worrier_gender=worrier_gender,
        parent=parent,
        bond=bond,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        nook = NOOKS[params.nook]
        source = SOURCES[params.source]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err!s}.)") from err

    if not source_fits(nook, source):
        raise StoryError(explain_combo_rejection(nook, source))
    if method.sense < SENSE_MIN or not method_works(nook, method):
        raise StoryError(explain_method_rejection(nook, method))

    world = tell(
        nook=nook,
        source=source,
        method=method,
        teaser_name=params.teaser,
        teaser_gender=params.teaser_gender,
        worrier_name=params.worrier,
        worrier_gender=params.worrier_gender,
        parent_type=params.parent,
        bond=params.bond,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (nook, source, method) combos:\n")
        for nook, source, method in combos:
            print(f"  {nook:15} {source:12} {method}")
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
            header = f"### {p.teaser} & {p.worrier}: {p.source} in {p.nook} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
