#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stegosaurus_chipmunk_hoist_storage_closet_friendship_sound.py
=========================================================================================

A standalone story world for a small adventure in a storage closet.

Seed requirements rebuilt as a simulated domain:
- words: stegosaurus, chipmunk, hoist
- setting: storage closet
- features: Friendship, Sound Effects
- style: Adventure

Premise
-------
Two friends turn a storage closet into an expedition base. One beloved toy ends up
stranded on a shelf while the other waits below. A little hand hoist is the honest
tool in the room: when one child cannot manage alone, the other joins in, and the
rescue becomes a friendship moment instead of just a retrieval.

Reasonableness constraint
-------------------------
Not every hoist can rescue every toy from every shelf. The world model checks:
- the hoist must reach the chosen shelf
- the hoist must safely hold the toy's weight
- the hoist must have enough lifting power, at least when both friends work together

So the story never asks a flimsy bucket hoist to lift a heavy stegosaurus from a
high shelf. Invalid explicit choices raise StoryError with a clear explanation.

Run it
------
    python storyworlds/worlds/gpt-5.4/stegosaurus_chipmunk_hoist_storage_closet_friendship_sound.py
    python storyworlds/worlds/gpt-5.4/stegosaurus_chipmunk_hoist_storage_closet_friendship_sound.py --cargo chipmunk --hoist basket --shelf high
    python storyworlds/worlds/gpt-5.4/stegosaurus_chipmunk_hoist_storage_closet_friendship_sound.py --cargo stegosaurus --hoist basket
    python storyworlds/worlds/gpt-5.4/stegosaurus_chipmunk_hoist_storage_closet_friendship_sound.py --all
    python storyworlds/worlds/gpt-5.4/stegosaurus_chipmunk_hoist_storage_closet_friendship_sound.py --qa --json
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    weight: int
    call: str
    reunion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shelf:
    id: str
    label: str
    phrase: str
    height: int
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HoistRig:
    id: str
    label: str
    phrase: str
    reach: int
    capacity: int
    power: int
    sounds: tuple[str, str]
    cradle: str
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


def _r_stuck_worry(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["stuck"] < THRESHOLD:
        return out
    sig = ("stuck_worry", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for role in ("lead", "friend"):
        kid = world.get(role)
        kid.memes["worry"] += 1
    world.get("closet").meters["problem"] += 1
    out.append("__stuck__")
    return out


def _r_lowered_relief(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["lowered"] < THRESHOLD:
        return out
    sig = ("lowered_relief", cargo.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for role in ("lead", "friend"):
        kid = world.get(role)
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    world.get("closet").meters["problem"] = 0.0
    out.append("__rescued__")
    return out


def _r_stall_frustration(world: World) -> list[str]:
    out: list[str] = []
    hoist = world.get("hoist")
    if hoist.meters["stalled"] < THRESHOLD:
        return out
    sig = ("stall_frustration", hoist.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("lead").memes["frustration"] += 1
    world.get("friend").memes["care"] += 1
    out.append("__stall__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck_worry", tag="emotion", apply=_r_stuck_worry),
    Rule(name="lowered_relief", tag="emotion", apply=_r_lowered_relief),
    Rule(name="stall_frustration", tag="emotion", apply=_r_stall_frustration),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


CARGO = {
    "chipmunk": Cargo(
        id="chipmunk",
        label="chipmunk",
        phrase="a little plush chipmunk",
        weight=1,
        call='"Pip, hang on!"',
        reunion="The chipmunk tucked close beside the stegosaurus as soon as it landed.",
        tags={"chipmunk", "toy"},
    ),
    "stegosaurus": Cargo(
        id="stegosaurus",
        label="stegosaurus",
        phrase="a chunky green stegosaurus",
        weight=2,
        call='"Spike, we are coming!"',
        reunion="The stegosaurus thumped down safely, and the chipmunk climbed onto its broad back at once.",
        tags={"stegosaurus", "dinosaur", "toy"},
    ),
}

SHELVES = {
    "middle": Shelf(
        id="middle",
        label="middle shelf",
        phrase="the middle shelf",
        height=1,
        image="half-hidden behind winter hats and a rolled sleeping bag",
        tags={"shelf", "storage"},
    ),
    "high": Shelf(
        id="high",
        label="high shelf",
        phrase="the high shelf",
        height=2,
        image="up near the ceiling, above the broom and the old board games",
        tags={"shelf", "storage"},
    ),
}

HOISTS = {
    "basket": HoistRig(
        id="basket",
        label="basket hoist",
        phrase="a little basket hoist bolted to a ceiling hook",
        reach=2,
        capacity=1,
        power=1,
        sounds=("whirr-click", "creak"),
        cradle="the small wire basket",
        tags={"hoist", "pulley"},
    ),
    "sling": HoistRig(
        id="sling",
        label="sling hoist",
        phrase="a canvas sling hoist tied to a ceiling pulley",
        reach=2,
        capacity=2,
        power=1,
        sounds=("zip-zip", "whuff"),
        cradle="the snug canvas sling",
        tags={"hoist", "pulley"},
    ),
    "crate": HoistRig(
        id="crate",
        label="crate hoist",
        phrase="a sturdy crate hoist with a hand crank",
        reach=2,
        capacity=3,
        power=2,
        sounds=("clack-clack", "whumm"),
        cradle="the little wooden crate",
        tags={"hoist", "pulley"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["brave", "careful", "cheerful", "curious", "steady", "thoughtful"]


@dataclass
class StoryParams:
    cargo: str
    shelf: str
    hoist: str
    start_mode: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    lead_trait: str
    friend_trait: str
    seed: Optional[int] = None


def required_effort(cargo: Cargo, shelf: Shelf) -> int:
    return cargo.weight + shelf.height - 1


def initial_effort(hoist: HoistRig, start_mode: str) -> int:
    return hoist.power + (1 if start_mode == "together" else 0)


def max_effort_with_help(hoist: HoistRig) -> int:
    return hoist.power + 1


def combo_reasonable(cargo: Cargo, shelf: Shelf, hoist: HoistRig) -> bool:
    if hoist.reach < shelf.height:
        return False
    if hoist.capacity < cargo.weight:
        return False
    return max_effort_with_help(hoist) >= required_effort(cargo, shelf)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for cargo_id, cargo in CARGO.items():
        for shelf_id, shelf in SHELVES.items():
            for hoist_id, hoist in HOISTS.items():
                if combo_reasonable(cargo, shelf, hoist):
                    combos.append((cargo_id, shelf_id, hoist_id))
    return combos


def explain_rejection(cargo: Cargo, shelf: Shelf, hoist: HoistRig) -> str:
    if hoist.reach < shelf.height:
        return (
            f"(No story: the {hoist.label} does not reach {shelf.phrase}. "
            f"The rescue tool has to reach the stranded {cargo.label}.)"
        )
    if hoist.capacity < cargo.weight:
        return (
            f"(No story: the {hoist.label} cannot safely hold the {cargo.label}. "
            f"Use a stronger hoist for that toy.)"
        )
    need = required_effort(cargo, shelf)
    max_effort = max_effort_with_help(hoist)
    return (
        f"(No story: even with both friends pulling, the {hoist.label} is too weak "
        f"for the {cargo.label} on {shelf.phrase} ({max_effort} < {need}).)"
    )


def outcome_of(params: StoryParams) -> str:
    cargo = CARGO[params.cargo]
    shelf = SHELVES[params.shelf]
    hoist = HOISTS[params.hoist]
    if not combo_reasonable(cargo, shelf, hoist):
        raise StoryError(explain_rejection(cargo, shelf, hoist))
    need = required_effort(cargo, shelf)
    first_try = initial_effort(hoist, params.start_mode)
    return "smooth" if first_try >= need else "teamup"


def sound_pair(hoist: HoistRig) -> str:
    return f'{hoist.sounds[0]}! {hoist.sounds[1]}!'


def companion_id(cargo_id: str) -> str:
    return "stegosaurus" if cargo_id == "chipmunk" else "chipmunk"


def introduce(world: World, lead: Entity, friend: Entity, hoist: HoistRig) -> None:
    world.say(
        f"One rainy afternoon, {lead.id} and {friend.id} slipped into the storage closet "
        f"and decided it was not a closet at all, but an expedition cave full of hidden shelves."
    )
    world.say(
        f"Brooms stood like tall pine trees, boxes made crooked cliffs, and {hoist.phrase} "
        f"waited above them like the gear of real explorers."
    )
    world.say(
        f"{lead.id} and {friend.id} were best friends, the kind who could turn even dust and old boots into an adventure."
    )


def discover(world: World, lead: Entity, friend: Entity, cargo_cfg: Cargo, shelf: Shelf) -> None:
    cargo = world.get("cargo")
    companion = world.get("companion")
    cargo.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {friend.id} looked up and gasped. {cargo_cfg.phrase} was stranded on {shelf.phrase}, "
        f"{shelf.image}."
    )
    world.say(
        f"Down below, the {companion.label} waited on a box lid as if keeping watch."
    )
    world.say(
        f'{cargo_cfg.call} {lead.id} whispered, and the little rescue mission began.'
    )


def plan(world: World, lead: Entity, friend: Entity, hoist: HoistRig, shelf: Shelf) -> None:
    for kid in (lead, friend):
        kid.memes["courage"] += 1
        kid.memes["teamwork"] += 1
    world.say(
        f'"No climbing the boxes," {friend.id} said, giving the wobbly stack a careful look. '
        f'"But the hoist can reach {shelf.phrase}."'
    )
    world.say(
        f"That was true. The rope ran over the pulley and down to a small crank, ready to go {sound_pair(hoist)}"
    )


def load_hoist(world: World, cargo_cfg: Cargo, hoist: HoistRig) -> None:
    cargo = world.get("cargo")
    hoist_ent = world.get("hoist")
    hoist_ent.meters["loaded"] += 1
    cargo.meters["in_cradle"] += 1
    world.say(
        f"They guided the line until {hoist.cradle} brushed the shelf, and soon the {cargo_cfg.label} was tucked inside."
    )


def try_lift(world: World, lead: Entity, friend: Entity, cargo_cfg: Cargo, hoist: HoistRig,
             start_mode: str, need: int) -> bool:
    hoist_ent = world.get("hoist")
    effort = initial_effort(hoist, start_mode)
    if start_mode == "together":
        lead.memes["trust"] += 1
        friend.memes["trust"] += 1
        world.say(
            f"{lead.id} took the crank, {friend.id} caught the guide rope, and together they pulled."
        )
    else:
        world.say(
            f"{lead.id} grabbed the crank first and tried alone while {friend.id} watched the line."
        )
    world.say(
        f'{sound_pair(hoist)} went the hoist as the rope tightened.'
    )
    if effort >= need:
        hoist_ent.meters["moving"] += 1
        return True
    hoist_ent.meters["stalled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But the line only twitched. The {cargo_cfg.label} wobbled, and the hoist gave a stubborn little {hoist.sounds[1]}."
    )
    return False


def ask_help(world: World, lead: Entity, friend: Entity) -> None:
    lead.memes["humility"] += 1
    friend.memes["care"] += 1
    world.say(
        f'{lead.id} let out a puff of air. "I can\'t do it by myself," {lead.pronoun()} admitted.'
    )
    world.say(
        f'"Then you won\'t be by yourself," {friend.id} said, stepping in shoulder to shoulder. '
        f'That made the closet feel less like a trap and more like a team camp.'
    )


def finish_lift(world: World, lead: Entity, friend: Entity, cargo_cfg: Cargo, hoist: HoistRig) -> None:
    cargo = world.get("cargo")
    cargo.meters["stuck"] = 0.0
    cargo.meters["lowered"] += 1
    world.get("hoist").meters["moving"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Now the rope slid for real. {sound_pair(hoist)} sang through the closet as the {cargo_cfg.label} floated down."
    )
    world.say(
        f"{cargo_cfg.reunion}"
    )
    world.say(
        f"{lead.id} and {friend.id} caught the toy together, laughing so softly that even the dust seemed to listen."
    )


def ending(world: World, lead: Entity, friend: Entity, cargo_cfg: Cargo, shelf: Shelf) -> None:
    companion = world.get("companion")
    world.say(
        f"They set both toys on a folded blanket and made a new base camp low to the ground, far from {shelf.phrase}."
    )
    world.say(
        f'The {cargo_cfg.label} leaned against the {companion.label}, and {friend.id} grinned. "Next time," {friend.pronoun()} said, "our expedition starts with teamwork."'
    )
    world.say(
        f"{lead.id} nodded. In the dim, cozy storage closet, the adventure ended with two friends, one safe rescue, and a room that no longer felt quite so high."
    )


def tell(params: StoryParams) -> World:
    cargo_cfg = CARGO[params.cargo]
    shelf = SHELVES[params.shelf]
    hoist = HOISTS[params.hoist]
    need = required_effort(cargo_cfg, shelf)

    world = World()
    lead = world.add(Entity(
        id="lead",
        kind="character",
        type=params.lead_gender,
        label=params.lead_name,
        phrase=params.lead_name,
        role="lead",
        traits=[params.lead_trait],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=params.friend_gender,
        label=params.friend_name,
        phrase=params.friend_name,
        role="friend",
        traits=[params.friend_trait],
    ))
    closet = world.add(Entity(
        id="closet",
        type="place",
        label="storage closet",
        phrase="the storage closet",
        tags={"storage", "closet"},
    ))
    cargo_ent = world.add(Entity(
        id="cargo",
        type="toy",
        label=cargo_cfg.label,
        phrase=cargo_cfg.phrase,
        tags=set(cargo_cfg.tags),
    ))
    companion_cfg = CARGO[companion_id(params.cargo)]
    companion = world.add(Entity(
        id="companion",
        type="toy",
        label=companion_cfg.label,
        phrase=companion_cfg.phrase,
        tags=set(companion_cfg.tags),
    ))
    hoist_ent = world.add(Entity(
        id="hoist",
        type="tool",
        label=hoist.label,
        phrase=hoist.phrase,
        tags=set(hoist.tags),
    ))
    shelf_ent = world.add(Entity(
        id="shelf",
        type="place",
        label=shelf.label,
        phrase=shelf.phrase,
        tags=set(shelf.tags),
    ))

    world.facts.update(
        cargo_cfg=cargo_cfg,
        companion_cfg=companion_cfg,
        shelf_cfg=shelf,
        hoist_cfg=hoist,
        lead=lead,
        friend=friend,
        closet=closet,
        shelf=shelf_ent,
        cargo=cargo_ent,
        companion=companion,
        hoist=hoist_ent,
        need=need,
        start_mode=params.start_mode,
    )

    introduce(world, lead, friend, hoist)
    discover(world, lead, friend, cargo_cfg, shelf)

    world.para()
    plan(world, lead, friend, hoist, shelf)
    load_hoist(world, cargo_cfg, hoist)
    smooth = try_lift(world, lead, friend, cargo_cfg, hoist, params.start_mode, need)

    if not smooth:
        world.para()
        ask_help(world, lead, friend)
        finish_lift(world, lead, friend, cargo_cfg, hoist)
        outcome = "teamup"
    else:
        finish_lift(world, lead, friend, cargo_cfg, hoist)
        outcome = "smooth"

    world.para()
    ending(world, lead, friend, cargo_cfg, shelf)
    world.facts["outcome"] = outcome
    return world


KNOWLEDGE = {
    "chipmunk": [(
        "What is a chipmunk?",
        "A chipmunk is a small furry animal a bit like a squirrel. It has cheeks for carrying food and it moves very quickly."
    )],
    "stegosaurus": [(
        "What was a stegosaurus?",
        "A stegosaurus was a plant-eating dinosaur with big plates along its back. It also had a tail with spikes at the end."
    )],
    "hoist": [(
        "What does a hoist do?",
        "A hoist is a tool that lifts or lowers things with a rope, chain, or pulley. It helps move something safely instead of reaching or climbing."
    )],
    "pulley": [(
        "What is a pulley?",
        "A pulley is a wheel with a rope over it. It helps make lifting easier because the rope can change the direction of the pull."
    )],
    "friendship": [(
        "What makes a good friend during a hard job?",
        "A good friend notices when you need help and joins in kindly. Working together can turn a hard problem into something manageable."
    )],
    "sound": [(
        "Why do tools make sounds like clack or whirr?",
        "Tools make sounds when their parts move and rub or click together. Those sounds can tell you that something is turning, pulling, or stopping."
    )],
    "storage": [(
        "What is a storage closet for?",
        "A storage closet is a small place where people keep things like boxes, boots, games, and tools. It helps keep useful things in one spot."
    )],
}
KNOWLEDGE_ORDER = ["chipmunk", "stegosaurus", "hoist", "pulley", "friendship", "sound", "storage"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cargo = f["cargo_cfg"]
    shelf = f["shelf_cfg"]
    hoist = f["hoist_cfg"]
    lead = f["lead"]
    friend = f["friend"]
    outcome = f["outcome"]
    if outcome == "teamup":
        return [
            f'Write a short adventure story for a 3-to-5-year-old set in a storage closet that includes the words "stegosaurus", "chipmunk", and "hoist".',
            f"Tell a gentle rescue story where {lead.label} tries to lower a stranded {cargo.label} from {shelf.phrase}, but needs {friend.label}'s help to work the {hoist.label}.",
            f'Write a friendship story with sound effects like "{hoist.sounds[0]}!" and "{hoist.sounds[1]}!" where teamwork solves the problem.',
        ]
    return [
        f'Write a short adventure story for a 3-to-5-year-old set in a storage closet that includes the words "stegosaurus", "chipmunk", and "hoist".',
        f"Tell a toy-rescue story where two best friends use a {hoist.label} to bring a {cargo.label} down from {shelf.phrase}.",
        f'Write a gentle adventure with sound effects and a happy ending that shows how friends can be brave together.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    cargo = f["cargo_cfg"]
    companion = f["companion_cfg"]
    shelf = f["shelf_cfg"]
    hoist = f["hoist_cfg"]
    lead = f["lead"]
    friend = f["friend"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {lead.label} and {friend.label}, in a storage closet with a {cargo.label} and a {companion.label}. The adventure becomes a rescue because one toy is stuck up high."
        ),
        (
            f"Why did they need the hoist?",
            f"They needed the hoist because the {cargo.label} was stranded on {shelf.phrase}. The hoist could reach safely where the children should not climb."
        ),
        (
            f"What made the story feel like an adventure?",
            f"The storage closet looked like an expedition cave full of cliffs and hidden gear. The sounds of the hoist and the high shelf made the rescue feel like a real mission."
        ),
    ]
    if outcome == "teamup":
        qa.append((
            f"Why could {lead.label} not finish the rescue alone?",
            f"{lead.label} started the lift alone, but the hoist stalled before the {cargo.label} could come down. The job needed more pulling power, so {friend.label} stepped in and the rescue worked once they teamed up."
        ))
        qa.append((
            "How did friendship help solve the problem?",
            f"Friendship helped because {friend.label} did not laugh or walk away when the first try failed. {friend.pronoun('subject').capitalize()} joined {lead.label}, and together they turned a stuck moment into a safe rescue."
        ))
    else:
        qa.append((
            "How did the rescue work?",
            f"They tucked the {cargo.label} into {hoist.cradle} and worked the hoist together from the start. Because the plan matched the tool, the toy came down safely with a cheerful {hoist.sounds[0]} and {hoist.sounds[1]}."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with both toys together on a low blanket base camp, and the friends feeling proud and close. The ending image shows that the high shelf was no longer the boss of the adventure."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"friendship", "sound", "storage", "hoist", "pulley"}
    tags |= set(f["cargo_cfg"].tags)
    tags |= set(f["companion_cfg"].tags)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        cargo="chipmunk",
        shelf="high",
        hoist="basket",
        start_mode="solo",
        lead_name="Lily",
        lead_gender="girl",
        friend_name="Tom",
        friend_gender="boy",
        lead_trait="brave",
        friend_trait="careful",
    ),
    StoryParams(
        cargo="stegosaurus",
        shelf="middle",
        hoist="sling",
        start_mode="solo",
        lead_name="Mia",
        lead_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        lead_trait="curious",
        friend_trait="steady",
    ),
    StoryParams(
        cargo="chipmunk",
        shelf="middle",
        hoist="basket",
        start_mode="together",
        lead_name="Sam",
        lead_gender="boy",
        friend_name="Zoe",
        friend_gender="girl",
        lead_trait="cheerful",
        friend_trait="thoughtful",
    ),
    StoryParams(
        cargo="stegosaurus",
        shelf="high",
        hoist="crate",
        start_mode="together",
        lead_name="Noah",
        lead_gender="boy",
        friend_name="Ella",
        friend_gender="girl",
        lead_trait="brave",
        friend_trait="careful",
    ),
]


ASP_RULES = r"""
reasonable(C, S, H) :- cargo(C), shelf(S), hoist(H),
                       shelf_height(S, Sh), hoist_reach(H, Hr), Hr >= Sh,
                       cargo_weight(C, W), hoist_capacity(H, Cap), Cap >= W,
                       need(C, S, Need), hoist_power(H, P), P + 1 >= Need.

need(C, S, W + Sh - 1) :- cargo(C), shelf(S), cargo_weight(C, W), shelf_height(S, Sh).

outcome(smooth) :- start_mode(together), chosen(C, S, H), reasonable(C, S, H).
outcome(smooth) :- start_mode(solo), chosen(C, S, H), reasonable(C, S, H),
                   need(C, S, Need), hoist_power(H, P), P >= Need.
outcome(teamup) :- start_mode(solo), chosen(C, S, H), reasonable(C, S, H),
                   need(C, S, Need), hoist_power(H, P), P < Need, P + 1 >= Need.
valid(C, S, H) :- reasonable(C, S, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cargo_id, cargo in CARGO.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("cargo_weight", cargo_id, cargo.weight))
    for shelf_id, shelf in SHELVES.items():
        lines.append(asp.fact("shelf", shelf_id))
        lines.append(asp.fact("shelf_height", shelf_id, shelf.height))
    for hoist_id, hoist in HOISTS.items():
        lines.append(asp.fact("hoist", hoist_id))
        lines.append(asp.fact("hoist_reach", hoist_id, hoist.reach))
        lines.append(asp.fact("hoist_capacity", hoist_id, hoist.capacity))
        lines.append(asp.fact("hoist_power", hoist_id, hoist.power))
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
        asp.fact("chosen", params.cargo, params.shelf, params.hoist),
        asp.fact("start_mode", params.start_mode),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        py = outcome_of(params)
        asp_val = asp_outcome(params)
        if py != asp_val:
            mismatches.append((params, py, asp_val))
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes: {len(mismatches)} cases.")
        for params, py, asp_val in mismatches[:5]:
            print(f"  {params} -> python={py} asp={asp_val}")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        if "{" in smoke.story or "}" in smoke.story:
            raise StoryError("smoke test story leaked template braces")
        buffer = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buffer
            emit(smoke, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: friends rescue a toy in a storage closet with a hoist."
    )
    ap.add_argument("--cargo", choices=sorted(CARGO))
    ap.add_argument("--shelf", choices=sorted(SHELVES))
    ap.add_argument("--hoist", choices=sorted(HOISTS))
    ap.add_argument("--start-mode", choices=["solo", "together"])
    ap.add_argument("--lead-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible cargo/shelf/hoist combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.cargo not in CARGO:
        raise StoryError(f"(Unknown cargo: {args.cargo})")
    if args.shelf and args.shelf not in SHELVES:
        raise StoryError(f"(Unknown shelf: {args.shelf})")
    if args.hoist and args.hoist not in HOISTS:
        raise StoryError(f"(Unknown hoist: {args.hoist})")

    if args.cargo and args.shelf and args.hoist:
        cargo = CARGO[args.cargo]
        shelf = SHELVES[args.shelf]
        hoist = HOISTS[args.hoist]
        if not combo_reasonable(cargo, shelf, hoist):
            raise StoryError(explain_rejection(cargo, shelf, hoist))

    combos = [
        combo for combo in valid_combos()
        if (args.cargo is None or combo[0] == args.cargo)
        and (args.shelf is None or combo[1] == args.shelf)
        and (args.hoist is None or combo[2] == args.hoist)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    cargo_id, shelf_id, hoist_id = rng.choice(sorted(combos))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or pick_name(rng, lead_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=lead_name)
    start_mode = args.start_mode or rng.choice(["solo", "together"])
    return StoryParams(
        cargo=cargo_id,
        shelf=shelf_id,
        hoist=hoist_id,
        start_mode=start_mode,
        lead_name=lead_name,
        lead_gender=lead_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        lead_trait=rng.choice(TRAITS),
        friend_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.cargo not in CARGO:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.shelf not in SHELVES:
        raise StoryError(f"(Unknown shelf: {params.shelf})")
    if params.hoist not in HOISTS:
        raise StoryError(f"(Unknown hoist: {params.hoist})")
    cargo = CARGO[params.cargo]
    shelf = SHELVES[params.shelf]
    hoist = HOISTS[params.hoist]
    if not combo_reasonable(cargo, shelf, hoist):
        raise StoryError(explain_rejection(cargo, shelf, hoist))

    world = tell(params)
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
        print(f"{len(combos)} compatible (cargo, shelf, hoist) combos:\n")
        for cargo, shelf, hoist in combos:
            print(f"  {cargo:11} {shelf:7} {hoist}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.lead_name} & {p.friend_name}: {p.cargo} from {p.shelf} with {p.hoist} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
