#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/position_bad_ending_moral_value_mystery.py
=====================================================================

A tiny storyworld for a child-facing mystery with a bad ending and a moral.
The key story idea is that a child sees a clue, wants to solve a little
household mystery alone, changes the position of furniture to reach a high
place, and causes the missing object to fall into a vent and vanish.

The world prefers only combinations that support the intended shape:
a small object, a room where a vent sits below the likely hiding place, and
a risky perch that makes the "one wrong move" turn plausible. Safer options
are known to the world but rejected because they do not support this mystery's
bad ending or its moral value.

Run it
------
    python storyworlds/worlds/gpt-5.4/position_bad_ending_moral_value_mystery.py
    python storyworlds/worlds/gpt-5.4/position_bad_ending_moral_value_mystery.py --all
    python storyworlds/worlds/gpt-5.4/position_bad_ending_moral_value_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/position_bad_ending_moral_value_mystery.py --trace
    python storyworlds/worlds/gpt-5.4/position_bad_ending_moral_value_mystery.py --verify
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
RISK_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    position: str = ""
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
class Room:
    id: str
    place: str
    shelf_phrase: str
    vent_phrase: str
    clue_phrase: str
    gloom: str
    tags: set[str] = field(default_factory=set)
    vent_below_shelf: bool = True


@dataclass
class MissingItem:
    id: str
    label: str
    phrase: str
    keeper_line: str
    sound: str
    tiny: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    lead_in: str
    inference: str
    close_view: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perch:
    id: str
    label: str
    phrase: str
    risk: int
    move_text: str
    wobble_text: str
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
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    child = world.entities.get("child")
    perch = world.entities.get("perch")
    if child is None or perch is None:
        return []
    if child.meters["climbing"] < THRESHOLD:
        return []
    if perch.meters["risk"] < THRESHOLD:
        return []
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["off_balance"] += 1
    child.memes["fear"] += 1
    perch.meters["wobbling"] += 1
    return ["__wobble__"]


def _r_bump_box(world: World) -> list[str]:
    child = world.entities.get("child")
    box = world.entities.get("box")
    item = world.entities.get("item")
    if child is None or box is None or item is None:
        return []
    if child.meters["off_balance"] < THRESHOLD:
        return []
    if box.position != "high_shelf":
        return []
    sig = ("bump", box.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    box.meters["bumped"] += 1
    item.meters["falling"] += 1
    return ["__fall__"]


def _r_lose_in_vent(world: World) -> list[str]:
    item = world.entities.get("item")
    vent = world.entities.get("vent")
    room = world.entities.get("room")
    if item is None or vent is None or room is None:
        return []
    if item.meters["falling"] < THRESHOLD:
        return []
    if item.attrs.get("tiny") is not True:
        return []
    if room.attrs.get("vent_below_shelf") is not True:
        return []
    sig = ("lost", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["lost"] += 1
    item.position = "vent"
    vent.meters["contains_item"] += 1
    if "child" in world.entities:
        world.get("child").memes["regret"] += 1
    if "parent" in world.entities:
        world.get("parent").memes["sad"] += 1
    return ["__lost__"]


CAUSAL_RULES = [
    Rule(name="wobble", apply=_r_wobble),
    Rule(name="bump_box", apply=_r_bump_box),
    Rule(name="lose_in_vent", apply=_r_lose_in_vent),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
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
        for bit in produced:
            if bit == "__wobble__":
                perch = world.get("perch")
                world.say(perch.attrs["wobble_text"])
            elif bit == "__fall__":
                item = world.get("item")
                box = world.get("box")
                world.say(
                    f"The edge of {box.phrase} knocked {item.phrase} loose. "
                    f"{item.sound.capitalize()} it dropped through the dim air."
                )
            elif bit == "__lost__":
                room = world.get("room")
                item = world.get("item")
                world.say(
                    f"Then came the tiny metal clink no detective ever wants to hear: "
                    f"{item.phrase} slipped straight through the grate in {room.attrs['vent_phrase']} "
                    f"and vanished."
                )
    return produced


def valid_combo(room: Room, item: MissingItem, perch: Perch) -> bool:
    return room.vent_below_shelf and item.tiny and perch.risk >= RISK_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for item_id, item in ITEMS.items():
            for perch_id, perch in PERCHES.items():
                if valid_combo(room, item, perch):
                    out.append((room_id, item_id, perch_id))
    return out


@dataclass
class StoryParams:
    room: str
    item: str
    clue: str
    perch: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def introduce(world: World, child: Entity, parent: Entity, room: Room, item: MissingItem) -> None:
    world.say(
        f"Late in the afternoon, {child.id} followed {parent.label_word} into {room.place}. "
        f"The room felt hushed and full of corners, and {room.gloom}."
    )
    world.say(
        f"{parent.label_word.capitalize()} stopped by {room.shelf_phrase} and frowned. "
        f'"That is strange," {parent.pronoun()} murmured. "{item.keeper_line}"'
    )


def mystery_setup(world: World, child: Entity, clue: Clue, room: Room) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} loved little mysteries, and {clue.lead_in} near {room.clue_phrase}. "
        f"To {child.pronoun('object')}, it felt like the room was whispering a secret."
    )
    world.say(
        f'"Maybe the clue means {clue.inference}," {child.pronoun()} whispered. '
        f"The word position rolled around in {child.pronoun('possessive')} mind, because every clue seemed to depend on where things stood."
    )


def warning(world: World, child: Entity, parent: Entity, room: Room) -> None:
    parent.memes["care"] += 1
    world.say(
        f'{parent.label_word.capitalize()} saw where {child.id} was looking and said, '
        f'"Wait for me. If something is up on {room.shelf_phrase}, we will check it together."'
    )


def decide_to_reach(world: World, child: Entity, perch: Perch, room: Room) -> None:
    child.memes["pride"] += 1
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} wanted to solve the mystery first. Quietly, {child.pronoun()} {perch.move_text} "
        f"until it stood under {room.shelf_phrase} in just the right position."
    )


def climb(world: World, child: Entity, perch: Entity, clue: Clue) -> None:
    child.meters["climbing"] += 1
    child.position = "on_perch"
    world.say(
        f"{child.id} climbed up for {clue.close_view}. One hand stretched toward the shelf, and the other windmilled in the still air."
    )
    propagate(world, narrate=True)


def aftermath(world: World, child: Entity, parent: Entity, item: MissingItem, room: Room) -> None:
    child.memes["shame"] += 1
    child.memes["sadness"] += 1
    world.say(
        f'{parent.label_word.capitalize()} hurried over at the sound. For one second, {child.id} could only stare at {room.vent_phrase}, '
        f"as if the lost thing might rise back out by itself."
    )
    world.say(
        f'"I only wanted to help," {child.id} said in a small voice. '
        f"But the mystery was over now, and the answer was a painful one."
    )
    world.say(
        f"{parent.label_word.capitalize()} knelt beside {child.pronoun('object')} and gave a sad sigh. "
        f'"Next time, tell me before you move things or climb," {parent.pronoun()} said. '
        f'"Some secrets are not worth losing {item.phrase} for."'
    )
    world.say(
        f"They looked down at the dark grate together. The room stayed quiet, {room.gloom}, "
        f"and {item.phrase} was gone."
    )


def tell(
    room: Room,
    item: MissingItem,
    clue: Clue,
    perch_cfg: Perch,
    name: str,
    gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="child",
            position="floor",
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
            position="room",
        )
    )
    room_ent = world.add(
        Entity(
            id="room",
            type="room",
            label=room.place,
            phrase=room.place,
            position="house",
            attrs={"vent_below_shelf": room.vent_below_shelf, "vent_phrase": room.vent_phrase},
            tags=set(room.tags),
        )
    )
    world.add(
        Entity(
            id="vent",
            type="vent",
            label="vent",
            phrase=room.vent_phrase,
            position="floor",
        )
    )
    world.add(
        Entity(
            id="box",
            type="box",
            label="a velvet box",
            phrase="a little velvet box",
            position="high_shelf",
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            type="missing_item",
            label=item.label,
            phrase=item.phrase,
            position="box",
            attrs={"tiny": item.tiny},
            tags=set(item.tags),
        )
    )
    perch_ent = world.add(
        Entity(
            id="perch",
            type="perch",
            label=perch_cfg.label,
            phrase=perch_cfg.phrase,
            position="floor",
            attrs={"wobble_text": perch_cfg.wobble_text},
            tags=set(perch_cfg.tags),
        )
    )
    perch_ent.meters["risk"] = float(perch_cfg.risk)

    introduce(world, child, parent, room, item)
    mystery_setup(world, child, clue, room)

    world.para()
    warning(world, child, parent, room)
    decide_to_reach(world, child, perch_cfg, room)

    world.para()
    climb(world, child, perch_ent, clue)
    aftermath(world, child, parent, item, room)

    world.facts.update(
        child=child,
        parent=parent,
        room_cfg=room,
        item_cfg=item,
        clue=clue,
        perch_cfg=perch_cfg,
        item=item_ent,
        lost=item_ent.meters["lost"] >= THRESHOLD,
        moral="Do not move things or climb alone to solve a mystery; ask a grown-up for help and tell the truth.",
    )
    return world


ROOMS = {
    "sewing_room": Room(
        id="sewing_room",
        place="the sewing room",
        shelf_phrase="the high walnut shelf",
        vent_phrase="the brass floor vent",
        clue_phrase="the leg of the sewing table",
        gloom="the long curtains made stripes of shadow on the rug",
        tags={"room", "vent", "shelf", "mystery"},
        vent_below_shelf=True,
    ),
    "music_room": Room(
        id="music_room",
        place="the music room",
        shelf_phrase="the tall piano shelf",
        vent_phrase="the black floor vent",
        clue_phrase="the piano bench",
        gloom="the lamp beside the piano left the far wall dusky and strange",
        tags={"room", "vent", "shelf", "mystery"},
        vent_below_shelf=True,
    ),
    "hall_table": Room(
        id="hall_table",
        place="the front hall",
        shelf_phrase="the narrow hall shelf",
        vent_phrase="the old iron floor vent",
        clue_phrase="the umbrella stand",
        gloom="the mirror caught only a thin slice of light",
        tags={"room", "vent", "shelf", "mystery"},
        vent_below_shelf=True,
    ),
    "kitchen_counter": Room(
        id="kitchen_counter",
        place="the kitchen",
        shelf_phrase="the bright counter shelf",
        vent_phrase="the far wall vent",
        clue_phrase="the cookie jar",
        gloom="the room was bright, with no dark corner to hide much at all",
        tags={"room"},
        vent_below_shelf=False,
    ),
}

ITEMS = {
    "brooch": MissingItem(
        id="brooch",
        label="brooch",
        phrase="the silver brooch",
        keeper_line="I left the silver brooch in its box this morning",
        sound="ting",
        tiny=True,
        tags={"brooch", "metal", "small_object"},
    ),
    "brass_key": MissingItem(
        id="brass_key",
        label="brass key",
        phrase="the brass key",
        keeper_line="The brass key should still be up here",
        sound="clink",
        tiny=True,
        tags={"key", "metal", "small_object"},
    ),
    "thimble": MissingItem(
        id="thimble",
        label="thimble",
        phrase="the tiny thimble",
        keeper_line="My tiny thimble was here a moment ago",
        sound="ping",
        tiny=True,
        tags={"thimble", "metal", "small_object"},
    ),
    "music_box": MissingItem(
        id="music_box",
        label="music box",
        phrase="the little music box",
        keeper_line="The little music box was beside the frame",
        sound="thunk",
        tiny=False,
        tags={"box"},
    ),
}

CLUES = {
    "thread": Clue(
        id="thread",
        lead_in="a bright red thread curled on the floor",
        inference="something from the shelf was moved in a hurry",
        close_view="a closer look at the thread and the dust around it",
        tags={"clue", "thread"},
    ),
    "pawprint": Clue(
        id="pawprint",
        lead_in="one dusty pawprint sat by itself",
        inference="the cat had leapt up and brushed past the box",
        close_view="a closer look at the pawprint and the shelf edge",
        tags={"clue", "pawprint", "cat"},
    ),
    "dust_gap": Clue(
        id="dust_gap",
        lead_in="a clean little square broke the dust on the wood",
        inference="something small had been lifted from that exact spot",
        close_view="a closer look at the clear square in the dust",
        tags={"clue", "dust"},
    ),
}

PERCHES = {
    "chair": Perch(
        id="chair",
        label="chair",
        phrase="a straight-backed chair",
        risk=1,
        move_text="dragged a straight-backed chair across the rug",
        wobble_text="The chair legs scraped, tipped, and gave a quick shiver under the small weight.",
        tags={"chair", "risk"},
    ),
    "stool": Perch(
        id="stool",
        label="stool",
        phrase="a round stool",
        risk=2,
        move_text="rolled a round stool over the boards",
        wobble_text="The round stool spun a little underfoot, and the whole world seemed to slide sideways.",
        tags={"stool", "risk"},
    ),
    "toy_box": Perch(
        id="toy_box",
        label="toy box",
        phrase="a painted toy box",
        risk=1,
        move_text="pushed a painted toy box under the shelf",
        wobble_text="The toy box lid shifted with a hollow creak, making the perch lurch at exactly the wrong moment.",
        tags={"box", "risk"},
    ),
    "step_ladder": Perch(
        id="step_ladder",
        label="step ladder",
        phrase="a steady step ladder",
        risk=0,
        move_text="opened the steady step ladder under the shelf",
        wobble_text="Nothing wobbled at all.",
        tags={"ladder", "safe"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Lucy"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Theo", "Noah"]
TRAITS = ["curious", "eager", "proud", "restless", "clever"]

KNOWLEDGE = {
    "vent": [
        (
            "What is a floor vent?",
            "A floor vent is a metal grate where warm or cool air moves through the house. Small things can slip through the holes if you are not careful.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Good detectives look carefully before they touch anything.",
        )
    ],
    "chair": [
        (
            "Why can standing on a chair be unsafe?",
            "A chair can tip or slide when someone stands on it the wrong way. That is why children should ask a grown-up before climbing.",
        )
    ],
    "stool": [
        (
            "Why is a round stool easy to wobble on?",
            "A round stool has a small top and can shift under your feet. Even a tiny wobble can make you lose your balance.",
        )
    ],
    "truth": [
        (
            "Why should you tell a grown-up the truth when something goes wrong?",
            "Telling the truth helps a grown-up solve the problem and keep everyone safe. Hiding a mistake usually makes the trouble bigger.",
        )
    ],
    "patience": [
        (
            "Why does patience help in a mystery?",
            "Patience helps you notice what is really there instead of rushing into the wrong answer. Slow, careful thinking keeps clues safe.",
        )
    ],
}
KNOWLEDGE_ORDER = ["clue", "vent", "chair", "stool", "patience", "truth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item_cfg"]
    room = f["room_cfg"]
    return [
        f'Write a child-friendly mystery story that includes the word "position" and ends sadly.',
        f"Tell a small house mystery where {child.id} tries to solve the disappearance of {item.phrase} alone in {room.place}, and that choice causes the loss.",
        "Write a moral mystery for young children about why you should ask a grown-up for help instead of moving things and climbing by yourself.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    room = f["room_cfg"]
    item = f["item_cfg"]
    clue = f["clue"]
    perch = f["perch_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who wanted to solve a little mystery, and {parent.label_word}, who had asked {child.pronoun('object')} to wait. The mystery was about {item.phrase} in {room.place}.",
        ),
        (
            f"What clue made {child.id} think about the shelf?",
            f"{clue.lead_in.capitalize()} near {room.clue_phrase}. That clue made {child.pronoun('object')} think something up on the shelf had been moved.",
        ),
        (
            "Why is the word position important in the story?",
            f"It mattered because {child.id} believed the answer depended on where the clue, the box, and the furniture were standing. Then {child.pronoun()} changed the position of {perch.phrase}, and that is what started the accident.",
        ),
        (
            f"What bad choice did {child.id} make?",
            f"{child.id} did not wait for {parent.label_word}. Instead, {child.pronoun()} moved {perch.phrase} under the shelf and climbed up alone. That rushed choice turned a mystery into a loss.",
        ),
    ]
    if f["lost"]:
        qa.append(
            (
                f"What happened to {item.phrase}?",
                f"It fell from the box and slipped through {room.vent_phrase}. Because it was small and the vent was right below the shelf, it was lost.",
            )
        )
        qa.append(
            (
                "What is the moral of the story?",
                f"{f['moral']} {child.id} was trying to help, but patience and honesty would have protected both the clue and the missing object.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"clue", "vent", "patience", "truth"}
    perch = world.facts["perch_cfg"]
    if perch.id == "chair":
        tags.add("chair")
    if perch.id == "stool":
        tags.add("stool")
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
        bits: list[str] = []
        if ent.position:
            bits.append(f"position={ent.position}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="sewing_room",
        item="brooch",
        clue="thread",
        perch="chair",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="curious",
        seed=1,
    ),
    StoryParams(
        room="music_room",
        item="brass_key",
        clue="pawprint",
        perch="stool",
        name="Max",
        gender="boy",
        parent="father",
        trait="proud",
        seed=2,
    ),
    StoryParams(
        room="hall_table",
        item="thimble",
        clue="dust_gap",
        perch="toy_box",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="eager",
        seed=3,
    ),
]


def explain_rejection(room: Room, item: MissingItem, perch: Perch) -> str:
    if not room.vent_below_shelf:
        return (
            f"(No story: in {room.place}, the vent is not below the hiding place, so the mystery cannot end with the object vanishing through a grate.)"
        )
    if not item.tiny:
        return (
            f"(No story: {item.phrase} is too large for this world's bad ending. The missing object must be small enough to slip into the vent.)"
        )
    if perch.risk < RISK_MIN:
        return (
            f"(No story: {perch.phrase} is too steady. This mystery needs a risky perch so one impatient move can cause the loss.)"
        )
    return "(No story: this combination does not support the mystery's accident.)"


ASP_RULES = r"""
small(Item) :- item(Item), tiny(Item).
risky(Perch) :- perch(Perch), risk(Perch, R), risk_min(M), R >= M.
valid(Room, Item, Perch) :- room(Room), vent_below(Room), small(Item), risky(Perch).
outcome(lost) :- chosen_room(Room), chosen_item(Item), chosen_perch(Perch),
                 valid(Room, Item, Perch).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        if room.vent_below_shelf:
            lines.append(asp.fact("vent_below", room_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.tiny:
            lines.append(asp.fact("tiny", item_id))
    for perch_id, perch in PERCHES.items():
        lines.append(asp.fact("perch", perch_id))
        lines.append(asp.fact("risk", perch_id, perch.risk))
    lines.append(asp.fact("risk_min", RISK_MIN))
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
            asp.fact("chosen_room", params.room),
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_perch", params.perch),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "none"


def outcome_of(params: StoryParams) -> str:
    return "lost" if valid_combo(ROOMS[params.room], ITEMS[params.item], PERCHES[params.perch]) else "none"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py:
            print("  only in clingo:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print("MISMATCH in outcome:", params)
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.story_qa or not sample.world_qa:
            raise StoryError("Smoke test produced an incomplete sample.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld with a bad ending: a child changes the position of furniture, climbs, and loses the missing object."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.room and args.item and args.perch:
        room = ROOMS[args.room]
        item = ITEMS[args.item]
        perch = PERCHES[args.perch]
        if not valid_combo(room, item, perch):
            raise StoryError(explain_rejection(room, item, perch))

    combos = [
        combo
        for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.item is None or combo[1] == args.item)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, item_id, perch_id = rng.choice(sorted(combos))
    clue_id = args.clue or rng.choice(sorted(CLUES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        room=room_id,
        item=item_id,
        clue=clue_id,
        perch=perch_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.perch not in PERCHES:
        raise StoryError(f"(Unknown perch: {params.perch})")
    if not valid_combo(ROOMS[params.room], ITEMS[params.item], PERCHES[params.perch]):
        raise StoryError(explain_rejection(ROOMS[params.room], ITEMS[params.item], PERCHES[params.perch]))

    world = tell(
        room=ROOMS[params.room],
        item=ITEMS[params.item],
        clue=CLUES[params.clue],
        perch_cfg=PERCHES[params.perch],
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (room, item, perch) combos:\n")
        for room_id, item_id, perch_id in combos:
            print(f"  {room_id:14} {item_id:10} {perch_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.item} in {p.room} ({p.perch})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
