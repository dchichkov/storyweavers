#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mob_mansion_kindness_whodunit.py
===========================================================

A standalone story world for a child-sized **whodunit** set in a big old
**mansion**, where a worried **mob** of guests starts guessing too fast and a
kind child solves the mystery by being gentle, patient, and fair.

Source-tale premise imagined from the seed
------------------------------------------
At a kindness party in a mansion, something special goes missing. The grown-ups
and children nearby form a noisy little mob of guesses and point at the wrong
person because of a hasty clue: flour on an apron, mud on boots, or feathers in
a hallway. But the young sleuth slows everyone down, asks kind questions, and
looks at what the world is actually doing. A puppy may have carried off a soft
ribbon, a breeze may have blown away a paper note, or a magpie may have taken a
shiny key. The mystery is solved, the wrongly suspected helper is comforted, and
the ending proves that kindness can be part of detective work.

Run it
------
    python storyworlds/worlds/gpt-5.4/mob_mansion_kindness_whodunit.py
    python storyworlds/worlds/gpt-5.4/mob_mansion_kindness_whodunit.py --room ballroom --item ribbon
    python storyworlds/worlds/gpt-5.4/mob_mansion_kindness_whodunit.py --cause breeze
    python storyworlds/worlds/gpt-5.4/mob_mansion_kindness_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/mob_mansion_kindness_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mob_mansion_kindness_whodunit.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/mob_mansion_kindness_whodunit.py --verify
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
KIND_MIN = 2


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"       # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    portable: bool = False
    shiny: bool = False
    soft: bool = False
    paper: bool = False
    can_fetch: bool = False
    can_carry_shiny: bool = False
    catches_breeze: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "cook"}
        male = {"boy", "man", "father", "butler", "gardener"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Config registries
# ---------------------------------------------------------------------------
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
class Room:
    id: str
    label: str
    phrase: str
    window: bool
    echoes: str
    hideaway: str
    suspects: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    owner_name: str
    purpose: str
    soft: bool = False
    shiny: bool = False
    paper: bool = False
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
class Cause:
    id: str
    culprit_type: str          # puppy | breeze | magpie
    clue: str
    found_at: str
    recovery: str
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
class SuspectCfg:
    id: str
    label: str
    type: str
    phrase: str
    job: str
    near_rooms: set[str]
    misleading_clue: str
    kind_detail: str
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
class StyleMode:
    id: str
    sense: int
    opening: str
    detective_name: str
    promise: str


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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
# Rules
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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    crowd = world.get("crowd")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd.meters["noise"] += 1
    crowd.memes["worry"] += 1
    sleuth = world.get("sleuth")
    sleuth.memes["concern"] += 1
    return ["__mob__"]


def _r_accuse_hurts(world: World) -> list[str]:
    suspect = world.get("suspect")
    crowd = world.get("crowd")
    if crowd.meters["pointing"] < THRESHOLD:
        return []
    sig = ("accuse_hurts", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    suspect.memes["lonely"] += 1
    return ["__hurt__"]


def _r_kindness_builds_trust(world: World) -> list[str]:
    sleuth = world.get("sleuth")
    suspect = world.get("suspect")
    if sleuth.memes["kindness"] < THRESHOLD:
        return []
    sig = ("kindness_builds_trust", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["trust"] += 1
    suspect.memes["calm"] += 1
    return ["__trust__"]


def _r_trust_reveals_clue(world: World) -> list[str]:
    suspect = world.get("suspect")
    if suspect.memes["trust"] < THRESHOLD:
        return []
    sig = ("trust_reveals_clue", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("sleuth").meters["clue"] += 1
    return ["__clue__"]


def _r_found_brings_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    crowd = world.get("crowd")
    crowd.meters["noise"] = 0.0
    crowd.memes["worry"] = 0.0
    crowd.meters["pointing"] = 0.0
    for eid in ("sleuth", "suspect", "host"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="social", apply=_r_missing_worry),
    Rule(name="accuse_hurts", tag="social", apply=_r_accuse_hurts),
    Rule(name="kindness_builds_trust", tag="social", apply=_r_kindness_builds_trust),
    Rule(name="trust_reveals_clue", tag="social", apply=_r_trust_reveals_clue),
    Rule(name="found_relief", tag="social", apply=_r_found_brings_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def cause_fits_item(cause: Cause, item: MissingItem) -> bool:
    if cause.culprit_type == "puppy":
        return item.soft
    if cause.culprit_type == "breeze":
        return item.paper
    if cause.culprit_type == "magpie":
        return item.shiny
    return False


def suspect_plausible(room: Room, suspect: SuspectCfg) -> bool:
    return room.id in suspect.near_rooms


def valid_combo(room: Room, item: MissingItem, cause: Cause, suspect: SuspectCfg, style: StyleMode) -> bool:
    return (
        cause_fits_item(cause, item)
        and suspect_plausible(room, suspect)
        and style.sense >= KIND_MIN
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for room_id, room in ROOMS.items():
        for item_id, item in ITEMS.items():
            for cause_id, cause in CAUSES.items():
                for suspect_id, suspect in SUSPECTS.items():
                    for style_id, style in STYLES.items():
                        if valid_combo(room, item, cause, suspect, style):
                            combos.append((room_id, item_id, cause_id, suspect_id, style_id))
    return sorted(combos)


def sensible_styles() -> list[StyleMode]:
    return [style for style in STYLES.values() if style.sense >= KIND_MIN]


def explain_combo_rejection(room: Room, item: MissingItem, cause: Cause, suspect: SuspectCfg, style: StyleMode) -> str:
    if style.sense < KIND_MIN:
        return (
            f"(No story: style '{style.id}' is too unkind for this world. "
            f"This whodunit is about solving the mystery with kindness.)"
        )
    if not cause_fits_item(cause, item):
        if cause.culprit_type == "puppy":
            why = "a puppy can run off with something soft to chew or cuddle"
        elif cause.culprit_type == "breeze":
            why = "a breeze can only whisk away something light and papery"
        else:
            why = "a magpie is only drawn to shiny things"
        return (
            f"(No story: {cause.id} does not fit the missing {item.label}. "
            f"Here, {why}, so pick a matching item.)"
        )
    if not suspect_plausible(room, suspect):
        return (
            f"(No story: {suspect.label} is not a sensible suspect in the {room.label}. "
            f"Choose a suspect who would actually be near that room.)"
        )
    return "(No story: this combination is unreasonable.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_cause(item: MissingItem) -> dict:
    if item.soft:
        return {"culprit_type": "puppy", "trail": "little paw marks near a basket"}
    if item.paper:
        return {"culprit_type": "breeze", "trail": "a flutter under a door"}
    return {"culprit_type": "magpie", "trail": "a glint near the open window"}


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, room: Room, item: MissingItem, style: StyleMode, sleuth: Entity, host: Entity) -> None:
    sleuth.memes["curiosity"] += 1
    host.memes["hope"] += 1
    world.say(
        f"{style.opening} In the old {room.label}, {host.id} was setting out kind surprises for the guests. "
        f"{item.phrase} was meant for {item.purpose}, and {sleuth.id} was proud to be {style.detective_name} for the evening."
    )
    world.say(
        f"The grand room echoed softly with {room.echoes}, and every doorway in the mansion seemed to be holding a secret."
    )


def celebration(world: World, room: Room, item: MissingItem, host: Entity) -> None:
    world.say(
        f'"When everyone arrives," {host.id} said, "I want them to find {item.phrase} and remember to be gentle with one another."'
    )
    world.say(
        f"But when {host.pronoun()} reached for it again, the place where it had rested was empty."
    )
    world.get("item").meters["missing"] += 1
    propagate(world, narrate=False)


def mob_guess(world: World, suspect: Entity, suspect_cfg: SuspectCfg) -> None:
    crowd = world.get("crowd")
    crowd.meters["pointing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At once a little mob of guests pressed closer. Some whispered, some gasped, and one after another they looked at {suspect.id}."
    )
    world.say(
        f'"Maybe {suspect.id} took it," somebody said, because {suspect_cfg.misleading_clue}.'
    )


def suspect_reacts(world: World, suspect: Entity, suspect_cfg: SuspectCfg) -> None:
    extra = ""
    if suspect.memes["hurt"] >= THRESHOLD:
        extra = f" {suspect.id}'s face fell, because {suspect_cfg.kind_detail}."
    world.say(
        f"{suspect.id}, {suspect_cfg.phrase}, blinked in surprise.{extra}"
    )


def gentle_pause(world: World, sleuth: Entity, suspect: Entity, style: StyleMode) -> None:
    sleuth.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(
        f'But {sleuth.id} lifted a hand. "{style.promise}" {sleuth.pronoun().capitalize()} said. '
        f'"A good detective does not begin with blame."'
    )
    world.say(
        f"{sleuth.id} stepped beside {suspect.id} instead of pointing from across the room."
    )


def kind_question(world: World, sleuth: Entity, suspect: Entity, room: Room, cause: Cause) -> None:
    pred = predict_cause(world.facts["item_cfg"])
    world.facts["predicted_trail"] = pred["trail"]
    world.say(
        f'{sleuth.id} asked in a soft voice, "What did you notice here in the {room.label}?"'
    )
    world.say(
        f"{suspect.id} took a breath and answered more steadily now. {cause.clue}"
    )


def inspect(world: World, sleuth: Entity, room: Room) -> None:
    sleuth.meters["searching"] += 1
    world.say(
        f"That clue sent {sleuth.id} across the {room.label}, past {room.hideaway}, looking not for a villain but for the truth."
    )


def discover(world: World, item: Entity, item_cfg: MissingItem, cause: Cause) -> None:
    item.meters["found"] += 1
    item.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(cause.recovery.replace("{item}", item_cfg.label))
    world.say(
        f"So that was the whole mystery: nobody had stolen anything at all."
    )


def apology(world: World, crowd: Entity, suspect: Entity, host: Entity) -> None:
    crowd.memes["shame"] += 1
    suspect.memes["hurt"] = 0.0
    suspect.memes["lonely"] = 0.0
    world.say(
        f"The room went quiet. Then {host.id} turned to {suspect.id} first."
    )
    world.say(
        f'"We were too quick to guess," {host.pronoun()} said. "I am sorry." '
        f"The rest of the crowd murmured sorry too, and the hard, hot feeling in the room began to melt."
    )


def ending(world: World, sleuth: Entity, suspect: Entity, item_cfg: MissingItem, cause: Cause, room: Room) -> None:
    sleuth.memes["pride"] += 1
    suspect.memes["gratitude"] += 1
    world.say(
        f"{suspect.id} smiled at {sleuth.id}. {cause.lesson}"
    )
    world.say(
        f"Before the lamps glowed low in the mansion, {item_cfg.phrase} was back in its place, "
        f"and the {room.label} felt warmer than before. The mystery had been solved with clear eyes and a kind heart."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    room: Room,
    item_cfg: MissingItem,
    cause: Cause,
    suspect_cfg: SuspectCfg,
    style: StyleMode,
    sleuth_name: str = "Nora",
    sleuth_gender: str = "girl",
    host_type: str = "aunt",
) -> World:
    world = World()
    sleuth = world.add(Entity(
        id=sleuth_name,
        kind="character",
        type=sleuth_gender,
        role="sleuth",
        label=sleuth_name,
        traits=["careful", "kind"],
    ))
    host = world.add(Entity(
        id="Aunt Bea" if host_type == "aunt" else "Uncle Theo",
        kind="character",
        type=host_type,
        role="host",
        label="the host",
        attrs={"title": host_type},
    ))
    suspect = world.add(Entity(
        id=suspect_cfg.label,
        kind="character",
        type=suspect_cfg.type,
        role="suspect",
        label=suspect_cfg.label,
        attrs={"job": suspect_cfg.job},
    ))
    item = world.add(Entity(
        id="item",
        type="item",
        label=item_cfg.label,
        owner=host.id,
        portable=True,
        shiny=item_cfg.shiny,
        soft=item_cfg.soft,
        paper=item_cfg.paper,
    ))
    crowd = world.add(Entity(
        id="crowd",
        type="crowd",
        label="the crowd",
        role="crowd",
    ))
    world.add(Entity(
        id="room",
        type="room",
        label=room.label,
        attrs={"window": room.window},
    ))
    if cause.culprit_type == "puppy":
        world.add(Entity(id="culprit", type="puppy", label="a little puppy", can_fetch=True))
    elif cause.culprit_type == "breeze":
        world.add(Entity(id="culprit", type="breeze", label="the breeze", catches_breeze=True))
    else:
        world.add(Entity(id="culprit", type="magpie", label="a bright-eyed magpie", can_carry_shiny=True))

    world.facts.update(
        room_cfg=room,
        item_cfg=item_cfg,
        cause_cfg=cause,
        suspect_cfg=suspect_cfg,
        style_cfg=style,
        sleuth=sleuth,
        host=host,
        suspect=suspect,
        crowd=crowd,
        culprit_type=cause.culprit_type,
    )

    introduce(world, room, item_cfg, style, sleuth, host)
    celebration(world, room, item_cfg, host)

    world.para()
    mob_guess(world, suspect, suspect_cfg)
    suspect_reacts(world, suspect, suspect_cfg)

    world.para()
    gentle_pause(world, sleuth, suspect, style)
    kind_question(world, sleuth, suspect, room, cause)
    inspect(world, sleuth, room)

    world.para()
    discover(world, item, item_cfg, cause)
    apology(world, crowd, suspect, host)
    ending(world, sleuth, suspect, item_cfg, cause, room)

    world.facts.update(
        mystery_started=item.meters["found"] < THRESHOLD or crowd.meters["pointing"] >= THRESHOLD,
        falsely_accused=True,
        item_found=item.meters["found"] >= THRESHOLD,
        clues_seen=sleuth.meters["clue"] >= THRESHOLD,
        kindness_used=sleuth.memes["kindness"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ROOMS = {
    "ballroom": Room(
        id="ballroom",
        label="ballroom",
        phrase="the moon-bright ballroom",
        window=True,
        echoes="soft music and tiny shoe taps",
        hideaway="the curtain folds by the window",
        suspects={"butler", "gardener"},
        tags={"mansion", "room"},
    ),
    "library": Room(
        id="library",
        label="library",
        phrase="the lamp-lit library",
        window=True,
        echoes="page rustles and low whispers",
        hideaway="the rolling ladder and the reading nook",
        suspects={"butler", "cook"},
        tags={"mansion", "room", "books"},
    ),
    "sunroom": Room(
        id="sunroom",
        label="sunroom",
        phrase="the glassy sunroom",
        window=True,
        echoes="leafy shadows and clinking flowerpots",
        hideaway="the fern stand by the wicker bench",
        suspects={"gardener", "cook"},
        tags={"mansion", "room", "garden"},
    ),
}

ITEMS = {
    "ribbon": MissingItem(
        id="ribbon",
        label="ribbon",
        phrase="a velvet kindness ribbon",
        owner_name="Aunt Bea",
        purpose="the first guest who helped someone else",
        soft=True,
        tags={"ribbon", "kindness"},
    ),
    "note": MissingItem(
        id="note",
        label="note",
        phrase="a paper kindness note",
        owner_name="Aunt Bea",
        purpose="the evening's secret thank-you game",
        paper=True,
        tags={"paper", "kindness"},
    ),
    "key": MissingItem(
        id="key",
        label="gold key",
        phrase="a little gold kindness key",
        owner_name="Aunt Bea",
        purpose="opening the box of treats for everyone",
        shiny=True,
        tags={"shiny", "kindness"},
    ),
}

CAUSES = {
    "puppy": Cause(
        id="puppy",
        culprit_type="puppy",
        clue="I saw a tiny wagging tail disappear behind the bench with something soft in its mouth.",
        found_at="under the wicker bench",
        recovery="A small bark answered from under the wicker bench, and there lay the {item}, tucked beside a sleepy puppy who had carried it off like a toy.",
        lesson="\"Thank you for asking kindly,\" said the suspect. \"That helped the truth come out faster.\"",
        tags={"puppy"},
    ),
    "breeze": Cause(
        id="breeze",
        culprit_type="breeze",
        clue="The window was cracked open, and I heard a papery flutter scoot under the door.",
        found_at="under the library door",
        recovery="A silver draft slipped along the floor, and there was the {item}, caught flat under the door where the breeze had pushed it.",
        lesson="\"You listened before you judged,\" said the suspect. \"That was braver than shouting.\"",
        tags={"wind"},
    ),
    "magpie": Cause(
        id="magpie",
        culprit_type="magpie",
        clue="Something shiny flashed past the sill, and I heard wings outside the open window.",
        found_at="in the ivy by the sill",
        recovery="Just outside the open window, a bright-eyed magpie hopped in the ivy, and beside its nest glittered the {item}.",
        lesson="\"You looked for clues instead of a person to blame,\" said the suspect. \"That was very kind detective work.\"",
        tags={"bird"},
    ),
}

SUSPECTS = {
    "butler": SuspectCfg(
        id="butler",
        label="Mr. Vale",
        type="butler",
        phrase="the neat butler with the silver tray",
        job="butler",
        near_rooms={"ballroom", "library"},
        misleading_clue="he had just been straightening the tables and was nearest to the empty spot",
        kind_detail="he had spent all morning helping little guests reach the tall coat hooks",
        tags={"butler"},
    ),
    "cook": SuspectCfg(
        id="cook",
        label="Cook Mara",
        type="cook",
        phrase="the flour-dusted cook from the warm kitchen",
        job="cook",
        near_rooms={"library", "sunroom"},
        misleading_clue="there was flour on her apron, which made her look as if she had been in a hurry",
        kind_detail="she was famous for slipping extra berry buns onto shy children's plates",
        tags={"cook"},
    ),
    "gardener": SuspectCfg(
        id="gardener",
        label="Old Pip",
        type="gardener",
        phrase="the gardener with moss on his boots",
        job="gardener",
        near_rooms={"ballroom", "sunroom"},
        misleading_clue="there were damp leaf marks by his boots, and everyone noticed them at once",
        kind_detail="he always saved the prettiest flowers for children who felt left out",
        tags={"gardener"},
    ),
}

STYLES = {
    "kind": StyleMode(
        id="kind",
        sense=3,
        opening="One misty evening, a small mystery tiptoed into the mansion.",
        detective_name="junior detective",
        promise="Please wait. We can ask first and guess later.",
    ),
    "gentle": StyleMode(
        id="gentle",
        sense=3,
        opening="On a quiet evening, the mansion seemed full of clues and candlelight.",
        detective_name="house detective",
        promise="Let us be fair. Clues speak better when everyone feels safe.",
    ),
    "snappy": StyleMode(
        id="snappy",
        sense=1,
        opening="The mansion buzzed with sharp questions.",
        detective_name="chief detective",
        promise="Stand back. I will sort this out fast.",
    ),
}

GIRL_NAMES = ["Nora", "Lila", "Mina", "Ada", "Ivy", "Rosa"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Finn", "Eli", "Sam"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    room: str
    item: str
    cause: str
    suspect: str
    style: str
    sleuth_name: str
    sleuth_gender: str
    host_type: str
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
    "whodunit": [
        (
            "What is a whodunit story?",
            "A whodunit is a mystery story where someone tries to figure out what really happened. The fun comes from following clues instead of guessing wildly."
        )
    ],
    "kindness": [
        (
            "Why does kindness help in a mystery?",
            "Kindness helps people feel calm enough to tell what they know. When people are not scared or blamed, true clues are easier to find."
        )
    ],
    "mob": [
        (
            "What is a mob?",
            "A mob is a big crowd all pressing together at once. A noisy mob can make it hard to think clearly."
        )
    ],
    "mansion": [
        (
            "What is a mansion?",
            "A mansion is a very large house with many rooms. In stories, all those rooms make good places for mysteries and hiding spots."
        )
    ],
    "puppy": [
        (
            "Why might a puppy carry something away?",
            "A puppy may carry away something soft because it feels like a toy. Puppies explore with their mouths and do not understand important things yet."
        )
    ],
    "wind": [
        (
            "How can a breeze move paper?",
            "A breeze can catch light paper and slide or flutter it away. That is why loose notes should be kept flat or tucked safely."
        )
    ],
    "bird": [
        (
            "Why would a magpie take something shiny?",
            "Some birds notice glittering things very quickly. A shiny object can catch a magpie's eye the way a bright bead catches a child's eye."
        )
    ],
}
KNOWLEDGE_ORDER = ["whodunit", "kindness", "mob", "mansion", "puppy", "wind", "bird"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    room = f["room_cfg"]
    item = f["item_cfg"]
    suspect = f["suspect"]
    cause = f["cause_cfg"]
    return [
        f'Write a child-friendly whodunit set in a mansion where {item.label} goes missing and a little mob of guests blames the wrong person.',
        f"Tell a gentle mystery where a young detective questions {suspect.id} kindly in the {room.label} and solves what happened.",
        f'Write a story about kindness helping solve a mystery, where the missing thing is {item.phrase} and the real cause is {cause.id}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sleuth = f["sleuth"]
    suspect = f["suspect"]
    host = f["host"]
    room = f["room_cfg"]
    item = f["item_cfg"]
    cause = f["cause_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sleuth.id}, a child detective in a big mansion, and {host.id}, who was getting ready for a kind party. It is also about {suspect.id}, who was blamed before anyone knew the truth."
        ),
        (
            f"What went missing in the {room.label}?",
            f"{item.phrase.capitalize()} went missing. It mattered because it was meant for {item.purpose}."
        ),
        (
            f"Why did the crowd suspect {suspect.id}?",
            f"They blamed {suspect.id} because {f['suspect_cfg'].misleading_clue}. The crowd saw one quick clue and turned it into a wrong guess."
        ),
        (
            f"How did {sleuth.id} help solve the mystery?",
            f"{sleuth.id} slowed the noisy mob down and asked kind questions instead of blaming anyone. That made {suspect.id} feel safe enough to share the clue that led to the missing item."
        ),
    ]
    if f.get("item_found"):
        qa.append(
            (
                "What really happened to the missing thing?",
                f"No person had stolen it. {cause.recovery.replace('{item}', item.label)}"
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The item was found, the wrong guess was fixed, and everyone apologized to {suspect.id}. The ending shows that kindness helped the detective find the truth and made the room feel warm again."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"whodunit", "kindness", "mob", "mansion"}
    tags |= set(world.facts["cause_cfg"].tags)
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
        flags = [
            name for name, on in (
                ("portable", ent.portable),
                ("shiny", ent.shiny),
                ("soft", ent.soft),
                ("paper", ent.paper),
                ("can_fetch", ent.can_fetch),
                ("can_carry_shiny", ent.can_carry_shiny),
                ("catches_breeze", ent.catches_breeze),
            ) if on
        ]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Registry-driven reasonableness gate.
valid(Room, Item, Cause, Suspect, Style) :-
    room(Room), item(Item), cause(Cause), suspect(Suspect), style(Style),
    sensible_style(Style),
    fits(Cause, Item),
    near(Suspect, Room).

sensible_style(S) :- style(S), style_sense(S, N), kind_min(K), N >= K.

% Cause compatibility.
fits(C, I) :- cause_type(C, puppy), item_soft(I).
fits(C, I) :- cause_type(C, breeze), item_paper(I).
fits(C, I) :- cause_type(C, magpie), item_shiny(I).

% Outcome and culprit type for one chosen scenario.
culprit_type(T) :- chosen_cause(C), cause_type(C, T).
solved :- chosen_style(S), sensible_style(S), chosen_suspect(Su), chosen_room(R), near(Su, R),
          chosen_item(I), chosen_cause(C), fits(C, I).
ending(found_and_apology) :- solved.

#show valid/5.
#show sensible_style/1.
#show culprit_type/1.
#show ending/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room_id in ROOMS:
        lines.append(asp.fact("room", room_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.soft:
            lines.append(asp.fact("item_soft", item_id))
        if item.paper:
            lines.append(asp.fact("item_paper", item_id))
        if item.shiny:
            lines.append(asp.fact("item_shiny", item_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_type", cause_id, cause.culprit_type))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for room_id in sorted(suspect.near_rooms):
            lines.append(asp.fact("near", suspect_id, room_id))
    for style_id, style in STYLES.items():
        lines.append(asp.fact("style", style_id))
        lines.append(asp.fact("style_sense", style_id, style.sense))
    lines.append(asp.fact("kind_min", KIND_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_styles() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(s for (s,) in asp.atoms(model, "sensible_style"))


def asp_culprit_type(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_room", params.room),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_cause", params.cause),
        asp.fact("chosen_suspect", params.suspect),
        asp.fact("chosen_style", params.style),
    ])
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "culprit_type")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: valid_combos() matches ASP ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    c_styles = set(asp_sensible_styles())
    p_styles = {s.id for s in sensible_styles()}
    if c_styles == p_styles:
        print(f"OK: sensible styles match ({sorted(c_styles)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible styles: clingo={sorted(c_styles)} python={sorted(p_styles)}")

    smoke_params = CURATED[0]
    try:
        smoke = generate(smoke_params)
        if not smoke.story.strip():
            raise StoryError("empty story")
        if not smoke.prompts or not smoke.story_qa or not smoke.world_qa:
            raise StoryError("missing QA or prompts")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(30):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {s}.")
            break
    mismatches = 0
    for p in cases:
        py = CAUSES[p.cause].culprit_type
        cl = asp_culprit_type(p)
        if py != cl:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: culprit type matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: culprit type differed on {mismatches}/{len(cases)} scenarios.")
    return rc


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        room="ballroom",
        item="ribbon",
        cause="puppy",
        suspect="butler",
        style="kind",
        sleuth_name="Nora",
        sleuth_gender="girl",
        host_type="aunt",
    ),
    StoryParams(
        room="library",
        item="note",
        cause="breeze",
        suspect="cook",
        style="gentle",
        sleuth_name="Milo",
        sleuth_gender="boy",
        host_type="uncle",
    ),
    StoryParams(
        room="sunroom",
        item="key",
        cause="magpie",
        suspect="gardener",
        style="kind",
        sleuth_name="Ada",
        sleuth_gender="girl",
        host_type="aunt",
    ),
    StoryParams(
        room="ballroom",
        item="key",
        cause="magpie",
        suspect="gardener",
        style="gentle",
        sleuth_name="Finn",
        sleuth_gender="boy",
        host_type="uncle",
    ),
    StoryParams(
        room="library",
        item="note",
        cause="breeze",
        suspect="butler",
        style="kind",
        sleuth_name="Lila",
        sleuth_gender="girl",
        host_type="aunt",
    ),
]


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a kind whodunit in a mansion where a worried mob guesses wrong."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("--host-type", choices=["aunt", "uncle"])
    ap.add_argument("--sleuth-name")
    ap.add_argument("--sleuth-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_sleuth(rng: random.Random, gender: Optional[str], name: Optional[str]) -> tuple[str, str]:
    chosen_gender = gender or rng.choice(["girl", "boy"])
    if name:
        return name, chosen_gender
    pool = GIRL_NAMES if chosen_gender == "girl" else BOY_NAMES
    return rng.choice(pool), chosen_gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    room = ROOMS.get(args.room) if args.room else None
    item = ITEMS.get(args.item) if args.item else None
    cause = CAUSES.get(args.cause) if args.cause else None
    suspect = SUSPECTS.get(args.suspect) if args.suspect else None
    style = STYLES.get(args.style) if args.style else None

    if all(v is not None for v in (room, item, cause, suspect, style)):
        if not valid_combo(room, item, cause, suspect, style):
            raise StoryError(explain_combo_rejection(room, item, cause, suspect, style))

    combos = [
        combo for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
        and (args.suspect is None or combo[3] == args.suspect)
        and (args.style is None or combo[4] == args.style)
    ]
    if not combos:
        probe_room = room or next(iter(ROOMS.values()))
        probe_item = item or next(iter(ITEMS.values()))
        probe_cause = cause or next(iter(CAUSES.values()))
        probe_suspect = suspect or next(iter(SUSPECTS.values()))
        probe_style = style or next(iter(STYLES.values()))
        raise StoryError(explain_combo_rejection(probe_room, probe_item, probe_cause, probe_suspect, probe_style))

    room_id, item_id, cause_id, suspect_id, style_id = rng.choice(combos)
    sleuth_name, sleuth_gender = _pick_sleuth(rng, args.sleuth_gender, args.sleuth_name)
    host_type = args.host_type or rng.choice(["aunt", "uncle"])
    return StoryParams(
        room=room_id,
        item=item_id,
        cause=cause_id,
        suspect=suspect_id,
        style=style_id,
        sleuth_name=sleuth_name,
        sleuth_gender=sleuth_gender,
        host_type=host_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect: {params.suspect})")
    if params.style not in STYLES:
        raise StoryError(f"(Unknown style: {params.style})")

    room = ROOMS[params.room]
    item = ITEMS[params.item]
    cause = CAUSES[params.cause]
    suspect = SUSPECTS[params.suspect]
    style = STYLES[params.style]

    if not valid_combo(room, item, cause, suspect, style):
        raise StoryError(explain_combo_rejection(room, item, cause, suspect, style))

    world = tell(
        room=room,
        item_cfg=item,
        cause=cause,
        suspect_cfg=suspect,
        style=style,
        sleuth_name=params.sleuth_name,
        sleuth_gender=params.sleuth_gender,
        host_type=params.host_type,
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
        print(f"{len(combos)} compatible (room, item, cause, suspect, style) combos:\n")
        for room, item, cause, suspect, style in combos:
            print(f"  {room:9} {item:7} {cause:7} {suspect:9} {style}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.sleuth_name}: {p.item} in the {p.room} ({p.cause}, suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
