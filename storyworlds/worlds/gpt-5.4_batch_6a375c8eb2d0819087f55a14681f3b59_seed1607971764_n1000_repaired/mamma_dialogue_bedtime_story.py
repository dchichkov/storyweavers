#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py
==========================================================

A standalone story world for a gentle bedtime tale: a child feels worried in the
dark, calls for mamma, and together they discover a small real cause and fix it.

The world is intentionally narrow and concrete. A bedtime worry is only valid
when the chosen remedy actually matches the cause strongly enough to settle it.
The child-facing story then grows out of the simulated state: darkness, sounds,
moving cloth, missing comfort toys, fear, calm, and sleepiness.

Run it
------
    python storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py --worry curtain_wave
    python storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py --worry lost_bunny --remedy close_window
    python storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py --trace
    python storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py --json
    python storyworlds/worlds/gpt-5.4/mamma_dialogue_bedtime_story.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "mamma"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mamma"
        return self.label or self.type
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
class Worry:
    id: str
    label: str
    opening: str
    source_label: str
    kind: str
    severity: int
    child_line: str
    mamma_guess: str
    reveal: str
    ending_image: str
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
class Remedy:
    id: str
    label: str
    solves: set[str] = field(default_factory=set)
    power: int = 0
    sense: int = 0
    action: str = ""
    soothe: str = ""
    qa_text: str = ""
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


def _r_worry_bites(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    source = world.get("source")
    if source.meters["active"] < THRESHOLD:
        return out
    sig = ("worry_bites", source.id, world.facts.get("worry_kind", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += float(world.facts.get("severity", 1))
    child.meters["awake"] += 1
    world.get("room").memes["unrest"] += 1
    out.append("__worry__")
    return out


def _r_calm_returns(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    source = world.get("source")
    mamma = world.get("mamma")
    if source.meters["active"] >= THRESHOLD:
        return out
    if mamma.memes["comforting"] < THRESHOLD:
        return out
    sig = ("calm_returns", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["calm"] += 2
    child.meters["sleepy"] += 1
    world.get("room").memes["peace"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry_bites", tag="emotional", apply=_r_worry_bites),
    Rule(name="calm_returns", tag="emotional", apply=_r_calm_returns),
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


def remedy_fits(worry: Worry, remedy: Remedy) -> bool:
    return (
        worry.kind in remedy.solves
        and remedy.power >= worry.severity
        and remedy.sense >= SENSE_MIN
    )


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for wid, worry in WORRIES.items():
        for rid, remedy in REMEDIES.items():
            if remedy_fits(worry, remedy):
                combos.append((wid, rid))
    return combos


def explain_rejection(worry: Worry, remedy: Remedy) -> str:
    if remedy.sense < SENSE_MIN:
        return (
            f"(No story: '{remedy.id}' is too weak as a real bedtime fix "
            f"(sense={remedy.sense} < {SENSE_MIN}). Pick a remedy that actually "
            f"addresses the cause.)"
        )
    if worry.kind not in remedy.solves:
        return (
            f"(No story: {remedy.label} does not solve a {worry.kind} worry. "
            f"The bedtime fix has to match what is really bothering the child.)"
        )
    if remedy.power < worry.severity:
        return (
            f"(No story: {remedy.label} is too weak for this worry. "
            f"It would not settle {worry.label} enough for a peaceful bedtime ending.)"
        )
    return "(No story: that worry and remedy do not make sense together.)"


def predict_settled(world: World, remedy: Remedy) -> bool:
    sim = world.copy()
    apply_remedy(sim, remedy, narrate=False)
    return sim.get("child").memos["fear"] < THRESHOLD if hasattr(sim.get("child"), "memos") else sim.get("child").memes["fear"] < THRESHOLD


def introduce(world: World, child: Entity, worry: Worry) -> None:
    child.memes["trust"] += 1
    world.say(
        f"It was bedtime, and {child.id} lay tucked under a soft blanket while a small lamp glowed low."
    )
    world.say(
        f"The room felt warm and sleepy at first, but then {worry.opening}"
    )


def notice(world: World, child: Entity, worry: Worry) -> None:
    source = world.get("source")
    source.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} sat up and whispered, "{worry.child_line}"'
    )
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f"The worry suddenly felt bigger in the dark, and {child.pronoun()} held the blanket right under {child.pronoun('possessive')} chin."
        )


def call_mamma(world: World, child: Entity, mamma: Entity) -> None:
    mamma.memes["alert"] += 1
    world.say(
        f'"Mamma?" {child.id} called. "{mamma.label_word.capitalize()}, will you come?"'
    )
    world.say(
        f"In a moment, mamma came in with quiet steps and sat beside the bed."
    )


def mamma_listens(world: World, child: Entity, mamma: Entity, worry: Worry) -> None:
    mamma.memes["care"] += 1
    child.memes["trust"] += 1
    world.say(
        f'"Tell me what feels wrong," mamma said.'
    )
    world.say(
        f'"{worry.child_line}" {child.id} said again, a little louder this time.'
    )
    world.say(
        f'"Let us look together," mamma whispered. "{worry.mamma_guess}"'
    )


def reveal(world: World, child: Entity, mamma: Entity, worry: Worry) -> None:
    source = world.get("source")
    world.say(worry.reveal)
    source.attrs["cause_seen"] = True
    child.memes["curiosity"] += 1
    world.say(
        f'{child.id} blinked. "Oh," {child.pronoun()} said. "It was only {worry.source_label}."'
    )


def apply_remedy(world: World, remedy: Remedy, narrate: bool = True) -> None:
    source = world.get("source")
    mamma = world.get("mamma")
    child = world.get("child")
    mamma.memes["comforting"] += 1
    source.meters["active"] = 0.0
    if source.meters["noise"] >= THRESHOLD:
        source.meters["noise"] = 0.0
    if source.meters["shadow"] >= THRESHOLD:
        source.meters["shadow"] = 0.0
    if source.meters["missing"] >= THRESHOLD:
        source.meters["missing"] = 0.0
    child.meters["awake"] = 0.0
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"Mamma {remedy.action}"
        )
        world.say(
            f'"There now," mamma said. "{remedy.soothe}"'
        )


def settle(world: World, child: Entity, mamma: Entity, worry: Worry) -> None:
    child.meters["sleepy"] += 1
    child.memes["calm"] += 1
    world.say(
        f'{child.id} let out a long breath. "It does not look scary now," {child.pronoun()} said.'
    )
    world.say(
        f'"Most night noises are small once we know them," mamma said. "And if you are unsure, you can always call me."'
    )
    world.say(
        f"Soon {worry.ending_image}"
    )


def tell(
    worry: Worry,
    remedy: Remedy,
    child_name: str = "Lina",
    child_gender: str = "girl",
    mamma_name: str = "Mamma",
    comfort_item: str = "blanket",
    night_sound: str = "the hush of the house",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["sleepy"],
        attrs={"comfort_item": comfort_item},
    ))
    mamma = world.add(Entity(
        id=mamma_name,
        kind="character",
        type="mother",
        role="mamma",
        label="mamma",
        attrs={"night_sound": night_sound},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="bedroom",
        label="bedroom",
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="worry_source",
        label=worry.source_label,
        attrs={"kind": worry.kind, "cause_seen": False},
    ))

    room.meters["dark"] = 1
    child.meters["awake"] = 0.0
    child.meters["sleepy"] = 0.0
    source.meters["active"] = 0.0
    source.meters["noise"] = 1.0 if worry.kind == "noise" else 0.0
    source.meters["shadow"] = 1.0 if worry.kind == "shadow" else 0.0
    source.meters["missing"] = 1.0 if worry.kind == "missing" else 0.0
    child.memes["fear"] = 0.0
    child.memes["calm"] = 0.0
    child.memes["trust"] = 1.0
    child.memes["curiosity"] = 0.0
    mamma.memes["care"] = 0.0
    mamma.memes["comforting"] = 0.0
    room.memes["unrest"] = 0.0
    room.memes["peace"] = 0.0

    world.facts["worry_kind"] = worry.kind
    world.facts["severity"] = worry.severity
    world.facts["predicted_settled"] = False
    world.facts["settled"] = False
    world.facts["resolved_by"] = remedy.id
    world.facts["comfort_item"] = comfort_item

    introduce(world, child, worry)

    world.para()
    notice(world, child, worry)
    call_mamma(world, child, mamma)

    world.para()
    mamma_listens(world, child, mamma, worry)
    reveal(world, child, mamma, worry)

    world.facts["predicted_settled"] = remedy_fits(worry, remedy)
    apply_remedy(world, remedy, narrate=True)

    world.para()
    settle(world, child, mamma, worry)

    world.facts.update(
        child=child,
        mamma=mamma,
        room=room,
        source=source,
        worry=worry,
        remedy=remedy,
        settled=child.memes["fear"] < THRESHOLD and source.meters["active"] < THRESHOLD,
        cause_seen=bool(source.attrs.get("cause_seen")),
    )
    return world


WORRIES = {
    "curtain_wave": Worry(
        id="curtain_wave",
        label="the waving curtain",
        opening="the curtain puffed and swayed, and its shape slid across the wall like a slow gray ghost.",
        source_label="the curtain by the open window",
        kind="shadow",
        severity=2,
        child_line="Mamma, something is waving at me from the wall.",
        mamma_guess="Sometimes a room looks strange when cloth and moonlight move together.",
        reveal="Mamma pointed to the open window, where a little night breeze kept nudging the curtain. The long cloth made the wall-shadow stretch and bend.",
        ending_image="the curtain hung still, the wall turned plain again, and Lina curled down with a sleepy smile.",
        tags={"shadow", "window", "curtain"},
    ),
    "rain_tap": Worry(
        id="rain_tap",
        label="the tapping rain",
        opening="rain began tapping the window ledge in quick little beats that sounded busy in the dark.",
        source_label="the rain on the window",
        kind="noise",
        severity=2,
        child_line="Mamma, there is a tiny knocking in my room.",
        mamma_guess="Rain and wood can make busy sounds at night.",
        reveal="Mamma listened, then touched the cool glass. Raindrops were pattering on the sill and the loose shade cord was ticking softly beside it.",
        ending_image="the room went gentle and hushed, and the rain became only a faraway whisper while Lina's eyes drifted closed.",
        tags={"rain", "noise", "window"},
    ),
    "hall_creak": Worry(
        id="hall_creak",
        label="the creaky floorboard",
        opening="a board in the hallway gave one old creak, and then another, as the house settled for the night.",
        source_label="the hallway floorboard",
        kind="noise",
        severity=1,
        child_line="Mamma, I hear footsteps outside my door.",
        mamma_guess="Sometimes a house talks in little creaks when it cools down.",
        reveal="Mamma opened the door and listened. No one was there at all. The long board near the rug was only making its small bedtime creak.",
        ending_image="the door stood calm, the hallway stayed empty, and Lina snuggled deeper into bed with the blanket warm around her shoulders.",
        tags={"noise", "house"},
    ),
    "lost_bunny": Worry(
        id="lost_bunny",
        label="the missing bunny",
        opening="when Lina reached for her bedtime bunny, her hand found only the cool sheet beside her pillow.",
        source_label="the little bunny under the bed",
        kind="missing",
        severity=1,
        child_line="Mamma, I cannot sleep without Bunny.",
        mamma_guess="Then we should find Bunny before sleep goes any farther.",
        reveal="Mamma bent down and looked under the bed. There was the little bunny, tipped onto one ear beside a slipper.",
        ending_image="Bunny rested under Lina's chin, and the whole bed felt right again as sleep came softly back.",
        tags={"toy", "missing", "comfort"},
    ),
    "branch_shadow": Worry(
        id="branch_shadow",
        label="the branch shadow",
        opening="outside, a thin branch swayed across the moon, and a long crooked shadow kept walking over the ceiling.",
        source_label="the branch outside the window",
        kind="shadow",
        severity=2,
        child_line="Mamma, a tall thing is walking on my ceiling.",
        mamma_guess="Moonlight can make outdoor things look grand and strange indoors.",
        reveal="Mamma drew back the curtain a little and showed Lina the branch moving outside. Each sway on the glass sent a shadow gliding over the room.",
        ending_image="the ceiling grew quiet and pale, and the branch became only a tree outside while Lina gave one last drowsy yawn.",
        tags={"shadow", "tree", "window"},
    ),
}

REMEDIES = {
    "close_window": Remedy(
        id="close_window",
        label="closing the window",
        solves={"noise", "shadow"},
        power=2,
        sense=3,
        action="closed the window softly until the latch clicked and the curtain stopped breathing in and out.",
        soothe="The night is outside now, and your room is resting again.",
        qa_text="She closed the window so the moving air and tapping sounds stopped.",
        tags={"window", "quiet"},
    ),
    "tie_curtain": Remedy(
        id="tie_curtain",
        label="tying back the curtain",
        solves={"shadow"},
        power=2,
        sense=3,
        action="gathered the curtain with a ribbon and tied it back so no shape could drift over the wall.",
        soothe="See? It was only cloth, and now the wall can be just a wall.",
        qa_text="She tied back the curtain so it could not wave and make a scary shadow.",
        tags={"curtain", "shadow"},
    ),
    "check_hall": Remedy(
        id="check_hall",
        label="checking the hallway",
        solves={"noise"},
        power=1,
        sense=3,
        action="opened the door, stood still for a moment, and showed Lina the empty hallway and the old creaky board by the rug.",
        soothe="Nothing is waiting there. It is only the house settling down.",
        qa_text="She checked the hallway and showed that the sound was only the old floorboard.",
        tags={"hall", "noise"},
    ),
    "find_bunny": Remedy(
        id="find_bunny",
        label="finding Bunny",
        solves={"missing"},
        power=1,
        sense=3,
        action="reached under the bed and brought Bunny back into Lina's arms.",
        soothe="There is your Bunny. Sleep can come now.",
        qa_text="She found Bunny under the bed and put it back in Lina's arms.",
        tags={"toy", "comfort"},
    ),
    "nightlight": Remedy(
        id="nightlight",
        label="switching on the night-light",
        solves={"shadow"},
        power=1,
        sense=2,
        action="switched on the little night-light, and a puddle of honey-colored light spread beside the bed.",
        soothe="A small light can help us see what is ordinary.",
        qa_text="She switched on the night-light so the room was easier to see.",
        tags={"light", "shadow"},
    ),
    "humming": Remedy(
        id="humming",
        label="just humming a song",
        solves={"noise", "shadow", "missing"},
        power=0,
        sense=1,
        action="hummed a tune in the doorway.",
        soothe="There, there.",
        qa_text="She only hummed a tune.",
        tags={"song"},
    ),
}

GIRL_NAMES = ["Lina", "Mila", "Nora", "Eva", "Zoe", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Eli", "Theo", "Max", "Sam", "Ben"]
COMFORT_ITEMS = ["blanket", "small pillow", "soft quilt"]
NIGHT_SOUNDS = ["the hush of the house", "the faraway rain", "the quiet clock downstairs"]


@dataclass
class StoryParams:
    worry: str
    remedy: str
    child_name: str
    child_gender: str
    comfort_item: str
    night_sound: str
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
    "shadow": [
        (
            "What is a shadow?",
            "A shadow is a dark shape made when light is blocked. Shadows can look strange at night even when the real thing is ordinary.",
        )
    ],
    "noise": [
        (
            "Why does a house make little noises at night?",
            "Wood and pipes can creak or tick as the air gets cooler and things settle. Small night noises do not always mean someone is there.",
        )
    ],
    "window": [
        (
            "Why can a window make bedtime noises?",
            "Rain, wind, and loose cords can tap or rattle near a window. When the room is quiet, those little sounds can seem much bigger.",
        )
    ],
    "curtain": [
        (
            "Why can a curtain look spooky in the dark?",
            "A curtain moves softly and can make big shapes when moonlight shines behind it. Once the cloth is still, the scary shape usually disappears.",
        )
    ],
    "comfort": [
        (
            "Why do children like to sleep with a comfort toy?",
            "A comfort toy feels familiar and safe. Holding it can help a child relax at bedtime.",
        )
    ],
    "rain": [
        (
            "Why does rain sound louder at night?",
            "At night there is less busy daytime noise, so the tapping rain stands out more. Quiet rooms make tiny sounds easier to hear.",
        )
    ],
    "light": [
        (
            "What does a night-light do?",
            "A night-light gives a small, gentle glow so the room is easier to see. It helps children notice what is ordinary without making the room bright like daytime.",
        )
    ],
    "quiet": [
        (
            "How can a room become quieter for sleep?",
            "Closing a window, settling loose things, or stopping a tapping sound can make a room calmer. Quiet helps the body feel ready to rest.",
        )
    ],
    "toy": [
        (
            "Why can losing a bedtime toy feel upsetting?",
            "A bedtime toy is part of a child's usual routine. When it is missing, the bed can feel wrong until the toy is found again.",
        )
    ],
    "house": [
        (
            "What does it mean when people say a house is settling?",
            "It means the house is making tiny creaks as materials cool and shift a little. The house is not waking up; it is simply resting in its own way.",
        )
    ],
}
KNOWLEDGE_ORDER = ["shadow", "noise", "window", "curtain", "rain", "light", "quiet", "toy", "comfort", "house"]


def generation_prompts(world: World) -> list[str]:
    worry = world.facts["worry"]
    remedy = world.facts["remedy"]
    child = world.facts["child"]
    return [
        'Write a gentle bedtime story with dialogue that includes the word "mamma".',
        f"Tell a bedtime story where {child.id} feels scared by {worry.label}, calls for mamma, and learns the real cause.",
        f"Write a cozy night story in which mamma solves {worry.label} by {remedy.label} and the child falls asleep peacefully.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    worry = world.facts["worry"]
    remedy = world.facts["remedy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and mamma at bedtime. {child.id} feels worried in the dark, and mamma comes to help.",
        ),
        (
            "What frightened the child at first?",
            f"{worry.label.capitalize()} frightened {child.id} at first. In the dark it seemed bigger and stranger than it really was.",
        ),
        (
            "Why did the child call for mamma?",
            f'{child.id} called for mamma because the worry felt real and scary in the quiet room. {child.pronoun().capitalize()} wanted a grown-up to look with {child.pronoun("object")} and explain what was happening.',
        ),
    ]
    if world.facts.get("cause_seen"):
        qa.append(
            (
                "What was the worry really caused by?",
                f"It was really caused by {worry.source_label}. When mamma looked closely, she showed the small ordinary thing behind the scary feeling.",
            )
        )
    if world.facts.get("settled"):
        qa.append(
            (
                "How did mamma solve the problem?",
                f"{remedy.qa_text} That changed the room itself, not just the feeling, so the fear could fade for real.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly and safely, with {child.id} calm in bed again. Once the cause was understood and fixed, sleep could come back.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    worry = world.facts["worry"]
    remedy = world.facts["remedy"]
    tags = set(worry.tags) | set(remedy.tags)
    if "comfort" in worry.tags or "comfort" in remedy.tags or worry.kind == "missing":
        tags.add("comfort")
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
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        worry="curtain_wave",
        remedy="tie_curtain",
        child_name="Lina",
        child_gender="girl",
        comfort_item="blanket",
        night_sound="the hush of the house",
    ),
    StoryParams(
        worry="rain_tap",
        remedy="close_window",
        child_name="Noah",
        child_gender="boy",
        comfort_item="small pillow",
        night_sound="the faraway rain",
    ),
    StoryParams(
        worry="hall_creak",
        remedy="check_hall",
        child_name="Maya",
        child_gender="girl",
        comfort_item="soft quilt",
        night_sound="the quiet clock downstairs",
    ),
    StoryParams(
        worry="lost_bunny",
        remedy="find_bunny",
        child_name="Leo",
        child_gender="boy",
        comfort_item="blanket",
        night_sound="the hush of the house",
    ),
    StoryParams(
        worry="branch_shadow",
        remedy="close_window",
        child_name="Anna",
        child_gender="girl",
        comfort_item="small pillow",
        night_sound="the faraway rain",
    ),
]


ASP_RULES = r"""
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
fits(W, R) :- worry(W), remedy(R), kind(W, K), solves(R, K), severity(W, SW), power(R, PR), PR >= SW.
valid(W, R) :- fits(W, R), sensible(R).

chosen_valid :- chosen_worry(W), chosen_remedy(R), valid(W, R).
outcome(settled) :- chosen_valid.
outcome(unsettled) :- chosen_worry(_), chosen_remedy(_), not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid, worry in WORRIES.items():
        lines.append(asp.fact("worry", wid))
        lines.append(asp.fact("kind", wid, worry.kind))
        lines.append(asp.fact("severity", wid, worry.severity))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("power", rid, remedy.power))
        lines.append(asp.fact("sense", rid, remedy.sense))
        for kind in sorted(remedy.solves):
            lines.append(asp.fact("solves", rid, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_worry", params.worry),
            asp.fact("chosen_remedy", params.remedy),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    worry = WORRIES[params.worry]
    remedy = REMEDIES[params.remedy]
    return "settled" if remedy_fits(worry, remedy) else "unsettled"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: bedtime worries, dialogue, and mamma's gentle fix."
    )
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible worry/remedy set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.worry and args.remedy:
        worry = WORRIES[args.worry]
        remedy = REMEDIES[args.remedy]
        if not remedy_fits(worry, remedy):
            raise StoryError(explain_rejection(worry, remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.worry is None or combo[0] == args.worry)
        and (args.remedy is None or combo[1] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    worry_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(
        worry=worry_id,
        remedy=remedy_id,
        child_name=name,
        child_gender=gender,
        comfort_item=rng.choice(COMFORT_ITEMS),
        night_sound=rng.choice(NIGHT_SOUNDS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.worry not in WORRIES:
        raise StoryError(f"(Unknown worry: {params.worry})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    worry = WORRIES[params.worry]
    remedy = REMEDIES[params.remedy]
    if not remedy_fits(worry, remedy):
        raise StoryError(explain_rejection(worry, remedy))

    world = tell(
        worry=worry,
        remedy=remedy,
        child_name=params.child_name,
        child_gender=params.child_gender,
        comfort_item=params.comfort_item,
        night_sound=params.night_sound,
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid combos match ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    python_sens = {r.id for r in sensible_remedies()}
    clingo_sens = set(asp_sensible())
    if python_sens == clingo_sens:
        print(f"OK: sensible remedies match ({sorted(python_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: python={sorted(python_sens)} clingo={sorted(clingo_sens)}")

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Empty story from smoke test.")
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(smoke, trace=True, qa=True, header="### smoke")
            rendered = buf.getvalue()
        if "mamma" not in smoke.story.lower():
            raise StoryError("Smoke story did not include required word 'mamma'.")
        if not rendered.strip():
            raise StoryError("Emit produced no output in smoke test.")
        print("OK: smoke generate/emit test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (worry, remedy) combos:\n")
        for worry, remedy in combos:
            print(f"  {worry:14} {remedy}")
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
            header = f"### {p.child_name}: {p.worry} with {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
