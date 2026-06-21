#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/linger_auditorium_tennis_suspense_foreshadowing_mystery.py
======================================================================================

A standalone story world about a child who lingers in a school auditorium after an
event, notices a clue, hears a mysterious sound, and discovers that the scary
secret has an ordinary cause connected to tennis gear.

This world is built for child-facing mystery stories with suspense and
foreshadowing. The source of the mystery is always reasonable: a tennis item left
in or near the auditorium makes a sound that could feel spooky in a dim, empty
space. The early clue must honestly point toward that source.

Run it
------
    python storyworlds/worlds/gpt-5.4/linger_auditorium_tennis_suspense_foreshadowing_mystery.py
    python storyworlds/worlds/gpt-5.4/linger_auditorium_tennis_suspense_foreshadowing_mystery.py --event assembly --source ball_bag --clue yellow_fuzz
    python storyworlds/worlds/gpt-5.4/linger_auditorium_tennis_suspense_foreshadowing_mystery.py --event concert --source ball_bag
    python storyworlds/worlds/gpt-5.4/linger_auditorium_tennis_suspense_foreshadowing_mystery.py --all
    python storyworlds/worlds/gpt-5.4/linger_auditorium_tennis_suspense_foreshadowing_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/linger_auditorium_tennis_suspense_foreshadowing_mystery.py --verify
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
NOTICE_THRESHOLD = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Event:
    id: str
    title: str
    opening: str
    leftovers: str
    source_ids: set[str] = field(default_factory=set)
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
class Reason:
    id: str
    linger_text: str
    near_text: str
    goal_text: str
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
    place: str
    sound: str
    reveal: str
    settle: str
    clue_kinds: set[str] = field(default_factory=set)
    moving: bool = True
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
class Clue:
    id: str
    label: str
    early_text: str
    notice_text: str
    kind: str = ""
    strength: int = 1
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
class Companion:
    id: str
    label: str
    type: str
    role: str
    entrance: str
    whisper: str
    adult: bool = False
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
    def __init__(self, event: Event) -> None:
        self.event = event
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
        clone = World(self.event)
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


def _r_noise_spreads(world: World) -> list[str]:
    hero = world.get("hero")
    source = world.get("source")
    room = world.get("room")
    out: list[str] = []
    if source.meters["noise"] >= THRESHOLD:
        sig = ("noise", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            hero.memes["curiosity"] += 1
            room.memes["suspense"] += 1
            out.append("__noise__")
    return out


def _r_clue_focus(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["clue_seen"] >= THRESHOLD:
        sig = ("clue_focus", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["focus"] += 1
            return ["__clue__"]
    return []


def _r_reveal_relief(world: World) -> list[str]:
    hero = world.get("hero")
    room = world.get("room")
    source = world.get("source")
    out: list[str] = []
    if source.meters["found"] >= THRESHOLD and source.meters["explained"] >= THRESHOLD:
        sig = ("relief", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] = 0.0
            hero.memes["relief"] += 1
            room.memes["suspense"] = 0.0
            out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="noise_spreads", tag="emotional", apply=_r_noise_spreads),
    Rule(name="clue_focus", tag="emotional", apply=_r_clue_focus),
    Rule(name="reveal_relief", tag="emotional", apply=_r_reveal_relief),
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


def clue_matches(source: Source, clue: Clue) -> bool:
    return clue.kind == "generic" or clue.kind in source.clue_kinds


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for event_id, event in EVENTS.items():
        for source_id in sorted(event.source_ids):
            source = SOURCES[source_id]
            for clue_id, clue in CLUES.items():
                if clue_matches(source, clue):
                    combos.append((event_id, source_id, clue_id))
    return combos


def notice_score(source: Source, clue: Clue, companion: Companion) -> int:
    return clue.strength + (1 if companion.adult else 0)


def outcome_name(params: "StoryParams") -> str:
    source = SOURCES[params.source]
    clue = CLUES[params.clue]
    companion = COMPANIONS[params.companion]
    return "noticed" if notice_score(source, clue, companion) >= NOTICE_THRESHOLD else "called_help"


def predict_notice(source: Source, clue: Clue, companion: Companion) -> dict:
    return {
        "score": notice_score(source, clue, companion),
        "noticed": notice_score(source, clue, companion) >= NOTICE_THRESHOLD,
    }


def introduce(world: World, hero: Entity, event: Event, reason: Reason) -> None:
    world.say(
        f"After the {event.title}, most families had already gone home, but {hero.id} did not hurry away."
    )
    world.say(
        f"{hero.pronoun().capitalize()} chose to linger in the auditorium because {reason.linger_text}."
    )
    world.say(event.opening)


def foreshadow(world: World, hero: Entity, clue: Clue, reason: Reason) -> None:
    hero.meters["clue_seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On the way toward {reason.near_text}, {hero.pronoun()} noticed {clue.early_text}."
    )
    world.say(clue.notice_text)


def bring_companion(world: World, hero: Entity, companion: Entity, cfg: Companion) -> None:
    if cfg.role == "friend":
        world.say(
            f"{cfg.entrance} \"Did you find it yet?\" {companion.id} whispered."
        )
    else:
        world.say(cfg.entrance)


def darken(world: World, hero: Entity) -> None:
    room = world.get("room")
    room.meters["dim"] += 1
    hero.memes["worry"] += 1
    world.say(
        "The work lights by the stage clicked off one row at a time, and the empty auditorium seemed to grow larger around the red seats."
    )


def start_noise(world: World, source: Entity, source_cfg: Source) -> None:
    source.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a sound came from {source_cfg.place}: {source_cfg.sound}."
    )


def react(world: World, hero: Entity, companion: Entity, companion_cfg: Companion) -> None:
    if companion_cfg.role == "friend":
        world.say(
            f"{hero.id} stopped so quickly that {companion.id} stopped too. {companion_cfg.whisper}"
        )
    else:
        world.say(
            f"{hero.id} froze for a breath, but {companion.id} stayed calm nearby."
        )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"For one tick of the clock, the noise felt like a secret that did not want to be found."
        )


def investigate(world: World, hero: Entity, clue: Clue, companion: Entity, companion_cfg: Companion) -> None:
    world.say(
        f"{hero.id} remembered {clue.label} and took a careful step toward the sound."
    )
    if companion_cfg.role == "friend":
        world.say(
            f"{companion.id} came close enough that their sleeves brushed."
        )
    else:
        world.say(
            f"{companion.id} lifted a small flashlight and aimed its circle of light ahead."
        )


def reveal_by_notice(world: World, hero: Entity, companion: Entity, source: Entity,
                     source_cfg: Source, clue: Clue, companion_cfg: Companion) -> None:
    source.meters["found"] += 1
    source.meters["explained"] += 1
    propagate(world, narrate=False)
    if companion_cfg.adult:
        world.say(
            f"In the beam, {clue.label} suddenly made sense. There was {source_cfg.reveal}."
        )
    else:
        world.say(
            f"Then {hero.id} saw how {clue.label} fit the mystery. There was {source_cfg.reveal}."
        )
    world.say(source_cfg.settle)


def call_for_help(world: World, hero: Entity, companion: Entity, source: Entity,
                  source_cfg: Source, caretaker: Entity, clue: Clue) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"The sound came again, closer this time, and {hero.id}'s voice came out as a small call. \"Who's there?\""
    )
    world.say(
        f"At once, {caretaker.id} answered from the side door and hurried over with a brighter flashlight."
    )
    source.meters["found"] += 1
    source.meters["explained"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The stronger light slid across {clue.label} and then onto the truth: {source_cfg.reveal}."
    )
    world.say(
        f"{caretaker.id} smiled, gentle now that the mystery was solved. {source_cfg.settle}"
    )


def ending(world: World, hero: Entity, companion: Entity, reason: Reason,
           source_cfg: Source, companion_cfg: Companion) -> None:
    hero.memes["bravery"] += 1
    room = world.get("room")
    room.meters["safe"] += 1
    if companion_cfg.role == "friend":
        world.say(
            f"{hero.id} let out a laugh that sounded much bigger than the fear had been."
        )
        world.say(
            f"Together they finished {reason.goal_text}, and the auditorium no longer felt full of secrets."
        )
    else:
        world.say(
            f"{hero.id} breathed out slowly and smiled."
        )
        world.say(
            f"{reason.goal_text.capitalize()} was easy after that, because the auditorium felt like an ordinary room again."
        )
    world.say(
        f"When they left, {hero.id} glanced back once more. The mystery had only been tennis after all, but the clue had been there from the start."
    )


def tell(event: Event, reason: Reason, source_cfg: Source, clue: Clue, companion_cfg: Companion,
         hero_name: str = "Nora", hero_type: str = "girl",
         companion_name: str = "Eli", companion_type: str = "boy") -> World:
    world = World(event)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_type,
        role=companion_cfg.role,
        label=companion_cfg.label,
        attrs={"adult": companion_cfg.adult},
        tags=set(companion_cfg.tags),
    ))
    caretaker = world.add(Entity(id="Ms. Vale", kind="character", type="woman", role="caretaker", label="caretaker"))
    room = world.add(Entity(id="room", type="place", label="auditorium"))
    source = world.add(Entity(id="source", type="thing", label=source_cfg.label, tags=set(source_cfg.tags)))

    world.facts["predicted_notice"] = predict_notice(source_cfg, clue, companion_cfg)
    world.facts["event"] = event
    world.facts["reason_cfg"] = reason
    world.facts["source_cfg"] = source_cfg
    world.facts["clue_cfg"] = clue
    world.facts["companion_cfg"] = companion_cfg
    world.facts["caretaker"] = caretaker
    world.facts["hero"] = hero
    world.facts["companion"] = companion
    world.facts["source"] = source
    world.facts["room"] = room

    introduce(world, hero, event, reason)
    foreshadow(world, hero, clue, reason)
    world.para()
    bring_companion(world, hero, companion, companion_cfg)
    darken(world, hero)
    start_noise(world, source, source_cfg)
    react(world, hero, companion, companion_cfg)
    world.para()
    investigate(world, hero, clue, companion, companion_cfg)
    if predict_notice(source_cfg, clue, companion_cfg)["noticed"]:
        reveal_by_notice(world, hero, companion, source, source_cfg, clue, companion_cfg)
        outcome = "noticed"
    else:
        call_for_help(world, hero, companion, source, source_cfg, caretaker, clue)
        outcome = "called_help"
    world.para()
    ending(world, hero, companion, reason, source_cfg, companion_cfg)

    world.facts["outcome"] = outcome
    world.facts["mystery_sound"] = source_cfg.sound
    world.facts["resolved"] = source.meters["found"] >= THRESHOLD
    return world


EVENTS = {
    "assembly": Event(
        id="assembly",
        title="school assembly",
        opening="The stage still held a few club signs and folded stands from the busy afternoon.",
        leftovers="club signs and folded stands",
        source_ids={"ball_bag", "racket_tap"},
        tags={"school", "auditorium"},
    ),
    "concert": Event(
        id="concert",
        title="winter concert",
        opening="Programs still lay on some seats, and a lost-and-found table waited by the back curtain.",
        leftovers="programs and a lost-and-found table",
        source_ids={"tube_box", "racket_tap"},
        tags={"music", "auditorium"},
    ),
    "fair": Event(
        id="fair",
        title="family fair",
        opening="Prize baskets and club displays had been lined along the side aisle, and a few had not been packed away yet.",
        leftovers="prize baskets and club displays",
        source_ids={"ball_bag", "tube_box", "racket_tap"},
        tags={"fair", "auditorium"},
    ),
}

REASONS = {
    "scarf": Reason(
        id="scarf",
        linger_text="she was looking for her blue scarf",
        near_text="the last row of seats",
        goal_text="finding the scarf",
        tags={"lost_item"},
    ),
    "program": Reason(
        id="program",
        linger_text="he wanted to pick up the program with his drawing on the cover",
        near_text="the edge of the stage",
        goal_text="getting the special program",
        tags={"program"},
    ),
    "note": Reason(
        id="note",
        linger_text="she was checking under the seats for the thank-you note her teacher had given her",
        near_text="the center aisle",
        goal_text="saving the note",
        tags={"note"},
    ),
}

SOURCES = {
    "ball_bag": Source(
        id="ball_bag",
        label="mesh bag of tennis balls",
        place="behind the side curtain",
        sound="soft thump... thump... then the round skitter of something rolling across the floorboards",
        reveal="a mesh bag had slipped against a prop trunk, and one loose tennis ball kept bumping out and rolling back",
        settle="The bag was tied shut properly, the wandering ball was tucked back in, and the sound stopped at once.",
        clue_kinds={"ball"},
        moving=True,
        tags={"tennis_ball", "sound"},
    ),
    "tube_box": Source(
        id="tube_box",
        label="box of tennis-ball tubes",
        place="under the back curtain",
        sound="a papery bump, then a hollow roll like a can nudging wood",
        reveal="a half-open box of tennis-ball tubes had tipped sideways, and one bright tube was rocking against the leg of a chair",
        settle="Once the box was set straight, the rocking tube rested still and the mystery ended.",
        clue_kinds={"tube"},
        moving=True,
        tags={"tennis_ball", "tube", "sound"},
    ),
    "racket_tap": Source(
        id="racket_tap",
        label="tennis racket",
        place="the row beside the aisle",
        sound="tap... tap... tap, as if careful fingers were knocking from the dark",
        reveal="a tennis racket had been left leaning against a seat, and the vent above it kept nudging the handle so the frame tapped the wood",
        settle="When the racket was laid flat across the seat, the tapping quit and the room lost its shiver.",
        clue_kinds={"racket"},
        moving=False,
        tags={"tennis_racket", "sound", "air"},
    ),
}

CLUES = {
    "yellow_fuzz": Clue(
        id="yellow_fuzz",
        label="the tiny yellow fuzz on the carpet",
        early_text="a tiny streak of yellow fuzz near the curtain",
        notice_text="It was only a little thing, but it made her wonder what had been dragged through the auditorium.",
        kind="ball",
        strength=2,
        tags={"tennis_ball", "clue"},
    ),
    "rubber_smell": Clue(
        id="rubber_smell",
        label="the clean rubbery smell",
        early_text="a clean rubbery smell that did not belong with dusty stage curtains",
        notice_text="The smell lingered in one corner as if some sporty secret had been left behind.",
        kind="ball",
        strength=1,
        tags={"tennis_ball", "smell", "clue"},
    ),
    "bright_tube": Clue(
        id="bright_tube",
        label="the bright green tube cap",
        early_text="a bright green tube cap peeking out from under a folded program",
        notice_text="She almost walked past it, but the odd little cap felt like the first page of a mystery.",
        kind="tube",
        strength=2,
        tags={"tube", "clue"},
    ),
    "green_strings": Clue(
        id="green_strings",
        label="the loose green strings",
        early_text="two loose green strings caught on the arm of a seat",
        notice_text="They looked too neat to be thread and too springy to be ribbon.",
        kind="racket",
        strength=2,
        tags={"tennis_racket", "clue"},
    ),
    "sports_sign": Clue(
        id="sports_sign",
        label="the sign for the tennis club",
        early_text="a signboard that said TENNIS CLUB leaning near the wall",
        notice_text="It was easy to ignore in the daylight crowd, but in the empty room it seemed to point somewhere on purpose.",
        kind="generic",
        strength=1,
        tags={"tennis", "clue"},
    ),
}

COMPANIONS = {
    "friend": Companion(
        id="friend",
        label="friend",
        type="girl",
        role="friend",
        entrance="A moment later, a classmate padded back in from the lobby.",
        whisper='"Did you hear that too?"',
        adult=False,
        tags={"friend"},
    ),
    "coach": Companion(
        id="coach",
        label="coach",
        type="man",
        role="coach",
        entrance="Coach Reed was still stacking signs near the side door and looked over at once.",
        whisper="",
        adult=True,
        tags={"coach"},
    ),
    "custodian": Companion(
        id="custodian",
        label="custodian",
        type="man",
        role="custodian",
        entrance="Mr. Dale the custodian was checking the aisle lights and came closer when he saw the worried face.",
        whisper="",
        adult=True,
        tags={"custodian"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Anna"]
BOY_NAMES = ["Eli", "Ben", "Max", "Theo", "Sam", "Leo"]


@dataclass
class StoryParams:
    event: str
    reason: str
    source: str
    clue: str
    companion: str
    hero_name: str
    hero_gender: str
    companion_name: str
    companion_gender: str
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
    "auditorium": [
        ("What is an auditorium?",
         "An auditorium is a big room with many seats and a stage for shows, concerts, and school events.")
    ],
    "tennis_ball": [
        ("Why does a tennis ball bounce and roll so easily?",
         "A tennis ball is light and springy, so it can bounce and roll when it gets loose. On a hard floor, that can make surprising sounds.")
    ],
    "tennis_racket": [
        ("What is a tennis racket?",
         "A tennis racket is the tool players use to hit a tennis ball. It has strings stretched across a frame.")
    ],
    "tube": [
        ("Why are tennis balls sometimes kept in tubes?",
         "Tennis balls are often packed in round tubes so they stay together neatly. If one tube tips over, it can roll like a little can.")
    ],
    "sound": [
        ("Why can a room sound spooky when it is empty?",
         "An empty room can make small sounds seem bigger because the noise bounces around. When you do not know the cause yet, your imagination can make it feel mysterious.")
    ],
    "clue": [
        ("What is a clue?",
         "A clue is a small sign that helps you figure something out. In a mystery, clues often make sense later when the secret is revealed.")
    ],
    "coach": [
        ("What does a coach do?",
         "A coach teaches a sport, helps players practice, and takes care of the equipment for the team.")
    ],
    "custodian": [
        ("What does a custodian do at a school?",
         "A custodian helps keep the school clean, safe, and tidy. That can include checking rooms after an event is over.")
    ],
}
KNOWLEDGE_ORDER = ["auditorium", "clue", "sound", "tennis_ball", "tube", "tennis_racket", "coach", "custodian"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    event = f["event"]
    reason = f["reason_cfg"]
    source = f["source_cfg"]
    clue = f["clue_cfg"]
    outcome = f["outcome"]
    if outcome == "called_help":
        return [
            f'Write a short mystery for a 3-to-5-year-old that includes the words "linger", "auditorium", and "tennis".',
            f"Tell a suspenseful but gentle story where {hero.id} lingers in the auditorium because {reason.linger_text}, notices {clue.label}, hears a strange sound, and needs a grown-up to help reveal that it came from {source.label}.",
            "Write a foreshadowing story in which an early clue seems small at first, but later explains a scary sound in an empty school auditorium."
        ]
    return [
        f'Write a short mystery for a 3-to-5-year-old that includes the words "linger", "auditorium", and "tennis".',
        f"Tell a suspenseful but gentle story where {hero.id} lingers in the auditorium after a {event.title}, notices {clue.label}, and solves the mystery of a strange sound.",
        "Write a foreshadowing story in which an early clue quietly points to the true cause of a spooky noise, so the ending feels surprising and fair."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    reason = f["reason_cfg"]
    source_cfg = f["source_cfg"]
    clue = f["clue_cfg"]
    event = f["event"]
    caretaker = f["caretaker"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who stayed behind after the {event.title} and lingered in the auditorium. The mystery begins because {hero.pronoun()} was still there when the room grew quiet."
        ),
        (
            f"Why did {hero.id} stay in the auditorium?",
            f"{hero.id} stayed because {reason.linger_text}. That small reason kept {hero.pronoun('object')} in the room long enough to hear the strange sound."
        ),
        (
            "What was the early clue?",
            f"The early clue was {clue.label}. It seemed small at first, but later it pointed straight to the tennis mystery."
        ),
        (
            "Why did the auditorium feel scary for a moment?",
            f"It felt scary because the room had grown dim and almost empty, so every little sound seemed larger. Not knowing the cause made the noise feel mysterious."
        ),
    ]
    if outcome == "noticed":
        qa.append(
            (
                "How was the mystery solved?",
                f"{hero.id} followed the clue and realized the sound came from {source_cfg.reveal}. The foreshadowing mattered because {clue.label} had already pointed toward tennis."
            )
        )
        qa.append(
            (
                f"How did {hero.id} feel at the end?",
                f"{hero.id} felt relieved and a little proud. Once the cause was explained, the auditorium stopped feeling spooky and went back to feeling ordinary."
            )
        )
    else:
        qa.append(
            (
                "Did anyone help solve the mystery?",
                f"Yes. {hero.id} called out, and {caretaker.id} came with a brighter flashlight to help. The extra light made it clear that the sound came from {source_cfg.label}, not anything magical or dangerous."
            )
        )
        qa.append(
            (
                f"Why did {hero.id} call for help?",
                f"{hero.id} had a clue, but the sound came again in the dark and felt too uncertain to solve alone. Calling for help was wise because a grown-up could check the room safely and explain what was really happening."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"auditorium", "sound", "clue"}
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["clue_cfg"].tags)
    tags |= set(f["companion_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(event: Event, source: Source, clue: Optional[Clue] = None) -> str:
    if source.id not in event.source_ids:
        allowed = ", ".join(sorted(event.source_ids))
        return (
            f"(No story: after a {event.title}, {source.label} is not a reasonable leftover in this auditorium setup. "
            f"Try one of: {allowed}.)"
        )
    if clue is not None and not clue_matches(source, clue):
        return (
            f"(No story: {clue.label} does not honestly foreshadow {source.label}. "
            f"The clue must point toward the real tennis cause of the sound.)"
        )
    return "(No story: this combination is not reasonable in the world model.)"


ASP_RULES = r"""
valid(E,S,C) :- event(E), affords_source(E,S), source(S), clue(C), clue_matches(S,C).

notice_score(V) :- chosen_clue(C), clue_strength(C, CS), chosen_companion(P), companion_bonus(P, PB), V = CS + PB.
noticed :- notice_score(V), notice_threshold(T), V >= T.
outcome(noticed) :- noticed.
outcome(called_help) :- not noticed.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for event_id, event in EVENTS.items():
        lines.append(asp.fact("event", event_id))
        for source_id in sorted(event.source_ids):
            lines.append(asp.fact("affords_source", event_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for kind in sorted(source.clue_kinds):
            lines.append(asp.fact("source_kind", source_id, kind))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_strength", clue_id, clue.strength))
        if clue.kind == "generic":
            lines.append(asp.fact("clue_matches_any", clue_id))
        else:
            lines.append(asp.fact("clue_kind", clue_id, clue.kind))
    for companion_id, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", companion_id))
        lines.append(asp.fact("companion_bonus", companion_id, 1 if companion.adult else 0))
    lines.append(asp.fact("notice_threshold", NOTICE_THRESHOLD))
    lines.append("clue_matches(S,C) :- clue_matches_any(C), source(S).")
    lines.append("clue_matches(S,C) :- clue_kind(C,K), source_kind(S,K).")
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_companion", params.companion),
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_name(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generate/emit passed.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child lingers in an auditorium, a tennis mystery stirs, and the clue points to the truth."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--reason", choices=REASONS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.event and args.source:
        event = EVENTS[args.event]
        source = SOURCES[args.source]
        if args.source not in event.source_ids:
            raise StoryError(explain_rejection(event, source))
    if args.source and args.clue:
        source = SOURCES[args.source]
        clue = CLUES[args.clue]
        if not clue_matches(source, clue):
            raise StoryError(explain_rejection(EVENTS[args.event] if args.event else next(iter(EVENTS.values())), source, clue))

    combos = [
        combo for combo in valid_combos()
        if (args.event is None or combo[0] == args.event)
        and (args.source is None or combo[1] == args.source)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    event_id, source_id, clue_id = rng.choice(sorted(combos))
    reason_id = args.reason or rng.choice(sorted(REASONS))
    companion_id = args.companion or rng.choice(sorted(COMPANIONS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    companion_cfg = COMPANIONS[companion_id]
    if companion_cfg.adult:
        companion_gender = "boy"
        companion_name = "Coach Reed" if companion_id == "coach" else "Mr. Dale"
    else:
        companion_gender = "girl" if hero_gender == "boy" else "boy"
        companion_name = _pick_name(rng, companion_gender, avoid=hero_name)

    return StoryParams(
        event=event_id,
        reason=reason_id,
        source=source_id,
        clue=clue_id,
        companion=companion_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
    )


def _validate_params(params: StoryParams) -> None:
    if params.event not in EVENTS:
        raise StoryError(f"(Unknown event: {params.event})")
    if params.reason not in REASONS:
        raise StoryError(f"(Unknown reason: {params.reason})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.companion not in COMPANIONS:
        raise StoryError(f"(Unknown companion: {params.companion})")
    event = EVENTS[params.event]
    source = SOURCES[params.source]
    clue = CLUES[params.clue]
    if source.id not in event.source_ids:
        raise StoryError(explain_rejection(event, source))
    if not clue_matches(source, clue):
        raise StoryError(explain_rejection(event, source, clue))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        event=EVENTS[params.event],
        reason=REASONS[params.reason],
        source_cfg=SOURCES[params.source],
        clue=CLUES[params.clue],
        companion_cfg=COMPANIONS[params.companion],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        companion_name=params.companion_name,
        companion_type=params.companion_gender,
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
        event="assembly",
        reason="scarf",
        source="ball_bag",
        clue="yellow_fuzz",
        companion="friend",
        hero_name="Nora",
        hero_gender="girl",
        companion_name="Eli",
        companion_gender="boy",
    ),
    StoryParams(
        event="concert",
        reason="program",
        source="tube_box",
        clue="sports_sign",
        companion="friend",
        hero_name="Max",
        hero_gender="boy",
        companion_name="Lily",
        companion_gender="girl",
    ),
    StoryParams(
        event="fair",
        reason="note",
        source="racket_tap",
        clue="green_strings",
        companion="custodian",
        hero_name="Ava",
        hero_gender="girl",
        companion_name="Mr. Dale",
        companion_gender="boy",
    ),
    StoryParams(
        event="fair",
        reason="scarf",
        source="tube_box",
        clue="bright_tube",
        companion="coach",
        hero_name="Leo",
        hero_gender="boy",
        companion_name="Coach Reed",
        companion_gender="boy",
    ),
    StoryParams(
        event="assembly",
        reason="note",
        source="racket_tap",
        clue="sports_sign",
        companion="friend",
        hero_name="Mia",
        hero_gender="girl",
        companion_name="Theo",
        companion_gender="boy",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (event, source, clue) combos:\n")
        for event_id, source_id, clue_id in combos:
            print(f"  {event_id:9} {source_id:11} {clue_id}")
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
            header = f"### {p.hero_name}: {p.event}, {p.source}, {p.clue} ({outcome_name(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
