#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/office_viaduct_lesson_learned_curiosity_fairy_tale.py
=================================================================================

A standalone story world about a curious child in a little office tucked beneath
a stone viaduct. In this fairy-tale-flavored domain, curiosity is not treated as
bad; the lesson is that curious feet and hands should ask for help before they
climb, sneak, or wander.

Run it
------
    python storyworlds/worlds/gpt-5.4/office_viaduct_lesson_learned_curiosity_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/office_viaduct_lesson_learned_curiosity_fairy_tale.py --target blue_plaque --shortcut side_door
    python storyworlds/worlds/gpt-5.4/office_viaduct_lesson_learned_curiosity_fairy_tale.py --target pigeon_cubby --shortcut side_door
    python storyworlds/worlds/gpt-5.4/office_viaduct_lesson_learned_curiosity_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/office_viaduct_lesson_learned_curiosity_fairy_tale.py --verify
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
CURIOSITY_INIT = 5.0
ASKING_TRAITS = {"patient", "careful", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "woman": "keeper",
            "man": "keeper",
        }.get(self.type, self.type)
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
class Target:
    id: str
    label: str
    phrase: str
    gleam: str
    location: str
    kind: str
    risk: int
    lesson: str
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
class Shortcut:
    id: str
    label: str
    phrase: str
    kind: str
    wobble_word: str
    danger_text: str
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
    power: int
    text_high: str
    text_outside: str
    fail_high: str
    fail_outside: str
    qa_high: str
    qa_outside: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    place = world.facts.get("scene_kind", "")
    if place != "high":
        return out
    if child.meters["climbing"] < THRESHOLD:
        return out
    sig = ("wobble", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["wobble"] += 1
    child.memes["fear"] += 1
    world.get("office").meters["flutter"] += 1
    out.append("__wobble__")
    return out


def _r_lost(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    place = world.facts.get("scene_kind", "")
    if place != "outside":
        return out
    if child.meters["wandering"] < THRESHOLD:
        return out
    sig = ("lost", "child")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["distance"] += 1
    child.memes["fear"] += 1
    world.get("viaduct").meters["wind"] += 1
    out.append("__lost__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="lost", tag="physical", apply=_r_lost),
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


def compatible(target: Target, shortcut: Shortcut) -> bool:
    return target.kind == shortcut.kind


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def scene_severity(target: Target, delay: int) -> int:
    return target.risk + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= scene_severity(target, delay)


def initial_asking(trait: str) -> float:
    return 5.0 if trait in ASKING_TRAITS else 3.0


def would_ask_first(trait: str, trust: int) -> bool:
    authority = initial_asking(trait) + (1.0 if trust >= 7 else 0.0)
    return authority > CURIOSITY_INIT


def predict_risk(world: World, target: Target, shortcut: Shortcut) -> dict:
    sim = world.copy()
    child = sim.get("child")
    sim.facts["scene_kind"] = target.kind
    if shortcut.kind == "high":
        child.meters["climbing"] += 1
    else:
        child.meters["wandering"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": child.meters["wobble"] >= THRESHOLD,
        "lost": child.meters["distance"] >= THRESHOLD,
        "fear": child.memes["fear"],
    }


def opening(world: World, child: Entity, keeper: Entity) -> None:
    world.say(
        f"Once, in a little office tucked beneath a stone viaduct, "
        f"{child.id} spent the afternoon with the town's letter-keeper."
    )
    world.say(
        f"The office smelled of paper, beeswax, and rain on stone, and "
        f"{keeper.id} sorted ribbons of mail while the arches overhead hummed softly."
    )
    child.memes["wonder"] += 1
    keeper.memes["care"] += 1


def show_target(world: World, child: Entity, target: Target) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"Then {child.id} noticed {target.phrase} {target.location}. "
        f"It {target.gleam}, and curiosity tugged at {child.pronoun('possessive')} heart like a small bright string."
    )


def tempt(world: World, child: Entity, shortcut: Shortcut) -> None:
    world.say(
        f'"I could reach it by {shortcut.phrase}," {child.id} whispered. '
        f"For one breath, the shortcut sounded clever."
    )
    child.memes["defiance"] += 1


def warn(world: World, keeper: Entity, child: Entity, target: Target, shortcut: Shortcut) -> None:
    pred = predict_risk(world, target, shortcut)
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["hesitation"] += 1
    if target.kind == "high":
        world.say(
            f'{keeper.id} looked up from the letters. "Little star," {keeper.pronoun()} said, '
            f'"if you try {shortcut.phrase}, {shortcut.danger_text}. Curious eyes are good, '
            f'but they must not climb faster than wise feet."'
        )
    else:
        world.say(
            f'{keeper.id} heard the latch and turned at once. "Little star," {keeper.pronoun()} said, '
            f'"if you slip out by {shortcut.phrase}, {shortcut.danger_text}. Curiosity may walk, '
            f'but it should not wander alone onto the viaduct."'
        )


def back_down(world: World, child: Entity, keeper: Entity, target: Target) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} looked at {target.label}, then at {keeper.id}, and took a slower breath."
    )
    world.say(
        f'"Will you show me the right way?" {child.pronoun()} asked. '
        f'The question itself made the room feel steadier.'
    )


def try_shortcut(world: World, child: Entity, target: Target, shortcut: Shortcut) -> None:
    world.facts["scene_kind"] = target.kind
    if shortcut.kind == "high":
        child.meters["climbing"] += 1
        propagate(world, narrate=False)
        world.say(
            f"But curiosity ran ahead of caution. {child.id} set a foot on {shortcut.phrase}, "
            f"reached for {target.label}, and at once {shortcut.wobble_word}."
        )
        world.say(
            "The neat piles of paper shivered, and a frightened flutter went through the little office."
        )
    else:
        child.meters["wandering"] += 1
        propagate(world, narrate=False)
        world.say(
            f"But curiosity ran ahead of caution. {child.id} slipped out by {shortcut.phrase} "
            f"and hurried toward the viaduct stones to see {target.label} better."
        )
        world.say(
            "Wind moved through the arches with a deep booming voice, and the world suddenly felt much bigger than before."
        )


def alarm(world: World, child: Entity, keeper: Entity, target: Target) -> None:
    if target.kind == "high":
        world.say(f'"{keeper.id}!" gasped {child.id}, clutching at the air.')
    else:
        world.say(
            f'"{keeper.id}!" {child.id} called, and the name sounded very small beneath the viaduct.'
        )


def rescue(world: World, child: Entity, keeper: Entity, target: Target, response: Response) -> None:
    if target.kind == "high":
        child.meters["wobble"] = 0.0
        child.meters["climbing"] = 0.0
        world.get("office").meters["flutter"] = 0.0
        world.say(
            f"{keeper.id} moved as quickly as a storybook robin and {response.text_high}."
        )
        world.say(
            f"Soon both feet were safe on the floor again, and {child.id} could feel {child.pronoun('possessive')} knees shaking."
        )
    else:
        child.meters["distance"] = 0.0
        child.meters["wandering"] = 0.0
        world.get("viaduct").meters["wind"] = 0.0
        world.say(
            f"{keeper.id} hurried out after {child.id} and {response.text_outside}."
        )
        world.say(
            f"With a warm hand around {child.pronoun('possessive')} own, the great viaduct no longer seemed quite so lonely."
        )
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    keeper.memes["care"] += 1


def rescue_fail(world: World, child: Entity, keeper: Entity, target: Target, response: Response) -> None:
    if target.kind == "high":
        world.get("office").meters["flutter"] += 1
        child.memes["fear"] += 1
        world.say(f"{keeper.id} {response.fail_high}.")
        world.say(
            "Letters spilled like startled white birds across the floor before the child could be gathered down."
        )
    else:
        world.get("viaduct").meters["wind"] += 1
        child.memes["fear"] += 1
        world.say(f"{keeper.id} {response.fail_outside}.")
        world.say(
            "By the time the child was found, dusk had already laid a gray ribbon over the viaduct."
        )
    child.meters["climbing"] = 0.0
    child.meters["wandering"] = 0.0
    child.meters["distance"] = 0.0
    child.meters["wobble"] = 0.0


def lesson(world: World, child: Entity, keeper: Entity, target: Target) -> None:
    child.memes["lesson"] += 1
    child.memes["trust"] += 1
    world.say(
        f'Then {keeper.id} knelt so {child.id} could see the kindness in {keeper.pronoun("possessive")} face. '
        f'"Curiosity is a fine lantern," {keeper.pronoun()} said softly, '
        f'"but it must travel with asking. {target.lesson}"'
    )
    world.say(
        f"{child.id} nodded. {child.pronoun().capitalize()} had wanted to know, and now {child.pronoun()} also knew how to ask."
    )


def sad_lesson(world: World, child: Entity, keeper: Entity, target: Target) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"When the room was quiet again, {keeper.id} wrapped a coat around {child.id}'s shoulders."
    )
    world.say(
        f'"Do you see why I asked you to wait?" {keeper.pronoun()} murmured. '
        f'"Curiosity is precious, but it should never pull you farther than help can reach. {target.lesson}"'
    )
    world.say(
        f"{child.id} nodded against the coat. The lesson felt heavy for a moment, but it stayed."
    )


def safe_showing(world: World, child: Entity, keeper: Entity, target: Target) -> None:
    child.memes["joy"] += 1
    if target.kind == "high":
        world.say(
            f"A little later, {keeper.id} fetched a stout stool, set it flat, and stood close beside {child.id}."
        )
        world.say(
            f"From there {child.id} could see {target.label} properly at last. {target.gleam.capitalize()}, and wonder had no need to hurry."
        )
    else:
        world.say(
            f"A little later, {keeper.id} locked the office, took {child.id}'s hand, and together they walked to the safe overlook beside the viaduct."
        )
        world.say(
            f"From there {child.id} could admire {target.label} without fear, while evening gold lay softly on the stone arches."
        )


def closing(world: World, child: Entity, keeper: Entity, target: Target, outcome: str) -> None:
    if outcome == "burned":
        world.say(
            f"After that day, whenever curiosity knocked inside {child.id}, {child.pronoun()} answered with a question first."
        )
        world.say(
            f"And in the little office beneath the viaduct, even the paper seemed to rustle more wisely."
        )
    else:
        world.say(
            f"By sunset the little office was calm again, and {child.id} stood beside {keeper.id} with bright eyes and slower feet."
        )
        world.say(
            f"So the child kept curiosity, but learned to carry it gently, like a lantern with two hands."
        )


def tell(
    target: Target,
    shortcut: Shortcut,
    response: Response,
    *,
    child_name: str = "Mira",
    child_gender: str = "girl",
    keeper_name: str = "Alder",
    keeper_gender: str = "man",
    trait: str = "patient",
    parent_type: str = "mother",
    trust: int = 7,
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
            attrs={"trust": trust},
        )
    )
    keeper = world.add(
        Entity(
            id=keeper_name,
            kind="character",
            type=keeper_gender,
            label=keeper_name,
            role="keeper",
            traits=["kind"],
            attrs={"relation": parent_type},
        )
    )
    world.add(Entity(id="office", type="office", label="office"))
    world.add(Entity(id="viaduct", type="viaduct", label="viaduct"))
    world.add(Entity(id="target", type="wonder", label=target.label))
    world.facts["scene_kind"] = target.kind

    child.memes["trust"] = float(trust)
    child.memes["curiosity"] = CURIOSITY_INIT
    child.memes["asking"] = initial_asking(trait)
    child.memes["fear"] = 0.0
    child.meters["climbing"] = 0.0
    child.meters["wandering"] = 0.0
    child.meters["distance"] = 0.0
    child.meters["wobble"] = 0.0

    opening(world, child, keeper)
    show_target(world, child, target)

    world.para()
    tempt(world, child, shortcut)
    warn(world, keeper, child, target, shortcut)

    averted = would_ask_first(trait, trust)
    if averted:
        back_down(world, child, keeper, target)
        world.para()
        safe_showing(world, child, keeper, target)
        outcome = "averted"
        contained = True
    else:
        world.para()
        try_shortcut(world, child, target, shortcut)
        alarm(world, child, keeper, target)

        contained = is_contained(response, target, delay)
        world.para()
        if contained:
            rescue(world, child, keeper, target, response)
            lesson(world, child, keeper, target)
            world.para()
            safe_showing(world, child, keeper, target)
            outcome = "contained"
        else:
            rescue_fail(world, child, keeper, target, response)
            sad_lesson(world, child, keeper, target)
            outcome = "burned"

    world.para()
    closing(world, child, keeper, target, outcome)

    world.facts.update(
        child=child,
        keeper=keeper,
        target_cfg=target,
        shortcut=shortcut,
        response=response,
        outcome=outcome,
        delay=delay,
        trust=trust,
        averted=averted,
        contained=contained,
        predicted_kind=world.facts.get("scene_kind", ""),
        relation=parent_type,
    )
    return world


TARGETS = {
    "pigeon_cubby": Target(
        id="pigeon_cubby",
        label="the silver pigeon cubby",
        phrase="a silver pigeon cubby",
        gleam="gleamed with tiny wings carved along its edge",
        location="high above the sorting desk",
        kind="high",
        risk=1,
        lesson="When a wonder lives up high, we fetch it safely or wait for helping hands.",
        tags={"office", "high_shelf", "curiosity"},
    ),
    "brass_tube": Target(
        id="brass_tube",
        label="the brass speaking tube",
        phrase="a brass speaking tube",
        gleam="shone like honey in the lamplight",
        location="near the tall office window",
        kind="high",
        risk=2,
        lesson="Things near a high window are for looking with care, not reaching in a rush.",
        tags={"office", "tube", "curiosity"},
    ),
    "blue_plaque": Target(
        id="blue_plaque",
        label="the blue plaque on the viaduct arch",
        phrase="a blue plaque",
        gleam="glimmered where the afternoon sun touched the stone",
        location="outside on the nearest viaduct arch",
        kind="outside",
        risk=2,
        lesson="Stone arches and windy paths are places to explore together, not alone.",
        tags={"viaduct", "outside", "stone"},
    ),
}

SHORTCUTS = {
    "swivel_chair": Shortcut(
        id="swivel_chair",
        label="swivel chair",
        phrase="the rolling office chair",
        kind="high",
        wobble_word="the chair glided and wobbled underfoot",
        danger_text="the rolling chair may slide and send you tumbling",
        tags={"chair", "climb"},
    ),
    "parcel_stack": Shortcut(
        id="parcel_stack",
        label="parcel stack",
        phrase="the stack of tied parcels",
        kind="high",
        wobble_word="the parcels shifted like a little paper hill",
        danger_text="those parcels may tip and bring half the office down with you",
        tags={"parcels", "climb"},
    ),
    "side_door": Shortcut(
        id="side_door",
        label="side door",
        phrase="the little side door",
        kind="outside",
        wobble_word="",
        danger_text="the wind may hurry you farther than you mean to go",
        tags={"door", "wander"},
    ),
}

RESPONSES = {
    "swift_arms": Response(
        id="swift_arms",
        sense=3,
        power=3,
        text_high="caught the chair with one hand and lifted the child down with the other",
        text_outside="reached the child quickly, wrapped a steady arm around little shoulders, and led the way back inside",
        fail_high="darted forward, but the papers and parcels burst apart before order could be found",
        fail_outside="called and hurried after the child, but the wind carried the sound away for a frightening while",
        qa_high="caught the wobbling seat and lifted the child down",
        qa_outside="reached the child and guided the way back from the viaduct",
        tags={"rescue", "help"},
    ),
    "watchman": Response(
        id="watchman",
        sense=2,
        power=2,
        text_high="called the old hall watchman, and together they steadied the mess and brought the child carefully down",
        text_outside="called to the viaduct watchman, who blocked the windy path while the keeper hurried over",
        fail_high="called for help, but in those extra moments the stack gave way and papers flew everywhere",
        fail_outside="called to the watchman, but dusk and wind made the search longer than anyone liked",
        qa_high="called for the watchman and brought the child safely down together",
        qa_outside="called the viaduct watchman to help stop the child on the windy path",
        tags={"watchman", "rescue"},
    ),
    "wait_call": Response(
        id="wait_call",
        sense=1,
        power=1,
        text_high="told the child to freeze and hoped stillness would be enough",
        text_outside="called from the office door and hoped the child would turn back alone",
        fail_high="only called out for the child to wait, and that was too little for such a shaky moment",
        fail_outside="only called from the doorway, and the child wandered farther before hearing",
        qa_high="only called out from across the room",
        qa_outside="only called from the office doorway",
        tags={"weak_response"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tessa", "Poppy", "Nell", "Ivy", "Ada", "June"]
BOY_NAMES = ["Rowan", "Theo", "Finn", "Milo", "Ellis", "Jasper", "Owen", "Ari"]
KEEPER_WOMEN = ["Elowen", "Briar", "Maris", "Faye"]
KEEPER_MEN = ["Alder", "Rowe", "Silas", "Bram"]
TRAITS = ["patient", "careful", "thoughtful", "gentle", "hasty", "restless", "bold"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    if not sensible_responses():
        return combos
    for tid, target in TARGETS.items():
        for sid, shortcut in SHORTCUTS.items():
            if compatible(target, shortcut):
                combos.append((tid, sid))
    return combos


@dataclass
class StoryParams:
    target: str
    shortcut: str
    response: str
    child_name: str
    child_gender: str
    keeper_name: str
    keeper_gender: str
    relation: str
    trait: str
    trust: int = 7
    delay: int = 0
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
    "office": [
        (
            "What is an office?",
            "An office is a place where people do careful work with papers, tools, and messages. It is often a quiet room where grown-ups keep things in order.",
        )
    ],
    "viaduct": [
        (
            "What is a viaduct?",
            "A viaduct is a long bridge, often made of stone or brick, that carries a road or railway high across the land. Its tall arches can make sounds echo underneath.",
        )
    ],
    "high_shelf": [
        (
            "Why is climbing on a rolling chair unsafe?",
            "A rolling chair can slide when you put your weight on it, so your feet may slip suddenly. That is why a sturdy stool and a grown-up are safer.",
        )
    ],
    "tube": [
        (
            "What is a speaking tube?",
            "A speaking tube is a hollow tube used to carry a voice from one place to another. In old buildings, people could talk through it before telephones were common.",
        )
    ],
    "stone": [
        (
            "Why can a windy stone walkway feel scary?",
            "Wind can push at your clothes and make sounds seem bigger than they are. On high stone paths, that can make a child feel small and unsure.",
        )
    ],
    "watchman": [
        (
            "What does a watchman do?",
            "A watchman keeps watch over a place and helps people stay safe. In a story, a watchman may notice trouble quickly and help guide people back.",
        )
    ],
    "rescue": [
        (
            "What should a child do when something interesting is too high or too far away?",
            "The child should stop and ask a grown-up for help. Curiosity is good, but safe help keeps curious children from getting hurt or lost.",
        )
    ],
    "curiosity": [
        (
            "Is curiosity a bad thing?",
            "No. Curiosity means wanting to learn, and that is a good beginning. The wise part is asking questions in a safe way instead of rushing into danger.",
        )
    ],
}
KNOWLEDGE_ORDER = ["office", "viaduct", "high_shelf", "tube", "stone", "watchman", "rescue", "curiosity"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    target = f["target_cfg"]
    shortcut = f["shortcut"]
    outcome = f["outcome"]
    base = (
        f'Write a fairy-tale-style story for a 3-to-5-year-old set in an office beneath a viaduct, '
        f'where a curious child notices {target.label} and is tempted by {shortcut.phrase}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle fairy tale where {child.id} feels strong curiosity but chooses to ask for help before trying a shortcut.",
            'Write a story with the lesson that curiosity is good when it walks together with patience and asking.',
        ]
    if outcome == "burned":
        return [
            base,
            f"Tell a more serious fairy tale where {child.id}'s shortcut leads to a frightening moment before the lesson is learned.",
            'Write a child-facing cautionary story that keeps curiosity kind but shows why asking first matters.',
        ]
    return [
        base,
        f"Tell a warm fairy tale where {child.id} makes an unsafe choice, is helped by a caring keeper, and learns a lesson without losing wonder.",
        'Write a simple story that includes the words "office" and "viaduct" and ends with curiosity becoming wiser.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    target = f["target_cfg"]
    shortcut = f["shortcut"]
    response = f["response"]
    outcome = f["outcome"]
    relation = f["relation"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and {keeper.id}, the kind keeper in the office beneath the viaduct.",
        ),
        (
            "What made the child curious?",
            f"{child.id} noticed {target.phrase} {target.location}. It looked so special that {child.pronoun('possessive')} curiosity began tugging right away.",
        ),
        (
            f"Why did {keeper.id} warn {child.id} not to use {shortcut.phrase}?",
            f"{keeper.id} knew that {shortcut.danger_text}. The warning came before the trouble because the keeper could already picture what might go wrong.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {child.id} do instead of rushing ahead?",
                f"{child.id} stopped and asked to be shown the right way. That choice changed the whole story, because the wonder could still be seen without fear.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{child.id} learned that curiosity is a good thing when it travels with asking and patience. The lesson was not to stop wondering, but to wonder safely.",
            )
        )
    elif outcome == "contained":
        qa_text = response.qa_high if target.kind == "high" else response.qa_outside
        qa.append(
            (
                f"How did {keeper.id} help when the trouble began?",
                f"{keeper.id} {qa_text}. That quick help ended the dangerous moment before it could grow worse.",
            )
        )
        qa.append(
            (
                "How did the child feel after being helped?",
                f"{child.id} felt shaken at first, and then relieved. Because the keeper stayed kind, the fear turned into a lesson instead of turning wonder into shame.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {child.id} seeing the wonder safely at last. The ending shows that the child kept curiosity, but learned to carry it more wisely.",
            )
        )
    else:
        qa.append(
            (
                "Why was the moment so frightening?",
                f"The shortcut gave the trouble time to grow, so the office or the viaduct felt bigger and wilder than before. That is why the lesson landed so deeply in the child's heart.",
            )
        )
        qa.append(
            (
                "What lesson stayed with the child afterward?",
                f"{child.id} learned that precious curiosity still needs safe help. Asking first became the new habit, because the scary moment showed what rushing can cost.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    target = f["target_cfg"]
    response = f["response"]
    tags: set[str] = {"office", "viaduct", "curiosity", "rescue"}
    tags |= set(target.tags)
    tags |= set(response.tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: { {k: v for k, v in world.facts.items() if k not in {'child', 'keeper', 'target_cfg', 'shortcut', 'response'}} }")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        target="pigeon_cubby",
        shortcut="swivel_chair",
        response="swift_arms",
        child_name="Mira",
        child_gender="girl",
        keeper_name="Alder",
        keeper_gender="man",
        relation="keeper",
        trait="hasty",
        trust=4,
        delay=0,
    ),
    StoryParams(
        target="blue_plaque",
        shortcut="side_door",
        response="watchman",
        child_name="Theo",
        child_gender="boy",
        keeper_name="Elowen",
        keeper_gender="woman",
        relation="keeper",
        trait="restless",
        trust=3,
        delay=1,
    ),
    StoryParams(
        target="brass_tube",
        shortcut="parcel_stack",
        response="swift_arms",
        child_name="Ivy",
        child_gender="girl",
        keeper_name="Bram",
        keeper_gender="man",
        relation="keeper",
        trait="patient",
        trust=8,
        delay=0,
    ),
    StoryParams(
        target="blue_plaque",
        shortcut="side_door",
        response="watchman",
        child_name="Rowan",
        child_gender="boy",
        keeper_name="Maris",
        keeper_gender="woman",
        relation="keeper",
        trait="bold",
        trust=2,
        delay=2,
    ),
]


def explain_rejection(target: Target, shortcut: Shortcut) -> str:
    if target.kind != shortcut.kind:
        return (
            f"(No story: {shortcut.phrase} does not honestly reach {target.label}. "
            f"Use a climbing shortcut for office wonders up high, or the side door for a wonder out on the viaduct.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_ask_first(params.trait, params.trust):
        return "averted"
    contained = is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay)
    return "contained" if contained else "burned"


ASP_RULES = r"""
compatible(T,S) :- target(T), shortcut(S), target_kind(T,K), shortcut_kind(S,K).

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T,S) :- target(T), shortcut(S), compatible(T,S).

asking_init(5) :- trait(T), asking_trait(T).
asking_init(3) :- trait(T), not asking_trait(T).
trust_bonus(1) :- trust(V), V >= 7.
trust_bonus(0) :- trust(V), V < 7.
ask_first :- asking_init(A), trust_bonus(B), curiosity_init(C), A + B > C.

severity(Risk + D) :- chosen_target(T), risk(T,Risk), delay(D).
resp_power(P) :- chosen_response(R), power(R,P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- ask_first.
outcome(contained) :- not ask_first, contained.
outcome(burned) :- not ask_first, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("target_kind", tid, target.kind))
        lines.append(asp.fact("risk", tid, target.risk))
    for sid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", sid))
        lines.append(asp.fact("shortcut_kind", sid, shortcut.kind))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(ASKING_TRAITS):
        lines.append(asp.fact("asking_trait", trait))
    for trait in sorted(set(TRAITS)):
        lines.append(asp.fact("trait_name", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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

    c_sense = set(asp_sensible())
    p_sense = {r.id for r in sensible_responses()}
    if c_sense == p_sense:
        print(f"OK: sensible responses match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome(s) differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a curious child, an office, a viaduct, and a lesson about asking first."
    )
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--relation", choices=["keeper", "mother", "father"])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def _pick_child(rng: random.Random, gender: Optional[str], avoid: str = "") -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if g == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), g


def _pick_keeper(rng: random.Random, gender: Optional[str]) -> tuple[str, str]:
    g = gender or rng.choice(["woman", "man"])
    return (rng.choice(KEEPER_WOMEN), g) if g == "woman" else (rng.choice(KEEPER_MEN), g)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.shortcut:
        target = TARGETS[args.target]
        shortcut = SHORTCUTS[args.shortcut]
        if not compatible(target, shortcut):
            raise StoryError(explain_rejection(target, shortcut))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.target is None or combo[0] == args.target)
        and (args.shortcut is None or combo[1] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    target_id, shortcut_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_child(rng, args.child_gender)
    keeper_name, keeper_gender = _pick_keeper(rng, args.keeper_gender)
    relation = args.relation or rng.choice(["keeper", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(0, 10)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    if args.child_name:
        child_name = args.child_name

    return StoryParams(
        target=target_id,
        shortcut=shortcut_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        keeper_name=keeper_name,
        keeper_gender=keeper_gender,
        relation=relation,
        trait=trait,
        trust=trust,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    target = TARGETS[params.target]
    shortcut = SHORTCUTS[params.shortcut]
    response = RESPONSES[params.response]

    if not compatible(target, shortcut):
        raise StoryError(explain_rejection(target, shortcut))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        target=target,
        shortcut=shortcut,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        keeper_name=params.keeper_name,
        keeper_gender=params.keeper_gender,
        trait=params.trait,
        parent_type=params.relation,
        trust=params.trust,
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (target, shortcut) combos:\n")
        for target_id, shortcut_id in combos:
            print(f"  {target_id:14} {shortcut_id}")
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
            header = f"### {p.child_name}: {p.target} via {p.shortcut} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
