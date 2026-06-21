#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hydro_dummy_pan_magic_friendship_mystery.py
======================================================================

A small storyworld about two friends solving a gentle magical mystery.

Seed anchors
------------
This world always includes the words "hydro", "dummy", and "pan" in natural
story text. The domain rebuilds a tiny source-tale premise:

- a magical hydro device should be singing, but has gone quiet
- a little pan under the drip keeps making a clue-like sound
- a dummy clue tries to fool the children
- friendship helps them solve the mystery kindly
- the "thief" is a small magical resident who borrowed the missing charm

The world model prefers only combinations where:
- the chosen sprite plausibly belongs in the place
- the chosen magic method actually works with that place's water features
- the chosen dummy clue belongs in that place

Run it
------
python storyworlds/worlds/gpt-5.4/hydro_dummy_pan_magic_friendship_mystery.py
python storyworlds/worlds/gpt-5.4/hydro_dummy_pan_magic_friendship_mystery.py --all
python storyworlds/worlds/gpt-5.4/hydro_dummy_pan_magic_friendship_mystery.py --trace
python storyworlds/worlds/gpt-5.4/hydro_dummy_pan_magic_friendship_mystery.py --qa --json
python storyworlds/worlds/gpt-5.4/hydro_dummy_pan_magic_friendship_mystery.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    device: str
    waterway: str
    nook: str
    mood: str
    methods: set[str] = field(default_factory=set)
    sprites: set[str] = field(default_factory=set)
    decoys: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class SpriteKind:
    id: str
    label: str
    phrase: str
    habit: str
    borrow_reason: str
    apology: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    action: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DummyClue:
    id: str
    label: str
    phrase: str
    trickiness: int = 1
    mislead: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Trait:
    id: str
    patience: int
    line: str
    tags: set[str] = field(default_factory=set)


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


def _r_quiet_device(world: World) -> list[str]:
    device = world.entities.get("device")
    if not device or device.meters["missing_charm"] < THRESHOLD:
        return []
    sig = ("quiet", "device")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    device.meters["quiet"] += 1
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["worry"] += 1
            ent.memes["curiosity"] += 1
    return []


def _r_pan_ping(world: World) -> list[str]:
    pan = world.entities.get("pan")
    device = world.entities.get("device")
    if not pan or not device or device.meters["quiet"] < THRESHOLD:
        return []
    sig = ("ping", "pan")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pan.meters["ringing"] += 1
    return []


def _r_friendship_courage(world: World) -> list[str]:
    a = world.entities.get("lead")
    b = world.entities.get("friend")
    if not a or not b:
        return []
    if a.memes["sharing"] < THRESHOLD or b.memes["sharing"] < THRESHOLD:
        return []
    sig = ("courage", "pair")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    a.memes["courage"] += 1
    b.memes["courage"] += 1
    return []


def _r_restored_song(world: World) -> list[str]:
    device = world.entities.get("device")
    charm = world.entities.get("charm")
    if not device or not charm or charm.attrs.get("returned") is not True:
        return []
    sig = ("restored", "device")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    device.meters["quiet"] = 0.0
    device.meters["glow"] += 1
    pan = world.entities.get("pan")
    if pan:
        pan.meters["ringing"] = 0.0
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["relief"] += 1
            ent.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="quiet_device", tag="physical", apply=_r_quiet_device),
    Rule(name="pan_ping", tag="physical", apply=_r_pan_ping),
    Rule(name="friendship_courage", tag="social", apply=_r_friendship_courage),
    Rule(name="restored_song", tag="physical", apply=_r_restored_song),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


PLACES = {
    "greenhouse": Place(
        id="greenhouse",
        label="greenhouse",
        phrase="the glass-roofed greenhouse",
        device="a hydro lily wheel",
        waterway="the narrow runnel between the fern tables",
        nook="the warm potting shelf behind the mint jars",
        mood="Every pane held a silver bead of water, and the place smelled green and secret.",
        methods={"floatleaf", "mist_lantern"},
        sprites={"froglet", "rain_mouse"},
        decoys={"dummy_key", "dummy_petals"},
        tags={"hydro", "garden", "mystery"},
    ),
    "mill": Place(
        id="mill",
        label="old mill room",
        phrase="the old mill room by the stream",
        device="a hydro song wheel",
        waterway="the shallow wooden channel under the wheel",
        nook="the flour shelf tucked behind the turning beam",
        mood="The boards smelled like rain and grain, and the shadows seemed to be listening.",
        methods={"echo_rhyme", "floatleaf"},
        sprites={"otterkin", "rain_mouse"},
        decoys={"dummy_key", "dummy_feather"},
        tags={"hydro", "mill", "mystery"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="moon courtyard",
        phrase="the little moon courtyard behind the school",
        device="a hydro fountain clock",
        waterway="the thin stream running around the blue stones",
        nook="the ivy arch beside the fountain basin",
        mood="The stones shone like polished plums, and the air felt full of waiting.",
        methods={"mist_lantern", "echo_rhyme"},
        sprites={"froglet", "otterkin"},
        decoys={"dummy_feather", "dummy_petals"},
        tags={"hydro", "courtyard", "mystery"},
    ),
}

SPRITES = {
    "froglet": SpriteKind(
        id="froglet",
        label="froglet sprite",
        phrase="a small froglet sprite with shining knees",
        habit="liked tucking round things into safe little corners",
        borrow_reason="thought the missing moon charm looked lonely and wanted to polish it in a damp leaf-cup",
        apology="I was only borrowing it, not stealing it. I should have asked first.",
        tags={"sprite", "friendship"},
    ),
    "otterkin": SpriteKind(
        id="otterkin",
        label="otterkin sprite",
        phrase="an otterkin sprite with whiskers like threads of rain",
        habit="collected bright things that made the water laugh",
        borrow_reason="borrowed the charm to brighten a tiny raft of reeds",
        apology="I meant to bring it back before supper. I forgot how fast the water sings.",
        tags={"sprite", "friendship"},
    ),
    "rain_mouse": SpriteKind(
        id="rain_mouse",
        label="rain mouse",
        phrase="a rain mouse with a silver tail",
        habit="hid small treasures where the damp stayed cool",
        borrow_reason="borrowed the charm to light a nest made of moss and string",
        apology="I did not want anyone to worry. I only wanted one little hour of glow.",
        tags={"sprite", "friendship"},
    ),
}

METHODS = {
    "echo_rhyme": Method(
        id="echo_rhyme",
        label="echo rhyme",
        phrase="an echo rhyme over the pan",
        action="sang a soft counting rhyme into the pan and listened for the answer in the water",
        reveal="The pan answered with three bright pings, and the echo skipped toward the hiding place.",
        tags={"pan", "magic"},
    ),
    "floatleaf": Method(
        id="floatleaf",
        label="floating leaf spell",
        phrase="a floating leaf spell",
        action="set a mint leaf on the water and whispered a hydro finding spell",
        reveal="The leaf spun once, then sailed steadily toward the hiding place.",
        tags={"hydro", "magic"},
    ),
    "mist_lantern": Method(
        id="mist_lantern",
        label="mist lantern",
        phrase="a mist lantern charm",
        action="lifted a small lantern charm so the wet air could catch its light",
        reveal="A pale beam crossed the mist and rested on the hiding place like a pointing finger.",
        tags={"magic", "mystery"},
    ),
}

DECOYS = {
    "dummy_key": DummyClue(
        id="dummy_key",
        label="dummy key",
        phrase="a dummy key made of painted wood",
        trickiness=1,
        mislead="It looked important, but the teeth were smooth and could not open anything at all.",
        tags={"dummy", "clue"},
    ),
    "dummy_petals": DummyClue(
        id="dummy_petals",
        label="dummy petals",
        phrase="a ring of dummy petals cut from waxed paper",
        trickiness=2,
        mislead="The petals glittered like a real trail, but they had been tucked there on purpose to fool quick eyes.",
        tags={"dummy", "clue"},
    ),
    "dummy_feather": DummyClue(
        id="dummy_feather",
        label="dummy feather",
        phrase="a dummy feather carved from soap",
        trickiness=2,
        mislead="From far away it looked soft and magical, but close up it smelled faintly of lavender soap.",
        tags={"dummy", "clue"},
    ),
}

TRAITS = {
    "patient": Trait(
        id="patient",
        patience=2,
        line="liked to stop and listen before guessing",
        tags={"friendship"},
    ),
    "careful": Trait(
        id="careful",
        patience=2,
        line="noticed little things that hurried feet might miss",
        tags={"friendship"},
    ),
    "brisk": Trait(
        id="brisk",
        patience=1,
        line="was brave enough to hurry toward an answer",
        tags={"friendship"},
    ),
    "sparky": Trait(
        id="sparky",
        patience=1,
        line="often had an idea before the whole puzzle was ready",
        tags={"friendship"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Tess", "Ruby", "Nora", "Ivy", "Ada", "June"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Eli", "Jude", "Noah", "Arlo"]


def sprite_belongs(place_id: str, sprite_id: str) -> bool:
    return sprite_id in PLACES[place_id].sprites


def method_works(place_id: str, method_id: str) -> bool:
    return method_id in PLACES[place_id].methods


def decoy_belongs(place_id: str, decoy_id: str) -> bool:
    return decoy_id in PLACES[place_id].decoys


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for sprite_id in sorted(place.sprites):
            for method_id in sorted(place.methods):
                for decoy_id in sorted(place.decoys):
                    combos.append((place_id, sprite_id, method_id, decoy_id))
    return combos


@dataclass
class StoryParams:
    place: str
    sprite: str
    method: str
    decoy: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    lead_trait: str
    friend_trait: str
    seed: Optional[int] = None


def pair_patience(params: StoryParams) -> int:
    return max(TRAITS[params.lead_trait].patience, TRAITS[params.friend_trait].patience)


def outcome_of(params: StoryParams) -> str:
    return "straight" if pair_patience(params) >= DECOYS[params.decoy].trickiness else "detour"


def intro(world: World, lead: Entity, friend: Entity, place: Place) -> None:
    world.say(
        f"After lessons, {lead.id} and {friend.id} slipped into {place.phrase}. "
        f"{place.mood}"
    )
    world.say(
        f"They were the sort of friends who always shared the middle of a mystery, "
        f"and today the quiet around {place.device} felt strange at once."
    )


def missing_charm(world: World, lead: Entity, friend: Entity, place: Place) -> None:
    device = world.get("device")
    charm = world.get("charm")
    device.meters["missing_charm"] += 1
    charm.attrs["missing"] = True
    propagate(world)
    world.say(
        f"A little copper pan sat under the drip, and every drop went ping ... ping ... ping. "
        f'"That pan never sounds lonely unless something is wrong," {friend.id} whispered.'
    )
    world.say(
        f"The moon charm that usually hung inside {place.device} was gone, and the hydro water "
        f"moved with no song at all."
    )
    world.facts["mystery_started"] = True


def examine_dummy(world: World, lead: Entity, friend: Entity, decoy: DummyClue, detour: bool) -> None:
    lead.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    propagate(world)
    world.say(
        f"Near the stones they found {decoy.phrase}. "
        f'"A dummy clue," said {lead.id}. "{decoy.mislead}"'
    )
    if detour:
        world.say(
            f"For a minute they chased that wrong clue anyway, peering into corners where nothing but wet moss waited. "
            f"The mistake made the puzzle feel deeper, not meaner."
        )
    else:
        world.say(
            f"They almost followed it, but then both friends stopped together. "
            f"Because they compared what each had noticed, the dummy clue lost its spell."
        )


def do_method(world: World, lead: Entity, friend: Entity, method: Method, place: Place) -> None:
    lead.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    propagate(world)
    world.say(
        f'So they tried {method.phrase}. {lead.id} and {friend.id} {method.action} by {place.waterway}.'
    )
    world.say(method.reveal)
    world.facts["method_used"] = method.id


def find_sprite(world: World, lead: Entity, friend: Entity, sprite: SpriteKind, place: Place) -> None:
    spr = world.get("sprite")
    spr.attrs["found"] = True
    spr.memes["nervous"] += 1
    world.say(
        f"In {place.nook} they found {sprite.phrase}, curled around the missing charm. "
        f"The little creature looked startled rather than sneaky."
    )
    world.say(
        f'{friend.id} remembered that the {sprite.label} {sprite.habit}. '
        f'"Maybe this is not a thief-mystery," {friend.pronoun()} said. "Maybe it is a ask-first mystery."'
    )


def kind_talk(world: World, lead: Entity, friend: Entity, sprite: SpriteKind) -> None:
    spr = world.get("sprite")
    lead.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    spr.memes["trust"] += 1
    world.say(
        f'{lead.id} knelt beside the nook. "We were worried," {lead.pronoun()} said. '
        f'"If you borrow shining things, you have to tell somebody."'
    )
    world.say(
        f'The sprite blinked and hugged the charm. "{sprite.apology}"'
    )
    world.say(
        f'When {friend.id} promised they could help make a tiny bright corner another day, the creature relaxed at once.'
    )


def return_charm(world: World, place: Place) -> None:
    charm = world.get("charm")
    charm.attrs["returned"] = True
    charm.attrs["missing"] = False
    propagate(world)
    world.say(
        f'Together they hung the moon charm back inside {place.device}. '
        f'At once the hydro water caught the light and began to sing again.'
    )
    world.say(
        "The lonely pan fell quiet, except for one last pleased ping."
    )


def ending(world: World, lead: Entity, friend: Entity, sprite: SpriteKind, place: Place) -> None:
    world.say(
        f"Before they left, the friends tucked a polished pebble near the nook for the {sprite.label}. "
        f"It was a smaller gift than the missing charm, but it was given honestly."
    )
    world.say(
        f"So the mystery ended not with a scold, but with a new promise: next time, they would ask, answer, "
        f"and keep the music of {place.device} safe together."
    )


def tell(
    place: Place,
    sprite_cfg: SpriteKind,
    method_cfg: Method,
    decoy_cfg: DummyClue,
    lead_name: str,
    lead_gender: str,
    friend_name: str,
    friend_gender: str,
    lead_trait: Trait,
    friend_trait: Trait,
) -> World:
    world = World(place=place)
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    sprite = world.add(Entity(id="sprite", kind="character", type="sprite", role="sprite", label=sprite_cfg.label))
    device = world.add(Entity(id="device", type="device", label=place.device))
    pan = world.add(Entity(id="pan", type="pan", label="pan"))
    charm = world.add(Entity(id="charm", type="charm", label="moon charm"))

    lead.attrs["trait"] = lead_trait.id
    friend.attrs["trait"] = friend_trait.id
    lead.memes["friendship"] += 1
    friend.memes["friendship"] += 1

    intro(world, lead, friend, place)
    world.say(
        f"{lead.id} {lead_trait.line}, and {friend.id} {friend_trait.line}. "
        f"That was why they solved things better side by side than alone."
    )

    world.para()
    missing_charm(world, lead, friend, place)

    detour = max(lead_trait.patience, friend_trait.patience) < decoy_cfg.trickiness
    world.para()
    examine_dummy(world, lead, friend, decoy_cfg, detour=detour)
    do_method(world, lead, friend, method_cfg, place)

    world.para()
    find_sprite(world, lead, friend, sprite_cfg, place)
    kind_talk(world, lead, friend, sprite_cfg)
    return_charm(world, place)

    world.para()
    ending(world, lead, friend, sprite_cfg, place)

    world.facts.update(
        lead=lead,
        friend=friend,
        sprite=sprite,
        place=place,
        sprite_cfg=sprite_cfg,
        method=method_cfg,
        decoy=decoy_cfg,
        device=device,
        pan=pan,
        charm=charm,
        detour=detour,
        outcome="detour" if detour else "straight",
        borrowed_reason=sprite_cfg.borrow_reason,
    )
    return world


KNOWLEDGE = {
    "hydro": [
        (
            "What does hydro mean?",
            "Hydro has to do with water. In a story like this, a hydro wheel or hydro fountain uses moving water to make something work."
        )
    ],
    "pan": [
        (
            "What is a pan?",
            "A pan is a wide metal dish or container. In this story, the little pan catches drips and makes a pinging sound."
        )
    ],
    "dummy": [
        (
            "What is a dummy clue?",
            "A dummy clue is a false clue that looks important at first. It is there to trick you into guessing the wrong thing."
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is something wonderful that does not happen in ordinary life, like water that sings or light that points the way. Story magic often helps characters show what they feel and notice."
        )
    ],
    "friendship": [
        (
            "How can friendship help solve a problem?",
            "Friends can share clues, calm each other down, and notice different things. Working together often helps them make a wiser choice than one child would make alone."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle about something hidden or unexplained. The fun is finding clues and slowly learning what really happened."
        )
    ],
    "sprite": [
        (
            "What is a sprite in a story?",
            "A sprite is a tiny magical being, often linked to water, leaves, or light. A sprite can be mischievous without being truly mean."
        )
    ],
}
KNOWLEDGE_ORDER = ["hydro", "pan", "dummy", "magic", "friendship", "mystery", "sprite"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    place = f["place"]
    method = f["method"]
    decoy = f["decoy"]
    sprite = f["sprite_cfg"]
    if f["outcome"] == "detour":
        middle = "a dummy clue briefly sends them the wrong way before"
    else:
        middle = "they notice a dummy clue but do not let it fool them, and"
    return [
        'Write a gentle mystery story for a 3-to-5-year-old that includes the words "hydro", "dummy", and "pan".',
        f"Tell a magical friendship mystery where two friends in {place.phrase} hear a strange pan, discover a missing charm in {place.device}, and use {method.phrase} to solve the puzzle.",
        f"Write a small mystery in which {middle} the children discover that a {sprite.label} borrowed the missing charm and needs a kind talk more than a scolding.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    place = f["place"]
    method = f["method"]
    decoy = f["decoy"]
    sprite = f["sprite_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {lead.id} and {friend.id}, solving a mystery together. The mystery begins in {place.phrase} when the singing water device goes quiet."
        ),
        (
            "What was the mystery?",
            f"The moon charm was missing from {place.device}, so the hydro water had no song. The little pan under the drip kept pinging as if it were trying to tell the friends something."
        ),
        (
            "What was the dummy clue?",
            f"The dummy clue was {decoy.phrase}. It looked useful at first, but it was only there to pull quick guesses in the wrong direction."
        ),
    ]
    if f["outcome"] == "detour":
        out.append(
            (
                "Did the friends get fooled at first?",
                f"Yes, for a little while they did. They followed the wrong clue first, but then they stopped, shared what each one had noticed, and tried a better idea together."
            )
        )
    else:
        out.append(
            (
                "Why did the dummy clue not fool them?",
                f"It did not fool them because they compared clues instead of grabbing the first answer. Their friendship helped them slow down and think together."
            )
        )
    out.append(
        (
            "How did they solve the mystery?",
            f"They used {method.phrase} by the water and watched where the clue led. The magic worked because it matched the place and helped the hidden path show itself."
        )
    )
    out.append(
        (
            "Who had the missing charm, and why?",
            f"A {sprite.label} had it. The creature had borrowed it because it {f['borrowed_reason']}, but it had not understood how much worry that would cause."
        )
    )
    out.append(
        (
            "How did the story end?",
            f"The friends spoke kindly, the charm was returned, and {place.device} sang again. The ending shows that the real fix was not only magic, but honesty and friendship too."
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"hydro", "pan", "dummy", "magic", "friendship", "mystery", "sprite"}
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="greenhouse",
        sprite="froglet",
        method="floatleaf",
        decoy="dummy_petals",
        lead_name="Lila",
        lead_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        lead_trait="patient",
        friend_trait="brisk",
        seed=1,
    ),
    StoryParams(
        place="mill",
        sprite="otterkin",
        method="echo_rhyme",
        decoy="dummy_key",
        lead_name="Milo",
        lead_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        lead_trait="careful",
        friend_trait="sparky",
        seed=2,
    ),
    StoryParams(
        place="courtyard",
        sprite="froglet",
        method="mist_lantern",
        decoy="dummy_feather",
        lead_name="Tess",
        lead_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        lead_trait="brisk",
        friend_trait="sparky",
        seed=3,
    ),
]


def explain_rejection(place_id: str, sprite_id: str, method_id: str, decoy_id: str) -> str:
    problems: list[str] = []
    if place_id not in PLACES:
        problems.append(f"unknown place '{place_id}'")
    if sprite_id not in SPRITES:
        problems.append(f"unknown sprite '{sprite_id}'")
    if method_id not in METHODS:
        problems.append(f"unknown method '{method_id}'")
    if decoy_id not in DECOYS:
        problems.append(f"unknown decoy '{decoy_id}'")
    if problems:
        return "(No story: " + "; ".join(problems) + ".)"
    if not sprite_belongs(place_id, sprite_id):
        return (
            f"(No story: a {SPRITES[sprite_id].label} does not belong naturally in {PLACES[place_id].phrase}. "
            f"Pick a sprite that fits that place.)"
        )
    if not method_works(place_id, method_id):
        return (
            f"(No story: {METHODS[method_id].phrase} does not fit the water features of {PLACES[place_id].phrase}. "
            f"The magic method must match the place.)"
        )
    if not decoy_belongs(place_id, decoy_id):
        return (
            f"(No story: {DECOYS[decoy_id].phrase} is not a natural dummy clue for {PLACES[place_id].phrase}. "
            f"Pick a decoy that belongs in that mystery.)"
        )
    return "(No story: this combination is not supported.)"


ASP_RULES = r"""
valid(P, S, M, D) :- place(P), sprite(S), method(M), decoy(D),
                     lives_in(S, P), works_in(M, P), decoy_in(D, P).

pair_patience(V) :- lead_trait(T), trait_patience(T, V), not better_lead.
pair_patience(V) :- friend_trait(T), trait_patience(T, V), not better_friend.
better_lead      :- lead_trait(T1), friend_trait(T2), trait_patience(T1, V1), trait_patience(T2, V2), V2 > V1.
better_friend    :- lead_trait(T1), friend_trait(T2), trait_patience(T1, V1), trait_patience(T2, V2), V1 > V2.

straight :- chosen_decoy(D), decoy_trickiness(D, N), pair_patience(P), P >= N.
detour   :- chosen_decoy(D), decoy_trickiness(D, N), pair_patience(P), P < N.

outcome(straight) :- straight.
outcome(detour)   :- detour.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for sprite_id in sorted(place.sprites):
            lines.append(asp.fact("lives_in", sprite_id, place_id))
        for method_id in sorted(place.methods):
            lines.append(asp.fact("works_in", method_id, place_id))
        for decoy_id in sorted(place.decoys):
            lines.append(asp.fact("decoy_in", decoy_id, place_id))
    for sprite_id in SPRITES:
        lines.append(asp.fact("sprite", sprite_id))
    for method_id in METHODS:
        lines.append(asp.fact("method", method_id))
    for decoy_id, decoy in DECOYS.items():
        lines.append(asp.fact("decoy", decoy_id))
        lines.append(asp.fact("decoy_trickiness", decoy_id, decoy.trickiness))
    for trait_id, trait in TRAITS.items():
        lines.append(asp.fact("trait_patience", trait_id, trait.patience))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_decoy", params.decoy),
            asp.fact("lead_trait", params.lead_trait),
            asp.fact("friend_trait", params.friend_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle magical friendship mystery with a hydro device, a dummy clue, and a little pan."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--sprite", choices=sorted(SPRITES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--decoy", choices=sorted(DECOYS))
    ap.add_argument("--lead-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--lead-trait", choices=sorted(TRAITS))
    ap.add_argument("--friend-trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place_id = args.place
    sprite_id = args.sprite
    method_id = args.method
    decoy_id = args.decoy

    explicit_all = place_id and sprite_id and method_id and decoy_id
    if explicit_all:
        if (place_id, sprite_id, method_id, decoy_id) not in set(valid_combos()):
            raise StoryError(explain_rejection(place_id, sprite_id, method_id, decoy_id))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.sprite is None or combo[1] == args.sprite)
        and (args.method is None or combo[2] == args.method)
        and (args.decoy is None or combo[3] == args.decoy)
    ]
    if not combos:
        p = args.place or next(iter(PLACES))
        s = args.sprite or next(iter(SPRITES))
        m = args.method or next(iter(METHODS))
        d = args.decoy or next(iter(DECOYS))
        raise StoryError(explain_rejection(p, s, m, d))

    place_id, sprite_id, method_id, decoy_id = rng.choice(sorted(combos))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or pick_name(rng, lead_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=lead_name)
    lead_trait = args.lead_trait or rng.choice(sorted(TRAITS))
    friend_trait = args.friend_trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        place=place_id,
        sprite=sprite_id,
        method=method_id,
        decoy=decoy_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        lead_trait=lead_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}').")
    if params.sprite not in SPRITES:
        raise StoryError(f"(No story: unknown sprite '{params.sprite}').")
    if params.method not in METHODS:
        raise StoryError(f"(No story: unknown method '{params.method}').")
    if params.decoy not in DECOYS:
        raise StoryError(f"(No story: unknown decoy '{params.decoy}').")
    if (params.place, params.sprite, params.method, params.decoy) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, params.sprite, params.method, params.decoy))

    world = tell(
        place=PLACES[params.place],
        sprite_cfg=SPRITES[params.sprite],
        method_cfg=METHODS[params.method],
        decoy_cfg=DECOYS[params.decoy],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        lead_trait=TRAITS[params.lead_trait],
        friend_trait=TRAITS[params.friend_trait],
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

    cases: list[StoryParams] = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, sprite, method, decoy) combos:\n")
        for place, sprite, method, decoy in combos:
            print(f"  {place:10} {sprite:10} {method:12} {decoy}")
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
            header = f"### {p.lead_name} & {p.friend_name}: {p.place}, {p.sprite}, {p.method}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
