#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shackle_cleat_reciprocate_misunderstanding_slice_of_life.py
======================================================================================

A standalone story world about a small misunderstanding at a dock. Two children
are getting ready near a little sailboat. One child does a kind favor and waits
for the other child to reciprocate, but a blocked reply makes the kindness feel
ignored. The misunderstanding is later cleared by a concrete helpful action and
a simple explanation.

The domain is deliberately small and child-facing:
- a dockside place with a little boat
- a favor offered between children
- a hidden cause that blocks the reply
- a later small problem the other child can solve to reciprocate

The words "shackle", "cleat", and "reciprocate" are included naturally in the
stories and world knowledge.

Run it
------
    python storyworlds/worlds/gpt-5.4/shackle_cleat_reciprocate_misunderstanding_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/shackle_cleat_reciprocate_misunderstanding_slice_of_life.py --place marina --cause motorboat
    python storyworlds/worlds/gpt-5.4/shackle_cleat_reciprocate_misunderstanding_slice_of_life.py --place quiet_pond
    python storyworlds/worlds/gpt-5.4/shackle_cleat_reciprocate_misunderstanding_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/shackle_cleat_reciprocate_misunderstanding_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shackle_cleat_reciprocate_misunderstanding_slice_of_life.py --verify
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    scene: str
    water: str
    dock_kind: str
    supports_motorboat: bool = False
    supports_wind: bool = True
    has_cleat: bool = True
    has_boat: bool = True
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
class Favor:
    id: str
    opening: str
    object_label: str
    need: str
    action_word: str
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
class Cause:
    id: str
    text: str
    blocks_reply: str
    needs_motorboat: bool = False
    needs_hands_busy: bool = False
    needs_wind: bool = False
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
class Reciprocation:
    id: str
    problem_text: str
    fix_text: str
    ending_text: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "reply_blocked": False,
            "misunderstood": False,
            "explained": False,
            "reciprocated": False,
            "cause_text": "",
            "hurt_level": "mild",
        }

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


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts["reply_blocked"]:
        return out
    if world.facts["explained"]:
        return out
    sig = ("misread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["hurt"] += 1
    hero.memes["confusion"] += 1
    friend.memes["flustered"] += 1
    world.facts["misunderstood"] = True
    out.append("__misunderstood__")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if not (world.facts["explained"] and world.facts["reciprocated"]):
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["hurt"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    friend.memes["gratitude"] += 1
    friend.memes["relief"] += 1
    world.facts["misunderstood"] = False
    out.append("__repair__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="misread", tag="social", apply=_r_misread),
    Rule(name="repair", tag="social", apply=_r_repair),
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


def cause_works(place: Place, cause: Cause) -> bool:
    if cause.needs_motorboat and not place.supports_motorboat:
        return False
    if cause.needs_wind and not place.supports_wind:
        return False
    if cause.needs_hands_busy and not (place.has_cleat and place.has_boat):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for favor_id in FAVORS:
            for cause_id, cause in CAUSES.items():
                if not cause_works(place, cause):
                    continue
                for rec_id in RECIPROCATIONS:
                    combos.append((place_id, favor_id, cause_id, rec_id))
    return combos


def explain_rejection(place: Place, cause: Cause) -> str:
    if cause.needs_motorboat and not place.supports_motorboat:
        return (
            f"(No story: {place.label} is too quiet for the '{cause.id}' cause. "
            "There is no passing motorboat there to swallow a reply.)"
        )
    if cause.needs_hands_busy and not (place.has_boat and place.has_cleat):
        return (
            f"(No story: {place.label} does not provide the boat hardware needed for "
            "a hands-busy misunderstanding with a shackle and cleat.)"
        )
    if cause.needs_wind and not place.supports_wind:
        return (
            f"(No story: {place.label} does not fit the windy misunderstanding you asked for.)"
        )
    return "(No story: that place and cause do not make a believable misunderstanding.)"


def predict_hurt(place: Place, cause: Cause) -> str:
    if cause.id == "motorboat":
        return "sharp"
    if cause.id == "busy_hands":
        return "mild"
    if cause.id == "wind":
        return "mild"
    return "mild"


def introduce(world: World, hero: Entity, friend: Entity, place: Place) -> None:
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    world.say(
        f"After school, {hero.id} met {friend.id} at {place.label}. {place.scene}"
    )
    world.say(
        f"A little sailboat bumped softly against {place.dock_kind}, and the water in "
        f"{place.water} flashed silver between the boards."
    )


def show_boat_task(world: World, friend: Entity) -> None:
    friend.meters["hands_busy"] += 1
    world.say(
        f"{friend.id} was crouched near the bow, fastening a small shackle and "
        f"looping the rope around a cleat so the boat would stay put while they got ready."
    )


def favor_beat(world: World, hero: Entity, friend: Entity, favor: Favor) -> None:
    hero.memes["kindness"] += 1
    friend.memes["need"] += 1
    world.say(
        f"When {friend.id} needed {favor.need}, {hero.id} {favor.opening}."
    )
    world.say(
        f"It was a small thing, but {hero.id} felt pleased to be useful."
    )


def blocked_reply(world: World, hero: Entity, friend: Entity, cause: Cause) -> None:
    world.facts["reply_blocked"] = True
    world.facts["cause_text"] = cause.text
    world.facts["hurt_level"] = predict_hurt(world.place, cause)
    propagate(world, narrate=False)
    world.say(
        f"{friend.id} tried to answer right away, but {cause.text}"
    )
    if world.facts["hurt_level"] == "sharp":
        world.say(
            f"From where {hero.id} stood, it looked as if {friend.pronoun()} had simply taken the help and turned away."
        )
    else:
        world.say(
            f"From where {hero.id} stood, it looked as if {friend.pronoun()} had not bothered to answer."
        )


def hurt_beat(world: World, hero: Entity, friend: Entity, favor: Favor) -> None:
    if hero.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{hero.id} pressed {hero.pronoun('possessive')} lips together and stepped back. "
            f"{hero.pronoun().capitalize()} had hoped {friend.id} would at least thank "
            f"{hero.pronoun('object')}, or maybe reciprocate later by helping with the next little job."
        )
    else:
        world.say(
            f"{hero.id} waited a second, then looked down at the boards of the dock."
        )


def later_problem(world: World, hero: Entity, rec: Reciprocation) -> None:
    hero.meters["wobble"] += 1
    world.say(rec.problem_text)


def reciprocate_help(world: World, hero: Entity, friend: Entity, rec: Reciprocation) -> None:
    world.facts["reciprocated"] = True
    friend.memes["kindness"] += 1
    hero.meters["wobble"] = 0.0
    world.say(rec.fix_text)


def explain(world: World, hero: Entity, friend: Entity, favor: Favor, cause: Cause) -> None:
    world.facts["explained"] = True
    propagate(world, narrate=False)
    world.say(
        f'"I was trying to thank you," {friend.id} said. "I just could not get the words out because {cause.blocks_reply}."'
    )
    world.say(
        f'"You helped me with the {favor.object_label}, and I wanted to reciprocate, not ignore you."'
    )


def ending(world: World, hero: Entity, friend: Entity, rec: Reciprocation) -> None:
    hero.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    world.say(
        f"{hero.id} felt silly for guessing wrong, but lighter too. The hard little knot in "
        f"{hero.pronoun('possessive')} chest was gone."
    )
    world.say(rec.ending_text)


def tell(
    place: Place,
    favor: Favor,
    cause: Cause,
    rec: Reciprocation,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    friend_name: str = "Owen",
    friend_gender: str = "boy",
    parent_type: str = "father",
    hero_trait: str = "thoughtful",
    friend_trait: str = "steady",
) -> World:
    world = World(place)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[hero_trait],
            attrs={"expected_reciprocation": True},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            label=friend_name,
            role="friend",
            traits=[friend_trait],
            attrs={"working_on_boat": True},
        )
    )
    world.add(
        Entity(
            id="adult",
            kind="character",
            type=parent_type,
            label="the sailing teacher",
            role="adult",
            traits=["nearby"],
            attrs={"watching": True},
        )
    )
    world.add(
        Entity(
            id="boat",
            kind="thing",
            type="sailboat",
            label="the little sailboat",
            attrs={"has_shackle": True, "has_cleat": True},
        )
    )

    introduce(world, hero, friend, place)
    show_boat_task(world, friend)

    world.para()
    favor_beat(world, hero, friend, favor)
    blocked_reply(world, hero, friend, cause)
    hurt_beat(world, hero, friend, favor)

    world.para()
    later_problem(world, hero, rec)
    reciprocate_help(world, hero, friend, rec)
    explain(world, hero, friend, favor, cause)

    world.para()
    ending(world, hero, friend, rec)

    world.facts.update(
        hero=hero,
        friend=friend,
        favor=favor,
        cause=cause,
        place_cfg=place,
        reciprocation=rec,
        repaired=world.facts["explained"] and world.facts["reciprocated"],
    )
    return world


PLACES = {
    "lake_dock": Place(
        id="lake_dock",
        label="the little lake dock",
        scene="The boards were warm from the sun, and someone had left a coil of rope in a neat yellow ring.",
        water="the lake",
        dock_kind="the dock cleat",
        supports_motorboat=True,
        supports_wind=True,
        has_cleat=True,
        has_boat=True,
        tags={"dock", "boat"},
    ),
    "marina": Place(
        id="marina",
        label="the marina",
        scene="Painted posts stood in a row, and the air smelled like rope, wood, and clean water.",
        water="the marina basin",
        dock_kind="a weathered cleat",
        supports_motorboat=True,
        supports_wind=True,
        has_cleat=True,
        has_boat=True,
        tags={"dock", "boat", "marina"},
    ),
    "quiet_pond": Place(
        id="quiet_pond",
        label="the quiet pond landing",
        scene="The narrow landing sat under willow branches, and the water barely wrinkled at all.",
        water="the pond",
        dock_kind="the small wooden cleat",
        supports_motorboat=False,
        supports_wind=True,
        has_cleat=True,
        has_boat=True,
        tags={"dock", "boat", "pond"},
    ),
}

FAVORS = {
    "carry_bag": Favor(
        id="carry_bag",
        opening="lifted the heavy sail bag onto the bench for him",
        object_label="sail bag",
        need="help getting the sail bag up from the ground",
        action_word="carry",
        tags={"help", "gear"},
    ),
    "hold_line": Favor(
        id="hold_line",
        opening="held the bow line high so it would not drag in the water",
        object_label="bow line",
        need="an extra hand with the rope",
        action_word="hold",
        tags={"help", "rope"},
    ),
    "lend_towel": Favor(
        id="lend_towel",
        opening="passed over her striped towel so he could dry the wet seat",
        object_label="towel",
        need="something dry for the seat",
        action_word="lend",
        tags={"help", "towel"},
    ),
}

CAUSES = {
    "busy_hands": Cause(
        id="busy_hands",
        text="both of his hands were still full with the shackle and rope, and if he let go the boat would swing away from the cleat.",
        blocks_reply="my hands were busy and the boat would have drifted off the cleat",
        needs_hands_busy=True,
        tags={"misunderstanding", "dock"},
    ),
    "wind": Cause(
        id="wind",
        text="a quick gust snapped the little sailcloth cover and blew his first words right across the water.",
        blocks_reply="the wind snatched my words away",
        needs_wind=True,
        tags={"misunderstanding", "wind"},
    ),
    "motorboat": Cause(
        id="motorboat",
        text="a passing motorboat growled at just that moment and swallowed his voice under its engine noise.",
        blocks_reply="a motorboat went by and you could not hear me",
        needs_motorboat=True,
        tags={"misunderstanding", "noise"},
    ),
}

RECIPROCATIONS = {
    "catch_cap": Reciprocation(
        id="catch_cap",
        problem_text="Just then, a puff of air skipped over the dock and tugged {hero}'s cap off {poss} head. It skittered toward the edge.".replace(
            "{hero}", "{hero}"
        ),
        fix_text="{friend} lunged, caught the cap with two fingers, and set it back in {hero}'s hands before it could fall into the water.",
        ending_text="Together they sat on the edge of the dock with their feet tucked up, and the boat rocked quietly beside them.",
        tags={"help", "cap"},
    ),
    "save_sketchbook": Reciprocation(
        id="save_sketchbook",
        problem_text="{hero} had brought a little sketchbook to draw the boats, and it slid off the bench when {poss} elbow bumped it.",
        fix_text="{friend} caught the sketchbook against his knee, wiped one damp corner with the towel, and handed it over carefully.",
        ending_text="After that, they drew little boats in the margins of the page while waiting for their turn on the water.",
        tags={"help", "sketchbook"},
    ),
    "steady_juice": Reciprocation(
        id="steady_juice",
        problem_text="{hero}'s juice bottle tipped from the bench and began to wobble toward a crack between the boards.",
        fix_text="{friend} pinned it with his shoe, picked it up, and tightened the lid before giving it back.",
        ending_text="A minute later they were sharing crackers on the bench, with the boat rope neat and safe beside them.",
        tags={"help", "juice"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Ruby", "Tessa", "Maya", "Zoe"]
BOY_NAMES = ["Owen", "Ben", "Sam", "Theo", "Finn", "Eli", "Max", "Leo"]
TRAITS = ["thoughtful", "patient", "quiet", "careful", "cheerful", "steady"]


@dataclass
class StoryParams:
    place: str
    favor: str
    cause: str
    reciprocation: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    hero_trait: str
    friend_trait: str
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


def _render_problem_text(rec: Reciprocation, hero: Entity) -> str:
    return (
        rec.problem_text.replace("{hero}", hero.id)
        .replace("{poss}", hero.pronoun("possessive"))
    )


def _render_fix_text(rec: Reciprocation, hero: Entity, friend: Entity) -> str:
    return (
        rec.fix_text.replace("{hero}", hero.id)
        .replace("{friend}", friend.id)
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    favor = f["favor"]
    cause = f["cause"]
    place = f["place_cfg"]
    rec = f["reciprocation"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old about two children at {place.label} where a small misunderstanding happens after one child helps the other. Include the words "shackle", "cleat", and "reciprocate".',
        f"Tell a gentle story where {hero.id} helps {friend.id} with the {favor.object_label}, thinks the kindness was ignored, and later learns that {cause.id.replace('_', ' ')} caused the misunderstanding.",
        f"Write a calm story about ordinary feelings, a mistaken guess, and a small act of kindness where {friend.id} gets the chance to reciprocate by {rec.id.replace('_', ' ')}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    favor = f["favor"]
    cause = f["cause"]
    place = f["place_cfg"]
    rec = f["reciprocation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} at {place.label}, getting ready beside a little sailboat. The story follows how a small misunderstanding grew between them and then was gently fixed.",
        ),
        (
            f"What kind thing did {hero.id} do first?",
            f"{hero.id} helped {friend.id} with the {favor.object_label}. It felt small, but it mattered because {friend.id} needed that help right then.",
        ),
        (
            f"Why did {hero.id} think {friend.id} was being unkind?",
            f"{hero.id} could not hear or see the answer the way {friend.id} meant it. Because {cause.blocks_reply}, the reply was blocked, so the kindness looked ignored even though it was not.",
        ),
        (
            f"What was {friend.id} doing near the boat?",
            f"{friend.id} was fastening a shackle and keeping the rope secure on a cleat so the little boat would stay in place. That job is part of why the misunderstanding could happen at all.",
        ),
        (
            f"How did {friend.id} reciprocate later?",
            f"{_render_fix_text(rec, hero, friend)} That helpful action showed with deeds what {friend.pronoun()} had not been able to say earlier.",
        ),
        (
            "How was the misunderstanding solved?",
            f"It was solved when {friend.id} both helped and explained. The explanation named the blocked reply, and the helpful action made the true feeling easy to believe.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "shackle": [
        (
            "What is a shackle?",
            "A shackle is a small metal loop with a pin that can hold parts together. People use one on boats when they need to clip a rope or fitting in place.",
        )
    ],
    "cleat": [
        (
            "What is a cleat on a dock?",
            "A cleat is a strong metal piece fixed to a dock or boat. You wrap a rope around it to keep the boat from drifting away.",
        )
    ],
    "reciprocate": [
        (
            "What does reciprocate mean?",
            "To reciprocate means to return a kindness with kindness. If someone helps you, you reciprocate when you help them back.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone guesses wrong about what another person meant. It can happen even when nobody wanted to be mean.",
        )
    ],
    "wind": [
        (
            "How can wind make it hard to hear?",
            "Wind can whip sounds away and flap cloth or ropes loudly. Then a person's words may not reach your ears clearly.",
        )
    ],
    "motorboat": [
        (
            "Why is an engine hard to talk over?",
            "An engine can make a loud rumbling sound that covers softer voices. That means someone may speak kindly and still not be heard.",
        )
    ],
    "dock": [
        (
            "Why do boats need to be tied at a dock?",
            "Boats float and move with water and wind, so they can drift if nobody secures them. A tied rope keeps the boat close and safe while people get ready.",
        )
    ],
}
KNOWLEDGE_ORDER = ["shackle", "cleat", "reciprocate", "misunderstanding", "wind", "motorboat", "dock"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"shackle", "cleat", "reciprocate", "misunderstanding", "dock"}
    cause_id = world.facts["cause"].id
    if cause_id == "wind":
        tags.add("wind")
    if cause_id == "motorboat":
        tags.add("motorboat")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={{{k: v for k, v in world.facts.items() if isinstance(v, (str, bool))}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, F, C, R) :- place(P), favor(F), cause(C), reciprocation(R), cause_ok(P, C).

cause_ok(P, C) :- cause(C), not needs_motorboat(C), not needs_hands_busy(C), not needs_wind(C).
cause_ok(P, C) :- cause(C), needs_motorboat(C), supports_motorboat(P).
cause_ok(P, C) :- cause(C), needs_hands_busy(C), has_boat(P), has_cleat(P).
cause_ok(P, C) :- cause(C), needs_wind(C), supports_wind(P).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        if place.supports_motorboat:
            lines.append(asp.fact("supports_motorboat", place_id))
        if place.supports_wind:
            lines.append(asp.fact("supports_wind", place_id))
        if place.has_boat:
            lines.append(asp.fact("has_boat", place_id))
        if place.has_cleat:
            lines.append(asp.fact("has_cleat", place_id))
    for favor_id in FAVORS:
        lines.append(asp.fact("favor", favor_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        if cause.needs_motorboat:
            lines.append(asp.fact("needs_motorboat", cause_id))
        if cause.needs_hands_busy:
            lines.append(asp.fact("needs_hands_busy", cause_id))
        if cause.needs_wind:
            lines.append(asp.fact("needs_wind", cause_id))
    for rec_id in RECIPROCATIONS:
        lines.append(asp.fact("reciprocation", rec_id))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        place="lake_dock",
        favor="carry_bag",
        cause="busy_hands",
        reciprocation="catch_cap",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        parent="father",
        hero_trait="thoughtful",
        friend_trait="steady",
    ),
    StoryParams(
        place="marina",
        favor="lend_towel",
        cause="motorboat",
        reciprocation="save_sketchbook",
        hero_name="Ruby",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        hero_trait="careful",
        friend_trait="quiet",
    ),
    StoryParams(
        place="quiet_pond",
        favor="hold_line",
        cause="wind",
        reciprocation="steady_juice",
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Maya",
        friend_gender="girl",
        parent="father",
        hero_trait="patient",
        friend_trait="cheerful",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a dockside misunderstanding, a blocked reply, and a gentle reciprocation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--favor", choices=FAVORS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--reciprocation", choices=RECIPROCATIONS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cause:
        place = PLACES[args.place]
        cause = CAUSES[args.cause]
        if not cause_works(place, cause):
            raise StoryError(explain_rejection(place, cause))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.favor is None or c[1] == args.favor)
        and (args.cause is None or c[2] == args.cause)
        and (args.reciprocation is None or c[3] == args.reciprocation)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, favor_id, cause_id, rec_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        favor=favor_id,
        cause=cause_id,
        reciprocation=rec_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.favor not in FAVORS:
        raise StoryError(f"(Unknown favor: {params.favor})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.reciprocation not in RECIPROCATIONS:
        raise StoryError(f"(Unknown reciprocation: {params.reciprocation})")

    place = PLACES[params.place]
    cause = CAUSES[params.cause]
    if not cause_works(place, cause):
        raise StoryError(explain_rejection(place, cause))

    world = tell(
        place=place,
        favor=FAVORS[params.favor],
        cause=cause,
        rec=RECIPROCATIONS[params.reciprocation],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
        friend_trait=params.friend_trait,
    )

    hero = world.get("hero")
    friend = world.get("friend")
    rec = world.facts["reciprocation"]
    for i, paragraph in enumerate(world.paragraphs):
        if not paragraph:
            continue
        world.paragraphs[i] = [
            line
            .replace("{hero}", hero.id)
            .replace("{friend}", friend.id)
            .replace("{poss}", hero.pronoun("possessive"))
            for line in paragraph
        ]

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
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP failure: {exc}")
        return 1

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

    smoke_cases = list(CURATED)
    try:
        parser = build_parser()
        for seed in range(5):
            args = parser.parse_args([])
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            smoke_cases.append(p)
    except Exception as exc:
        print(f"SMOKE setup failed: {exc}")
        return 1

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            if sample.world is None:
                raise StoryError("missing world")
            _ = sample.to_dict()
        except Exception as exc:
            print(f"SMOKE failure on case {idx}: {exc}")
            return 1

    print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, favor, cause, reciprocation) combos:\n")
        for place, favor, cause, rec in combos:
            print(f"  {place:11} {favor:11} {cause:11} {rec}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.place}, {p.cause}, {p.reciprocation}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
