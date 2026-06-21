#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drunk_wire_surprise_problem_solving_detective_story.py
=================================================================================

A standalone story world for a tiny child-facing detective story: a child
detective prepares a surprise welcome, but a wire problem stops an important
signal from working. The detective follows clues, forms a simple explanation,
asks a grown-up for help, and the surprise succeeds.

Seed words required by the prompt:
- drunk
- wire

The world models a few small mystery cases in the same family shape:

    setup a surprise
    something technical stops it
    clues point to a physical cause
    the child detective reasons it out
    a grown-up helps with the safe fix
    the surprise works after all

The core constraint is simple and explicit:
- a chosen repair must actually fit the break type
- some machine/break pairs are unreasonable and refused
- the child never performs the risky repair alone; the adult helps

Like other storyworlds, this script includes:
- a Python reasonableness gate
- an inline ASP twin for parity checking
- world-state-driven prose
- prompts + story-grounded QA + world-knowledge QA
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/ to path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


# ---------------------------------------------------------------------------
# Shared entity model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
@dataclass
class Venue:
    id: str
    place: str
    hideout: str
    arrival: str
    floor_mark: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    signal: str
    purpose: str
    wire_name: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BreakType:
    id: str
    label: str
    visible: str
    sound: str
    cause_text: str
    clue_text: str
    needs: str
    severity: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    text: str
    suspect: str
    points_to: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    sense: int
    fixes: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Forward rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_problem_blocks_signal(world: World) -> list[str]:
    device = world.get("device")
    if device.meters["broken"] < THRESHOLD:
        return []
    sig = ("problem_blocks_signal", "device")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    device.meters["signal_working"] = 0.0
    world.get("surprise").meters["at_risk"] += 1
    detective = world.get("detective")
    helper = world.get("helper")
    detective.memes["worry"] += 1
    helper.memes["worry"] += 1
    return []


def _r_collecting_clues_builds_theory(world: World) -> list[str]:
    detective = world.get("detective")
    if detective.meters["clues_seen"] < 2:
        return []
    sig = ("collecting_clues_builds_theory", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["focus"] += 1
    detective.memes["confidence"] += 1
    return []


def _r_good_repair_restores_signal(world: World) -> list[str]:
    device = world.get("device")
    if device.meters["repair_match"] < THRESHOLD:
        return []
    sig = ("good_repair_restores_signal", device.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    device.meters["broken"] = 0.0
    device.meters["signal_working"] = 1.0
    world.get("surprise").meters["at_risk"] = 0.0
    detective = world.get("detective")
    helper = world.get("helper")
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="problem_blocks_signal", tag="physical", apply=_r_problem_blocks_signal),
    Rule(name="collecting_clues_builds_theory", tag="mental", apply=_r_collecting_clues_builds_theory),
    Rule(name="good_repair_restores_signal", tag="physical", apply=_r_good_repair_restores_signal),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraints / reasonableness
# ---------------------------------------------------------------------------
def break_possible(device: Device, break_type: BreakType) -> bool:
    if device.id == "bell" and break_type.id == "empty_battery":
        return False
    if device.id == "string_lights" and break_type.id == "jammed_button":
        return False
    if device.id == "music_box" and break_type.id == "frayed_wire":
        return False
    return True


def repair_matches(break_type: BreakType, repair: Repair) -> bool:
    return break_type.id in repair.fixes


def sensible_repairs() -> list[Repair]:
    return [repair for repair in REPAIRS.values() if repair.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for venue_id in VENUES:
        for device_id, device in DEVICES.items():
            for break_id, break_type in BREAKS.items():
                if not break_possible(device, break_type):
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair.sense >= SENSE_MIN and repair_matches(break_type, repair):
                        for clue_id, clue in CLUES.items():
                            if break_id in clue.points_to:
                                combos.append((venue_id, device_id, break_id, repair_id, clue_id))
    return combos


def explain_break_rejection(device: Device, break_type: BreakType) -> str:
    return (
        f"(No story: {break_type.label} is not a sensible problem for {device.phrase}. "
        f"Pick a problem this device could really have.)"
    )


def explain_repair_rejection(break_type: BreakType, repair: Repair) -> str:
    return (
        f"(No story: {repair.label} does not solve {break_type.label}. "
        f"The fix must actually match the problem.)"
    )


def predict_success(world: World, break_type: BreakType, repair: Repair) -> dict:
    sim = world.copy()
    sim.get("device").meters["broken"] = float(break_type.severity)
    propagate(sim, narrate=False)
    if repair_matches(break_type, repair) and repair.sense >= SENSE_MIN:
        sim.get("device").meters["repair_match"] += 1
        propagate(sim, narrate=False)
    return {
        "working": sim.get("device").meters["signal_working"] >= THRESHOLD,
        "risk": sim.get("surprise").meters["at_risk"],
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, detective: Entity, helper: Entity, venue: Venue,
              device: Device, surprise_for: str) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"On the afternoon of the surprise, {detective.id} and {helper.id} crouched in "
        f"{venue.hideout} at {venue.place}. {detective.id} liked detective stories so much "
        f"that even tying ribbon felt like opening a case."
    )
    world.say(
        f"They were getting {device.phrase} ready so it could {device.signal} when "
        f"{surprise_for} arrived. That signal was the secret sign for everyone to jump out "
        f"and shout hello."
    )


def setup_surprise(world: World, device: Device, venue: Venue, surprise_for: str) -> None:
    surprise = world.get("surprise")
    surprise.meters["ready"] += 1
    world.say(
        f"In {venue.arrival}, paper stars waited, a cake hid under a cloth, and the room held its breath "
        f"for {surprise_for}. Everything depended on one small machine and its {device.wire_name}."
    )


def show_failure(world: World, device: Device, break_type: BreakType) -> None:
    device_ent = world.get("device")
    device_ent.meters["broken"] = float(break_type.severity)
    propagate(world, narrate=False)
    world.say(
        f"But when {world.get('helper').id} gave the test signal, nothing happened. "
        f"There was only {break_type.sound}."
    )
    world.say(
        f"{world.get('detective').id} narrowed {world.get('detective').pronoun('possessive')} eyes. "
        f'"A real detective does not panic," {world.get("detective").pronoun()} said. '
        f'"A real detective looks for clues."'
    )


def inspect_clue(world: World, detective: Entity, clue: Clue) -> None:
    detective.meters["clues_seen"] += 1
    world.facts.setdefault("clues_found", []).append(clue.id)
    propagate(world, narrate=False)
    world.say(clue.text)


def wrong_guess(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["suspicion"] += 1
    world.say(
        f"For one second, {detective.id} wondered if {clue.suspect} had ruined the surprise on purpose. "
        f"But the rest of the clues did not fit that idea."
    )


def special_drunk_clue(world: World, detective: Entity) -> None:
    detective.meters["clues_seen"] += 1
    world.facts.setdefault("clues_found", []).append("drunk_juice")
    propagate(world, narrate=False)
    world.say(
        f"Then {detective.id} spotted a tiny cup on its side and a wet ring beside it. "
        f'"The fern has drunk half the berry juice from the spill," {detective.pronoun()} murmured. '
        f'"So somebody bumped this table before the juice could dry."'
    )


def form_theory(world: World, detective: Entity, device: Device, break_type: BreakType) -> None:
    detective.memes["theory"] += 1
    world.facts["theory"] = break_type.id
    world.say(
        f"{detective.id} looked from the floor marks to the machine and then to the {device.wire_name}. "
        f'"I know it," {detective.pronoun()} said. "{break_type.cause_text} '
        f'That is why the signal stopped."'
    )


def ask_for_help(world: World, adult: Entity, detective: Entity, repair: Repair,
                 break_type: BreakType) -> None:
    adult.memes["calm"] += 1
    detective.memes["trust"] += 1
    pred = predict_success(world, break_type, repair)
    world.facts["predicted_success"] = pred["working"]
    world.say(
        f"{detective.id} did not touch the broken part alone. Instead, {detective.pronoun()} hurried to "
        f"{adult.label_word.capitalize()} and explained the case."
    )
    world.say(
        f'{adult.label_word.capitalize()} listened, checked the {world.get("device").label}, and nodded. '
        f'"Good detecting," {adult.pronoun()} said. "We will fix it safely together."'
    )


def repair_device(world: World, adult: Entity, repair: Repair) -> None:
    world.get("device").meters["repair_match"] += 1
    propagate(world, narrate=False)
    world.say(
        f"With careful hands, {adult.label_word} {repair.action}."
    )


def reveal_surprise(world: World, device: Device, surprise_for: str) -> None:
    world.say(
        f"This time the {device.label} worked at once. {device.signal.capitalize()}, and the hidden room burst open with laughter."
    )
    world.say(
        f"{surprise_for} blinked, gasped, and then smiled so wide that even the paper stars seemed brighter. "
        f"{world.get('detective').id} tucked the solved mystery into {world.get('detective').pronoun('possessive')} heart like a shiny badge."
    )


# ---------------------------------------------------------------------------
# Full screenplay
# ---------------------------------------------------------------------------
def tell(
    venue: Venue,
    device: Device,
    break_type: BreakType,
    repair: Repair,
    clue: Clue,
    *,
    detective_name: str = "Nora",
    detective_gender: str = "girl",
    helper_name: str = "Ben",
    helper_gender: str = "boy",
    adult_type: str = "mother",
    surprise_for: str = "Grandpa",
    pet: str = "the kitten",
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=["careful", "curious"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["eager"],
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the grown-up",
    ))
    world.add(Entity(
        id="device",
        kind="thing",
        type="device",
        label=device.label,
        phrase=device.phrase,
        tags=set(device.tags),
    ))
    world.add(Entity(
        id="surprise",
        kind="thing",
        type="surprise",
        label="surprise",
    ))
    world.facts["pet"] = pet

    introduce(world, detective, helper, venue, device, surprise_for)
    setup_surprise(world, device, venue, surprise_for)

    world.para()
    show_failure(world, device, break_type)
    inspect_clue(world, detective, clue)
    special_drunk_clue(world, detective)
    wrong_guess(world, detective, clue)
    world.say(
        f"Near the wall, {venue.floor_mark} led straight to the little table with the machine on it."
    )
    inspect_clue(
        world,
        detective,
        Clue(
            id="wire_seen",
            label="wire clue",
            text=f"{detective.id} lifted the cloth and found {break_type.visible} on the {device.wire_name}.",
            suspect="nobody",
            points_to={break_type.id},
            tags={"wire"},
        ),
    )
    form_theory(world, detective, device, break_type)

    world.para()
    ask_for_help(world, adult, detective, repair, break_type)
    repair_device(world, adult, repair)
    reveal_surprise(world, device, surprise_for)

    world.facts.update(
        venue=venue,
        device_cfg=device,
        break_cfg=break_type,
        repair_cfg=repair,
        clue_cfg=clue,
        detective=detective,
        helper=helper,
        adult=adult,
        surprise_for=surprise_for,
        solved=world.get("device").meters["signal_working"] >= THRESHOLD,
        safe_help=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
VENUES = {
    "hall": Venue(
        id="hall",
        place="the town hall",
        hideout="the coat room",
        arrival="the big front doorway",
        floor_mark="three dusty wheel lines",
        tags={"party"},
    ),
    "library": Venue(
        id="library",
        place="the little library",
        hideout="the story corner behind the puppet shelf",
        arrival="the quiet reading door",
        floor_mark="a ribbon trail and one crooked chair leg mark",
        tags={"library"},
    ),
    "greenhouse": Venue(
        id="greenhouse",
        place="the school greenhouse",
        hideout="the potting bench nook",
        arrival="the glass garden door",
        floor_mark="thin soil streaks by the watering table",
        tags={"garden"},
    ),
}

DEVICES = {
    "bell": Device(
        id="bell",
        label="bell",
        phrase="a bright brass bell button",
        signal="ring loudly",
        purpose="call everyone out",
        wire_name="bell wire",
        tags={"bell", "wire"},
    ),
    "string_lights": Device(
        id="string_lights",
        label="string lights",
        phrase="a string of star lights",
        signal="blink on in a shower of gold",
        purpose="light the surprise",
        wire_name="light wire",
        tags={"lights", "wire"},
    ),
    "music_box": Device(
        id="music_box",
        label="music box",
        phrase="a little welcome music box",
        signal="play a chirpy tune",
        purpose="start the song",
        wire_name="music wire",
        tags={"music", "wire"},
    ),
}

BREAKS = {
    "loose_wire": BreakType(
        id="loose_wire",
        label="a loose wire",
        visible="one wire dangling from its clip",
        sound="a stubborn silence",
        cause_text="The wire slipped loose when the table was bumped",
        clue_text="A wire has slipped away from where it belongs",
        needs="reattach",
        severity=1,
        tags={"wire"},
    ),
    "frayed_wire": BreakType(
        id="frayed_wire",
        label="a frayed wire",
        visible="the wire cover scraped and fuzzy at the edge",
        sound="a weak fizz and then nothing",
        cause_text="The wire was rubbed hard against the table leg until it frayed",
        clue_text="The wire has been worn rough and cannot work properly",
        needs="replace",
        severity=1,
        tags={"wire"},
    ),
    "empty_battery": BreakType(
        id="empty_battery",
        label="an empty battery",
        visible="a battery tray sitting open and tired",
        sound="one tiny click",
        cause_text="The battery had run out after too many test tries",
        clue_text="The power inside the battery is gone",
        needs="battery",
        severity=1,
        tags={"battery"},
    ),
    "jammed_button": BreakType(
        id="jammed_button",
        label="a jammed button",
        visible="the button stuck halfway down under dried juice",
        sound="a sticky little thunk",
        cause_text="Juice dried around the button and made it stick",
        clue_text="The button cannot spring up because it is sticky",
        needs="clean",
        severity=1,
        tags={"button"},
    ),
}

CLUES = {
    "wheel_marks": Clue(
        id="wheel_marks",
        label="wheel marks",
        text="On the floor, small wagon-wheel marks curved toward the table and away again.",
        suspect="the wagon",
        points_to={"loose_wire", "frayed_wire"},
        tags={"floor"},
    ),
    "sticky_ring": Clue(
        id="sticky_ring",
        label="sticky ring",
        text="Beside the machine was a purple sticky ring that still smelled like berry juice.",
        suspect="the spilled cup",
        points_to={"jammed_button"},
        tags={"juice"},
    ),
    "open_tray": Clue(
        id="open_tray",
        label="open tray",
        text="The little back flap stood open, as if someone had checked the battery tray and forgotten to shut it tight.",
        suspect="the open tray",
        points_to={"empty_battery"},
        tags={"battery"},
    ),
}

REPAIRS = {
    "reattach_wire": Repair(
        id="reattach_wire",
        label="reattaching the wire",
        sense=3,
        fixes={"loose_wire"},
        action="clipped the wire back into place and made sure it sat snug and safe",
        qa_text="clipped the loose wire back into place",
        tags={"wire", "repair"},
    ),
    "replace_wire": Repair(
        id="replace_wire",
        label="replacing the wire",
        sense=3,
        fixes={"frayed_wire"},
        action="removed the damaged wire and fitted a new safe one",
        qa_text="replaced the frayed wire with a new safe one",
        tags={"wire", "repair"},
    ),
    "new_battery": Repair(
        id="new_battery",
        label="putting in a new battery",
        sense=3,
        fixes={"empty_battery"},
        action="slid in a fresh battery and closed the little tray with a click",
        qa_text="put in a fresh battery",
        tags={"battery", "repair"},
    ),
    "clean_button": Repair(
        id="clean_button",
        label="cleaning the button",
        sense=2,
        fixes={"jammed_button"},
        action="wiped away the sticky dried juice until the button bounced back happily",
        qa_text="cleaned the sticky button",
        tags={"button", "repair"},
    ),
    "shake_it": Repair(
        id="shake_it",
        label="shaking the machine",
        sense=1,
        fixes=set(),
        action="gave the machine a hard shake",
        qa_text="shook the machine",
        tags={"bad_fix"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Theo"]
SURPRISE_FOR = ["Grandpa", "Grandma", "the new librarian", "Coach Ada"]
PETS = ["the kitten", "the puppy", "the rabbit", "the turtle"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    venue: str
    device: str
    break_type: str
    repair: str
    clue: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    adult: str
    surprise_for: str
    pet: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "wire": [
        (
            "What does a wire do?",
            "A wire carries power or signals from one part of a machine to another. If the wire is loose or damaged, the machine may stop working."
        )
    ],
    "battery": [
        (
            "What does a battery do?",
            "A battery stores energy that some small machines use. When the battery is empty, the machine may click weakly or not work at all."
        )
    ],
    "button": [
        (
            "Why can a sticky button stop a machine?",
            "A button needs to move in and out. If sticky juice dries around it, the button can get stuck and the machine may not start."
        )
    ],
    "repair": [
        (
            "Why should a child ask a grown-up for help with a broken machine?",
            "A grown-up can check the problem safely and use the right fix. Asking for help is smart problem solving, not giving up."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues, thinks carefully, and tries to explain what happened. Good detectives do not just guess; they compare clues and look for what fits."
        )
    ],
    "surprise": [
        (
            "What makes a surprise party a surprise?",
            "People keep the plan secret until the special person arrives. Then everyone reveals the hidden decorations or greeting at the right moment."
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a clear ringing sound that can tell people it is time to come in, look up, or pay attention."
        )
    ],
    "lights": [
        (
            "Why are lights useful at a celebration?",
            "Lights help a place feel bright and special. They can also be the signal that tells everyone the surprise has begun."
        )
    ],
    "music": [
        (
            "What does a music box do?",
            "A music box plays a tune. In a story, that tune can be a cheerful signal that something special is starting."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "surprise", "wire", "battery", "button", "repair", "bell", "lights", "music"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    device = f["device_cfg"]
    break_type = f["break_cfg"]
    return [
        f'Write a short detective story for a 3-to-5-year-old that includes the words "drunk" and "wire".',
        f"Tell a gentle mystery where {detective.id} is preparing a surprise, but {device.phrase} stops working because of {break_type.label}, and the clues lead to the answer.",
        f"Write a child-facing detective story with a surprise ending, a small broken machine, and a problem-solving child who asks a grown-up for the safe fix.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    adult = f["adult"]
    device = f["device_cfg"]
    break_type = f["break_cfg"]
    repair = f["repair_cfg"]
    surprise_for = f["surprise_for"]
    clue_ids = list(f.get("clues_found", []))
    clue_names: list[str] = []
    if "drunk_juice" in clue_ids:
        clue_names.append("the spilled juice ring")
    if "wire_seen" in clue_ids:
        clue_names.append("the wire itself")
    if f["clue_cfg"].id == "wheel_marks":
        clue_names.append("the wagon-wheel marks")
    elif f["clue_cfg"].id == "sticky_ring":
        clue_names.append("the sticky berry-juice ring")
    elif f["clue_cfg"].id == "open_tray":
        clue_names.append("the open battery tray")

    qas: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, {helper.id}, and a calm grown-up who helped them save a surprise for {surprise_for}."
        ),
        (
            "What problem did they have?",
            f"They needed {device.phrase} to {device.signal}, but it stopped working just before the surprise. That put the whole plan at risk because the signal was how everyone knew when to jump out."
        ),
        (
            f"How did {detective.id} act like a detective?",
            f"{detective.id} did not give up or just guess. {detective.pronoun().capitalize()} looked for clues, compared them, and used them to explain what had gone wrong."
        ),
        (
            "What clues helped solve the case?",
            f"The clues were {', '.join(clue_names)}. Together, those details pointed to {break_type.label} instead of a random guess."
        ),
        (
            f"Why is the word 'drunk' in the story?",
            f"{detective.id} noticed that the fern had drunk some of the spilled berry juice. That helped show the spill had happened earlier, which made the table-bumping clue easier to understand."
        ),
        (
            "How was the problem solved?",
            f"{detective.id} asked {adult.label_word} for help, and together they used the right fix: {repair.qa_text}. The machine worked again because the repair matched the real problem."
        ),
        (
            "How did the story end?",
            f"The signal worked, the hiding place burst open, and {surprise_for} was delighted. The ending proves the mystery was truly solved because the surprise could happen at exactly the right moment."
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "surprise", "repair"} | set(world.facts["device_cfg"].tags) | set(world.facts["break_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        venue="hall",
        device="bell",
        break_type="loose_wire",
        repair="reattach_wire",
        clue="wheel_marks",
        detective_name="Nora",
        detective_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        adult="mother",
        surprise_for="Grandpa",
        pet="the kitten",
    ),
    StoryParams(
        venue="library",
        device="music_box",
        break_type="empty_battery",
        repair="new_battery",
        clue="open_tray",
        detective_name="Mia",
        detective_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
        adult="father",
        surprise_for="the new librarian",
        pet="the rabbit",
    ),
    StoryParams(
        venue="greenhouse",
        device="string_lights",
        break_type="jammed_button",
        repair="clean_button",
        clue="sticky_ring",
        detective_name="Zoe",
        detective_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        adult="mother",
        surprise_for="Coach Ada",
        pet="the turtle",
    ),
    StoryParams(
        venue="hall",
        device="string_lights",
        break_type="frayed_wire",
        repair="replace_wire",
        clue="wheel_marks",
        detective_name="Ava",
        detective_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        adult="father",
        surprise_for="Grandma",
        pet="the puppy",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% device/break compatibility
possible(D, B) :- device(D), break(B), not impossible(D, B).

% repair compatibility
matches(B, R) :- break(B), repair(R), fixes(R, B).
sensible(R)   :- repair(R), sense(R, S), sense_min(M), S >= M.

% a clue is usable when it points to the chosen break
usable_clue(B, C) :- break(B), clue(C), points_to(C, B).

valid(V, D, B, R, C) :- venue(V), possible(D, B), sensible(R), matches(B, R), usable_clue(B, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id in VENUES:
        lines.append(asp.fact("venue", venue_id))
    for device_id in DEVICES:
        lines.append(asp.fact("device", device_id))
    for break_id in BREAKS:
        lines.append(asp.fact("break", break_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        for fix in sorted(repair.fixes):
            lines.append(asp.fact("fixes", repair_id, fix))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for point in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, point))
    for device_id, device in DEVICES.items():
        for break_id, break_type in BREAKS.items():
            if not break_possible(device, break_type):
                lines.append(asp.fact("impossible", device_id, break_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(item[0] for item in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: valid combos match ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = {repair.id for repair in sensible_repairs()}
    clingo_sensible = set(asp_sensible_repairs())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible repairs match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible repairs:")
        print("  python:", sorted(python_sensible))
        print("  clingo:", sorted(clingo_sensible))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "wire" not in sample.story.lower() or "drunk" not in sample.story.lower():
            raise StoryError("Smoke test story did not render expected seed words.")
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Child detective story world: a surprise, a clue trail, and a small machine problem solved safely."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--break-type", dest="break_type", choices=BREAKS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.device and args.break_type:
        device = DEVICES[args.device]
        break_type = BREAKS[args.break_type]
        if not break_possible(device, break_type):
            raise StoryError(explain_break_rejection(device, break_type))
    if args.break_type and args.repair:
        break_type = BREAKS[args.break_type]
        repair = REPAIRS[args.repair]
        if repair.sense < SENSE_MIN:
            raise StoryError(
                f"(No story: {repair.label} is not a sensible fix. Pick a repair that safely matches the problem.)"
            )
        if not repair_matches(break_type, repair):
            raise StoryError(explain_repair_rejection(break_type, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.device is None or combo[1] == args.device)
        and (args.break_type is None or combo[2] == args.break_type)
        and (args.repair is None or combo[3] == args.repair)
        and (args.clue is None or combo[4] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue, device, break_type, repair, clue = rng.choice(sorted(combos))
    detective_name, detective_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=detective_name)
    adult = args.adult or rng.choice(["mother", "father"])
    surprise_for = rng.choice(SURPRISE_FOR)
    pet = rng.choice(PETS)
    return StoryParams(
        venue=venue,
        device=device,
        break_type=break_type,
        repair=repair,
        clue=clue,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult=adult,
        surprise_for=surprise_for,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Invalid venue: {params.venue})")
    if params.device not in DEVICES:
        raise StoryError(f"(Invalid device: {params.device})")
    if params.break_type not in BREAKS:
        raise StoryError(f"(Invalid break type: {params.break_type})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Invalid repair: {params.repair})")
    if params.clue not in CLUES:
        raise StoryError(f"(Invalid clue: {params.clue})")
    if params.adult not in {"mother", "father"}:
        raise StoryError(f"(Invalid adult type: {params.adult})")

    device = DEVICES[params.device]
    break_type = BREAKS[params.break_type]
    repair = REPAIRS[params.repair]
    clue = CLUES[params.clue]

    if not break_possible(device, break_type):
        raise StoryError(explain_break_rejection(device, break_type))
    if repair.sense < SENSE_MIN:
        raise StoryError(f"(No story: {repair.label} is not a sensible repair.)")
    if not repair_matches(break_type, repair):
        raise StoryError(explain_repair_rejection(break_type, repair))
    if params.break_type not in clue.points_to:
        raise StoryError("(No story: the chosen clue does not honestly point to that problem.)")

    world = tell(
        VENUES[params.venue],
        device,
        break_type,
        repair,
        clue,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        surprise_for=params.surprise_for,
        pet=params.pet,
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
        print(asp_program("#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        print(f"{len(combos)} compatible (venue, device, break, repair, clue) combos:\n")
        for venue, device, break_type, repair, clue in combos:
            print(f"  {venue:10} {device:13} {break_type:14} {repair:15} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for idx, params in enumerate(CURATED):
            cp = StoryParams(**{**params.__dict__, "seed": base_seed + idx})
            samples.append(generate(cp))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.device} / {p.break_type} at {p.venue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
