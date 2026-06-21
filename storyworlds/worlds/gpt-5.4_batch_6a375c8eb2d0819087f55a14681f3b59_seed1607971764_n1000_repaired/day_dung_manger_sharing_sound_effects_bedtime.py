#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/day_dung_manger_sharing_sound_effects_bedtime.py
==============================================================================

A standalone story world for a gentle bedtime tale about two young barn friends
at the end of the day. One comes to the manger hungry but embarrassed because
some dung is stuck on them. The other notices, makes soft playful sound effects,
promises to share, and a calm caretaker helps clean the mess so both friends can
eat together and settle down for sleep.

The world is small on purpose: the important change is not a huge adventure, but
a shy child-like creature moving from hunger and embarrassment to comfort,
sharing, and rest.

Run it
------
    python storyworlds/worlds/gpt-5.4/day_dung_manger_sharing_sound_effects_bedtime.py
    python storyworlds/worlds/gpt-5.4/day_dung_manger_sharing_sound_effects_bedtime.py --spot hoof --tool hoof_brush
    python storyworlds/worlds/gpt-5.4/day_dung_manger_sharing_sound_effects_bedtime.py --spot tail --tool hoof_brush
    python storyworlds/worlds/gpt-5.4/day_dung_manger_sharing_sound_effects_bedtime.py --all
    python storyworlds/worlds/gpt-5.4/day_dung_manger_sharing_sound_effects_bedtime.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/day_dung_manger_sharing_sound_effects_bedtime.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing
    type: str = "thing"          # foal | calf | goat_kid | lamb | caretaker | food
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mare", "nanny", "hen"}
        male = {"boy", "man", "father", "stallion", "buck", "ram"}
        if self.attrs.get("gender") == "girl" or self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.attrs.get("gender") == "boy" or self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class AnimalKind:
    id: str
    child_word: str
    hoof_word: str
    night_sound: str
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
class MessSpot:
    id: str
    label: str
    on_phrase: str
    notice_text: str
    cleaner_tags: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    action_text: str
    cleans: set[str] = field(default_factory=set)
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
class Snack:
    id: str
    label: str
    phrase: str
    rustle: str
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
class CallStyle:
    id: str
    sound: str
    line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_shy_from_mess(world: World) -> list[str]:
    out: list[str] = []
    sleeper = world.get("sleeper")
    if sleeper.meters["dirty"] >= THRESHOLD and sleeper.memes["near_manger"] >= THRESHOLD:
        sig = ("shy_from_mess", sleeper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            sleeper.memes["embarrassed"] += 1
            out.append("__shy__")
    return out


def _r_tummy_rumble(world: World) -> list[str]:
    out: list[str] = []
    sleeper = world.get("sleeper")
    if sleeper.memes["hunger"] >= THRESHOLD and sleeper.memes["waiting"] >= THRESHOLD:
        sig = ("tummy_rumble", sleeper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            sleeper.meters["rumble"] += 1
            out.append("__rumble__")
    return out


def _r_share_comfort(world: World) -> list[str]:
    out: list[str] = []
    sleeper = world.get("sleeper")
    friend = world.get("friend")
    manger = world.get("manger")
    if sleeper.memes["invited"] >= THRESHOLD and sleeper.meters["dirty"] < THRESHOLD:
        sig = ("share_comfort", sleeper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            sleeper.memes["belonging"] += 1
            friend.memes["belonging"] += 1
            sleeper.meters["full"] += 1
            friend.meters["full"] += 1
            manger.meters["shared"] += 1
            out.append("__shared__")
    return out


CAUSAL_RULES = [
    Rule(name="shy_from_mess", tag="social", apply=_r_shy_from_mess),
    Rule(name="tummy_rumble", tag="physical", apply=_r_tummy_rumble),
    Rule(name="share_comfort", tag="social", apply=_r_share_comfort),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def tool_fits_spot(spot: MessSpot, tool: Tool) -> bool:
    return spot.id in tool.cleans and bool(spot.cleaner_tags & tool.tags)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for spot_id, spot in SPOTS.items():
        for tool_id, tool in TOOLS.items():
            if tool_fits_spot(spot, tool):
                combos.append((spot_id, tool_id))
    return combos


def explain_rejection(spot: MessSpot, tool: Tool) -> str:
    if spot.id not in tool.cleans:
        return (
            f"(No story: {tool.label} is not the right tool for mess on the {spot.label}. "
            f"A bedtime fix should clean the real problem, so choose a tool that fits that spot.)"
        )
    return (
        f"(No story: {tool.label} and {spot.label} do not share the same kind of gentle cleanup here.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, sleeper: Entity, friend: Entity, snack: Snack,
              sleeper_kind: AnimalKind, friend_kind: AnimalKind) -> None:
    sleeper.memes["sleepy"] += 1
    friend.memes["sleepy"] += 1
    world.say(
        f"At the end of the day, the barn had gone quiet and gold. "
        f"{sleeper.id}, a little {sleeper_kind.child_word}, and {friend.id}, a little "
        f"{friend_kind.child_word}, came in from the last soft light."
    )
    world.say(
        f"From the manger came a {snack.rustle}: {snack.phrase} waiting for supper."
    )


def arrive_messy(world: World, sleeper: Entity, spot: MessSpot) -> None:
    sleeper.meters["dirty"] = 1.0
    sleeper.memes["near_manger"] = 1.0
    sleeper.memes["waiting"] = 1.0
    sleeper.memes["hunger"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But {sleeper.id} stopped short. {spot.notice_text}, and a little bit of dung "
        f"still clung there after play."
    )
    if sleeper.memes["embarrassed"] >= THRESHOLD:
        world.say(
            f"{sleeper.pronoun().capitalize()} felt too shy to step close to the manger, "
            f"even though supper smelled warm and sweet."
        )
    if sleeper.meters["rumble"] >= THRESHOLD:
        world.say(
            f'Then {sleeper.pronoun("possessive")} tummy said, "grrr-rumble, grrr-rumble."'
        )


def notice_and_invite(world: World, sleeper: Entity, friend: Entity, call: CallStyle,
                      snack: Snack) -> None:
    friend.memes["kindness"] += 1
    sleeper.memes["heard_friend"] += 1
    world.say(
        f'{friend.id} lifted {friend.pronoun("possessive")} head and made a tiny sound: '
        f'"{call.sound}," {call.line}'
    )
    world.say(
        f'"There is room beside me," {friend.id} whispered. "We can share the {snack.label}."'
    )


def call_caretaker(world: World, caretaker: Entity, friend: Entity) -> None:
    world.say(
        f"{friend.id} gave one more soft call, and {caretaker.id}, the gentle "
        f"{caretaker.label_word}, looked into the stall."
    )


def clean_mess(world: World, sleeper: Entity, caretaker: Entity, spot: MessSpot, tool: Tool) -> None:
    sleeper.meters["dirty"] = 0.0
    sleeper.memes["embarrassed"] = 0.0
    sleeper.memes["cleaned"] += 1
    world.say(
        f"{caretaker.id} brought {tool.phrase} and {tool.action_text} {spot.on_phrase}. "
        f'"There now," {caretaker.pronoun()} murmured. "All fresh for bed."'
    )


def invite_after_clean(world: World, sleeper: Entity, friend: Entity) -> None:
    sleeper.memes["invited"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{friend.id} shuffled over and made room with a soft nudge."
    )
    world.say(
        f'"Come close," {friend.pronoun()} said. "Clean and hungry friends belong together."'
    )


def share_supper(world: World, sleeper: Entity, friend: Entity, snack: Snack) -> None:
    world.say(
        f"So {sleeper.id} stepped up at last, and the two friends ate {snack.phrase} from the manger."
    )
    world.say(
        f'The barn filled with little bedtime sounds: "{snack.rustle}," "snuffle-snuffle," and '
        f'"munch, munch, munch."'
    )


def sleep_end(world: World, sleeper: Entity, friend: Entity,
              sleeper_kind: AnimalKind, friend_kind: AnimalKind) -> None:
    sleeper.memes["safe"] += 1
    friend.memes["safe"] += 1
    world.say(
        f"When their bellies were full, {sleeper.id} leaned against {friend.id}, "
        f"and {friend.id} leaned back."
    )
    world.say(
        f"Outside, the last light slipped away. Inside, the little {sleeper_kind.child_word} "
        f"and little {friend_kind.child_word} breathed, \"{sleeper_kind.night_sound}\" and "
        f"\"{friend_kind.night_sound},\" until the whole stall felt sleepy."
    )
    world.say(
        "The manger was still between them, but now it was a shared place, not a lonely one, "
        "and the barn held them both through the night."
    )


def tell(sleeper_name: str, sleeper_kind: AnimalKind,
         friend_name: str, friend_kind: AnimalKind,
         spot: MessSpot, tool: Tool, snack: Snack, call: CallStyle,
         caretaker_type: str = "mother") -> World:
    world = World()
    sleeper = world.add(Entity(
        id=sleeper_name,
        kind="character",
        type=sleeper_kind.id,
        label=sleeper_kind.child_word,
        role="sleeper",
        attrs={"gender": "girl"},
        tags=set(sleeper_kind.tags),
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_kind.id,
        label=friend_kind.child_word,
        role="friend",
        attrs={"gender": "boy"},
        tags=set(friend_kind.tags),
    ))
    caretaker_name = "Mama May" if caretaker_type == "mother" else "Papa Ben"
    caretaker = world.add(Entity(
        id=caretaker_name,
        kind="character",
        type=caretaker_type,
        label="caretaker",
        role="caretaker",
        attrs={"gender": "girl" if caretaker_type == "mother" else "boy"},
    ))
    world.add(Entity(id="manger", kind="thing", type="manger", label="manger", role="manger"))
    world.add(Entity(id="supper", kind="thing", type="food", label=snack.label, role="food"))

    world.facts.update(
        sleeper=sleeper,
        friend=friend,
        caretaker=caretaker,
        sleeper_kind=sleeper_kind,
        friend_kind=friend_kind,
        spot=spot,
        tool=tool,
        snack=snack,
        call=call,
        outcome="shared",
    )

    introduce(world, sleeper, friend, snack, sleeper_kind, friend_kind)
    world.para()
    arrive_messy(world, sleeper, spot)
    notice_and_invite(world, sleeper, friend, call, snack)
    call_caretaker(world, caretaker, friend)
    world.para()
    clean_mess(world, sleeper, caretaker, spot, tool)
    invite_after_clean(world, sleeper, friend)
    share_supper(world, sleeper, friend, snack)
    world.para()
    sleep_end(world, sleeper, friend, sleeper_kind, friend_kind)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ANIMALS = {
    "foal": AnimalKind(
        id="foal",
        child_word="foal",
        hoof_word="hoof",
        night_sound="hufff",
        tags={"horse", "barn"},
    ),
    "calf": AnimalKind(
        id="calf",
        child_word="calf",
        hoof_word="hoof",
        night_sound="mmmr",
        tags={"cow", "barn"},
    ),
    "goat_kid": AnimalKind(
        id="goat_kid",
        child_word="kid goat",
        hoof_word="hoof",
        night_sound="meeh",
        tags={"goat", "barn"},
    ),
    "lamb": AnimalKind(
        id="lamb",
        child_word="lamb",
        hoof_word="hoof",
        night_sound="baaah",
        tags={"sheep", "barn"},
    ),
}

SPOTS = {
    "hoof": MessSpot(
        id="hoof",
        label="hoof",
        on_phrase="the muddy edge of one small hoof",
        notice_text="A dark smear lay on the edge of one little hoof",
        cleaner_tags={"brush"},
        tags={"hoof", "dung"},
    ),
    "tail": MessSpot(
        id="tail",
        label="tail",
        on_phrase="the end of the swishy tail",
        notice_text="A brown tangle had dried near the end of the tail",
        cleaner_tags={"cloth"},
        tags={"tail", "dung"},
    ),
    "blanket": MessSpot(
        id="blanket",
        label="blanket",
        on_phrase="the corner of the little night blanket",
        notice_text="A messy brown mark spotted the corner of the bedtime blanket",
        cleaner_tags={"cloth", "straw"},
        tags={"blanket", "dung", "bedtime"},
    ),
}

TOOLS = {
    "hoof_brush": Tool(
        id="hoof_brush",
        label="hoof brush",
        phrase="a hoof brush",
        action_text="gently brushed away the dried bits from",
        cleans={"hoof"},
        tags={"brush", "hoof_brush"},
    ),
    "warm_cloth": Tool(
        id="warm_cloth",
        label="warm cloth",
        phrase="a warm cloth",
        action_text="wiped and patted clean",
        cleans={"tail", "blanket"},
        tags={"cloth", "warm_cloth"},
    ),
    "fresh_straw": Tool(
        id="fresh_straw",
        label="fresh straw",
        phrase="a bundle of fresh straw",
        action_text="rubbed and lifted the mess from",
        cleans={"blanket"},
        tags={"straw", "fresh_straw"},
    ),
}

SNACKS = {
    "hay": Snack(
        id="hay",
        label="hay",
        phrase="sweet hay",
        rustle="hush-rustle",
        tags={"hay", "manger"},
    ),
    "clover": Snack(
        id="clover",
        label="clover",
        phrase="a pile of clover and hay",
        rustle="soft-rustle",
        tags={"clover", "manger"},
    ),
    "oats": Snack(
        id="oats",
        label="oats",
        phrase="oats tucked into soft hay",
        rustle="tap-rustle",
        tags={"oats", "manger"},
    ),
}

CALLS = {
    "snuffle": CallStyle(
        id="snuffle",
        sound="snuffle-snuffle",
        line="called in the tiniest supper voice",
        tags={"sound_effects", "sharing"},
    ),
    "clipclop": CallStyle(
        id="clipclop",
        sound="clip-clop",
        line="tapped one hoof and smiled with sleepy eyes",
        tags={"sound_effects", "sharing"},
    ),
    "swish": CallStyle(
        id="swish",
        sound="swish-swish",
        line="brushed the straw with a friendly little tail-song",
        tags={"sound_effects", "sharing"},
    ),
}

GIRL_NAMES = ["Mira", "Lulu", "Poppy", "Tess", "Nell", "Daisy"]
BOY_NAMES = ["Ollie", "Pip", "Milo", "Benji", "Finn", "Rory"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    sleeper_kind: str
    friend_kind: str
    spot: str
    tool: str
    snack: str
    call: str
    sleeper_name: str
    friend_name: str
    caretaker: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "manger": [
        (
            "What is a manger?",
            "A manger is a feeding place in a barn where animals can eat hay or grain. It keeps supper in one easy spot.",
        )
    ],
    "dung": [
        (
            "What is dung?",
            "Dung is animal poop. It belongs far away from supper and bedding, so grown-ups clean it off when it gets stuck somewhere.",
        )
    ],
    "hoof": [
        (
            "What is a hoof?",
            "A hoof is the hard foot of an animal like a horse, goat, or cow. It helps the animal stand and walk.",
        )
    ],
    "hoof_brush": [
        (
            "What is a hoof brush for?",
            "A hoof brush helps clean dirt and messy bits from around a hoof. It is a careful tool for a careful job.",
        )
    ],
    "warm_cloth": [
        (
            "Why can a warm cloth help?",
            "A warm cloth can loosen a sticky mess and wipe it away gently. Warmth also feels comforting when someone is tired.",
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting someone else have part of what you have. It can make a lonely moment feel friendly and safe.",
        )
    ],
    "sound_effects": [
        (
            "What are sound effects in a story?",
            "Sound effects are playful sound words like 'snuffle-snuffle' or 'swish-swish.' They help you hear the story in your mind.",
        )
    ],
    "barn": [
        (
            "Why do barns feel quiet at night?",
            "Barns often grow quiet at night because the work of the day is over and the animals are settling down. The soft sounds feel calm and sleepy.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "manger",
    "dung",
    "hoof",
    "hoof_brush",
    "warm_cloth",
    "sharing",
    "sound_effects",
    "barn",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sleeper = f["sleeper"]
    friend = f["friend"]
    spot = f["spot"]
    snack = f["snack"]
    call = f["call"]
    return [
        (
            f'Write a bedtime story for a 3-to-5-year-old that includes the words "day", '
            f'"dung", and "manger", and uses sound effects and sharing.'
        ),
        (
            f"Tell a gentle barn story where {sleeper.id} feels shy because of dung on "
            f"{spot.label}, and {friend.id} invites {sleeper.pronoun('object')} to share "
            f"{snack.label} with a soft \"{call.sound}\" sound."
        ),
        (
            "Write a calm sleepy story where a little problem gets cleaned up, supper is shared, "
            "and the ending image feels safe enough for bedtime."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleeper = f["sleeper"]
    friend = f["friend"]
    caretaker = f["caretaker"]
    spot = f["spot"]
    tool = f["tool"]
    snack = f["snack"]
    sleeper_kind = f["sleeper_kind"]
    friend_kind = f["friend_kind"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleeper.id}, a little {sleeper_kind.child_word}, and {friend.id}, a little {friend_kind.child_word}. The gentle caretaker {caretaker.id} helps them before bed.",
        ),
        (
            f"Why did {sleeper.id} stop near the manger?",
            f"{sleeper.id} stopped because dung was stuck on {sleeper.pronoun('possessive')} {spot.label}, and {sleeper.pronoun()} felt embarrassed. {sleeper.pronoun().capitalize()} was hungry, but did not want to come close while feeling messy.",
        ),
        (
            f"How did {friend.id} help before the cleanup?",
            f"{friend.id} noticed the problem and used a soft \"{f['call'].sound}\" sound to call {sleeper.id} kindly. Then {friend.pronoun()} promised there was room to share at the manger, so {sleeper.id} did not have to feel left out.",
        ),
        (
            f"How did {caretaker.id} fix the problem?",
            f"{caretaker.id} used {tool.phrase} and cleaned {spot.on_phrase}. That removed the mess gently, so {sleeper.id} could come near the manger without feeling ashamed.",
        ),
        (
            "How did the story end?",
            f"The two friends shared {snack.phrase} from the manger and settled down side by side. Their full bellies and quiet little sounds showed that the lonely feeling had changed into comfort.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"manger", "dung", "sharing", "sound_effects", "barn"}
    if f["spot"].id == "hoof":
        tags.add("hoof")
    if f["tool"].id == "hoof_brush":
        tags.add("hoof_brush")
    if f["tool"].id == "warm_cloth":
        tags.add("warm_cloth")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
spot_needs(S, T) :- dirty_spot(S), suitable_tool(T, S).
valid(S, T) :- dirty_spot(S), tool(T), spot_needs(S, T).

cleaned :- chosen_spot(S), chosen_tool(T), valid(S, T).
outcome(shared) :- cleaned.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for spot_id in SPOTS:
        lines.append(asp.fact("dirty_spot", spot_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for spot_id in sorted(tool.cleans):
            lines.append(asp.fact("suitable_tool", tool_id, spot_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_spot", params.spot),
        asp.fact("chosen_tool", params.tool),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "shared" if (params.spot, params.tool) in set(valid_combos()) else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"FAILED: resolve_params rejected default seed {seed}.")
            continue
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH outcome for seed {seed}: asp={asp_outcome(params)} python={outcome_of(params)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"FAILED: smoke generation/emit crashed: {err}")
    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime barn story world: a shy animal, a small mess, a shared manger."
    )
    ap.add_argument("--sleeper-kind", choices=ANIMALS)
    ap.add_argument("--friend-kind", choices=ANIMALS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--call", choices=CALLS)
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (spot, tool) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, pool: list[str], avoid: str = "") -> str:
    names = [n for n in pool if n != avoid]
    return rng.choice(names)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.spot and args.tool:
        spot = SPOTS[args.spot]
        tool = TOOLS[args.tool]
        if not tool_fits_spot(spot, tool):
            raise StoryError(explain_rejection(spot, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.tool is None or combo[1] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spot_id, tool_id = rng.choice(sorted(combos))
    sleeper_kind = args.sleeper_kind or rng.choice(sorted(ANIMALS))
    friend_kind = args.friend_kind or rng.choice(sorted(ANIMALS))
    snack = args.snack or rng.choice(sorted(SNACKS))
    call = args.call or rng.choice(sorted(CALLS))
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    sleeper_name = _pick_name(rng, GIRL_NAMES)
    friend_name = _pick_name(rng, BOY_NAMES, avoid=sleeper_name)
    return StoryParams(
        sleeper_kind=sleeper_kind,
        friend_kind=friend_kind,
        spot=spot_id,
        tool=tool_id,
        snack=snack,
        call=call,
        sleeper_name=sleeper_name,
        friend_name=friend_name,
        caretaker=caretaker,
    )


def generate(params: StoryParams) -> StorySample:
    if params.sleeper_kind not in ANIMALS:
        raise StoryError(f"(Unknown sleeper kind: {params.sleeper_kind})")
    if params.friend_kind not in ANIMALS:
        raise StoryError(f"(Unknown friend kind: {params.friend_kind})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.call not in CALLS:
        raise StoryError(f"(Unknown call: {params.call})")
    if params.caretaker not in {"mother", "father"}:
        raise StoryError(f"(Unknown caretaker: {params.caretaker})")

    spot = SPOTS[params.spot]
    tool = TOOLS[params.tool]
    if not tool_fits_spot(spot, tool):
        raise StoryError(explain_rejection(spot, tool))

    world = tell(
        sleeper_name=params.sleeper_name,
        sleeper_kind=ANIMALS[params.sleeper_kind],
        friend_name=params.friend_name,
        friend_kind=ANIMALS[params.friend_kind],
        spot=spot,
        tool=tool,
        snack=SNACKS[params.snack],
        call=CALLS[params.call],
        caretaker_type=params.caretaker,
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


CURATED = [
    StoryParams(
        sleeper_kind="foal",
        friend_kind="lamb",
        spot="hoof",
        tool="hoof_brush",
        snack="hay",
        call="clipclop",
        sleeper_name="Mira",
        friend_name="Pip",
        caretaker="mother",
    ),
    StoryParams(
        sleeper_kind="calf",
        friend_kind="goat_kid",
        spot="tail",
        tool="warm_cloth",
        snack="clover",
        call="swish",
        sleeper_name="Lulu",
        friend_name="Milo",
        caretaker="father",
    ),
    StoryParams(
        sleeper_kind="lamb",
        friend_kind="foal",
        spot="blanket",
        tool="fresh_straw",
        snack="oats",
        call="snuffle",
        sleeper_name="Poppy",
        friend_name="Finn",
        caretaker="mother",
    ),
    StoryParams(
        sleeper_kind="goat_kid",
        friend_kind="calf",
        spot="blanket",
        tool="warm_cloth",
        snack="hay",
        call="swish",
        sleeper_name="Nell",
        friend_name="Rory",
        caretaker="father",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spot, tool) combos:\n")
        for spot, tool in combos:
            print(f"  {spot:8} {tool}")
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
            header = (
                f"### {p.sleeper_name} and {p.friend_name}: {p.spot} + {p.tool} "
                f"({p.sleeper_kind}, {p.friend_kind}, {p.snack})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
