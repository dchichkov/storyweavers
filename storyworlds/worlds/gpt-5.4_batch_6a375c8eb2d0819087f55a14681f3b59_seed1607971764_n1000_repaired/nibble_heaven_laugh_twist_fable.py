#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nibble_heaven_laugh_twist_fable.py
=============================================================

A standalone story world in a small fable domain: a hungry little animal sees a
crumb drift down from above and calls it "a nibble from heaven." A wiser friend
urges patience. The twist is that the supposed heavenly gift has an ordinary
source above -- a baker, a miller, or a bell-ringer -- and the ending depends on
whether the seeker rushes upward or waits to learn the truth.

This world models:
- typed entities with physical meters and emotional memes
- a small causal engine for wobble, tumbles, sharing, and lessons
- a reasonableness gate over who can climb where
- an inline ASP twin for the compatibility and outcome logic
- three Q&A sets generated from world state, not from parsing prose

Run it
------
python storyworlds/worlds/gpt-5.4/nibble_heaven_laugh_twist_fable.py
python storyworlds/worlds/gpt-5.4/nibble_heaven_laugh_twist_fable.py --all
python storyworlds/worlds/gpt-5.4/nibble_heaven_laugh_twist_fable.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/nibble_heaven_laugh_twist_fable.py --trace --seed 12
python storyworlds/worlds/gpt-5.4/nibble_heaven_laugh_twist_fable.py --verify
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
TUMBLE_LIMIT = 4


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
        if self.type in {"mouse", "squirrel", "hedgehog", "rabbit", "sparrow", "crow", "owl"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"hen", "goose"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SeekerKind:
    id: str
    label: str
    agility: int
    weight: int
    nibble_verb: str
    home_image: str
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
class HelperKind:
    id: str
    label: str
    counsel: str
    watch_style: str
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
    type: str
    perch: str
    height: int
    crumb_label: str
    crumb_phrase: str
    gift_phrase: str
    action: str
    laugh_style: str
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
class Route:
    id: str
    label: str
    reaches: set[str]
    shaky: int
    style: str
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


def climb_risk(seeker: SeekerKind, source: Source, route: Route) -> int:
    return source.height + route.shaky + seeker.weight - seeker.agility


def route_works(seeker: SeekerKind, source: Source, route: Route) -> bool:
    return source.perch in route.reaches and climb_risk(seeker, source, route) <= 5


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for seeker_id, seeker in SEEKERS.items():
        for source_id, source in SOURCES.items():
            for route_id, route in ROUTES.items():
                if route_works(seeker, source, route):
                    combos.append((seeker_id, source_id, route_id))
    return sorted(combos)


def explain_rejection(seeker: SeekerKind, source: Source, route: Route) -> str:
    if source.perch not in route.reaches:
        return (
            f"(No story: {route.label} does not reach the {source.perch}, so "
            f"{seeker.label} has no honest way even to try the climb.)"
        )
    risk = climb_risk(seeker, source, route)
    return (
        f"(No story: {seeker.label} on {route.label} is too unsafe for the "
        f"{source.perch} here (risk {risk} > 5). Pick a steadier route or a "
        f"nimbler seeker.)"
    )


def outcome_of(params: "StoryParams") -> str:
    seeker = SEEKERS[params.seeker]
    source = SOURCES[params.source]
    route = ROUTES[params.route]
    if params.choice == "wait":
        return "wise"
    return "tumble" if climb_risk(seeker, source, route) >= TUMBLE_LIMIT else "scramble"


def _r_wobble(world: World) -> list[str]:
    seeker = world.get("seeker")
    helper = world.get("helper")
    if seeker.meters["wobble"] < THRESHOLD:
        return []
    sig = ("wobble", seeker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["fear"] += 1
    helper.memes["alarm"] += 1
    return []


def _r_tumble(world: World) -> list[str]:
    seeker = world.get("seeker")
    if seeker.meters["wobble"] < TUMBLE_LIMIT:
        return []
    sig = ("tumble", seeker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.meters["bruise"] += 1
    seeker.meters["on_ground"] = 1
    seeker.meters["climbing"] = 0
    seeker.memes["shame"] += 1
    seeker.memes["humility"] += 1
    return ["__tumble__"]


def _r_share(world: World) -> list[str]:
    seeker = world.get("seeker")
    helper = world.get("helper")
    if world.facts.get("gift_waiting", 0) < THRESHOLD:
        return []
    sig = ("share", seeker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.meters["belly_full"] += 1
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="tumble", tag="physical", apply=_r_tumble),
    Rule(name="share", tag="social", apply=_r_share),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def predict_rush(world: World) -> dict:
    sim = world.copy()
    seeker = sim.get("seeker")
    seeker.meters["climbing"] = 1
    seeker.meters["wobble"] = float(world.facts["risk"])
    events = propagate(sim, narrate=False)
    return {
        "tumble": "__tumble__" in events or seeker.meters["bruise"] >= THRESHOLD,
        "bruise": seeker.meters["bruise"],
    }


def opening(world: World, seeker: Entity, helper: Entity, source: Source) -> None:
    world.say(
        f"In the cool part of morning, {seeker.id} the {seeker.type} and "
        f"{helper.id} the {helper.type} walked beneath the {source.perch}."
    )
    world.say(
        f"A pale {source.crumb_label} came drifting down in a slow little dance. "
        f'It landed by a stone, and {seeker.id} cried, "A nibble from heaven!"'
    )
    seeker.memes["wonder"] += 1
    seeker.memes["hunger"] += 1


def desire(world: World, seeker: Entity, source: Source, route: Route) -> None:
    seeker.memes["greed"] += 1
    world.say(
        f"{seeker.id} sniffed the air. The {source.crumb_label} smelled good, and "
        f"{source.action}. {seeker.pronoun().capitalize()} looked up toward the "
        f"{source.perch} and set {seeker.pronoun('possessive')} paws on {route.label}."
    )


def warning(world: World, helper: Entity, seeker: Entity, source: Source, route: Route) -> None:
    pred = predict_rush(world)
    world.facts["predicted_tumble"] = pred["tumble"]
    helper.memes["caution"] += 1
    if pred["tumble"]:
        world.say(
            f'"Wait," said {helper.id}. "Heaven does not need {route.label}. '
            f"If you rush up there, you will tumble before you learn what fell."
        )
    else:
        world.say(
            f'"Wait," said {helper.id}. "Look first, then climb if you must. '
            f"A quick paw can still make a foolish heart."
        )


def wait_and_watch(world: World, seeker: Entity, helper: Entity, source: Source) -> None:
    helper.memes["wisdom"] += 1
    seeker.memes["patience"] += 1
    seeker.memes["greed"] = 0.0
    world.say(
        f"{helper.id} stood still in {helper.attrs['watch_style']}, and {seeker.id} "
        f"at last stood still too. They watched one more moment."
    )
    world.say(
        f"Then they saw the truth: high above, {source.label} was at the "
        f"{source.perch}, and {source.action}."
    )


def rush(world: World, seeker: Entity, route: Route) -> None:
    seeker.meters["climbing"] = 1
    seeker.meters["wobble"] = float(world.facts["risk"])
    propagate(world, narrate=False)
    world.say(
        f"But hunger pulled harder than sense. {seeker.id} scrambled up "
        f"{route.style}."
    )


def narrate_tumble(world: World, seeker: Entity, helper: Entity) -> None:
    if seeker.meters["bruise"] >= THRESHOLD:
        world.say(
            f"{route_word(world)} gave a rude shake. Down came {seeker.id} in a puff "
            f"of dust, not badly hurt, but with a sore hip and a hotter face."
        )
        world.say(f"{helper.id} jumped back, then hurried close to make sure {seeker.pronoun()} was safe.")


def route_word(world: World) -> str:
    return world.facts["route"].label


def reveal_after_rush(world: World, helper: Entity, source: Source) -> None:
    world.say(
        f'"Look up now," said {helper.id}. "There is your heaven."'
    )
    world.say(
        f"And when they looked, they saw only {source.label} at the {source.perch}. "
        f"The grand mystery was merely {source.action}."
    )


def polite_share(world: World, seeker: Entity, helper: Entity, source: Source, outcome: str) -> None:
    source_ent = world.get("source")
    if outcome == "wise":
        source_ent.memes["kindness"] += 1
        source_ent.memes["amusement"] += 1
        world.say(
            f'{source_ent.id} heard them below, leaned down, and {source.laugh_style}. '
            f'"Not from heaven," {source_ent.pronoun()} said, "only from my own hands."'
        )
        world.say(
            f"{source_ent.pronoun().capitalize()} tossed down {source.gift_phrase}, "
            f"large enough for two small mouths."
        )
    elif outcome == "scramble":
        seeker.memes["embarrassment"] += 1
        source_ent.memes["amusement"] += 1
        world.say(
            f'{source_ent.id} turned, found {seeker.id} peering up, and let out a warm laugh. '
            f'"Little friend, ask before you snatch," {source_ent.pronoun()} said.'
        )
        world.say(
            f"{source_ent.pronoun().capitalize()} reached lower and handed down "
            f"{source.gift_phrase} instead."
        )
    else:
        source_ent.memes["kindness"] += 1
        source_ent.memes["amusement"] += 1
        world.say(
            f'{source_ent.id} had seen the whole tumble and gave a soft laugh, not a cruel one. '
            f'"The sky dropped nothing," {source_ent.pronoun()} said. "I did."'
        )
        world.say(
            f"{source_ent.pronoun().capitalize()} set down {source.gift_phrase} on the ground, "
            f"where no climbing was needed."
        )
    world.facts["gift_waiting"] = 1.0
    propagate(world, narrate=False)
    seeker.memes["humility"] += 1
    helper.memes["joy"] += 1


def feast_and_moral(world: World, seeker: Entity, helper: Entity, source: Source, outcome: str) -> None:
    seeker_kind = world.facts["seeker_cfg"]
    world.say(
        f"{seeker.id} took a careful {seeker_kind.nibble_verb}, and {helper.id} took one too. "
        f"Soon both could eat and laugh together beneath the {source.perch}."
    )
    if outcome == "wise":
        world.say(
            f"{seeker.id} said, \"I called it heaven because it fell from high up. "
            f'''Now I know height is not the same as holiness.\"'''
        )
    elif outcome == "scramble":
        world.say(
            f"{seeker.id} climbed down more slowly than {seeker.pronoun()} had climbed up. "
            f"{seeker.pronoun().capitalize()} had learned that a gift asked for kindly tastes better than one chased in haste."
        )
    else:
        world.say(
            f"{seeker.id} rubbed {seeker.pronoun('possessive')} sore side and promised to look up before leaping after wonders."
        )
    world.say(
        "So the little ones learned that what falls from above is not always from heaven, "
        "and the quickest mouth is not always the wisest."
    )
@dataclass
class StoryParams:
    seeker: str
    helper: str
    source: str
    route: str
    choice: str
    seeker_name: str
    helper_name: str
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


MOUSE_NAMES = ["Milo", "Pip", "Nim", "Tumble", "Moss"]
SQUIRREL_NAMES = ["Hazel", "Skip", "Nutkin", "Rill", "Bramble"]
HEDGEHOG_NAMES = ["Prickle", "Thimble", "Burr", "Penny", "Mop"]
HELPER_NAMES = ["Lark", "Clover", "Fern", "Ash", "Poppy", "Reed"]

CURATED = [
    StoryParams(
        seeker="mouse",
        helper="sparrow",
        source="baker",
        route="crate",
        choice="wait",
        seeker_name="Milo",
        helper_name="Lark",
    ),
    StoryParams(
        seeker="squirrel",
        helper="rabbit",
        source="miller",
        route="vine",
        choice="rush",
        seeker_name="Hazel",
        helper_name="Clover",
    ),
    StoryParams(
        seeker="hedgehog",
        helper="owl",
        source="bellringer",
        route="stone_steps",
        choice="rush",
        seeker_name="Prickle",
        helper_name="Ash",
    ),
    StoryParams(
        seeker="mouse",
        helper="rabbit",
        source="bellringer",
        route="stone_steps",
        choice="wait",
        seeker_name="Pip",
        helper_name="Fern",
    ),
    StoryParams(
        seeker="squirrel",
        helper="owl",
        source="baker",
        route="barrel",
        choice="rush",
        seeker_name="Bramble",
        helper_name="Reed",
    ),
]

KNOWLEDGE = {
    "bread": [
        (
            "What is a crumb?",
            "A crumb is a very small piece that breaks off a larger food, like bread or cake."
        )
    ],
    "bakery": [
        (
            "What does a baker do?",
            "A baker makes bread and other foods from dough and bakes them with heat."
        )
    ],
    "mill": [
        (
            "What is a mill for?",
            "A mill grinds grain into meal or flour, so people can make food from it."
        )
    ],
    "oat": [
        (
            "What are oats?",
            "Oats are grains that can be cooked or baked into food. They are small, pale, and good for eating."
        )
    ],
    "bell": [
        (
            "Why does a bell ring?",
            "A bell rings when it is struck or swung. The metal vibrates and makes a loud sound."
        )
    ],
    "cheese": [
        (
            "What is cheese?",
            "Cheese is food made from milk. It can be soft or hard, and people often eat it in small bites."
        )
    ],
    "laugh": [
        (
            "Can a laugh be kind?",
            "Yes. A kind laugh is warm and friendly, and it does not try to hurt someone."
        )
    ],
    "watch": [
        (
            "Why is it smart to watch before you act?",
            "Watching first helps you learn what is really happening. Then you can choose a safer and wiser action."
        )
    ],
    "nibble": [
        (
            "What does nibble mean?",
            "To nibble means to take very small bites. Little animals often nibble their food bit by bit."
        )
    ],
}
KNOWLEDGE_ORDER = ["nibble", "bread", "bakery", "mill", "oat", "bell", "cheese", "laugh", "watch"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    source = f["source_kind"]
    outcome = f["outcome"]
    base = (
        f'Write a short fable for a young child that includes the words "nibble", '
        f'"heaven", and "laugh". A {seeker.type} thinks a falling {source.crumb_label} is a gift from heaven.'
    )
    if outcome == "wise":
        return [
            base,
            f"Tell a fable where {helper.id} advises patience, the mystery is solved with a twist, and the ending is gentle and wise.",
            f"Write a child-facing animal fable in which waiting reveals that the supposed gift from heaven came from {source.label} above."
        ]
    if outcome == "tumble":
        return [
            base,
            f"Tell a fable with a small tumble and a kind laugh, where haste leads to embarrassment but not disaster.",
            "Write a twist fable where an eager creature chases a blessing from above, only to learn it came from ordinary hands."
        ]
    return [
        base,
        f"Tell a fable where {seeker.id} rushes upward, learns to ask politely, and ends with shared food and a lesson.",
        "Write a twisty fable in which a foolish scramble turns into a kind correction and a warm ending."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker = f["seeker"]
    helper = f["helper"]
    source_ent = f["source"]
    source = f["source_kind"]
    route = f["route_kind"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {seeker.id} the {seeker.type}, {helper.id} the {helper.type}, and {source_ent.id} above them. "
            f"The little story begins when a {source.crumb_label} drifts down from the {source.perch}."
        ),
        (
            f"Why did {seeker.id} call the crumb a nibble from heaven?",
            f"{seeker.id} saw the pale morsel float down from high above and did not know where it truly came from. "
            f"Because it fell from the skyward place over {seeker.pronoun('object')}, {seeker.pronoun()} imagined it must be heavenly."
        ),
    ]
    if outcome == "wise":
        qa.append(
            (
                f"How did {helper.id} help solve the problem?",
                f"{helper.id} told {seeker.id} to wait and watch instead of rushing up {route.label}. "
                f"That patience revealed the twist: the crumb came from {source_ent.id}, not from heaven."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with {source_ent.id} sharing {source.gift_phrase} and the friends eating below the {source.perch}. "
                f"They could nibble and laugh because they chose patience before action."
            )
        )
    elif outcome == "scramble":
        qa.append(
            (
                f"What did {seeker.id} learn by rushing upward?",
                f"{seeker.id} learned that being quick is not the same as being wise. "
                f"When {seeker.pronoun()} hurried up {route.label}, {seeker.pronoun()} discovered the crumb had an ordinary source and that a polite ask works better than a snatch."
            )
        )
        qa.append(
            (
                "Was the laugh mean or kind?",
                f"It was kind. {source_ent.id} laughed warmly and then helped, so the laugh corrected the foolishness without making the ending cruel."
            )
        )
    else:
        qa.append(
            (
                f"Why did {seeker.id} tumble?",
                f"{seeker.id} rushed up {route.label} while hunger was stronger than caution. "
                f"The climb was too wobbly for such haste, so {seeker.pronoun()} fell and learned the truth from the ground."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"At first {seeker.id} chased wonder without thinking, but by the end {seeker.pronoun()} looked more carefully and moved more humbly. "
                f"The final shared bite shows that wisdom, not grabbing, brought the happy ending."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["seeker_cfg"].tags)
    tags |= set(world.facts["helper_cfg"].tags)
    tags |= set(world.facts["source_kind"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


ASP_RULES = r"""
works(S, So, R) :- seeker(S), source(So), route(R),
                   reaches(R, P), perch(So, P),
                   risk(S, So, R, V), V <= 5.

risk(S, So, R, H + Sh + W - A) :-
    seeker(S), source(So), route(R),
    height(So, H), shaky(R, Sh), weight(S, W), agility(S, A).

outcome(wise) :- choice(wait).
outcome(tumble) :- choice(rush), chosen(S, So, R), risk(S, So, R, V), tumble_limit(T), V >= T.
outcome(scramble) :- choice(rush), chosen(S, So, R), risk(S, So, R, V), tumble_limit(T), V < T.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, seeker in SEEKERS.items():
        lines.append(asp.fact("seeker", sid))
        lines.append(asp.fact("agility", sid, seeker.agility))
        lines.append(asp.fact("weight", sid, seeker.weight))
    for soid, source in SOURCES.items():
        lines.append(asp.fact("source", soid))
        lines.append(asp.fact("perch", soid, source.perch))
        lines.append(asp.fact("height", soid, source.height))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("shaky", rid, route.shaky))
        for perch in sorted(route.reaches):
            lines.append(asp.fact("reaches", rid, perch))
    lines.append(asp.fact("tumble_limit", TUMBLE_LIMIT))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show works/3."))
    return sorted(set(asp.atoms(model, "works")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen", params.seeker, params.source, params.route),
        asp.fact("choice", params.choice),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a little creature mistakes an earthly crumb for a heavenly gift."
    )
    ap.add_argument("--seeker", choices=SEEKERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--choice", choices=["wait", "rush"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(kind: str, rng: random.Random) -> str:
    if kind == "mouse":
        return rng.choice(MOUSE_NAMES)
    if kind == "squirrel":
        return rng.choice(SQUIRREL_NAMES)
    return rng.choice(HEDGEHOG_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.seeker and args.source and args.route:
        seeker = SEEKERS[args.seeker]
        source = SOURCES[args.source]
        route = ROUTES[args.route]
        if not route_works(seeker, source, route):
            raise StoryError(explain_rejection(seeker, source, route))

    combos = [
        combo for combo in valid_combos()
        if (args.seeker is None or combo[0] == args.seeker)
        and (args.source is None or combo[1] == args.source)
        and (args.route is None or combo[2] == args.route)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    seeker_id, source_id, route_id = rng.choice(combos)
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    choice = args.choice or rng.choice(["wait", "rush"])
    seeker_name = pick_name(seeker_id, rng)
    helper_name = rng.choice(HELPER_NAMES)
    return StoryParams(
        seeker=seeker_id,
        helper=helper_id,
        source=source_id,
        route=route_id,
        choice=choice,
        seeker_name=seeker_name,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.seeker not in SEEKERS:
        raise StoryError(f"(Unknown seeker '{params.seeker}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source '{params.source}'.)")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route '{params.route}'.)")
    if params.choice not in {"wait", "rush"}:
        raise StoryError(f"(Unknown choice '{params.choice}'.)")

    seeker = SEEKERS[params.seeker]
    source = SOURCES[params.source]
    route = ROUTES[params.route]
    if not route_works(seeker, source, route):
        raise StoryError(explain_rejection(seeker, source, route))

    world = tell(
        seeker_cfg=seeker,
        helper_cfg=HELPERS[params.helper],
        source_cfg=source,
        route_cfg=route,
        choice=params.choice,
        seeker_name=params.seeker_name,
        helper_name=params.helper_name,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            continue

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("empty story")
        print("OK: random generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: random generation crashed: {err}")

    try:
        curated_sample = generate(CURATED[0])
        if "heaven" not in curated_sample.story or "laugh" not in curated_sample.story:
            raise StoryError("required seed words missing from story text")
        print("OK: curated story smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: curated generation crashed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show works/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (seeker, source, route) combos:\n")
        for seeker, source, route in combos:
            print(f"  {seeker:10} {source:12} {route}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.seeker_name}: {p.choice} toward {p.source} by {p.route} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    seeker_cfg: SeekerKind,
    helper_cfg: HelperKind,
    source_cfg: Source,
    route_cfg: Route,
    choice: str,
    seeker_name: str,
    helper_name: str,
) -> World:
    world = World()
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_cfg.id,
        label=seeker_cfg.label,
        role="seeker",
        attrs={"home_image": seeker_cfg.home_image},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg.id,
        label=helper_cfg.label,
        role="helper",
        attrs={"watch_style": helper_cfg.watch_style},
    ))
    source = world.add(Entity(
        id=source_cfg.label,
        kind="character",
        type=source_cfg.type,
        label=source_cfg.label,
        role="source",
    ))

    seeker.meters["on_ground"] = 1
    seeker.meters["wobble"] = 0.0
    seeker.meters["bruise"] = 0.0
    seeker.meters["belly_full"] = 0.0
    seeker.memes["fear"] = 0.0
    seeker.memes["joy"] = 0.0
    seeker.memes["humility"] = 0.0
    helper.memes["joy"] = 0.0
    helper.memes["alarm"] = 0.0
    world.facts["gift_waiting"] = 0.0
    world.facts["risk"] = climb_risk(seeker_cfg, source_cfg, route_cfg)
    world.facts["route"] = route_cfg
    world.facts["source_cfg"] = source_cfg
    world.facts["seeker_cfg"] = seeker_cfg
    world.facts["helper_cfg"] = helper_cfg
    world.facts["choice"] = choice

    opening(world, seeker, helper, source_cfg)
    desire(world, seeker, source_cfg, route_cfg)

    world.para()
    warning(world, helper, seeker, source_cfg, route_cfg)

    if choice == "wait":
        wait_and_watch(world, seeker, helper, source_cfg)
        world.para()
        polite_share(world, seeker, helper, source_cfg, "wise")
        feast_and_moral(world, seeker, helper, source_cfg, "wise")
        outcome = "wise"
    else:
        rush(world, seeker, route_cfg)
        if seeker.meters["bruise"] >= THRESHOLD:
            world.say("")
        narrate_tumble(world, seeker, helper)
        reveal_after_rush(world, helper, source_cfg)
        world.para()
        outcome = "tumble" if seeker.meters["bruise"] >= THRESHOLD else "scramble"
        polite_share(world, seeker, helper, source_cfg, outcome)
        feast_and_moral(world, seeker, helper, source_cfg, outcome)

    world.facts.update(
        seeker=seeker,
        helper=helper,
        source=source,
        source_kind=source_cfg,
        route_kind=route_cfg,
        outcome=outcome,
        tumbled=seeker.meters["bruise"] >= THRESHOLD,
        shared=seeker.meters["belly_full"] >= THRESHOLD,
        moral="look_up_before_you_leap",
    )
    return world


SEEKERS = {
    "mouse": SeekerKind(
        id="mouse",
        label="a field mouse",
        agility=3,
        weight=1,
        nibble_verb="nibble",
        home_image="a mossy hole beneath the roots",
        tags={"mouse", "nibble"},
    ),
    "squirrel": SeekerKind(
        id="squirrel",
        label="a red squirrel",
        agility=4,
        weight=1,
        nibble_verb="nibble",
        home_image="a nest tucked in a forked branch",
        tags={"squirrel", "nibble"},
    ),
    "hedgehog": SeekerKind(
        id="hedgehog",
        label="a small hedgehog",
        agility=1,
        weight=2,
        nibble_verb="nibble",
        home_image="a leaf house under the hedge",
        tags={"hedgehog", "nibble"},
    ),
}

HELPERS = {
    "sparrow": HelperKind(
        id="sparrow",
        label="a sparrow",
        counsel="look first",
        watch_style="a bright patch of sun",
        tags={"bird", "watch"},
    ),
    "rabbit": HelperKind(
        id="rabbit",
        label="a rabbit",
        counsel="stand still",
        watch_style="the clover by the wall",
        tags={"rabbit", "watch"},
    ),
    "owl": HelperKind(
        id="owl",
        label="an owl",
        counsel="name things slowly",
        watch_style="a ring of shade",
        tags={"owl", "watch"},
    ),
}

SOURCES = {
    "baker": Source(
        id="baker",
        label="Baker Bess",
        type="hen",
        perch="bakery window",
        height=2,
        crumb_label="bread crumb",
        crumb_phrase="a warm bread crumb",
        gift_phrase="a warm crust with seeds on it",
        action="brushing crumbs from a fresh loaf on the sill",
        laugh_style="gave such a merry laugh that even the shutters seemed to smile",
        tags={"bread", "bakery", "laugh"},
    ),
    "miller": Source(
        id="miller",
        label="Miller Moss",
        type="crow",
        perch="mill ledge",
        height=3,
        crumb_label="oat flake",
        crumb_phrase="a pale oat flake",
        gift_phrase="a sweet oat scrap",
        action="shaking oat flakes from his apron at the ledge",
        laugh_style="laughed in a crackly miller's voice, kind as dry grain in a sack",
        tags={"mill", "oat", "laugh"},
    ),
    "bellringer": Source(
        id="bellringer",
        label="Bell-Ringer Bea",
        type="goose",
        perch="bell stair",
        height=3,
        crumb_label="cheese crumb",
        crumb_phrase="a moon-pale cheese crumb",
        gift_phrase="a little cheese heel",
        action="eating breakfast on the bell stair and dropping crumbs between bites",
        laugh_style="laughed so warmly that the bronze bell answered with a bright hum",
        tags={"bell", "cheese", "laugh"},
    ),
}

ROUTES = {
    "crate": Route(
        id="crate",
        label="the stack of apple crates",
        reaches={"bakery window", "mill ledge"},
        shaky=1,
        style="the stack of apple crates, quick and neat",
        tags={"crates"},
    ),
    "vine": Route(
        id="vine",
        label="the old vine by the wall",
        reaches={"mill ledge", "bell stair"},
        shaky=2,
        style="the old vine, clutching and stretching",
        tags={"vine"},
    ),
    "barrel": Route(
        id="barrel",
        label="the rain barrel and its crooked hoop",
        reaches={"bakery window"},
        shaky=2,
        style="the rain barrel and the crooked hoop, which rolled a little underfoot",
        tags={"barrel"},
    ),
    "stone_steps": Route(
        id="stone_steps",
        label="the low stone steps",
        reaches={"bakery window", "bell stair"},
        shaky=0,
        style="the low stone steps, one sober hop at a time",
        tags={"steps"},
    ),
}

if __name__ == "__main__":
    main()
