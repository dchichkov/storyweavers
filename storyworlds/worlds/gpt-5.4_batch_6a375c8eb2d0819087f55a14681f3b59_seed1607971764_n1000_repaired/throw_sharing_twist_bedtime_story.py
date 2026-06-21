#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/throw_sharing_twist_bedtime_story.py
===============================================================

A standalone storyworld for gentle bedtime stories about **sharing** with a small
state-driven **twist**: a child thinks a bedtime treasure belongs to only one
sleepy person, tries to solve the problem by trying to throw some other object
across the room instead, and then learns that the treasured thing works best
when shared.

The domain is deliberately small and classical:

* Two children are settling down at night.
* One child has a beloved bedtime treasure.
* The other child has a real bedtime need: warmth, light, or calm.
* The owner does not want to share and tries an inadequate throw-instead move.
* A grown-up notices the mismatch and reveals the twist:
  the very thing that seemed "just mine" can help both children at once.
* The room softens, the children share, and the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/throw_sharing_twist_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/throw_sharing_twist_bedtime_story.py --room attic_nook --worry dark
    python storyworlds/worlds/gpt-5.4/throw_sharing_twist_bedtime_story.py --treasure moon_quilt
    python storyworlds/worlds/gpt-5.4/throw_sharing_twist_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/throw_sharing_twist_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/throw_sharing_twist_bedtime_story.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Room:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)
    opening: str = ""
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
class Worry:
    id: str
    label: str
    need_kind: str
    cue: str
    complaint: str
    symptom: str
    solved_by: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    supports: str
    bedtime_use: str
    share_action: str
    twist: str
    ending: str
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
class ThrowThing:
    id: str
    label: str
    phrase: str
    landing: str
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
    def __init__(self, room: Room) -> None:
        self.room_cfg = room
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
        clone = World(self.room_cfg)
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


def comfort_meter_name(kind: str) -> str:
    return {"warmth": "warmth", "light": "light", "calm": "calm"}[kind]


def room_meter_name(kind: str) -> str:
    return {"warmth": "cold", "light": "dark", "calm": "noise"}[kind]


def comfort_fail_sentence(worry: Worry, throw_item: ThrowThing) -> str:
    if worry.need_kind == "warmth":
        return (
            f"But {throw_item.phrase} could not warm shoulders, knees, and toes. "
            f"{worry.symptom}"
        )
    if worry.need_kind == "light":
        return (
            f"But {throw_item.phrase} could not make the room bright. "
            f"{worry.symptom}"
        )
    return (
        f"But {throw_item.phrase} could not hush the noisy night. "
        f"{worry.symptom}"
    )


def _r_unsettled(world: World) -> list[str]:
    guest = world.get("guest")
    room = world.get("room")
    need_kind = world.facts["need_kind"]
    need_meter = comfort_meter_name(need_kind)
    room_meter = room_meter_name(need_kind)
    if guest.memes["worry"] < THRESHOLD:
        return []
    if guest.meters[need_meter] >= THRESHOLD:
        return []
    sig = ("unsettled", need_kind, int(guest.memes["worry"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guest.memes["tears"] += 1
    room.meters["wakefulness"] += 1
    room.meters[room_meter] += 0
    return ["__unsettled__"]


def _r_thrown_fails(world: World) -> list[str]:
    thrown = world.get("throw_item")
    if thrown.meters["thrown"] < THRESHOLD:
        return []
    need_kind = world.facts["need_kind"]
    if need_kind in set(thrown.attrs.get("supports", set())):
        return []
    sig = ("thrown_fails", need_kind, thrown.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guest = world.get("guest")
    owner = world.get("owner")
    guest.memes["disappointment"] += 1
    owner.memes["distance"] += 1
    return ["__throw_fail__"]


def _r_shared_helps(world: World) -> list[str]:
    treasure = world.get("treasure")
    if treasure.meters["shared"] < THRESHOLD:
        return []
    need_kind = world.facts["need_kind"]
    if treasure.attrs.get("supports") != need_kind:
        return []
    sig = ("shared_helps", need_kind, treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner = world.get("owner")
    guest = world.get("guest")
    room = world.get("room")
    meter = comfort_meter_name(need_kind)
    guest.meters[meter] += 1
    owner.meters[meter] += 1
    guest.memes["worry"] = 0.0
    guest.memes["tears"] = 0.0
    owner.memes["possessive"] = 0.0
    owner.memes["generous"] += 1
    guest.memes["relief"] += 1
    owner.memes["relief"] += 1
    owner.memes["closeness"] += 1
    guest.memes["closeness"] += 1
    room.meters["wakefulness"] = 0.0
    room.meters["cozy"] += 1
    world.facts["shared_success"] = True
    return ["__shared__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="unsettled", tag="emotion", apply=_r_unsettled),
    Rule(name="thrown_fails", tag="emotion", apply=_r_thrown_fails),
    Rule(name="shared_helps", tag="social", apply=_r_shared_helps),
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


ROOMS = {
    "shared_bedroom": Room(
        id="shared_bedroom",
        label="shared bedroom",
        phrase="their small shared bedroom",
        affords={"cold", "dark"},
        opening="A sleepy lamp glowed low in their small shared bedroom.",
        tags={"bedroom"},
    ),
    "attic_nook": Room(
        id="attic_nook",
        label="attic nook",
        phrase="the little attic nook",
        affords={"dark", "thunder"},
        opening="The little attic nook tucked itself under the roof like a nest.",
        tags={"bedroom", "attic"},
    ),
    "guest_room": Room(
        id="guest_room",
        label="guest room",
        phrase="the guest room at Grandma's house",
        affords={"cold", "thunder"},
        opening="At Grandma's house, the guest room felt hushed and full of blankets.",
        tags={"bedroom", "grandma"},
    ),
}

WORRIES = {
    "cold": Worry(
        id="cold",
        label="cold",
        need_kind="warmth",
        cue="a silver draft slipped around the window frame",
        complaint="My feet feel cold.",
        symptom="The smaller child tucked chilly feet under the sheet and still could not get cozy.",
        solved_by="warmth",
        tags={"cold"},
    ),
    "dark": Worry(
        id="dark",
        label="dark",
        need_kind="light",
        cue="the room looked bigger and blacker after the lamp clicked off",
        complaint="The corners look too dark.",
        symptom="The shadows stayed in the corners, and the smaller child kept peeking over the blanket.",
        solved_by="light",
        tags={"dark"},
    ),
    "thunder": Worry(
        id="thunder",
        label="thunder",
        need_kind="calm",
        cue="soft thunder rolled across the roof",
        complaint="The thunder is too loud.",
        symptom="Each rumble made the smaller child squeeze the sheet in two worried fists.",
        solved_by="calm",
        tags={"thunder"},
    ),
}

TREASURES = {
    "moon_quilt": Treasure(
        id="moon_quilt",
        label="moon quilt",
        phrase="a moon-stitched quilt",
        supports="warmth",
        bedtime_use="liked to tuck the moon quilt right under the chin",
        share_action="spread the moon quilt wide so it covered both children from shoulders to toes",
        twist="it was much wider than one sleepy child needed",
        ending="Soon two quiet lumps rested under one moon quilt, warm clear to their toes.",
        tags={"blanket", "warmth", "sharing"},
    ),
    "star_lantern": Treasure(
        id="star_lantern",
        label="star lantern",
        phrase="a small star lantern with tiny holes in it",
        supports="light",
        bedtime_use="liked to watch little stars blink through the lantern lid",
        share_action="set the star lantern on the stool between the beds so both pillows glowed with soft pinprick stars",
        twist="its light was never meant for only one pillow",
        ending="Soon both beds were under the same gentle star-shine, and the room looked small and friendly again.",
        tags={"light", "sharing", "stars"},
    ),
    "lullaby_book": Treasure(
        id="lullaby_book",
        label="lullaby book",
        phrase="a thick lullaby book with a cloth cover",
        supports="calm",
        bedtime_use="liked to keep a thumb tucked in the favorite lullaby page",
        share_action="open the lullaby book and read in a slow whisper that curled all the way to the second bed",
        twist="a bedtime story can wrap around everyone who listens",
        ending="Soon the thunder was only far-away grumbling outside, while the lullaby words floated softly over both beds.",
        tags={"book", "calm", "sharing"},
    ),
}

THROW_ITEMS = {
    "pillow": ThrowThing(
        id="pillow",
        label="pillow",
        phrase="a little pillow",
        landing="It bounced once and leaned against the blanket chest.",
        tags={"pillow"},
    ),
    "plush_mouse": ThrowThing(
        id="plush_mouse",
        label="plush mouse",
        phrase="a tiny plush mouse",
        landing="It landed with a soft plop by the rug.",
        tags={"toy"},
    ),
    "sock_ball": ThrowThing(
        id="sock_ball",
        label="sock ball",
        phrase="a rolled-up pair of socks",
        landing="The sock ball made a silly hop and then was still.",
        tags={"socks"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Eli", "Theo"]
TRAITS = ["gentle", "sleepy", "curious", "careful", "soft-hearted", "stubborn"]


@dataclass
class StoryParams:
    room: str
    worry: str
    treasure: str
    throw_item: str
    owner: str
    owner_gender: str
    guest: str
    guest_gender: str
    caregiver: str
    owner_trait: str
    relation: str = "siblings"
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


def room_allows(room_id: str, worry_id: str) -> bool:
    return worry_id in ROOMS[room_id].affords


def treasure_solves(worry_id: str, treasure_id: str) -> bool:
    return WORRIES[worry_id].need_kind == TREASURES[treasure_id].supports


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for room_id, room in ROOMS.items():
        for worry_id in sorted(room.affords):
            for treasure_id in TREASURES:
                if not treasure_solves(worry_id, treasure_id):
                    continue
                for throw_id in THROW_ITEMS:
                    combos.append((room_id, worry_id, treasure_id, throw_id))
    return combos


def explain_rejection(room_id: str, worry_id: str, treasure_id: str) -> str:
    if not room_allows(room_id, worry_id):
        room = ROOMS[room_id]
        worry = WORRIES[worry_id]
        allowed = ", ".join(sorted(room.affords))
        return (
            f"(No story: {room.label} does not fit the bedtime problem '{worry.label}' here. "
            f"That room supports worries about {allowed}.)"
        )
    if not treasure_solves(worry_id, treasure_id):
        worry = WORRIES[worry_id]
        treasure = TREASURES[treasure_id]
        return (
            f"(No story: {treasure.label} gives {treasure.supports}, but the worry '{worry.label}' "
            f"needs {worry.solved_by}. Pick a treasure that honestly helps.)"
        )
    return "(No story: this combination does not make sense in the bedtime world.)"


def predict_shared_comfort(world: World) -> dict:
    sim = world.copy()
    sim.get("treasure").meters["shared"] += 1
    propagate(sim, narrate=False)
    guest = sim.get("guest")
    need_kind = sim.facts["need_kind"]
    need_meter = comfort_meter_name(need_kind)
    return {
        "settled": guest.meters[need_meter] >= THRESHOLD and guest.memes["worry"] < THRESHOLD,
        "cozy": sim.get("room").meters["cozy"],
    }


def introduce(world: World, owner: Entity, guest: Entity, treasure: Treasure, relation: str) -> None:
    together = "brother and sister" if relation == "siblings" and owner.type != guest.type else (
        "two sisters" if relation == "siblings" and owner.type == "girl" else
        "two brothers" if relation == "siblings" and owner.type == "boy" else
        "two friends"
    )
    world.say(
        f"{world.room_cfg.opening} {owner.id} and {guest.id} were {together}, and bedtime was almost ready to begin."
    )
    world.say(
        f"{owner.id} had {treasure.phrase} and {treasure.bedtime_use}. "
        f"It felt like the very best part of settling down."
    )


def trouble_begins(world: World, guest: Entity, worry: Worry) -> None:
    world.say(
        f"But tonight, {worry.cue}. From the second bed, {guest.id} whispered, "
        f'"{worry.complaint}"'
    )
    guest.memes["worry"] += 1
    propagate(world, narrate=False)


def refuse_and_throw(world: World, owner: Entity, guest: Entity, treasure: Treasure, throw_item: ThrowThing) -> None:
    owner.memes["possessive"] += 1
    world.say(
        f"{owner.id} hugged the {treasure.label} close. "
        f'"But it is mine," {owner.pronoun()} said in a small tight voice.'
    )
    world.say(
        f'Then {owner.pronoun()} tried to fix everything without sharing. '
        f'"I can throw you {throw_item.phrase} instead," {owner.pronoun()} said.'
    )
    world.get("throw_item").meters["thrown"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} gave it a quick throw across the room. {throw_item.landing}"
    )


def throw_does_not_help(world: World, guest: Entity, worry: Worry, throw_item: ThrowThing) -> None:
    world.say(comfort_fail_sentence(worry, throw_item))
    guest.memes["worry"] += 1
    propagate(world, narrate=False)


def caregiver_turn(world: World, caregiver: Entity, owner: Entity, guest: Entity, treasure: Treasure) -> None:
    pred = predict_shared_comfort(world)
    world.facts["predicted_settled"] = pred["settled"]
    world.say(
        f"{caregiver.label_word.capitalize()} came to the doorway and listened for a moment."
    )
    world.say(
        f'"The funny thing about the {treasure.label}," {caregiver.pronoun()} said softly, '
        f'"is that {treasure.twist}."'
    )
    world.say(
        f"{caregiver.pronoun().capitalize()} looked at {owner.id}, then at {guest.id}, and smiled. "
        f'"Maybe the {treasure.label} is not smaller when it is shared. Maybe it gets bigger in the room."'
    )


def share_treasure(world: World, owner: Entity, guest: Entity, treasure: Treasure) -> None:
    world.get("treasure").meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{owner.id} blinked, scooted over, and let {guest.id} come close. Together they {treasure.share_action}."
    )
    world.say(
        f"The room changed at once. {guest.id}'s worried face softened, and {owner.id} felt the tight little knot in {owner.pronoun('possessive')} chest come loose."
    )


def settle_end(world: World, owner: Entity, guest: Entity, caregiver: Entity, treasure: Treasure) -> None:
    owner.memes["sleepy"] += 1
    guest.memes["sleepy"] += 1
    world.say(
        f'"That is better," whispered {guest.id}. "{treasure.label.capitalize()} can be for both of us."'
    )
    world.say(
        f"{owner.id} nodded. {caregiver.label_word.capitalize()} tucked the blankets and kissed both foreheads."
    )
    world.say(treasure.ending)


def tell(
    room_cfg: Room,
    worry_cfg: Worry,
    treasure_cfg: Treasure,
    throw_cfg: ThrowThing,
    owner_name: str = "Lily",
    owner_gender: str = "girl",
    guest_name: str = "Ben",
    guest_gender: str = "boy",
    caregiver_type: str = "mother",
    owner_trait: str = "gentle",
    relation: str = "siblings",
) -> World:
    world = World(room_cfg)
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        traits=[owner_trait],
    ))
    guest = world.add(Entity(
        id=guest_name,
        kind="character",
        type=guest_gender,
        role="guest",
        traits=["sleepy"],
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=caregiver_type,
        role="caregiver",
        label="the grown-up",
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=room_cfg.label,
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        attrs={"supports": treasure_cfg.supports, "tags": set(treasure_cfg.tags)},
    ))
    throw_item = world.add(Entity(
        id="throw_item",
        kind="thing",
        type="throw_item",
        label=throw_cfg.label,
        phrase=throw_cfg.phrase,
        attrs={"supports": set(), "tags": set(throw_cfg.tags)},
    ))

    world.facts.update(
        room=room_cfg,
        worry=worry_cfg,
        treasure_cfg=treasure_cfg,
        throw_cfg=throw_cfg,
        owner=owner,
        guest=guest,
        caregiver=caregiver,
        relation=relation,
        need_kind=worry_cfg.need_kind,
        shared_success=False,
        predicted_settled=False,
    )

    room.meters[room_meter_name(worry_cfg.need_kind)] += 1
    owner.meters[comfort_meter_name(treasure_cfg.supports)] += 1

    introduce(world, owner, guest, treasure_cfg, relation)
    trouble_begins(world, guest, worry_cfg)

    world.para()
    refuse_and_throw(world, owner, guest, treasure_cfg, throw_cfg)
    throw_does_not_help(world, guest, worry_cfg, throw_cfg)

    world.para()
    caregiver_turn(world, caregiver, owner, guest, treasure_cfg)
    share_treasure(world, owner, guest, treasure_cfg)
    settle_end(world, owner, guest, caregiver, treasure_cfg)

    world.facts.update(
        throw_attempted=world.get("throw_item").meters["thrown"] >= THRESHOLD,
        guest_was_worried=True,
        ended_shared=world.get("treasure").meters["shared"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "cold": [
        (
            "Why do children sometimes feel colder at night?",
            "At night, rooms can cool down and bodies are lying still instead of running around. That can make hands and feet feel chilly under a thin blanket."
        )
    ],
    "dark": [
        (
            "Why can a room look scary in the dark?",
            "In the dark, shapes are harder to see clearly, so corners and coats can look strange. A gentle light helps your eyes understand the room again."
        )
    ],
    "thunder": [
        (
            "What is thunder?",
            "Thunder is the big rumbling sound that can happen during a storm. It can sound loud indoors, even when the storm is far away."
        )
    ],
    "blanket": [
        (
            "How can a blanket help at bedtime?",
            "A blanket holds warmth close to your body. When you feel warm, it is easier to relax and settle down."
        )
    ],
    "light": [
        (
            "Why does a little light help at bedtime?",
            "A little light lets you see where things are and reminds you that the room is safe. Soft light can feel calmer than a pitch-black room."
        )
    ],
    "book": [
        (
            "How can a bedtime story help someone feel calm?",
            "A bedtime story gives your mind something gentle to follow. Listening to slow, cozy words can make your breathing and feelings settle down."
        )
    ],
    "sharing": [
        (
            "Why can sharing make bedtime easier?",
            "Sharing can help two children feel close instead of alone. When someone lets you join in their comfort, the whole room can feel softer."
        )
    ],
}
KNOWLEDGE_ORDER = ["cold", "dark", "thunder", "blanket", "light", "book", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    guest = f["guest"]
    worry = f["worry"]
    treasure = f["treasure_cfg"]
    throw_cfg = f["throw_cfg"]
    return [
        (
            f'Write a bedtime story for a 3-to-5-year-old where one child tries to throw '
            f'{throw_cfg.phrase} instead of sharing {treasure.phrase}, but learns to share in the end.'
        ),
        (
            f"Tell a gentle night-time story where {guest.id} worries about the {worry.label}, "
            f"{owner.id} does not want to share {owner.pronoun('possessive')} {treasure.label}, "
            f"and a grown-up reveals a soft twist."
        ),
        (
            f'Write a cozy story with the word "throw" in it, built around sharing, a bedtime problem, '
            f"and the discovery that the {treasure.label} can comfort two children at once."
        ),
    ]


def relation_phrase(owner: Entity, guest: Entity, relation: str) -> str:
    if relation == "friends":
        return "two friends"
    if owner.type == guest.type == "girl":
        return "two sisters"
    if owner.type == guest.type == "boy":
        return "two brothers"
    return "a brother and a sister"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    guest = f["guest"]
    caregiver = f["caregiver"]
    worry = f["worry"]
    treasure = f["treasure_cfg"]
    throw_cfg = f["throw_cfg"]
    relation = f["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {relation_phrase(owner, guest, relation)}, {owner.id} and {guest.id}, at bedtime. {caregiver.label_word.capitalize()} helps them when the room stops feeling peaceful."
        ),
        (
            f"What was worrying {guest.id}?",
            f"{guest.id} was worried about the {worry.label}. {worry.symptom}"
        ),
        (
            f"Why did {owner.id} try to throw {throw_cfg.phrase} instead of sharing the {treasure.label}?",
            f"{owner.id} wanted to keep the {treasure.label} all to {owner.pronoun('object')}. Throwing {throw_cfg.phrase} seemed like a way to help without giving up something precious."
        ),
        (
            f"Did the thing {owner.id} threw solve the problem?",
            f"No. {comfort_fail_sentence(worry, throw_cfg)} That is why the bedtime trouble was still there after the throw."
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the {treasure.label} was not really a one-child comfort after all. {treasure.twist.capitalize()}, so sharing it helped both children at the same time."
        ),
        (
            "How did the story end?",
            f"{owner.id} shared the {treasure.label}, and {guest.id} finally settled. The ending image shows the room itself becoming softer and safer once they shared."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["worry"].tags) | {"sharing"}
    treasure = f["treasure_cfg"]
    if treasure.id == "moon_quilt":
        tags.add("blanket")
    elif treasure.id == "star_lantern":
        tags.add("light")
    elif treasure.id == "lullaby_book":
        tags.add("book")
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
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="guest_room",
        worry="cold",
        treasure="moon_quilt",
        throw_item="pillow",
        owner="Lily",
        owner_gender="girl",
        guest="Ben",
        guest_gender="boy",
        caregiver="mother",
        owner_trait="gentle",
        relation="siblings",
    ),
    StoryParams(
        room="attic_nook",
        worry="dark",
        treasure="star_lantern",
        throw_item="plush_mouse",
        owner="Max",
        owner_gender="boy",
        guest="Nora",
        guest_gender="girl",
        caregiver="father",
        owner_trait="stubborn",
        relation="friends",
    ),
    StoryParams(
        room="attic_nook",
        worry="thunder",
        treasure="lullaby_book",
        throw_item="sock_ball",
        owner="Zoe",
        owner_gender="girl",
        guest="Sam",
        guest_gender="boy",
        caregiver="mother",
        owner_trait="soft-hearted",
        relation="siblings",
    ),
    StoryParams(
        room="shared_bedroom",
        worry="dark",
        treasure="star_lantern",
        throw_item="pillow",
        owner="Theo",
        owner_gender="boy",
        guest="Eli",
        guest_gender="boy",
        caregiver="father",
        owner_trait="careful",
        relation="siblings",
    ),
]


ASP_RULES = r"""
need_kind(cold,warmth).
need_kind(dark,light).
need_kind(thunder,calm).

valid(Room,Worry,Treasure,Throw) :-
    room(Room),
    affords(Room,Worry),
    treasure(Treasure),
    throw_item(Throw),
    need_kind(Worry,Kind),
    supports(Treasure,Kind).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for worry_id in sorted(room.affords):
            lines.append(asp.fact("affords", room_id, worry_id))
    for worry_id in WORRIES:
        lines.append(asp.fact("worry", worry_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        lines.append(asp.fact("supports", treasure_id, treasure.supports))
    for throw_id in THROW_ITEMS:
        lines.append(asp.fact("throw_item", throw_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_params = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        resolved = resolve_params(default_args, random.Random(123))
        smoke_params.append(resolved)
    except StoryError as err:
        rc = 1
        print("SMOKE TEST FAILED during resolve_params():", err)
        smoke_params = list(CURATED)

    for params in smoke_params[:3]:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated story was empty")
            with contextlib.redirect_stdout(io.StringIO()):
                emit(sample, trace=True, qa=True, header="smoke")
        except Exception as err:  # noqa: BLE001
            rc = 1
            print(f"SMOKE TEST FAILED for {params}: {err}")
            break
    else:
        print("OK: generate()/emit() smoke test passed.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime sharing storyworld with a throw-first mistake and a soft twist."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--throw-item", choices=THROW_ITEMS, dest="throw_item")
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.worry and not room_allows(args.room, args.worry):
        treasure_id = args.treasure or next(iter(TREASURES))
        raise StoryError(explain_rejection(args.room, args.worry, treasure_id))
    if args.worry and args.treasure:
        room_id = args.room or next(iter(ROOMS))
        if not treasure_solves(args.worry, args.treasure):
            raise StoryError(explain_rejection(room_id, args.worry, args.treasure))

    combos = [
        combo for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.worry is None or combo[1] == args.worry)
        and (args.treasure is None or combo[2] == args.treasure)
        and (args.throw_item is None or combo[3] == args.throw_item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, worry_id, treasure_id, throw_id = rng.choice(sorted(combos))
    owner_gender = rng.choice(["girl", "boy"])
    guest_gender = rng.choice(["girl", "boy"])
    owner_name = _pick_name(rng, owner_gender)
    guest_name = _pick_name(rng, guest_gender, avoid=owner_name)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    owner_trait = rng.choice(TRAITS)
    return StoryParams(
        room=room_id,
        worry=worry_id,
        treasure=treasure_id,
        throw_item=throw_id,
        owner=owner_name,
        owner_gender=owner_gender,
        guest=guest_name,
        guest_gender=guest_gender,
        caregiver=caregiver,
        owner_trait=owner_trait,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.worry not in WORRIES:
        raise StoryError(f"(Unknown worry: {params.worry})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.throw_item not in THROW_ITEMS:
        raise StoryError(f"(Unknown throw item: {params.throw_item})")
    if params.caregiver not in {"mother", "father"}:
        raise StoryError(f"(Unknown caregiver type: {params.caregiver})")
    if params.relation not in {"siblings", "friends"}:
        raise StoryError(f"(Unknown relation: {params.relation})")
    if not room_allows(params.room, params.worry) or not treasure_solves(params.worry, params.treasure):
        raise StoryError(explain_rejection(params.room, params.worry, params.treasure))

    world = tell(
        room_cfg=ROOMS[params.room],
        worry_cfg=WORRIES[params.worry],
        treasure_cfg=TREASURES[params.treasure],
        throw_cfg=THROW_ITEMS[params.throw_item],
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        guest_name=params.guest,
        guest_gender=params.guest_gender,
        caregiver_type=params.caregiver,
        owner_trait=params.owner_trait,
        relation=params.relation,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, worry, treasure, throw_item) combos:\n")
        for room_id, worry_id, treasure_id, throw_id in combos:
            print(f"  {room_id:14} {worry_id:8} {treasure_id:13} {throw_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.owner} & {p.guest}: {p.worry} in {p.room} ({p.treasure})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
