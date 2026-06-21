#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py
===================================================

A standalone story world for a child-facing whodunit shaped around one gentle
mystery: **a special suit goes missing, clues point to a suspect, and the
solution turns out to be an act of kindness.**

This world models a small "missing suit" mystery with typed entities, physical
meters, emotional memes, a simple forward-chaining rule layer, a Python
reasonableness gate, and an inline ASP twin. The stories are not template swaps:
state changes drive the turn from worry and suspicion to discovery and
kindness.

Run it
------
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py --venue recital_hall --need kitten
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py --place coat_closet
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py --response hand_brush
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py --asp
    python storyworlds/worlds/gpt-5.4/suit_kindness_whodunit.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""
    portable: bool = False
    soft: bool = False
    warmth: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
class Venue:
    id: str
    label: str
    event: str
    afford_places: set[str] = field(default_factory=set)
    afford_responses: set[str] = field(default_factory=set)
    opening: str = ""
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
class Need:
    id: str
    label: str
    who_phrase: str
    verb: str
    need_word: str
    clue: str
    clue_text: str
    trace_text: str
    hide_places: set[str] = field(default_factory=set)
    severity: int = 1
    tags: set[str] = field(default_factory=set)

    def clue_question(self) -> str:
        return {
            "pawprints": "What clue did they see on the floor?",
            "crumbs": "What clue did they see on the floor?",
            "raindrops": "What clue did they see on the floor?",
            "feathers": "What clue did they see on the floor?",
        }.get(self.clue, "What clue did they find?")
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
class Place:
    id: str
    label: str
    prep: str
    scene: str
    whisper: str
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
class Response:
    id: str
    sense: int = 0
    power: int = 0
    text: str = ""
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
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.venue)
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


def _r_missing_worry(world: World) -> list[str]:
    suit = world.get("suit")
    if suit.location != "missing":
        return []
    out: list[str] = []
    owner = world.get("owner")
    sig = ("missing_worry", owner.id)
    if sig not in world.fired:
        world.fired.add(sig)
        owner.memes["worry"] += 1
        out.append("__missing__")
    helper = world.get("helper")
    sig2 = ("helper_guilty", helper.id)
    if sig2 not in world.fired:
        world.fired.add(sig2)
        helper.memes["unease"] += 1
    return out


def _r_clue_focus(world: World) -> list[str]:
    if not world.facts.get("clue_seen"):
        return []
    owner = world.get("owner")
    detective = world.get("detective")
    out: list[str] = []
    for actor in (owner, detective):
        sig = ("focus", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["curiosity"] += 1
        out.append("__focus__")
    return out


def _r_reveal_kindness(world: World) -> list[str]:
    if not world.facts.get("truth_revealed"):
        return []
    owner = world.get("owner")
    helper = world.get("helper")
    needy = world.get("needy")
    out: list[str] = []
    sig = ("kindness", owner.id)
    if sig not in world.fired:
        world.fired.add(sig)
        owner.memes["kindness"] += 1
        owner.memes["worry"] = 0.0
        out.append("__kindness__")
    sig2 = ("gratitude", needy.id)
    if sig2 not in world.fired:
        world.fired.add(sig2)
        needy.memes["relief"] += 1
        helper.memes["relief"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_focus", tag="cognitive", apply=_r_clue_focus),
    Rule(name="reveal_kindness", tag="social", apply=_r_reveal_kindness),
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


VENUES = {
    "recital_hall": Venue(
        id="recital_hall",
        label="the recital hall",
        event="the spring music recital",
        afford_places={"under_piano", "coat_closet", "backstage_curtain"},
        afford_responses={"lint_roller", "warm_towel", "hand_brush"},
        opening="Rows of folding chairs waited under soft yellow lights, and every whisper sounded important.",
        tags={"hall", "music"},
    ),
    "town_hall": Venue(
        id="town_hall",
        label="the town hall",
        event="the kindness award ceremony",
        afford_places={"coat_closet", "reading_nook", "backstage_curtain"},
        afford_responses={"lint_roller", "hand_brush"},
        opening="The polished floor shone like a pond, and everybody was trying to walk quietly.",
        tags={"hall", "ceremony"},
    ),
    "photo_studio": Venue(
        id="photo_studio",
        label="the photo studio",
        event="a big family portrait",
        afford_places={"reading_nook", "coat_closet", "backstage_curtain"},
        afford_responses={"lint_roller", "warm_towel", "hand_brush"},
        opening="Bright lamps blinked softly, and a painted garden backdrop leaned against the wall.",
        tags={"photos", "family"},
    ),
}

NEEDS = {
    "kitten": Need(
        id="kitten",
        label="kitten",
        who_phrase="a tiny kitten",
        verb="was shivering",
        need_word="warmth",
        clue="pawprints",
        clue_text="little dusty paw prints",
        trace_text="The kitten had crawled away from a cracked side door and was trembling in the draft.",
        hide_places={"under_piano", "coat_closet"},
        severity=2,
        tags={"kitten", "animal", "warmth"},
    ),
    "puppy": Need(
        id="puppy",
        label="puppy",
        who_phrase="a wet puppy",
        verb="was dripping and whining",
        need_word="dryness",
        clue="raindrops",
        clue_text="a dotted trail of raindrops and paw marks",
        trace_text="The puppy had wandered in from the rain and was shaking water everywhere.",
        hide_places={"coat_closet", "backstage_curtain"},
        severity=2,
        tags={"puppy", "animal", "rain"},
    ),
    "cousin": Need(
        id="cousin",
        label="little cousin",
        who_phrase="a little cousin",
        verb="was hiding and trying not to cry",
        need_word="comfort",
        clue="crumbs",
        clue_text="cracker crumbs",
        trace_text="The little cousin had gotten stage fright and wanted a quiet, covered place to breathe.",
        hide_places={"reading_nook", "backstage_curtain"},
        severity=1,
        tags={"cousin", "comfort"},
    ),
    "duckling": Need(
        id="duckling",
        label="duckling",
        who_phrase="a lost duckling",
        verb="was peeping in a scared little voice",
        need_word="shelter",
        clue="feathers",
        clue_text="two downy yellow feathers",
        trace_text="The duckling had blundered in through an open loading door and pressed itself into a corner.",
        hide_places={"coat_closet", "under_piano"},
        severity=2,
        tags={"duckling", "animal", "shelter"},
    ),
}

PLACES = {
    "under_piano": Place(
        id="under_piano",
        label="under the grand piano",
        prep="under the grand piano",
        scene="In the dim space under the grand piano, the shadows looked as black as a detective's hat.",
        whisper="Something rustled beneath the piano bench.",
        tags={"piano", "dark"},
    ),
    "coat_closet": Place(
        id="coat_closet",
        label="inside the coat closet",
        prep="inside the coat closet",
        scene="The coat closet smelled of wool and rainy air, and all the hanging sleeves made tiny caves.",
        whisper="A small sound came from behind the winter coats.",
        tags={"closet", "coats"},
    ),
    "reading_nook": Place(
        id="reading_nook",
        label="in the reading nook",
        prep="in the reading nook",
        scene="The reading nook was tucked behind a screen, with pillows and a lamp shaped like a moon.",
        whisper="The lamp in the nook glowed on something dark and folded.",
        tags={"books", "quiet"},
    ),
    "backstage_curtain": Place(
        id="backstage_curtain",
        label="behind the backstage curtain",
        prep="behind the backstage curtain",
        scene="Behind the curtain, ropes and painted flats made a maze of corners and secrets.",
        whisper="The curtain gave the tiniest wobble.",
        tags={"curtain", "backstage"},
    ),
}

RESPONSES = {
    "lint_roller": Response(
        id="lint_roller",
        sense=3,
        power=1,
        text="used a sticky lint roller and quick careful hands until the cloth looked neat again",
        qa_text="used a lint roller to tidy the suit",
        tags={"lint_roller", "cleaning"},
    ),
    "warm_towel": Response(
        id="warm_towel",
        sense=3,
        power=2,
        text="pressed the cloth with a warm towel, dabbed away the marks, and smoothed the wrinkles with patient fingers",
        qa_text="used a warm towel to dry and smooth the suit",
        tags={"warm_towel", "cleaning"},
    ),
    "hand_brush": Response(
        id="hand_brush",
        sense=2,
        power=2,
        text="brushed the cloth, straightened the lapels, and puffed the jacket back into shape",
        qa_text="brushed and straightened the suit",
        tags={"hand_brush", "cleaning"},
    ),
    "blow_dryer": Response(
        id="blow_dryer",
        sense=1,
        power=1,
        text="waved a noisy blow-dryer at the cloth",
        qa_text="waved a blow-dryer at the suit",
        tags={"dryer", "cleaning"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Ruby", "Ivy", "Sasha", "June"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Eli", "Finn", "Owen", "Leo", "Jasper"]
TRAITS = ["careful", "bright", "gentle", "curious", "earnest", "thoughtful"]


def place_supports(venue: Venue, place: Place, need: Need) -> bool:
    return place.id in venue.afford_places and place.id in need.hide_places


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def available_sensible_responses(venue: Venue) -> list[Response]:
    return [RESPONSES[rid] for rid in sorted(venue.afford_responses) if RESPONSES[rid].sense >= SENSE_MIN]


def best_response_for(venue: Venue) -> Response:
    opts = available_sensible_responses(venue)
    if not opts:
        raise StoryError(f"(No story: {venue.label} has no sensible way to tidy the suit.)")
    return max(opts, key=lambda r: (r.power, r.sense, r.id))


def mess_severity(need: Need, delay: int) -> int:
    return need.severity + delay


def suit_ready(response: Response, need: Need, delay: int) -> bool:
    return response.power >= mess_severity(need, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for venue_id, venue in VENUES.items():
        if not available_sensible_responses(venue):
            continue
        for need_id, need in NEEDS.items():
            for place_id, place in PLACES.items():
                if place_supports(venue, place, need):
                    combos.append((venue_id, need_id, place_id))
    return combos


def explain_rejection(venue: Venue, need: Need, place: Place) -> str:
    if place.id not in venue.afford_places:
        return (
            f"(No story: {place.label} is not part of {venue.label}, so there is no fair clue trail there.)"
        )
    if place.id not in need.hide_places:
        return (
            f"(No story: {need.who_phrase} would not reasonably hide {place.prep}, so the mystery would feel forced.)"
        )
    return "(No story: this combination does not support a fair kindness mystery.)"


def explain_response(response_id: str, venue: Venue) -> str:
    r = RESPONSES[response_id]
    if r.sense < SENSE_MIN:
        better = ", ".join(sorted(x.id for x in available_sensible_responses(venue)))
        return (
            f"(Refusing response '{response_id}': it scores too low on common sense "
            f"(sense={r.sense} < {SENSE_MIN}). Try one of the sensible options at this venue: {better}.)"
        )
    if response_id not in venue.afford_responses:
        better = ", ".join(sorted(venue.afford_responses))
        return (
            f"(No story: {venue.label} does not have '{response_id}' available. "
            f"Try one of: {better}.)"
        )
    return ""


def predict_missing(world: World, need: Need, place: Place) -> dict:
    sim = world.copy()
    sim.get("suit").location = "missing"
    sim.get("suit").meters["hidden"] += 1
    sim.get("helper").location = place.id
    sim.get("needy").location = place.id
    sim.facts["clue_seen"] = True
    sim.facts["hidden_need"] = need.id
    propagate(sim, narrate=False)
    return {
        "owner_worry": sim.get("owner").memes["worry"],
        "detective_focus": sim.get("detective").memes["curiosity"],
    }


def introduce(world: World, owner: Entity, detective: Entity, venue: Venue) -> None:
    world.say(
        f"{owner.id} arrived at {venue.label} wearing a small blue suit for {venue.event}. "
        f"{venue.opening}"
    )
    world.say(
        f"{detective.id} came too, and the two of them liked pretending that every shiny floor and closed door might hide a clue."
    )


def admire_suit(world: World, owner: Entity) -> None:
    suit = world.get("suit")
    owner.memes["pride"] += 1
    suit.location = "hook"
    world.say(
        f"{owner.id} brushed the sleeve once and hung the suit jacket on a brass hook so it would stay crisp until it was time."
    )


def vanish(world: World, owner: Entity) -> None:
    suit = world.get("suit")
    suit.location = "missing"
    suit.meters["hidden"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {owner.id} reached for it again, the hook was empty. The suit had vanished."
    )
    if owner.memes["worry"] >= THRESHOLD:
        world.say(
            f'"This is a real case," {owner.id} whispered. "{owner.pronoun("possessive").capitalize()} suit cannot walk away by itself."'
        )


def gather_suspects(world: World, owner: Entity, detective: Entity, helper: Entity) -> None:
    detective.memes["play"] += 1
    world.say(
        f"{detective.id} put a finger to {detective.pronoun('possessive')} chin. "
        f'"Then we need suspects," {detective.pronoun()} said. "Maybe the wind. Maybe a prank. Maybe {helper.id}."'
    )
    world.facts["suspect_named"] = helper.id
    owner.memes["suspicion"] += 1


def first_clue(world: World, owner: Entity, detective: Entity, need: Need, place: Place) -> None:
    world.facts["clue_seen"] = True
    world.facts["first_place"] = place.id
    propagate(world, narrate=False)
    world.say(
        f"On the polished floor they found {need.clue_text} leading away from the empty hook."
    )
    if detective.memes["curiosity"] >= THRESHOLD:
        world.say(
            f'"A clue!" {detective.id} breathed. "{place.whisper}"'
        )


def follow_clue(world: World, place: Place) -> None:
    world.say(place.scene)
    world.say(
        f"The trail led {place.prep}."
    )


def reveal(world: World, owner: Entity, helper: Entity, needy: Entity, need: Need, place: Place) -> None:
    suit = world.get("suit")
    helper.location = place.id
    needy.location = place.id
    suit.location = place.id
    suit.meters["wrinkled"] += 1
    suit.meters["kind_use"] += 1
    if need.severity >= 2:
        suit.meters["mussed"] += 1
    world.facts["truth_revealed"] = True
    world.facts["kind_place"] = place.id
    propagate(world, narrate=False)
    world.say(
        f"There was {helper.id}, crouched {place.prep}, with {owner.id}'s suit jacket wrapped around {need.who_phrase} who {need.verb}."
    )
    world.say(
        f"{need.trace_text} {helper.id} looked up with wide eyes and said, "
        f'"I was going to tell you. {need.who_phrase.capitalize()} needed {need.need_word} right away."'
    )


def owner_choice(world: World, owner: Entity, helper: Entity, need: Need) -> None:
    owner.memes["kindness_choice"] += 1
    owner.memes["anger"] = 0.0
    world.say(
        f"For one tiny second, {owner.id} only saw the missing suit and the crumpled sleeve."
    )
    world.say(
        f"Then {owner.pronoun()} saw {need.who_phrase} pressing close to the warm cloth, and {owner.pronoun('possessive')} face softened."
    )
    world.say(
        f'"You should have told me," {owner.id} said, "but I am glad you were kind."'
    )
    helper.memes["gratitude"] += 1


def tidy_suit(world: World, adult: Entity, response: Response, need: Need, delay: int) -> None:
    suit = world.get("suit")
    ready = suit_ready(response, need, delay)
    if ready:
        suit.meters["ready"] = 1.0
        suit.meters["wrinkled"] = 0.0
        suit.meters["mussed"] = 0.0
    else:
        suit.meters["ready"] = 0.0
    world.say(
        f"{adult.label_word.capitalize()} came over, listened to the whole mystery, and {response.text}."
    )
    if ready:
        world.say(
            "Soon the jacket looked almost as sharp as before, with only the gentlest memory of the adventure left in it."
        )
    else:
        world.say(
            "The jacket was still a little rumpled, but it was clean enough and kind enough to wear proudly."
        )
    world.facts["ready"] = ready


def ending(world: World, owner: Entity, detective: Entity, helper: Entity, need: Need, venue: Venue) -> None:
    suit = world.get("suit")
    if world.facts.get("ready"):
        world.say(
            f"When it was finally time for {venue.event}, {owner.id} slipped back into the suit and stood a little taller."
        )
    else:
        world.say(
            f"When it was finally time for {venue.event}, {owner.id} slipped back into the suit, wrinkles and all, and stood a little taller anyway."
        )
    world.say(
        f"{detective.id} leaned over and whispered, \"Case solved.\""
    )
    world.say(
        f"And {owner.id} knew the best clue of all was this: a suit can look smart, but kindness is what makes someone truly grand."
    )
    if need.id in {"kitten", "puppy", "duckling"}:
        world.say(
            f"Nearby, the little {need.label} was safe at last, and even {helper.id} looked lighter, as if a hidden secret had turned into a warm bright truth."
        )
    else:
        world.say(
            f"Nearby, {need.who_phrase} was calm again, and even {helper.id} looked lighter, as if a hidden secret had turned into a warm bright truth."
        )


def tell(
    venue: Venue,
    need: Need,
    place: Place,
    response: Response,
    owner_name: str = "Lina",
    owner_gender: str = "girl",
    detective_name: str = "Theo",
    detective_gender: str = "boy",
    helper_name: str = "Milo",
    helper_gender: str = "boy",
    adult_type: str = "mother",
    owner_trait: str = "careful",
    delay: int = 0,
) -> World:
    world = World(venue)

    owner = world.add(
        Entity(
            id=owner_name,
            kind="character",
            type=owner_gender,
            role="owner",
            traits=[owner_trait],
        )
    )
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            role="detective",
            traits=["curious"],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            traits=["kind"],
        )
    )
    adult = world.add(
        Entity(
            id="Adult",
            kind="character",
            type=adult_type,
            role="adult",
            label="the grown-up",
        )
    )
    suit = world.add(
        Entity(
            id="suit",
            type="suit",
            label="blue suit jacket",
            owner=owner.id,
            portable=True,
            soft=True,
            warmth=2,
        )
    )
    needy_type = "animal" if need.id in {"kitten", "puppy", "duckling"} else "child"
    needy = world.add(
        Entity(
            id="needy",
            type=needy_type,
            label=need.label,
            role="needy",
        )
    )

    world.facts.update(
        venue=venue,
        need=need,
        place=place,
        response=response,
        delay=delay,
        clue_seen=False,
        truth_revealed=False,
        suspect_named="",
        ready=False,
    )

    introduce(world, owner, detective, venue)
    admire_suit(world, owner)

    world.para()
    vanish(world, owner)
    gather_suspects(world, owner, detective, helper)
    pred = predict_missing(world, need, place)
    world.facts["predicted_worry"] = pred["owner_worry"]
    world.facts["predicted_focus"] = pred["detective_focus"]
    first_clue(world, owner, detective, need, place)
    follow_clue(world, place)

    world.para()
    reveal(world, owner, helper, needy, need, place)
    owner_choice(world, owner, helper, need)

    world.para()
    tidy_suit(world, adult, response, need, delay)
    ending(world, owner, detective, helper, need, venue)

    world.facts.update(
        owner=owner,
        detective=detective,
        helper=helper,
        adult=adult,
        suit=suit,
        needy=needy,
        outcome="ready" if world.facts.get("ready") else "rumpled",
    )
    return world


@dataclass
class StoryParams:
    venue: str
    need: str
    place: str
    response: str
    owner: str
    owner_gender: str
    detective: str
    detective_gender: str
    helper: str
    helper_gender: str
    adult: str
    trait: str
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
    "kitten": [(
        "Why might a kitten need help in a busy place?",
        "A tiny kitten can get cold, frightened, or lost in a big noisy room. A gentle person should tell a grown-up and help keep it safe."
    )],
    "puppy": [(
        "Why does a wet puppy need to be dried off?",
        "A wet puppy can get cold and shaky. Drying it and getting help keeps it warm and comfortable."
    )],
    "duckling": [(
        "Why should a lost duckling be handled gently?",
        "A duckling is small and easily frightened. Gentle hands and a calm grown-up help it stay safe."
    )],
    "cousin": [(
        "What is stage fright?",
        "Stage fright is when someone feels scared about being seen by a crowd. A quiet space and kind words can help them calm down."
    )],
    "warmth": [(
        "Why can a piece of clothing help someone who is cold?",
        "Soft clothing can hold in warmth and block chilly air for a little while. It is a simple way to comfort someone until proper help comes."
    )],
    "rain": [(
        "Why do raindrops make clues on a floor?",
        "Water falls off something wet and leaves little spots behind. Those spots can show where someone went."
    )],
    "pawprints": [(
        "What are paw prints?",
        "Paw prints are marks left by an animal's feet. They can show that an animal walked through dust, water, or mud."
    )],
    "crumbs": [(
        "What are crumbs?",
        "Crumbs are tiny pieces of food that break off while someone is eating. They often show where a snack has been."
    )],
    "feathers": [(
        "What can a feather tell you in a mystery?",
        "A feather can be a clue that a bird was nearby. In a mystery, small clues help people figure out what happened."
    )],
    "lint_roller": [(
        "What does a lint roller do?",
        "A lint roller is a sticky tool that picks up fuzz, crumbs, and pet hair from clothes. It helps tidy fabric quickly."
    )],
    "warm_towel": [(
        "Why can a warm towel help clothing look better?",
        "A warm towel can dab away damp spots and help smooth fabric. It is a gentle way to freshen clothes."
    )],
    "hand_brush": [(
        "What does a clothes brush do?",
        "A clothes brush sweeps away dust and helps fabric lie flat. It can make a jacket look neat again."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness is choosing to help someone who needs comfort or care. Sometimes kindness means sharing something important for a little while."
    )],
    "mystery": [(
        "What is a whodunit?",
        "A whodunit is a mystery story where people follow clues to learn who did something. The fun comes from asking questions and solving the puzzle."
    )],
}
KNOWLEDGE_ORDER = [
    "mystery",
    "kindness",
    "kitten",
    "puppy",
    "duckling",
    "cousin",
    "warmth",
    "rain",
    "pawprints",
    "crumbs",
    "feathers",
    "lint_roller",
    "warm_towel",
    "hand_brush",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    detective = f["detective"]
    venue = f["venue"]
    need = f["need"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old about a missing suit at {venue.label}. Include the word "suit" and make the real answer an act of kindness.',
        f"Tell a gentle mystery where {owner.id} and {detective.id} follow clues after a blue suit disappears, then learn someone moved it to help {need.who_phrase}.",
        "Write a child-friendly detective story with a clear clue trail, a small surprise, and an ending where kindness matters more than looking perfect.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    detective = f["detective"]
    helper = f["helper"]
    adult = f["adult"]
    venue = f["venue"]
    need = f["need"]
    place = f["place"]
    response = f["response"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {owner.id}, {owner.pronoun('possessive')} friend {detective.id}, and the mystery of a missing suit at {venue.label}. It is also about {helper.id}, whose secret choice turns out to be kind.",
        ),
        (
            f"Why was the suit important that day?",
            f"{owner.id} was going to wear it for {venue.event}. That is why the empty hook felt like such a serious clue.",
        ),
        (
            need.clue_question(),
            f"They saw {need.clue_text} on the floor. Those marks gave them a fair trail to follow toward {place.label}.",
        ),
        (
            f"Why did {owner.id} first think something bad had happened?",
            f"{owner.id} only knew that the suit was gone and {helper.id} had been named as a suspect. With no answer yet, the mystery made {owner.pronoun('object')} worried.",
        ),
        (
            f"What had really happened to the suit?",
            f"{helper.id} had taken the suit jacket to help {need.who_phrase}, who {need.verb}. It was not a mean trick at all; it was a quick act of kindness.",
        ),
        (
            f"How did {owner.id} react when the truth came out?",
            f"At first {owner.id} noticed the wrinkled cloth and the missing suit. Then {owner.pronoun()} saw why it had been used and chose kindness over anger.",
        ),
    ]

    if outcome == "ready":
        qa.append(
            (
                "Was the suit ruined?",
                f"No. {adult.label_word.capitalize()} {response.qa_text}, so the suit was ready in time. The ending shows that the mystery was solved without losing the big event.",
            )
        )
    else:
        qa.append(
            (
                "Was the suit ruined?",
                f"No, but it stayed a little rumpled. {adult.label_word.capitalize()} {response.qa_text}, and {owner.id} wore it proudly anyway because the kind deed mattered more than perfect cloth.",
            )
        )

    qa.append(
        (
            "How did the story end?",
            f"It ended with the case solved, the suit back on {owner.id}, and everybody understanding what had really happened. The final change is that the missing suit stops being a problem and becomes proof of kindness.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    need = f["need"]
    response = f["response"]
    tags: set[str] = {"mystery", "kindness"}

    if need.id == "kitten":
        tags |= {"kitten", "warmth", "pawprints"}
    elif need.id == "puppy":
        tags |= {"puppy", "rain"}
    elif need.id == "duckling":
        tags |= {"duckling", "feathers"}
    elif need.id == "cousin":
        tags |= {"cousin", "crumbs"}

    tags.add(response.id)

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
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {{k: v for k, v in world.facts.items() if k not in {'owner', 'detective', 'helper', 'adult', 'suit', 'needy'}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="recital_hall",
        need="kitten",
        place="under_piano",
        response="warm_towel",
        owner="Lina",
        owner_gender="girl",
        detective="Theo",
        detective_gender="boy",
        helper="Milo",
        helper_gender="boy",
        adult="mother",
        trait="careful",
        delay=0,
    ),
    StoryParams(
        venue="town_hall",
        need="cousin",
        place="reading_nook",
        response="lint_roller",
        owner="Ben",
        owner_gender="boy",
        detective="Ruby",
        detective_gender="girl",
        helper="Ella",
        helper_gender="girl",
        adult="father",
        trait="earnest",
        delay=0,
    ),
    StoryParams(
        venue="photo_studio",
        need="puppy",
        place="coat_closet",
        response="warm_towel",
        owner="Nora",
        owner_gender="girl",
        detective="Finn",
        detective_gender="boy",
        helper="Ivy",
        helper_gender="girl",
        adult="mother",
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        venue="recital_hall",
        need="duckling",
        place="under_piano",
        response="hand_brush",
        owner="Eli",
        owner_gender="boy",
        detective="June",
        detective_gender="girl",
        helper="Maya",
        helper_gender="girl",
        adult="uncle",
        trait="bright",
        delay=1,
    ),
    StoryParams(
        venue="town_hall",
        need="kitten",
        place="coat_closet",
        response="hand_brush",
        owner="Sasha",
        owner_gender="girl",
        detective="Leo",
        detective_gender="boy",
        helper="Owen",
        helper_gender="boy",
        adult="aunt",
        trait="gentle",
        delay=1,
    ),
]


def outcome_of(params: StoryParams) -> str:
    venue = VENUES[params.venue]
    need = NEEDS[params.need]
    response = RESPONSES[params.response]
    if response.id not in venue.afford_responses or response.sense < SENSE_MIN:
        raise StoryError("(No story: invalid response for this venue.)")
    return "ready" if suit_ready(response, need, params.delay) else "rumpled"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(V, N, P) :- venue(V), need(N), place(P), affords_place(V, P), hides_in(N, P), sensible_venue(V).
sensible_venue(V) :- venue(V), affords_response(V, R), response(R), sense(R, S), sense_min(M), S >= M.

% --- response availability / outcome --------------------------------------
response_ok(V, R) :- affords_response(V, R), response(R), sense(R, S), sense_min(M), S >= M.
severity(N, D, S) :- need(N), need_severity(N, NS), delay(D), S = NS + D.
ready :- chosen_venue(V), chosen_need(N), chosen_response(R), response_ok(V, R),
         severity(N, D, S), delay(D), power(R, P), P >= S.
outcome(ready) :- ready.
outcome(rumpled) :- not ready.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        for place_id in sorted(venue.afford_places):
            lines.append(asp.fact("affords_place", venue_id, place_id))
        for response_id in sorted(venue.afford_responses):
            lines.append(asp.fact("affords_response", venue_id, response_id))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        lines.append(asp.fact("need_severity", need_id, need.severity))
        for place_id in sorted(need.hide_places):
            lines.append(asp.fact("hides_in", need_id, place_id))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_venue", params.venue),
            asp.fact("chosen_need", params.need),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
            if py != cl:
                bad += 1
        except StoryError:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a missing suit, a clue trail, and a kind answer."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the suit was used before it was found")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n not in avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    venue_id = args.venue or rng.choice(sorted(VENUES))
    venue = VENUES[venue_id]

    if args.response:
        msg = explain_response(args.response, venue)
        if msg:
            raise StoryError(msg)

    if args.place and args.need and args.venue:
        if not place_supports(venue, PLACES[args.place], NEEDS[args.need]):
            raise StoryError(explain_rejection(venue, NEEDS[args.need], PLACES[args.place]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.need is None or combo[1] == args.need)
        and (args.place is None or combo[2] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, need_id, place_id = rng.choice(sorted(combos))
    venue = VENUES[venue_id]

    responses = [
        rid
        for rid in sorted(venue.afford_responses)
        if RESPONSES[rid].sense >= SENSE_MIN
        and (args.response is None or rid == args.response)
    ]
    if not responses:
        raise StoryError(f"(No story: {venue.label} has no sensible response matching the request.)")

    response_id = rng.choice(responses)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])

    owner_gender = rng.choice(["girl", "boy"])
    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])

    used: set[str] = set()
    owner = _pick_name(rng, owner_gender, used)
    used.add(owner)
    detective = _pick_name(rng, detective_gender, used)
    used.add(detective)
    helper = _pick_name(rng, helper_gender, used)

    trait = rng.choice(TRAITS)

    return StoryParams(
        venue=venue_id,
        need=need_id,
        place=place_id,
        response=response_id,
        owner=owner,
        owner_gender=owner_gender,
        detective=detective,
        detective_gender=detective_gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(No story: unknown venue '{params.venue}'.)")
    if params.need not in NEEDS:
        raise StoryError(f"(No story: unknown need '{params.need}'.)")
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")

    venue = VENUES[params.venue]
    need = NEEDS[params.need]
    place = PLACES[params.place]
    response = RESPONSES[params.response]

    if not place_supports(venue, place, need):
        raise StoryError(explain_rejection(venue, need, place))
    msg = explain_response(params.response, venue)
    if msg:
        raise StoryError(msg)

    world = tell(
        venue=venue,
        need=need,
        place=place,
        response=response,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_type=params.adult,
        owner_trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, need, place) combos:\n")
        for venue, need, place in combos:
            print(f"  {venue:13} {need:8} {place}")
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
            header = f"### {p.owner}: {p.need} at {p.venue} ({p.place}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
