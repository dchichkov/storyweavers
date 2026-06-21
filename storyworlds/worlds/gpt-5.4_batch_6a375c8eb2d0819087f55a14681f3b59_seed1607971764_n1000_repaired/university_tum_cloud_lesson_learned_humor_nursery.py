#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py
================================================================================

A small standalone storyworld in a playful nursery-rhyme voice.

Domain:
    A child visits a TUM university open day, spots a cloud-shaped treat set
    too high, and is tempted to climb on something silly instead of asking for
    help. The shortcut leads to a funny wobble and a soft lesson: ask first,
    and use the proper step stool.

Run it
------
    python storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py
    python storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py --booth bakery --treat cloud_bun
    python storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py --treat apple
    python storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py --response hop
    python storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py --all
    python storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/university_tum_cloud_lesson_learned_humor_nursery.py --verify
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
SENSE_MIN = 2
EAGER_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    unstable: bool = False
    edible: bool = False
    helper: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "professor_f"}
        male = {"boy", "father", "man", "professor_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "professor_f": "professor",
            "professor_m": "professor",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Booth:
    id: str
    place: str
    sparkle: str
    host_line: str
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
class Treat:
    id: str
    label: str
    phrase: str
    height: int
    squish: int
    cream: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"

    @property
    def The(self) -> str:
        return f"The {self.label}"
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
class Shortcut:
    id: str
    label: str
    phrase: str
    wobble: int
    reach: int
    nudge: str
    unstable: bool = True
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
class Response:
    id: str
    sense: int
    reach: int
    text: str
    short: str
    fail: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"reacher", "watcher"}]

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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    support = world.get("support")
    if child.meters["climbing"] >= THRESHOLD and support.unstable:
        sig = ("wobble", child.id, support.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["wobble"] += support.meters["wobble_power"]
            child.memes["alarm"] += 1
            out.append("__wobble__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    treat = world.get("treat")
    needed = treat.meters["height_need"]
    if child.meters["reaching"] >= THRESHOLD and child.meters["wobble"] >= THRESHOLD:
        sig = ("drop", child.id, treat.id)
        if sig not in world.fired:
            world.fired.add(sig)
            treat.meters["fallen"] += 1
            treat.meters["squashed"] += treat.meters["squish_power"]
            child.memes["embarrassed"] += 1
            out.append("__drop__")
    elif child.meters["reaching"] >= THRESHOLD and child.meters["height_gain"] >= needed:
        sig = ("grab", child.id, treat.id)
        if sig not in world.fired:
            world.fired.add(sig)
            treat.meters["held"] += 1
            out.append("__grab__")
    return out


def _r_splat(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    treat = world.get("treat")
    if treat.meters["fallen"] >= THRESHOLD:
        sig = ("splat", treat.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["sticky_tum"] += 1
            child.memes["embarrassed"] += 1
            out.append("__splat__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="drop", tag="physical", apply=_r_drop),
    Rule(name="splat", tag="physical", apply=_r_splat),
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


def treat_needs_reach(treat: Treat, shortcut: Shortcut) -> bool:
    return treat.height > 1 and shortcut.unstable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, reacher_age: int, watcher_age: int, trait: str) -> bool:
    older = relation == "siblings" and watcher_age > reacher_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > EAGER_INIT


def can_help(response: Response, treat: Treat) -> bool:
    return response.reach >= treat.height


def explain_rejection(treat: Treat, shortcut: Shortcut) -> str:
    if treat.height <= 1:
        return (
            f"(No story: {treat.the} sits low enough already, so nobody needs to climb "
            f"on {shortcut.phrase}. Pick a higher cloud treat for an honest problem.)"
        )
    return "(No story: this combination does not make a reasonable reaching problem.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a sensible helper like {better}.)"
    )


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["climbing"] += 1
    child.meters["reaching"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("child").meters["wobble"],
        "fallen": sim.get("treat").meters["fallen"] >= THRESHOLD,
        "sticky_tum": sim.get("child").meters["sticky_tum"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, watcher: Entity, booth: Booth, treat: Treat) -> None:
    child.memes["joy"] += 1
    watcher.memes["joy"] += 1
    world.say(
        f"At TUM university on open-day noon, {child.id} came skipping to {booth.place}. "
        f"{booth.sparkle}"
    )
    world.say(
        f"There on a tray, just puffed and proud, sat {treat.phrase}, the fluffiest little cloud."
    )
    world.say(booth.host_line)


def want_treat(world: World, child: Entity, watcher: Entity, treat: Treat) -> None:
    child.memes["eager"] += 1
    world.say(
        f'"Oh, that one! That high one! That sweet white cloud!" sang {child.id}. '
        f'{watcher.id} stood close and smiled at the sound.'
    )


def tempt(world: World, child: Entity, shortcut: Shortcut) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} pointed at {shortcut.phrase}. "{shortcut.label.capitalize()} for a ladder," '
        f'{child.pronoun()} said with a grin. "I shall be up and down again!"'
    )


def warn(world: World, watcher: Entity, child: Entity, shortcut: Shortcut, treat: Treat) -> None:
    pred = predict_wobble(world)
    watcher.memes["caution"] += 1
    world.facts["predicted_fall"] = pred["fallen"]
    world.facts["predicted_sticky_tum"] = pred["sticky_tum"]
    extra = ""
    if pred["sticky_tum"]:
        extra = " and perhaps cream on your tum"
    world.say(
        f'{watcher.id} shook {watcher.pronoun("possessive")} head. '
        f'"That {shortcut.label} wobbles. If you climb for {treat.the}, '
        f'you may get a bump of fright{extra}."'
    )


def back_down(world: World, child: Entity, watcher: Entity, helper: Entity, response: Response, treat: Treat) -> None:
    child.memes["relief"] += 1
    watcher.memes["relief"] += 1
    world.say(
        f"{child.id} looked, then blinked, then made a sensible sound: "
        f'"You are right. Two feet stay on the ground."'
    )
    world.say(
        f'So {watcher.id} called the {helper.label_word}, and soon {helper.pronoun()} '
        f'{response.text}. Up came {treat.the}, safe and neat, and nobody wobbled on silly feet.'
    )


def climb(world: World, child: Entity, shortcut: Shortcut) -> None:
    child.meters["climbing"] += 1
    child.meters["reaching"] += 1
    child.meters["height_gain"] += shortcut.reach
    world.say(
        f"Up went {child.id} on {shortcut.phrase} with a hop and a hum. "
        f"{shortcut.nudge}"
    )
    propagate(world, narrate=False)


def wobble_turn(world: World, child: Entity, treat: Treat, shortcut: Shortcut) -> None:
    if child.meters["wobble"] >= THRESHOLD:
        world.say(
            f"But wobble went {shortcut.label}, wiggle-wee-wum. "
            f"{child.id}'s knees went jingle, and so did {child.pronoun('possessive')} tum."
        )
    if treat.meters["fallen"] >= THRESHOLD:
        world.say(
            f"Down came {treat.the} with a ploppy little drum, and a puff of {treat.cream} landed right on {child.id}'s tum."
        )
    elif treat.meters["held"] >= THRESHOLD:
        world.say(
            f"And somehow {child.id} caught {treat.the} before it could roam, though the wobble still taught that tall trays need care at home."
        )


def help_and_lesson(world: World, helper: Entity, child: Entity, watcher: Entity, response: Response, treat: Treat) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    watcher.memes["relief"] += 1
    if can_help(response, treat):
        world.say(
            f"The {helper.label_word} came briskly and {response.text}. "
            f'"At university," {helper.pronoun()} said, "we ask first, then reach. '
            f'That is the tidy and tip-top way to teach."'
        )
        world.say(
            f'Soon {child.id} held a fresh sweet cloud in careful hands, while {watcher.id} '
            f'got the napkin and helped wipe the cream from {child.pronoun("possessive")} tum.'
        )
    else:
        world.say(
            f"The {helper.label_word} hurried over and {response.fail}. "
            f'"When something sits too high," {helper.pronoun()} said, '
            f'"do not climb first. Ask first."'
        )
        world.say(
            f"{child.id} had no second treat that time, but the lesson stayed bright as a bell in rhyme."
        )


def ending_image(world: World, child: Entity, watcher: Entity, booth: Booth, treat: Treat) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Then side by side by the {booth.place}, they shared {treat.the} crumb by crumb. "
        f"{child.id} laughed, patted {child.pronoun('possessive')} clean little tum, "
        f'and sang, "At TUM university, I ask before I climb for a cloud!"'
    )


def tell(
    booth: Booth,
    treat_cfg: Treat,
    shortcut_cfg: Shortcut,
    response_cfg: Response,
    *,
    child_name: str = "Mimi",
    child_gender: str = "girl",
    watcher_name: str = "Otto",
    watcher_gender: str = "boy",
    watcher_trait: str = "careful",
    helper_type: str = "professor_f",
    relation: str = "siblings",
    child_age: int = 4,
    watcher_age: int = 6,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="reacher",
            age=child_age,
            traits=["eager"],
            attrs={"relation": relation},
        )
    )
    watcher = world.add(
        Entity(
            id=watcher_name,
            kind="character",
            type=watcher_gender,
            role="watcher",
            age=watcher_age,
            traits=[watcher_trait],
            attrs={"relation": relation},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the professor",
            helper=True,
        )
    )
    support = world.add(
        Entity(
            id="support",
            kind="thing",
            type="support",
            label=shortcut_cfg.label,
            phrase=shortcut_cfg.phrase,
            unstable=shortcut_cfg.unstable,
        )
    )
    support.meters["wobble_power"] = float(shortcut_cfg.wobble)
    treat = world.add(
        Entity(
            id="treat",
            kind="thing",
            type="treat",
            label=treat_cfg.label,
            phrase=treat_cfg.phrase,
            edible=True,
        )
    )
    treat.meters["height_need"] = float(treat_cfg.height)
    treat.meters["squish_power"] = float(treat_cfg.squish)

    child.memes["eager"] = EAGER_INIT
    watcher.memes["caution"] = initial_caution(watcher_trait)

    introduce(world, child, watcher, booth, treat_cfg)
    want_treat(world, child, watcher, treat_cfg)

    world.para()
    tempt(world, child, shortcut_cfg)
    warn(world, watcher, child, shortcut_cfg, treat_cfg)

    averted = would_avert(relation, child_age, watcher_age, watcher_trait)
    if averted:
        back_down(world, child, watcher, helper, response_cfg, treat_cfg)
        outcome = "averted"
    else:
        world.say(
            f'But {child.id} gave a giggle-sniff and said, "Just one quick climb!"'
        )
        world.para()
        climb(world, child, shortcut_cfg)
        wobble_turn(world, child, treat_cfg, shortcut_cfg)
        world.para()
        help_and_lesson(world, helper, child, watcher, response_cfg, treat_cfg)
        outcome = "helped" if can_help(response_cfg, treat_cfg) else "missed"

    world.para()
    ending_image(world, child, watcher, booth, treat_cfg)

    world.facts.update(
        booth=booth,
        treat_cfg=treat_cfg,
        shortcut=shortcut_cfg,
        response=response_cfg,
        child=child,
        watcher=watcher,
        helper=helper,
        outcome=outcome,
        relation=relation,
        fell=treat.meters["fallen"] >= THRESHOLD,
        sticky_tum=child.meters["sticky_tum"] >= THRESHOLD,
        got_treat=(treat.meters["held"] >= THRESHOLD) or outcome in {"averted", "helped"},
        lesson=child.memes["lesson"] >= THRESHOLD or outcome == "averted",
    )
    return world


BOOTHS = {
    "bakery": Booth(
        id="bakery",
        place="the TUM university bakery booth",
        sparkle="Blue bunting twinkled, and little paper stars swung under a silver sign.",
        host_line='"Cloud buns for the patient," called the professor with a wink.',
        tags={"university", "treat"},
    ),
    "weather_lab": Booth(
        id="weather_lab",
        place="the TUM university weather booth",
        sparkle="Tiny fans whirred, and cotton clouds bobbed above jars of shiny rain.",
        host_line='"Taste a cloud bun after the weather song," called the professor with a grin.',
        tags={"university", "cloud"},
    ),
    "robot_corner": Booth(
        id="robot_corner",
        place="the TUM university robot booth",
        sparkle="A toy robot clicked and bowed while a string of little lights blinked hello.",
        host_line='"The cloud buns wait on the top tray," said the professor. "One each, after the demo."',
        tags={"university", "robot"},
    ),
}

TREATS = {
    "cloud_bun": Treat(
        id="cloud_bun",
        label="cloud bun",
        phrase="a cloud bun dusted with sugar",
        height=3,
        squish=2,
        cream="vanilla cream",
        tags={"cloud", "bun"},
    ),
    "cloud_cupcake": Treat(
        id="cloud_cupcake",
        label="cloud cupcake",
        phrase="a cloud cupcake with a swirly top",
        height=2,
        squish=2,
        cream="frosting",
        tags={"cloud", "cupcake"},
    ),
    "cloud_meringue": Treat(
        id="cloud_meringue",
        label="cloud meringue",
        phrase="a cloud meringue as light as a puff",
        height=3,
        squish=1,
        cream="sweet crumbs",
        tags={"cloud", "meringue"},
    ),
    "apple": Treat(
        id="apple",
        label="apple",
        phrase="a plain red apple on the low tray",
        height=1,
        squish=0,
        cream="juice",
        tags={"apple"},
    ),
}

SHORTCUTS = {
    "rolling_stool": Shortcut(
        id="rolling_stool",
        label="rolling stool",
        phrase="the rolling stool",
        wobble=2,
        reach=2,
        nudge="Its little wheels whispered, clickety-clack, as if planning a joke behind its back.",
        unstable=True,
        tags={"stool"},
    ),
    "swivel_chair": Shortcut(
        id="swivel_chair",
        label="swivel chair",
        phrase="the swivel chair",
        wobble=3,
        reach=3,
        nudge="Round went the seat with a squeaky little swoon.",
        unstable=True,
        tags={"chair"},
    ),
    "book_crate": Shortcut(
        id="book_crate",
        label="book crate",
        phrase="the crate of books",
        wobble=2,
        reach=2,
        nudge="The books muttered shuffle-shuff as the corners puffed.",
        unstable=True,
        tags={"books"},
    ),
}

RESPONSES = {
    "step_stool": Response(
        id="step_stool",
        sense=3,
        reach=3,
        text="brought the proper step stool and lifted the tray to child height",
        short="used the proper step stool",
        fail="brought a step stool, but this tray was still up too high for little hands alone",
        tags={"step_stool", "ask_first"},
    ),
    "ask_professor": Response(
        id="ask_professor",
        sense=4,
        reach=4,
        text="lifted the tray down with a warm laugh and a clean napkin ready",
        short="helped by lifting the tray down",
        fail="was busy for a moment too long, and the treat was already gone splat",
        tags={"professor", "ask_first"},
    ),
    "grabber": Response(
        id="grabber",
        sense=2,
        reach=2,
        text="used the long grabber to pull the tray close",
        short="used a long grabber",
        fail="tried the long grabber, but it was too short to reach safely",
        tags={"grabber", "ask_first"},
    ),
    "hop": Response(
        id="hop",
        sense=1,
        reach=1,
        text="told the child to hop again",
        short="hopped again",
        fail="could only suggest another hop, which was no help at all",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mimi", "Lina", "Nora", "Tia", "Lulu", "Pia", "Eva", "Rosa"]
BOY_NAMES = ["Otto", "Milo", "Ben", "Toni", "Leo", "Finn", "Nico", "Karl"]
TRAITS = ["careful", "steady", "sensible", "curious", "cheery", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for booth_id in BOOTHS:
        for treat_id, treat in TREATS.items():
            for shortcut_id, shortcut in SHORTCUTS.items():
                if treat_needs_reach(treat, shortcut):
                    combos.append((booth_id, treat_id, shortcut_id))
    return combos


@dataclass
class StoryParams:
    booth: str
    treat: str
    shortcut: str
    response: str
    child_name: str
    child_gender: str
    watcher_name: str
    watcher_gender: str
    watcher_trait: str
    helper_type: str
    relation: str = "siblings"
    child_age: int = 4
    watcher_age: int = 6
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
    "university": [
        (
            "What is a university?",
            "A university is a place where grown-ups study, teach, and do experiments. It can also have open days where children visit and look around."
        )
    ],
    "cloud": [
        (
            "What is a cloud?",
            "A cloud is a big group of tiny water drops or ice bits floating high in the sky. It only looks soft like cotton, but it is made of water."
        )
    ],
    "step_stool": [
        (
            "What is a step stool for?",
            "A step stool is a small sturdy thing to stand on when something is too high. It helps you reach more safely than climbing on a chair with wheels."
        )
    ],
    "ask_first": [
        (
            "Why should you ask first when something is high up?",
            "Asking first helps a grown-up choose the safest way to reach it. A quick question can stop a quick tumble."
        )
    ],
    "chair": [
        (
            "Why is a swivel chair a bad ladder?",
            "A swivel chair can turn or roll when you do not expect it. That makes your body wobble when you need it to stay steady."
        )
    ],
    "stool": [
        (
            "Why can a rolling stool be tricky to stand on?",
            "A rolling stool has wheels, so it can slide when weight shifts. If you reach too far, the wheels may scoot away."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that helps pull light things closer. It only works when the thing is near enough and not too hard to handle."
        )
    ],
    "professor": [
        (
            "What does a professor do?",
            "A professor is a teacher at a university. Professors explain things and help people learn safely."
        )
    ],
}
KNOWLEDGE_ORDER = ["university", "cloud", "ask_first", "step_stool", "chair", "stool", "grabber", "professor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    watcher = f["watcher"]
    booth = f["booth"]
    treat = f["treat_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short nursery-rhyme story that includes the words "university", "tum", and "cloud". Set it at {booth.place} and let a child decide not to climb after a wiser child warns them.',
            f"Tell a funny gentle story where {child.id} wants {treat.the} at a university booth, but {watcher.id} talks {child.pronoun('object')} into asking first.",
            "Write a humorous lesson-learned rhyme for a 3-to-5-year-old about keeping both feet on the ground and asking for help."
        ]
    return [
        f'Write a nursery-rhyme style story that includes the words "university", "tum", and "cloud". Set it at {booth.place}, where a child reaches for {treat.the} in a silly way and learns a lesson.',
        f"Tell a playful rhyming story where {child.id} climbs on something wobbly for {treat.the}, gets a funny scare, and is helped kindly by a professor.",
        "Write a child-facing humorous cautionary rhyme that ends with the child laughing and remembering to ask first."
    ]


def pair_noun(child: Entity, watcher: Entity, relation: str) -> str:
    if relation == "siblings":
        if child.type == "boy" and watcher.type == "boy":
            return "two brothers"
        if child.type == "girl" and watcher.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    watcher = f["watcher"]
    helper = f["helper"]
    booth = f["booth"]
    treat = f["treat_cfg"]
    shortcut = f["shortcut"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(child, watcher, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {child.id} and {watcher.id}, visiting {booth.place}. A professor there helps them at the turning point."
        ),
        (
            f"Where were they, and what did {child.id} want?",
            f"They were at TUM university on open day, standing by {booth.place}. {child.id} wanted {treat.the} from the high tray because it looked soft and special like a little cloud."
        ),
        (
            f"Why did {watcher.id} warn {child.id}?",
            f"{watcher.id} warned {child.id} because {shortcut.the if hasattr(shortcut, 'the') else shortcut.label} was wobbly, and climbing on it could make the treat fall. In this story, the warning was about both a scare and a silly sticky mess."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {child.id} do after the warning?",
                f"{child.id} stopped and chose not to climb. That kept the problem small, because the professor could help safely before anything tipped or splatted."
            )
        )
        qa.append(
            (
                "What lesson did the story teach?",
                "The story taught that asking first is smarter than climbing on something wobbly. The happy ending comes because the child listens before trouble starts."
            )
        )
    else:
        qa.append(
            (
                f"What funny thing happened in the middle of the story?",
                f"The {shortcut.label} wobbled, and {treat.the} came down with a soft splat. Some {treat.cream} landed on {child.id}'s tum, which made the moment funny even while it felt embarrassing."
            )
        )
        if can_help(response, treat):
            qa.append(
                (
                    f"How did the professor solve the problem?",
                    f"The professor {response.short}. That worked because the proper help could actually reach the high tray, so {child.id} did not need to climb again."
                )
            )
        else:
            qa.append(
                (
                    "Did the first rescue idea work?",
                    f"No. The helper tried to use {response.short}, but it was not enough to reach safely. That is why the story feels a little disappointing before the lesson settles in."
                )
            )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned to ask before climbing for a high treat. The cream on {child.pronoun('possessive')} tum made the lesson easy to remember."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"university", "cloud", "ask_first"}
    tags |= set(f["shortcut"].tags)
    tags |= set(f["response"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.unstable:
            bits.append("unstable=True")
        if e.helper:
            bits.append("helper=True")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        booth="bakery",
        treat="cloud_bun",
        shortcut="rolling_stool",
        response="step_stool",
        child_name="Mimi",
        child_gender="girl",
        watcher_name="Otto",
        watcher_gender="boy",
        watcher_trait="careful",
        helper_type="professor_f",
        relation="siblings",
        child_age=4,
        watcher_age=6,
    ),
    StoryParams(
        booth="weather_lab",
        treat="cloud_cupcake",
        shortcut="swivel_chair",
        response="ask_professor",
        child_name="Ben",
        child_gender="boy",
        watcher_name="Lina",
        watcher_gender="girl",
        watcher_trait="steady",
        helper_type="professor_m",
        relation="friends",
        child_age=5,
        watcher_age=5,
    ),
    StoryParams(
        booth="robot_corner",
        treat="cloud_meringue",
        shortcut="book_crate",
        response="grabber",
        child_name="Nora",
        child_gender="girl",
        watcher_name="Milo",
        watcher_gender="boy",
        watcher_trait="curious",
        helper_type="professor_f",
        relation="siblings",
        child_age=5,
        watcher_age=4,
    ),
    StoryParams(
        booth="bakery",
        treat="cloud_bun",
        shortcut="swivel_chair",
        response="ask_professor",
        child_name="Leo",
        child_gender="boy",
        watcher_name="Pia",
        watcher_gender="girl",
        watcher_trait="sensible",
        helper_type="professor_m",
        relation="siblings",
        child_age=4,
        watcher_age=7,
    ),
]


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.child_age, params.watcher_age, params.watcher_trait):
        return "averted"
    return "helped" if can_help(RESPONSES[params.response], TREATS[params.treat]) else "missed"


ASP_RULES = r"""
% Reasonable reaching problem: the treat is high enough to tempt climbing.
valid(B, T, S) :- booth(B), treat(T), shortcut(S), height(T, H), H > 1, unstable(S).

% Common-sense helpers.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

% Outcome model.
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
watcher_older :- relation(siblings), child_age(CA), watcher_age(WA), WA > CA.
bonus(3) :- watcher_older.
bonus(0) :- not watcher_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- watcher_older, authority(A), eager_init(E), A > E.

reachable :- chosen_response(R), chosen_treat(T), reach(R, RR), height(T, H), RR >= H.
outcome(averted) :- averted.
outcome(helped) :- not averted, reachable.
outcome(missed) :- not averted, not reachable.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bid in BOOTHS:
        lines.append(asp.fact("booth", bid))
    for tid, treat in TREATS.items():
        lines.append(asp.fact("treat", tid))
        lines.append(asp.fact("height", tid, treat.height))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        if shortcut.unstable:
            lines.append(asp.fact("unstable", sid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("reach", rid, response.reach))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("eager_init", int(EAGER_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_treat", params.treat),
            asp.fact("chosen_response", params.response),
            asp.fact("relation", params.relation),
            asp.fact("child_age", params.child_age),
            asp.fact("watcher_age", params.watcher_age),
            asp.fact("trait", params.watcher_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child at TUM university, a high cloud treat, and a funny lesson about asking first."
    )
    ap.add_argument("--booth", choices=BOOTHS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["professor_f", "professor_m"])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treat and args.shortcut:
        treat = TREATS[args.treat]
        shortcut = SHORTCUTS[args.shortcut]
        if not treat_needs_reach(treat, shortcut):
            raise StoryError(explain_rejection(treat, shortcut))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.booth is None or c[0] == args.booth)
        and (args.treat is None or c[1] == args.treat)
        and (args.shortcut is None or c[2] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    booth_id, treat_id, shortcut_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_kid(rng)
    watcher_name, watcher_gender = _pick_kid(rng, avoid=child_name)
    watcher_trait = rng.choice(TRAITS)
    helper_type = args.helper or rng.choice(["professor_f", "professor_m"])
    relation = rng.choice(["siblings", "friends"])
    child_age, watcher_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        booth=booth_id,
        treat=treat_id,
        shortcut=shortcut_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        watcher_name=watcher_name,
        watcher_gender=watcher_gender,
        watcher_trait=watcher_trait,
        helper_type=helper_type,
        relation=relation,
        child_age=child_age,
        watcher_age=watcher_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.booth not in BOOTHS:
        raise StoryError(f"(Unknown booth: {params.booth})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.helper_type not in {"professor_f", "professor_m"}:
        raise StoryError(f"(Unknown helper type: {params.helper_type})")

    treat = TREATS[params.treat]
    shortcut = SHORTCUTS[params.shortcut]
    response = RESPONSES[params.response]

    if not treat_needs_reach(treat, shortcut):
        raise StoryError(explain_rejection(treat, shortcut))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        BOOTHS[params.booth],
        treat,
        shortcut,
        response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        watcher_name=params.watcher_name,
        watcher_gender=params.watcher_gender,
        watcher_trait=params.watcher_trait,
        helper_type=params.helper_type,
        relation=params.relation,
        child_age=params.child_age,
        watcher_age=params.watcher_age,
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (booth, treat, shortcut) combos:\n")
        for booth_id, treat_id, shortcut_id in combos:
            print(f"  {booth_id:12} {treat_id:14} {shortcut_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.child_name} & {p.watcher_name}: {p.treat} at {p.booth} via {p.shortcut} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
